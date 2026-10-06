# -*- coding: utf-8 -*-
"""生成应用图标与安装程序美术(全部取自三虎的精灵帧):python tools/gen_art.py
美术素材版权 © 三虎 Sanhuu,保留所有权利。未经许可,禁止商用、二次修改、转载传播。"""
import json, os, glob
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SP = os.path.join(ROOT, 'assets', 'sprites')
OUT = os.path.join(ROOT, 'assets')
META = json.load(open(os.path.join(SP, 'sprites.json'), encoding='utf-8'))
INK, ORANGE, ORANGE2, CREAM, GOLD = (43, 45, 54), (232, 87, 30), (240, 138, 60), (246, 244, 240), (242, 194, 48)


def frame(anim, i):
    a = META['anims'][anim]
    sh = Image.open(os.path.join(SP, a['file'])).convert('RGBA')
    s = META['size']
    return sh.crop(((i % a['cols']) * s, (i // a['cols']) * s, (i % a['cols']) * s + s, (i // a['cols']) * s + s))


def up(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def font(size):
    for pat in ('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', '/System/Library/Fonts/PingFang.ttc',
                'C:/Windows/Fonts/msyhbd.ttc', 'C:/Windows/Fonts/msyh.ttc'):
        if os.path.exists(pat):
            return ImageFont.truetype(pat, size)
    return ImageFont.load_default()


def head(anim='idle_11', i=0):
    h = frame(anim, i).crop((META['cx'] - 22, META['ground'] - 54, META['cx'] + 22, META['ground'] - 16))
    h.paste((0, 0, 0, 0), (37, 31, 44, 38))      # 去掉裁进来的尾巴尖
    return h


def stripes(d, w, h, col, step=46):
    """虎纹装饰:左右两侧向内的楔形。"""
    for k, y in enumerate(range(20, h, step)):
        if k % 2 == 0:
            d.polygon([(0, y), (w * 0.34, y + 9), (0, y + 20)], fill=col)
        else:
            d.polygon([(w, y), (w * 0.66, y + 9), (w, y + 20)], fill=col)


def icon():
    im = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((16, 16, 496, 496), 108, fill=ORANGE2, outline=INK, width=14)
    d.rounded_rectangle((38, 38, 474, 474), 88, outline=(250, 180, 110), width=8)
    h = up(head(), 9)
    im.alpha_composite(h, ((512 - h.width) // 2, 96))
    im.save(os.path.join(OUT, 'icon.png'))
    im.save(os.path.join(OUT, 'icon.ico'), sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
    im.resize((1024, 1024), Image.NEAREST).save(os.path.join(OUT, 'icon.icns'))


def wizard(scale):
    w, h = 164 * scale, 314 * scale
    im = Image.new('RGBA', (w, h), INK + (255,))
    d = ImageDraw.Draw(im)
    stripes(d, w, h, (59, 62, 72), 46 * scale)
    d.rectangle((0, h - 54 * scale, w, h), fill=ORANGE)
    d.rectangle((0, h - 58 * scale, w, h - 54 * scale), fill=GOLD)
    f = up(frame('wave', 5), 1 if scale == 1 else 3)
    if scale == 1:
        f = up(frame('wave', 5).crop((14, 22, 82, 90)), 2)
    im.alpha_composite(f, ((w - f.width) // 2, h - 54 * scale - f.height + (6 if scale == 1 else 26)))
    d.text((w // 2, 30 * scale), '三虎', font=font(30 * scale), fill=(255, 255, 255), anchor='mm')
    d.text((w // 2, 58 * scale), 'S a n h u u', font=font(13 * scale), fill=GOLD, anchor='mm')
    d.text((w // 2, h - 27 * scale), '你的桌面小老虎', font=font(12 * scale), fill=(255, 255, 255), anchor='mm')
    im.convert('RGB').save(os.path.join(OUT, 'installer', f'wizard_{164 * scale}.bmp'))


def small(scale):
    w, h = 55 * scale, 58 * scale
    im = Image.new('RGBA', (w, h), ORANGE2 + (255,))
    hd = up(head(), scale)
    im.alpha_composite(hd, ((w - hd.width) // 2, (h - hd.height) // 2 + scale))
    im.convert('RGB').save(os.path.join(OUT, 'installer', f'small_{55 * scale}.bmp'))


def dmg_bg():
    w, h = 660, 420
    im = Image.new('RGBA', (w, h), CREAM + (255,))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w, 70), fill=INK)
    d.polygon([(0, 70), (120, 70), (0, 96)], fill=INK)
    d.polygon([(w, 70), (w - 120, 70), (w, 96)], fill=INK)
    d.rectangle((0, 70, w, 74), fill=ORANGE)
    d.text((w // 2, 35), '把三虎拖进「应用程序」文件夹', font=font(22), fill=(255, 255, 255), anchor='mm')
    # 像素箭头
    y = 205
    for i, x in enumerate(range(258, 392, 12)):
        d.rectangle((x, y - 4, x + 7, y + 4), fill=ORANGE if i % 2 == 0 else ORANGE2)
    d.polygon([(392, y - 18), (422, y), (392, y + 18)], fill=ORANGE)
    f = up(frame('happy', 3), 2)
    im.alpha_composite(f, ((w - f.width) // 2, 208))
    d.text((w // 2, h - 14), '美术素材版权 © 三虎 Sanhuu,保留所有权利。未经许可,禁止商用、二次修改、转载传播。',
           font=font(10), fill=(124, 128, 140), anchor='mm')
    im.convert('RGB').save(os.path.join(OUT, 'installer', 'dmg_background.png'))


if __name__ == '__main__':
    os.makedirs(os.path.join(OUT, 'installer'), exist_ok=True)
    icon(); wizard(1); wizard(2); small(1); small(2); dmg_bg()
    print('art ok')
