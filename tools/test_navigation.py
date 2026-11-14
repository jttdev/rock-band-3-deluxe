#!/usr/bin/env python3
"""Provide a temporary gamepad for isolated RPCS3 menu tests."""

import argparse
import json
from pathlib import Path
import signal
import socket
import time

SDL_CLASSIC_MAPPING = (
    "00001bb25242332054657374204e6100,RB3 Test Navigation,"
    "a:b0,b:b1,x:b2,y:b3,leftshoulder:b4,rightshoulder:b5,back:b6,start:b7,"
    "guide:b8,leftstick:b9,rightstick:b10,dpup:h0.1,dpright:h0.2,dpdown:h0.4,dpleft:h0.8,"
    "leftx:a0,lefty:a1,rightx:a3,righty:a4,lefttrigger:a2,righttrigger:a5,platform:Linux,"
)


def serve(path):
    import evdev
    from evdev import ecodes as ec

    if path.exists():
        raise RuntimeError("Refusing to replace an existing control socket")
    buttons = {
        "confirm": ec.BTN_SOUTH, "back": ec.BTN_EAST,
        "square": ec.BTN_NORTH, "triangle": ec.BTN_WEST,
        "start": ec.BTN_START, "select": ec.BTN_SELECT,
    }
    axes = {"left": (ec.ABS_HAT0X, -1), "right": (ec.ABS_HAT0X, 1),
            "up": (ec.ABS_HAT0Y, -1), "down": (ec.ABS_HAT0Y, 1)}
    caps = {
        ec.EV_KEY: [ec.BTN_SOUTH, ec.BTN_EAST, ec.BTN_NORTH, ec.BTN_WEST,
                    ec.BTN_TL, ec.BTN_TR, ec.BTN_SELECT, ec.BTN_START,
                    ec.BTN_MODE, ec.BTN_THUMBL, ec.BTN_THUMBR],
        ec.EV_ABS: [(axis, evdev.AbsInfo(0, -32768, 32767, 16, 128, 0))
                    for axis in (ec.ABS_X, ec.ABS_Y, ec.ABS_RX, ec.ABS_RY)] +
                   [(axis, evdev.AbsInfo(0, 0, 255, 0, 0, 0)) for axis in (ec.ABS_Z, ec.ABS_RZ)] +
                   [(axis, evdev.AbsInfo(0, -1, 1, 0, 0, 0)) for axis in (ec.ABS_HAT0X, ec.ABS_HAT0Y)],
    }
    def stop(_signal, _frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, stop)
    with evdev.UInput(caps, name="RB3 Test Navigation", vendor=0x045e,
                      product=0x028e, version=0x0114, bustype=ec.BUS_USB,
                      max_effects=0) as pad:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
            server.bind(str(path))
            path.chmod(0o600)
            server.listen(1)
            print(f"Ready: {pad.name}; control socket {path}", flush=True)
            try:
                while True:
                    connection, _ = server.accept()
                    with connection:
                        data = connection.recv(4096)
                        actions = json.loads(data)
                        if not isinstance(actions, list) or not all(action in buttons or action in axes for action in actions):
                            connection.sendall(b"Invalid actions")
                            continue
                        for action in actions:
                            if action in axes:
                                code, value = axes[action]
                                kind = ec.EV_ABS
                            else:
                                code, value, kind = buttons[action], 1, ec.EV_KEY
                            pad.write(kind, code, value)
                            pad.syn()
                            time.sleep(0.15)
                            pad.write(kind, code, 0)
                            pad.syn()
                            time.sleep(0.35)
                        connection.sendall(b"OK")
            except KeyboardInterrupt:
                pass
            finally:
                path.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--socket", type=Path, required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("serve")
    send = commands.add_parser("send")
    send.add_argument("actions", nargs="+", choices=["confirm", "back", "square", "triangle", "start", "select", "left", "right", "up", "down"])
    args = parser.parse_args()
    if args.command == "serve":
        serve(args.socket.resolve())
    else:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(str(args.socket.resolve()))
            client.sendall(json.dumps(args.actions).encode())
            reply = client.recv(4096).decode()
            if reply != "OK":
                raise RuntimeError(reply)
            print(reply)


if __name__ == "__main__":
    main()
