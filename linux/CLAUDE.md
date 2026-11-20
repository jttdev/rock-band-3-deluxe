# Rock Band Linux

Linux RPCS3 / Rock Band 3 Deluxe setup for all instruments and local multiplayer.
EFNOTE drums through a CME C2MIDI Pro are the connected hardware target.

- `README.md`: usage and configuration ownership.
- `docs/setup.md`: installation and verified workstation state.
- `docs/efnote.md`: connected kit, measured MIDI notes and calibration status.
- `docs/roland.md`: uncommissioned Roland alternative.
- `docs/projector.md`: display choice, low-lag settings and ceiling-mount geometry.
- `docs/latency.md`: audio and video delay per stage, the settings that set it, how to check and tune.
- `config/`: reviewed, portable settings; `scripts/config.py` applies or captures them.
- Keep game data, firmware, licences, saves, binaries, RPCN credentials and console
  identifiers outside this repo. Never copy the full RPCS3 config tree into git.
- Do not change live settings while RPCS3 is open.
- MIDI is configured through RPCS3 I/O; the keyboard drum profile is a fallback.
- Pad mapping and latency must be measured with the connected kit; see commissioning docs.
