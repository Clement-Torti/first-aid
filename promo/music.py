"""Pulsing 110 BPM soundtrack for the promo, synthesised from scratch (no samples).
Usage: python music.py out.wav"""
import sys, numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile

SR, DUR = 48000, 25.5
N = int(SR * DUR)
BPM = 110.0
BEAT = 60 / BPM
OFF = 2.9 - 5 * BEAT                # grid aligned so the phone impact (2.9 s) and end card (22.0 s) land on beats
rng = np.random.default_rng(7)
L = np.zeros(N); R = np.zeros(N)


def t_(n): return np.arange(n) / SR
def beat_t(k): return OFF + k * BEAT
def add(buf, x, t0, g=1.0):
    i = int(t0 * SR)
    if i >= N: return
    if i < 0: x = x[-i:]; i = 0
    n = min(len(x), N - i)
    buf[i:i + n] += x[:n] * g
def both(x, t0, g=1.0, pan=0.0):
    add(L, x, t0, g * np.sqrt(0.5 * (1 - pan))); add(R, x, t0, g * np.sqrt(0.5 * (1 + pan)))
def lp(x, f, o=2): return sosfilt(butter(o, f, 'low', fs=SR, output='sos'), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x)
def bp(x, a, b, o=2): return sosfilt(butter(o, [a, b], 'band', fs=SR, output='sos'), x)
def env(n, a, d, s=0.0, curve=4.0):
    e = np.ones(n); na = max(1, int(a * SR)); e[:na] = np.linspace(0, 1, na)
    k = np.arange(n - na) / SR
    e[na:] = s + (1 - s) * np.exp(-curve * k / max(d, 1e-3))
    return e
def midi(m): return 440 * 2 ** ((m - 69) / 12)


# ---------------- instruments
def kick(g=1.0, long=False):
    n = int((0.9 if long else 0.45) * SR); t = t_(n)
    f = 45 + 120 * np.exp(-t * 32)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) * env(n, 0.001, 0.35 if long else 0.18, curve=3)
    x += 0.35 * lp(rng.standard_normal(n), 3000) * env(n, 0.0005, 0.012)
    return np.tanh(2.2 * x) * g

def heartbeat(t0, g=1.0):
    for dt, gg in ((0, 1.0), (0.24, 0.7)):
        n = int(0.35 * SR); t = t_(n)
        x = np.sin(2 * np.pi * np.cumsum(38 + 40 * np.exp(-t * 25)) / SR) * env(n, 0.004, 0.12, curve=3)
        both(lp(x, 180), t0 + dt, g * gg)

def hat(open_=False, g=1.0):
    n = int((0.28 if open_ else 0.05) * SR)
    x = hp(rng.standard_normal(n), 7000, 4) * env(n, 0.0005, 0.12 if open_ else 0.02, curve=4)
    return x * g

def clap(g=1.0):
    n = int(0.25 * SR)
    x = bp(rng.standard_normal(n), 900, 3500) * env(n, 0.001, 0.08)
    return x * g

def saw(freq, n, harm=24, detune=0.0):
    t = t_(n); x = np.zeros(n)
    for h in range(1, harm + 1):
        if freq * h > 16000: break
        x += np.sin(2 * np.pi * freq * (1 + detune) * h * t + rng.uniform(0, 6.28)) / h
    return x

def pad_chord(notes, n):
    x = np.zeros(n)
    for m in notes:
        for d in (-0.004, 0.0, 0.0045):
            x += saw(midi(m), n, harm=18, detune=d)
    return lp(x / (len(notes) * 3), 1400)

def pluck(m, g=1.0, bright=6000):
    n = int(0.42 * SR)
    x = saw(midi(m), n, harm=30)
    x = lp(x, bright) * env(n, 0.002, 0.16, curve=4)
    return x * g

def sub(m, n):
    t = t_(n)
    return np.sin(2 * np.pi * midi(m) * t)

def riser(t0, t1, g=1.0):
    n = int((t1 - t0) * SR); t = t_(n); p = t / t[-1]
    x = hp(rng.standard_normal(n), 400) * p ** 2
    x = bp(x, 800, 9000)
    both(x * g, t0, 1.0)

def impact(t0, g=1.0):
    n = int(2.6 * SR); t = t_(n)
    x = np.sin(2 * np.pi * np.cumsum(30 + 90 * np.exp(-t * 9)) / SR) * env(n, 0.002, 1.2, curve=3)
    x += 0.4 * lp(rng.standard_normal(n), 1800) * env(n, 0.001, 0.35)
    both(np.tanh(1.6 * x) * g, t0)

def click(g=1.0, f=1100):
    n = int(0.08 * SR); t = t_(n)
    return np.sin(2 * np.pi * f * t) * env(n, 0.001, 0.02, curve=5) * g


# ---------------- arrangement
# chords (A minor): Am  F  C  G   -- 2 bars each (8 beats)
PROG = [[57, 60, 64, 69], [53, 57, 60, 65], [55, 60, 64, 67], [55, 59, 62, 67]]
BASS = [45, 41, 48, 43]
ARP = [[69, 72, 76, 81], [65, 69, 72, 77], [67, 72, 76, 79], [67, 71, 74, 79]]

# intro: heartbeats + dark swell + riser into the impact
for k, t0 in enumerate((0.15, 1.0, 1.82)):
    heartbeat(t0, 0.9 + 0.1 * k)
nsw = int(2.9 * SR)
swell = pad_chord([45, 52, 57], nsw) * np.linspace(0, 1, nsw) ** 2
both(swell, 0.0, 0.35)
riser(1.5, 2.9, 0.12)
impact(2.9, 0.9)

# groove from beat 5 (2.9 s) to beat 40 (22.0 s)
side = np.ones(N)                     # sidechain envelope (pad ducks on every kick)
for k in range(5, 40):
    tb = beat_t(k)
    sec = 'build' if tb >= 16.9 else ('main' if tb >= 5.0 else 'soft')
    both(kick(0.95 if sec != 'soft' else 0.75), tb)
    i = int(tb * SR); n = int(0.45 * SR)
    if i < N:
        e = 1 - 0.75 * np.exp(-t_(min(n, N - i)) * 9)
        side[i:i + len(e)] = np.minimum(side[i:i + len(e)], e)
    if sec != 'soft':
        both(hat(g=0.18), tb + BEAT / 2, pan=0.3)
        if k % 2 == 1:
            both(clap(0.22), tb, pan=-0.1)
    if sec == 'build':
        both(hat(True, 0.12), tb + BEAT / 2, pan=-0.3)
        both(hat(g=0.1), tb + BEAT / 4, pan=0.5); both(hat(g=0.1), tb + 3 * BEAT / 4, pan=-0.5)
    # CPR metronome section: the app's own click on every beat
    if 10.4 <= tb < 12.4:
        both(click(0.22), tb)

# pad + bass + arps by chord (2 bars = 8 beats)
pad = np.zeros(N)
for c in range(5):
    k0 = 5 + c * 8
    t0 = beat_t(k0); t1 = min(beat_t(k0 + 8), 22.0)
    if t0 >= 22.0: break
    n = int((t1 - t0) * SR) + int(0.3 * SR)
    ch = c % 4
    x = pad_chord(PROG[ch], n) * env(n, 0.05, 99, s=1.0)
    x[-int(0.3 * SR):] *= np.linspace(1, 0, int(0.3 * SR))
    i = int(t0 * SR); m = min(n, N - i)
    pad[i:i + m] += x[:m]
    b = sub(BASS[ch] - 12, n) * 0.5 + 0.35 * lp(saw(midi(BASS[ch]), n, harm=8), 400)
    b[-int(0.3 * SR):] *= np.linspace(1, 0, int(0.3 * SR))
    for kk in range(8):
        tb = beat_t(k0 + kk)
        if tb >= 22.0: break
        # bass pumps on offbeats (classic pulse)
        seg = int(BEAT * SR)
        j = int((tb - t0) * SR)
        gate = np.zeros(seg); h = seg // 2
        gate[h:] = env(seg - h, 0.004, 0.2, curve=3)
        if j + seg <= len(b):
            b[j:j + seg] *= 0.25 + 0.75 * gate
        if tb >= 5.0:
            steps = 4 if tb >= 16.9 else 2
            for s in range(steps):
                note = ARP[ch][(kk * steps + s) % 4]
                pan = (-0.45, 0.45)[(kk * steps + s) % 2]
                both(pluck(note, 0.07 if tb < 16.9 else 0.085, 4500 if tb < 16.9 else 7000), tb + s * BEAT / steps, pan=pan)
    both(b, t0, 0.32)
both(pad * side, 0.0, 0.16)
riser(19.8, 22.0, 0.14)

# end card: big hit + resolving chord with long tail
impact(22.0, 1.0)
both(kick(1.0, long=True), 22.0)
n = int(3.5 * SR)
endc = pad_chord([45, 57, 60, 64, 71], n) * env(n, 0.02, 1.6, s=0.0, curve=2)
both(endc, 22.0, 0.28)
for s, m in enumerate((81, 76, 72, 69)):
    both(pluck(m, 0.06, 5000), 22.0 + s * 0.14, pan=(-0.4, 0.4)[s % 2])

# ---------------- reverb + master
def reverb(x, secs=2.2, mix=0.22, seed=1):
    n = int(secs * SR)
    ir = np.random.default_rng(seed).standard_normal(n) * np.exp(-np.arange(n) / SR * 3.2)
    ir = lp(ir, 5000); ir /= np.sqrt((ir ** 2).sum())
    return x + mix * fftconvolve(x, ir)[:len(x)]
L, R = reverb(L, seed=1), reverb(R, seed=2)
mix = np.stack([L, R], 1)
mix = hp(mix.T, 28).T
fade = np.ones(N); fo = int(1.2 * SR); fade[-fo:] = np.linspace(1, 0, fo) ** 2
fi = int(0.05 * SR); fade[:fi] = np.linspace(0, 1, fi)
mix *= fade[:, None]
mix /= np.max(np.abs(mix)) + 1e-9
mix = np.tanh(1.4 * mix) / np.tanh(1.4)
mix *= 0.89
wavfile.write(sys.argv[1], SR, (mix * 32767).astype(np.int16))
print('wrote', sys.argv[1], round(DUR, 2), 's')
