#!/usr/bin/env python3
"""Locate expert Pro Drums tom passages in a locally installed RB3 chart."""

import argparse
import bisect
from collections import Counter
import json
from pathlib import Path
import struct


def ark_file(header, wanted):
    raw = header.read_bytes()
    seed = abs(struct.unpack_from("<i", raw)[0]) or 1
    data = bytearray()
    for byte in raw[4:]:
        seed = seed * 16807 % 2147483647
        data.append(byte ^ (seed & 255))
    if struct.unpack_from("<I", data)[0] != 6:
        raise ValueError("Expected an RB3 version-6 archive")
    position = 24  # version plus versioned HxGuid

    def integer():
        nonlocal position
        value, = struct.unpack_from("<I", data, position)
        position += 4
        return value

    integer()  # number of archive files
    sizes = [integer() for _ in range(integer())]
    names = []
    for _ in range(integer()):
        size = integer()
        names.append(bytes(data[position:position + size]).decode())
        position += size
    priorities = integer()
    position += 4 * priorities
    size = integer()
    strings = data[position:position + size]
    position += size
    offsets = [integer() for _ in range(integer())]

    def string(index):
        start = offsets[index]
        return bytes(strings[start:strings.index(0, start)]).decode()

    for _ in range(integer()):
        offset, name, folder, size, unpacked = struct.unpack_from("<Q4I", data, position)
        position += 24
        path = string(folder) + "/" + string(name)
        if path != wanted:
            continue
        if unpacked not in (0, size):
            raise ValueError("Compressed chart entries are unsupported")
        boundaries, total = [], 0
        for length in sizes:
            total += length
            boundaries.append(total)
        chunks, remaining = [], size
        while remaining:
            index = bisect.bisect_right(boundaries, offset)
            start = offset - (boundaries[index - 1] if index else 0)
            length = min(remaining, sizes[index] - start)
            with (header.parent.parent / names[index]).open("rb") as stream:
                stream.seek(start)
                chunk = stream.read(length)
            if len(chunk) != length:
                raise ValueError("Truncated archive entry")
            chunks.append(chunk)
            offset += length
            remaining -= length
        return b"".join(chunks)
    raise ValueError(f"Chart not found: {wanted}")


def midi_events(data):
    if data[:4] != b"MThd":
        raise ValueError("Expected a standard MIDI file")
    length, = struct.unpack_from(">I", data, 4)
    _, tracks, division = struct.unpack_from(">3H", data, 8)
    if division & 0x8000:
        raise ValueError("SMPTE MIDI timing is unsupported")
    cursor, result = 8 + length, []
    for _ in range(tracks):
        if data[cursor:cursor + 4] != b"MTrk":
            raise ValueError("Missing MIDI track")
        size, = struct.unpack_from(">I", data, cursor + 4)
        cursor += 8
        end, tick, running, name, events = cursor + size, 0, 0, "", []

        def variable():
            nonlocal cursor
            value = 0
            for _ in range(4):
                byte = data[cursor]
                cursor += 1
                value = value * 128 + (byte & 127)
                if not byte & 128:
                    return value
            raise ValueError("Invalid MIDI variable length")

        while cursor < end:
            tick += variable()
            status = data[cursor]
            if status & 128:
                cursor += 1
            else:
                status = running
            if status == 0xFF:
                kind = data[cursor]
                cursor += 1
                size = variable()
                payload = data[cursor:cursor + size]
                cursor += size
                if kind == 3:
                    name = payload.decode(errors="replace")
                elif kind == 0x51:
                    events.append((tick, "tempo", int.from_bytes(payload, "big")))
                elif kind == 1 and (payload.startswith(b"[prc_") or payload.startswith(b"[section ")):
                    events.append((tick, "section", payload.decode(errors="replace")))
            elif status in (0xF0, 0xF7):
                size = variable()
                cursor += size
            elif 0x80 <= status < 0xF0:
                running = status
                count = 1 if status & 0xF0 in (0xC0, 0xD0) else 2
                payload = data[cursor:cursor + count]
                cursor += count
                if status & 0xF0 in (0x80, 0x90):
                    events.append((tick, "on" if status & 0xF0 == 0x90 and payload[1] else "off", payload[0]))
            else:
                raise ValueError(f"Unsupported MIDI status {status:x}")
        result.extend((tick, name, kind, value) for tick, kind, value in events)
    return division, result


def summarize(data):
    division, events = midi_events(data)
    tempo, previous, seconds, section = 500000, 0, 0.0, ""
    active, counts, passages = set(), Counter(), []
    # Tom markers at the same tick apply to that tick's notes.
    for tick, track, kind, value in sorted(events, key=lambda row: (row[0], 0 if row[3] in (110, 111, 112) else 1)):
        seconds += (tick - previous) * tempo / division / 1000000
        previous = tick
        if kind == "tempo":
            tempo = value
        elif kind == "section":
            section = value
        elif track == "PART DRUMS":
            if value in (110, 111, 112):
                (active.add if kind == "on" else active.discard)(value)
            elif kind == "on" and value in range(96, 101):
                part = {96: "kick", 97: "snare", 98: "high_tom" if 110 in active else "hihat",
                        99: "middle_tom" if 111 in active else "ride",
                        100: "floor_tom" if 112 in active else "crash"}[value]
                counts[part] += 1
                if part.endswith("_tom"):
                    passages.append(dict(seconds=round(seconds, 3), part=part, section=section))
    return dict(counts=dict(counts), tom_passages=passages)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("header", type=Path)
    parser.add_argument("song", help="disc song identifier, for example 20thcenturyboy")
    args = parser.parse_args()
    print(json.dumps(summarize(ark_file(args.header, f"songs/{args.song}/{args.song}.mid")), indent=2))


if __name__ == "__main__":
    main()
