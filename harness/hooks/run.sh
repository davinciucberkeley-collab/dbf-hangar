#!/bin/sh
# Runs a hangar hook with the first Python 3 found. Usage: run.sh <hook-name>
[ -f "$(dirname "$0")/$1.py" ] || exit 0
for c in python3 python py; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1; then
    exec "$c" "$(dirname "$0")/$1.py"
  fi
done
echo "hangar hook $1: no Python 3 found on PATH" >&2
exit 0
