#!/usr/bin/env python3
"""Apply/capture the reviewed subset of RPCS3 settings, with local backups."""
import argparse
import configparser
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

import yaml

ROOT = Path(__file__).resolve().parents[1]
FILES = ('config.yml', 'custom_configs/config_BLUS30463.yml',
         'input_configs/BLUS30463/Default.yml')


def merge(old, new):
    result = dict(old or {})
    for key, value in new.items():
        result[key] = merge(result.get(key), value) if isinstance(value, dict) else value
    return result


def select(live, template):
    return {k: select(live[k], v) if isinstance(v, dict) else live[k]
            for k, v in template.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['apply', 'capture'])
    parser.add_argument('--config-dir', type=Path, default=Path.home()/'.config/rpcs3')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    # Avoid losing changes RPCS3 will write when it exits.
    if args.action == 'apply' and not args.dry_run:
        for proc in Path('/proc').glob('[0-9]*/comm'):
            try:
                if proc.read_text().strip().lower() == 'rpcs3':
                    parser.error('Close RPCS3 before applying settings.')
            except (FileNotFoundError, PermissionError, ProcessLookupError):
                pass
    writes = []
    for name in FILES:
        tracked = ROOT/'config/rpcs3'/name
        local = args.config_dir/name
        template = yaml.safe_load(tracked.read_text())
        live = yaml.safe_load(local.read_text()) if local.exists() else {}
        if args.action == 'capture':
            data = live if name.startswith('input_configs/') else select(live, template)
            if not data:
                raise ValueError(f'Missing or empty config: {local}')
            writes.append((tracked, yaml.safe_dump(data, sort_keys=False)))
        else:
            data = template if name.startswith('input_configs/') else merge(live, template)
            writes.append((local, yaml.safe_dump(data, sort_keys=False)))
    gui_template = ROOT/'config/gui.json'
    gui_file = args.config_dir/'GuiConfigs/CurrentSettings.ini'
    gui = configparser.RawConfigParser(strict=False)
    gui.optionxform = str
    gui.read(gui_file)
    settings = json.loads(gui_template.read_text())
    if args.action == 'capture':
        settings = {s: {k: gui.get(s, k) for k in values} for s, values in settings.items()}
        writes.append((gui_template, json.dumps(settings, indent=2)+'\n'))
    else:
        import io
        for section, values in settings.items():
            if not gui.has_section(section):
                gui.add_section(section)
            for key, value in values.items():
                gui.set(section, key, value)
        output = io.StringIO()
        gui.write(output, space_around_delimiters=False)
        writes.append((gui_file, output.getvalue()))
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    backup = Path.home()/'.local/state/rock-band-linux/backups'/stamp
    for target, content in writes:
        print(f'{args.action}: {target}')
        if args.dry_run:
            continue
        if target.exists():
            relative = target.relative_to(args.config_dir if args.action == 'apply' else ROOT)
            saved = backup/relative
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, saved)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)


if __name__ == '__main__':
    main()
