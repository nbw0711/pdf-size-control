#!/usr/bin/env python3
"""Render every page into contact sheets for manual visual verification."""
import argparse
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw

parser = argparse.ArgumentParser()
parser.add_argument('files', nargs='+', type=Path)
parser.add_argument('--output-dir', type=Path, default=Path('tmp/pdfs'))
args = parser.parse_args()
args.output_dir.mkdir(parents=True, exist_ok=True)
for index, pdf in enumerate(args.files, 1):
    folder = args.output_dir / str(index)
    folder.mkdir(exist_ok=True)
    subprocess.run(['pdftoppm', '-scale-to', '400', '-png', str(pdf), str(folder / 'page')], check=True)
    pages = sorted(folder.glob('page-*.png'))
    sheet = Image.new('RGB', (5 * 240, ((len(pages) + 4) // 5) * 350), 'white')
    draw = ImageDraw.Draw(sheet)
    for n, page in enumerate(pages):
        im = Image.open(page).convert('RGB')
        im.thumbnail((230, 320))
        x, y = (n % 5) * 240, (n // 5) * 350
        sheet.paste(im, (x + (240-im.width)//2, y + 22))
        draw.text((x + 8, y + 4), f'Page {n+1}', fill='black')
    target = args.output_dir / f'contact-{index}.jpg'
    sheet.save(target, quality=90)
    print(target)
