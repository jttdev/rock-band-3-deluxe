# Latency

Where the delay between a hit, the picture and the sound comes from on this
workstation, which tracked settings shorten it, and how to check them.
Calibration hides a constant delay for scoring only; see [projector](projector.md)
for what it cannot compensate.

## Audio path

RPCS3 → cubeb `pulse` backend → pipewire-pulse → PipeWire graph → ALSA →
MOTU M4 (`…HiFi__Line1__sink`, "Headphone + Monitor Out") at 48 kHz.

| Stage | Tracked setting | Size | RPCS3 defaults |
| --- | --- | --- | --- |
| RPCS3 ring buffer | `Desired Audio Buffer Duration: 22` in the game config | 22 ms | 34 ms |
| pipewire-pulse stream buffer | `PULSE_LATENCY_MSEC=12` in `scripts/rock-band-3` | 9 ms (432 frames) | 18.75 ms (900 frames) |
| PipeWire graph cycle | `config/pipewire/rock-band-rpcs3.conf` | 128 frames, 2.7 ms | 256 frames, 5.3 ms |
| M4 ALSA buffer | none | about 4 ms | about 8 ms |
| USB and converter | none | 1-2 ms | 1-2 ms |

That is roughly 39 ms against 67 ms. How the pieces behave:

- cubeb asks PulseAudio for a fixed 25 ms buffer and RPCS3 cannot change it.
  libpulse replaces that request with `PULSE_LATENCY_MSEC`; pipewire-pulse keeps
  part of it as stream buffer and turns the rest into the graph cycle length.
- pipewire-pulse does not let a client go below 256 frames. The rule in
  `config/pipewire/rock-band-rpcs3.conf` lowers that floor to 128 frames for
  RPCS3 only. It changes nothing by itself: without the launcher's variable
  RPCS3 keeps the 25 ms request, so other PS3 games and desktop audio are
  unaffected. With the variable but without the rule the stream buffer is
  11.3 ms and the cycle stays at 256 frames.
- RPCS3 never buffers less than its callback length plus two audio blocks,
  about 21 ms. Values below 22 have no effect while `Enable Buffering` is on.
- PipeWire keeps one cycle plus half a cycle of headroom in a USB device's
  buffer. The M4 row is derived from that rule in the PipeWire source, not
  measured.
- The Pro Audio profile does not shorten this path; the UCM HiFi profile stays.
- Realphones mode forces the whole graph to 1024 frames (21 ms). Keep it off
  while playing.

RPCS3 has no backend setting. cubeb tries pulse, JACK, sndio and ALSA in that
order; its ALSA backend asks for at least 40 ms, so direct ALSA is slower.
Running RPCS3 under `pw-jack` with the Pulse server hidden would skip the
stream buffer (about 9 ms). That is untested here.

## Video path

The game runs windowed through XWayland with RPCS3 VSync disabled, so KWin
shows the newest finished frame at each display refresh.

- `Frame limit: 120` in the game config lets RPCS3 render up to 120 fps, so
  the newest frame is at most 8 ms old instead of 17 ms.
- The limit only matters with Deluxe's own Vsync off: Options → Deluxe Settings
  → Venue Options → Graphics → Advanced → **Vsync: OFF**. With it on the game
  locks itself to 60 fps. This is a save setting outside git. The FPS counter
  in the same Deluxe settings shows the result.
- `Vblank Rate` stays at 60; MiloHax reports online disconnects above it.
- Fullscreen stays off on this workstation (see [setup](setup.md)), so the
  compositor remains in the path.

## Check and tune

Run `scripts/latency-report` while a song plays. With the tracked settings it
shows backend `pulse`, a 9.0 ms stream buffer, `QUANT 128` on the M4 sink and
`ERR 0`.

Crackling means a buffer ran empty. Raise one value at a time:

1. `PULSE_LATENCY_MSEC=16 rock-band-3` for a single launch: 12 ms stream
   buffer, and 20 gives 15 ms. From 24 (18 ms) the cycle is back at 256 frames.
2. `Desired Audio Buffer Duration` towards 32, the MiloHax starting point.
3. If `ERR` keeps counting and the report lists PipeWire's `data-loop` threads
   as `TS`, PipeWire runs without realtime priority. The fix is host setup
   (`pipewire` group membership), tracked in beads `dev-utqzt`.

Recalibrate after every change to these values, the display or the audio
route. Deluxe adjusts audio and video offsets during a song and has a
"Calibration Mode" modifier with a very small hit window.

## Verification

On 2026-11-20 the stream buffer and cycle figures for both columns were measured
with PipeWire 1.6.2 on the workstation, using a test client that sends cubeb's
request to a private PipeWire instance with the tracked rule. RPCS3's logs of
two sessions on the M4 show the same buffers: 900 frames with its default
settings, 432 frames with the tracked ones. The user confirms play with the
tracked settings and a recalibration with clearly lower offsets; the offsets
and a `latency-report` during play (cycle length, xruns) are not recorded.

## Sources

- RPCS3: [CubebBackend.cpp](https://github.com/RPCS3/rpcs3/blob/master/rpcs3/Emu/Audio/Cubeb/CubebBackend.cpp),
  [cellAudio.cpp](https://github.com/RPCS3/rpcs3/blob/master/rpcs3/Emu/Cell/Modules/cellAudio.cpp)
- cubeb: [backend order](https://github.com/mozilla/cubeb/blob/master/src/cubeb.c),
  [pulse backend](https://github.com/mozilla/cubeb/blob/master/src/cubeb_pulse.c)
- PipeWire 1.6.2: [pulse buffer attributes](https://github.com/PipeWire/pipewire/blob/1.6.2/src/modules/module-protocol-pulse/pulse-server.c),
  [ALSA headroom](https://github.com/PipeWire/pipewire/blob/1.6.2/spa/plugins/alsa/alsa-pcm.c)
- MiloHax: [audio](https://guides.milohax.org/en/rb3pc/customconfig/audio/),
  [GPU](https://guides.milohax.org/en/rb3pc/customconfig/gpu/),
  [troubleshooting](https://guides.milohax.org/en/rb3pc/troubleshooting/)
- Reddit: [RPCS3 lag](https://www.reddit.com/r/Rockband/comments/1o1rc6b/how_is_the_lag_with_emulators_rcps3xenia_between/),
  [PipeWire low-latency guide](https://www.reddit.com/r/rhythmgames/comments/1gamrnc/low_latency_guide_for_linux_using_pipewire/)
