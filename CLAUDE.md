# Rock Band 3 development

Single checkout for Deluxe source, Linux setup, lane-layout tooling and engine
references. Read `/home/janosch/DEV/CLAUDE.md` and `fun/CLAUDE.md` first.

- `readme.md`, `building.md`: upstream Deluxe overview and build pipeline.
- `linux/`: workstation configuration, launchers and hardware documentation;
  its original history is imported as a git subtree.
- `tools/`: development tooling; `tools/bootstrap.py` initializes pinned tools.
- `third_party/rb3-engine-reference`: pinned Wii decompilation for understanding
  engine behavior, not a replacement PS3 executable.
- `third_party/MiloLib`: pinned library for reading the actual Milo object graph.
- `docs/drum-lanes.md`: lane model, constraints and verification status.

Keep upstream changes localized. Modify our tools rather than editing submodule
sources. Do not initialize the optional `rb3dx_assets` character pack unless needed.
Game data, firmware, licences, saves, binaries from the workstation, RPCN
credentials and console identifiers stay outside git. Never capture the full
RPCS3 configuration tree. Do not change live settings while RPCS3 is open.

The requested kit order is hi-hat, snare, high tom, middle tom, ride, floor tom,
crash. Kick remains a full-width bar. Both physical crash cymbals share the chart's
green-cymbal part. MIDI mapping and scoring semantics must remain consistent.
