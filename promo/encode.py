# Blender -b -P encode.py -- <seqdir> <out.mp4> [fps]
import bpy, sys, os
a = sys.argv[sys.argv.index('--') + 1:]
seq, out = a[0], a[1]
fps = int(a[2]) if len(a) > 2 else 30
audio = a[3] if len(a) > 3 else None
files = sorted(f for f in os.listdir(seq) if f.endswith('.jpg'))
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.render.fps = fps
sc.sequence_editor_create()
st = sc.sequence_editor.sequences.new_image('seq', os.path.join(seq, files[0]), 1, 1)
for f in files[1:]:
    st.elements.append(f)
sc.frame_start, sc.frame_end = 1, len(files)
sc.view_settings.view_transform = 'Standard'
sc.render.image_settings.file_format = 'FFMPEG'
ff = sc.render.ffmpeg
ff.format, ff.codec, ff.constant_rate_factor, ff.ffmpeg_preset, ff.gopsize = 'MPEG4', 'H264', 'HIGH', 'GOOD', 30
if audio:
    sc.sequence_editor.sequences.new_sound('music', audio, 2, 1)
    ff.audio_codec, ff.audio_bitrate, ff.audio_mixrate, ff.audio_channels = 'AAC', 192, 48000, 'STEREO'
else:
    ff.audio_codec = 'NONE'
sc.render.filepath = out
bpy.ops.render.render(animation=True)
print('ENCODED', out, len(files))
