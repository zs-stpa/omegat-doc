#!/bin/bash
# Converts screenshots to lossless WebP for assets/: same pixels, about half
# the size of PNG.  Usage: tools/to_webp.sh <image.png>...
set -euo pipefail
OUT="$(cd "$(dirname "$0")/.." && pwd)/assets"
for f in "$@"; do
  cwebp -quiet -lossless -z 9 "$f" -o "$OUT/$(basename "${f%.*}").webp"
done
