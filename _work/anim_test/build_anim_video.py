#!/usr/bin/env python3
"""视频抽帧 → 色键抠底 → 裁框 → 像素化归一 → 动画帧 + 预览GIF"""
import glob, os, sys
from PIL import Image, ImageOps

SRC_DIR = sys.argv[1]          # 帧目录（frame_XX.png）
OUT_DIR = sys.argv[2]          # 输出目录
OUT_SIZE = 160                 # 归一尺寸
BG_KEY = (50, 150, 39)         # 色键基色（实测视频背景）
KEY_TOL = 90                   # 色键距离容差

os.makedirs(OUT_DIR, exist_ok=True)
files = sorted(glob.glob(os.path.join(SRC_DIR, "frame_*.png")))
if not files:
    print("无帧文件"); sys.exit(1)

frames = []
for f in files:
    im = Image.open(f).convert("RGBA")
    px = im.load()
    w, h = im.size
    # 色键抠底：绿色距离>容差 保留，否则透明（软边：距离边缘平滑）
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            dist = abs(r - BG_KEY[0]) + abs(g - BG_KEY[1]) + abs(b - BG_KEY[2])
            if dist < KEY_TOL:
                px[x, y] = (r, g, b, 0)
    # 裁 bbox
    bbox = im.getbbox()
    if bbox is None:
        print(f"{f} 全透明，跳过"); continue
    im = im.crop(bbox)
    # 像素化：先缩到小尺寸（保留硬边），再放大回 OUT_SIZE 画布
    im = im.convert("RGB")  # 计算尺寸用
    ratio = OUT_SIZE / max(im.size)
    new_size = (max(1, int(im.size[0] * ratio)), max(1, int(im.size[1] * ratio)))
    im = im.convert("RGBA").resize(new_size, Image.NEAREST)
    canvas = Image.new("RGBA", (OUT_SIZE, OUT_SIZE), (0, 0, 0, 0))
    canvas.paste(im, ((OUT_SIZE - new_size[0]) // 2, OUT_SIZE - new_size[1]))
    frames.append(canvas)

# 输出帧
for i, fr in enumerate(frames):
    fr.save(os.path.join(OUT_DIR, f"{i+1:02d}.png"))
print(f"输出 {len(frames)} 帧 → {OUT_DIR}")

# 预览 GIF（白底，2 轮循环）
gif_frames = []
for fr in frames:
    bg = Image.new("RGB", (OUT_SIZE, OUT_SIZE), (245, 242, 236))
    bg.paste(fr, (0, 0), fr)
    gif_frames.append(bg.resize((OUT_SIZE * 3, OUT_SIZE * 3), Image.NEAREST))
gif_frames[0].save(os.path.join(OUT_DIR, "preview.gif"), save_all=True,
                   append_images=gif_frames[1:] + gif_frames, duration=125, loop=0)
print("预览: " + os.path.join(OUT_DIR, "preview.gif"))
