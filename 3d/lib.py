"""Blender toolkit: studio scene, Xbot mannequins posed in world space (analytic IK), props, render."""
import bpy, math, os, subprocess
from mathutils import Vector as V, Matrix, Quaternion

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSET = os.path.join(ROOT, 'assets', 'Xbot.glb')
TEX = os.path.join(ROOT, 'tex')
os.makedirs(TEX, exist_ok=True)
MX = 'mixamorig:'


def srgb(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)


# ---------------------------------------------------------------- scene
def reset(frames=60, fps=30, res=(720, 900)):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 50 if os.environ.get('PREVIEW') else 84
    sc.render.fps = fps
    sc.frame_start, sc.frame_end = 1, frames
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast'
    e = sc.eevee
    e.taa_render_samples = 8 if os.environ.get('PREVIEW') else 32
    e.use_shadows = True
    try:
        e.use_raytracing = True
        e.ray_tracing_options.resolution_scale = '1'
        e.use_fast_gi = True
        e.fast_gi_distance = 1.5
    except Exception:
        pass
    w = bpy.data.worlds.new('W')
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    bg.inputs[0].default_value = srgb('#16171a')
    bg.inputs[1].default_value = 0.6
    return sc


def mat(name, hexc, rough=0.5, metal=0.0, emit=None, emit_s=0.0, alpha=1.0, trans=0.0, coat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = srgb(hexc)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    if coat:
        p.inputs['Coat Weight'].default_value = coat
    if emit:
        p.inputs['Emission Color'].default_value = srgb(emit)
        p.inputs['Emission Strength'].default_value = emit_s
    if trans:
        p.inputs['Transmission Weight'].default_value = trans
        p.inputs['IOR'].default_value = 1.33
    if alpha < 1:
        p.inputs['Alpha'].default_value = alpha
        m.surface_render_method = 'BLENDED' if hasattr(m, 'surface_render_method') else None
    return m


def img_mat(name, path, rough=0.35, emit_s=0.0, alpha=False):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image = bpy.data.images.load(path)
    nt.links.new(t.outputs['Color'], p.inputs['Base Color'])
    if emit_s:
        nt.links.new(t.outputs['Color'], p.inputs['Emission Color'])
        p.inputs['Emission Strength'].default_value = emit_s
    if alpha:
        nt.links.new(t.outputs['Alpha'], p.inputs['Alpha'])
    p.inputs['Roughness'].default_value = rough
    return m


def studio(key=(2.5, -2.5, 4.0), target=(0, 0, 0.3), power=900, floor='#26272b', fill=0.35, rim=True, size=4):
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
    fl = bpy.context.object
    fl.name = 'Floor'
    fl.data.materials.append(mat('floor', floor, rough=0.85))
    tgt = V(target)

    def area(name, loc, pw, sz, col='#ffffff'):
        d = bpy.data.lights.new(name, 'AREA')
        d.energy = pw
        d.size = sz
        d.color = srgb(col)[:3]
        o = bpy.data.objects.new(name, d)
        bpy.context.collection.objects.link(o)
        o.location = loc
        o.rotation_euler = (tgt - V(loc)).to_track_quat('-Z', 'Y').to_euler()
        return o
    area('Key', key, power, size, '#fff4e8')
    k = V(key)
    area('Fill', (-k.x * 1.1, k.y * 0.6, k.z * 0.7), power * fill, size * 1.5, '#e8f0ff')
    if rim:
        area('Rim', (-k.x * 0.4, -k.y * 1.3, k.z * 0.9), power * 0.8, 2, '#dfe8ff')
    return fl


def camera(loc, target, lens=50, dof=None):
    c = bpy.data.cameras.new('Cam')
    c.lens = lens
    o = bpy.data.objects.new('Cam', c)
    bpy.context.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (V(target) - V(loc)).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = o
    if dof:
        c.dof.use_dof = True
        c.dof.focus_distance = (V(target) - V(loc)).length
        c.dof.aperture_fstop = dof
    return o


# ---------------------------------------------------------------- props
def smooth(o, bevel=0.0, seg=4, sub=0):
    if bevel:
        m = o.modifiers.new('bev', 'BEVEL')
        m.width = bevel
        m.segments = seg
        m.limit_method = 'NONE'
    if sub:
        s = o.modifiers.new('sub', 'SUBSURF')
        s.levels = s.render_levels = sub
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def box(loc, size, m, bevel=0.01, rot=(0, 0, 0), name='box'):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    smooth(o, bevel)
    o.data.materials.append(m)
    return o


def cyl(loc, r, depth, m, rot=(0, 0, 0), bevel=0.0, verts=48, name='cyl'):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    smooth(o, bevel)
    o.data.materials.append(m)
    return o


def sphere(loc, r, m, scale=(1, 1, 1), name='sph'):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=48, ring_count=24)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    for p in o.data.polygons:
        p.use_smooth = True
    o.data.materials.append(m)
    return o


def torus(loc, R, r, m, rot=(0, 0, 0), name='tor'):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=loc, rotation=rot, major_segments=64, minor_segments=24)
    o = bpy.context.object
    o.name = name
    for p in o.data.polygons:
        p.use_smooth = True
    o.data.materials.append(m)
    return o


def key(o, frame, **kw):
    for k, v in kw.items():
        setattr(o, k, v)
        o.keyframe_insert(k, frame=frame)


def ease_all(kind='BEZIER'):
    for a in bpy.data.actions:
        fcs = a.fcurves if hasattr(a, 'fcurves') else []
        for fc in fcs:
            for kp in fc.keyframe_points:
                kp.interpolation = kind


def magick(name, args):
    p = os.path.join(TEX, name)
    subprocess.run(['magick'] + args + [p], check=True)
    return p


# ---------------------------------------------------------------- mannequin
LIMB = {'L': 'Left', 'R': 'Right'}


class Char:
    def __init__(self, name, body='#d9dde3', joints='#6b7280', scale=1.0, rough=0.42):
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=ASSET)
        new = [o for o in bpy.data.objects if o not in before]
        ico = [o for o in new if o.type == 'MESH' and o.name.startswith('Icosphere')]
        new = [o for o in new if o not in ico]
        for o in ico:
            bpy.data.objects.remove(o)
        self.arm = [o for o in new if o.type == 'ARMATURE'][0]
        self.arm.name = name
        self.arm.animation_data_clear()
        self.arm.scale = (0.01 * scale,) * 3
        mb = mat(name + '_body', body, rough=rough, coat=0.25)
        mj = mat(name + '_joint', joints, rough=0.5)
        for o in new:
            if o.type == 'MESH':
                o.data.materials.clear()
                o.data.materials.append(mj if 'Joint' in o.name else mb)
                for p in o.data.polygons:
                    p.use_smooth = True
        bpy.context.view_layer.update()
        self.W = self.arm.matrix_world.copy()
        self.Wi = self.W.inverted()
        self.pb = self.arm.pose.bones
        for p in self.pb:
            p.rotation_mode = 'QUATERNION'
            p.location = (0, 0, 0)
            p.rotation_quaternion = (1, 0, 0, 0)
            p.scale = (1, 1, 1)
        self.bones = self.arm.data.bones
        self.prevq = {}
        # rest-based lengths (armature units)
        h = lambda n: self.bones[MX + n].head_local
        self.L = {}
        for s in 'LR':
            S = LIMB[s]
            self.L['arm' + s] = ((h(S + 'ForeArm') - h(S + 'Arm')).length, (h(S + 'Hand') - h(S + 'ForeArm')).length)
            self.L['leg' + s] = ((h(S + 'Leg') - h(S + 'UpLeg')).length, (h(S + 'Foot') - h(S + 'Leg')).length)

    # --- rest frame helpers
    def child_of(self, n):
        return {'Hips': 'Spine', 'Spine': 'Spine1', 'Spine1': 'Spine2', 'Spine2': 'Neck', 'Neck': 'Head', 'Head': 'HeadTop_End',
                'LeftArm': 'LeftForeArm', 'LeftForeArm': 'LeftHand', 'LeftHand': 'LeftHandMiddle1',
                'RightArm': 'RightForeArm', 'RightForeArm': 'RightHand', 'RightHand': 'RightHandMiddle1',
                'LeftUpLeg': 'LeftLeg', 'LeftLeg': 'LeftFoot', 'LeftFoot': 'LeftToeBase',
                'RightUpLeg': 'RightLeg', 'RightLeg': 'RightFoot', 'RightFoot': 'RightToeBase'}.get(n)

    def rest_axes(self, n):
        b = self.bones[MX + n]
        c = self.child_of(n)
        a = (self.bones[MX + c].head_local - b.head_local).normalized() if c else b.matrix_local.to_3x3().col[1].normalized()
        if 'Hand' in n and 'Hand' == n[-4:]:
            s = V((0, 0, -1))          # palm normal (T-pose palms down)
        elif 'Foot' in n:
            s = V((0, 0, 1))           # top of foot
        elif 'UpLeg' in n:
            s = V((0, 1, 0))           # shin bends backwards
        else:
            s = V((0, -1, 0))          # character forward
        return a, s

    @staticmethod
    def basis(a, s):
        a = a.normalized()
        s = (s - a * s.dot(a))
        if s.length < 1e-6:
            s = a.orthogonal()
        s.normalize()
        return Matrix((a, s, a.cross(s))).transposed()

    # --- world <-> armature
    def to_arm_p(self, p):
        return self.Wi @ V(p)

    def to_arm_d(self, d):
        return (self.Wi.to_3x3() @ V(d)).normalized()

    # --- solve & key a pose
    def solve(self, pose):
        """pose keys: hips{pos,up,fwd}, Spine/Spine1/Spine2/Neck/Head: (dir[,fwd]) world,
        chest (dir,fwd) spreads over spine, armL/armR: {'ik':pos,'pole':dir} or {'dirs':(upper,fore)},
        handL/handR: (dir,palm), legL/legR same as arms, footL/footR: (dir,top), curlL/curlR: 0..1, headscale"""
        posed = {}
        order = [b for b in self.bones]  # bones are in hierarchy order
        rest = {b.name: b.matrix_local.copy() for b in order}
        spec = {}
        hp = pose.get('hips', {})
        if 'chest' in pose:
            d, f = pose['chest']
            for n in ('Spine', 'Spine1', 'Spine2'):
                spec.setdefault(n, (d, f))
        for n in ('Spine', 'Spine1', 'Spine2', 'Neck', 'Head'):
            if n in pose:
                spec[n] = pose[n]
        # arms/legs: resolve IK later when parent posed
        basisq = {}
        for b in order:
            n = b.name[len(MX):]
            par = b.parent
            if par is None:
                R = self._rot_for(n, (hp.get('up', (0, 0, 1)), hp.get('fwd', (0, -1, 0))), None)
                head = self.to_arm_p(hp['pos']) if 'pos' in hp else b.head_local.copy()
                M = Matrix.Translation(head) @ (R @ rest[b.name].to_3x3()).to_4x4()
                posed[b.name] = M
                continue
            relrest = rest[par.name].inverted() @ rest[b.name]
            inh = posed[par.name] @ relrest
            Rinh = inh.to_3x3().normalized() @ rest[b.name].to_3x3().inverted()
            headp = inh.to_translation()
            R = None
            if n in spec:
                R = self._rot_for(n, spec[n], Rinh)
            # limbs
            for s in 'LR':
                S = LIMB[s]
                for kind, up, lo, end in (('arm', S + 'Arm', S + 'ForeArm', 'hand'), ('leg', S + 'UpLeg', S + 'Leg', 'foot')):
                    k = kind + s
                    if k not in pose:
                        continue
                    if n == up:
                        dirs = self._limb_dirs(k, headp, pose[k])
                        pose.setdefault('_dirs', {})[k] = dirs
                        u, f, _ = dirs
                        R = self._rot_for(n, (u, f) if f is not None else (u,), Rinh, arm_space=True)
                    elif n == lo:
                        R = self._rot_for(n, (pose['_dirs'][k][2],), Rinh, arm_space=True)
                ek = ('hand' if 'Hand' == n[-4:] and n in ('LeftHand', 'RightHand') else 'foot' if n in ('LeftFoot', 'RightFoot') else None)
                if ek and n.startswith(S) and (ek + s) in pose:
                    R = self._rot_for(n, pose[ek + s], Rinh)
            if R is None:
                R = Rinh
            M = Matrix.Translation(headp) @ (R @ rest[b.name].to_3x3()).to_4x4()
            # finger curl (local X rotation)
            for s in 'LR':
                S = LIMB[s]
                c = pose.get('curl' + s)
                if c and n.startswith(S + 'Hand') and n != S + 'Hand' and n[-1] in '123':
                    thumb = 'Thumb' in n
                    fname = n[len(S) + 4:-1]
                    cv = c.get(fname, c.get('all', 0)) if isinstance(c, dict) else c
                    ang = cv * (0.6 if thumb else (1.25 if n[-1] != '1' else 1.05))
                    loc = Matrix.Rotation(ang, 4, 'X' if not thumb else 'Z')
                    M = M @ loc
            if n == 'Head' and pose.get('headscale'):
                M = M @ Matrix.Scale(pose['headscale'], 4)
            posed[b.name] = M
        self._posed = posed
        # to basis
        for b in order:
            if b.parent is None:
                basis = rest[b.name].inverted() @ posed[b.name]
            else:
                relrest = rest[b.parent.name].inverted() @ rest[b.name]
                basis = relrest.inverted() @ posed[b.parent.name].inverted() @ posed[b.name]
            basisq[b.name] = basis
        return basisq

    def _rot_for(self, n, spec, Rinh, arm_space=False):
        a, s = self.rest_axes(n)
        conv = (lambda d: V(d).normalized()) if arm_space else self.to_arm_d
        d = conv(spec[0])
        if len(spec) > 1 and spec[1] is not None:
            g = conv(spec[1])
            return self.basis(d, g) @ self.basis(a, s).transposed()
        a2 = Rinh @ a
        return a2.rotation_difference(d).to_matrix() @ Rinh

    def _limb_dirs(self, k, S, spec):
        if 'dirs' in spec:
            u, f = (self.to_arm_d(x) for x in spec['dirs'])
            dev = f - u * f.dot(u)
            return u, (dev.normalized() if dev.length > 0.2 else None), f
        L1, L2 = self.L[k]
        T = self.to_arm_p(spec['ik'])
        P = self.to_arm_d(spec.get('pole', (0, -1, 0)))
        dv = T - S
        if dv.length > (L1 + L2) * 1.03:
            self.last_warn = (k, round((dv.length - L1 - L2) * self.W.to_scale().x, 3))
        dist = max(1e-3, min(dv.length, (L1 + L2) * 0.9995))
        u = dv.normalized()
        a = (L1 * L1 - L2 * L2 + dist * dist) / (2 * dist)
        h = math.sqrt(max(0.0, L1 * L1 - a * a))
        p = P - u * P.dot(u)
        p = p.normalized() if p.length > 1e-6 else u.orthogonal().normalized()
        E = S + u * a + p * h
        up = (E - S).normalized()
        lo = (T - E).normalized() if (T - E).length > 1e-6 else up
        # bend plane secondary: arms -> forearm deviates toward rest 'forward' axis; legs -> backward
        dev = lo - up * lo.dot(up)
        if dev.length < 0.2:
            return up, None, lo
        return up, dev.normalized(), lo

    def key(self, frame, pose, fit=True):
        pose = dict(pose)
        if fit and self.arm.name.startswith('Res') and 'hips' in pose:
            fit_reach(self, pose)
        self.last_warn = None
        B = self.solve(pose)
        for name, M in B.items():
            pb = self.pb[name]
            q = M.to_quaternion()
            pq = self.prevq.get(name)
            if pq is not None and pq.dot(q) < 0:
                q.negate()
            self.prevq[name] = q.copy()
            pb.rotation_quaternion = q
            pb.keyframe_insert('rotation_quaternion', frame=frame)
            sc = M.to_scale()
            if abs(sc.x - 1) > 1e-3:
                pb.scale = sc
                pb.keyframe_insert('scale', frame=frame)
            if pb.parent is None:
                pb.location = M.to_translation()
                pb.keyframe_insert('location', frame=frame)
        if self.last_warn:
            print('WARN reach', self.arm.name, frame, *self.last_warn)

    def wpos(self, pose, n):
        self.solve(dict(pose))
        return self.W @ self._posed[MX + n].to_translation()

    def wmat(self, pose, n):
        self.solve(dict(pose))
        return self.W @ self._posed[MX + n]

    def attach(self, obj, n, frame=1):
        sc = bpy.context.scene
        sc.frame_set(frame)
        bpy.context.view_layer.update()
        mw = obj.matrix_world.copy()
        obj.parent = self.arm
        obj.parent_type = 'BONE'
        obj.parent_bone = MX + n
        bpy.context.view_layer.update()
        obj.matrix_world = mw

    def world_bone(self, n):
        bpy.context.view_layer.update()
        return self.W @ self.pb[MX + n].head


def lerp(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def blend(p0, p1, t):
    """blend two pose dicts (numbers/tuples) for in-betweens"""
    out = {}
    for k in p0:
        a, b = p0[k], p1.get(k, p0[k])
        if isinstance(a, dict):
            out[k] = blend(a, b, t)
        elif isinstance(a, (int, float)):
            out[k] = a + (b - a) * t
        elif isinstance(a, tuple) and a and isinstance(a[0], (tuple, list)):
            out[k] = tuple(lerp(x, y, t) if x is not None else None for x, y in zip(a, b))
        elif isinstance(a, tuple):
            out[k] = lerp(a, b, t)
        else:
            out[k] = a
    return out


# ---------------------------------------------------------------- render
def render(out, still=None):
    sc = bpy.context.scene
    ease_all()
    if still is not None:
        if any(m.type in ('CLOTH', 'PARTICLE_SYSTEM') for o in bpy.data.objects for m in getattr(o, 'modifiers', [])):
            for f in range(1, still + 1):
                sc.frame_set(f)
        sc.frame_set(still)
        sc.render.image_settings.file_format = 'PNG'
        sc.render.filepath = out
        bpy.ops.render.render(write_still=True)
        return
    sc.render.image_settings.file_format = 'FFMPEG'
    f = sc.render.ffmpeg
    f.format = 'MPEG4'
    f.codec = 'H264'
    f.constant_rate_factor = 'HIGH'
    f.ffmpeg_preset = 'GOOD'
    f.gopsize = 12
    f.audio_codec = 'NONE'
    sc.render.filepath = out
    bpy.ops.render.render(animation=True)


def surface(origin, direction=(0, 0, -1), frame=1):
    """first hit on evaluated (deformed) geometry"""
    sc = bpy.context.scene
    sc.frame_set(frame)
    dg = bpy.context.evaluated_depsgraph_get()
    hit, loc, nrm, idx, obj, mw = sc.ray_cast(dg, V(origin), V(direction).normalized())
    return (loc, nrm) if hit else (None, None)


def palm_on(contact, fingers, normal_out, back=0.05, lift=0.022):
    """wrist position so that the palm centre rests on 'contact'; normal_out = surface normal"""
    fd = V(fingers).normalized()
    n = V(normal_out).normalized()
    fd = (fd - n * fd.dot(n)).normalized()
    return tuple(V(contact) - fd * back + n * lift)


def fit_reach(ch, pose, margin=0.985, iters=14, vertical=False):
    """shift hips so every IK arm target is reachable (in place). returns pose"""
    s = ch.W.to_scale().x
    z0 = pose['hips']['pos'][2]
    for it in range(iters):
        vertical = it >= 5
        worst, push = 0.0, V((0, 0, 0))
        for side in 'LR':
            k = 'arm' + side
            if k not in pose or 'ik' not in pose[k]:
                continue
            sh = ch.wpos(pose, LIMB[side] + 'Arm')
            tg = V(pose[k]['ik'])
            L = sum(ch.L[k]) * s * margin
            ex = (tg - sh).length - L
            if ex > 0:
                d = (tg - sh)
                if not vertical:
                    d.z = 0
                if d.length > 1e-6:
                    push += d.normalized() * ex
                worst = max(worst, ex)
        if worst < 0.002:
            break
        hp = V(pose['hips']['pos']) + push * 0.9
        hp.z = max(hp.z, z0 - 0.16)
        pose['hips'] = dict(pose['hips'], pos=tuple(hp))
        if vertical and 'chest' in pose:
            d, f = pose['chest']
            d = (V(d) + push.normalized() * 0.25).normalized()
            pose['chest'] = (tuple(d), f)
    return pose


def mask(ch, keep=('LeftForeArm', 'LeftHand', 'RightForeArm', 'RightHand'), thr=0.35):
    """show only vertices mostly weighted to the given bones (substring match)"""
    for o in bpy.data.objects:
        if o.type != 'MESH' or o.parent != ch.arm:
            continue
        idx = [g.index for g in o.vertex_groups if any(k in g.name for k in keep)]
        vg = o.vertex_groups.new(name='keep')
        for v in o.data.vertices:
            w = sum(g.weight for g in v.groups if g.group in idx)
            if w > thr:
                vg.add([v.index], 1.0, 'REPLACE')
        m = o.modifiers.new('mask', 'MASK')
        m.vertex_group = 'keep'
        # mask must come after armature
        while o.modifiers.find('mask') > 0 and o.modifiers[0].name == 'mask':
            break
