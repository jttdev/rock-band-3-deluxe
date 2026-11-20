# Projector

Selected display: BenQ TH671ST (1080p short-throw DLP, lamp), ceiling mounted.
It also serves projection visuals (Resolume / TouchDesigner style VJ work).
Offer on 2026-11-13: refurbished, new lamp, 2-year warranty, about 500 USD.
Not purchased yet. Every latency figure below is a published spec or a
third-party test; nothing has been measured on this workstation.

## Why this model

Rock Band needs low display lag and a picture nobody stands in front of; the
visuals need brightness in a dark room. A short-throw projector hangs between
the players and the wall, so the band casts no shadows.

| | BenQ TH671ST | Optoma GT1090HDR | Epson EB-2250U |
| --- | --- | --- | --- |
| Lag, 1080p60 | ~16 ms, Fast Mode (~50 ms off) | ~16 ms, Enhanced Gaming (32 ms off) | no published measurement |
| Lag, 1080p120 | 8.3 ms (spec) | 8 ms (spec) | n/a |
| Brightness | 3,000 lm | 4,200 lm | 5,000 lm white and colour |
| Imaging, light | DLP, lamp | DLP, laser 20,000-30,000 h | 3LCD, lamp 5,000-10,000 h |
| Resolution | 1920x1080 | 1920x1080 | 1920x1200 |
| Throw ratio | 0.69-0.83, 1.2x zoom | 0.5 fixed, no zoom | 1.38-2.28, 1.65x zoom |
| Lens shift | none | none | none |
| Price seen | ~500 USD refurbished | ~1,000 USD | 150 USD used |

- **GT1090HDR**: same lag at twice the price, and the fixed lens leaves no slack
  for the mount position. Early units need a firmware update from Optoma support
  to get Enhanced Gaming, and that mode disables keystone. It earns its price
  only in a room that cannot be darkened, for images wider than about 3 m, or
  for gigs.
- **EB-2250U** (PowerLite 2250U in the US): the stronger projector for visuals.
  Colour brightness equals white brightness, there is no colour wheel (no
  rainbow artefacts, clean on camera) and the lamp is cheap. Its lag is
  unmeasured (guesses for this class start at 40 ms) and the standard throw
  puts standing players in the beam. Candidate second projector for visuals.
- **Optoma GT2100HDR** is not a substitute for the GT1090HDR: Tom's Guide
  measured 24-28 ms in gaming mode against a 17 ms spec.

## Low-lag settings

- Fast Mode on. BenQ documents two routes for the sibling TH685: the Game
  picture mode enables it, or Picture → Advanced → Fast Mode. Confirm the menu
  names on the unit.
- Keystone at 0 and aspect ratio on auto. BenQ states the 16 ms figure only
  with keystone at 0, and non-default values conflict with Fast Mode. Overscan
  and aspect ratio grey out while Fast Mode is on.
- Desktop output at the native 1920x1080 so the projector's scaler stays idle.
  A 120 Hz output selects the 8.3 ms mode; this is inferred from the spec and
  untested with RPCS3. The game's frame limit is 120 fps ([latency](latency.md)).
- Audio through a wired analog output, never HDMI audio via the projector, a
  soundbar or Bluetooth.
- Calibrate audio and video with this display and the final audio route, as
  required in [EFNOTE commissioning](efnote.md). Deluxe can shift calibration
  live during a song. Calibration moves the note highway only: drum fills,
  overdrive activation and microphone monitoring keep the full latency, which
  is why real display lag matters for drums and vocals.
- Reported RPCS3 totals are 20-60 ms depending on the audio buffer, the audio
  output path and the instrument connection. [Latency](latency.md) has this
  workstation's audio path stage by stage.

## Ceiling mount

- Lens-to-wall distance = throw ratio x image width. A 2.5 m wide image needs
  1.73-2.08 m. Clear focus covers 60-120 inch diagonals (1.33-2.66 m wide).
- No lens shift; projection offset is 102.5 % +/- 2.5 %, so the mount height
  sets where the picture sits. Online offset calculators have been wrong for
  similar short-throw models.
- Mount it physically square to the wall. Keystone must stay at 0.
- Run it from a ladder or shelf at the planned spot before drilling.
- Leave room to take it down: the lamp is replaced with the projector off the
  mount. Owners report 6,000-8,000 h per lamp; replacements cost about
  100-236 EUR. SmartEco extends lamp life.

## Checks on arrival

- Lamp hour counter near zero.
- Full-white and full-black frames show no dust blobs or spots.
- Fast Mode is present and selectable.
- Who backs the warranty, and whether it covers the lamp.

## Visuals

- r/vjing guidance: about 3,000 lm is enough in a dark room at home, 5,000 lm
  and more for gigs; favour brightness over resolution and name brands.
- Low projector lag helps live and audio-reactive visuals as well.
- Warp and map in the VJ software and leave the projector's keystone at 0.
- The DLP colour wheel can show as rainbow flashes on fast, bright content and
  as flicker or banding on camera. Filming the projection is the case for the
  3LCD EB-2250U.

## Unverified

- The only independent TH671ST lag test found is Gagadget's (16.4 ms with Fast
  Mode); BenQ specifies 16.7 ms. RTINGS reviewed both DLP models but its pages
  could not be retrieved.
- Reddit claims about an EU phase-out of mercury projector lamps conflict;
  Epson states its replacement lamps remain available.
- No lag data exists for the EB-2250U.

## Sources

- BenQ: [TH671ST specifications](https://www.benq.eu/en-eu/projector/cinema/th671st/spec.html),
  [enabling low input lag](https://www.benq.eu/en-uk/support/downloads-faq/faq/product/application/projector-faq-k-00087.html),
  [keystone with Fast Mode](https://www.benq.eu/en-eu/support/downloads-faq/faq/product/explanation/projector-faq-k-00030.html),
  [GameMaestro flicker](https://www.benq.com/en-us/support/downloads-faq/faq/product/troubleshooting/projector-faq-kn-00025.html)
- TH671ST tests: [Gagadget](https://gagadget.com/en/727238-benq-th671st/),
  [ProjectorCentral](https://www.projectorcentral.com/BenQ-TH671ST.htm)
- GT1090HDR: [Optoma spec sheet](https://www.optomausa.com/ContentStorage/Documents/8f60d081-410e-4bfd-abc5-a0a2bdcd52f1.pdf),
  [Optoma product manager on lag and firmware](https://www.reddit.com/r/projectors/comments/fuvqfs/gt1080hdr_vs_gt1090hdr/),
  [Enhanced Gaming disables keystone](https://www.reddit.com/r/projectors/comments/kt67rk/optoma_gt1090hdr_enhanced_gaming_mode_distorts/)
- GT2100HDR: [Tom's Guide](https://www.tomsguide.com/reviews/optoma-gt2100hdr)
- EB-2250U: [ProjectorCentral](https://www.projectorcentral.com/Epson-PowerLite_2250U.htm),
  [r/vjing comparison](https://www.reddit.com/r/vjing/comments/939uxl/narrowed_down_my_projector_buy_to_3_choices_can/)
- Rock Band: [RPCS3 lag](https://www.reddit.com/r/Rockband/comments/1o1rc6b/how_is_the_lag_with_emulators_rcps3xenia_between/),
  [low-latency projectors](https://www.reddit.com/r/Rockband/comments/1x542sg/affordable_projectors_with_low_latency/)
- Owners: [used TH671ST](https://www.reddit.com/r/projectors/comments/1f69p3t/second_hand_benq_th671st/),
  [TH671ST vs GT2100HDR](https://www.reddit.com/r/Golfsimulator/comments/1h635k0/benq_th671st_vs_optoma_gt2100hdr/)
- r/vjing: [entry-level projectors](https://www.reddit.com/r/vjing/comments/12sskxn/best_entry_level_projectors/),
  [low lag for live visuals](https://www.reddit.com/r/vjing/comments/1wj4gx5/120240_hz_projectors/),
  [TH671ST recommendation](https://www.reddit.com/r/vjing/comments/1ssn9fb/projector_recommendations/)
