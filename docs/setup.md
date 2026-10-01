# Setup and workstation reference

## Installed baseline

Verified on 2026-10-01 on `jt-TPP16`: Core i9-12950HX, 64 GB RAM,
NVIDIA RTX A4500 Laptop GPU. RPCS3 `0.0.43-20133-53d44aa4`, Sony firmware 4.93.

US Rock Band 3 (`BLUS30463`) is registered from
`~/Games/Roms/PS3/Rock Band 3 (USA) (En,Fr,De,Es,It)/`.
Deluxe build `2afbd3e` is installed in RPCS3's virtual HDD and reports APP_VER 01.05.
The log confirms boot from its updated EBOOT and loading the keyboard drum profile.
The user reported reasonable song performance in the earlier European vanilla
copy; sustained US Deluxe gameplay and real drums have not yet been validated.

## Rebuild

1. Download the official Linux AppImage from <https://rpcs3.net/download>.
   Store it at `~/.local/opt/rpcs3/RPCS3.AppImage`, mark executable, and install
   this repository's launcher as `~/.local/bin/rpcs3`.
   `APPIMAGELAUNCHER_DISABLE=1` avoids this host's incompatible AppImageLauncher
   registration; `QT_QPA_PLATFORM=xcb` uses XWayland.
2. Follow <https://rpcs3.net/quickstart> to install official Sony firmware.
3. Add the extracted US disc folder to RPCS3. Configure `/games/` in its virtual
   filesystem if desired; local game paths are intentionally not tracked here.
4. Download the PS3 main build from <https://rb3dx.milohax.org/downloads/>.
   Install the extracted PKG through File → Install Packages/Raps/Edats.
   See <https://rb3dx.milohax.org/install/> for current requirements.
5. Close RPCS3, apply this repository's configuration, and reopen it. Choose the
   local Vulkan adapter if needed; its hardware-specific name is not tracked.

Tracked settings include Vulkan/720p, Cubeb stereo with a 34 ms requested buffer,
the game's Write Color Buffers override, keyboard drum input, and the bundled
`Darker Style by TheMitoSan` theme. The buffer duration is a baseline, not a
measurement of end-to-end latency. The dark theme avoids white text on the
default stylesheet's white toolbar and game-list backgrounds under KDE dark mode.

The headless package installer on this build reports a teardown error after
logging successful installation. Check the success log and installed files, then
verify GUI boot; a nonzero exit alone does not establish installation failure.

## Local assets (outside git)

- Firmware: `~/Games/Firmware/PS3/PS3UPDAT.PUP`
- Deluxe installer: `~/Games/Mods/RB3Deluxe/`
- Live emulator configuration and virtual HDD: `~/.config/rpcs3/`
- Logs and shader caches: `~/.cache/rpcs3/`

Install US-compatible DLC packages and their corresponding licences through the
package menu. Neither DLC nor licences belong in git. Do not confuse chart
upgrades included in Deluxe with the songs themselves. Saves and calibration
stored inside game saves need a separate local backup; this repo does not capture
the virtual HDD, accounts, saves or Deluxe in-game settings.
