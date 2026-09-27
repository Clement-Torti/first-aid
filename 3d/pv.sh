#!/bin/zsh
# usage: pv.sh scene f1 f2 ...  -> preview/<scene>_sheet.png
cd "$(dirname $0)"
B=/Applications/Blender.app/Contents/MacOS/Blender
n=$1; shift
cat > /tmp/pv_$n.py <<P
import sys, os
sys.path.insert(0, '$PWD')
import bpy, lib, scenes
scenes.SCENES['$n']()
sc = bpy.context.scene
frames = [int(x) for x in '$*'.split()]
cloth = any(m.type in ('CLOTH','PARTICLE_SYSTEM') for o in bpy.data.objects for m in o.modifiers)
lib.ease_all()
sc.render.image_settings.file_format = 'PNG'
last = 0
for f in frames:
    if cloth:
        for g in range(last + 1, f + 1): sc.frame_set(g)
    sc.frame_set(f); last = f
    sc.render.filepath = '$PWD/preview/_%s_%03d.png' % ('$n', f)
    bpy.ops.render.render(write_still=True)
P
PREVIEW=1 $B -b -P /tmp/pv_$n.py > preview/$n.log 2>&1 || { grep -A5 Traceback preview/$n.log | tail -6; }
grep -A5 Traceback preview/$n.log | tail -6
magick montage preview/_${n}_*.png -tile x1 -geometry +4+0 -background '#000' preview/${n}_sheet.png && rm preview/_${n}_*.png && echo "sheet preview/${n}_sheet.png"
