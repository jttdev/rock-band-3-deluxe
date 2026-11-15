#!/usr/bin/env python3
"""Supervise one private RPCS3 run and retain startup and exit evidence."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import signal
import subprocess
import time

import yaml


def utc():
    return datetime.now(timezone.utc).isoformat()


def read_log(path, offset):
    """Read written bytes from an append-only, NUL-preallocated emulator log."""
    if path.stat().st_size < offset:
        offset = 0
    with path.open("rb") as stream:
        stream.seek(offset)
        chunks = []
        while True:
            block = stream.read(1024 * 1024)
            if not block:
                break
            written = block.split(b"\0", 1)[0]
            chunks.append(written)
            if len(written) != len(block):
                break
    data = b"".join(chunks)
    return data, offset + len(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", type=Path)
    parser.add_argument("run", type=Path)
    args = parser.parse_args()
    state, run = args.state.resolve(), args.run.resolve()
    run.mkdir(parents=True, exist_ok=False)
    metadata = json.loads((state / "test.json").read_text())
    config = Path(metadata["config"])
    game = config / "dev_hdd0/game/BLUS30463/USRDIR"
    cache = state / "cache/rpcs3"
    events = (run / "events.jsonl").open("a", buffering=1)

    def event(stage, **fields):
        record = dict(time=utc(), elapsed_seconds=round(time.monotonic() - started, 3),
                      stage=stage, **fields)
        events.write(json.dumps(record) + "\n")
        print(json.dumps(record), flush=True)

    started = time.monotonic()
    profile = config / "input_configs/BLUS30463/Default.yml"
    pads = yaml.safe_load(profile.read_text())
    settings = yaml.safe_load((config / "config.yml").read_text())
    custom = yaml.safe_load((config / "custom_configs/config_BLUS30463.yml").read_text())
    video = dict(settings.get("Video", {}), **custom.get("Video", {}))
    audio = dict(settings.get("Audio", {}), **custom.get("Audio", {}))
    cgroup = Path("/proc/self/cgroup").read_text().strip()
    resources = Path("/sys/fs/cgroup") / cgroup.split("::", 1)[1].lstrip("/")
    header = game / "gen/patch_ps3.hdr"
    event("supervisor_started", pid=os.getpid(), build=metadata.get("build"),
          renderer=video.get("Renderer"), audio_renderer=audio.get("Renderer"),
          music_handler=audio.get("Music Handler"),
          midi_devices=custom.get("Input/Output", {}).get("Emulated Midi devices"),
          qt_media_backend=os.environ.get("QT_MEDIA_BACKEND"),
          cgroup=cgroup,
          patch_header_sha256=hashlib.sha256(header.read_bytes()).hexdigest(),
          controllers={key: {name: value.get(name) for name in ("Handler", "Device")}
                       for key, value in pads.items() if key.startswith("Player")})
    patterns = {
        "input_profile_loaded": "Loading input configuration:",
        "game_executable_selected": "SYS: Elf path:",
        "qt_music_initialization": "Constructing Qt music handler",
        "navigation_device_detected": "name='RB3 Test Navigation'",
        "midi_controller_registered": "LDD, VID=",
        "renderer_ready": "GL RENDERER:",
        "vulkan_renderer_ready": "Vulkan: Adapter:",
        "drum_start_received": "hit combo: start",
        "settings_opened": "sys_fs_open(path=“/dev_hdd0/game/BLUS30463/USRDIR/dx_settings.dta",
        "track_asset_opened": "tracksystem.milo_ps3",
        "fatal_log_entry": "·F ",
        "emulator_fatal_error": "Emulation has been frozen!",
        "shader_compile_failed": "RSX: Compilation failed:",
        "evdev_navigation_detected": "Capability info for RB3 Test Navigation",
        "native_segfault": "Segfault reading location",
    }
    seen = set()
    offsets = {}
    tails = {}
    trace_previous = None
    interrupted = []
    for name in ("RPCS3.log", "TTY.log"):
        source = cache / name
        if source.exists():
            shutil.copy2(source, run / ("previous_" + name))
            source.unlink()
    previous_trace = game / "dx_lane_startup.dta"
    if previous_trace.exists():
        shutil.copy2(previous_trace, run / "previous_dx_lane_startup.dta")
        previous_trace.unlink()
    with (run / "console.log").open("wb") as console:
        child = subprocess.Popen([str(Path.home() / ".local/bin/rpcs3"), "--no-gui", metadata["game"]],
                                 stdout=console, stderr=subprocess.STDOUT, start_new_session=True)
        event("emulator_spawned", pid=child.pid)

        def forward(number, _frame):
            interrupted.append(number)
            event("supervisor_signal", signal=number)
            if child.poll() is None:
                try:
                    os.killpg(child.pid, number)
                except ProcessLookupError:
                    pass

        for number in (signal.SIGTERM, signal.SIGINT):
            signal.signal(number, forward)

        def collect():
            nonlocal trace_previous
            for name in ("RPCS3.log", "TTY.log"):
                source = cache / name
                if not source.exists():
                    continue
                data, offsets[name] = read_log(source, offsets.get(name, 0))
                if data:
                    with (run / name).open("ab") as out:
                        out.write(data)
                    if name == "RPCS3.log":
                        decoded = tails.get(name, "") + data.decode(errors="replace")
                        tails[name] = decoded[-1024:]
                        for stage, marker in patterns.items():
                            if stage not in seen and marker in decoded:
                                seen.add(stage)
                                detail = next((line.split(marker, 1)[1].strip()
                                               for line in decoded.splitlines() if marker in line), "")
                                event(stage, **({"device": detail} if stage == "renderer_ready" else {}))
                        fault = re.search(r"Segfault reading location [0-9a-fA-F]+ at (?:0x)?([0-9a-fA-F]+)", decoded)
                        if fault and "native_fault_module" not in seen:
                            address = int(fault[1], 16)
                            for pid in (resources / "cgroup.procs").read_text().split():
                                try:
                                    mappings = Path("/proc", pid, "maps").read_text().splitlines()
                                except (FileNotFoundError, PermissionError, ProcessLookupError):
                                    continue
                                for mapping in mappings:
                                    fields = mapping.split()
                                    low, high = (int(value, 16) for value in fields[0].split("-"))
                                    if low <= address < high:
                                        seen.add("native_fault_module")
                                        event("native_fault_module", pid=int(pid), module=Path(fields[-1]).name,
                                              file_offset=hex(address - low + int(fields[2], 16)))
                                        break
                                if "native_fault_module" in seen:
                                    break
            source = game / "dx_lane_startup.dta"
            if source.exists():
                data = source.read_bytes()
                if data != trace_previous:
                    trace_previous = data
                    (run / source.name).write_bytes(data)
                    event("game_startup_trace_updated", trace=data.decode(errors="replace"))

        last_heartbeat = 0
        try:
            while child.poll() is None:
                collect()
                if time.monotonic() - last_heartbeat >= 10:
                    last_heartbeat = time.monotonic()
                    counters = {}
                    for name in ("memory.current", "memory.peak", "memory.events"):
                        path = resources / name
                        if path.exists():
                            counters[name] = path.read_text().strip()
                    event("heartbeat", observed_stages=sorted(seen), resources=counters)
                time.sleep(.5)
            event("emulator_exited", returncode=child.returncode, received_signals=interrupted)
        finally:
            collect()
            (run / "result.json").write_text(json.dumps(dict(time=utc(), returncode=child.poll(),
                received_signals=interrupted, observed_stages=sorted(seen)), indent=2) + "\n")
            events.close()
    return child.returncode if child.returncode >= 0 else 128 - child.returncode


if __name__ == "__main__":
    raise SystemExit(main())
