"""Scene definitions. Run: Blender -b -P render.py -- <scene> [frame]"""
import math
from lib import *

VIC = dict(body='#d7dbe1', joints='#7b818c')
RES = dict(body='#3d8bff', joints='#1d3f7a')
Z = V((0, 0, 1))


def lat(f):
    return Z.cross(V(f).normalized()).normalized()


def smooth01(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def nz(i, k):
    x = math.sin(i * 12.9898 + k * 78.233) * 43758.5453
    return (x - math.floor(x)) - 0.5


def T(v):
    return tuple(V(v))


def orient(o, x=None, y=None, z=None):
    if z is not None and y is not None:
        z = V(z).normalized(); y = (V(y) - z * V(y).dot(z)).normalized(); x = y.cross(z)
    elif z is not None and x is not None:
        z = V(z).normalized(); x = (V(x) - z * V(x).dot(z)).normalized(); y = z.cross(x)
    elif x is not None and y is not None:
        x = V(x).normalized(); y = (V(y) - x * V(y).dot(x)).normalized(); z = x.cross(y)
    o.rotation_euler = Matrix((x, y, z)).transposed().to_euler()


def plane(loc, w, h, m, x=(1, 0, 0), z=(0, 0, 1), name='plane', sub=0):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = (w, h, 1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if sub:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.subdivide(number_cuts=sub)
        bpy.ops.object.mode_set(mode='OBJECT')
    orient(o, x=x, z=z)
    o.data.materials.append(m)
    return o


# ---------------------------------------------------------------- poses
def supine(x=0.35, y=0.0, z=0.105):
    """victim lying on back, head toward -X; character left = +Y"""
    return {
        'hips': {'pos': (x, y, z), 'up': (-1, 0, 0), 'fwd': (0, 0, 1)},
        'Spine2': ((-1, 0, 0.0), (0, 0, 1)),
        'Neck': ((-1, 0, 0.06), (0, 0, 1)), 'Head': ((-1, 0, 0.0), (0, 0, 1)),
        'armL': {'dirs': ((0.9, 0.42, -0.06), (1, 0.12, -0.03))},
        'armR': {'dirs': ((0.9, -0.42, -0.06), (1, -0.12, -0.03))},
        'handL': ((1, 0.05, -0.08), (0, 0, -1)), 'handR': ((1, -0.05, -0.08), (0, 0, -1)),
        'legL': {'dirs': ((1, 0.06, -0.02), (1, 0.03, -0.02))},
        'legR': {'dirs': ((1, -0.06, -0.02), (1, -0.03, -0.02))},
        'footL': ((0.35, 0.05, 1), (1, 0, 0.1)), 'footR': ((0.35, -0.05, 1), (1, 0, 0.1)),
    }


def kneel(hx, hy, hz, face=(0, -1, 0), lean=0.8, side=0.13, knee_fwd=0.1):
    f = V(face).normalized()
    left = lat(f)
    up = (Z + f * lean).normalized()
    hips = V((hx, hy, hz))
    p = {'hips': {'pos': T(hips), 'up': T((Z + f * 0.12).normalized()), 'fwd': T(f)},
         'chest': (T(up), T((f - Z * 0.3 * lean).normalized()))}
    for s, sg in (('L', 1), ('R', -1)):
        ankle = hips - f * 0.36 + left * sg * side * 1.1
        p['leg' + s] = {'ik': (ankle.x, ankle.y, 0.085), 'pole': T((f - Z * 0.4).normalized())}
        p['foot' + s] = (T((-f + V((0, 0, -0.35))).normalized()), (0, 0, -1))
    look(p, hips + up * 0.62 + f * 0.5 - Z * 0.4, hips + up * 0.55)
    return p


def stand(x, y, face=(0, -1, 0), hz=1.0, spread=0.1):
    f = V(face).normalized()
    l = lat(f)
    p = {'hips': {'pos': (x, y, hz), 'up': (0, 0, 1), 'fwd': T(f)}, 'chest': ((0, 0, 1), T(f)),
         'Neck': ((0, 0, 1), T(f)), 'Head': ((0, 0, 1), T(f))}
    for s, sg in (('L', 1), ('R', -1)):
        ank = V((x, y, 0.085)) + l * sg * spread
        p['leg' + s] = {'ik': T(ank), 'pole': T(f)}
        p['foot' + s] = (T((f - Z * 0.5).normalized()), (0, 0, 1))
        p['arm' + s] = {'dirs': (T((l * sg * 0.15 + f * 0.03 - Z).normalized()), T((f * 0.2 - Z + l * sg * 0.02).normalized()))}
        p['hand' + s] = (T((f * 0.1 - Z).normalized()), T(-l * sg))
    return p


def sitfloor(x, y, face=(1, 0, 0), lean=0.3, knees=True):
    f = V(face).normalized()
    l = lat(f)
    up = (Z - f * lean).normalized()
    p = {'hips': {'pos': (x, y, 0.15), 'up': T(up), 'fwd': T((f + Z * lean).normalized())},
         'chest': (T((Z - f * lean * 0.6).normalized()), T(f)),
         'Neck': (T((Z + f * 0.1).normalized()), T(f)), 'Head': (T((Z + f * 0.05).normalized()), T(f))}
    for s, sg in (('L', 1), ('R', -1)):
        if knees:
            ank = V((x, y, 0.085)) + f * 0.62 + l * sg * 0.13
            p['leg' + s] = {'ik': T(ank), 'pole': T((Z + f * 0.4 + l * sg * 0.15).normalized())}
            p['foot' + s] = (T((f - Z * 0.6).normalized()), (0, 0, 1))
        else:
            p['leg' + s] = {'dirs': (T((f - Z * 0.12 + l * sg * 0.08).normalized()), T((f - Z * 0.02 + l * sg * 0.05).normalized()))}
            p['foot' + s] = (T((Z + f * 0.4).normalized()), T(-f))
        p['arm' + s] = {'dirs': (T((-Z + f * 0.35 + l * sg * 0.18).normalized()), T((f - Z * 0.25 + l * sg * 0.05).normalized()))}
        p['hand' + s] = (T((f - Z * 0.3).normalized()), (0, 0, -1))
    return p


def seated(x, y, face=(0, -1, 0), hz=0.56):
    f = V(face).normalized()
    l = lat(f)
    p = {'hips': {'pos': (x, y, hz), 'up': (0, 0, 1), 'fwd': T(f)}, 'chest': ((0, 0, 1), T(f)),
         'Neck': ((0, 0, 1), T(f)), 'Head': ((0, 0, 1), T(f))}
    for s, sg in (('L', 1), ('R', -1)):
        ank = V((x, y, 0.085)) + f * 0.5 + l * sg * 0.14
        p['leg' + s] = {'ik': T(ank), 'pole': T((f + Z * 0.3).normalized())}
        p['foot' + s] = (T((f - Z * 0.5).normalized()), (0, 0, 1))
        p['arm' + s] = {'dirs': (T((-Z + f * 0.3 + l * sg * 0.12).normalized()), T((f - Z * 0.3).normalized()))}
        p['hand' + s] = (T((f - Z * 0.4).normalized()), (0, 0, -1))
    return p


def look(p, target, headpos):
    d = (V(target) - V(headpos)).normalized()
    upv = (Z - d * Z.dot(d)).normalized()
    p['Neck'] = (T((upv * 0.8 + d * 0.4).normalized()), T(d))
    p['Head'] = (T(upv), T(d))
    return p


def keys(char, f0, f1, p0, p1, step=2, ease=True):
    f = f0
    while f <= f1:
        t = (f - f0) / max(1, (f1 - f0))
        char.key(f, blend(p0, p1, smooth01(t) if ease else t))
        f += step
    if (f - step) != f1:
        char.key(f1, blend(p0, p1, 1.0))


def rescuer():
    return Char('Res', **RES)


def victim(scale=1.0):
    return Char('Vic', **VIC, scale=scale)


def M_gauze(): return mat('gauze', '#f4f2ee', rough=0.95)
def M_blood(): return mat('blood', '#7a0a0a', rough=0.25, coat=0.6)
def M_wound(): return mat('wound', '#b3161b', rough=0.3, coat=0.5)


def wound(loc, normal, r=0.03, name='wound'):
    o = sphere(loc, r, M_wound(), scale=(1.3, 0.8, 0.12), name=name)
    orient(o, x=(1, 0, 0), z=normal)
    return o


def phone(m_screen):
    body = box((0, 0, 0), (0.072, 0.148, 0.008), mat('alu', '#2b2b2e', rough=0.3, metal=0.9), bevel=0.004, name='phone')
    scr = plane((0, 0, 0.0042), 0.068, 0.143, m_screen, name='screen')
    scr.parent = body
    return body


# ================================================================ SCENES
# ---------------- CPR
def sc_push():
    reset(frames=66)
    studio(key=(1.8, -2.6, 3.4), target=(0.05, 0.1, 0.35), power=700)
    vic, res = victim(), rescuer()
    period = 30 * 60 / 110.0
    for i in range(5):
        for ph, dz in ((0.0, 0.0), (0.38, -0.05)):
            fr = 1 + i * period + ph * period
            p = supine()
            p['Spine2'] = ((-1, 0, dz * 0.9), (0, 0, 1))
            vic.key(fr, p)
            r = kneel(0.1, 0.40, 0.45 + dz, face=(0, -1, 0), lean=1.25)
            hand = (0.1, 0.0, 0.235 + dz * 0.8)
            r['armL'] = {'ik': (hand[0] + 0.012, hand[1] + 0.01, hand[2] + 0.028), 'pole': (0.3, 1, 0)}
            r['armR'] = {'ik': (hand[0] - 0.012, hand[1] + 0.01, hand[2]), 'pole': (-0.3, 1, 0)}
            r['handL'] = ((0.15, -1, -0.15), (0, 0, -1))
            r['handR'] = ((-0.15, -1, -0.15), (0, 0, -1))
            r['curlL'] = 0.55
            r['curlR'] = 0.3
            r['Neck'] = ((0, -0.8, 1), (0, -1, -0.8))
            r['Head'] = ((0, -1, 0.45), (0, -0.35, -1))
            res.key(fr, r)
    camera((0.75, -2.1, 1.05), (0.1, 0.12, 0.4), lens=42)


def sc_hands():
    reset(frames=75)
    studio(key=(1.2, -2.2, 3.4), target=(0.1, 0, 0.25), power=650)
    vic, res = victim(), rescuer()
    vic.key(1, supine())
    base = kneel(0.1, 0.42, 0.47, face=(0, -1, 0), lean=1.2)
    C = V((0.1, 0.0, 0.235))

    def P(lh, rh, cl, cr):
        r = dict(base)
        r['armR'] = {'ik': T(rh), 'pole': (-0.3, 1, -0.2)}
        r['armL'] = {'ik': T(lh), 'pole': (0.3, 1, -0.2)}
        r['handL'] = ((0.15, -1, -0.15), (0, 0, -1))
        r['handR'] = ((-0.15, -1, -0.15), (0, 0, -1))
        r['curlL'], r['curlR'] = cl, cr
        look(r, C, (0.1, 0.1, 0.95))
        return r
    up = V((0, 0.05, 0.18))
    p0 = P(C + up + V((0.1, 0.08, 0.06)), C + up + V((-0.08, 0.02, 0)), 0.1, 0.1)
    p1 = P(C + up + V((0.08, 0.08, 0.08)), C + V((-0.012, 0.01, 0)), 0.1, 0.12)
    p2 = P(C + V((0.012, 0.01, 0.03)), C + V((-0.012, 0.01, 0)), 0.6, 0.35)
    keys(res, 1, 8, p0, p0)
    keys(res, 8, 28, p0, p1)
    keys(res, 28, 48, p1, p2)
    keys(res, 48, 75, p2, p2, step=9)
    camera((0.55, -0.75, 1.15), (0.08, 0.02, 0.22), lens=40)


# ---------------- unresponsive
def sc_shake():
    reset(frames=60)
    studio(key=(1.4, -2.4, 3.4), target=(-0.1, 0, 0.3), power=700)
    vic, res = victim(), rescuer()
    vic.key(1, supine())
    sL, _ = surface((-0.04, 0.13, 1))
    sR, _ = surface((-0.04, -0.13, 1))
    for f in range(1, 61, 2):
        s = math.sin(f / 60 * 2 * math.pi * 6)
        p = supine()
        p['Spine2'] = ((-1, 0.02 * s, 0.0), (0, 0.04 * s, 1))
        p['Head'] = ((-1, 0.05 * s, 0.0), (0, 0.1 * s, 1))
        vic.key(f, p)
        r = kneel(0.0, 0.42, 0.45, face=(0, -1, 0), lean=1.3)
        d = V((0.02 * s, 0, 0))
        r['armL'] = {'ik': palm_on(sL + d, (0, -1, -0.4), (0, 0.3, 1)), 'pole': (0.8, 0.6, 0)}
        r['armR'] = {'ik': palm_on(sR + d, (0, -1, -0.4), (0, -0.3, 1)), 'pole': (-0.8, 0.6, 0)}
        r['handL'] = ((0, -1, -0.4), (0, -0.3, -1))
        r['handR'] = ((0, -1, -0.4), (0, 0.3, -1))
        r['curlL'] = r['curlR'] = 0.35
        look(r, (-0.3, 0, 0.1), (0.0, 0.15, 0.9))
        res.key(f, r)
    cam((-0.12, 0.05, 0.25), -55, 32, 1.55, lens=40)


def sc_shout():
    reset(frames=72)
    studio(key=(1.8, -2.4, 3.4), target=(0.1, 0.2, 0.6), power=700)
    vic, res = victim(), rescuer()
    vic.key(1, supine())
    for f in list(range(1, 73, 3)) + [72]:
        t = math.sin(f / 72 * 2 * math.pi)
        r = kneel(0.12, 0.48, 0.5, face=(0, -1, 0), lean=0.15)
        head = V((0.12, 0.40, 1.05))
        yaw = V((0.9 * t + 0.25, -0.6, 0.15)).normalized()
        look(r, head + yaw, head - V((0, 0, 0.1)))
        mouth = head + yaw * 0.13 - V((0, 0, 0.05))
        side = lat(yaw)
        r['armR'] = {'ik': T(mouth - side * 0.05 - yaw * 0.03), 'pole': (0, 0.4, -1)}
        r['handR'] = (T((yaw * 0.3 + Z).normalized()), T(side))
        r['curlR'] = 0.3
        r['armL'] = {'ik': (0.1, 0.14, 0.19), 'pole': (0.8, 0.5, 0.2)}
        r['handL'] = ((0, -1, -0.4), (0, 0, -1))
        res.key(f, r)
    camera((1.45, -1.55, 1.05), (0.1, 0.22, 0.62), lens=40)


def _airway(vic, t):
    p = supine()
    p['Neck'] = ((-1, 0, 0.06 - 0.25 * t), (0.25 * t, 0, 1))
    p['Head'] = ((-1, 0, -0.5 * t), (0.5 * t, 0, 1))
    return p


def sc_tilt():
    reset(frames=80)
    studio(key=(1.0, -2.0, 3.0), target=(-0.3, 0, 0.15), power=600)
    vic, res = victim(), rescuer()
    fl, cl = _airway_hands(vic)
    for f in list(range(1, 81, 2)) + [80]:
        t = smooth01((f - 10) / 20) if f < 55 else 1 - smooth01((f - 60) / 16)
        p = _airway(vic, t)
        vic.key(f, p)
        r = _airway_rescuer(vic, p, fl, cl)
        look(r, (-0.28, 0, 0.12), (-0.2, 0.2, 0.9))
        res.key(f, r)
    cam((-0.27, 0.02, 0.15), -80, 18, 0.95, lens=45, dof=5)


def sc_look():
    reset(frames=90)
    studio(key=(1.4, -2.2, 3.0), target=(0, 0.1, 0.2), power=650)
    vic, res = victim(), rescuer()
    fl, cl = _airway_hands(vic)
    for f in list(range(1, 91, 3)) + [90]:
        b = (1 - math.cos(f / 90 * 2 * math.pi)) / 2
        p = _airway(vic, 1)
        p['Spine1'] = ((-1, 0, 0.04 * b), (0, 0, 1))
        p['Spine2'] = ((-1, 0, 0.07 * b), (0, 0, 1))
        vic.key(f, p)
        r = _airway_rescuer(vic, p, fl, cl, kx=-0.12, ky=0.5, lean=1.2)
        r['hips']['pos'] = (-0.12, 0.52, 0.5)
        r['chest'] = ((-0.3, -1, -0.45), (0, -0.4, -1))
        r['Neck'] = ((-0.4, -1, -0.2), (0.3, -0.3, -1))
        r['Head'] = ((-0.9, -0.3, 0.1), (0.8, -0.1, -0.6))
        res.key(f, r)
    cam((-0.05, 0.05, 0.25), -35, 28, 1.45, lens=38)


def sc_still():
    reset(frames=60)
    studio(key=(1.2, -2.2, 3.0), target=(-0.4, 0, 0.2), power=650)
    vic, res = victim(), rescuer()
    vic.key(1, supine())
    sl, _ = surface((-0.3, 0.5, 0.09), (0, -1, 0))
    sr, _ = surface((-0.3, -0.5, 0.09), (0, 1, 0))
    for f in (1, 31, 60):
        b = 0 if f != 31 else 1
        p = supine()
        p['Spine2'] = ((-1, 0, 0.04 * b), (0, 0, 1))
        vic.key(f, p)
        r = kneel(-0.78, 0.0, 0.45, face=(1, 0, 0), lean=1.25)
        r['armL'] = {'ik': palm_on(sl, (1, 0, -0.15), (0, 1, 0), back=0.05), 'pole': (-0.3, 1, 0.4)}
        r['armR'] = {'ik': palm_on(sr, (1, 0, -0.15), (0, -1, 0), back=0.05), 'pole': (-0.3, -1, 0.4)}
        r['handL'] = ((1, 0, -0.15), (0, -1, 0))
        r['handR'] = ((1, 0, -0.15), (0, 1, 0))
        r['curlL'] = r['curlR'] = 0.15
        look(r, (-0.3, 0, 0.1), (-0.72, 0, 0.9))
        res.key(f, r)
    cam((-0.45, 0, 0.25), -60, 25, 1.5, lens=40)


def sc_blanket():
    reset(frames=75)
    studio(key=(1.6, -2.2, 3.2), target=(0.4, 0, 0.15), power=700)
    vic = victim()
    vic.key(1, supine())
    bpy.context.scene.frame_set(1)
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.parent == vic.arm:
            o.modifiers.new('col', 'COLLISION')
            o.collision.thickness_outer = 0.01
    fl = bpy.data.objects['Floor']
    fl.modifiers.new('col', 'COLLISION')
    bl = plane((0.62, 0, 0.55), 1.55, 1.05, mat('foil', '#d9a93a', rough=0.28, metal=0.95), name='blanket', sub=40)
    cm = bl.modifiers.new('cloth', 'CLOTH')
    cm.settings.quality = 6
    cm.settings.mass = 0.15
    cm.settings.bending_stiffness = 0.05
    cm.settings.air_damping = 3.0
    cm.collision_settings.use_self_collision = False
    cm.collision_settings.distance_min = 0.006
    cm.point_cache.frame_start, cm.point_cache.frame_end = 1, 75
    smooth(bl, sub=1)
    camera((1.55, -1.55, 1.2), (0.35, 0.0, 0.12), lens=36)


def sc_legs():
    reset(frames=75)
    studio(key=(1.6, -2.4, 3.2), target=(0.8, 0, 0.3), power=700)
    vic, res = victim(), rescuer()
    box((1.3, 0, 0.2), (0.3, 0.55, 0.4), mat('crate', '#5b5f66', rough=0.7), bevel=0.02)

    def P(t):
        p = supine()
        for s, sg in (('L', 1), ('R', -1)):
            a0, a1 = V((1.22, 0.1 * sg, 0.085)), V((1.3, 0.1 * sg, 0.48))
            a = a0.lerp(a1, t)
            p['leg' + s] = {'ik': T(a), 'pole': (0.2, 0, 1)}
            p['foot' + s] = (T((Z + V((0.3, 0, 0))).normalized()), (1, 0, 0.1))
        return p
    for f in list(range(1, 76, 2)) + [75]:
        t = smooth01((f - 8) / 32)
        p = P(t)
        vic.key(f, p)
        r = kneel(1.75 - 0.08 * t, 0.0, 0.47 + 0.08 * t, face=(-1, 0, 0), lean=0.9 - 0.4 * t)
        aL, aR = vic.wpos(p, 'LeftFoot'), vic.wpos(p, 'RightFoot')
        r['armL'] = {'ik': T(aL + V((0.02, 0.03, -0.05))), 'pole': (0.3, 1, -0.5)}
        r['armR'] = {'ik': T(aR + V((0.02, -0.03, -0.05))), 'pole': (0.3, -1, -0.5)}
        r['handL'] = ((-1, 0, -0.1), (0, 0, 1))
        r['handR'] = ((-1, 0, -0.1), (0, 0, 1))
        r['curlL'] = r['curlR'] = 0.55
        res.key(f, r)
    camera((1.35, -1.85, 1.05), (0.75, 0.0, 0.3), lens=36)


def _convulse(f, amp=1.0):
    p = supine()
    i = f // 3
    a = amp
    p['armL'] = {'dirs': ((0.6 + 0.3 * nz(i, 1) * a, 0.7, 0.2 + 0.3 * nz(i, 2) * a), (0.2 + 0.5 * nz(i, 3) * a, 0.3, 0.7))}
    p['armR'] = {'dirs': ((0.6 + 0.3 * nz(i, 4) * a, -0.7, 0.2 + 0.3 * nz(i, 5) * a), (0.2 + 0.5 * nz(i, 6) * a, -0.3, 0.7))}
    p['Head'] = ((-1, 0.12 * nz(i, 7) * a, 0.1 * nz(i, 8) * a), (0.3 * nz(i, 9) * a, 0.2 * nz(i, 10) * a, 1))
    p['legL'] = {'dirs': ((1, 0.08 + 0.1 * nz(i, 11) * a, 0.15 + 0.15 * nz(i, 12) * a), (1, 0.03, -0.15))}
    p['legR'] = {'dirs': ((1, -0.08 + 0.1 * nz(i, 13) * a, 0.15 + 0.15 * nz(i, 14) * a), (1, -0.03, -0.15))}
    p['curlL'] = p['curlR'] = 0.8
    return p


def chair(loc, rot=0):
    m = mat('wood', '#8a5a3b', rough=0.55)
    parts = [box((0, 0, 0.45), (0.42, 0.42, 0.04), m), box((0, 0.19, 0.72), (0.42, 0.04, 0.5), m)]
    for dx in (-0.18, 0.18):
        for dy in (-0.18, 0.18):
            parts.append(cyl((dx, dy, 0.225), 0.018, 0.45, m))
    root = bpy.data.objects.new('chair', None)
    bpy.context.collection.objects.link(root)
    for o in parts:
        o.parent = root
    root.location = loc
    root.rotation_euler = (0, 0, rot)
    return root


def sc_clear():
    reset(frames=90)
    studio(key=(1.8, -2.4, 3.4), target=(0.3, -0.4, 0.3), power=750)
    vic, res = victim(), rescuer()
    ch = chair((0.3, -0.62, 0), rot=0)
    for f in range(1, 91, 3):
        vic.key(f, _convulse(f))
    for f in list(range(1, 91, 3)) + [90]:
        t = smooth01((f - 10) / 45)
        cy = -0.62 - 0.55 * t
        ch.location = (0.3, cy, 0)
        ch.keyframe_insert('location', frame=f)
        r = stand(0.3, cy - 0.55, face=(0, 1, 0), hz=0.92)
        r['chest'] = ((0, 0.55, 1), (0, 1, -0.4))
        r['armL'] = {'ik': (0.5, cy - 0.2, 0.9), 'pole': (1, -0.3, -0.5)}
        r['armR'] = {'ik': (0.1, cy - 0.2, 0.9), 'pole': (-1, -0.3, -0.5)}
        r['handL'] = ((0, 1, 0.3), (0, 0, -1))
        r['handR'] = ((0, 1, 0.3), (0, 0, -1))
        r['curlL'] = r['curlR'] = 0.6
        look(r, (0.2, 0.0, 0.1), (0.3, cy - 0.5, 1.6))
        res.key(f, r)
    camera((2.0, -2.0, 1.55), (0.25, -0.45, 0.35), lens=34)


def sc_cushion():
    reset(frames=60)
    studio(key=(1.2, -2.2, 3.0), target=(-0.4, 0, 0.2), power=650)
    vic, res = victim(), rescuer()
    box((-0.34, 0, 0.035), (0.34, 0.42, 0.07), mat('jacket', '#2f3a4f', rough=0.9), bevel=0.03)
    for f in range(1, 61, 3):
        p = _convulse(f, 0.8)
        p['Neck'] = ((-1, 0, 0.2), (0, 0, 1))
        p['Head'] = ((-1, 0.1 * nz(f // 3, 7), 0.1), (0.3 * nz(f // 3, 9), 0, 1))
        vic.key(f, p)
    r = kneel(-0.9, 0.0, 0.46, face=(1, 0, 0), lean=1.0)
    r['armL'] = {'ik': (-0.46, 0.2, 0.12), 'pole': (-0.3, 1, 0.3)}
    r['armR'] = {'ik': (-0.46, -0.2, 0.12), 'pole': (-0.3, -1, 0.3)}
    r['handL'] = ((1, -0.3, 0.05), (0, -1, 0))
    r['handR'] = ((1, 0.3, 0.05), (0, 1, 0))
    r['curlL'] = r['curlR'] = 0.15
    look(r, (-0.3, 0, 0.1), (-0.85, 0, 0.95))
    res.key(1, r)
    camera((0.4, -1.35, 0.95), (-0.45, 0.0, 0.25), lens=40)


def sc_nohold():
    reset(frames=60)
    studio(key=(1.6, -2.4, 3.2), target=(0.1, 0.2, 0.4), power=700)
    vic, res = victim(), rescuer()
    for f in range(1, 61, 3):
        vic.key(f, _convulse(f))
    r = kneel(0.15, 0.62, 0.5, face=(0, -1, 0), lean=0.25)
    r['armL'] = {'ik': (0.32, 0.38, 0.95), 'pole': (1, 0.4, -0.6)}
    r['armR'] = {'ik': (-0.02, 0.38, 0.95), 'pole': (-1, 0.4, -0.6)}
    r['handL'] = ((0.1, -0.2, 1), (0, -1, 0))
    r['handR'] = ((-0.1, -0.2, 1), (0, -1, 0))
    look(r, (0.1, 0, 0.1), (0.15, 0.55, 1.05))
    res.key(1, r)
    camera((1.2, -1.6, 1.1), (0.1, 0.25, 0.4), lens=38)


# ---------------- recovery position
def _pls_side():
    p = supine(x=0.33, y=0.1, z=0.16)
    p['hips'] = {'pos': (0.33, 0.1, 0.165), 'up': (-1, 0.0, 0.0), 'fwd': (0, 1, 0.12)}
    p['Spine2'] = ((-1, 0, 0.02), (0, 1, 0.15))
    p['Neck'] = ((-1, 0.0, 0.05), (0, 1, 0.2))
    p['Head'] = ((-1, -0.1, 0.1), (0.1, 1, 0.1))
    p['armL'] = {'dirs': ((0.05, 1, -0.05), (-1, 0.05, -0.05))}
    p['handL'] = ((-1, 0, -0.05), (0, 0, 1))
    p['armR'] = {'ik': (-0.27, 0.14, 0.05), 'pole': (0.6, 0.6, 0.6)}
    p['handR'] = ((-1, 0.3, -0.1), (0, 0.2, 1))
    p['legR'] = {'ik': (0.75, 0.25, 0.085), 'pole': (0.2, 1, 0)}
    p['footR'] = ((1, 0, -0.3), (0, 0.5, 1))
    p['legL'] = {'dirs': ((1, -0.05, -0.08), (1, -0.1, -0.05))}
    p['footL'] = ((0.6, 0, -0.2), (0, 1, 0.3))
    return p


def _pls_pose(stage, t):
    p = supine()
    L_arm = {'dirs': ((0.05, 1, -0.05), (-1, 0.05, -0.05))}
    L_hand = ((-1, 0, -0.05), (0, 0, 1))
    if stage == 0:
        p['armL'] = blend({'x': p['armL']}, {'x': L_arm}, t)['x']
        p['handL'] = blend({'x': p['handL']}, {'x': L_hand}, t)['x']
        return p
    p['armL'] = L_arm
    p['handL'] = L_hand
    cheek = V((-0.24, 0.1, 0.16))
    knee_ik = V((0.8, -0.1, 0.085))
    if stage == 1:
        ta, tk = smooth01(t / 0.55), smooth01((t - 0.45) / 0.55)
        hr = V((0.95, -0.48, 0.04))
        p['armR'] = {'ik': T(hr.lerp(cheek, ta)), 'pole': T(V((0.2, -1, 0.2)).lerp(V((0.7, -0.3, 0.7)), ta))}
        p['handR'] = blend({'x': ((1, -0.05, -0.08), (0, 0, -1))}, {'x': ((-1, 0.2, 0.3), (0, 1, 0))}, ta)['x']
        a0 = V((1.24, -0.12, 0.085))
        p['legR'] = {'ik': T(a0.lerp(knee_ik, tk)), 'pole': (0, -0.2, 1)}
        p['footR'] = ((0.35, -0.05, 1), (1, 0, 0.1)) if tk < 0.5 else ((1, 0, -0.5), (0, 0, 1))
        return p
    p['armR'] = {'ik': T(cheek), 'pole': (0.7, -0.3, 0.7)}
    p['handR'] = ((-1, 0.2, 0.3), (0, 1, 0))
    p['legR'] = {'ik': T(knee_ik), 'pole': (0, -0.2, 1)}
    p['footR'] = ((1, 0, -0.5), (0, 0, 1))
    if stage == 2:
        side = _pls_side()
        side['legL'] = {'dirs': p['legL']['dirs']} if False else side['legL']
        out = blend(p, side, t)
        return out
    return _pls_side()


def _pls_scene(stage, frames=75, cam=None):
    reset(frames=frames)
    studio(key=(1.6, -2.2, 3.4), target=(0.3, 0, 0.1), power=700)
    vic, res = victim(), rescuer()
    for f in list(range(1, frames + 1, 2)) + [frames]:
        t = smooth01((f - 8) / (frames * 0.6)) if stage < 3 else 0
        p = _pls_pose(stage, t)
        if stage == 3:
            b = (1 - math.cos(f / frames * 2 * math.pi)) / 2
            p['Spine2'] = ((-1, 0, 0.02 + 0.04 * b), (0, 1, 0.15))
        vic.key(f, p)
        if stage == 3:
            r = kneel(0.95, 0.62, 0.47, face=(-0.3, -1, 0), lean=0.5)
            r['armR'] = {'ik': (0.45, 0.28, 0.33), 'pole': (-1, 0.5, 0)}
            r['handR'] = ((-0.4, -1, -0.3), (0, 0, -1))
            look(r, (-0.2, 0.1, 0.15), (0.95, 0.5, 1.0))
        else:
            r = kneel(0.2, 0.55, 0.47, face=(0, -1, 0), lean=0.95)
            if stage == 0:
                wl = vic.wpos(p, 'LeftHand')
                el = vic.wpos(p, 'LeftForeArm')
                r['armL'] = {'ik': T(wl + V((0.03, 0.02, 0.06))), 'pole': (1, 1, 0)}
                r['armR'] = {'ik': T(el + V((0, 0.02, 0.06))), 'pole': (-1, 1, 0)}
                r['handL'] = ((0, -1, -0.5), (0, 0, -1))
                r['handR'] = ((0, -1, -0.5), (0, 0, -1))
                r['curlL'] = r['curlR'] = 0.5
                look(r, T(wl), (0.2, 0.4, 0.95))
            else:
                hr = vic.wpos(p, 'RightHand')
                kn = vic.wpos(p, 'RightLeg')
                r['armR'] = {'ik': T(hr + V((0.02, 0.03, 0.07))), 'pole': (-1, 1, 0.2)}
                r['handR'] = ((-0.5, -1, -0.4), (0, 0, -1))
                r['armL'] = {'ik': T(kn + V((0.0, 0.03, 0.08))), 'pole': (1, 1, 0.2)}
                r['handL'] = ((0, -1, -0.8), (0, 0, -1))
                r['curlL'] = r['curlR'] = 0.55
                look(r, T(kn.lerp(hr, 0.5)), (0.2, 0.4, 0.95))
        res.key(f, r)
    if cam:
        camera(*cam)
    else:
        camera((0.9, -1.7, 1.6), (0.25, 0.08, 0.12), lens=36)


def sc_pls1(): _pls_scene(0)
def sc_pls2(): _pls_scene(1, frames=90)
def sc_pls3(): _pls_scene(2, frames=80, cam=((-1.25, 0.95, 1.45), (0.3, 0.1, 0.1), 36))


def sc_pls4(): _pls_scene(3, frames=90, cam=((0.35, 1.65, 1.05), (0.3, 0.05, 0.12), 40))


def sc_cough():
    reset(frames=60)
    studio(key=(2.0, -2.4, 3.8), target=(0, 0, 1.1), power=800)
    vic, res = victim(), rescuer()
    for f in list(range(1, 61, 2)) + [60]:
        c = max(0, math.sin(f / 60 * 2 * math.pi * 3)) ** 3
        p = stand(0, 0, face=(0, -1, 0), hz=1.0)
        p['chest'] = ((0, -0.15 - 0.35 * c, 1), (0, -1, -0.2 - 0.4 * c))
        p['Head'] = ((0, -0.2 - 0.4 * c, 1), (0, -1, -0.1 - 0.3 * c))
        hz = 1.36 - 0.05 * c
        p['armL'] = {'ik': (0.06, -0.14 - 0.08 * c, hz), 'pole': (1, 0, -0.6)}
        p['armR'] = {'ik': (-0.06, -0.14 - 0.08 * c, hz), 'pole': (-1, 0, -0.6)}
        p['handL'] = ((-0.3, 0, 1), (-0.3, 1, 0))
        p['handR'] = ((0.3, 0, 1), (0.3, 1, 0))
        p['curlL'] = p['curlR'] = 0.35
        vic.key(f, p)
    r = stand(0.55, 0.12, face=(-1, -0.25, 0), hz=1.0)
    r['armR'] = {'ik': (0.13, 0.12, 1.25), 'pole': (0, 1, -0.6)}
    r['handR'] = ((-0.3, 0.2, 1), (-1, 0, 0))
    look(r, (0, -0.1, 1.5), (0.55, 0.1, 1.6))
    res.key(1, r)
    camera((1.35, -2.1, 1.45), (0.15, 0.0, 1.1), lens=40)


def sc_back():
    reset(frames=72)
    studio(key=(-1.6, -2.4, 3.8), target=(0, 0, 0.9), power=800)
    vic, res = victim(), rescuer()
    vp = stand(0, 0, face=(0, -1, 0), hz=0.98)
    vp['hips']['up'] = (0, -0.5, 1)
    vp['chest'] = ((0, -1, 0.35), (0, -0.35, -1))
    vp['Neck'] = ((0, -1, 0.1), (0, -0.2, -1))
    vp['Head'] = ((0, -1, -0.2), (0, 0.1, -1))
    vp['armL'] = {'dirs': ((0.15, -0.3, -1), (0.05, -0.2, -1))}
    vp['armR'] = {'dirs': ((-0.15, -0.3, -1), (-0.05, -0.2, -1))}
    vic.key(1, vp)
    backpt = vic.wpos(vp, 'Spine2') + V((0, 0.06, 0.11))
    chestpt = vic.wpos(vp, 'Spine2') + V((0, -0.05, -0.14))
    period = 24
    for f in list(range(1, 73, 2)) + [72]:
        ph = ((f - 1) % period) / period
        if ph < 0.32:
            lift = 0.16 * (1 - ph / 0.32)
        elif ph < 0.42:
            lift = 0.0
        else:
            lift = 0.16 * smooth01((ph - 0.42) / 0.58)
        r = stand(-0.42, 0.18, face=(1, -0.25, 0), hz=0.97)
        r['chest'] = ((0.35, -0.1, 1), (1, -0.25, -0.3))
        r['armL'] = {'ik': T(backpt + V((-0.05, 0.02, lift + 0.02))), 'pole': (-0.3, 1, 0.2)}
        r['handL'] = ((0.3, -1, 0), (0, 0.2, -1))
        r['curlL'] = 0.15
        r['armR'] = {'ik': T(chestpt + V((-0.08, 0, -0.03))), 'pole': (-0.4, -1, -0.3)}
        r['handR'] = ((1, 0.05, 0.1), (0, 0, 1))
        look(r, T(backpt), (-0.35, 0.18, 1.6))
        res.key(f, r)
    camera((-1.35, -1.9, 1.35), (-0.1, 0.0, 0.95), lens=38)


def sc_abdo():
    reset(frames=81)
    studio(key=(1.8, -2.6, 3.8), target=(0, 0, 1.1), power=800)
    vic, res = victim(), rescuer()
    period = 27
    for f in list(range(1, 82, 2)) + [81]:
        ph = ((f - 1) % period) / period
        k = math.sin(min(1, ph / 0.3) * math.pi) if ph < 0.3 else 0
        vp = stand(0, 0, face=(0, -1, 0), hz=1.0)
        vp['chest'] = ((0, -0.25 - 0.2 * k, 1), (0, -1, -0.2))
        vp['Head'] = ((0, -0.3 - 0.3 * k, 1), (0, -1, -0.3))
        vp['armL'] = {'dirs': ((0.3, -0.25, -1), (0.1, -0.5, -1))}
        vp['armR'] = {'dirs': ((-0.3, -0.25, -1), (-0.1, -0.5, -1))}
        vic.key(f, vp)
        navel = V((0, -0.14, 1.14)) + V((0, 0.035, 0.035)) * k
        r = stand(0, 0.24, face=(0, -1, 0), hz=0.98, spread=0.16)
        r['chest'] = ((0, -0.2, 1), (0, -1, -0.2))
        r['armR'] = {'ik': T(navel + V((-0.02, 0.0, 0))), 'pole': (-1, 0.3, -0.3)}
        r['handR'] = ((0.9, -0.2, 0.1), (0, 1, 0))
        r['curlR'] = 1.0
        r['armL'] = {'ik': T(navel + V((0.07, -0.02, 0.0))), 'pole': (1, 0.3, -0.3)}
        r['handL'] = ((-0.9, -0.3, -0.1), (0, 1, 0))
        r['curlL'] = 0.7
        look(r, (0.25, -0.6, 1.2), (0, 0.2, 1.62))
        r['Head'] = ((0.25, 0, 1), (0.6, -1, -0.2))
        res.key(f, r)
    camera((1.45, -1.85, 1.3), (0.02, 0.0, 1.08), lens=38)


# ---------------- infant
def baby():
    return Char('Baby', body='#e6dfd8', joints='#9a8f86', scale=0.4)


def sc_bback():
    reset(frames=72)
    studio(key=(1.6, -2.2, 3.4), target=(0, 0, 0.7), power=750)
    res = rescuer()
    bb = baby()
    box((0.0, 0.25, 0.23), (0.45, 0.45, 0.46), mat('stool', '#5b5f66', rough=0.7), bevel=0.02)
    r = seated(0.0, 0.25, face=(0, -1, 0), hz=0.56)
    elbow = V((0.14, 0.02, 0.72))
    handp = V((0.04, -0.3, 0.6))
    r['armL'] = {'ik': T(handp), 'pole': (1, 0.6, -0.4)}
    r['handL'] = (T((handp - elbow).normalized()), (0, 0, 1))
    r['curlL'] = 0.4
    r['chest'] = ((0, -0.35, 1), (0, -1, -0.4))
    fa = (handp - elbow).normalized()
    babyhip = elbow + fa * 0.02 + V((0, 0, 0.09))
    bp = {'hips': {'pos': T(babyhip), 'up': T(fa), 'fwd': (0, 0, -1)},
          'chest': (T(fa), (0, 0, -1)), 'Neck': (T(fa), (0, 0, -1)), 'Head': (T((fa + V((0, 0, -0.1))).normalized()), (0, 0.2, -1)),
          'headscale': 1.55,
          'armL': {'dirs': ((0.4, -0.2, -1), (0.2, -0.3, -1))}, 'armR': {'dirs': ((-0.4, -0.2, -1), (-0.2, -0.3, -1))},
          'legL': {'dirs': ((0.6, 0.5, -0.6), (0.2, 0.4, -1))}, 'legR': {'dirs': ((-0.6, 0.5, -0.6), (-0.2, 0.4, -1))}}
    bb.key(1, bp)
    back = bb.wpos(bp, 'Spine2') + V((0, 0, 0.06))
    period = 24
    for f in list(range(1, 73, 2)) + [72]:
        ph = ((f - 1) % period) / period
        if ph < 0.32:
            lift = 0.16 * (1 - ph / 0.32)
        elif ph < 0.42:
            lift = 0.0
        else:
            lift = 0.16 * smooth01((ph - 0.42) / 0.58)
        rr = dict(r)
        rr['armR'] = {'ik': T(back + V((-0.02, 0.05, lift + 0.03))), 'pole': (-1, 0.4, 0)}
        rr['handR'] = ((0.1, -1, 0), (0, 0, -1))
        look(rr, T(back), (0, 0.15, 1.2))
        res.key(f, rr)
    camera((1.0, -1.35, 1.2), (0.05, -0.12, 0.72), lens=40)


def sc_bchest():
    reset(frames=66)
    studio(key=(1.5, -2.2, 3.4), target=(0, 0, 0.9), power=750)
    res = rescuer()
    bb = baby()
    box((0, 0, 0.4), (0.9, 0.6, 0.8), mat('table', '#5b5f66', rough=0.6), bevel=0.02)
    bz = 0.8 + 0.045
    bp = {'hips': {'pos': (0.12, 0, bz), 'up': (-1, 0, 0), 'fwd': (0, 0, 1)}, 'headscale': 1.55,
          'chest': ((-1, 0, 0), (0, 0, 1)), 'Neck': ((-1, 0, 0), (0, 0, 1)), 'Head': ((-1, 0, 0), (0, 0, 1)),
          'armL': {'dirs': ((0.2, 1, 0.2), (0.6, 0.4, 0.4))}, 'armR': {'dirs': ((0.2, -1, 0.2), (0.6, -0.4, 0.4))},
          'legL': {'dirs': ((1, 0.35, 0.3), (0.6, 0.2, -0.4))}, 'legR': {'dirs': ((1, -0.35, 0.3), (0.6, -0.2, -0.4))}}
    bb.key(1, bp)
    chest = bb.wpos(bp, 'Spine2') + V((0.0, 0, 0.055))
    head = bb.wpos(bp, 'Head') + V((-0.03, 0, 0.05))
    period = 30 * 60 / 110
    for i in range(5):
        for ph, dz in ((0, 0.0), (0.4, -0.03)):
            f = 1 + (i + ph) * period
            r = stand(0.02, 0.55, face=(0, -1, 0), hz=1.0)
            r['chest'] = ((0, -0.5, 1), (0, -1, -0.5))
            r['armR'] = {'ik': T(chest + V((0.025, 0.07, 0.05 + dz))), 'pole': (-0.4, 1, 0.2)}
            r['handR'] = ((-0.1, -0.5, -1), (0, 1, -0.2))
            r['curlR'] = {'Index': 0.0, 'Middle': 0.0, 'Ring': 1.1, 'Pinky': 1.1, 'Thumb': 0.8}
            r['armL'] = {'ik': T(head + V((0.02, 0.06, 0.03))), 'pole': (0.2, 1, 0.3)}
            r['handL'] = ((-0.4, -1, -0.2), (0, 0, -1))
            r['curlL'] = 0.2
            look(r, T(chest), (0.02, 0.45, 1.62))
            res.key(f, r)
    camera((0.95, -1.05, 1.45), (0.08, 0.0, 0.88), lens=42)


# ---------------- sitting (chest pain / stroke)
def wall():
    return box((-0.42, 0, 0.75), (0.1, 3.0, 1.5), mat('wall', '#2a2b30', rough=0.9), bevel=0.0)


def sc_sit():
    reset(frames=90)
    studio(key=(1.8, -2.2, 3.4), target=(0.1, 0, 0.5), power=750)
    wall()
    vic, res = victim(), rescuer()
    p0 = sitfloor(-0.12, 0, face=(1, 0, 0), lean=0.3)
    vic.key(1, p0)
    sh = vic.wpos(p0, 'LeftArm') + V((0.01, 0.0, 0.07))
    for f in list(range(1, 91, 3)) + [90]:
        b = (1 - math.cos(f / 90 * 2 * math.pi * 2)) / 2
        p = sitfloor(-0.12, 0, face=(1, 0, 0), lean=0.3)
        p['chest'] = ((-0.2 + 0.03 * b, 0, 1), (1, 0, 0.05 * b))
        p['armR'] = {'ik': (0.04, -0.03, 0.57), 'pole': (0.2, -1, -0.5)}
        p['handR'] = ((0.1, 1, 0.3), (-1, 0, 0))
        p['curlR'] = 0.4
        p['Head'] = ((-0.1, 0, 1), (1, 0, -0.2))
        vic.key(f, p)
    r = kneel(0.28, 0.5, 0.45, face=(-0.35, -1, 0), lean=0.5)
    r['armR'] = {'ik': palm_on(sh, (-0.3, -1, -0.5), (0, 0.3, 1)), 'pole': (-1, 0.3, -0.3)}
    r['handR'] = ((-0.3, -1, -0.5), (0, -0.3, -1))
    r['curlR'] = 0.3
    look(r, (-0.05, 0, 0.85), (0.22, 0.42, 0.95))
    res.key(1, r)
    cam((0.02, 0.1, 0.55), -40, 18, 1.9, lens=40)


def sc_loosen():
    reset(frames=75)
    studio(key=(1.8, -2.2, 3.4), target=(0.1, 0, 0.6), power=750)
    wall()
    vic, res = victim(), rescuer()
    p = sitfloor(-0.12, 0, face=(1, 0, 0), lean=0.3)
    p['Head'] = ((-0.2, 0, 1), (1, 0, 0.05))
    vic.key(1, p)
    nk = vic.wpos(p, 'Neck')
    bpy.context.scene.frame_set(1)
    col = torus(T(nk + V((0.01, 0, -0.02))), 0.065, 0.014, mat('shirt', '#f5f5f7', rough=0.6), name='collar')
    orient(col, x=(0, 1, 0), z=(0.3, 0, 1))
    tie_m = mat('tie', '#a3162a', rough=0.45)
    knot = box(T(nk + V((0.075, 0, -0.04))), (0.03, 0.035, 0.04), tie_m, bevel=0.012, name='knot')
    blade = box(T(nk + V((0.105, 0, -0.2))), (0.012, 0.06, 0.28), tie_m, bevel=0.005, name='blade')
    orient(blade, x=(1, 0, 0.2), y=(0, 1, 0))
    for o in (col, blade):
        vic.attach(o, 'Spine2')
    k0 = nk + V((0.075, 0, -0.04))
    for f in list(range(1, 76, 3)) + [75]:
        t = smooth01((f - 10) / 40)
        kp = k0 + V((0.012, 0, -0.1 * t))
        knot.location = kp
        knot.keyframe_insert('location', frame=f)
        r = kneel(0.45, -0.25, 0.47, face=(-1, 0.4, 0), lean=0.6)
        r['armR'] = {'ik': T(kp + V((0.03, -0.03, -0.02))), 'pole': (0.3, -1, -0.5)}
        r['handR'] = ((-0.8, 0.3, 0.3), (-0.3, 1, 0))
        r['curlR'] = 0.6
        r['armL'] = {'ik': T(nk + V((0.1, 0.07, -0.02))), 'pole': (0.3, 1, -0.5)}
        r['handL'] = ((-0.5, -0.3, 0.8), (-1, 0, 0))
        r['curlL'] = 0.35
        look(r, T(kp), (0.4, -0.2, 1.05))
        res.key(f, r)
    camera((1.05, -0.95, 0.95), (0.0, 0.0, 0.72), lens=45, dof=5)


def sc_aspirin():
    reset(frames=60)
    studio(key=(1.2, -1.8, 2.6), target=(0.25, -0.2, 0.55), power=600)
    wall()
    vic, res = victim(), rescuer()
    vic.key(1, sitfloor(-0.12, 0, face=(1, 0, 0), lean=0.3))
    palm = V((0.3, -0.16, 0.6))
    pill = cyl(T(palm), 0.011, 0.005, mat('pill', '#ffffff', rough=0.7), bevel=0.0015, name='pill')
    fd = V((-0.6, 0.8, 0.05))
    for f in (1, 30, 60):
        s = 0.008 if f == 30 else 0.0
        r = kneel(0.62, -0.5, 0.45, face=(-0.6, 0.8, 0), lean=0.55)
        c = palm + V((0, 0, s))
        r['armR'] = {'ik': palm_on(c, fd, (0, 0, -1), back=0.05, lift=0.0), 'pole': (0.5, -1, -0.5)}
        r['handR'] = (T(fd), (0, 0, 1))
        r['curlR'] = 0.25
        look(r, T(palm), (0.55, -0.42, 0.95))
        res.key(f, r)
    r1 = kneel(0.62, -0.5, 0.45, face=(-0.6, 0.8, 0), lean=0.55)
    r1.update({'armR': {'ik': palm_on(palm, fd, (0, 0, -1), back=0.05, lift=0.0), 'pole': (0.5, -1, -0.5)}, 'handR': (T(fd), (0, 0, 1)), 'curlR': 0.25})
    res.key(1, r1)
    top, _ = surface(T(palm + V((0, 0, 0.3))))
    pill.location = top + V((0, 0, 0.004))
    res.attach(pill, 'RightHand')
    cam(T(top), 30, 38, 0.55, lens=55, dof=2.8, clip=0.1)


def sc_epipen():
    reset(frames=90)
    studio(key=(1.6, -2.0, 3.0), target=(0.2, -0.1, 0.25), power=650)
    wall()
    vic, res = victim(), rescuer()
    p = sitfloor(-0.12, 0, face=(1, 0, 0), lean=0.3, knees=False)
    vic.key(1, p)
    mid = vic.wpos(p, 'RightUpLeg').lerp(vic.wpos(p, 'RightLeg'), 0.55)
    side, _ = surface(T(mid + V((0, -0.5, 0.01))), (0, 1, 0))
    pen = cyl((0, 0, 0), 0.016, 0.15, mat('pen', '#f2f2f2', rough=0.35), name='pen', bevel=0.004)
    tip = cyl((0, 0, -0.085), 0.015, 0.02, mat('tip', '#ff8a00', rough=0.4), bevel=0.003)
    band = cyl((0, 0, 0.03), 0.0165, 0.04, mat('lbl', '#ff9f0a', rough=0.4))
    tip.parent = band.parent = pen
    kx, ky = side.x + 0.45, side.y - 0.3
    for o in bpy.data.objects:
        if o.parent == res.arm:
            o.hide_render = True
    for f in list(range(1, 91, 3)) + [90]:
        t = smooth01((f - 5) / 20)
        press = smooth01((f - 25) / 5) * 0.006
        pos = side + V((0, -0.095 - 0.2 * (1 - t) + press, 0.0))
        pen.location = pos
        orient(pen, z=(0, -1, 0.0), x=(1, 0, 0))
        pen.keyframe_insert('location', frame=f)
        pen.keyframe_insert('rotation_euler', frame=f)
        r = kneel(kx, ky, 0.44, face=(-1, 0.45, 0), lean=0.85)
        r['armR'] = {'ik': T(pos + V((0.055, -0.03, 0.0))), 'pole': (0.3, -1, -0.6)}
        r['handR'] = ((-1, 0, 0), (0, 1, 0))
        r['curlR'] = 1.0
        r['armL'] = {'ik': palm_on(mid + V((0.05, 0, 0.07)), (-0.3, 1, -0.3), (0, 0, 1)), 'pole': (1, 0.5, -0.5)}
        r['handL'] = ((-0.3, 1, -0.3), (0, 0, -1))
        r['curlL'] = 0.3
        look(r, T(side), (kx - 0.15, ky + 0.05, 0.95))
        res.key(f, r)
    cam(T(side + V((0.03, -0.1, 0.0))), -95, 28, 0.62, lens=42, dof=4)


def sc_armsup():
    reset(frames=90)
    studio(key=(1.8, -2.4, 3.6), target=(0, -0.2, 1.0), power=800)
    box((0, 0, 0.23), (0.4, 0.4, 0.46), mat('stool', '#5b5f66', rough=0.7), bevel=0.02)
    vic = victim()
    for f in list(range(1, 91, 3)) + [90]:
        t = smooth01((f - 15) / 40) if f < 70 else 1 - smooth01((f - 72) / 16)
        up = smooth01((f - 1) / 12) if f < 70 else 1
        p = seated(0, 0, face=(0, -1, 0), hz=0.54)
        p['armL'] = {'dirs': ((0.12, -1, -0.02 - 1.2 * (1 - up)), (0.05, -1, 0.0 - 1.0 * (1 - up)))}
        p['armR'] = {'dirs': ((-0.12, -1, -0.02 - 0.55 * t - 1.2 * (1 - up)), (-0.05, -1, -0.05 - 0.6 * t - 1.0 * (1 - up)))}
        p['handL'] = ((0, -1, 0), (0, 0, 1))
        p['handR'] = ((0, -1, -0.3 * t), (0.1, 0, 1))
        p['chest'] = ((0.03 * t, 0, 1), (0, -1, 0))
        vic.key(f, p)
    camera((1.35, -2.0, 1.35), (0, -0.25, 0.95), lens=40)


def sc_bad():
    reset(frames=90)
    studio(key=(1.8, -2.2, 3.4), target=(0, 0, 0.5), power=750)
    vic = victim()
    for f in list(range(1, 91, 3)) + [90]:
        s = math.sin(f / 90 * 2 * math.pi)
        p = sitfloor(0, 0, face=(1, -0.3, 0), lean=0.1)
        p['chest'] = ((0.1 * s, 0.1 * s, 1), (1, -0.3, -0.2))
        p['Head'] = ((0.25 + 0.1 * s, 0.1 * s, 1), (1, -0.3, -0.5))
        p['armR'] = {'ik': (0.12, -0.1, 0.98), 'pole': (-0.2, -1, 0.3)}
        p['handR'] = ((0.3, 0.6, 0.6), (-0.8, 0.3, 0))
        p['curlR'] = 0.3
        p['armL'] = {'ik': (-0.05, 0.3, 0.08), 'pole': (-1, 0.5, 0)}
        p['handL'] = ((0.6, 0.6, -0.2), (0, 0, -1))
        vic.key(f, p)
    camera((1.6, -1.3, 1.0), (0.1, 0, 0.55), lens=40)


# ---------------- phone / AED
def sc_call():
    """phone on the floor on speaker next to the victim, rescuer behind (DOF)"""
    reset(frames=60)
    studio(key=(1.2, -2.0, 3.0), target=(-0.2, -0.3, 0.1), power=650)
    vic, res = victim(), rescuer()
    vic.key(1, supine())
    scr = img_mat('scr', os.path.join(TEX, 'phone.png'), rough=0.12, emit_s=2.2)
    ph = phone(scr)
    ph.location = (-0.33, -0.36, 0.006)
    ph.rotation_euler = (0, 0, math.radians(-12))
    for f in list(range(1, 61, 3)) + [60]:
        p = supine()
        r = kneel(0.1, 0.40, 0.45, face=(0, -1, 0), lean=1.25)
        period = 30 * 60 / 110.0
        ph_ = ((f - 1) % period) / period
        dz = -0.05 if 0.25 < ph_ < 0.55 else 0.0
        r['hips'] = dict(r['hips'], pos=(0.1, 0.40, 0.45 + dz))
        hand = (0.1, 0.0, 0.235 + dz * 0.8)
        r['armL'] = {'ik': (hand[0] + 0.012, hand[1] + 0.01, hand[2] + 0.028), 'pole': (0.3, 1, 0)}
        r['armR'] = {'ik': (hand[0] - 0.012, hand[1] + 0.01, hand[2]), 'pole': (-0.3, 1, 0)}
        r['handL'] = ((0.15, -1, -0.15), (0, 0, -1))
        r['handR'] = ((-0.15, -1, -0.15), (0, 0, -1))
        r['curlL'], r['curlR'] = 0.55, 0.3
        res.key(f, r, fit=False)
        vic.key(f, p)
    cam((-0.33, -0.36, 0.02), -115, 42, 0.62, lens=50, dof=2.0)


def sc_aed():
    reset(frames=90)
    studio(key=(1.2, -2.0, 3.0), target=(0, 0, 0.1), power=650)
    vic = victim()
    vic.key(1, supine(x=0.75))
    m = mat('aedcase', '#169c55', rough=0.35, coat=0.4)
    body = box((0, 0, 0), (0.3, 0.1, 0.25), m, bevel=0.03, name='aed')
    face = plane((0, -0.0505, 0), 0.27, 0.225, img_mat('aedf', os.path.join(TEX, 'aed.png'), rough=0.35), x=(1, 0, 0), z=(0, -1, 0))
    face.parent = body
    handle = torus((0, 0, 0.13), 0.06, 0.012, mat('blk', '#1c1c1e', rough=0.5), rot=(math.pi / 2, 0, 0))
    handle.parent = body
    btn = cyl((0.1, -0.055, 0.08), 0.014, 0.01, mat('btn', '#30d158', emit='#30d158', emit_s=4), rot=(math.pi / 2, 0, 0))
    btn.parent = body
    for f in (1, 90):
        body.location = (0.02, -0.3, 0.126)
        body.rotation_euler = (0, 0, math.radians(-25 + (10 if f == 90 else 0)))
        body.keyframe_insert('location', frame=f)
        body.keyframe_insert('rotation_euler', frame=f)
    bm = btn.data.materials[0].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
    for f in range(1, 91, 15):
        bm.default_value = 6 if (f // 15) % 2 == 0 else 0.5
        bm.keyframe_insert('default_value', frame=f)
    camera((0.55, -1.25, 0.55), (0.0, -0.25, 0.14), lens=45, dof=3)


# ---------------- bleeding (right forearm on floor)
def _arm_out(p):
    p['armR'] = {'dirs': ((0.25, -1, -0.02), (0.35, -1, -0.02))}
    p['handR'] = ((0.35, -1, -0.02), (0, 0, 1))
    return p


def _bleed(stage):
    frames = {'press': 60, 'cloth': 90, 'bandage': 90, 'tourniquet': 72}[stage]
    reset(frames=frames)
    studio(key=(1.2, -2.4, 3.0), target=(0.1, -0.4, 0.1), power=650)
    vic, res = victim(), rescuer()
    p = _arm_out(supine())
    vic.key(1, p)
    fa, hd = vic.wpos(p, 'RightForeArm'), vic.wpos(p, 'RightHand')
    ax = (hd - fa).normalized()
    mid = fa.lerp(hd, 0.5)
    top, _ = surface(T(mid + V((0, 0, 0.5))))
    wound(T(top + V((0, 0, 0.001))), (0, 0, 1), r=0.028)
    g1 = box(T(top + V((0, 0, 0.007))), (0.09, 0.075, 0.012), mat('gz1', '#e8c9c4' if stage != 'press' else '#f4f2ee', rough=0.95), bevel=0.004)
    orient(g1, x=ax, z=(0, 0, 1))
    hands_at = top + V((0, 0, 0.013))
    if stage == 'cloth':
        g2 = box(T(top + V((0, 0, 0.02))), (0.095, 0.08, 0.014), M_gauze(), bevel=0.004)
        orient(g2, x=ax, z=(0, 0, 1))
        for f, z in ((1, 0.3), (15, 0.3), (32, 0.02)):
            g2.location = top + V((0, 0, z))
            g2.keyframe_insert('location', frame=f)
        hands_at = top + V((0, 0, 0.027))
    w = ax.cross(V((0, 0, 1)))
    a0, a1 = fa + ax * 0.06, hd - ax * 0.05
    rad = (top.z - mid.z) + 0.006
    if stage == 'bandage':
        cu = bpy.data.curves.new('band', 'CURVE')
        cu.dimensions = '3D'
        sp = cu.splines.new('POLY')
        turns, n = 4.5, 200
        sp.points.add(n - 1)
        for i in range(n):
            t = i / (n - 1)
            ang = t * turns * 2 * math.pi
            c = a0.lerp(a1, t)
            pt = c + V((0, 0, 1)) * math.cos(ang) * (rad + 0.012) + w * math.sin(ang) * (rad * 0.9 + 0.01)
            sp.points[i].co = (*pt, 1)
        cu.extrude = 0.026
        cu.bevel_depth = 0.0015
        cu.twist_mode = 'MINIMUM'
        bo = bpy.data.objects.new('band', cu)
        bpy.context.collection.objects.link(bo)
        bo.data.materials.append(M_gauze())
        for f, e in ((1, 0.0), (10, 0.0), (80, 1.0)):
            cu.bevel_factor_end = e
            cu.keyframe_insert('bevel_factor_end', frame=f)
    if stage == 'tourniquet':
        ua = vic.wpos(p, 'RightArm')
        tp = ua.lerp(fa, 0.62)
        axu = (fa - ua).normalized()
        ttop, _ = surface(T(tp + V((0, 0, 0.5))))
        r0 = ttop.z - tp.z
        strap = torus(T(tp), r0 + 0.006, 0.01, mat('strap', '#1c1c1e', rough=0.6), name='strap')
        orient(strap, z=axu, x=(0, 0, 1))
        strap.scale = (1, 1, 1.8)
        rod = cyl(T(ttop + V((0, 0, 0.018))), 0.006, 0.12, mat('rod', '#ff9f0a', rough=0.4), name='rod')
        side = V((axu.y, -axu.x, 0)).normalized()
        for f in range(1, frames + 1, 3):
            ang = (f - 1) / 36 * math.pi
            orient(rod, z=(axu * math.cos(ang) + side * math.sin(ang)), x=(0, 0, 1))
            rod.keyframe_insert('rotation_euler', frame=f)
        hands_at = ttop + V((0, 0, 0.02))
    kx, ky = hands_at.x - 0.02, hands_at.y - 0.36
    _hands_only(res)
    for f in list(range(1, frames + 1, 2)) + [frames]:
        ph = math.sin(f / 30 * 2 * math.pi * 0.8)
        r = kneel(kx, ky, 0.44, face=(0.05, 1, 0), lean=1.45)
        prz = -0.005 * max(0, ph) if stage in ('press', 'cloth') else 0
        fdR, fdL = V((0.25, 1, -0.25)), V((-0.1, 1, -0.25))
        if stage == 'bandage':
            t = smooth01((f - 10) / 70)
            c = a0.lerp(a1, t)
            ang = t * 4.5 * 2 * math.pi
            end = c + V((0, 0, 1)) * math.cos(ang) * (rad + 0.03) + w * math.sin(ang) * (rad + 0.03)
            r['armR'] = {'ik': T(end - fdR.normalized() * 0.06), 'pole': (-1, -0.5, 0)}
            r['armL'] = {'ik': palm_on(fa + V((0, 0, rad)), fdL, (0, 0, 1)), 'pole': (1, -0.5, 0)}
            r['handR'] = (T(fdR), (0, 0, -1))
            r['handL'] = (T(fdL), (0, 0, -1))
            r['curlR'] = 0.7
            r['curlL'] = 0.3
        elif stage == 'tourniquet':
            ang = (f - 1) / 36 * math.pi
            tipA = hands_at + (axu * math.cos(ang) + side * math.sin(ang)) * 0.055
            r['armR'] = {'ik': T(tipA - fdR.normalized() * 0.06 + V((0, 0, 0.02))), 'pole': (-1, -0.5, 0)}
            r['armL'] = {'ik': palm_on(tp + V((0, 0, r0)) + axu * 0.09, fdL, (0, 0, 1)), 'pole': (1, -0.5, 0)}
            r['handR'] = (T(fdR), (0, 0, -1))
            r['handL'] = (T(fdL), (0, 0, -1))
            r['curlR'] = 0.8
            r['curlL'] = 0.3
        else:
            c = V(hands_at) + V((0, 0, prz))
            if stage == 'cloth' and f < 36:
                c = c + V((0, 0, 0.14 * (1 - smooth01((f - 26) / 10))))
            r['armR'] = {'ik': palm_on(c, fdR, (0, 0, 1)), 'pole': (-1, -0.3, 0.2)}
            r['armL'] = {'ik': palm_on(c + V((0, 0, 0.028)), fdL, (0, 0, 1)), 'pole': (1, -0.3, 0.2)}
            r['handR'] = (T(fdR), (0, 0, -1))
            r['handL'] = (T(fdL), (0, 0, -1))
            r['curlR'], r['curlL'] = 0.25, 0.45
        look(r, T(mid), (kx, ky + 0.2, 0.85))
        res.key(f, r)
    _bleed_cam(mid)


def sc_press():
    _bleed('press')


def sc_cloth():
    _bleed('cloth')


def sc_bandage():
    _bleed('bandage')


def sc_tourniquet():
    _bleed('tourniquet')


def counter():
    box((0, 0.3, 0.45), (1.4, 0.6, 0.9), mat('counter', '#3a3b40', rough=0.35), bevel=0.01)
    box((0, 0.28, 0.9), (0.55, 0.4, 0.02), mat('sink', '#16171a', rough=0.2, metal=0.6), bevel=0.02)


def sc_water():
    reset(frames=60)
    studio(key=(1.0, -1.8, 2.8), target=(0, 0.2, 0.95), power=600)
    counter()
    vic = victim()
    p = stand(0.1, -0.35, face=(0, 1, 0), hz=1.0)
    p['armR'] = {'ik': (0.12, 0.08, 0.96), 'pole': (1, -0.3, -0.5)}
    p['hips'] = dict(p['hips'], pos=(0.1, -0.28, 0.98))
    p['handR'] = ((-0.05, 1, 0), (0, 0, 1))
    p['chest'] = ((0, 0.12, 1), (0, 1, -0.1))
    vic.key(1, p)
    mask(vic, keep=('RightArm', 'RightForeArm', 'RightHand'))
    fa, hd = vic.wpos(p, 'RightForeArm'), vic.wpos(p, 'RightHand')
    bx = fa.lerp(hd, 0.62)
    burn_at = bx + V((0, 0, 0.034))
    wound(T(burn_at + V((0, 0, 0.001))), (0, 0, 1), r=0.03)
    chrome = mat('chrome', '#d0d3d8', rough=0.12, metal=1.0)
    sx, sy = burn_at.x, burn_at.y
    top_z = burn_at.z + 0.24
    cyl((sx, sy + 0.25, (0.9 + top_z) / 2), 0.02, top_z - 0.9, chrome)
    box((sx, sy + 0.125, top_z), (0.03, 0.27, 0.03), chrome, bevel=0.012)
    cyl((sx, sy + 0.25, 0.93), 0.03, 0.06, chrome)
    cyl((sx, sy, top_z - 0.03), 0.017, 0.05, chrome)
    water = mat('water', '#cfeaff', rough=0.02, alpha=0.6, coat=1.0, emit='#bfe6ff', emit_s=0.4)
    L = top_z - 0.055 - burn_at.z
    st = cyl((sx, sy, burn_at.z + L / 2), 0.008, L, water, verts=24, name='stream')
    tx = bpy.data.textures.new('n', 'CLOUDS')
    tx.noise_scale = 0.015
    dm = st.modifiers.new('d', 'DISPLACE')
    dm.texture = tx
    dm.strength = 0.003
    em = bpy.data.objects.new('e', None)
    bpy.context.collection.objects.link(em)
    dm.texture_coords = 'OBJECT'
    dm.texture_coords_object = em
    for f in (1, 60):
        em.location = (0, 0, 0 if f == 1 else -1.5)
        em.keyframe_insert('location', frame=f)
    for fc in em.animation_data.action.fcurves:
        for k in fc.keyframe_points:
            k.interpolation = 'LINEAR'
    sheet = sphere(T(burn_at + V((0, 0, 0.003))), 0.035, water, scale=(1.4, 1.0, 0.1), name='film')
    drop = sphere((0, 0, -5), 0.0035, water, name='drop')
    host = sphere(T(burn_at + V((0, 0, 0.004))), 0.012, water, name='splash')
    host.hide_render = True
    psys = host.modifiers.new('ps', 'PARTICLE_SYSTEM').particle_system
    s = psys.settings
    s.count = 500
    s.frame_start, s.frame_end = -20, 60
    s.lifetime = 10
    s.normal_factor = 0.8
    s.factor_random = 0.6
    s.render_type = 'OBJECT'
    s.instance_object = drop
    s.particle_size = 0.9
    s.size_random = 0.6
    s.use_rotation_instance = True
    print('BURN', tuple(burn_at))
    cam(T(burn_at + V((0, 0, 0.1))), -25, 18, 0.62, lens=40, dof=4, clip=0.1)


def sc_ring():
    reset(frames=72)
    studio(key=(0.9, -1.4, 2.2), target=(0, 0, 0.8), power=450)
    box((0, 0.2, 0.39), (1.0, 0.8, 0.78), mat('table', '#3a3b40', rough=0.4), bevel=0.01)
    vic = victim()
    p = stand(-0.05, -0.45, face=(0, 1, 0), hz=1.0)
    p['armL'] = {'ik': (0.08, 0.0, 0.83), 'pole': (1, -0.5, -0.4)}
    p['handL'] = ((0.05, 1, -0.12), (0, 0, -1))
    p['curlL'] = 0.08
    vic.key(1, p)
    mask(vic, keep=('LeftArm', 'LeftForeArm', 'LeftHand'))
    r1, r2, r3 = vic.wpos(p, 'LeftHandRing1'), vic.wpos(p, 'LeftHandRing2'), vic.wpos(p, 'LeftHandRing3')
    ax = (r3 - r1).normalized()
    ring = torus(T(r1.lerp(r2, 0.5)), 0.0105, 0.0022, mat('gold', '#e0b34a', rough=0.18, metal=1.0), name='ring')
    orient(ring, z=ax, x=(1, 0, 0))
    res = rescuer()
    mask(res, keep=('RightForeArm', 'RightHand'))
    for f in list(range(1, 73, 3)) + [72]:
        t = smooth01((f - 12) / 40)
        pos = r1.lerp(r2, 0.5).lerp(r3 + ax * 0.06, t)
        ring.location = pos
        ring.keyframe_insert('location', frame=f)
        r = stand(0.1, 0.75, face=(-0.1, -1, 0), hz=1.0)
        r['chest'] = ((0, -0.35, 1), (0, -1, -0.4))
        r['armR'] = {'ik': T(pos + V((-0.05, 0.075, 0.035))), 'pole': (-1, 0.5, -0.5)}
        r['handR'] = ((0.5, -1, -0.5), (0, 0, -1))
        r['curlR'] = {'Index': 0.45, 'Middle': 0.8, 'Ring': 1.0, 'Pinky': 1.0, 'Thumb': 0.5}
        look(r, T(pos), (0.1, 0.7, 1.6))
        res.key(f, r)
    cam(T(r2 + V((0, 0.03, 0))), -60, 40, 0.45, lens=50, dof=3)


def sc_film():
    reset(frames=70)
    studio(key=(1.0, -1.6, 2.6), target=(0, 0, 0.8), power=500)
    tb = box((0, 0.2, 0.39), (1.0, 0.8, 0.78), mat('table', '#3a3b40', rough=0.4), bevel=0.01)
    vic = victim()
    p = stand(-0.05, -0.5, face=(0, 1, 0), hz=1.0)
    p['armL'] = {'ik': (-0.02, -0.02, 0.84), 'pole': (1, -0.5, -0.4)}
    p['handL'] = ((0.0, 1, -0.1), (0, 0, 1))
    vic.key(1, p)
    mask(vic, keep=('LeftArm', 'LeftForeArm', 'LeftHand'))
    fa, hd = vic.wpos(p, 'LeftForeArm'), vic.wpos(p, 'LeftHand')
    mid = fa.lerp(hd, 0.6)
    top, _ = surface(T(mid + V((0, 0, 0.5))))
    wound(T(top + V((0, 0, 0.001))), (0, 0, 1), r=0.03)
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.parent == vic.arm:
            o.modifiers.new('col', 'COLLISION')
    tb.modifiers.new('col', 'COLLISION')
    fm = mat('film', '#e6f4ff', rough=0.03, alpha=0.45, coat=1.0, emit='#dff1ff', emit_s=0.15)
    fp = plane(T(top + V((0, 0, 0.18))), 0.2, 0.22, fm, name='film', sub=24)
    cm = fp.modifiers.new('cloth', 'CLOTH')
    cm.settings.quality = 8
    cm.settings.mass = 0.04
    cm.settings.bending_stiffness = 0.01
    cm.settings.air_damping = 5
    cm.collision_settings.distance_min = 0.003
    cm.point_cache.frame_start, cm.point_cache.frame_end = 1, 70
    smooth(fp, sub=1)
    cam(T(top), -40, 40, 0.55, lens=45, dof=4, clip=0.1)


def sc_away():
    reset(frames=60)
    studio(key=(1.0, 1.8, 2.6), target=(0, 0.2, 0.95), power=450)
    counter()
    coil_m = mat('coil', '#ff3b1f', emit='#ff4a1c', emit_s=25)
    torus((0.12, 0.25, 0.915), 0.08, 0.008, coil_m, name='coil')
    torus((0.12, 0.25, 0.915), 0.045, 0.007, coil_m)
    lt = bpy.data.lights.new('glow', 'POINT')
    lt.energy = 25
    lt.color = (1, 0.35, 0.1)
    lo = bpy.data.objects.new('glow', lt)
    bpy.context.collection.objects.link(lo)
    lo.location = (0.12, 0.25, 0.97)
    vic, res = victim(), rescuer()
    mask(vic, keep=('RightArm', 'RightForeArm', 'RightHand'))
    mask(res, keep=('LeftForeArm', 'LeftHand'))
    for f in list(range(1, 61, 2)) + [60]:
        t = smooth01((f - 12) / 14)
        hand = V((0.1, 0.18, 0.99)).lerp(V((0.05, -0.25, 1.1)), t)
        p = stand(0.0, -0.45, face=(0, 1, 0), hz=1.0)
        p['armR'] = {'ik': T(hand), 'pole': (1, -0.3, -0.6)}
        p['handR'] = ((0, 1, -0.2), (0, 0, -1))
        p['chest'] = ((0, 0.1 - 0.15 * t, 1), (0, 1, -0.1))
        vic.key(f, p)
        r = stand(-0.45, -0.3, face=(1, 0.6, 0), hz=1.0)
        r['armL'] = {'ik': T(hand + V((0.02, -0.12, 0.02))), 'pole': (0, -1, -0.5)}
        r['handL'] = ((0.6, 0.6, 0), (0, 0, -1))
        r['curlL'] = 0.7 * smooth01((f - 6) / 6)
        look(r, T(hand), (-0.45, -0.3, 1.6))
        res.key(f, r)
    cam((0.08, 0.0, 1.02), -30, 25, 1.0, lens=40, dof=5)


def sc_noice():
    reset(frames=90)
    studio(key=(1.0, -2.0, 2.6), target=(0, 0, 0.05), power=450)
    ice = mat('ice', '#dff3ff', rough=0.06, trans=0.9, coat=0.6)
    for i, (dx, dy, rz) in enumerate(((-0.135, 0.0, 0.3), (-0.105, 0.035, 0.9), (-0.12, -0.02, 1.5))):
        box((dx, dy, 0.02 + (0.036 if i == 2 else 0)), (0.04, 0.04, 0.04), ice, bevel=0.007, rot=(0, 0, rz))
    ang = 0.35
    cyl((0.0, 0.0, 0.022), 0.02, 0.12, mat('tube', '#f5f5f7', rough=0.35), rot=(0, math.pi / 2, ang), bevel=0.008)
    cyl((0.07 * math.cos(ang), 0.07 * math.sin(ang), 0.022), 0.011, 0.024, mat('cap', '#0a84ff', rough=0.3), rot=(0, math.pi / 2, ang))
    sy = mat('steel', '#d8dade', rough=0.1, metal=1)
    cyl((0.13, 0.0, 0.006), 0.0015, 0.09, sy, rot=(0, math.pi / 2, -0.5))
    cyl((0.13 - 0.05 * math.cos(-0.5), -0.05 * math.sin(-0.5), 0.007), 0.007, 0.025, mat('hub', '#ffd60a', rough=0.3), rot=(0, math.pi / 2, -0.5))
    c = cam((0, 0, 0.02), -90, 24, 0.62, lens=70, dof=6)
    for f in (1, 90):
        a = math.radians(-90 + (-7 if f == 1 else 7))
        e = math.radians(24)
        c.location = V((math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e))) * 0.62 + V((0, 0, 0.02))
        c.rotation_euler = (V((0, 0, 0.02)) - c.location).to_track_quat('-Z', 'Y').to_euler()
        c.keyframe_insert('location', frame=f)
        c.keyframe_insert('rotation_euler', frame=f)


def _leg_scene(kind):
    reset(frames=90)
    studio(key=(1.4, -2.0, 3.0), target=(0.5, 0, 0.1), power=650)
    wall()
    vic, res = victim(), rescuer()
    p = sitfloor(-0.12, 0, face=(1, 0, 0), lean=0.3, knees=False)
    vic.key(1, p)
    kn, an = vic.wpos(p, 'RightLeg'), vic.wpos(p, 'RightFoot')
    ax = (an - kn).normalized()
    mid = kn.lerp(an, 0.5)
    top, _ = surface(T(mid + V((0, 0, 0.5))))
    rad = top.z - mid.z
    if kind == 'splint':
        wood = mat('board', '#b88a5a', rough=0.7)
        for sg in (1, -1):
            b = box(T(mid + V((0, (rad + 0.01) * sg, 0.0))), (0.5, 0.012, 0.07), wood, bevel=0.004)
            orient(b, x=ax, z=(0, 0, 1))
        for i, t in enumerate((0.15, 0.5, 0.85)):
            tie = torus(T(kn.lerp(an, t)), rad + 0.02, 0.009, M_gauze(), name='tie%d' % i)
            orient(tie, z=ax, x=(0, 0, 1))
            for f, s in ((1, 0.001), (15 + i * 20, 0.001), (25 + i * 20, 1.0)):
                tie.scale = (s, s, 2.2)
                tie.keyframe_insert('scale', frame=f)
        tgt = lambda f: kn.lerp(an, 0.15 + 0.35 * min(2, max(0, (f - 15) / 20))) + V((0, 0, rad + 0.03))
    else:
        atop, _ = surface(T(an + V((-0.03, 0, 0.5))))
        tw = box(T(atop + V((0, 0, 0.012))), (0.13, 0.13, 0.024), M_gauze(), bevel=0.01, name='towel')
        pack = box(T(atop + V((0, 0, 0.032))), (0.11, 0.1, 0.018), mat('gel', '#6ec6ff', rough=0.15, coat=1.0), bevel=0.008, name='pack')
        for o in (tw, pack):
            base = o.location.copy()
            for f, z in ((1, 0.25), (8, 0.25), (35, 0.0)):
                o.location = base + V((0, 0, z))
                o.keyframe_insert('location', frame=f)
        tgt = lambda f: atop + V((0, 0, 0.045 + 0.25 * (1 - smooth01((f - 8) / 27))))
    kx, ky = mid.x + 0.02, mid.y - 0.42
    _hands_only(res)
    for f in list(range(1, 91, 3)) + [90]:
        pt = tgt(f)
        r = kneel(kx, ky, 0.44, face=(0, 1, 0), lean=1.3)
        fdR, fdL = V((0.35, 1, -0.3)), V((-0.35, 1, -0.3))
        r['armR'] = {'ik': palm_on(pt + V((-0.035, 0, 0)), fdR, (0, 0, 1)), 'pole': (-1, -0.5, 0)}
        r['armL'] = {'ik': palm_on(pt + V((0.035, 0, 0)), fdL, (0, 0, 1)), 'pole': (1, -0.5, 0)}
        r['handR'] = (T(fdR), (0, 0, -1))
        r['handL'] = (T(fdL), (0, 0, -1))
        r['curlR'] = r['curlL'] = 0.25
        look(r, T(mid), (kx, ky + 0.2, 0.9))
        res.key(f, r)
    cam(T(mid + V((0.05, 0, 0.03))), 60, 58, 0.95, lens=40, dof=5)


def sc_splint(): _leg_scene('splint')
def sc_cold(): _leg_scene('cold')




def sc_victest():
    reset(frames=2)
    studio(key=(1.2, -2.0, 3.0), target=(0.3, 0, 0.1), power=650)
    vic = victim()
    vic.key(1, supine())
    camera((0.35, -1.9, 1.3), (0.35, 0, 0.1), lens=35)


def cam(target, az, el, dist, lens=40, dof=None, clip=0.05):
    """camera on a sphere around target: az from +X toward +Y (deg), el above horizon (deg)"""
    a, e = math.radians(az), math.radians(el)
    t = V(target)
    loc = t + V((math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e))) * dist
    c = camera(T(loc), T(t), lens=lens, dof=dof)
    c.data.clip_start = clip
    return c


def _airway_hands(vic, frame=1):
    """forehead / chin contact points in head-local space, measured at neutral pose"""
    p0 = _airway(vic, 0)
    vic.key(frame, p0)
    fh, _ = surface((-0.36, 0.0, 1), frame=frame)
    ch, _ = surface((-0.235, 0.0, 1), frame=frame)
    Hi = vic.wmat(p0, 'Head').inverted()
    return Hi @ fh, Hi @ ch


def _airway_rescuer(vic, p, fl, cl, kx=-0.2, ky=0.46, lean=1.15):
    Hm = vic.wmat(p, 'Head')
    fh, ch = Hm @ fl, Hm @ cl
    up = (Hm.to_3x3() @ V((0, 1, 0))).normalized()
    r = kneel(kx, ky, 0.45, face=(0, -1, 0), lean=lean)
    fd_f = V((0.1, -1, 0))
    r['armR'] = {'ik': palm_on(fh, fd_f, (0, 0, 1), back=0.045), 'pole': (-0.5, 1, 0.4)}
    r['handR'] = (T(fd_f - V((0, 0, 0.25))), (0, 0, -1))
    r['curlR'] = 0.1
    fd_c = V((-1, -0.35, -0.1))
    r['armL'] = {'ik': T(V(ch) - fd_c.normalized() * 0.1 + V((0, 0, 0.02))), 'pole': (0.8, 1, 0)}
    r['handL'] = (T(fd_c), (0, 0.2, -1))
    r['curlL'] = {'Index': 0.05, 'Middle': 0.05, 'Ring': 1.1, 'Pinky': 1.1, 'Thumb': 0.6}
    return r


def sc_ask():
    """rescuer kneeling in front of seated victim, talking (stroke checks)"""
    reset(frames=90)
    studio(key=(1.8, -2.4, 3.6), target=(0, -0.2, 1.0), power=800)
    box((0, 0, 0.23), (0.4, 0.4, 0.46), mat('stool', '#5b5f66', rough=0.7), bevel=0.02)
    vic, res = victim(), rescuer()
    for f in list(range(1, 91, 3)) + [90]:
        s = math.sin(f / 90 * 2 * math.pi)
        p = seated(0, 0, face=(0, -1, 0), hz=0.54)
        p['Head'] = ((0.05 * s, -0.1, 1), (0.1 * s, -1, -0.15))
        vic.key(f, p)
        r = kneel(0.2, -0.75, 0.45, face=(-0.3, 1, 0), lean=0.2)
        look(r, (0.0, -0.1, 1.02), (0.18, -0.7, 1.0))
        r['armR'] = {'ik': (0.12, -0.45, 0.95 + 0.02 * s), 'pole': (-0.3, -0.5, -1)}
        r['handR'] = ((-0.3, 0.8, 0.4), (-0.6, 0, 0.8))
        r['curlR'] = 0.2
        res.key(f, r)
    cam((0.05, -0.35, 0.85), -20, 12, 2.0, lens=42)


def _bleed_cam(mid):
    cam(T(mid + V((0, -0.04, 0.03))), -30, 40, 0.8, lens=42, dof=4)


def _hands_only(res):
    mask(res)


SCENES = {k[3:]: v for k, v in globals().items() if k.startswith('sc_')}
