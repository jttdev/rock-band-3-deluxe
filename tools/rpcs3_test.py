#!/usr/bin/env python3
"""Prepare or launch a private RPCS3 test profile with a built Deluxe overlay."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import shlex
import subprocess
import sys

import yaml

from bootstrap import ROOT
from test_navigation import SDL_CLASSIC_MAPPING

TITLE = "BLUS30463"
READ_ONLY_EXTENSIONS = {".bin", ".self", ".hdr", ".ark", ".milo_ps3", ".bik",
                        ".png", ".pam", ".mogg", ".mid", ".edat", ".sfo",
                        ".dat", ".psarc", ".rwm", ".pck"}


def ensure_closed():
    for comm in Path("/proc").glob("[0-9]*/comm"):
        try:
            if comm.read_text().strip().lower() in ("rpcs3", "apprun.wrapped"):
                raise RuntimeError("Close RPCS3 before refreshing test files")
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            pass


def overlay(source, overrides, destination):
    """Copy changed files and mutable settings; link read-only game assets."""
    destination.mkdir(parents=True)
    names = set(path.name for path in source.iterdir()) if source.exists() else set()
    names.update(path.name for path in overrides.iterdir())
    for name in names:
        original, replacement, target = source / name, overrides / name, destination / name
        if replacement.is_dir():
            overlay(original, replacement, target)
        elif replacement.is_file():
            shutil.copy2(replacement, target)
        elif original.is_file() and original.suffix.lower() not in READ_ONLY_EXTENSIONS:
            shutil.copy2(original, target)
        else:
            target.symlink_to(original.resolve(), target_is_directory=original.is_dir())


def prepare(source, build, game, midi_device, navigation_device, renderer=None, mute=False,
            navigation_handler="Evdev"):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    state = Path.home() / ".local/state/rock-band-linux/lane-tests" / stamp
    config = state / "config/rpcs3"
    config.mkdir(parents=True)
    for name in ("config.yml", "vfs.yml", "rb3drums.yml"):
        if (source / name).exists():
            shutil.copy2(source / name, config / name)
    global_config = config / "config.yml"
    global_settings = yaml.safe_load(global_config.read_text())
    global_settings.setdefault("Miscellaneous", {})["Start games in fullscreen mode"] = False
    if renderer:
        global_settings.setdefault("Video", {})["Renderer"] = renderer
    if mute:
        global_settings.setdefault("Audio", {}).update({"Renderer": "Null", "Music Handler": "Null"})
    global_config.write_text(yaml.safe_dump(global_settings, sort_keys=False))
    drum_config = config / "rb3drums.yml"
    drum_settings = yaml.safe_load(drum_config.read_text())
    drum_settings["Pulse width ms"] = 200
    drum_config.write_text(yaml.safe_dump(drum_settings, sort_keys=False))
    for name in ("custom_configs", "input_configs", "GuiConfigs"):
        if (source / name).exists():
            shutil.copytree(source / name, config / name)
    if not (source / "dev_flash").is_dir():
        raise RuntimeError("Source profile has no installed firmware")
    (config / "dev_flash").symlink_to((source / "dev_flash").resolve(), target_is_directory=True)
    for name in ("dev_flash2", "dev_flash3"):
        if (source / name).is_dir():
            shutil.copytree(source / name, config / name)
    home = source / "dev_hdd0/home"
    if home.exists():
        shutil.copytree(home, config / "dev_hdd0/home")
    installed = source / "dev_hdd0/game"
    games = config / "dev_hdd0/game"
    games.mkdir(parents=True)
    for entry in installed.iterdir():
        if entry.name != TITLE:
            (games / entry.name).symlink_to(entry.resolve(), target_is_directory=entry.is_dir())
    overlay(installed / TITLE, build, games / TITLE)
    custom = config / f"custom_configs/config_{TITLE}.yml"
    settings = yaml.safe_load(custom.read_text())
    settings.setdefault("Miscellaneous", {})["Start games in fullscreen mode"] = False
    if renderer:
        settings.setdefault("Video", {})["Renderer"] = renderer
    if mute:
        settings.setdefault("Audio", {}).update({"Renderer": "Null", "Music Handler": "Null"})
    devices = settings.setdefault("Input/Output", {}).get("Emulated Midi devices", "").split("@@@")
    devices[0] = "Drumsßßß" + midi_device
    settings["Input/Output"]["Emulated Midi devices"] = "@@@".join(devices)
    custom.write_text(yaml.safe_dump(settings, sort_keys=False))
    profile = config / f"input_configs/{TITLE}/Default.yml"
    pads = yaml.safe_load(profile.read_text())
    navigation_device = navigation_device or ("RB3 Test Navigation 1" if navigation_handler == "SDL"
                                               else "RB3 Test Navigation")
    pads["Player 2 Input"]["Handler"] = navigation_handler
    pads["Player 2 Input"]["Device"] = navigation_device
    if navigation_handler == "Evdev":
        pads["Player 2 Input"]["Config"] = {"Device Class Type": 0, "Vendor ID": 1356, "Product ID": 616}
    profile.write_text(yaml.safe_dump(pads, sort_keys=False))
    if navigation_device == "RB3 Test Navigation 1":
        database = config / "input_configs/gamecontrollerdb.txt"
        original = database.read_text() if database.exists() else ""
        database.write_text(original.rstrip() + "\n" + SDL_CLASSIC_MAPPING + "\n")
    metadata = {"game": str(game.resolve()), "config": str(config), "source": str(source.resolve())}
    (state / "test.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(state)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("prepare")
    create.add_argument("--source-config", type=Path, default=Path.home() / ".config/rpcs3")
    create.add_argument("--build", type=Path, default=ROOT / "out/ps3")
    create.add_argument("--game", type=Path, required=True)
    create.add_argument("--midi-device", default="Midi Through:Midi Through Port-0 14:0",
                        help="ALSA source for this test profile; defaults to the kernel virtual MIDI port")
    create.add_argument("--navigation-device", help="navigation device; tools/test_navigation.py provides the default")
    create.add_argument("--navigation-handler", choices=("Evdev", "SDL"), default="Evdev",
                        help="backend for the temporary navigation gamepad (default: Evdev)")
    create.add_argument("--renderer", choices=("OpenGL", "Vulkan"), help="override renderer in the private profile")
    create.add_argument("--mute", action="store_true", help="disable game audio and Qt music in the private profile")
    launch = commands.add_parser("launch")
    launch.add_argument("state", type=Path)
    launch.add_argument("--dry-run", action="store_true", help="print the service command without starting RPCS3")
    launch.add_argument("--nvidia", action="store_true", help="use NVIDIA PRIME offload for diagnostic OpenGL runs")
    refresh = commands.add_parser("refresh")
    refresh.add_argument("state", type=Path)
    refresh.add_argument("--baseline", action="store_true", help="use the working installation as a control")
    refresh.add_argument("--build", type=Path, default=ROOT / "out/ps3")
    args = parser.parse_args()
    if args.command == "prepare":
        if not (args.build / "USRDIR/gen/patch_ps3.hdr").is_file():
            parser.error("Build the mod first with python3 tools/build.py")
        if not args.game.is_dir():
            parser.error("The disc game directory does not exist")
        prepare(args.source_config.resolve(), args.build.resolve(), args.game, args.midi_device,
                args.navigation_device, args.renderer, args.mute, args.navigation_handler)
    elif args.command == "refresh":
        ensure_closed()
        state = args.state.resolve()
        metadata = json.loads((state / "test.json").read_text())
        source = (Path(metadata["source"]) / f"dev_hdd0/game/{TITLE}"
                  if args.baseline else args.build.resolve())
        target = Path(metadata["config"]) / f"dev_hdd0/game/{TITLE}"
        for relative in ("PARAM.SFO", "USRDIR/EBOOT.BIN", "USRDIR/band_s.self",
                         "USRDIR/gen/patch_ps3.hdr", "USRDIR/gen/patch_ps3_0.ark"):
            destination = target / relative
            if destination.is_symlink():
                destination.unlink()
            shutil.copy2(source / relative, destination)
        metadata["build"] = "baseline" if args.baseline else str(args.build.resolve())
        (state / "test.json").write_text(json.dumps(metadata, indent=2) + "\n")
        print(f"Refreshed isolated test profile: {metadata['build']}")
    else:
        state = args.state.resolve()
        metadata = json.loads((state / "test.json").read_text())
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        unit = "rb3-lane-test-" + stamp.lower().replace(".", "-") + ".service"
        run = state / "runs" / stamp
        env = {key: os.environ[key] for key in
               ("DISPLAY", "XAUTHORITY", "WAYLAND_DISPLAY", "XDG_RUNTIME_DIR",
                "DBUS_SESSION_BUS_ADDRESS", "PULSE_SERVER") if key in os.environ}
        env.update(XDG_CONFIG_HOME=str(state / "config"),
                   XDG_CACHE_HOME=str(state / "cache"), SDL_JOYSTICK_LINUX_CLASSIC="1")
        if args.nvidia:
            env.update(__NV_PRIME_RENDER_OFFLOAD="1", __GLX_VENDOR_LIBRARY_NAME="nvidia")
        command = ["systemd-run", "--user", "--unit=" + unit, "--collect",
                   "--service-type=exec", "--working-directory=" + str(ROOT),
                   "--property=MemoryMax=60%", "--property=MemorySwapMax=0",
                   "--property=KillMode=control-group", "--property=TimeoutStopSec=10"]
        command.extend("--setenv=" + key + "=" + value for key, value in env.items())
        command.extend([sys.executable, str(ROOT / "tools/rpcs3_run.py"), str(state), str(run)])
        if args.dry_run:
            print(shlex.join(command))
            return
        ensure_closed()
        subprocess.run(command, check=True)
        metadata["unit"] = unit
        metadata["last_run"] = str(run)
        (state / "test.json").write_text(json.dumps(metadata, indent=2) + "\n")
        print(f"RPCS3 service: {unit}")
        print(f"Startup evidence: {run}")
        print(f"Logs: journalctl --user -u {unit}")
        print(f"Stop: systemctl --user stop {unit}")


if __name__ == "__main__":
    main()
