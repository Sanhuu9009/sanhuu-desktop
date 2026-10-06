#!/bin/bash
# ===== XiaoBaiHu Desktop Pet launcher (macOS) =====
cd "$(dirname "$0")"

HTML=$(ls -1 *.html 2>/dev/null | head -n1)
if [ -z "$HTML" ]; then
  echo "[Error] No .html file found in this folder."
  read -r -p "Press Enter to close..."
  exit 1
fi

URL="file://$PWD/$HTML"
ARGS="--app=$URL --window-size=480,700 --window-position=center --disable-features=Translate"

if [ -d "/Applications/Google Chrome.app" ]; then
  open -a "Google Chrome" --args $ARGS
elif [ -d "/Applications/Microsoft Edge.app" ]; then
  open -a "Microsoft Edge" --args $ARGS
else
  open "$PWD/$HTML"
fi
