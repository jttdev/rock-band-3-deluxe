# Rock Band Linux

This directory is the Linux workstation portion of the combined Rock Band 3
development checkout. Run the commands below from `linux/`; the paths are relative
to this directory. The source and development tools live at the repository root.

Reproducible Linux setup for the full Rock Band 3 Deluxe experience: drums,
guitar, bass, vocals, keys, and local multiplayer through RPCS3.
The connected electronic kit is reported as an EFNOTE 3B, using a CME C2MIDI Pro
DIN-to-USB interface. Its pad mapping is measured from live MIDI events.
Audio uses the MOTU M4. The Bluetooth 8Bitdo SN30 Pro uses XInput mode and serves
as the drum player's navigation pad, with a separate keyboard drum fallback.
Two wired Xbox 360 X-plorer guitars are configured on Players 3 and 4;
the user confirms multiplayer input and play work.

Private repository: <https://github.com/jttdev/rock-band-linux>.

## Configuration

Close RPCS3 before applying or capturing settings. Python 3 and PyYAML are required
(`uv run --with pyyaml python scripts/config.py ...` also works).

```sh
python3 scripts/config.py apply --dry-run
python3 scripts/config.py apply
python3 scripts/config.py capture
git diff
```

Apply merges the tracked global and game settings into existing YAML files,
copies the global and US game controller profiles, and sets the GUI theme. Existing destinations
are backed up under `~/.local/state/rock-band-linux/backups/`.
Untracked YAML/GUI settings are preserved. Input profiles and the custom SDL
controller database are replaced in full.
Capture only reads the keys and files already tracked here; review the diff before
committing. This is an explicit snapshot workflow, not a live symlink.

The PipeWire rule in `config/pipewire/` is installed by hand (see
[setup](docs/setup.md)). Together with the launcher's `PULSE_LATENCY_MSEC` it
shortens RPCS3's audio path; `scripts/latency-report` prints the result while a
song plays. Details and tuning: [latency](docs/latency.md).

Use `--config-dir PATH` for a different RPCS3 installation or a disposable test.
The script does not install RPCS3, firmware, Deluxe, DLC, or the launcher.

`scripts/rpcs3` is the workstation launcher; install it to `~/.local/bin/rpcs3`
after placing the official AppImage at `~/.local/opt/rpcs3/RPCS3.AppImage`.
Install `scripts/rock-band-3` to `~/.local/bin/rock-band-3` for the game-specific
external-drive check and audio setting; see [setup](docs/setup.md).

## Controller and keyboard fallback

The global profile uses SDL device `8Bitdo SN30 Pro 1` as Player 1. The US game
reserves Player 1 for the MIDI adapter and puts the SN30 Pro on Player 2, selected
as Deluxe's Navigation Pad. It emulates a standard DualShock 3. Face buttons follow PS3 positions: bottom is
Cross, right is Circle, left is Square, and top is Triangle. D-pad, both sticks,
shoulders, triggers, stick clicks, Start and Select are mapped. Right-stick click
still needs an isolated test; Home/Guide is unavailable in this XInput mapping.
In the measured Bluetooth mode this means **B = Cross, A = Circle,
Y = Square, X = Triangle**. The measured XInput mapping is in
`config/rpcs3/input_configs/gamecontrollerdb.txt`. Keep this controller in
XInput mode with that mapping. The game launcher uses the classic SDL joystick
endpoint; drums join by hitting a tom, as described in [EFNOTE commissioning](docs/efnote.md).

To use keyboard drums, select **Keyboard Drums** as the US game's input profile
in RPCS3, or launch with `--input-config "Keyboard Drums"`.

| Key | Action |
| --- | --- |
| D / F / J / K | Red / yellow / blue / green pad |
| Space | Kick |
| Enter | Start |
| K / D | Confirm / back |
| Arrows | Menu navigation |
| Tab | Select |

See [setup](docs/setup.md), [EFNOTE commissioning](docs/efnote.md) and
[projector](docs/projector.md).
The user confirms calibration and a full-song playthrough are complete. Reconnect
and advanced input checks remain listed in the commissioning notes. Guitar
whammy, tilt and reconnect checks remain pending. Microphones and keys
will need hardware checks and profiles as they are added.
