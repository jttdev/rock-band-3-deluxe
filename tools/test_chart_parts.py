"""Pro Drums marker and tempo regression checks using an original tiny chart."""

import struct
import unittest

from chart_parts import summarize


def variable(value):
    result = [value & 127]
    while value >> 7:
        value >>= 7
        result.insert(0, (value & 127) | 128)
    return bytes(result)


def track(events):
    previous, result = 0, bytearray()
    for tick, event in events:
        result.extend(variable(tick - previous) + event)
        previous = tick
    result.extend(b"\0\xff\x2f\0")
    return b"MTrk" + struct.pack(">I", len(result)) + result


def fixture():
    tempo = track([(0, b"\xff\x51\x03\x07\xa1\x20"),
                   (960, b"\xff\x51\x03\x03\xd0\x90")])
    events = [(0, b"\xff\x03\x0aPART DRUMS")]
    def note(tick, pitch, velocity=100):
        events.append((tick, bytes([0x90, pitch, velocity])))
    for pitch in (96, 97, 98):
        note(0, pitch)
    note(480, 110); note(480, 98)
    note(960, 110, 0); note(960, 98)
    note(1440, 99)
    note(1920, 111); note(1920, 99)
    note(2400, 111, 0); note(2400, 99)
    note(2880, 100)
    note(3360, 112); note(3360, 100)
    note(3840, 112, 0); note(3840, 100)
    return b"MThd" + struct.pack(">I3H", 6, 1, 2, 480) + tempo + track(events)


class ChartPartsTests(unittest.TestCase):
    def test_same_pitch_is_a_tom_only_inside_its_marker(self):
        result = summarize(fixture())
        self.assertEqual(result["counts"], dict(kick=1, snare=1, hihat=2, high_tom=1,
            ride=2, middle_tom=1, crash=2, floor_tom=1))

    def test_tom_times_follow_the_tempo_map(self):
        self.assertEqual(summarize(fixture())["tom_passages"], [
            dict(seconds=.5, part="high_tom", section=""),
            dict(seconds=1.5, part="middle_tom", section=""),
            dict(seconds=2.25, part="floor_tom", section=""),
        ])


if __name__ == "__main__":
    unittest.main()
