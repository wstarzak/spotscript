#!/usr/bin/env bash
set -euo pipefail

case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*) ;;
    *)
        echo "Run this script in Git Bash on Windows." >&2
        exit 1
        ;;
esac

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

if command -v py >/dev/null 2>&1; then
    python_cmd=(py -3)
else
    python_cmd=(python)
fi

if ! "${python_cmd[@]}" -c 'import sys; sys.exit(sys.platform != "win32" or sys.version_info < (3, 9))'; then
    echo "Install native Windows Python 3.9 or later and make py or python available in Git Bash." >&2
    exit 1
fi

build_dir=build/windows
"${python_cmd[@]}" -m venv "$build_dir/venv"
build_python="$build_dir/venv/Scripts/python.exe"
"$build_python" -m pip install -r requirements.txt 'pyinstaller>=6,<7'
"$build_python" -m PyInstaller \
    --onefile --console --noconfirm \
    --name spotscript \
    --specpath "$build_dir" --workpath "$build_dir/work" --distpath dist \
    main.py

./dist/spotscript.exe --help >/dev/null
echo "Built dist/spotscript.exe"
