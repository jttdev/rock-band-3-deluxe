# Rock Band Linux

Linux RPCS3 / Rock Band 3 Deluxe setup for all instruments and local multiplayer.
Roland electronic drums are the first hardware target.

- `README.md`: usage and configuration ownership.
- `docs/setup.md`: installation and verified workstation state.
- `docs/roland.md`: hardware commissioning and calibration.
- `docs/projector.md`: display choice, low-lag settings and ceiling-mount geometry.
- `config/`: reviewed, portable settings; `scripts/config.py` applies or captures them.
- Keep game data, firmware, licences, saves, binaries, RPCN credentials and console
  identifiers outside this repo. Never copy the full RPCS3 config tree into git.
- Do not change live settings while RPCS3 is open.
- MIDI is configured through RPCS3 I/O; the keyboard drum profile is a fallback.
- Actual Roland pad mapping and latency must be measured with the connected kit.
