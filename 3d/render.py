import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, lib, scenes
argv = sys.argv[sys.argv.index('--') + 1:]
name = argv[0]
frame = int(argv[1]) if len(argv) > 1 else None
scenes.SCENES[name]()
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'preview', f'{name}_{frame}.png') if frame else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'media', f'{name}.mp4')
os.makedirs(os.path.dirname(out), exist_ok=True)
lib.render(out, still=frame)
print('WROTE', out)
