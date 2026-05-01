"""Normalize CRLF line endings for repository source files."""

from __future__ import annotations

from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
SKIP_DIRS = {
    '.git',
    'node_modules',
    'vendor',
}


def iter_repo_files() -> list[Path]:
    try:
        raw = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT)
        return [ROOT / item for item in raw.decode('utf-8', errors='ignore').split('\x00') if item]
    except Exception:
        files: list[Path] = []
        for path in ROOT.rglob('*'):
            if not path.is_file():
                continue
            relative = path.relative_to(ROOT).parts
            if any(part in SKIP_DIRS for part in relative):
                continue
            files.append(path)
        return files


converted = 0
skipped = 0
errors = 0

for filepath in iter_repo_files():
    relative_parts = filepath.relative_to(ROOT).parts
    if any(part in SKIP_DIRS for part in relative_parts):
        continue

    try:
        raw = filepath.read_bytes()
        if b'\r\n' not in raw:
            skipped += 1
            continue
        if b'\x00' in raw:
            skipped += 1
            continue
        filepath.write_bytes(raw.replace(b'\r\n', b'\n'))
        print(f'  converted: {filepath.relative_to(ROOT)}')
        converted += 1
    except Exception as exc:
        errors += 1
        print(f'  error: {filepath} -> {exc}')

print(f'\nDone. Converted {converted} files, skipped {skipped} (already LF or binary), errors {errors}.')
