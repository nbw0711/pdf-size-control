#!/usr/bin/env python3
"""Compress embedded PDF images, preserving pages and document structure."""
import argparse
import io
import json
import math
import shutil
import tempfile
from pathlib import Path

from PIL import Image
from pypdf import PdfReader, PdfWriter
from i18n import tr


class CompressionCancelled(Exception):
    pass


def validate_limit(value):
    mb = float(value)
    if not math.isfinite(mb) or not math.isfinite(mb * 1_000_000) or mb <= 0 or mb * 1_000_000 < 1:
        raise ValueError('请输入有效的正数大小（MB），例如 5、9.5、10')
    return int(mb * 1_000_000)


def compress(source, output_dir, limit, progress=None, cancel=None, language='zh-Hans'):
    if limit < 1:
        raise ValueError(tr(language, 'invalid_limit'))
    def emit(message):
        (progress or (lambda s: print(s, flush=True)))(message)
    def cancelled():
        if cancel is not None and cancel.is_set():
            raise CompressionCancelled(tr(language, 'cancelled'))
    cancelled()
    source = source.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / (source.stem + '_压缩.pdf')
    counter = 2
    while target.exists():
        target = output_dir / f'{source.stem}_压缩_{counter}.pdf'
        counter += 1
    if target.resolve() == source:
        raise ValueError(tr(language, 'overwrite'))
    reader = PdfReader(source)
    if reader.is_encrypted:
        raise ValueError(tr(language, 'encrypted'))
    if reader.get_fields():
        raise ValueError(tr(language, 'forms'))
    descriptor, trial_name = tempfile.mkstemp(suffix='.partial.pdf', dir=output_dir)
    import os
    os.close(descriptor)
    trial = Path(trial_name)
    profiles = [(2600, 88), (2400, 85), (2200, 82), (2000, 80),
                (1800, 78), (1600, 75), (1400, 70), (1200, 65), (1000, 60)]
    try:
        if source.stat().st_size < limit:
            cancelled()
            shutil.copyfile(source, trial)
            trial.replace(target)
            emit(tr(language, 'already_small', name=source.name))
            return dict(source=source.name, output=target.name,
                        original_bytes=source.stat().st_size, output_bytes=target.stat().st_size,
                        pages=len(reader.pages), unchanged=True)
        for max_edge, quality in profiles:
            cancelled()
            emit(tr(language, 'trying', name=source.name, edge=max_edge, quality=quality))
            writer = PdfWriter(clone_from=reader)
            seen = set()
            image_count = 0
            for page in writer.pages:
                cancelled()
                for embedded in list(page.images):
                    ref = embedded.indirect_reference
                    key = (ref.idnum, ref.generation) if ref else None
                    if ref is None or key in seen:
                        continue
                    seen.add(key)
                    obj = ref.get_object()
                    # Preserve masks/transparency and unusual bitonal images.
                    if obj.get('/SMask') or obj.get('/Mask') or obj.get('/ImageMask'):
                        continue
                    original = embedded.image
                    if original.mode in ('1', 'P', 'RGBA', 'LA'):
                        continue
                    im = original.convert('RGB')
                    im.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)
                    encoded = io.BytesIO()
                    im.save(encoded, 'JPEG', quality=quality, optimize=True)
                    # Do not replace an image when its new JPEG would be larger.
                    if len(encoded.getvalue()) < len(embedded.data):
                        embedded.replace(im, quality=quality, optimize=True)
                        image_count += 1
            with trial.open('wb') as handle:
                writer.write(handle)
            size = trial.stat().st_size
            emit(tr(language, 'attempt_size', name=source.name, edge=max_edge, quality=quality, mb=size / 1_000_000))
            if size < limit:
                check = PdfReader(trial)
                if len(check.pages) != len(reader.pages):
                    raise RuntimeError(tr(language, 'page_mismatch'))
                for before, after in zip(reader.pages, check.pages):
                    if list(before.mediabox) != list(after.mediabox):
                        raise RuntimeError(tr(language, 'dimensions_mismatch'))
                    if (before.extract_text() or '') != (after.extract_text() or ''):
                        raise RuntimeError(tr(language, 'text_mismatch'))
                cancelled()
                trial.replace(target)
                return dict(source=source.name, output=target.name,
                            original_bytes=source.stat().st_size, output_bytes=size,
                            pages=len(check.pages), max_image_edge=max_edge,
                            jpeg_quality=quality, replaced_images=image_count)
        raise RuntimeError(tr(language, 'unattainable', name=source.name))
    finally:
        trial.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description='压缩 PDF 到指定 MB 以下（1 MB = 1,000,000 字节），原文件保留。')
    parser.add_argument('files', nargs='+', type=Path)
    parser.add_argument('--output-dir', type=Path, default=Path('output/pdf'))
    parser.add_argument('--max-mb', type=float, default=10)
    args = parser.parse_args()
    try:
        limit = validate_limit(args.max_mb)
    except ValueError as exc:
        parser.error(str(exc))
    results = [compress(p, args.output_dir, limit) for p in args.files]
    report = args.output_dir / 'compression_report.json'
    report.write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'完成，报告：{report}')


if __name__ == '__main__':
    main()
