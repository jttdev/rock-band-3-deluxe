# EFNOTE drum commissioning

The connected kit is reported by the user as an **EFNOTE 3B**; the exact module
label and firmware version remain unconfirmed. [roland.md](roland.md) covers an
uncommissioned alternative.

## Connections and module settings

- Module MIDI OUT → CME C2MIDI Pro → laptop USB.
- RPCS3 I/O emulates a MIDI Pro Adapter of type **Drums**.
- RtMidi input: `C2MIDI Pro:C2MIDI Pro MIDI 1 28:0` on this workstation;
  the numeric ALSA address depends on device connection order.
- Module **Settings → MIDI Ch: 10**, so all pads transmit on channel 10.
- Audio: RPCS3 → MOTU M4 stereo at 48 kHz.
- Menu controller: Bluetooth SN30 Pro in XInput mode, standard gamepad profile
  on RPCS3 Player 2; Deluxe Navigation Pad = Player 2.

EFNOTE Multi mode assigns different channels to different pads; kick was observed
on channel 1 and snare on channel 2. RPCS3's drum adapter accepts note-on messages
on channel 10. Snare 38 and kick 36 were both verified on channel 10 after setting
the module's MIDI Ch to 10.

The ALSA client number in the RtMidi name can change after reconnecting devices.
If RPCS3 reports that it cannot find the device, reselect the CME input under the
US game's custom I/O configuration. Use `aconnect -l` to inspect current ports.

## Measured notes

| Playing surface | Observed note | Rock Band input |
| --- | --- | --- |
| Snare centre / tested rim | 38 / 37 | Red drum |
| Kick | 36 | Kick |
| Left/high tom head / rim | 48 / 50 | Yellow drum |
| Middle tom head / rim | 45 / 47 | Blue drum |
| Floor tom head / rim | 43 / 58 | Green drum |
| Closed hi-hat surface / edge | 42 / 22 | Yellow cymbal |
| Open hi-hat surface | 46 | Yellow cymbal |
| Hi-hat pedal | CC4 0–127, note 44 | Pedal/navigation |
| Ride surface / bell / edge | 51 / 53 / 59 | Blue cymbal |
| Left crash surface / tested bell strikes | 49 | Green cymbal |
| Right crash surface / bell | 57 / 56 | Green cymbal |

The tracked `rb3drums.yml` has the measured overrides
`56=Crash,58=FloorTom,255=HihatPedal`. Note 56 is the right crash bell and would
otherwise be treated as a ride. Note 58 is the floor-tom rim and is not in RPCS3's
default map. Note 255 is RPCS3's internal event for a CC threshold crossing, not a
physical MIDI note.

The hi-hat pedal sends CC4 on channel 10, with 0=open and 127=closed. The drum
configuration uses `Midi CC status: 185` (0xB9, channel 10), CC number 4,
threshold 64 and normal polarity. Its synthetic CC event maps to `HihatPedal`,
so it provides navigation combos without generating a kick. Most physical pedal
note-44 events had velocity 1 and would be dropped by the minimum-velocity filter.

Pulse width is 30 ms, minimum velocity is 10, and cymbal staggering remains enabled.
Weak incidental pedal/motion notes below 10 were observed. Open-hi-hat/splash
notes 46 at velocities 14–21 also occurred during pedal-only movement; check for
unwanted hits during playing before changing sensitivity or crosstalk settings.

The raw measurement captures are outside git under
`~/.local/state/rock-band-linux/hardware/efnote-*.json`.

## Gamepad navigation and initial sign-in

The US input profile leaves Player 1 empty for the MIDI adapter's LDD controller
and assigns the SN30 Pro to Player 2. The local Deluxe settings file uses
`dx_nav_controller_port = 1` (zero-based Player 2). The global RPCS3 input profile
still assigns the SN30 Pro to Player 1 for other games.

The game launcher sets `SDL_JOYSTICK_LINUX_CLASSIC=1`. The classic joystick
endpoint avoids an `eventN` path that changes as USB/Bluetooth
devices reconnect. With both guitars connected first, they occupy `js0`/`js1`
and the SN30 occupies `js2`; RPCS3 selects the SN30 by its SDL name.
RPCS3's SDL backend matches both name and path when reattaching
an existing controller. The current custom SDL database entry supplies the
mapping for the classic endpoint in XInput mode, including Start and Select.

Measured XInput button indices are bottom B=0, right A=1, left Y=2, top X=3,
L=4, R=5, Select=6, Start=7 and left-stick click=8. Right-stick click uses the
remaining digital button 9; that individual click has not been isolated in the
capture. Stick axes are 0/1 and 3/4; trigger axes are 2/5. D-pad uses hat 0.

Deluxe's navigation pad controls the local session leader. Join drums before
either guitar so the SN30 navigates the drummer's menus; if bass joins first,
the navigation pad can control bass instead. Hit a tom at the title screen to
join as the MIDI drummer, then use the SN30 Pro to navigate.

`scripts/sn30-drum-start.py` sends the drum Start sequence when Start is pressed
on the SN30 Pro. The launcher does not start it: the user reports that the game
crashes when launched with it. The cause has not been investigated.

## Verification and calibration

Pad heads, tested rims, cymbal surfaces/edges/bells and pedal CC have been measured.
The left crash bell/edge tests stayed on note 49; right crash edge tests stayed on
57. No separate left-crash bell note was observed.
The kit was observed scoring hits in Pro Drums during the DLC song "1901".
The unused microphone "Start / Join" prompt
is an available slot, not a joined vocals player. The user confirms calibration
and a full-song playthrough are complete, and that calibration was repeated with
the [low-latency settings](latency.md). Numeric calibration offsets have not
been supplied; calibration remains in the local game save outside git.

Full menu coverage after joining, fast rolls, simultaneous hits and reconnect
persistence still need explicit verification. Recalibrate after changing the
display or audio route; use the external display and the M4's wired output.

References: [EFNOTE 3/5/7 guide](https://ef-note.com/products/drums/common357/EFNOTE_3_5_7_RG_en04.pdf)
and [MiloHax MIDI setup](https://guides.milohax.org/en/rb3pc/controllers/drums/midi/).
