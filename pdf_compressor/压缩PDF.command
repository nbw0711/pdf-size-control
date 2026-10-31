#!/bin/zsh
set -e
cd "${0:A:h}"
# Prefer an existing environment with Tk and PDF dependencies.
candidates=("$PWD/.venv/bin/python" "$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3" "$(command -v python3)")
for interpreter in "${candidates[@]}"; do
  if [[ -x "$interpreter" ]] && "$interpreter" -c 'import tkinter, pypdf, PIL' 2>/dev/null; then
    exec "$interpreter" gui.py "$@"
  fi
done
if ! python3 -c 'import tkinter' 2>/dev/null; then
  print '当前 Python 缺少 Tk 图形库。请安装包含 Tk 的 Python（python.org macOS 安装包），然后重试。'
  read 'reply?按回车关闭'
  exit 1
fi
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
exec .venv/bin/python gui.py "$@"
