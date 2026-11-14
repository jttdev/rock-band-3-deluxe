# Configurable drum lanes

The requested EFNOTE layout, from left to right, is **hi-hat, snare, high tom,
middle tom, ride, floor tom, crash**, with a full-width kick bar. The menu must
offer the standard shared-lane highway and separate cymbal lanes, remember the
selection, and allow changing the order. Both crash cymbals send the chart's
green-cymbal part; the chart cannot distinguish left and right crashes.

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

Separate cymbal lanes and their menu are not yet implemented or verified in
RPCS3. The workstation installation remains the known working Deluxe build.
