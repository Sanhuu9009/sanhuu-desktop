# -*- coding: utf-8 -*-
"""格式转换 + 压缩/解压（纯 Python，跨平台）"""
import os
import shutil
import zipfile

from PyQt6.QtWidgets import QMessageBox


# ---------- 图片转换 ----------
IMG_FORMATS = {"png": "PNG", "jpg": "JPEG", "jpeg": "JPEG", "webp": "WEBP", "bmp": "BMP", "gif": "GIF", "ico": "ICO"}


def convert_image(src, dst_format):
    from PIL import Image
    im = Image.open(src)
    if dst_format == "ico":
        im.convert("RGBA").save(_out_path(src, "ico"))
        return _out_path(src, "ico")
    out = _out_path(src, dst_format)
    if dst_format in ("jpg", "jpeg"):
        im.convert("RGB").save(out, quality=92)
    else:
        im.save(out)
    return out


# ---------- 文本 → PDF ----------
def convert_text_pdf(src):
    out = _out_path(src, "pdf")
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=11)
    with open(src, encoding="utf-8", errors="ignore") as f:
        for line in f.read().splitlines():
            pdf.multi_cell(0, 6, line)
    pdf.output(out)
    return out


# ---------- 视频 → GIF（抽帧） ----------
def convert_video_gif(src, fps=8, scale=0.5):
    out = _out_path(src, "gif")
    try:
        import imageio
        reader = imageio.get_reader(src, format="FFMPEG")
        frames = [im for _, im in zip(range(120), reader)]
        if not frames:
            raise RuntimeError("无法读取视频帧")
        import numpy as np
        frames = [np.asarray(f)[:: max(1, f.shape[0] // 360), :: max(1, f.shape[0] // 360)] for f in frames]
        imageio.mimsave(out, frames, fps=fps)
        return out
    except Exception as e:
        QMessageBox.warning(None, "转换失败", f"视频转 GIF 失败：{e}\n请确认安装了 imageio-ffmpeg")
        return None


# ---------- 压缩 ----------
def make_zip(paths, out_zip, password=None):
    if password:
        import pyzipper
        with pyzipper.AESZipFile(out_zip, "w", compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as z:
            z.setpassword(password.encode())
            _add_to_zip(z, paths, "")
        return
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
        _add_to_zip(z, paths, "")


def _add_to_zip(z, paths, prefix):
    for p in paths:
        if os.path.isdir(p):
            for root, _, files in os.walk(p):
                for f in files:
                    fp = os.path.join(root, f)
                    arc = os.path.join(prefix, os.path.relpath(fp, os.path.dirname(p) if os.path.isdir(p) else p))
                    z.write(fp, arc)
        else:
            z.write(p, os.path.join(prefix, os.path.basename(p)))


def make_7z(paths, out_7z, password=None):
    import py7zr
    if password:
        with py7zr.SevenZipFile(out_7z, "w", password=password) as z:
            for p in paths:
                if os.path.isdir(p):
                    z.writeall(p, os.path.basename(p))
                else:
                    z.write(p, os.path.basename(p))
    else:
        with py7zr.SevenZipFile(out_7z, "w") as z:
            for p in paths:
                if os.path.isdir(p):
                    z.writeall(p, os.path.basename(p))
                else:
                    z.write(p, os.path.basename(p))


def extract_archive(arc, out_dir, password=None):
    ext = os.path.splitext(arc)[1].lower()
    if ext == ".zip":
        if password:
            import pyzipper
            with pyzipper.AESZipFile(arc) as z:
                if password:
                    z.setpassword(password.encode())
                z.extractall(out_dir)
        else:
            with zipfile.ZipFile(arc) as z:
                z.extractall(out_dir)
    elif ext == ".7z":
        import py7zr
        with py7zr.SevenZipFile(arc, password=password) as z:
            z.extractall(out_dir)
    elif ext in (".rar",):
        # rar 依赖外部 unrar/7z
        rar = shutil.which("7z") or shutil.which("7zz") or shutil.which("unrar")
        if not rar:
            raise RuntimeError("RAR 解压需要系统安装 7-Zip 或 unrar")
        import subprocess
        cmd = [rar, "x", "-y", "-o" + out_dir, arc]
        if password:
            cmd.insert(1, "-p" + password)
        subprocess.run(cmd, check=True)
    else:
        raise RuntimeError(f"不支持的压缩格式：{ext}")


def _out_path(src, ext):
    base, _ = os.path.splitext(src)
    return base + "." + ext
