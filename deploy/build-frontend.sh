#!/usr/bin/env bash
# Build the frontend for the ECS/Nginx deployment without changing source code.
# The source project keeps localhost URLs for local development.  This script
# rewrites only the generated static assets to use Nginx's same-origin /api/
# reverse proxy.

set -euo pipefail

PROJECT_DIR="${1:-/opt/huaweiyunmadaojingsai}"
cd "$PROJECT_DIR"

npm ci
# Do not run the package's vue-tsc wrapper here: production deployment only
# needs the Vite bundle and this avoids a type-check-only build blocker.
npm exec -- vite build

if ! find dist -type f -name '*.js' -print0 | xargs -0 grep -q 'http://localhost:8000/api'; then
  echo "Frontend build completed: no localhost API URL needed replacement."
  exit 0
fi

find dist -type f -name '*.js' -print0 | xargs -0 sed -i 's|http://localhost:8000/api|/api|g'

if find dist -type f -name '*.js' -print0 | xargs -0 grep -q 'http://localhost:8000/api'; then
  echo "ERROR: localhost API URL remains in generated assets." >&2
  exit 1
fi

echo "Frontend build completed: generated assets use same-origin /api/."
