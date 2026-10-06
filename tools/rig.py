# -*- coding: utf-8 -*-
"""三虎 Sanhuu 像素骨架(rig)。

美术素材版权 © 三虎 Sanhuu,保留所有权利。未经许可,禁止商用、二次修改、转载传播。

本文件把角色拆成可摆姿势的部件,每一帧都按姿势参数重新逐像素绘制
(不是对同一张图做平移/旋转),因此得到的是真正的逐帧动画。
画布 96x96,脚底基线 y=G,角色水平中心 x=CX。
"""
import math
import numpy as np
from PIL import Image, ImageDraw

S = 96
G = 86
CX = 48
YY, XX = np.mgrid[0:S, 0:S].astype(np.float32)

C = dict(
    line=(43, 45, 54), fur=(248, 249, 251), shade=(212, 216, 226), shade2=(184, 189, 201),
    inner=(134, 138, 150), stripe=(59, 62, 72), ear_in=(188, 191, 202),
    eye_r=(176, 42, 18), eye_o=(234, 92, 30), eye_y=(248, 198, 50), pupil=(42, 20, 16),
    eye_w=(255, 255, 255), nose=(36, 36, 42), pad=(242, 167, 160), choker=(30, 30, 36),
    bell=(242, 194, 48), watch=(47, 69, 88), watch_f=(232, 120, 42), mouth=(92, 95, 106),
    mouth_in=(122, 40, 46), tongue=(240, 130, 130), clip=(150, 156, 172),
    um_a=(240, 132, 52), um_b=(248, 198, 50), um_pole=(96, 100, 112),
    scarf=(234, 92, 30), scarf_d=(190, 66, 20),
    rain=(104, 168, 236), rain_l=(170, 210, 246), pink=(245, 110, 130),
    spark=(250, 206, 60), zz=(110, 140, 204), bang=(232, 70, 40),
    leaf=(112, 172, 84), leaf2=(222, 142, 52), flake=(150, 196, 242),
    cloud=(244, 246, 250), cloud_l=(160, 168, 186), cloud_d=(122, 128, 144), cloud_dl=(70, 74, 88),
    sun=(255, 208, 66), sun_l=(232, 140, 30), bolt=(255, 226, 80), glass=(30, 30, 36),
    glass_h=(120, 132, 156), wind=(170, 186, 208), snow=(236, 244, 255), snow_l=(143, 180, 217),
    paper=(252, 252, 255), paper_l=(120, 150, 210),
)


# ---------- 基础图元 ----------
def ell(cx, cy, rx, ry):
    return ((XX - cx) / rx) ** 2 + ((YY - cy) / ry) ** 2 <= 1.0


def circ(cx, cy, r):
    return ell(cx, cy, r, r)


def poly(pts):
    im = Image.new('1', (S, S), 0)
    ImageDraw.Draw(im).polygon([(float(x), float(y)) for x, y in pts], fill=1, outline=1)
    return np.array(im, dtype=bool)


def cap(x0, y0, x1, y1, r):
    dx, dy = x1 - x0, y1 - y0
    L = dx * dx + dy * dy
    if L < 1e-6:
        return circ(x0, y0, r)
    t = np.clip(((XX - x0) * dx + (YY - y0) * dy) / L, 0, 1)
    return (XX - (x0 + t * dx)) ** 2 + (YY - (y0 + t * dy)) ** 2 <= r * r


def bez(p0, p1, p2, p3, n=30):
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
                    a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def mir(pts, ax):
    return [(2 * ax - x, y) for x, y in pts]


def shift(m, dx, dy):
    out = np.zeros_like(m)
    h, w = m.shape
    ys, yd = (slice(0, h - dy), slice(dy, h)) if dy >= 0 else (slice(-dy, h), slice(0, h + dy))
    xs, xd = (slice(0, w - dx), slice(dx, w)) if dx >= 0 else (slice(-dx, w), slice(0, w + dx))
    out[yd, xd] = m[ys, xs]
    return out


def dil(m):
    return m | shift(m, 1, 0) | shift(m, -1, 0) | shift(m, 0, 1) | shift(m, 0, -1)


class Layer:
    def __init__(self):
        self.a = np.zeros((S, S, 4), np.uint8)

    def fill(self, m, c):
        self.a[m] = (c[0], c[1], c[2], 255)

    @property
    def m(self):
        return self.a[..., 3] > 0

    def rim(self, m, c=None):
        r = m & ~(shift(m, -1, 0) & shift(m, 0, -1))
        self.fill(r, c or C['shade'])


def put(cv, x, y, c):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < S and 0 <= y < S:
        cv[y, x] = (c[0], c[1], c[2], 255)


def comp(cv, L, line=C['line'], inner=C['inner']):
    """把图层合成到画布:外轮廓用深色描边,压在已有色块上的内轮廓用柔和灰。"""
    m = L.m
    if line is not None:
        e = dil(m) & ~m
        occ = cv[..., 3] == 255
        isline = occ & (cv[..., 0] == C['line'][0]) & (cv[..., 1] == C['line'][1]) & (cv[..., 2] == C['line'][2])
        cv[e & (~occ | isline)] = (*line, 255)
        if inner is not None:
            cv[e & occ & ~isline] = (*inner, 255)
    cv[m] = L.a[m]


def stamp(cv, x, y, rows, cmap, flip=False):
    for j, row in enumerate(rows):
        r = row[::-1] if flip else row
        for i, ch in enumerate(r):
            if ch in cmap:
                put(cv, x + i, y + j, cmap[ch])


# ---------- 眼睛模板(左眼,右眼镜像) ----------
EYEMAP = {'K': C['line'], 'R': C['eye_r'], 'O': C['eye_o'], 'Y': C['eye_y'], 'W': C['eye_w'], 'P': C['pupil']}
EYES = {
    'half': (-2, ["KKKKKKK", "KRRRRRW", "WOOOOOW", ".YYYYY."]),
    'wide': (-3, ["KKKKKKK", "WRRRRRW", "WOOOOOW", "WOOOOOW", "WYYYYYW", ".KKKKK."]),
    'closed': (0, ["KKKKKKK"]),
    'sleep': (0, ["K.....K", ".KKKKK."]),
    'happy': (-1, ["..KKK..", ".K...K.", "K.....K"]),
    'squeeze': (-2, ["KK.....", "..KK...", "....KK.", "..KK...", "KK....."]),
}


def draw_eye(cv, ex, ey, kind, gx, right):
    y0, rows = EYES[kind]
    stamp(cv, ex - 3, ey + y0, rows, EYEMAP, flip=right)
    if kind == 'half':
        for dy in (-1, 0, 1):
            put(cv, ex + gx, ey + dy, C['pupil'])
    elif kind == 'wide':
        for dy in (-1, 0):
            put(cv, ex + gx, ey + dy, C['pupil'])


def draw_mouth(cv, fx, fy, kind):
    pts = {
        'w': [(-2, 8), (-1, 9), (0, 8), (1, 9), (2, 8)],
        'smile': [(-3, 8), (-2, 9), (-1, 9), (0, 8), (1, 9), (2, 9), (3, 8)],
        'frown': [(-2, 9), (-1, 8), (0, 8), (1, 8), (2, 9)],
        'flat': [(-1, 9), (0, 9), (1, 9)],
    }
    if kind in pts:
        for dx, dy in pts[kind]:
            put(cv, fx + dx, fy + dy, C['mouth'])
    elif kind == 'open':
        for dx in (-2, -1, 0, 1, 2):
            put(cv, fx + dx, fy + 8, C['mouth_in'])
            put(cv, fx + dx, fy + 9, C['mouth_in'])
        for dx in (-1, 0, 1):
            put(cv, fx + dx, fy + 10, C['tongue'])
        put(cv, fx, fy + 9, C['tongue'])
    elif kind == 'o':
        for dx in (-1, 0, 1):
            put(cv, fx + dx, fy + 8, C['mouth_in'])
            put(cv, fx + dx, fy + 9, C['mouth_in'])
    elif kind == 'yawn':
        for dy in (8, 9, 10, 11):
            for dx in (-2, -1, 0, 1, 2):
                put(cv, fx + dx, fy + dy, C['mouth_in'])
        for dx in (-1, 0, 1):
            put(cv, fx + dx, fy + 11, C['tongue'])
        put(cv, fx - 2, fy + 8, C['eye_w'])
        put(cv, fx + 2, fy + 8, C['eye_w'])


def default_pose():
    return dict(ox=0, oy=0, bob=0, drop=0, tuck=0, head_dx=0, head_dy=0, gx=0, gy=0,
                eyes='half', eyeL=None, eyeR=None, mouth='w', ears='up', earL=0, earR=0,
                armL=(-11, -8), armR=(11, -8), arms_front=False, legs='stand', swing=0.0,
                tail=0.0, tail_mode='up', blush=False, glasses=False, scarf=None,
                umbrella=None, snowcap=0, leaf_face=False, doc=None, fur_spike=False)


def tail_layer(cx, by, s, mode, side=False):
    L = Layer()
    if side:
        pts = bez((cx + 6, by - 8), (cx + 16, by - 3), (cx + 23, by - 10 + s), (cx + 19 + 3 * s, by - 23))
    elif mode == 'down':
        pts = bez((cx + 6, by - 7), (cx + 17, by - 8), (cx + 19 + 3 * s, by), (cx + 15 + 6 * s, by + 8))
    elif mode == 'blown':
        pts = bez((cx + 6, by - 6), (cx + 14, by - 9), (cx + 4, by - 18 + s), (cx - 10, by - 20 + 2 * s))
    else:
        pts = bez((cx + 6, by - 6), (cx + 18, by - 3), (cx + 22 + 4 * s, by - 13), (cx + 17 + 7 * s, by - 23))
    n = len(pts)
    for i, (x, y) in enumerate(pts):
        L.fill(circ(x, y, 2.0), C['fur'])
    for i, (x, y) in enumerate(pts):
        if i >= n - 4 or (i % 8 == 5 and i < n - 7):
            L.fill(circ(x, y, 2.0), C['stripe'])
    return L


def draw_front(P):
    """正面姿势绘制。返回 RGBA 数组。"""
    cv = np.zeros((S, S, 4), np.uint8)
    cx = CX + P['ox']
    gy0 = G + P['oy']
    by = gy0 + P['bob'] + P['drop']
    hx = cx + P['head_dx']
    hy = by - 32 + P['head_dy']
    legs = P['legs']

    # 地面阴影(离地越高越小)
    lift = max(0, -P['oy'])
    srx = max(5, 15 - lift * 0.45)
    sh = ell(CX + P['ox'], G + 1, srx, 2.4)
    cv[sh] = (20, 22, 30, 70)

    # 尾巴
    comp(cv, tail_layer(cx, by, P['tail'], P['tail_mode']))

    # 腿(站立/收腿/悬空)
    def leg_layer():
        L = Layer()
        if legs == 'dangle':
            sw = P['swing']
            for sgn in (-1, 1):
                tx = cx + sgn * 5 + sw * 0.6
                t = ell(tx, by - 5, 4.2, 6.0)
                L.fill(t, C['fur'])
                L.rim(t)
                L.fill(poly([(tx + sgn * 5, by - 7), (tx + sgn * 1, by - 5), (tx + sgn * 5, by - 4)]) & t, C['stripe'])
            return L, None
        if legs == 'sit':
            return None, None
        tk = P['tuck']
        dr = P['drop']
        for sgn in (-1, 1):
            tx = cx + sgn * (6 + dr * 0.35)
            ty = gy0 - 7 - tk * 0.5 + dr * 0.45
            t = ell(tx, ty, 5.5, max(3.5, 6 - dr * 0.3 - tk * 0.3))
            L.fill(t, C['fur'])
            L.rim(t)
            L.fill(poly([(tx + sgn * 7, ty - 4), (tx + sgn * 1, ty - 2), (tx + sgn * 7, ty - 1)]) & t, C['stripe'])
            L.fill(poly([(tx + sgn * 7, ty + 1), (tx + sgn * 2, ty + 2), (tx + sgn * 7, ty + 3)]) & t, C['stripe'])
        F = Layer()
        for sgn in (-1, 1):
            fx = cx + sgn * (7 + dr * 0.35)
            f = ell(fx, gy0 - 2 - tk, 5.5, 2.6)
            F.fill(f, C['fur'])
            F.rim(f)
            F.a[int(gy0 - 1 - tk), int(fx - 2)] = (*C['shade2'], 255)
            F.a[int(gy0 - 1 - tk), int(fx + 2)] = (*C['shade2'], 255)
        return L, F

    L, F = leg_layer()
    if L is not None:
        comp(cv, L)

    # 伞(在头后面)
    um = P['umbrella']
    if um is not None and um > 0:
        U = Layer()
        ucx, ucy = hx + 2, hy - 19
        handx, handy = cx + P['armR'][0], by + P['armR'][1]
        U.fill(cap(handx, handy + 1, ucx, ucy - 2, 0.6), C['um_pole'])
        rx, ry = 6 + 15 * um, 5 + 6 * um
        dome = ell(ucx, ucy, rx, ry) & (YY <= ucy)
        if um > 0.6:
            for k in range(-3, 4):
                dome &= ~circ(ucx + k * 7 + 3.5, ucy + 1.2, 2.7)
        band = np.floor((XX - (ucx - rx)) / max(3.0, (2 * rx) / 5)).astype(int)
        U.fill(dome & (band % 2 == 0), C['um_a'])
        U.fill(dome & (band % 2 == 1), C['um_b'])
        U.fill(cap(ucx, ucy - ry - 2, ucx, ucy - ry, 0.5), C['um_pole'])
        comp(cv, U, inner=C['line'])

    # 身体
    B = Layer()
    chest = ell(cx, by - 15, 6.5, 5.5)
    hips = ell(cx, by - 10, 9.5, 6.5)
    body = chest | hips
    B.fill(body, C['fur'])
    B.rim(body)
    for sgn in (-1, 1):
        B.fill(poly([(cx + sgn * 10, by - 14), (cx + sgn * 5, by - 12), (cx + sgn * 10, by - 11)]) & body, C['stripe'])
    comp(cv, B, inner=C['shade2'])
    if F is not None:
        comp(cv, F)

    # 项圈 + 铃铛 / 围巾
    if P['scarf'] is None:
        for x in range(int(cx - 5), int(cx + 6)):
            if cv[int(by - 19), x, 3] == 255:
                put(cv, x, by - 19, C['choker'])
        put(cv, cx, by - 18, C['bell'])
    else:
        Sc = Layer()
        Sc.fill((abs(XX - cx) <= 7) & (YY >= by - 20) & (YY <= by - 18), C['scarf'])
        fl = P['scarf']
        Sc.fill(cap(cx + 5, by - 18, cx + 6 + fl, by - 12, 1.3), C['scarf'])
        Sc.fill((abs(XX - cx) <= 7) & (YY == by - 18), C['scarf_d'])
        comp(cv, Sc, inner=C['line'])

    # 坐姿的膝盖与脚
    if legs == 'sit':
        K = Layer()
        for sgn in (-1, 1):
            kx = cx + sgn * 5.5
            k = ell(kx, gy0 - 7, 4.6, 6.2)
            K.fill(k, C['fur'])
            K.rim(k)
            K.fill(poly([(kx + sgn * 6, gy0 - 10), (kx + sgn * 1, gy0 - 8), (kx + sgn * 6, gy0 - 7)]) & k, C['stripe'])
        comp(cv, K)
        K2 = Layer()
        for sgn in (-1, 1):
            f = ell(cx + sgn * 6.5, gy0 - 1.5, 5.2, 2.5)
            K2.fill(f, C['fur'])
            K2.rim(f)
        comp(cv, K2)

    # 手臂
    def arms():
        for side, key in ((-1, 'armL'), (1, 'armR')):
            A = Layer()
            sx, sy = cx + side * 6, by - 16
            hxp, hyp = cx + P[key][0], by + P[key][1]
            arm = cap(sx, sy, hxp, hyp, 1.8) | circ(hxp, hyp, 2.4)
            A.fill(arm, C['fur'])
            mx, my = sx + (hxp - sx) * 0.45, sy + (hyp - sy) * 0.45
            A.fill(arm & circ(mx, my, 1.3), C['stripe'])
            if side == 1:
                wx, wy = sx + (hxp - sx) * 0.72, sy + (hyp - sy) * 0.72
                A.fill(arm & circ(wx, wy, 1.7), C['watch_f'])
                A.fill(arm & circ(wx, wy, 0.8), C['watch'])
            comp(cv, A)

    if not P['arms_front']:
        arms()

    # 耳朵
    for sgn, extra in ((-1, P['earL']), (1, P['earR'])):
        E = Layer()
        if P['ears'] == 'down':
            o = [(hx - 14, hy - 4), (hx - 20, hy - 10), (hx - 6, hy - 10)]
            i = [(hx - 13, hy - 6), (hx - 17, hy - 9), (hx - 9, hy - 9)]
        else:
            o = [(hx - 15, hy - 4), (hx - 13, hy - 19 + extra), (hx - 4, hy - 10)]
            i = [(hx - 12, hy - 7), (hx - 12, hy - 15 + extra), (hx - 7, hy - 10)]
        if sgn == 1:
            o, i = mir(o, hx), mir(i, hx)
        E.fill(poly(o), C['stripe'])
        E.fill(poly(i), C['ear_in'])
        comp(cv, E)

    # 头
    Hd = Layer()
    head = ell(hx, hy, 15.5, 12.5)
    ck = [(hx - 14, hy + 1), (hx - 18, hy + 4), (hx - 15, hy + 5), (hx - 17, hy + 8), (hx - 13, hy + 8),
          (hx - 13, hy + 11), (hx - 8, hy + 10)]
    head = head | poly(ck) | poly(mir(ck, hx))
    if P['fur_spike']:
        sp = [(hx - 15, hy - 3), (hx - 20, hy - 5), (hx - 15, hy)]
        head = head | poly(sp) | poly(mir(sp, hx))
    Hd.fill(head, C['fur'])
    Hd.rim(head)
    for w in ([(hx - 17, hy - 5), (hx - 11, hy - 3), (hx - 17, hy - 2)],
              [(hx - 18, hy + 4), (hx - 11, hy + 5), (hx - 18, hy + 6)],
              [(hx - 15, hy + 8), (hx - 10, hy + 8), (hx - 14, hy + 10)]):
        Hd.fill(poly(w) & head, C['stripe'])
        Hd.fill(poly(mir(w, hx)) & head, C['stripe'])
    for w in ([(hx - 6, hy - 11), (hx - 4, hy - 11), (hx - 4, hy - 6)],
              [(hx - 1, hy - 11), (hx + 1, hy - 11), (hx, hy - 5)],
              [(hx + 4, hy - 11), (hx + 6, hy - 11), (hx + 4, hy - 6)]):
        Hd.fill(poly(w) & head, C['stripe'])
    comp(cv, Hd)

    # 头顶毛簇 + 发夹
    T = Layer()
    T.fill(poly([(hx - 6, hy - 10), (hx - 10, hy - 16), (hx - 5, hy - 14), (hx - 3, hy - 20), (hx + 1, hy - 14),
                 (hx + 4, hy - 17), (hx + 5, hy - 10)]), C['fur'])
    comp(cv, T, inner=C['shade2'])
    for dx, dy in ((6, -13), (7, -12), (8, -11), (8, -13), (6, -11)):
        put(cv, hx + dx, hy + dy, C['clip'])
    if P['snowcap'] > 0:
        Sn = Layer()
        Sn.fill(ell(hx - 1, hy - 14, 4 + 2.0 * P['snowcap'], 1.2 + 0.9 * P['snowcap']), C['snow'])
        comp(cv, Sn, line=C['snow_l'], inner=C['snow_l'])

    # 五官
    fx, fy = hx + P['gx'], hy + P['gy']
    eL = P['eyeL'] or P['eyes']
    eR = P['eyeR'] or P['eyes']
    if P['glasses']:
        for ex in (fx - 7, fx + 7):
            for dy in range(-2, 3):
                for dx in range(-4, 5):
                    if abs(dx) == 4 and dy in (-2, 2):
                        continue
                    put(cv, ex + dx, fy + 2 + dy, C['glass'])
            put(cv, ex - 2, fy + 1, C['glass_h'])
            put(cv, ex - 1, fy + 2, C['glass_h'])
        for x in range(int(fx - 3), int(fx + 4)):
            put(cv, x, fy + 1, C['glass'])
        for x in list(range(int(hx - 15), int(fx - 11))) + list(range(int(fx + 12), int(hx + 16))):
            put(cv, x, fy + 1, C['glass'])
    else:
        draw_eye(cv, fx - 7, fy + 2, eL, P['gx'], False)
        draw_eye(cv, fx + 7, fy + 2, eR, P['gx'], True)
    for dx in (-1, 0, 1):
        put(cv, fx + dx, fy + 6, C['nose'])
    put(cv, fx, fy + 7, C['nose'])
    draw_mouth(cv, fx, fy, P['mouth'])
    if P['blush']:
        for sgn in (-1, 1):
            for dx in (0, 1, 2):
                put(cv, fx + sgn * (10 + dx), fy + 6, C['pad'])
    if P['leaf_face']:
        stamp(cv, fx - 3, fy + 3, [".GGG.", "GGgGG", ".GGG."], {'G': C['leaf'], 'g': (70, 120, 54)})

    # 文件(干活时叼着吃)
    if P['doc'] is not None:
        bite = int(P['doc'])
        D = Layer()
        x0, y0 = int(cx - 5), int(by - 22 + bite)
        hgt = 11 - bite
        D.fill((XX >= x0) & (XX <= x0 + 9) & (YY >= y0) & (YY <= y0 + hgt), C['paper'])
        for r in range(2, hgt, 2):
            D.fill((XX >= x0 + 2) & (XX <= x0 + 7) & (YY == y0 + r + 1), C['paper_l'])
        if bite:
            for xx in (x0 + 1, x0 + 4, x0 + 8):
                D.a[y0, xx] = 0
        comp(cv, D, inner=C['line'])

    if P['arms_front']:
        arms()
    return cv


def draw_side(P):
    """侧面(朝左)绘制,用于走路。phase: 步态相位;watch: 近侧手是否戴表。"""
    cv = np.zeros((S, S, 4), np.uint8)
    cx = CX + P.get('ox', 0)
    gy0 = G
    ph = P['phase']
    bob = P.get('bob', 0)
    by = gy0 + bob
    hx, hy = cx - 2, by - 32 + P.get('head_dy', 0)
    cv[ell(cx, G + 1, 14, 2.4)] = (20, 22, 30, 70)

    comp(cv, tail_layer(cx, by, P.get('tail', 0), 'up', side=True))

    def leg(phase, far):
        L = Layer()
        hipx, hipy = cx + 1, by - 8
        fxp = hipx + 5.0 * math.cos(phase)
        lift = max(0.0, math.sin(phase)) * 3.2
        fyp = gy0 - 2 - lift
        col = C['shade'] if far else C['fur']
        th = cap(hipx, hipy, fxp + 0.5, fyp - 2.5, 3.6)
        L.fill(th, col)
        if not far:
            L.rim(th)
            L.fill(poly([(hipx + 5, hipy - 1), (hipx - 1, hipy + 1), (hipx + 5, hipy + 2)]) & th, C['stripe'])
        f = ell(fxp - 1.5, fyp, 4.6, 2.4)
        L.fill(f, col)
        if not far:
            L.rim(f)
        return L

    def arm(phase, far):
        L = Layer()
        sx, sy = cx - 1, by - 17
        hxp = sx + 4.5 * math.cos(phase)
        hyp = by - 9 - abs(math.cos(phase)) * 1.5
        a = cap(sx, sy, hxp, hyp, 1.8) | circ(hxp, hyp, 2.3)
        L.fill(a, C['shade'] if far else C['fur'])
        mx, my = sx + (hxp - sx) * 0.45, sy + (hyp - sy) * 0.45
        L.fill(a & circ(mx, my, 1.3), C['stripe'])
        if P.get('watch', True) != far:
            wx, wy = sx + (hxp - sx) * 0.72, sy + (hyp - sy) * 0.72
            L.fill(a & circ(wx, wy, 1.7), C['watch_f'])
            L.fill(a & circ(wx, wy, 0.8), C['watch'])
        return L

    comp(cv, arm(ph, True))
    comp(cv, leg(ph + math.pi, True))

    B = Layer()
    body = ell(cx + 1, by - 12, 7.2, 8.2) | ell(cx - 1, by - 16, 5.5, 5)
    B.fill(body, C['fur'])
    B.rim(body)
    for yy in (by - 15, by - 9):
        B.fill(poly([(cx + 9, yy - 1), (cx + 3, yy), (cx + 9, yy + 2)]) & body, C['stripe'])
    comp(cv, B, inner=C['shade2'])
    comp(cv, leg(ph, False))
    for x in range(int(cx - 6), int(cx + 6)):
        if cv[int(by - 19), x, 3] == 255 and tuple(cv[int(by - 19), x, :3]) != C['line']:
            put(cv, x, by - 19, C['choker'])
    put(cv, cx - 5, by - 18, C['bell'])

    # 远耳、近耳
    for o, i in (([(hx - 9, hy - 8), (hx - 7, hy - 18), (hx - 1, hy - 10)], [(hx - 7, hy - 10), (hx - 6, hy - 15), (hx - 3, hy - 11)]),
                 ([(hx + 1, hy - 9), (hx + 7, hy - 20), (hx + 12, hy - 6)], [(hx + 4, hy - 10), (hx + 7, hy - 16), (hx + 9, hy - 8)])):
        E = Layer()
        E.fill(poly(o), C['stripe'])
        E.fill(poly(i), C['ear_in'])
        comp(cv, E)

    Hd = Layer()
    head = ell(hx, hy, 14.5, 12.5)
    head |= poly([(hx - 11, hy + 1), (hx - 17, hy + 4), (hx - 17, hy + 7), (hx - 13, hy + 10), (hx - 6, hy + 11)])
    head |= poly([(hx + 11, hy - 6), (hx + 18, hy - 3), (hx + 13, hy)])
    head |= poly([(hx + 12, hy + 1), (hx + 18, hy + 5), (hx + 12, hy + 7)])
    head |= poly([(hx + 1, hy + 10), (hx + 6, hy + 15), (hx + 9, hy + 9)])
    Hd.fill(head, C['fur'])
    Hd.rim(head)
    for w in ([(hx + 15, hy - 3), (hx + 5, hy - 1), (hx + 15, hy)],
              [(hx + 15, hy + 4), (hx + 3, hy + 5), (hx + 15, hy + 7)],
              [(hx + 10, hy + 9), (hx + 2, hy + 9), (hx + 8, hy + 11)],
              [(hx - 11, hy - 9), (hx - 9, hy - 9), (hx - 9, hy - 4)],
              [(hx - 5, hy - 12), (hx - 3, hy - 12), (hx - 4, hy - 6)],
              [(hx + 1, hy - 12), (hx + 3, hy - 12), (hx + 1, hy - 7)]):
        Hd.fill(poly(w) & head, C['stripe'])
    comp(cv, Hd)
    T = Layer()
    T.fill(poly([(hx - 10, hy - 9), (hx - 14, hy - 14), (hx - 8, hy - 13), (hx - 7, hy - 19), (hx - 3, hy - 13),
                 (hx, hy - 16), (hx, hy - 10)]), C['fur'])
    comp(cv, T, inner=C['shade2'])
    # 眼睛(侧面)
    ex, ey = hx - 8, hy + 2
    blink = P.get('blink', False)
    if blink:
        for dx in range(-2, 4):
            put(cv, ex + dx, ey, C['line'])
    else:
        stamp(cv, ex - 2, ey - 2, ["KKKKKK", "WRRRRK", "WOOOO.", ".YYYY."], EYEMAP)
        for dy in (-1, 0, 1):
            put(cv, ex, ey + dy, C['pupil'])
    put(cv, hx - 17, hy + 4, C['nose'])
    put(cv, hx - 17, hy + 5, C['nose'])
    put(cv, hx - 16, hy + 4, C['nose'])
    for dx in (-15, -14, -13):
        put(cv, hx + dx, hy + 8, C['mouth'])
    comp(cv, arm(ph + math.pi, False))
    return cv
