# Animaciones 3D, voz y vídeo promocional

## Vídeos 3D (`../media/`)
Renderizados con Blender 4.3 a partir del maniquí Xbot (Mixamo). El modelo no se incluye en el repo:
`curl -L -o 3d/assets/Xbot.glb https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/models/gltf/Xbot.glb`

- `lib.py`: escena de estudio, poses en coordenadas del mundo con IK analítico, objetos y render.
- `scenes.py`: una función `sc_<nombre>` por animación.
- Previsualizar: `./pv.sh push 1 20` → `preview/push_sheet.png`
- Renderizar: `./render_all.sh push call ...` → `../media/<nombre>.mp4`

## Voz (`../voice/<idioma>/`)
Piper TTS, una voz por idioma (ver `VOICE` en `tts.py`; los modelos `.onnx` se descargan de huggingface.co/rhasspy/piper-voices a `3d/voices/`).
Desde la raíz: `node 3d/extract_texts.js && 3d/.venv/bin/python 3d/tts.py`

## Vídeo promocional (`../promo/`)
`promo.html` se graba fotograma a fotograma con tiempo virtual (`record_det.mjs`), la música se sintetiza con `music.py` y `encode.py` (Blender) une imagen y audio.
