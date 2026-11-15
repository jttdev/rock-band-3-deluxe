# Configurable drum lanes

The requested EFNOTE layout, from left to right, is **hi-hat, snare, high tom,
middle tom, ride, floor tom, crash**, with a full-width kick bar. The menu must
offer the standard shared-lane highway and separate cymbal lanes, remember the
selection, and allow changing the order. Both crash cymbals send the chart's
green-cymbal part; the chart cannot distinguish left and right crashes.

## Use

Before starting a song, open Start → Options → Deluxe Settings → Drum Lanes.
Choose **Separate: EFNOTE kit** for the requested layout, **Standard: shared
lanes** for the original highway, or **Edit custom order** to arrange the seven
parts. The numbers in the editor are positions from left to right. Left/right
swaps the selected part with its neighbor; confirm also moves it right. Back out
of Deluxe Settings to save. Choose Pro Drums when selecting the song instrument.

The layout applies to the next song. Kick stays full width, and instrument input
mapping and calibration retain their existing settings.

## Engine boundaries

The engine has five logical drum inputs: kick plus red, yellow, blue and green.
Pro Drums adds the cymbal distinction to those inputs. Seven visible lanes can
therefore retain the existing input and scoring model: snare plus three toms,
and yellow, blue and green cymbals. A visual lane is not an additional input bit.

The pinned engine reference is the Wii build `100901_A`. It explains the design,
but actual assets and RPCS3 behavior must verify applicability to PS3.

- `Gem::AddInstance` chooses `_cymbal` widgets independently of the input slot.
- `GemManager::GetWidgetName` reads the widget name for each slot and note state.
- `TrackWidget::ApplyOffsets` supports an independent `x_offset`.
- `TrackWidget::RemoveAt` also uses that offset when removing scored notes.
- `TrackDir::Load` assigns the owning track to widgets. Creating a widget at
  runtime does not establish this relationship; required widgets must be loaded
  with the track asset.
- `GemManager::UpdateSlotPositions` derives logical slot transforms from the
  hit receivers. Moving a receiver can also move subsequently spawned notes.
- The hit receivers cache separate cymbal and drum triggers. Changing a scripted
  `hit_cymbal` handler alone does not redirect the engine's cached trigger.

Star, unison and missed-note widgets are shared between logical slots in the
standard graphics table. Separate lanes require independent copies for these
states as well as normal notes. Hit feedback, fills, rolls, overdrive, practice
restarts, multiplayer and restoring the standard layout need verification.

## Receiver surface

The four stock receiver transforms describe a shallow curved surface. Their
local X/Z positions and X-axis slopes are captured once per smasher plate,
before separate-lane placement. Stock receiver directories retain their original
transforms; only their visual groups are reparented.

`dx_drum_lane_surface.dta` interpolates these samples with cubic Hermite segments
and extends the endpoint tangents to the outer lanes. The seven X positions are
`2.8 * (position - 3)`. Receiver height and tilt follow that position regardless
of which instrument occupies it. The visual anchors share the stock receivers'
parent coordinate system. Cymbals add Y = -2.55 and Z = -0.1 to the surface and
retain 45% opacity; pads retain their half-width mesh scale.

Note placement changes only the widget's lateral X offset. Y follows chart
time and Z retains stock note geometry; their asset offsets must be preserved.
The cymbal receiver's -2.55 Y offset must never reach travelling notes: that
moves them off their horizontal beat lines. Cosmetic target adjustments must
not enter `TrackWidget` placement/removal offsets or scoring calibration.
Target reaction animations and particle launchers use the visual
anchors. Standard mode restores the original visual parents, scales and trigger
references and hides the custom cymbal targets.

The Milo inspector exposes the complete row-vector affine matrix and axis
lengths. Matrix diagonal entries alone are not scales when a receiver is tilted.
The Python geometry tests evaluate the shipped pure DTA functions against stock
PS3 samples, including continuity, outer extrapolation and frame orthonormality.
DTA `do` bindings must precede commands; `*` is binary and `-` is unary/binary.
Live `surface_<part>_x_..._z_..._slope_...` trace entries verify the PS3 runtime
against the numerical tests.

## Asset tooling

Run `python3 tools/bootstrap.py --install-dotnet` once, then
`python3 tools/milo.py inspect INPUT.milo_ps3 OUTPUT.json`.
The bootstrap initializes only the pinned engine reference and MiloLib; the
optional custom-character pack is separate.

The bundled SuperFreq can extract this revision-28 asset but cannot safely
round-trip it: its writer emits an unsupported directory version, and its
delimiter-based extraction does not follow embedded directory boundaries.
Use MiloLib to identify objects. Preserve existing serialized payloads when
adding widgets, and reopen generated assets with the independent object reader.

## Verification status

The development checkout includes the Linux setup under `linux/` and pinned
engine and MiloLib references under `third_party/`. The archive inspector and
development bootstrap are under `tools/`.

The prototype adds Deluxe Settings → Drum Lanes before a song, with standard,
EFNOTE and custom orders. Settings persist through the existing Deluxe settings
file. The feature is gated by `DX_SPLIT_DRUM_LANES` and built with
`python3 tools/build.py`.

The PS3 build passes. The asset tool verifies 207 additions in the standalone
track system and 828 additions across the four embedded GemTrackDirs in
`trackpanel.milo_ps3`, preserving existing object payloads. Gameplay uses those
embedded directories. New widgets must also belong to the track's draw groups;
loading them alone does not make notes visible.

The user has confirmed scrolling hi-hat, snare, ride, crash and all three tom
lanes in gameplay. Beast and the Harlot provides tom notes early in its intro;
`tools/chart_parts.py` can inspect a song directly from the owned game archive
and report its Pro Drums parts and tom timestamps. Bottom cymbal targets reuse
the regular note geometry with separate materials so their opacity can change
without dimming scrolling notes. Targets are lowered and use 45% opacity.

The isolated-profile checks on 2026-11-15 cover:

- PS3 build, twelve Python regression tests and `git diff --check`.
- All seven live surface traces matching the numerical curve (0.0051 tolerance
  for two-decimal trace formatting), including repeated layout application.
- EFNOTE targets, simultaneous snare/crash notes on the same horizontal beat
  line, and individual hi-hat/ride/crash reaction and particle feedback in Olé.
  MIDI test pulses scored 1,710 points; the ride capture includes Perfect hits.
- Song restart, plus a saved custom order surviving a full emulator restart:
  ride, snare, high tom, crash, middle tom, hi-hat, floor tom. Ride takes the
  outer-left tilt; crash takes the nearly level centre transform.
- Custom-order practice in ¡Viva la Gloria!, including a practice restart, and
  standard-mode restoration in the same emulator instance. Standard mode shows
  four full-width targets and no separate cymbal receivers.

Evidence is under the private test state's `evidence/surface-fix-20261115/`;
`efnote.png`, `ride-sheet.png`, `crash-sheet.png`, `custom-practice.png`,
`practice-restart.png` and `standard-restored.png` cover these checks. The test
profile defaults to EFNOTE; its prior custom order is preserved. Alignment
acceptance uses the local receiver surface and note/target contact, not equal
screen bottom-edge heights. Final visual acceptance remains with the user.
Multiplayer still needs focused verification. The workstation uses the local
PS3 build from the owned `jttdev/rock-band-3-deluxe` fork.
The installed source commit and file hashes are recorded in its local backup
manifest.

### Test profile

Private test metadata is under
`~/.local/state/rock-band-linux/lane-tests/20261114T035032.661356Z/test.json`.
Start the temporary navigation service before launching that profile. The
external EXT_MICRON drive must be mounted: the profile links its installed game
assets and song library. Normal-profile updates replace only `PARAM.SFO`,
`USRDIR/EBOOT.BIN`, `USRDIR/band_s.self` and the two `USRDIR/gen/patch_ps3*`
files after closing RPCS3. Back up these files first under
`~/.local/state/rock-band-linux/backups/`; keep saves, `dx_settings.dta`,
calibration, controller settings and renderer/audio configuration intact.

Intel OpenGL is the verified renderer for this profile. If shader compilation
requests unsupported NVIDIA extensions after switching GPUs, stop RPCS3 and
preserve/rename the per-EBOOT `shaders_cache` directories in the private cache
before letting Intel rebuild them. Keep PPU/SPU caches and normal-profile caches
intact. NVIDIA OpenGL has produced a black window in this diagnostic profile.

## Isolated RPCS3 testing

`tools/rpcs3_test.py prepare --game PATH --renderer OpenGL --mute` creates a private profile outside git,
copies saves and mutable settings, links installed firmware and immutable game
assets, and overlays the build. `launch STATE` runs it; `refresh STATE` updates
the overlay while RPCS3 is closed. `refresh STATE --baseline` selects the
installed build for comparison. Launch uses a named systemd user service with
its own memory limit, independent of the calling tool command's lifetime. The
command prints the exact journal and stop commands; the unit name is also saved
in the private `test.json`. `launch STATE --dry-run` previews without starting
the emulator. Do not wrap launch in another systemd scope.

Each invocation retains `console.log`, `RPCS3.log`, `TTY.log`, timestamped
`events.jsonl`, game-side `dx_lane_startup.dta` checkpoints and an exit
`result.json` under `STATE/runs/TIMESTAMP`. The supervisor records launch build,
patch-header hash, renderer, controller handlers, its cgroup, incoming signals
and the emulator exit code. RPCS3's mapped logs contain preallocated NUL space;
the live collector advances only over written bytes. These logs remain outside
git because emulator output can contain private console and save identifiers.

An observed native startup segfault resolved to PipeWire's protocol library.
The private diagnostic profile uses `Audio / Renderer: Null` and
`Audio / Music Handler: Null` to bypass audio initialization while testing lanes.
This is a muted diagnostic setting; normal
audio configuration is unchanged. Game-script checkpoints distinguish UI
initialization, settings loading and track receiver setup from native emulator
startup failures.

The test profile reserves Player 1 for MIDI and uses Player 2 for Evdev navigation
(SDL is an optional preparation setting).
`tools/test_navigation.py --socket PATH serve` supplies a temporary gamepad;
`--socket PATH send start` or `send confirm` presses a button. The server needs
the controller venv with evdev and permission to access `/dev/uinput`. The profile
can also include the temporary device's SDL controller database entry. The drum
Start sequence in `linux/scripts/sn30-drum-start.py` joins the MIDI drummer before
Deluxe's navigation pad can control it.

Direct X11 window captures can return stale frames while RPCS3 continues
running. Spectacle compositor captures work with OpenGL in the private profile.
Confirm that the intended window still exists and is active before capturing.
An unchanged capture alone is insufficient evidence of failed input.
