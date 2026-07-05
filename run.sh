#!/usr/bin/env bash
# Convenience launcher — runs the configurator from the source tree without installing.
set -euo pipefail
cd "$(dirname "$0")"
exec python3 -m waybar_configurator "$@"
