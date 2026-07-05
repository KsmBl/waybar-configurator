#!/usr/bin/env bash
# Disk access (I/O throughput) module for Waybar — outputs JSON.
# Measures read/write bytes/s across physical disks over a 1s window.
set -uo pipefail

sample() {
  awk '$3 ~ /^(sd[a-z]|nvme[0-9]+n[0-9]+|vd[a-z]|mmcblk[0-9]+)$/ {r+=$6; w+=$10}
       END {print r*512, w*512}' /proc/diskstats
}

read -r r1 w1 <<<"$(sample)"
sleep 1
read -r r2 w2 <<<"$(sample)"

rd=$(( r2 - r1 )); wr=$(( w2 - w1 ))
[ "$rd" -lt 0 ] && rd=0
[ "$wr" -lt 0 ] && wr=0

hr() { numfmt --to=iec --suffix=B "$1" 2>/dev/null || echo "${1}B"; }
printf '{"text":"󰀦  %s/s  %s/s","tooltip":"Disk read %s/s\\nDisk write %s/s"}\n' \
  "$(hr "$rd")" "$(hr "$wr")" "$(hr "$rd")" "$(hr "$wr")"
