#!/usr/bin/env python3
"""Use the navigation pad's first Start press to join RPCS3's MIDI drummer."""

import argparse
from pathlib import Path
import select
import time

import evdev
import rtmidi


def find_controller(name):
    for path in evdev.list_devices():
        try:
            device = evdev.InputDevice(path)
        except OSError:
            continue
        if device.name == name:
            return device
        device.close()
    return None


def join_drums():
    # The MIDI device exposes this sequencer destination while RPCS3 is running.
    output = rtmidi.MidiOut(rtapi=rtmidi.API_LINUX_ALSA)
    for index, name in enumerate(output.get_ports()):
        if 'RPCS3 MIDI Drums Input' in name:
            output.open_port(index)
            break
    else:
        raise RuntimeError('RPCS3 MIDI drum input is not available yet')
    try:
        # RPCS3 translates this clean sequence to Start on the MIDI drum pad.
        for note in (44, 44, 44, 38):
            output.send_message([0x99, note, 127])
            time.sleep(0.1)
            output.send_message([0x89, note, 0])
            time.sleep(0.05)
    finally:
        output.close_port()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent-pid', type=int, required=True)
    parser.add_argument('--controller-name', default='8Bitdo SN30 Pro')
    parser.add_argument('--start-code', type=int, default=evdev.ecodes.BTN_START)
    args = parser.parse_args()
    parent = Path('/proc') / str(args.parent_pid)
    log = Path.home() / '.cache/rpcs3/RPCS3.log'
    device = None
    print('Waiting for the SN30 Pro Start button.', flush=True)
    try:
        while parent.exists():
            if device is None:
                device = find_controller(args.controller_name)
                if device is None:
                    time.sleep(0.5)
                    continue
            try:
                if not select.select([device], [], [], 0.5)[0]:
                    continue
                for event in device.read():
                    if (event.type != evdev.ecodes.EV_KEY
                            or event.code != args.start_code
                            or event.value != 1):
                        continue
                    # Do not send another Start if the drummer already joined.
                    if log.exists() and 'hit combo: start' in log.read_text(errors='replace'):
                        print('Drummer already initialized; navigation pad handles Start.', flush=True)
                        return
                    try:
                        join_drums()
                    except Exception as error:
                        print(f'{error}; press Start after the title screen appears.', flush=True)
                        continue
                    print('Sent MIDI drum Start; navigation pad handles subsequent buttons.', flush=True)
                    return
            except OSError:
                device.close()
                device = None
    finally:
        if device is not None:
            device.close()


if __name__ == '__main__':
    main()
