#!/bin/zsh
cd "$(dirname $0)"
B=/Applications/Blender.app/Contents/MacOS/Blender
mkdir -p ../media logs
for n in "$@"; do
  s=$(date +%s)
  $B -b -P render.py -- $n > logs/$n.log 2>&1 && echo "ok $n $(( $(date +%s)-s ))s" || echo "FAIL $n"
done
echo ALLDONE
