#!/usr/bin/env python3
"""Build the PS3 Deluxe mod with separate, reorderable cymbal lanes."""

import argparse
from pathlib import Path
import subprocess
import sys

from bootstrap import ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not 1 <= args.jobs <= 8:
        parser.error("--jobs must be between 1 and 8")
    if not args.worker:
        subprocess.run(["systemd-run", "--user", "--scope", "-p", "MemoryMax=60%",
                        sys.executable, str(Path(__file__).resolve()), "--worker",
                        "--jobs", str(args.jobs)], check=True, cwd=ROOT)
        return
    subprocess.run([sys.executable, "tools/bootstrap.py"], check=True, cwd=ROOT)
    subprocess.run([sys.executable, "dependencies/python/configure_build.py", "ps3",
                    "--define", "DX_SPLIT_DRUM_LANES"], check=True, cwd=ROOT)
    subprocess.run(["dependencies/linux/ninja", "-j", str(args.jobs)], check=True, cwd=ROOT)
    print(f"Built mod: {ROOT / 'out/ps3'}")


if __name__ == "__main__":
    main()
