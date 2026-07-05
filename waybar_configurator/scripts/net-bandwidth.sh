#!/usr/bin/env bash
# Combined network bandwidth module for Waybar — outputs JSON.
# Sums receive/transmit bytes/s across all interfaces (except lo) over 1s.
set -uo pipefail

sample() {
  awk 'NR>2 {gsub(/:/," "); if ($1 != "lo") {rx+=$2; tx+=$10}} END {print rx, tx}' /proc/net/dev
}

read -r rx1 tx1 <<<"$(sample)"
sleep 1
read -r rx2 tx2 <<<"$(sample)"

rx=$(( rx2 - rx1 )); tx=$(( tx2 - tx1 ))
[ "$rx" -lt 0 ] && rx=0
[ "$tx" -lt 0 ] && tx=0

hr() { numfmt --to=iec --suffix=B "$1" 2>/dev/null || echo "${1}B"; }
printf '{"text":"󰓅  %s/s  %s/s","tooltip":"Down %s/s\\nUp %s/s"}\n' \
  "$(hr "$rx")" "$(hr "$tx")" "$(hr "$rx")" "$(hr "$tx")"
