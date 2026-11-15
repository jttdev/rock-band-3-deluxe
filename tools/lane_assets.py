#!/usr/bin/env python3
"""Add separate-lane widgets while preserving the existing Milo object payload."""

import argparse
import base64
import bisect
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import zlib

from bootstrap import ROOT, dotnet

END = bytes.fromhex("addeadde")
MILO_A, MILO_B, MILO_C, MILO_D = range(0xCABEDEAF, 0xCEBEDEAF, 0x1000000)


def unpack(data):
    magic, offset, count, _largest = struct.unpack_from("<4I", data)
    if magic not in (MILO_A, MILO_B, MILO_C, MILO_D):
        raise ValueError("Unsupported Milo container")
    if not count or 16 + count * 4 > offset or offset > len(data):
        raise ValueError("Invalid Milo block table")
    sizes = struct.unpack_from(f"<{count}I", data, 16)
    cursor, chunks = offset, []
    for encoded_size in sizes:
        size = encoded_size & 0xFFFFFF
        block = data[cursor:cursor + size]
        if len(block) != size:
            raise ValueError("Truncated Milo block")
        cursor += size
        if magic == MILO_B:
            block = zlib.decompress(block, -15)
        elif magic == MILO_C:
            block = zlib.decompress(block, 31)
        elif magic == MILO_D and not encoded_size & 0xFF000000:
            expected, = struct.unpack_from("<I", block)
            block = zlib.decompress(block[4:], -15)
            if len(block) != expected:
                raise ValueError("Milo block size mismatch")
        chunks.append(block)
    if cursor != len(data):
        raise ValueError("Unexpected trailing data after Milo blocks")
    return b"".join(chunks), [len(block) for block in chunks], offset


def root_table(body, start=0):
    cursor = start + 4

    def string():
        nonlocal cursor
        size, = struct.unpack_from(">I", body, cursor)
        cursor += 4
        if size > 65536 or cursor + size > len(body):
            raise ValueError("Invalid directory string")
        value = body[cursor:cursor + size].decode("latin-1")
        cursor += size
        return value

    revision, = struct.unpack_from(">I", body, start)
    kind, name = string(), string()
    if revision != 28 or kind != "GemTrackDir":
        raise ValueError("Expected a big-endian revision-28 GemTrackDir")
    hints = cursor
    hashes, strings, count = struct.unpack_from(">3I", body, cursor)
    cursor += 12
    if count > 10000:
        raise ValueError("Unexpected directory entry count")
    entries = [(string(), string()) for _ in range(count)]
    return hints, hashes, strings, name, entries, cursor


def encode_string(value):
    data = value.encode("latin-1")
    return struct.pack(">I", len(data)) + data


def append_objects(original, manifest):
    if hashlib.sha256(original).hexdigest() != manifest["sourceSha256"]:
        raise ValueError("Manifest belongs to a different source archive")
    body, sizes, offset = unpack(original)
    edits = []
    directories = manifest.get("directories", [dict(manifest, headerOffset=0, endOffset=len(body))])
    for directory in directories:
        hints, hashes, strings, name, entries, table_end = root_table(body, directory["headerOffset"])
        if table_end != directory["dataOffset"] or len(entries) != directory["originalEntries"]:
            raise ValueError("Independent readers disagree about a track directory")
        if not table_end <= directory["endOffset"] <= len(body):
            raise ValueError("Invalid track directory end")
        additions = directory["entries"]
        if not additions:
            continue
        names = {entry_name for _, entry_name in entries}
        header, payloads = bytearray(), []
        for entry in additions:
            if entry["name"] in names:
                raise ValueError(f"Duplicate object name: {entry['name']}")
            names.add(entry["name"])
            header.extend(encode_string(entry["type"]) + encode_string(entry["name"]))
            payloads.append(base64.b64decode(entry["bytes"], validate=True) + END)
        additional_strings = sum(len(entry["name"].encode("latin-1")) + 1 for entry in additions)
        original_strings = sum(len(value.encode("latin-1")) + 1 for _, value in entries) + len(name) + 1
        table = (struct.pack(">3I", max(hashes, 2 * (len(entries) + 1)) + 2 * len(additions),
                             max(strings, original_strings) + additional_strings,
                             len(entries) + len(additions)) + body[hints + 12:table_end] + header)
        edits.extend([(hints, table_end, table),
                      (directory["endOffset"], directory["endOffset"], b"".join(payloads))])
    if not edits:
        return original
    boundaries, total = [], 0
    for size in sizes:
        total += size
        boundaries.append(total)
    chunks, cursor = [], 0
    for start, end, replacement in sorted(edits):
        if start < cursor:
            raise ValueError("Overlapping track directory edits")
        chunks.extend([body[cursor:start], replacement])
        cursor = end
        # Grow the original block containing each edit; every untouched byte
        # retains its original block, including embedded directory boundaries.
        sizes[bisect.bisect_left(boundaries, end)] += len(replacement) - (end - start)
    chunks.append(body[cursor:])
    new_body = b"".join(chunks)
    if 16 + len(sizes) * 4 > offset or max(sizes) > 0xFFFFFF:
        raise ValueError("Additional objects exceed the container's capacity")
    container = bytearray(offset)
    struct.pack_into("<4I", container, 0, MILO_A, offset, len(sizes), max(sizes))
    struct.pack_into(f"<{len(sizes)}I", container, 16, *sizes)
    result = bytes(container) + new_body
    check, _, _ = unpack(result)
    if check != new_body or sum(sizes) != len(new_body):
        raise ValueError("Container block sizes disagree with the edited payload")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("track", type=Path)
    parser.add_argument("meshes", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    sdk = dotnet()
    dll = ROOT / "tools/MiloTool/bin/Release/net10.0/MiloTool.dll"
    if not sdk or not dll.exists():
        parser.error("Run python3 tools/bootstrap.py first")
    if args.output.resolve() == args.track.resolve() or args.output.resolve().is_relative_to(ROOT / "_ark"):
        parser.error("Write generated assets to a build directory, not the source tree")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="drum-lanes-", dir=args.output.parent) as temporary:
        tmp = Path(temporary)
        manifest_file, generated, report_file = tmp / "manifest.json", tmp / "track.milo_ps3", tmp / "inspection.json"
        subprocess.run([sdk, str(dll), "prepare-lanes", str(args.track.resolve()),
                        str(args.meshes.resolve()), str(manifest_file)], check=True, cwd=ROOT)
        manifest = json.loads(manifest_file.read_text())
        generated.write_bytes(append_objects(args.track.read_bytes(), manifest))
        subprocess.run([sdk, str(dll), "inspect", str(generated), str(report_file)], check=True, cwd=ROOT)
        report = json.loads(report_file.read_text())
        directories = {directory["path"]: directory for directory in report["directories"]}
        for directory in manifest["directories"]:
            actual = directories[directory["path"]]
            if len(actual["entries"]) != directory["originalEntries"] + len(directory["entries"]):
                raise ValueError("Generated archive has the wrong object count")
            objects = {entry["name"]: entry for entry in actual["entries"]}
            for entry in directory["preserved"]:
                if objects[entry["name"]]["sha256"] != entry["sha256"]:
                    raise ValueError(f"Existing object payload changed: {directory['path']}/{entry['name']}")
            for entry in directory["entries"]:
                expected = hashlib.sha256(base64.b64decode(entry["bytes"])).hexdigest()
                if objects[entry["name"]]["sha256"] != expected:
                    raise ValueError(f"Generated object differs after reading: {entry['name']}")
        os.replace(generated, args.output)
    count = sum(len(directory["entries"]) for directory in manifest["directories"])
    print(f"Verified {count} new objects; existing payload unchanged: {args.output}")


if __name__ == "__main__":
    main()
