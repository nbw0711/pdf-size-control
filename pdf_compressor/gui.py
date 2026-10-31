#!/usr/bin/env python3
"""Desktop UI for local PDF compression. Worker threads never touch Tk widgets."""
import json
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from compress_pdf import CompressionCancelled, compress, validate_limit
from i18n import LANGUAGES, ROWS, tr


class CompressorApp:
    def __init__(self, root):
        self.root = root
        self.language_code = 'zh-Hans'
        self.status_model = ('idle', {})
        self.row_states = {}
        root.title('PDF 体积控制工具')
        root.geometry('1060x800')
        root.minsize(1000, 740)
        self.files = []
        self.events = queue.Queue()
        self.cancel = threading.Event()
        self.running = False
        self.limit = tk.StringVar(value='10')
        base = Path(__file__).resolve().parent
        if getattr(sys, 'frozen', False) or hasattr(sys, '_pdf_app_home'):
            base = Path.home() / 'Documents'
        elif base.name == 'Resources' and base.parent.parent.suffix == '.app':
            base = base.parents[2]
        self.output = tk.StringVar(value=str(base / '压缩结果'))
        self.status = tk.StringVar(value='选择 PDF，设置每个文件的大小上限，然后开始压缩。')
        style = ttk.Style(root)
        style.configure('Treeview', rowheight=32)
        style.configure('TButton', padding=(12, 7))
        style.configure('Title.TLabel', font=('Helvetica', 24, 'bold'))
        style.configure('Sub.TLabel', font=('Helvetica', 12))
        outer = ttk.Frame(root, padding=24)
        outer.pack(fill='both', expand=True)
        ttk.Label(outer, text='PDF 体积控制', style='Title.TLabel').pack(anchor='w')
        ttk.Label(outer, text='本地处理 · 保留原件 · 每个文件单独控制大小', style='Sub.TLabel').pack(anchor='w', pady=(6, 20))
        toolbar = ttk.Frame(outer)
        toolbar.pack(fill='x', pady=(0, 10))
        self.add_button = ttk.Button(toolbar, text='＋ 添加 PDF', command=self.add_files)
        self.add_button.pack(side='left')
        self.remove_button = ttk.Button(toolbar, text='移除所选', command=self.remove_files)
        self.remove_button.pack(side='left', padx=8)
        self.clear_button = ttk.Button(toolbar, text='清空列表', command=self.clear_files)
        self.clear_button.pack(side='left')
        self.language_choice = tk.StringVar(value=LANGUAGES[self.language_code])
        self.language_picker = ttk.Combobox(toolbar, textvariable=self.language_choice,
                                           values=list(LANGUAGES.values()), state='readonly', width=13)
        self.language_picker.pack(side='right')
        ttk.Label(toolbar, text='语言').pack(side='right', padx=(8, 6))
        self.language_picker.bind('<<ComboboxSelected>>', self.change_language)
        table_frame = ttk.Frame(outer)
        table_frame.pack(fill='both', expand=True)
        self.table = ttk.Treeview(table_frame, columns=('name', 'size', 'result', 'state'), show='headings', height=4)
        for name, label, width in [('name', '文件', 390), ('size', '原始大小', 110), ('result', '结果大小', 110), ('state', '状态', 150)]:
            self.table.heading(name, text=label)
            self.table.column(name, width=width, minwidth=80)
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        self.table.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        settings = ttk.LabelFrame(outer, text='压缩设置', padding=14)
        settings.pack(fill='x', pady=16)
        ttk.Label(settings, text='每个文件小于').grid(row=0, column=0, sticky='w')
        self.limit_entry = ttk.Entry(settings, textvariable=self.limit, width=12)
        self.limit_entry.grid(row=0, column=1, sticky='w', padx=10)
        ttk.Label(settings, text='MB（支持小数，例如 4.5；1 MB = 1,000,000 字节）').grid(row=0, column=2, columnspan=2, sticky='w')
        ttk.Label(settings, text='输出文件夹').grid(row=1, column=0, sticky='w', pady=(14, 0))
        self.output_entry = ttk.Entry(settings, textvariable=self.output)
        self.output_entry.grid(row=1, column=1, columnspan=2, sticky='ew', padx=10, pady=(14, 0))
        self.browse_button = ttk.Button(settings, text='选择…', command=self.choose_output)
        self.browse_button.grid(row=1, column=3, pady=(14, 0))
        settings.columnconfigure(2, weight=1)
        ttk.Label(outer, text='目标越小，画质可能越低。已达标文件保留画质复制；无法达标时会明确提示。', style='Sub.TLabel', wraplength=900).pack(anchor='w')
        actions = ttk.Frame(outer)
        actions.pack(fill='x', pady=(14, 10))
        self.start_button = ttk.Button(actions, text='开始压缩', command=self.start)
        self.start_button.pack(side='left')
        self.cancel_button = ttk.Button(actions, text='取消', command=self.cancel_work, state='disabled')
        self.cancel_button.pack(side='left', padx=8)
        ttk.Button(actions, text='打开输出文件夹', command=self.open_output).pack(side='right')
        self.progress = ttk.Progressbar(outer, mode='indeterminate')
        self.progress.pack(fill='x')
        ttk.Label(outer, textvariable=self.status, wraplength=900).pack(anchor='w', pady=(10, 6))
        self.log = tk.Text(outer, height=4, font=('Helvetica', 11), relief='flat', state='disabled')
        self.log.pack(fill='x')
        self.controls = [self.add_button, self.remove_button, self.clear_button,
                         self.limit_entry, self.output_entry, self.browse_button, self.start_button]
        self.localized_widgets = []
        reverse = {row[1]: key for key, row in ROWS.items()}
        def register(parent):
            for widget in parent.winfo_children():
                if 'text' in widget.keys() and not ('textvariable' in widget.keys() and widget.cget('textvariable')):
                    key = reverse.get(str(widget.cget('text')))
                    if key:
                        self.localized_widgets.append((widget, key))
                register(widget)
        register(root)
        self.change_language()
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.after(100, self.poll)

    def tr(self, key, **values):
        return tr(self.language_code, key, **values)

    def set_status(self, key, **values):
        self.status_model = (key, values)
        rendered = dict(values)
        if 'outcome_key' in rendered:
            rendered['outcome'] = self.tr(rendered.pop('outcome_key'))
        self.status.set(self.tr(key, **rendered))

    def set_row(self, item, key, result=None):
        self.row_states[item] = key
        self.table.set(item, 'state', self.tr(key))
        if result is not None:
            self.table.set(item, 'result', result)

    def change_language(self, event=None):
        self.language_code = next(code for code, name in LANGUAGES.items() if name == self.language_choice.get())
        self.root.title(self.tr('title'))
        for widget, key in self.localized_widgets:
            widget.configure(text=self.tr(key))
        for column in ('name', 'size', 'result', 'state'):
            self.table.heading(column, text=self.tr(column))
        for item in self.table.get_children():
            self.set_row(item, self.row_states[item])
        self.set_status(self.status_model[0], **self.status_model[1])

    def add_paths(self, paths):
        for raw in paths:
            path = Path(raw).resolve()
            if path not in self.files and path.is_file() and path.suffix.lower() == '.pdf':
                self.files.append(path)
                self.table.insert('', 'end', iid=str(path), values=(path.name, f'{path.stat().st_size / 1e6:.2f} MB', '—', self.tr('pending')))
                self.row_states[str(path)] = 'pending'

    def add_files(self):
        self.add_paths(filedialog.askopenfilenames(title=self.tr('select_pdf'), filetypes=[(self.tr('pdf_files'), '*.pdf *.PDF')]))

    def remove_files(self):
        for item in self.table.selection():
            self.files.remove(Path(item))
            self.table.delete(item)
            self.row_states.pop(item, None)

    def clear_files(self):
        self.files.clear()
        self.row_states.clear()
        self.table.delete(*self.table.get_children())

    def choose_output(self):
        folder = filedialog.askdirectory(title=self.tr('select_output'))
        if folder:
            self.output.set(folder)

    def open_output(self):
        try:
            path = Path(self.output.get()).expanduser().resolve()
            path.mkdir(parents=True, exist_ok=True)
            if sys.platform == 'darwin':
                subprocess.Popen(['open', str(path)])
            elif os.name == 'nt':
                os.startfile(path)
            else:
                subprocess.Popen(['xdg-open', str(path)])
        except Exception as exc:
            messagebox.showerror(self.tr('open_error'), str(exc))

    def start(self):
        if self.running:
            return
        try:
            try:
                limit = validate_limit(self.limit.get().strip())
            except ValueError:
                raise ValueError(self.tr('invalid_limit')) from None
            if not self.files:
                raise ValueError(self.tr('no_files'))
            if not self.output.get().strip():
                raise ValueError(self.tr('no_output'))
            output = Path(self.output.get()).expanduser().resolve()
            output.mkdir(parents=True, exist_ok=True)
        except (ValueError, OSError) as exc:
            messagebox.showerror(self.tr('check_settings'), str(exc))
            return
        self.running = True
        self.cancel.clear()
        for control in self.controls:
            control.configure(state='disabled')
        self.cancel_button.configure(state='normal')
        self.progress.start(12)
        self.language_picker.configure(state='disabled')
        self.set_status('running', mb=limit / 1e6)
        for path in self.files:
            self.set_row(str(path), 'queued')
            self.table.set(str(path), 'result', '—')
        threading.Thread(target=self.work, args=(list(self.files), output, limit), daemon=True).start()

    def work(self, paths, output, limit):
        results = []
        success = failed = 0
        was_cancelled = False
        try:
            for path in paths:
                if self.cancel.is_set():
                    was_cancelled = True
                    break
                self.events.put(('row', str(path), 'processing', '—'))
                try:
                    result = compress(path, output, limit, progress=lambda s: self.events.put(('log', s)), cancel=self.cancel, language=self.language_code)
                    results.append(result)
                    success += 1
                    self.events.put(('row', str(path), 'complete', f'{result["output_bytes"] / 1e6:.2f} MB'))
                except CompressionCancelled:
                    was_cancelled = True
                    self.events.put(('row', str(path), 'cancelled', '—'))
                    break
                except Exception as exc:
                    failed += 1
                    results.append(dict(source=str(path), error=str(exc)))
                    self.events.put(('row', str(path), 'failed', '—'))
                    self.events.put(('log', f'{path.name}：{exc}'))
            stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
            report = output / f'compression_report_{stamp}.json'
            report.write_text(json.dumps(dict(target_bytes=limit, cancelled=was_cancelled, files=results), ensure_ascii=False, indent=2), encoding='utf-8')
        except Exception as exc:
            self.events.put(('log', self.tr('report_error', error=str(exc))))
        finally:
            self.events.put(('done', success, failed, was_cancelled))

    def cancel_work(self):
        self.cancel.set()
        self.cancel_button.configure(state='disabled')
        self.set_status('cancelling')

    def poll(self):
        try:
            while True:
                event = self.events.get_nowait()
                if event[0] == 'log':
                    self.log.configure(state='normal')
                    self.log.insert('end', event[1] + '\n')
                    self.log.see('end')
                    self.log.configure(state='disabled')
                elif event[0] == 'row':
                    self.set_row(event[1], event[2], event[3])
                elif event[0] == 'done':
                    self.running = False
                    self.progress.stop()
                    for control in self.controls:
                        control.configure(state='normal')
                    self.cancel_button.configure(state='disabled')
                    self.language_picker.configure(state='readonly')
                    for item in self.table.get_children():
                        if self.row_states[item] == 'queued':
                            self.set_row(item, 'unprocessed')
                    self.set_status('finished', outcome_key='cancelled' if event[3] else 'finished_title', success=event[1], failed=event[2])
        except queue.Empty:
            pass
        self.root.after(100, self.poll)

    def close(self):
        if self.running:
            self.cancel_work()
            self.set_status('closing')
        else:
            self.root.destroy()


if __name__ == '__main__':
    if '--self-test' in sys.argv:
        import contextlib
        import io
        import traceback
        from smoke_check import main as check
        report = Path(sys.argv[sys.argv.index('--self-test') + 1])
        capture = io.StringIO()
        try:
            with contextlib.redirect_stdout(capture):
                check()
        except Exception:
            report.write_text(capture.getvalue() + traceback.format_exc(), encoding='utf-8')
            raise SystemExit(1)
        report.write_text(capture.getvalue(), encoding='utf-8')
        raise SystemExit(0)
    root = tk.Tk()
    app = CompressorApp(root)
    app.add_paths(sys.argv[1:])
    root.mainloop()
