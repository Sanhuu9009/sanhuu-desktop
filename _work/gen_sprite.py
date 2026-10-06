#!/usr/bin/env python3
"""生成 SPRITE_DATA JS 代码段（base64 数组）"""
import base64, glob, json

data = {}
for st in ["idle", "walk", "happy", "rain", "jump"]:
    files = sorted(glob.glob(f"assets/anim/{st}/*.png"))
    data[st] = [base64.b64encode(open(f, "rb").read()).decode() for f in files]
    print(st, len(files), "帧")

lines = ["const SPRITE_DATA={"]
for st, arr in data.items():
    lines.append(f"  {st}:[")
    for b in arr:
        lines.append('    "' + b + '",')
    lines.append("  ],")
lines.append("};")
open("_work/sprite_data.js", "w").write("\n".join(lines))
print("sprite_data.js 已生成，大小", len("\n".join(lines)), "字符")
