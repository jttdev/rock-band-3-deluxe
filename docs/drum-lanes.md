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

Runtime checks on 2026-11-14 verified that moving hi-hat right swaps it with
snare, the resulting custom order survives a full emulator restart, and gameplay
uses that order. MIDI test pulses scored 3,180 points without a crash. Switching
back to standard mode in the same instance restored four full-width targets and
removed the separate cymbal targets. The EFNOTE preset was then restored.
Restarting a song also preserved the seven-lane layout. A gameplay capture
showed hi-hat feedback at the left cymbal target and snare feedback at the next
pad target. Target opacity was accepted by the user. The current cymbal anchor
offset is Y = -2.55, Z = -0.1 for all three cymbals. Screenshot measurements put
their bottom edges at 611, 611 and 610 pixels in the normalized 720p capture.
The user deferred final visual fine-tuning; alignment is not signed off.
Individual ride/crash feedback, practice sections and multiplayer still need
focused verification. The workstation installation remains the known working
Deluxe build; these checks use the isolated profile.

### Paused handoff

The goal is paused at the user's request. The latest PS3 build passed, the five
Python regression tests passed, and `git diff --check` passed. The test emulator
and temporary navigation service were stopped for session close.

Resume by checking the current source and the private test metadata under
`~/.local/state/rock-band-linux/lane-tests/20261114T035032.661356Z/test.json`.
Restart the temporary navigation service before launching that profile. Keep
the accepted 45% opacity; finish target alignment using annotated screenshots
and measurements, then verify remaining hit feedback and practice behavior.
The normal workstation installation has not received this prototype.

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
