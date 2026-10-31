# PDF 体积控制工具 - 独立运行版

无需安装 Python 或其他依赖，无需联网；批量选择 PDF，手动输入每个文件的 MB 上限（支持小数），指定输出文件夹即可处理。
界面右上方的 Language / 语言选项支持 English、简体中文、繁體中文、日本語，切换会即时更新按钮、表格、提示与状态，并保留文件列表和设置。处理期间暂时禁用语言切换，日志采用启动该任务时所选的语言。操作系统原生文件选择器的通用按钮遵循系统语言。
原件保留，同名结果自动编号，已达标文件按原画质复制。压缩可能降低画质，无法达到过小的上限时会显示失败原因。

## macOS（Apple Silicon：M1/M2/M3/M4 等）

交付文件：`output/standalone/macos/PDF体积控制-macOS-AppleSilicon.zip`

解压后双击 `PDF体积控制.app`，也可将应用拖入“应用程序”文件夹。
应用自带 Python、Tk 和 PDF 处理依赖。本次已在当前 Apple Silicon Mac 上以清洁环境运行独立程序，并完成 0.65 MB 自定义目标的 GUI 压缩自检。
这是本地临时签名版本，未进行 Apple 开发者签名或公证；其他 Mac 的系统可能提示确认来源。
仅提供 Apple Silicon 架构，本包不支持 Intel Mac，未在其他 macOS 版本实机验证。

## Windows（x64）

交付文件：`output/standalone/windows/PDF体积控制-Windows-x64.zip`

完整解压后双击 `PDFCompressor-Windows-x64/PDFCompressor.exe`。
必须保留旁边的 `runtime` 和 `app` 文件夹；不要只复制 exe，不要在压缩包里直接启动。
这是带原生 GUI EXE 启动器和完整可移植 Python/Tk/依赖的便携版，无需安装 Python，无需运行脚本、联网下载或安装依赖。
本包为 Windows x86_64 架构，未提供 Windows ARM64 原生版或 32 位版。
已检查官方运行时 SHA256、EXE 架构、Tk 脚本和二进制、Pillow Windows 二进制、PDF 依赖和 ZIP 完整性；当前没有 Windows 主机，因此尚未进行 Windows 实机启动或压缩验证。
本地源码包不包含任何护照、证件图片或个人 PDF。

## 操作

1. 点击“添加 PDF”，可多选。
2. 输入每个文件的目标大小，例如 `10`、`5` 或 `4.5`（1 MB = 1,000,000 字节）。
3. 选择输出目录，点击“开始压缩”。
4. 在列表查看结果大小，点击“打开输出文件夹”获取结果和 JSON 报告。

独立版默认输出到用户的 `Documents/压缩结果`，可在界面修改。
取消会等待当前页面或写盘操作结束，保留已经完成的结果，删除当前临时文件。
不适用于需要保留数字签名有效性的 PDF；遇到加密或表单/签名字段会拒绝处理。

## 构建与源码

源码均保存在 `pdf_compressor`，打包脚本只打包工具，不包含个人文件。

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-build.txt
.venv/bin/python build_macos.py
.venv/bin/python build_windows.py
.venv/bin/python package_tool.py
```

`build_macos.py` 应在 Apple Silicon Mac 和包含 Tk 的 Python 环境运行，使用 PyInstaller 构建并本地签名。
`build_windows.py` 可在任意主机组装 x64 便携包：使用 Astral 官方 Python Standalone Windows 运行时，验证固定 SHA256；下载匹配 CPython 3.12 的 Windows wheels；使用 PyPA distlib 原生 GUI 启动器，以相对路径调用随包运行时。
依赖版本固定在 `requirements-build.txt` / `requirements.txt`；运行时来源和 SHA256 以及完整文件清单位于 `windows-build-manifest.json`。

- `gui.py`：后台线程处理的 Tk 界面。
- `i18n.py`：四语言界面、应用内提示、错误和压缩日志文案，无需联网翻译。
- `compress_pdf.py`：压缩引擎和命令行（支持 `--max-mb 4.5`）。
- `smoke_check.py`：使用生成的测试 PDF 验证界面、大小、取消及原件保留。
- `verify_previews.py`：可选预览工具，需 Poppler；独立程序日常运行无需 Poppler。
- `package_tool.py`：生成纯源码 ZIP，不再生成依赖外部 Python 的旧版应用。

参考：
- https://pyinstaller.org/en/stable/
- https://github.com/astral-sh/python-build-standalone
- https://distlib.readthedocs.io/en/stable/tutorial.html
