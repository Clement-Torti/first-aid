#!/bin/zsh
cd "$(dirname $0)"
B=/Applications/Blender.app/Contents/MacOS/Blender
for s in "$@"; do
  f=${s#*:}; n=${s%%:*}
  $B -b -P render.py -- $n $f > preview/$n.log 2>&1 && echo "ok $n" || { echo "FAIL $n"; grep -A3 Traceback preview/$n.log | tail -4; }
done
