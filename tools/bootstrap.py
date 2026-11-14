#!/usr/bin/env python3
"""Initialize the development dependencies without the optional character pack."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
SDK_HOME = Path.home() / ".local/share/rb3-dev/dotnet"


def dotnet():
    local = SDK_HOME / "dotnet"
    return str(local) if local.exists() else shutil.which("dotnet")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install-dotnet", action="store_true",
                        help="install the pinned SDK into ~/.local/share/rb3-dev/dotnet")
    args = parser.parse_args()
    subprocess.run(["git", "submodule", "update", "--init", "--depth", "1",
                    "third_party/rb3-engine-reference", "third_party/MiloLib"],
                   cwd=ROOT, check=True)
    if args.install_dotnet:
        version = json.loads((ROOT / "global.json").read_text())["sdk"]["version"]
        with tempfile.TemporaryDirectory(prefix="rb3-dotnet-") as tmp:
            installer = Path(tmp) / "dotnet-install.sh"
            urllib.request.urlretrieve("https://dot.net/v1/dotnet-install.sh", installer)
            subprocess.run(["bash", str(installer), "--version", version,
                            "--install-dir", str(SDK_HOME), "--no-path"], check=True)
    sdk = dotnet()
    if not sdk:
        parser.error(".NET 10 SDK missing; rerun with --install-dotnet")
    env = dict(os.environ, DOTNET_CLI_TELEMETRY_OPTOUT="1",
               DOTNET_SKIP_FIRST_TIME_EXPERIENCE="1")
    subprocess.run([sdk, "build", str(ROOT / "tools/MiloTool/MiloTool.csproj"),
                    "--configuration", "Release", "--nologo"],
                   cwd=ROOT, env=env, check=True)
    print("Ready: python3 tools/milo.py --help")


if __name__ == "__main__":
    main()
