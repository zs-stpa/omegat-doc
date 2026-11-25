#!/bin/bash
# Re-encodes the deck clips in assets/ from their original screen recordings:
# 1280 px wide, silent, H.264 with long GOP and many reference frames (screen
# recordings change little between frames), plus a poster frame each.
# Usage: ORIGINALS=<folder with the recordings> tools/make_clips.sh
set -euo pipefail
: "${ORIGINALS:?set ORIGINALS to the folder with the original recordings}"
FF=${FFMPEG:-ffmpeg}
OUT="$(cd "$(dirname "$0")/.." && pwd)/assets"

enc() {  # <source file> <asset name> <fps> <poster second> [ffmpeg input options...]
  local src=$ORIGINALS/$1 name=$2 fps=$3 poster=$4; shift 4
  "$FF" -v error -y "$@" -i "$src" -an -vf "scale='min(1280,iw)':-2,fps=$fps" \
    -c:v libx264 -preset veryslow -crf 30 -g 1200 -x264-params ref=6:bframes=8:b-adapt=2 \
    -pix_fmt yuv420p -movflags +faststart "$OUT/$name.mp4"
  "$FF" -v error -y -ss "$poster" -i "$OUT/$name.mp4" -frames:v 1 -q:v 3 "$OUT/$name-poster.jpg"
  echo "$name $(wc -c < "$OUT/$name.mp4")"
}
enc 2026-07-14-editor-features-integration-demo.mp4 number-autoconvert-demo 12 205 -ss 95 -to 505
enc 2026-08-09-number-substitution-exotic-numerals-demo.mp4 2026-08-09-number-substitution-exotic-numerals-demo 15 2
enc 2026-07-28-colors-preferences-table-sorting-demo.mp4 2026-07-28-colors-preferences-table-sorting-demo 15 2
enc 2026-11-25-shortcut-preferences-demo.mp4 shortcut-preferences-demo 15 10
enc 2026-08-16-editor-layout-demo.mp4 editor-layout-demo 12 15 -ss 15 -to 105
