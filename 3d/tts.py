"""Pre-record every step in every language with Piper. Run from the project root."""
import json, subprocess, re, os, sys
T = json.load(open('3d/texts.json'))
VOICE = {'es': ('es_ES-sharvard-medium', '0'), 'en': ('en_US-ryan-high', None), 'fr': ('fr_FR-tom-medium', None),
         'pt': ('pt_BR-faber-medium', None), 'de': ('de_DE-thorsten-high', None), 'it': ('it_IT-paola-medium', None)}
N = {  # spoken form instead of the digits (valid in every country)
 'es': [('al {N}', 'a emergencias'), ('{N} YA', 'llama ya a emergencias'), ('= {N}', ', llama a emergencias'), ('{N}', 'emergencias')],
 'en': [('call {N} NOW', 'call emergency services now'), ('= {N}', ', call emergency services'), ('{N}', 'emergency services')],
 'fr': [('{N} TOUT DE SUITE', 'appelle les secours tout de suite'), ('le {N}', 'les secours'), ('= {N}', ', appelle les secours'), ('{N}', 'les secours')],
 'pt': [('para o {N}', 'para a emergência'), ('{N} JÁ', 'ligue já para a emergência'), ('= {N}', ', ligue para a emergência'), ('{N}', 'emergência')],
 'de': [('SOFORT {N}', 'sofort den Notruf'), ('= {N}', ', Notruf'), ('{N}', 'den Notruf')],
 'it': [('{N} SUBITO', 'chiama subito i soccorsi'), ('il {N}', 'i soccorsi'), ('= {N}', ', chiama i soccorsi'), ('{N}', 'i soccorsi')],
}
ABBR = {
 'es': [('RCP', 'erre ce pe'), ('DEA', 'de e a'), (' cm', ' centímetros'), (' min', ' minutos')],
 'en': [('CPR', 'C P R'), ('AED', 'A E D'), (' cm', ' centimetres'), (' min', ' minutes')],
 'fr': [('RCP', 'R C P'), ('DAE', 'D A E'), (' cm', ' centimètres'), (' min', ' minutes')],
 'pt': [('RCP', 'erre cê pê'), ('DEA', 'dê é á'), (' cm', ' centímetros'), (' min', ' minutos')],
 'de': [('AED', 'A E D'), (' cm', ' Zentimeter'), (' Min.', ' Minuten')],
 'it': [('RCP', 'erre ci pi'), ('DAE', 'di a e'), (' cm', ' centimetri'), (' min', ' minuti')],
}
def norm(lg, t):
    for a, b in N[lg]: t = t.replace(a, b)
    for a, b in ABBR[lg]: t = t.replace(a, b)
    t = re.sub(r'[«»“”„"]', '', t).replace('→', ',').replace('·', ',').replace('…', '.').replace('×', ' ')
    t = re.sub(r'\b([A-ZÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÄÖÜÇÑ]{2,})\b', lambda m: m.group(1).lower(), t)
    return t[:1].upper() + t[1:]
langs = sys.argv[1:] or list(T)
for lg in langs:
    os.makedirs(f'voice/{lg}', exist_ok=True)
    model, spk = VOICE[lg]
    for x in T[lg]:
        w = f'/tmp/v_{lg}_{x["f"]}.wav'
        cmd = ['3d/.venv/bin/piper', '-m', f'3d/voices/{model}.onnx', '--length-scale', '1.05', '--sentence-silence', '0.35', '-f', w]
        if spk: cmd += ['-s', spk]
        subprocess.run(cmd, input=norm(lg, x['t']).encode(), check=True, capture_output=True)
        subprocess.run(['afconvert', '-f', 'm4af', '-d', 'aac', '-b', '64000', w, f'voice/{lg}/{x["f"]}.m4a'], check=True)
        os.remove(w)
    print('done', lg, len(T[lg]), flush=True)
