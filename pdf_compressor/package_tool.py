#!/usr/bin/env python3
"""Package reproducible sources; standalone builds have separate scripts."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
root = Path(__file__).resolve().parent
target = root.parent / 'output' / 'PDF压缩工具源码.zip'
target.parent.mkdir(parents=True, exist_ok=True)
with ZipFile(target, 'w', ZIP_DEFLATED) as archive:
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root)
        if path.is_file() and '__pycache__' not in relative.parts and (relative.parts[0] == 'licenses' or len(relative.parts) == 1 and path.suffix in {'.py', '.txt', '.md', '.command'}):
            archive.write(path, arcname=f'{root.name}/{relative.as_posix()}')
with ZipFile(target) as archive:
    assert archive.testzip() is None
print(target)
