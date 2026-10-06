# -*- coding: utf-8 -*-
"""压缩 / 解压。zip 用 pyzipper(AES-256),7z 用 py7zr;rar 的解压用 7-Zip / unrar,
rar 的压缩因 RAR 格式专利限制,只能调用用户已安装的 WinRAR / rar 命令行。"""
import os, shutil, subprocess, sys
from .paths import unique_path, resource, no_window_kwargs


class NeedPassword(Exception):
    pass


class ToolMissing(Exception):
    pass


def _which(names, extra=()):
    for d in extra:
        for n in names:
            p = os.path.join(d, n + ('.exe' if sys.platform == 'win32' else ''))
            if os.path.isfile(p):
                return p
    for n in names:
        p = shutil.which(n)
        if p:
            return p
    return None


def find_7z():
    extra = [resource('vendor')]
    if sys.platform == 'win32':
        extra += [os.path.join(os.environ.get(k, ''), '7-Zip') for k in ('ProgramFiles', 'ProgramFiles(x86)', 'ProgramW6432')]
    else:
        extra += ['/opt/homebrew/bin', '/usr/local/bin']
    return _which(['7z', '7zz', '7za'], extra)


def find_rar():
    extra = []
    if sys.platform == 'win32':
        extra = [os.path.join(os.environ.get(k, ''), 'WinRAR') for k in ('ProgramFiles', 'ProgramFiles(x86)', 'ProgramW6432')]
    else:
        extra = ['/opt/homebrew/bin', '/usr/local/bin', '/Applications/rar']
    return _which(['rar', 'Rar'], extra)


def find_unrar():
    extra = ['/opt/homebrew/bin', '/usr/local/bin'] if sys.platform != 'win32' else \
        [os.path.join(os.environ.get(k, ''), 'WinRAR') for k in ('ProgramFiles', 'ProgramFiles(x86)')]
    return _which(['unrar', 'UnRAR'], extra)


def _walk(paths):
    """产出 (磁盘路径, 包内路径)。"""
    for p in paths:
        p = os.path.abspath(p)
        base = os.path.dirname(p)
        if os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                if not files and not dirs:
                    yield root, os.path.relpath(root, base) + '/'
                for f in files:
                    full = os.path.join(root, f)
                    yield full, os.path.relpath(full, base)
        else:
            yield p, os.path.basename(p)


def default_archive_name(paths, fmt):
    p = os.path.abspath(paths[0])
    base = os.path.splitext(p)[0] if (len(paths) == 1 and os.path.isfile(p)) else p
    if len(paths) > 1:
        base = os.path.join(os.path.dirname(p), os.path.basename(os.path.dirname(p)) or '压缩包')
    return unique_path(base + '.' + fmt)


def compress(paths, fmt, password=None, out=None):
    out = out or default_archive_name(paths, fmt)
    password = password or None
    if fmt == 'zip':
        import pyzipper
        kw = dict(compression=pyzipper.ZIP_DEFLATED)
        if password:
            kw['encryption'] = pyzipper.WZ_AES
        with pyzipper.AESZipFile(out, 'w', **kw) as z:
            if password:
                z.setpassword(password.encode('utf-8'))
            for full, arc in _walk(paths):
                if arc.endswith('/'):
                    z.writestr(arc, b'')
                else:
                    z.write(full, arc)
    elif fmt == '7z':
        import py7zr
        with py7zr.SevenZipFile(out, 'w', password=password, header_encryption=bool(password)) as z:
            for p in paths:
                p = os.path.abspath(p)
                if os.path.isdir(p):
                    z.writeall(p, os.path.basename(p))
                else:
                    z.write(p, os.path.basename(p))
    elif fmt == 'rar':
        rar = find_rar()
        if not rar:
            raise ToolMissing('RAR 是专有格式,压缩成 rar 需要电脑上装有 WinRAR(或 rar 命令行)。'
                              '三虎没找到它——可以先装 WinRAR,或者改用 7z / zip(同样支持密码)。')
        cmd = [rar, 'a', '-ep1', '-r', '-idq', '-y']
        if password:
            cmd.append('-hp' + password)
        p = subprocess.run(cmd + [out] + [os.path.abspath(x) for x in paths], capture_output=True, **no_window_kwargs())
        if p.returncode != 0:
            raise RuntimeError('rar 压缩失败:' + (p.stderr or p.stdout).decode('utf-8', 'ignore')[-200:])
    else:
        raise RuntimeError('不支持的压缩格式:' + fmt)
    return out


def _safe_join(outdir, name):
    dest = os.path.normpath(os.path.join(outdir, name))
    if not (dest == outdir or dest.startswith(outdir + os.sep)):
        raise RuntimeError('压缩包里有可疑路径,已停止解压:' + name)
    return dest


def _fix_name(info):
    """Windows 上打的中文 zip 常是 GBK 文件名,这里纠正乱码。"""
    if info.flag_bits & 0x800:
        return info.filename
    try:
        return info.filename.encode('cp437').decode('gbk')
    except Exception:
        return info.filename


def _extract_zip(src, outdir, password):
    import pyzipper
    with pyzipper.AESZipFile(src) as z:
        infos = z.infolist()
        if any(i.flag_bits & 0x1 for i in infos):
            if not password:
                raise NeedPassword()
            z.setpassword(password.encode('utf-8'))
        for i in infos:
            name = _fix_name(i)
            dest = _safe_join(outdir, name)
            if name.endswith('/'):
                os.makedirs(dest, exist_ok=True)
                continue
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            try:
                with z.open(i) as r, open(dest, 'wb') as w:
                    shutil.copyfileobj(r, w)
            except RuntimeError as e:
                if 'password' in str(e).lower():
                    raise NeedPassword()
                raise


def _extract_7z(src, outdir, password):
    import py7zr
    try:
        with py7zr.SevenZipFile(src, 'r', password=password or None) as z:
            if z.needs_password() and not password:
                raise NeedPassword()
            z.extractall(outdir)
    except NeedPassword:
        raise
    except Exception as e:
        # 带了密码仍失败,基本就是密码不对;没带密码时按异常类型判断是否加密
        if password is not None or 'password' in str(e).lower() or e.__class__.__name__ in ('PasswordRequired', 'LZMAError'):
            raise NeedPassword()
        raise


def _extract_tool(src, outdir, password):
    seven, unrar = find_7z(), find_unrar()
    kw = no_window_kwargs()
    if seven:
        p = subprocess.run([seven, 'x', '-y', '-p' + (password or ''), '-o' + outdir, src], capture_output=True, **kw)
        txt = (p.stdout + p.stderr).decode('utf-8', 'ignore').lower()
        if p.returncode != 0:
            if 'password' in txt or 'encrypted' in txt:
                raise NeedPassword()
            if 'unsupported' not in txt and "can't open" not in txt and 'cannot open' not in txt or not unrar:
                raise RuntimeError('解压失败:' + txt[-200:])
        else:
            return
    if unrar:
        p = subprocess.run([unrar, 'x', '-y', '-p' + (password or '-'), src, outdir + os.sep], capture_output=True, **kw)
        txt = (p.stdout + p.stderr).decode('utf-8', 'ignore').lower()
        if p.returncode != 0:
            if 'password' in txt or 'encrypted' in txt:
                raise NeedPassword()
            raise RuntimeError('解压失败:' + txt[-200:])
        return
    tar = shutil.which('bsdtar') or shutil.which('tar')
    if tar and not password:
        p = subprocess.run([tar, '-xf', src, '-C', outdir], capture_output=True, **kw)
        if p.returncode == 0:
            return
        txt = p.stderr.decode('utf-8', 'ignore').lower()
        if 'encrypt' in txt or 'passphrase' in txt or 'password' in txt:
            raise ToolMissing('这个 rar 带密码,需要 7-Zip 或 unrar 才能解开。安装版的三虎已内置 7-Zip;'
                              '从源码运行时请先安装 7-Zip。')
    raise ToolMissing('解压 rar 需要 7-Zip 或 unrar。安装版的三虎已内置 7-Zip;从源码运行时请先安装 7-Zip。')


def extract(src, password=None, outdir=None):
    src = os.path.abspath(src)
    name = os.path.basename(src)
    for suf in ('.tar.gz', '.tar.bz2', '.tar.xz', '.tgz'):
        if name.lower().endswith(suf):
            stem = name[:-len(suf)]
            break
    else:
        stem = os.path.splitext(name)[0]
    created = outdir is None
    outdir = outdir or unique_path(os.path.join(os.path.dirname(src), stem))
    os.makedirs(outdir, exist_ok=True)
    low = name.lower()
    try:
        if low.endswith('.zip'):
            _extract_zip(src, outdir, password)
        elif low.endswith('.7z'):
            _extract_7z(src, outdir, password)
        elif low.endswith('.rar'):
            _extract_tool(src, outdir, password)
        else:
            shutil.unpack_archive(src, outdir)
    except Exception:
        if created:
            shutil.rmtree(outdir, ignore_errors=True)
        raise
    return outdir
