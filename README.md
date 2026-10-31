# PDF Size Control

A local desktop tool for compressing scanned PDFs to a size limit you choose.

本地 PDF 体积控制工具：手动输入每个文件的大小上限，支持批量处理及四语言界面。

**English · 简体中文 · 繁體中文 · 日本語**

## Download / 下载

Get the standalone packages from [Releases](https://github.com/nbw0711/pdf-size-control/releases/latest).
No Python installation or internet connection is needed to use these packages.

| Platform | Package | How to run | Verification |
| --- | --- | --- | --- |
| macOS Apple Silicon (M series) | macOS-AppleSilicon ZIP | Extract and open the `.app` | GUI and compression self-test passed on the development Mac |
| Windows x64 | Windows-x64 ZIP | Extract the entire folder and open `PDFCompressor.exe` | Bundle integrity and dependency checks passed; Windows execution has not yet been verified |

Keep the Windows `runtime` and `app` folders beside the EXE. The EXE is the entry point to a portable bundle, not a single-file application.
The macOS app has a local ad-hoc signature and is not Apple notarized. Intel Macs are not supported by the supplied macOS binary.

macOS：解压后打开应用；Windows：完整解压后双击 EXE，保留旁边的文件夹。两个版本均自带运行环境。

## Use / 使用

1. Add one or more PDFs / 添加一个或多个 PDF。
2. Set a per-file limit such as `10`, `5` or `4.5` MB / 输入每个文件的大小上限。
3. Choose an output folder and click **Compress** / 选择输出目录并开始压缩。
4. Use the language selector at the top right / 在右上角切换语言。

One MB means 1,000,000 bytes; successful output is strictly below the chosen limit.
Originals are preserved, existing output names receive a numeric suffix, and files already under the limit are copied without further quality loss.
Each run writes a JSON report. Cancellation keeps completed files and cleans up the current temporary PDF.

This uses lossy JPEG recompression of eligible embedded images. A smaller limit may reduce readability. Not every PDF can meet every limit; failure is reported instead of silently returning an oversized result.
Encrypted PDFs and PDFs containing form/signature fields are rejected. Do not use this workflow when digital-signature validity must be preserved.
No PDF contents are uploaded by this tool. Native file-picker buttons follow the operating system language; application text follows the selected language.

## Run from source

Requires Python 3.10+ with Tk; the build scripts are tested with Python 3.12.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r pdf_compressor/requirements.txt
.venv/bin/python pdf_compressor/gui.py
```

On Windows, replace `.venv/bin/python` with `.venv\Scripts\python.exe`.

```sh
.venv/bin/python pdf_compressor/compress_pdf.py input.pdf --max-mb 4.5 --output-dir results
```

## Build and verify

```sh
.venv/bin/python -m pip install -r pdf_compressor/requirements-build.txt
.venv/bin/python pdf_compressor/smoke_check.py
.venv/bin/python pdf_compressor/build_macos.py
.venv/bin/python pdf_compressor/build_windows.py
```

The macOS builder must run on an Apple Silicon Mac. The Windows builder assembles an x64 portable runtime on any host using a fixed, SHA256-verified official Astral Python distribution, matching Windows wheels, and a PyPA distlib GUI launcher.
Build outputs go to `output/standalone/`. Tests generate synthetic noise-image PDFs; no user PDFs are needed.
See [build notes](docs-build.md) and [third-party notices](THIRD_PARTY.md).

## License

Project code is available under the [MIT License](LICENSE). Bundled third-party components retain their own licenses.
