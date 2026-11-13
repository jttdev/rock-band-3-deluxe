# Setup and workstation reference

## Installed baseline

Workstation `jt-TPP16`: Core i9-12950HX, 64 GB RAM,
NVIDIA RTX A4500 Laptop GPU. RPCS3 `0.0.43-20133-53d44aa4`, Sony firmware 4.93.

US Rock Band 3 (`BLUS30463`) is registered from
`~/Games/Roms/PS3/Rock Band 3 (USA) (En,Fr,De,Es,It)/`.
Deluxe build `2afbd3e` is installed in RPCS3's virtual HDD and reports APP_VER 01.05.
Boot from its updated EBOOT and partial Pro Drums play with the EFNOTE kit are
verified. Sustained play and measured latency calibration remain pending.

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
6. Install the game launcher and first-Start helper:

   ```sh
   install -Dm755 scripts/rock-band-3 ~/.local/bin/rock-band-3
   install -Dm755 scripts/sn30-drum-start.py ~/.local/share/rock-band-linux/sn30-drum-start.py
   ```

   Rebuild the helper environment as described in [EFNOTE commissioning](efnote.md).
   The launcher uses this workstation's disc path listed above. Set Deluxe's
   Navigation Pad to Player 2 in-game; this save setting is outside git.

Tracked settings include Vulkan/720p, Cubeb stereo with a 34 ms requested buffer,
the game's Write Color Buffers and async multi-threaded shader overrides, the SDL SN30 Pro controller profile, a keyboard drum fallback, and the bundled
`Darker Style by TheMitoSan` theme. The buffer duration is a baseline, not a
measurement of end-to-end latency. The dark theme avoids white text on the
default stylesheet's white toolbar and game-list backgrounds under KDE dark mode.

The headless package installer on this build reports a teardown error after
logging successful installation (`manual_typemap` / "Emulation object is
unavailable"). KDE can show a separate crash notification for every package.
For batch installation, the external installation worker runs the extracted
AppImage (`~/.local/opt/rpcs3/squashfs-root/AppRun`) under batch GDB, with
`QT_QPA_PLATFORM=offscreen`, debuginfod disabled, and confirmation disabled.
GDB stops the shutdown trap and exits without generating a desktop crash report.
Package success must still be checked against RPCS3's explicit success log;
GDB's exit code alone is insufficient. Normal gameplay uses the AppImage directly.
Check installed files and verify GUI boot after installing.

## Local assets (outside git)

- Firmware: `~/Games/Firmware/PS3/PS3UPDAT.PUP`
- Deluxe installer: `~/Games/Mods/RB3Deluxe/`
- Live emulator configuration and virtual HDD: `~/.config/rpcs3/`
- Installed game/update/DLC storage: `~/EXT_MICRON/Rock Band/RB3 Deluxe Installed/game/`,
  linked from `~/.config/rpcs3/dev_hdd0/game`. The external drive must be mounted
  before launching RPCS3. Saves remain in the internal virtual HDD.
- Original installed game folder backup:
  `~/.config/rpcs3/dev_hdd0/game.before-external-20261113-153617/`
- Application-menu shortcut: **Rock Band 3 Deluxe**, using
  `~/.local/bin/rock-band-3`; it checks that external game storage is available.
- Source song packages and inventory spreadsheet:
  `~/EXT_MICRON/Rock Band/`
- Package manifest, per-package installation results and logs:
  `~/EXT_MICRON/Rock Band/RB3 Deluxe Installed/`
- Logs and shader caches: `~/.cache/rpcs3/`

Install US-compatible DLC packages and their corresponding licences through the
package menu. Neither DLC nor licences belong in git. Do not confuse chart
upgrades included in Deluxe with the songs themselves. Saves and calibration
stored inside game saves need a separate local backup; this repo does not capture
the virtual HDD, accounts, saves or Deluxe in-game settings.

## External song library

The active package selection includes RB1/RB3 DLC, RB4 conversions, series
exports, Beatles-to-RB3 conversions, Guitar Hero conversions and original-version
replacements. RBN is excluded from the active library. Extracted RBN folders under
`RB3 Deluxe Installed/disabled-rbn/` are outside RPCS3's scanned game directory;
original RBN packages remain available for a later installation.

`The-Beatles-Rock-Band-DLC.pkg` targets the standalone Beatles game
(`BLUS30282`), so it is excluded from RB3. `TheBeatlesRockBand3.pkg` provides the
RB3-compatible conversion. The supplied RB1 export licence is installed for
RPCS3 user `00000001`.

Song packages can overwrite the shared game's `PARAM.SFO`. Reinstall the local
Deluxe PKG last so the US game's update metadata and executable remain correct.
The installation worker checks RPCS3's success log for each package and retains
both its console output and detailed log on the external drive.

## Library verification

On 2026-11-13, all 38 selected song packages and the final Deluxe package reported
successful installation. Deluxe Quickplay displayed **3,754 songs**. All 3,678
referenced audio/chart paths checked by the external file audit exist (some
catalogues reference alternate charts). No RBN folders are in the active library.
A screenshot and the successful boot log are in `installation-logs/` on the
external drive. A complete song playback test remains unverified.

The game-specific shader mode is `Async Recompiler (multi-threaded)`. The shader
interpreter mode exhibited a black-screen boot and incomplete menus during
validation; the multi-threaded recompiler reached Quickplay. The external
`validation-config.yml` is a diagnostic snapshot; the normal launcher uses the
live game-specific configuration.

The connected EFNOTE mapping and remaining hardware checks are recorded in
[EFNOTE commissioning](efnote.md).

## Bluetooth gamepad

The paired and trusted `8Bitdo SN30 Pro` uses XInput mode (Linux VID/PID
`045e:02e0`). The global profile assigns it to Player 1; the US game profile
reserves Player 1 for the MIDI drum adapter and uses Player 2 for the standard
gamepad, with Deluxe Navigation Pad = Player 2. RPCS3 device name is
`8Bitdo SN30 Pro 1`, with emulated Sony VID/PID `054c:0268` and class type 0.

The game launcher uses `SDL_JOYSTICK_LINUX_CLASSIC=1` and the tracked custom
`input_configs/gamecontrollerdb.txt`. Its measured mapping gives bottom B=Cross,
right A=Circle, left Y=Square and top X=Triangle, plus Start and Select. The
first-Start helper initializes the MIDI drummer. See [EFNOTE commissioning](efnote.md)
for its lifecycle, installation and remaining verification.

`Keyboard Drums.yml` preserves the keyboard drum profile. EFNOTE MIDI input is
configured separately under I/O. Keep the SN30 Pro in XInput mode; its other modes
report different button layouts.

## Shader-cache startup and fullscreen

Shader caching is enabled (`Video → Disable On-Disk Shader Cache: false`). The
US game's `Miscellaneous → Use native user interface: false` override selects
RPCS3's desktop dialogs for emulator prompts and shader loading. Fullscreen
startup remains enabled. The game still uses Vulkan with the multi-threaded
async recompiler and retains its existing shader and CPU/SPU caches.

On this NVIDIA 595.99.02 / KDE XWayland setup, the renderer-drawn shader-loading
screen can hang during a fullscreen display-surface transition. A debugger
backtrace locates the busy RSX thread inside `libnvidia-glcore`, called from
`VKGSRender::reinitialize_swapchain`, `flip`, and
`shader_loading_dialog_native::update_msg`, before cache-loading workers start.
The desktop loading dialog avoids this rendering path while loading the same
cache. The cached shader files do not need to be deleted or disabled.

Three fullscreen launches passed shader preloading with caching enabled and
standard desktop dialogs, including a launch on the external HDMI display at
1920×1080/60 Hz (laptop panel disabled). The original shader cache is retained.
The debugger backtrace, startup logs and external-display title screenshot are
under `installation-logs/` on the external drive. The normal launcher uses the
game-specific overrides automatically.
