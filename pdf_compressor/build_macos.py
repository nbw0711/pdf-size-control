#!/usr/bin/env python3
"""Build a standalone macOS app using the current Python architecture."""
import subprocess
import sys
import os
import shutil
import importlib.metadata
from pathlib import Path

root = Path(__file__).resolve().parent
workspace = root.parent
os.environ['PYINSTALLER_CONFIG_DIR'] = str(workspace / '.build' / 'pyinstaller-cache')
subprocess.run([
    sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
    '--windowed', '--onedir', '--name', 'PDF体积控制',
    '--osx-bundle-identifier', 'local.pdfcompressor.desktop',
    '--distpath', str(workspace / 'output' / 'standalone' / 'macos'),
    '--workpath', str(workspace / '.build' / 'pyinstaller'),
    '--specpath', str(workspace / '.build'),
    '--hidden-import', 'smoke_check',
    str(root / 'gui.py')], check=True, cwd=root)
app = workspace / 'output' / 'standalone' / 'macos' / 'PDF体积控制.app'
licenses = app / 'Contents' / 'Resources' / 'licenses'
licenses.mkdir(parents=True, exist_ok=True)
for package in ('pypdf', 'Pillow', 'pyinstaller'):
    dist = importlib.metadata.distribution(package)
    for name in dist.files or []:
        if 'LICENSE' in str(name).upper() or 'COPYING' in str(name).upper():
            source = Path(dist.locate_file(name))
            if source.is_file():
                shutil.copy2(source, licenses / (package + '-' + source.name))
shutil.copy2(Path(sys.base_prefix) / 'lib' / f'python{sys.version_info.major}.{sys.version_info.minor}' / 'LICENSE.txt', licenses / 'CPython-LICENSE.txt')
if (root / 'licenses').exists():
    shutil.copytree(root / 'licenses', licenses, dirs_exist_ok=True)
subprocess.run(['codesign', '--force', '--deep', '--sign', '-', str(app)], check=True)
target = app.parent / 'PDF体积控制-macOS-AppleSilicon.zip'
subprocess.run(['ditto', '-c', '-k', '--sequesterRsrc', '--keepParent', str(app), str(target)], check=True)
print(target)
