#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${1:-$ROOT_DIR/dist/offline_bundle}"
WHEELHOUSE_DIR="$OUT_DIR/wheelhouse"
RUNTIME_DIR="$OUT_DIR/runtime"

rm -rf "$OUT_DIR"
mkdir -p "$WHEELHOUSE_DIR" "$RUNTIME_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="$ROOT_DIR/.offline-build-venv"
rm -rf "$VENV_DIR"

"$PYTHON_BIN" -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip

# Build project wheel and all dependency wheels for offline installation.
pip wheel --wheel-dir "$WHEELHOUSE_DIR" "$ROOT_DIR"

# Package runtime files required in air-gapped deployment.
cp "$ROOT_DIR/.env.example" "$RUNTIME_DIR/.env.example"
cp "$ROOT_DIR/README.md" "$RUNTIME_DIR/README.md"
cp "$ROOT_DIR/pyproject.toml" "$RUNTIME_DIR/pyproject.toml"
cp -R "$ROOT_DIR/specs" "$RUNTIME_DIR/specs"
cp -R "$ROOT_DIR/examples" "$RUNTIME_DIR/examples"
cp -R "$ROOT_DIR/scripts" "$RUNTIME_DIR/scripts"

cat > "$OUT_DIR/install_offline.sh" <<'INSTALL_EOF'
#!/usr/bin/env bash
set -euo pipefail

BUNDLE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${1:-$(pwd)/secure-xl2hwp-runtime}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

mkdir -p "$TARGET_DIR"
cp -R "$BUNDLE_DIR/runtime/." "$TARGET_DIR/"

"$PYTHON_BIN" -m venv "$TARGET_DIR/.venv"
source "$TARGET_DIR/.venv/bin/activate"

pip install --no-index --find-links "$BUNDLE_DIR/wheelhouse" secure-xl2hwp-local

echo "Offline install completed at: $TARGET_DIR"
echo "Run API: cd $TARGET_DIR && source .venv/bin/activate && uvicorn app.main:app --host 127.0.0.1 --port 8080"
INSTALL_EOF

chmod +x "$OUT_DIR/install_offline.sh"

tar -czf "$ROOT_DIR/dist/secure-xl2hwp-offline-bundle.tar.gz" -C "$OUT_DIR" .

rm -rf "$VENV_DIR"

echo "Offline bundle built: $ROOT_DIR/dist/secure-xl2hwp-offline-bundle.tar.gz"
