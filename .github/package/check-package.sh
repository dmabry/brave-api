set -euo pipefail

SMOKE_VENV="${SMOKE_VENV:-.package-smoke-venv}"
PYTHON_BIN="${PYTHON_BIN:-$(poetry run python -c 'import sys; print(sys.executable)')}"

rm -rf dist "$SMOKE_VENV"
trap 'rm -rf "$SMOKE_VENV"' EXIT

poetry check
poetry build

wheel="$(find dist -maxdepth 1 -type f -name '*.whl' | sort | tail -n 1)"
if [[ -z "$wheel" ]]; then
    echo "No wheel was built in dist/." >&2
    exit 1
fi

poetry run python .github/package/validate-wheel-metadata.py "$wheel"

"$PYTHON_BIN" -m venv "$SMOKE_VENV"
"$SMOKE_VENV/bin/python" -m pip install --upgrade pip
"$SMOKE_VENV/bin/python" -m pip install "$wheel"
"$SMOKE_VENV/bin/python" -m pip check
"$SMOKE_VENV/bin/python" - <<'PY'
import brave
from brave import AsyncBrave
from brave import Brave

assert brave.__name__ == "brave"
assert Brave.__name__ == "Brave"
assert AsyncBrave.__name__ == "AsyncBrave"
PY
