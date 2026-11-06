#!/usr/bin/env python3
"""Seven-day Downloads organizer. Dry-run by default; --apply moves eligible files."""
import argparse
import datetime as dt
import os
import pathlib
import plistlib
import shutil
import subprocess
import sys
import time

HOME = pathlib.Path.home()
DOWNLOADS = HOME / 'Downloads'
MIN_AGE_DAYS = 7
SKIP_EXT = {'.download', '.crdownload', '.part', '.partial', '.tmp', '.temp', '.lock'}


def date_added(path):
    """Read Spotlight's Date Added, accepting both raw text and plist output."""
    try:
        result = subprocess.run(
            ['mdls', '-raw', '-name', 'kMDItemDateAdded', str(path)],
            capture_output=True, text=True, timeout=8, check=True,
        )
        raw = result.stdout.strip()
        # mdls -raw commonly returns: 2025-01-29 00:12:06 +0000
        import re
        match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} [+-]\d{4})', raw)
        if match:
            return dt.datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S %z')
    except (OSError, subprocess.SubprocessError, ValueError):
        pass
    return None


def destination(name):
    """Conservative filename-based routing; never infer image contents."""
    lower = name.lower().replace('-', ' ').replace('_', ' ')
    stem = pathlib.Path(lower).stem
    ext = pathlib.Path(lower).suffix
    for project in ('numerio', 'zeod', 'jade villa'):
        if project in stem:
            return pathlib.Path('01 PROJECTS') / project.upper(), 'project name'
    if 'discovery factfind' in stem:
        return pathlib.Path('11 TO REVIEW'), 'project unknown: factfind'
    if any(x in stem for x in ('invoice', 'receipt', 'elfsight calculator basic', 'bank statement', 'tax return', 'superannuation', 'payslip', 'bas statement', 'insurance cost', 'insurane cost', 'freelance work log', 'billing')):
        if 'insurance' in stem or 'insurane' in stem:
            sub = 'Insurance'
        elif 'freelance work log' in stem:
            sub = 'Work Records'
        else:
            sub = 'Invoices & Receipts'
        return pathlib.Path('10 FINANCIAL MATTERS') / sub, 'financial filename'
    if any(x in stem for x in ('osint', 'investigation', 'intelligence', 'research')):
        return pathlib.Path('02 RESEARCH'), 'research filename'
    if any(x in stem for x in ('wisestamp', 'email signature')):
        return pathlib.Path('04 MEDIA & ARTWORK') / 'Email Branding', 'email branding'
    if stem == 'inter' or any(x in stem for x in ('space grotesk', 'font')):
        return pathlib.Path('04 MEDIA & ARTWORK') / 'Fonts', 'font filename'
    if 'stock images' in stem or 'istock' in stem:
        return pathlib.Path('04 MEDIA & ARTWORK') / 'Stock Images', 'stock imagery filename'
    if any(x in stem for x in ('substack wordmark', 'logo')):
        return pathlib.Path('04 MEDIA & ARTWORK') / 'Logos', 'logo filename'
    if any(x in stem for x in ('artwork', 'graphic', 'illustration', 'design', 'puzzle links', 'octagonal', 'glowred')) or ext in {'.psd', '.ai', '.afdesign', '.svg', '.eps'}:
        return pathlib.Path('04 MEDIA & ARTWORK') / 'Design Files', 'design filename or extension'
    if ext in {'.mov', '.mp4'}:
        return pathlib.Path('04 MEDIA & ARTWORK') / 'Video', 'video extension'
    if any(x in stem for x in ('script', 'source code')) or ext in {'.py', '.js', '.css'}:
        return pathlib.Path('06 DEVELOPMENT'), 'development filename or extension'
    if ext in {'.dmg', '.pkg'}:
        return pathlib.Path('07 SOFTWARE') / 'Installers', 'installer extension'
    return pathlib.Path('11 TO REVIEW'), 'uncertain'


def run(apply, root):
    if not root.is_dir() or not (root / '00 INBOX').is_dir() or not (root / '11 TO REVIEW').is_dir():
        print('Server unavailable or incorrect folder structure. Nothing moved.', file=sys.stderr)
        return 2
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=MIN_AGE_DAYS)
    moved = 0
    eligible = 0
    for path in sorted(DOWNLOADS.iterdir(), key=lambda p: p.name.casefold()):
        if path.is_symlink() or not path.is_file() or path.name.startswith('.') or path.suffix.lower() in SKIP_EXT or path.name == pathlib.Path(__file__).name:
            continue
        added = date_added(path)
        if added is None:
            print(f'KEEP (date added unavailable): {path.name}')
            continue
        if added > cutoff:
            print(f'KEEP (under 7 days): {path.name}')
            continue
        if dt.datetime.fromtimestamp(path.stat().st_mtime, dt.timezone.utc) > dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=24):
            print(f'KEEP (modified within 24h): {path.name}')
            continue
        relative, reason = destination(path.name)
        target_dir = root / relative
        if not target_dir.is_dir() and apply:
            print(f'KEEP (destination missing): {path.name} -> {relative}')
            continue
        target = target_dir / path.name
        if target.exists():
            print(f'KEEP (name collision): {path.name} -> {relative}')
            continue
        eligible += 1
        if not apply:
            print(f'WOULD MOVE: {path.name} -> {relative} ({reason})')
            continue
        try:
            # shutil.move supports local->SMB cross-filesystem moves.
            shutil.move(str(path), str(target))
            moved += 1
            print(f'MOVED: {path.name} -> {relative} ({reason})')
        except OSError as exc:
            print(f'ERROR: {path.name}: {exc}', file=sys.stderr)
    print(f'Eligible: {eligible}; moved: {moved}; mode: {"APPLY" if apply else "PREVIEW"}')
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='move files (do not use until preview approved and subfolders created)')
    parser.add_argument('--server', default='/Users/Shared/Server', help='Mac mini: /Users/Shared/Server; MacBook: /Volumes/Server')
    args = parser.parse_args()
    sys.exit(run(args.apply, pathlib.Path(args.server)))
