"""Evaluate the shipped pure DTA geometry functions against stock PS3 samples.

The small evaluator covers only the arithmetic/control subset used by these
functions. Object handlers still require the isolated RPCS3 runtime check.
"""

import math
import operator
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "_ark/dx/track/lanes/dx_drum_lane_surface.dta"


def parse(source):
    tokens = iter(re.findall(r"[{}()]|[^\s{}()]+", re.sub(r";[^\n]*", "", source)))

    def group(opener):
        result = []
        closer = "}" if opener == "{" else ")"
        for token in tokens:
            if token == closer:
                return (opener, result)
            if token in "})":
                raise ValueError("Mismatched DTA delimiters")
            result.append(group(token) if token in "{(" else token)
        raise ValueError("Unclosed DTA group")

    return [group(token) for token in tokens]


class GeometryScript:
    def __init__(self):
        self.functions = {}
        for _, form in parse(SOURCE.read_text()):
            assert form[0] == "func"
            self.functions[form[1]] = (form[2][1], form[3:])

    def call(self, name, *args):
        parameters, body = self.functions[name]
        assert len(parameters) == len(args)
        env = dict(zip(parameters, args))
        return self.sequence(body, env)

    def sequence(self, forms, env):
        result = None
        for form in forms:
            result = self.evaluate(form, env)
        return result

    def evaluate(self, node, env):
        if isinstance(node, str):
            if node.startswith("$"):
                return env[node]
            return float(node)
        kind, form = node
        if kind == "(":
            name, value = form
            env[name] = self.evaluate(value, env)
            return env[name]
        op, *args = form
        ev = lambda value: self.evaluate(value, env)
        if op == "do":
            # DataDo permits bindings only at the beginning and restores them on exit.
            bound, commands = {}, False
            for kind, form in args:
                if kind == "(":
                    if commands:
                        raise ValueError("DTA binding after command")
                    bound[form[0]] = env.get(form[0])
                else:
                    commands = True
            result = self.sequence(args, env)
            for name, previous in bound.items():
                if previous is None:
                    env.pop(name, None)
                else:
                    env[name] = previous
            return result
        if op == "set":
            env[args[0]] = ev(args[1])
            return env[args[0]]
        if op == "if_else":
            return ev(args[1] if ev(args[0]) else args[2])
        if op == "if":
            return self.sequence(args[1:], env) if ev(args[0]) else None
        if op == "foreach_int":
            for index in range(int(ev(args[1])), int(ev(args[2]))):
                env[args[0]] = index
                self.sequence(args[3:], env)
            return None
        if op == "array":
            return [ev(item) for item in args[0][1]]
        if op == "elem":
            return ev(args[0])[int(ev(args[1]))]
        values = [ev(arg) for arg in args]
        if op == "+":
            return sum(values)
        if op == "*":
            assert len(values) == 2, "DataMultiply is binary"
            return values[0] * values[1]
        if op == "-":
            assert len(values) in (1, 2), "DataSub is unary or binary"
            return -values[0] if len(values) == 1 else values[0] - values[1]
        if op == "/":
            return values[0] / values[1]
        if op == "sqrt":
            return math.sqrt(values[0])
        if op == "&&":
            return all(values)
        comparisons = {"<=": operator.le, ">=": operator.ge}
        if op in comparisons:
            return comparisons[op](*values)
        raise ValueError(f"Unsupported pure DTA operation: {op}")


# Extracted from stock PS3 smasher_plate_drum, X-axis basis z/x (not Euler guesses).
SAMPLES = [
    [-7.35, -.28, .07254193723201752 / .9973653554916382],
    [-2.445, -.0349, .014599164016544819 / .9998934268951416],
    [2.445, -.034341, -.014593816362321377 / .9998934864997864],
    [7.35, -.28, -.07253097742795944 / .9973661303520203],
]


class SurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = GeometryScript()

    def surface(self, x, samples=SAMPLES):
        return self.script.call("dx_drum_lane_surface_eval", samples, x)

    def test_all_do_bindings_precede_commands(self):
        def check(node):
            if not isinstance(node, tuple):
                return
            _, items = node
            if items and items[0] == "do":
                commands = False
                for kind, _ in items[1:]:
                    self.assertFalse(kind == "(" and commands, "DTA binding after command")
                    commands = commands or kind == "{"
            for item in items:
                check(item)
        for form in parse(SOURCE.read_text()):
            check(form)

    def test_stock_positions_and_tangents(self):
        for x, z, slope in SAMPLES:
            actual = self.surface(x)
            self.assertAlmostEqual(actual[0], z, places=12)
            self.assertAlmostEqual(actual[1], slope, places=12)

    def test_cubic_reproduction(self):
        # Hermite interpolation must reproduce an independent cubic and its derivative.
        height = lambda x: .03 * x**3 - .2 * x**2 + .1 * x + 2
        slope = lambda x: .09 * x**2 - .4 * x + .1
        samples = [[x, height(x), slope(x)] for x in (-7, -2, 2, 7)]
        for x in (-6, -3, 0, 1, 4, 6):
            z, s = self.surface(x, samples)
            self.assertAlmostEqual(z, height(x), places=12)
            self.assertAlmostEqual(s, slope(x), places=12)

    def test_continuity_and_derivative(self):
        epsilon = 1e-5
        for x, z, slope in SAMPLES:
            before, after = self.surface(x - epsilon), self.surface(x + epsilon)
            self.assertAlmostEqual((after[0] - before[0]) / (2 * epsilon), slope, places=6)
            self.assertAlmostEqual(before[1], after[1], places=6)

    def test_outer_lanes_use_endpoint_tangents(self):
        for x, sample in ((-8.4, SAMPLES[0]), (8.4, SAMPLES[-1])):
            z, slope = self.surface(x)
            self.assertAlmostEqual(z, sample[1] + (x - sample[0]) * sample[2])
            self.assertEqual(slope, sample[2])
            self.assertTrue(math.isfinite(z))

    def test_seven_lane_frames(self):
        for position in range(7):
            z, slope = self.surface(2.8 * (position - 3))
            self.assertTrue(-.37 < z < 0)
            basis = self.script.call("dx_drum_lane_surface_basis", slope)
            rows = [basis[i:i + 3] for i in (0, 3, 6)]
            for i in range(3):
                for j in range(3):
                    self.assertAlmostEqual(sum(a*b for a, b in zip(rows[i], rows[j])), float(i == j))
            self.assertEqual(rows[1], [0, 1, 0])
            self.assertAlmostEqual(rows[0][2] / rows[0][0], slope)
            self.assertAlmostEqual(rows[0][0] * rows[2][2] - rows[0][2] * rows[2][0], 1)

    def test_note_depth_and_height_survive_every_lane_assignment(self):
        # Nonzero asset offsets must survive; neither flatten them nor add receiver offsets.
        original = [.2, 1.25, -.3]
        for source_x, _, _ in SAMPLES:
            for position in range(7):
                dx = 2.8 * (position - 3) - source_x
                first = self.script.call("dx_drum_lane_widget_offsets", original, dx)
                repeated = self.script.call("dx_drum_lane_widget_offsets", original, dx)
                self.assertEqual(first, repeated)
                self.assertAlmostEqual(first[0] + source_x, original[0] + 2.8 * (position - 3))
                self.assertEqual(first[1:], original[1:])
                self.assertEqual(original, [.2, 1.25, -.3])


if __name__ == "__main__":
    unittest.main()
