#!/usr/bin/env python3
"""Prepare a source-only archive and explicitly selected release binaries."""
import argparse
import hashlib
import shutil
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parent
ROOT_FILES = {'README.md', 'LICENSE', 'THIRD_PARTY.md', 'RELEASE_NOTES.md',
              'docs-build.md', '.gitignore', 'prepare_release.py'}


def public_files():
    files = [ROOT / name for name in sorted(ROOT_FILES)]
    for directory in ('pdf_compressor', '.github'):
        for path in (ROOT / directory).rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts:
                assert path.suffix.lower() not in {'.pdf', '.jpg', '.png', '.exe', '.zip', '.pyc'}, path
                files.append(path)
    return sorted(files)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--artifacts-root', type=Path, default=ROOT / 'output' / 'standalone')
    parser.add_argument('--output', type=Path, default=ROOT / 'output' / 'release')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    source = args.output / 'PDF-Size-Control-v1.0.0-source.zip'
    files = public_files()
    for path in files:
        assert (b'/' + b'Users/') not in path.read_bytes(), f'Absolute personal path in {path.name}'
    with ZipFile(source, 'w', ZIP_DEFLATED) as z:
        for path in files:
            z.write(path, 'pdf-size-control/' + path.relative_to(ROOT).as_posix())
    binaries = {
        'macos/PDF体积控制-macOS-AppleSilicon.zip': 'PDF-Size-Control-macOS-arm64.zip',
        'windows/PDF体积控制-Windows-x64.zip': 'PDF-Size-Control-Windows-x64.zip',
    }
    targets = [source]
    for original, name in binaries.items():
        target = args.output / name
        shutil.copy2(args.artifacts_root / original, target)
        targets.append(target)
    for target in targets:
        with ZipFile(target) as z:
            assert z.testzip() is None
            assert not any(name.lower().endswith('.pdf') for name in z.namelist()), target
    checksum = args.output / 'SHA256SUMS.txt'
    checksum.write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n' for p in targets), encoding='utf-8')
    print(f'Prepared {len(files)} source files and {len(targets)} verified ZIP archives in {args.output}')


if __name__ == '__main__':
    main()
