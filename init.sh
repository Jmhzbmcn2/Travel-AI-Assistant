#!/bin/bash
set -e

SKIP_FRONTEND=0
if [ "${1:-}" = "--skip-frontend" ]; then
  SKIP_FRONTEND=1
fi

if command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v py >/dev/null 2>&1; then
  PYTHON_BIN="py -3"
else
  echo "Python was not found. Install Python or add python/python3/py to PATH." >&2
  exit 1
fi

echo "=== Harness Initialization ==="
echo "=== Verification Commands ==="
echo "$PYTHON_BIN -m compileall src main.py"
$PYTHON_BIN -m compileall src main.py

if [ "$SKIP_FRONTEND" -eq 0 ]; then
  echo "=== npm run lint ==="
  (cd frontend && npm run lint)

  echo "=== npm run build ==="
  (cd frontend && npm run build)
fi

echo "=== Verification Complete ==="
echo ""
echo "Next steps:"
echo "1. Record command and output summary as Verification Evidence in progress.md"
echo "2. Update feature_list.json status, evidence, and next_step"
echo "3. Refresh session-handoff.md before ending the session"
