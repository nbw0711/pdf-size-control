#!/usr/bin/env python3
"""Exercise custom limits, actual Tk worker, preservation and cancellation."""
import tempfile
import threading
import time
import tkinter as tk
from pathlib import Path
from PIL import Image
from pypdf import PdfReader
from compress_pdf import compress, CompressionCancelled, validate_limit
from gui import CompressorApp
from i18n import LANGUAGES, ROWS, TRANSLATIONS, tr
from string import Formatter


def main():
    for key, row in ROWS.items():
        fields = [{field for _, field, _, _ in Formatter().parse(text) if field} for text in row]
        assert all(value == fields[0] for value in fields), key
        assert all(text.strip() for text in row), key
    for value in ['0', '-1', 'nan', 'inf', 'abc', '']:
        try:
            validate_limit(value)
        except ValueError:
            pass
        else:
            raise AssertionError(value)
    assert validate_limit('4.5') == 4_500_000
    with tempfile.TemporaryDirectory(prefix='pdf-ui-check-') as tmp:
        base = Path(tmp)
        source = base / 'sample.pdf'
        Image.effect_noise((1200, 1600), 70).convert('RGB').save(source, 'PDF', resolution=150, quality=98)
        original_size = source.stat().st_size
        root = tk.Tk()
        app = CompressorApp(root)
        app.add_paths([source, source])
        assert len(app.files) == 1
        app.output.set(str(base / 'results'))
        app.limit.set('0.65')
        for language, name in LANGUAGES.items():
            app.language_choice.set(name)
            app.language_picker.event_generate('<<ComboboxSelected>>')
            root.update()
            assert app.language_code == language
            assert root.title() == tr(language, 'title')
            for widget, key in app.localized_widgets:
                assert str(widget.cget('text')) == tr(language, key), (language, key)
            assert app.table.heading('state', 'text') == tr(language, 'state')
            app.start()
            deadline = time.monotonic() + 90
            while app.running and time.monotonic() < deadline:
                root.update()
                time.sleep(0.02)
            assert not app.running, 'UI worker timeout'
            assert app.table.set(str(source.resolve()), 'state') == tr(language, 'complete')
            assert tr(language, 'finished_title') in app.status.get()
            assert str(app.language_picker.cget('state')) == 'readonly'
            assert app.limit.get() == '0.65' and len(app.files) == 1
            assert tr(language, 'trying', name=source.name, edge=2600, quality=88) in app.log.get('1.0', 'end')
            print(f'PASS: {name} widgets, headings, status, logs and custom-size GUI compression')
        result = next((base / 'results').glob('*.pdf'))
        assert result.stat().st_size < 650_000
        assert len(PdfReader(result).pages) == 1
        assert source.stat().st_size == original_size
        assert all(p.stat().st_size < 650_000 for p in (base / 'results').glob('*.pdf'))
        first = compress(result, base / 'copy', 1_000_000, progress=lambda _: None)
        second = compress(result, base / 'copy', 1_000_000, progress=lambda _: None)
        assert first['output'] != second['output']
        assert (base / 'copy' / first['output']).read_bytes() == result.read_bytes()
        cancel = threading.Event()
        def request_cancel(_):
            cancel.set()
        try:
            compress(source, base / 'cancel', 1, progress=request_cancel, cancel=cancel)
        except CompressionCancelled:
            pass
        else:
            raise AssertionError('Cancellation did not stop work')
        assert not list((base / 'cancel').glob('*.pdf'))
        root.destroy()
        print('PASS: custom 0.65 MB GUI compression, validation, page count, original preservation, unique outputs, cancellation cleanup')


if __name__ == '__main__':
    main()
