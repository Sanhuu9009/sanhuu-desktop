#!/usr/bin/env python3
"""三虎动画帧后处理：绿幕抠底 -> 像素化归一 160x160 透明帧 -> atlas manifest。
用法: python3 scripts/build_anim.py
"""
import os, json, math
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "anim_rows")     # 生成帧所在
OUT = os.path.join(ROOT, "assets", "anim")  # 输出目录

STATES = ["idle", "walk", "happy", "rain", "jump"]
CANVAS = 160          # 输出画布
TARGET_H = 142        # 角色在画布中的高度（留白）
GREEN = (0, 255, 0)
KEY_TOL = 130         # 绿幕色距阈值（角色主色距绿均>220，安全）

def chroma_key(img, tol=KEY_TOL):
    """把接近纯绿(0,255,0)的像素（含过渡带）转透明。"""
    px = img.convert("RGBA")
    data = px.load()
    w, h = px.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = data[x, y]
            if a == 0:
                continue
            d = math.sqrt((r-0)**2 + (g-255)**2 + (b-0)**2)
            if d <= tol:
                data[x, y] = (r, g, b, 0)
    return px

def process_frame(path, out_path):
    img = Image.open(path).convert("RGBA")
    img = chroma_key(img)
    # 裁切角色 bbox（alpha>0）
    bbox = img.getbbox()
    if not bbox:
        raise RuntimeError(f"empty frame: {path}")
    img = img.crop(bbox)
    # 像素化：先缩到像素网格（目标高度 TARGET_H），再放大到画布
    scale = TARGET_H / img.height
    pw = max(1, round(img.width * scale))
    ph = TARGET_H
    img = img.resize((pw, ph), Image.NEAREST)
    # 放入 160x160 画布（底部对齐、水平居中）
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    x = (CANVAS - pw) // 2
    y = CANVAS - ph
    canvas.paste(img, (x, y), img)
    canvas.save(out_path)
    return pw, ph

def main():
    os.makedirs(OUT, exist_ok=True)
    manifest = {
        "meta": {
            "character": "三虎 Sanhuu",
            "pixel_style": "16-bit pixel",
            "frame_size": [CANVAS, CANVAS],
            "background": "transparent",
            "copyright": "美术素材版权 © 三虎 Sanhuu，保留所有权利。未经许可，禁止商用、二次修改、转载传播。"
        },
        "states": {}
    }
    for st in STATES:
        frames = []
        i = 1
        while True:
            p = os.path.join(SRC, f"{st}-f{i}.png")
            if not os.path.exists(p):
                break
            frames.append(p)
            i += 1
        if not frames:
            print(f"[skip] {st}: no frames")
            continue
        st_out = os.path.join(OUT, st)
        os.makedirs(st_out, exist_ok=True)
        sizes = []
        for idx, fp in enumerate(frames, 1):
            out_p = os.path.join(st_out, f"{idx:02d}.png")
            pw, ph = process_frame(fp, out_p)
            sizes.append([pw, ph])
        manifest["states"][st] = {
            "frame_count": len(frames),
            "frames": [f"{st}/{i:02d}.png" for i in range(1, len(frames)+1)],
            "fps": 8,
            "pixel_sizes": sizes
        }
        print(f"[ok] {st}: {len(frames)} frames")
    with open(os.path.join(OUT, "atlas-manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print("manifest ->", os.path.join(OUT, "atlas-manifest.json"))

if __name__ == "__main__":
    main()
