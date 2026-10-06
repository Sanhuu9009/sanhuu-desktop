# -*- coding: utf-8 -*-
"""三虎 Sanhuu 精灵表生成器:python tools/gen_sprites.py
输出 assets/sprites/*.png 与 sprites.json。
美术素材版权 © 三虎 Sanhuu,保留所有权利。未经许可,禁止商用、二次修改、转载传播。
"""
import json, math, os, random, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rig import *

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'sprites')
HX, HY = CX, G - 32          # 默认头中心
UPL, UPR = (-19, -36), (19, -36)
TAU = math.pi * 2

BM = {
    'heart': (["PP.PP", "PPPPP", "PPPPP", ".PPP.", "..P.."], {'P': C['pink']}),
    'heart_s': (["P.P", "PPP", ".P."], {'P': C['pink']}),
    'spark': (["..Y..", "..Y..", "YYWYY", "..Y..", "..Y.."], {'Y': C['spark'], 'W': (255, 255, 255)}),
    'spark_s': ([".Y.", "YWY", ".Y."], {'Y': C['spark'], 'W': (255, 255, 255)}),
    'z': (["ZZZZ", "..Z.", ".Z..", "ZZZZ"], {'Z': C['zz']}),
    'z_s': (["ZZZ", ".Z.", "ZZZ"], {'Z': C['zz']}),
    'bang': (["RR", "RR", "RR", "..", "RR"], {'R': C['bang']}),
    'sweat': ([".B.", "BBB", "BWB", ".B."], {'B': C['rain'], 'W': C['rain_l']}),
    'leaf': ([".GGG.", "GGgGG", "GgGGG", ".GGG."], {'G': C['leaf'], 'g': (70, 120, 54)}),
    'leaf2': ([".GGG.", "GGGgG", "GGgGG", ".GGG."], {'G': C['leaf2'], 'g': (170, 96, 30)}),
    'flake': ([".F.", "FWF", ".F."], {'F': C['flake'], 'W': (255, 255, 255)}),
    'puff': ([".WW.", "WWWW", "bWWb", ".bb."], {'W': C['snow'], 'b': C['snow_l']}),
    'tear': (["B", "B"], {'B': C['rain']}),
    'drop': (["B", "b", "b", "b"], {'B': C['rain_l'], 'b': C['rain']}),
    'splash': (["b...b", ".b.b."], {'b': C['rain_l']}),
    'dot': (["DD", "DD"], {'D': C['inner']}),
    'crumb': (["W"], {'W': C['shade2']}),
}


def fx_draw(cv, item):
    k, x, y = item[0], item[1], item[2]
    if k in BM:
        rows, cm = BM[k]
        stamp(cv, int(round(x)), int(round(y)), rows, cm)
    elif k == 'cloud':
        dark = item[3]
        L = Layer()
        m = circ(x - 7, y + 1, 4.5) | circ(x, y - 2, 6.5) | circ(x + 8, y + 1, 4.5) | ((abs(XX - x) <= 11) & (YY >= y) & (YY <= y + 5))
        L.fill(m, C['cloud_d'] if dark else C['cloud'])
        L.fill(m & (YY >= y + 4), C['cloud_dl'] if dark else C['shade'])
        comp(cv, L, line=C['cloud_dl'] if dark else C['cloud_l'], inner=None)
    elif k == 'sun':
        L = Layer()
        L.fill(circ(x, y, 6.2), C['sun'])
        ph = item[3]
        for i in range(8):
            a = TAU * i / 8 + (math.pi / 8 if ph else 0)
            L.fill(cap(x + 9 * math.cos(a), y + 9 * math.sin(a), x + 12 * math.cos(a), y + 12 * math.sin(a), 0.7), C['sun'])
        comp(cv, L, line=C['sun_l'], inner=None)
    elif k == 'bolt':
        L = Layer()
        pts = item[3]
        for (a, b), (c, d) in zip(pts[:-1], pts[1:]):
            L.fill(cap(a, b, c, d, 1.0), C['bolt'])
        comp(cv, L, line=C['sun_l'], inner=None)
    elif k == 'streak':
        for i in range(int(item[3])):
            put(cv, x + i, y, C['wind'])


def over(dst, src):
    m = src[..., 3] == 255
    dst[m] = src[m]
    sh = (src[..., 3] > 0) & ~m & (dst[..., 3] == 0)
    dst[sh] = src[sh]


def render(P, bg=(), fg=(), side=False):
    cv = np.zeros((S, S, 4), np.uint8)
    for it in bg:
        fx_draw(cv, it)
    over(cv, draw_side(P) if side else draw_front(P))
    for it in fg:
        fx_draw(cv, it)
    return cv


def pose(**kw):
    P = default_pose()
    P.update(kw)
    return P


def rain_fx(f, n, seed=7, um=False, bob=0):
    R = random.Random(seed)
    out = []
    for i in range(26):
        x0, ph, sp = R.randint(6, 110), R.randint(0, 79), R.choice((5, 6, 5))
        if i >= n:
            continue
        sp = 5
        y = (ph + f * sp) % 80 + 4
        x = x0 - int(y * 0.22)
        if um and abs(x - (CX + 2)) <= 22 and y > HY - 30 + bob:
            if y - sp <= HY - 30 + bob and abs(x - (CX + 2)) <= 20:
                out.append(('splash', x - 2, HY - 30 + bob + (abs(x - CX - 2) // 6)))
            continue
        if y >= 80:
            out.append(('splash', x - 2, G))
        else:
            out.append(('drop', x, y))
    return out


# ---------------- 各状态逐帧编排 ----------------
def a_idle(gx, gy):
    fr = []
    for f in range(24):
        fr.append(render(pose(gx=gx, gy=gy, bob=1 if 12 <= f < 22 else 0,
                              eyes='closed' if f in (19, 20) else 'half',
                              tail=math.sin(TAU * f / 24) * 1.0, earR=2 if f in (6, 7) else 0)))
    return fr


def a_wave():
    fr = []
    for f in range(16):
        fg = [('heart', 68, 40 - (f - 4) // 2)] if 4 <= f < 14 else []
        fr.append(render(pose(armR=(19 + round(2 * math.sin(TAU * f / 4)), -36), eyeL='happy', mouth='smile',
                              bob=(f // 2) % 2, tail=math.sin(TAU * f / 8) * 1.5, blush=True), fg=fg))
    return fr


def a_happy():
    fr = []
    hop = [0, 3, 6, 7, 6, 3, 0, 0]
    for f in range(16):
        h = hop[f % 8]
        fg = [('heart', 20, 44 - f), ('heart_s', 74, 38 - f // 2 - (f % 2)),
              ('spark' if f % 4 < 2 else 'spark_s', 72 if f < 8 else 18, 26 + (f % 8))]
        fr.append(render(pose(oy=-h, drop=2 if f % 8 == 7 else 0, tuck=2 if h > 4 else 0, armL=UPL, armR=UPR,
                              eyes='happy', mouth='open', blush=True, tail=math.sin(TAU * f / 8) * 2), fg=fg))
    return fr


def a_jump():
    seq = [dict(drop=2), dict(drop=4, armL=(-13, -5), armR=(13, -5)),
           dict(oy=-5, armL=UPL, armR=UPR, mouth='open'),
           dict(oy=-12, tuck=2, armL=UPL, armR=UPR, mouth='open', eyes='happy'),
           dict(oy=-17, tuck=3, armL=UPL, armR=UPR, mouth='open', eyes='happy'),
           dict(oy=-19, tuck=3, armL=UPL, armR=UPR, mouth='open', eyes='happy'),
           dict(oy=-16, tuck=2, armL=UPL, armR=UPR, mouth='open', eyes='happy'),
           dict(oy=-9, armL=(-18, -30), armR=(18, -30), eyes='wide', mouth='o'),
           dict(oy=-2, armL=(-18, -24), armR=(18, -24), eyes='wide', mouth='o'),
           dict(drop=4, armL=(-15, -5), armR=(15, -5), eyes='squeeze', mouth='flat'),
           dict(drop=2, eyes='happy', mouth='smile'), dict(eyes='happy', mouth='smile')]
    return [render(pose(tail=1.5 - i * 0.2, **p)) for i, p in enumerate(seq)]


def a_land():
    seq = [dict(oy=-10, armL=UPL, armR=UPR, eyes='wide', mouth='o', tail_mode='up', tail=2),
           dict(oy=-4, armL=(-18, -30), armR=(18, -30), eyes='wide', mouth='o', tail=2),
           dict(drop=4, armL=(-15, -5), armR=(15, -5), eyes='squeeze', mouth='flat', ears='down'),
           dict(drop=3, armL=(-14, -6), armR=(14, -6), eyes='squeeze', mouth='flat'),
           dict(drop=1, eyes='closed'), dict(mouth='smile')]
    return [render(pose(**p)) for p in seq]


def a_drag(fast):
    fr = []
    for f in range(8):
        sw = math.sin(TAU * f / 8) * (3.0 if fast else 1.5)
        if fast:
            a = round(4 * math.sin(TAU * f / 4))
            P = pose(oy=-8, legs='dangle', swing=sw, tail_mode='down', tail=sw / 2, eyes='squeeze', mouth='open',
                     armL=(-17, -20 + a), armR=(17, -20 - a), ears='down', head_dx=round(sw / 3))
            fg = [('sweat', 68 + (f % 2), 42 + f % 4), ('sweat', 24 - (f % 2), 46 + (f + 2) % 4)]
        else:
            P = pose(oy=-8, legs='dangle', swing=sw, tail_mode='down', tail=sw / 2, eyes='wide', gy=-1, mouth='o',
                     armL=(-9 + sw * 0.5, -6), armR=(9 + sw * 0.5, -6), earL=2, earR=2)
            fg = [('sweat', 67, 40 + f // 2)] if f < 6 else []
        fr.append(render(P, fg=fg))
    return fr


def a_sleep():
    fr = []
    for f in range(24):
        fg = []
        for k in range(3):
            t = (f + k * 8) % 24
            fg.append(('z' if t > 10 else 'z_s', 66 + t // 3, 44 - t))
        fr.append(render(pose(legs='sit', drop=4, armL=(-6, -5), armR=(6, -5), arms_front=True, eyes='sleep',
                              head_dy=1 if f >= 12 else 0, earL=2, earR=2, tail=0.3), fg=fg))
    return fr


def a_work():
    fr = []
    for f in range(16):
        bite = (f // 4) * 2
        fg = [('crumb', 40 + (f * 5) % 17, 62 + (f % 4) * 2), ('crumb', 52 - (f * 3) % 9, 64 + ((f + 2) % 4) * 2)]
        fr.append(render(pose(doc=bite, armL=(-6, -15 + bite // 2), armR=(6, -15 + bite // 2), arms_front=True,
                              eyes='happy' if f % 4 < 2 else 'closed', mouth='w', bob=f % 2,
                              tail=math.sin(TAU * f / 8) * 1.5, blush=True), fg=fg))
    return fr


def a_walk(right):
    fr = []
    for f in range(8):
        ph = TAU * f / 8
        im = render(dict(phase=ph, bob=1 if f % 4 == 0 else 0, tail=math.sin(ph), watch=not right,
                         blink=False), side=True)
        fr.append(im[:, ::-1].copy() if right else im)
    return fr


def clouds(f, dark, spec):
    return [('cloud', (x0 + 1.5 * f) % 120 - 12, y, dark) for x0, y in spec]


def a_rain():
    fr = []
    for f in range(80):
        bg = clouds(f, True, [(10, 9), (70, 12)])
        P, fg, um, bob = pose(), [], False, 0
        if f < 12:
            P = pose(gy=-1, eyes='squeeze' if f in (8, 9) else 'half', mouth='frown' if f >= 6 else 'w',
                     earR=2 if f in (3, 4) else 0)
            n = 2 + f * 2
        elif f < 36:
            n = 26
            if f < 20:
                P = pose(legs='sit', drop=4, armL=(1, -6), armR=(-1, -8), arms_front=True, ears='down',
                         eyes='squeeze', mouth='frown', ox=f % 2, tail=-0.5)
            else:
                P = pose(legs='sit', drop=4, armL=(1, -6), armR=(-1, -8), arms_front=True, ears='down',
                         eyes='half', gy=1, mouth='frown', ox=f % 2, tail=-0.5)
                t = (f - 20) % 6
                fg += [('tear', CX - 9 + f % 2, HY + 4 + 9 + t * 2), ('tear', CX + 9 + f % 2, HY + 4 + 9 + ((t + 3) % 6) * 2)]
        elif f < 40:
            n = 26
            P = pose(eyes='wide', mouth='o', gy=-1)
            fg.append(('bang', 70, 36))
        elif f < 76:
            n = 26
            o = min(1.0, (f - 39) / 4)
            bob = 1 if (f % 8) >= 4 and f >= 44 else 0
            look = 58 <= f < 64
            P = pose(umbrella=o, armR=(9, -13), eyes='half' if (f < 44 or look) else 'happy', gy=-1 if look else 0,
                     mouth='smile', bob=bob, tail=math.sin(TAU * f / 16) * 1.5, blush=f >= 44)
            um = o > 0.6
        else:
            n = 26 - (f - 75) * 5
            P = pose(umbrella=(80 - f) / 5, armR=(9, -13), mouth='smile')
        fg += rain_fx(f, n, um=um, bob=bob)
        fr.append(render(P, bg=bg, fg=fg))
    return fr


def a_sunny():
    fr = []
    for f in range(80):
        bg = [('sun', 17, 16, (f // 4) % 2)]
        fg = []
        if f < 6:
            P = pose(gx=-1, gy=-1)
        elif f < 10:
            P = pose(gx=-1, gy=-1, eyes='squeeze', mouth='flat')
        elif f < 14:
            P = pose(eyes='squeeze', armR=(8, -31), arms_front=True)
        elif f < 16:
            P = pose(glasses=True, armR=(10, -30), arms_front=True, mouth='smile')
        elif f < 56:
            P = pose(glasses=True, mouth='smile', bob=1 if f % 8 >= 4 else 0, tail=math.sin(TAU * f / 16) * 1.5)
            if f % 16 < 4:
                fg.append(('spark' if f % 16 in (1, 2) else 'spark_s', CX + 9, HY - 4 + P['bob']))
            if 40 <= f < 52:
                fg.append(('sweat', CX + 17, HY - 10 + (f - 40) // 2))
        elif f < 68:
            up = min(1, (f - 55) / 3)
            P = pose(glasses=True, mouth='open', armL=(-19, -8 - 28 * up), armR=(19, -8 - 28 * up), drop=-1,
                     tail=2, blush=True)
            fg += [('spark_s' if f % 2 else 'spark', 16 + (f % 3) * 28, 30 + (f % 4) * 3)]
        elif f < 76:
            P = pose(glasses=True, mouth='smile', tail=math.sin(TAU * f / 16) * 1.5)
        elif f < 78:
            P = pose(glasses=True, armR=(10, -30), arms_front=True, mouth='smile')
        else:
            P = pose(eyes='happy' if f == 78 else 'half', mouth='smile')
        fr.append(render(P, bg=bg, fg=fg))
    return fr


def a_cloudy():
    fr = []
    for f in range(80):
        bg = clouds(f, False, [(0, 10), (45, 15), (85, 8)])
        fg = []
        if f < 36:
            P = pose(gx=(-1, 0, 1)[f // 12], gy=-1, tail=math.sin(TAU * f / 40))
        elif f < 40:
            P = pose(eyes='closed', mouth='o', head_dy=-1)
        elif f < 48:
            P = pose(eyes='sleep', mouth='yawn', head_dy=-1, armL=(-19, -34), armR=(13, -4), drop=-1)
        elif f < 52:
            P = pose(eyes='closed', mouth='w')
            fg.append(('tear', CX - 11, HY + 5))
        else:
            P = pose(eyes='closed' if f in (66, 67) else 'half', earR=2 if f in (58, 59) else 0,
                     tail=math.sin(TAU * f / 40), bob=1 if f % 16 >= 8 else 0)
            if 60 <= f < 74:
                for k in range(min(3, (f - 60) // 3 + 1)):
                    fg.append(('dot', 66 + k * 4, 34 - k * 2))
        fr.append(render(P, bg=bg, fg=fg))
    return fr


def a_snow():
    fr = []
    R0 = random.Random(3)
    fl = [(R0.randint(4, 92), R0.randint(0, 79), R0.random() * TAU) for _ in range(18)]
    for f in range(80):
        fg = [('flake', x0 + 2 * math.sin(TAU * 2 * f / 80 + p), (ph + f) % 80 + 4) for x0, ph, p in fl]
        bg = clouds(f, False, [(20, 9), (80, 12)])
        if f < 10:
            P = pose(gy=-1, tail=math.sin(TAU * f / 20))
        elif f < 16:
            P = pose(eyes='wide', mouth='o')
            fg.append(('flake', CX - 1, HY + 4))
        elif f < 18:
            P = pose(eyes='closed', mouth='smile')
        elif f < 32:
            h = [0, 3, 6, 7, 6, 3, 0][(f - 18) % 7]
            P = pose(oy=-h, armL=UPL, armR=UPR, eyes='happy', mouth='open', blush=True, tail=2, tuck=2 if h > 4 else 0)
        elif f < 36:
            P = pose(eyes='squeeze', mouth='flat', ox=f % 2, armL=(3, -11), armR=(-3, -12), arms_front=True)
        elif f < 68:
            cap_ = max(0.0, min(1.0, (f - 44) / 16))
            P = pose(scarf=(f // 2) % 2, armL=(3, -11), armR=(-3, -12), arms_front=True,
                     ox=f % 2 if f < 52 else 0, eyes='closed' if f in (57, 58) else 'half', mouth='flat',
                     snowcap=cap_, tail=math.sin(TAU * f / 20) * 0.6, blush=True)
            if (f - 36) % 12 < 5:
                fg.append(('puff', CX - 22 - ((f - 36) % 12), HY + 9 - ((f - 36) % 12) // 2))
        elif f < 74:
            d = 1 if f % 2 else -1
            P = pose(scarf=f % 2, head_dx=d, eyes='squeeze', mouth='flat', snowcap=max(0, 1 - (f - 67) / 5), blush=True)
            fg += [('flake', CX + d * (14 + (f - 68) * 2), HY - 16 + (f - 68)), ('flake', CX - d * (10 + (f - 68) * 2), HY - 18 + (f - 68) * 2)]
        else:
            P = pose(scarf=0 if f < 78 else None, eyes='happy', mouth='smile', blush=True)
        fr.append(render(P, bg=bg, fg=fg))
    return fr


def a_thunder():
    fr = []
    b1 = [(24, 17), (18, 34), (25, 37), (15, 58), (21, 60), (11, 83)]
    b2 = [(96 - x, y) for x, y in b1]
    for f in range(80):
        bg = clouds(f, True, [(5, 8), (45, 11), (85, 8)])
        fg = []
        if f in (12, 13):
            bg.append(('bolt', 0, 0, b1))
        if f in (44, 46):
            bg.append(('bolt', 0, 0, b2))
        cover = dict(legs='sit', drop=4, armL=(-18, -35), armR=(18, -35), ears='down', mouth='frown')
        if f < 12:
            P = pose(gy=-1, mouth='frown', earL=2 if f in (5, 6) else 0, earR=2 if f in (8, 9) else 0)
        elif f < 16:
            P = pose(oy=-4 if f < 14 else -2, eyes='wide', mouth='o', fur_spike=True, armL=(-18, -14), armR=(18, -14), tail=2)
            fg.append(('bang', 70, 30))
        elif f < 30:
            P = pose(eyes='squeeze', ox=f % 2, **cover)
        elif f < 44:
            P = pose(eyeL='squeeze', eyeR='half', gy=-1, **cover)
        elif f < 48:
            P = pose(eyes='wide', fur_spike=True, ox=(f % 2) * 2 - 1, **cover)
            fg.append(('bang', 24, 34))
        elif f < 68:
            P = pose(eyes='squeeze', ox=f % 2 if f < 60 else 0, **cover)
            if f >= 56:
                fg.append(('tear', CX - 9, HY + 13 + (f % 4) * 2))
        elif f < 72:
            P = pose(gy=-1, ears='down', mouth='frown')
        else:
            P = pose(eyes='closed' if f < 76 else 'half', mouth='flat' if f < 76 else 'w', earL=2, earR=2)
            if f < 77:
                fg.append(('puff', CX - 22 - (f - 72), HY + 9))
        fg += rain_fx(f, 20, seed=11)
        fr.append(render(P, bg=bg, fg=fg))
    return fr


def a_wind():
    fr = []
    R0 = random.Random(5)
    st = [(R0.randint(0, 159), R0.randint(12, 82), R0.randint(9, 18)) for _ in range(14)]
    lv = [(R0.randint(0, 159), R0.randint(20, 78), R0.random() * TAU, R0.choice(('leaf', 'leaf2'))) for _ in range(7)]
    push = [0, 0, 1, 1, 2, 2, 3, 3, 2, 1]
    for f in range(80):
        bg = [('streak', (x0 - 6 * f) % 160 - 32, y, n) for x0, y, n in st]
        fg = [(k, (x0 - 4 * f) % 160 - 32, y + 3 * math.sin(TAU * 3 * f / 80 + p)) for x0, y, p, k in lv]
        gust = f % 20 < 10
        base = dict(ears='down', tail_mode='blown', tail=math.sin(TAU * f / 8), ox=-push[(f // 2) % 10], mouth='flat')
        if 36 <= f < 50:
            P = pose(leaf_face=True, eyes='wide', armL=(-17, -16), armR=(17, -16), **base)
        elif 50 <= f < 56:
            P = pose(head_dx=1 if f % 2 else -1, eyes='squeeze', **base)
            fg.append(('leaf', CX - 12 - (f - 50) * 6, HY + 2 + (f - 50)))
        else:
            P = pose(eyes='squeeze' if gust else 'half', gx=0 if gust else 1, head_dx=-1 if gust else 0,
                     armR=(20, -33) if gust else (11, -8), **base)
        fr.append(render(P, bg=bg, fg=fg))
    return fr


def save_sheet(name, frames, fps, loop, meta, cols=10):
    n = len(frames)
    rows = (n + cols - 1) // cols
    sheet = Image.new('RGBA', (S * min(n, cols), S * rows), (0, 0, 0, 0))
    for i, fr in enumerate(frames):
        sheet.paste(Image.fromarray(fr), ((i % cols) * S, (i // cols) * S))
    sheet.save(os.path.join(OUT, name + '.png'), optimize=True)
    meta['anims'][name] = dict(file=name + '.png', frames=n, fps=fps, loop=loop, cols=min(n, cols))


def build():
    os.makedirs(OUT, exist_ok=True)
    meta = dict(size=S, ground=G, cx=CX, grab=[CX, G - 8 - 32 - 6], anims={},
                copyright='美术素材版权 © 三虎 Sanhuu,保留所有权利。未经许可,禁止商用、二次修改、转载传播。')
    for gx in (-1, 0, 1):
        for gy in (-1, 0, 1):
            save_sheet(f'idle_{gx + 1}{gy + 1}', a_idle(gx, gy), 8, True, meta)
    for name, fn, fps, loop in [
        ('wave', a_wave, 10, False), ('happy', a_happy, 12, False), ('jump', a_jump, 12, False),
        ('land', a_land, 12, False), ('drag', lambda: a_drag(False), 8, True),
        ('drag_fast', lambda: a_drag(True), 12, True), ('sleep', a_sleep, 6, True), ('work', a_work, 8, True),
        ('walk_l', lambda: a_walk(False), 10, True), ('walk_r', lambda: a_walk(True), 10, True),
        ('rain', a_rain, 8, False), ('sunny', a_sunny, 8, False), ('cloudy', a_cloudy, 8, False),
        ('snow', a_snow, 8, False), ('thunder', a_thunder, 8, False), ('wind', a_wind, 8, False)]:
        save_sheet(name, fn(), fps, loop, meta)
    with open(os.path.join(OUT, 'sprites.json'), 'w', encoding='utf-8') as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=1)
    tot = sum(a['frames'] for a in meta['anims'].values())
    print('animations:', len(meta['anims']), 'frames:', tot)


if __name__ == '__main__':
    build()
