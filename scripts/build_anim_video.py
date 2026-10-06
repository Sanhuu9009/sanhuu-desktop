#!/usr/bin/env python3
"""视频抽帧 v2：滑动窗口选循环闭合段 → 色键抠底 → 像素化 → 帧 + GIF + manifest"""
import glob, os, sys, json
from PIL import Image
import numpy as np

BASE = "/home/user/Doubao/chats/38445661819308290/tiger-pet/_work/anim_v2"
OUT_ROOT = "/home/user/Doubao/chats/38445661819308290/tiger-pet/assets/anim"
STATES = ["idle", "walk", "happy", "rain", "jump"]
WIN = 16          # 循环窗口帧数（8fps × 2s）
OUT_SIZE = 160
BG_KEY = None  # 每段自动检测
KEY_TOL = 90

def detect_bg(im):
    """取四角区域平均色作为背景键"""
    h, w = im.shape[:2]
    pts = [im[:15, :15], im[:15, -15:], im[-15:, :15], im[-15:, -15:]]
    return np.concatenate([p.reshape(-1, 4)[:, :3] for p in pts]).mean(axis=0)

def load(paths):
    return [np.array(Image.open(p).convert("RGBA"), dtype=np.int32) for p in paths]

def key_alpha(arr, bg):
    """色键抠底：与背景距离<容差 → alpha=0"""
    r, g, b, a = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3]
    dist = np.abs(r - bg[0]) + np.abs(g - bg[1]) + np.abs(b - bg[2])
    arr = arr.copy()
    arr[..., 3] = np.where(dist < KEY_TOL, 0, a)
    return arr

def pick_loop(imgs):
    """滑动窗口选首尾差异最小的窗口（惩罚静止窗口）"""
    n = len(imgs)
    best, best_score = None, 1e9
    for s in range(0, n - WIN):
        seg = imgs[s:s + WIN]
        d_loop = np.abs(seg[0].astype(int) - seg[-1].astype(int)) > 40
        loop_pct = d_loop[..., :3].any(axis=2).mean() * 100
        # 窗口内动作量（相邻平均显著差异）
        motion = []
        for i in range(WIN - 1):
            d = np.abs(seg[i].astype(int) - seg[i + 1].astype(int)) > 40
            motion.append(d[..., :3].any(axis=2).mean() * 100)
        avg_motion = np.mean(motion)
        score = loop_pct - (avg_motion * 0.5)  # 鼓励有动作+闭合
        if score < best_score and avg_motion > 2:
            best_score, best = score, (s, loop_pct, avg_motion)
    if best is None:
        s = 0
        d = np.abs(imgs[0].astype(int) - imgs[WIN - 1].astype(int)) > 40
        best = (s, d[..., :3].any(axis=2).mean() * 100, 0)
    return best

def pixelate(im, out=OUT_SIZE):
    """像素化归一：色键 → bbox 裁切 → NEAREST 缩放 → 居中画布"""
    im = key_alpha(im, detect_bg(im))
    pil = Image.fromarray(im.astype(np.uint8), "RGBA")
    bbox = pil.getbbox()
    if bbox is None:
        return Image.new("RGBA", (out, out), (0, 0, 0, 0))
    pil = pil.crop(bbox)
    ratio = out / max(pil.size)
    ns = (max(1, int(pil.size[0] * ratio)), max(1, int(pil.size[1] * ratio)))
    pil = pil.resize(ns, Image.NEAREST)
    canvas = Image.new("RGBA", (out, out), (0, 0, 0, 0))
    canvas.paste(pil, ((out - ns[0]) // 2, out - ns[1]))
    return canvas

manifest = {}
for st in STATES:
    files = sorted(glob.glob(os.path.join(BASE, f"{st}_[0-9]*.png")))
    imgs = load(files)
    if st == "jump":
        # 一次性动作：取中段完整跳跃（蓄力→腾空→落地），每2帧取1
        start = 12
        picked = imgs[start:start + 24:2]
        info = {"mode": "once", "frame_ms": 100}
    else:
        s, loop_pct, avg_m = pick_loop(imgs)
        picked = imgs[s:s + WIN]
        info = {"mode": "loop", "frame_ms": 125, "loop_pct": round(loop_pct, 1), "motion_pct": round(avg_m, 1)}
    out_dir = os.path.join(OUT_ROOT, st)
    os.makedirs(out_dir, exist_ok=True)
    frames = [pixelate(im) for im in picked]
    for i, fr in enumerate(frames):
        fr.save(os.path.join(out_dir, f"{i + 1:02d}.png"))
    # 预览 GIF
    gifs = []
    for fr in frames:
        bg = Image.new("RGB", (OUT_SIZE, OUT_SIZE), (245, 242, 236))
        bg.paste(fr, (0, 0), fr)
        gifs.append(bg.resize((OUT_SIZE * 3, OUT_SIZE * 3), Image.NEAREST))
    gifs[0].save(os.path.join(OUT_ROOT, "previews", f"{st}.gif"), save_all=True,
                 append_images=gifs[1:] + gifs, duration=info.get("frame_ms", 125), loop=0)
    manifest[st] = {"frames": len(frames), "frame_ms": info["frame_ms"], "mode": info["mode"],
                    **({k: v for k, v in info.items() if k not in ("mode", "frame_ms")})}
    print(f"{st}: {len(frames)}帧 {info}")

os.makedirs(os.path.join(OUT_ROOT, "previews"), exist_ok=True)
with open(os.path.join(OUT_ROOT, "atlas-manifest.json"), "w") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)
print("manifest 已写入", json.dumps(manifest, ensure_ascii=False))
