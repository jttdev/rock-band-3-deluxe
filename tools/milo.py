#!/usr/bin/env python3
"""Inspect Milo archives using the pinned MiloLib reader."""

import argparse
from pathlib import Path
import subprocess

from bootstrap import ROOT, dotnet


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["inspect"])
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    sdk = dotnet()
    dll = ROOT / "tools/MiloTool/bin/Release/net10.0/MiloTool.dll"
    if not sdk or not dll.exists():
        parser.error("Run python3 tools/bootstrap.py first")
    subprocess.run([sdk, str(dll), args.command, str(args.source.resolve()),
                    str(args.output.resolve())], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
