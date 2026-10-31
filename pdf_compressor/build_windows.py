#!/usr/bin/env python3
"""Assemble a Windows x64 portable app on any host, using official runtime/wheels."""
import hashlib
import io
import json
import shutil
import struct
import subprocess
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path
import distlib

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent
BUILD = BASE / '.build' / 'windows'
OUT = BASE / 'output' / 'standalone' / 'windows'
APP = OUT / 'PDFCompressor-Windows-x64'
RUNTIME_NAME = 'cpython-3.12.16+20261026-x86_64-pc-windows-msvc-install_only_stripped.tar.gz'
RUNTIME_URL = 'https://github.com/astral-sh/python-build-standalone/releases/download/20261026/' + RUNTIME_NAME.replace('+', '%2B')
RUNTIME_SHA256 = '1f2ab53880fc67ea323398c6388e05af28addc99a8e389209f08a51fdff4b149'


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    archive = BUILD / RUNTIME_NAME
    if not archive.exists():
        urllib.request.urlretrieve(RUNTIME_URL, archive)
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == RUNTIME_SHA256, 'Runtime checksum mismatch'
    if APP.exists():
        shutil.rmtree(APP)
    APP.mkdir()
    with tarfile.open(archive) as tar:
        tar.extractall(APP, filter='data')
    (APP / 'python').rename(APP / 'runtime')
    wheels = BUILD / 'wheels'
    wheels.mkdir(exist_ok=True)
    subprocess.run([
        sys.executable, '-m', 'pip', 'download', '--only-binary=:all:',
        '--platform', 'win_amd64', '--python-version', '312', '--implementation', 'cp',
        '--abi', 'cp312', '--dest', str(wheels), '-r', str(ROOT / 'requirements.txt'),
        *(['--no-index', '--find-links', str(wheels)] if
          (wheels / 'pypdf-6.10.0-py3-none-any.whl').exists() and
          (wheels / 'pillow-13.0.0-cp312-cp312-win_amd64.whl').exists() else [])], check=True)
    site = APP / 'runtime' / 'Lib' / 'site-packages'
    site.mkdir(parents=True, exist_ok=True)
    for wheel in wheels.glob('*.whl'):
        with zipfile.ZipFile(wheel) as z:
            z.extractall(site)
    sources = APP / 'app'
    sources.mkdir()
    for name in ['gui.py', 'compress_pdf.py', 'smoke_check.py', 'i18n.py']:
        shutil.copy2(ROOT / name, sources / name)
    bootstrap = '''import sys, os, runpy
from pathlib import Path
base = Path(sys.argv[0]).resolve().parent
sys._pdf_app_home = base
os.environ.pop('PYTHONHOME', None)
os.environ.pop('PYTHONPATH', None)
sys.path.insert(0, str(base / 'app'))
runpy.run_path(str(base / 'app' / 'gui.py'), run_name='__main__')
'''
    launcher = Path(distlib.__file__).parent / 'w64.exe'
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('__main__.py', bootstrap)
    exe = APP / 'PDFCompressor.exe'
    exe.write_bytes(launcher.read_bytes() + b'#!<launcher_dir>\\runtime\\pythonw.exe -E -s\n' + payload.getvalue())
    (APP / '使用说明.txt').write_text(
        'PDF 体积控制 - Windows x64 便携版\n\n'
        '完整解压后双击 PDFCompressor.exe；无需安装 Python，无需联网。\n'
        '请保留 runtime 和 app 文件夹，不能只复制 exe。\n'
        '添加 PDF，输入每个文件的 MB 上限（支持小数），选择输出目录后开始。\n'
        '右上角支持 English / 简体中文 / 繁體中文 / 日本語 界面切换。\n'
        '默认结果保存到用户 Documents/压缩结果。原件保留，同名结果自动编号。\n'
        '目标过小时可能影响画质或无法达标。\n'
        '本包已完成文件/架构/依赖静态校验，尚未在 Windows 实机运行验证。\n', encoding='utf-8-sig')
    license_dir = APP / 'licenses'
    license_dir.mkdir()
    if (ROOT / 'licenses').exists():
        shutil.copytree(ROOT / 'licenses', license_dir, dirs_exist_ok=True)
    distlib_root = Path(distlib.__file__).parent
    for candidate in distlib_root.parent.glob('distlib-*.dist-info/licenses/*'):
        if candidate.is_file():
            shutil.copy2(candidate, license_dir / ('distlib-' + candidate.name))
    required = ['runtime/pythonw.exe', 'runtime/python312.dll', 'app/gui.py',
                'runtime/Lib/site-packages/pypdf/__init__.py',
                'runtime/Lib/site-packages/PIL/__init__.py']
    for path in required:
        assert (APP / path).is_file(), path
    assert list((APP / 'runtime').rglob('_tkinter.pyd')), 'Missing Tk binary'
    assert list((APP / 'runtime').rglob('tk.tcl')), 'Missing Tk scripts'
    assert list(site.rglob('_imaging.cp312-win_amd64.pyd')), 'Missing Windows Pillow binary'
    pe = exe.read_bytes()
    offset = struct.unpack_from('<I', pe, 0x3C)[0]
    assert pe[offset:offset+4] == b'PE\0\0' and struct.unpack_from('<H', pe, offset+4)[0] == 0x8664
    manifest = dict(runtime_url=RUNTIME_URL, runtime_sha256=RUNTIME_SHA256,
                    architecture='Windows x86_64', windows_execution_verified=False,
                    files={str(p.relative_to(APP)): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in APP.rglob('*') if p.is_file()})
    (OUT / 'windows-build-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    target = OUT / 'PDF体积控制-Windows-x64.zip'
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(APP.rglob('*')):
            if p.is_file():
                z.write(p, str(p.relative_to(OUT)))
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
    print(target)


if __name__ == '__main__':
    main()
