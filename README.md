# Rock Band Drums

Reproducible Linux setup for playing Rock Band 3 Deluxe with Roland electronic
drums. Target kit: TD316 with V31 module; final hardware choice is not confirmed.
The current working input is a keyboard. No Roland device is connected yet.

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
copies the US game keyboard profile, and sets the GUI theme. Existing destinations
are backed up under `~/.local/state/rock-band-drums/backups/`.
Untracked YAML/GUI settings are preserved. The input profile is replaced in full.
Capture only reads the keys and files already tracked here; review the diff before
committing. This is an explicit snapshot workflow, not a live symlink.

Use `--config-dir PATH` for a different RPCS3 installation or a disposable test.
The script does not install RPCS3, firmware, Deluxe, DLC, or the launcher.

`scripts/rpcs3` is the workstation launcher; install it to `~/.local/bin/rpcs3`
after placing the official AppImage at `~/.local/opt/rpcs3/RPCS3.AppImage`.

## Keyboard fallback

| Key | Action |
| --- | --- |
| D / F / J / K | Red / yellow / blue / green pad |
| Space | Kick |
| Enter | Start |
| K / D | Confirm / back |
| Arrows | Menu navigation |
| Tab | Select |

See [setup](docs/setup.md) and [Roland commissioning](docs/roland.md).
Hardware calibration remains pending; the keyboard test does not validate MIDI
latency or electronic drum playability. Repository is local; no remote configured.
