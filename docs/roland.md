# Roland drum commissioning

Target: TD316 / V31. The kit has not been connected or tested on this workstation.
`aconnect -l` currently shows no Roland MIDI port. No hardware-specific mapping
is applied until its actual events and port name can be inspected.

## Connection

The V31 supports an OS-standard GENERIC USB driver mode with MIDI and two-channel
USB audio. Select it for the initial Linux USB test; consult the module's restart
instructions after changing the setting. Linux interoperability here still needs
hardware verification.

Sources: [Roland TD316](https://www.roland.com/us/products/td316/) and
[V31 USB driver settings](https://static.roland.com/manuals/v31_reference_v200/en-US/409622411412947723.html).

Use a USB data cable from USB COMPUTER to the laptop. If USB does not expose a
usable MIDI port, a supported USB MIDI interface connected to MIDI OUT is an
alternative. Confirm discovery with `lsusb` and `aconnect -l`; use
`aseqdump -p CLIENT:PORT` with the reported port to observe hits.

## RPCS3 and game

Use channel 10 and standard GM notes as a starting point. In Rock Band 3's custom
configuration, select I/O → Emulated MIDI Devices → Drums and the discovered port.
Do not map the real kit in Pads. Enable Pro Drums in the game and test tom/cymbal
distinction. Keep keyboard/gamepad menu navigation available; Deluxe provides a
Navigation Pad option. The existing keyboard-as-drums profile is only a fallback,
not the final navigation profile for MIDI play.

Follow the [MiloHax MIDI guide](https://guides.milohax.org/en/rb3pc/controllers/drums/midi/)
for note mappings and `rb3drums.yml` options. After validation, add the generated
MIDI configuration and measured overrides to the tracked configuration explicitly;
the capture script deliberately does not discover or copy arbitrary new files.

## Acceptance checks with the kit

- Record module firmware, USB mode, port name, MIDI channel, and each pad's notes.
- Check every head, rim, cymbal zone, kick and hi-hat pedal separately.
- Check quiet hits, fast rolls, simultaneous kick/snare and cymbal combinations.
- Resolve duplicate hits and crosstalk at the module before compensating in software.
- Pick and record an audio route: laptop/interface wired output or module USB audio
  if verified. Avoid Bluetooth for timing tests. Decide whether module sounds or
  game drum sounds will be monitored to avoid distracting doubled hits.
- Calibrate audio and video with the final display and audio route. Record both
  offsets, buffer setting, and any minimum velocity adjustment here.
- Play several complete songs, then reconnect the kit and restart RPCS3 to check
  discovery, mapping persistence, and navigation.

Do not claim completion from a keyboard test. Device mapping, monitoring route,
calibration offsets and sustained-play results remain unmeasured.
