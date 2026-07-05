#!/usr/bin/env bash
# Weather module for Waybar — outputs JSON (text + tooltip).
# Data from wttr.in. Set WEATHER_LOCATION to override IP-based auto-detection,
# e.g. export WEATHER_LOCATION="Berlin".
set -uo pipefail

LOC="${WEATHER_LOCATION:-}"
current=$(curl -sf --max-time 10 "https://wttr.in/${LOC}?format=%c+%t" 2>/dev/null)

if [ -z "${current// }" ]; then
  echo '{"text":"󰖝 N/A","tooltip":"Weather unavailable"}'
  exit 0
fi

tooltip=$(curl -sf --max-time 10 \
  "https://wttr.in/${LOC}?format=%l:+%C,+%t+(feels+%f)\n%h+humidity,+wind+%w" 2>/dev/null)

esc() { printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g' | tr '\n' '\036' | sed 's/\036/\\n/g'; }
printf '{"text":"%s","tooltip":"%s"}\n' "$(esc "$(echo "$current" | xargs)")" "$(esc "$tooltip")"
