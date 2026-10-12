#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fp_files.py — 打印 WRF 源文件的 md5/行数指纹表（文库篇首"版本指纹"节用）。
用法: fp_files.py <相对WRFV4.8.0根的路径> [<路径>...]
"""
import hashlib
import sys
from pathlib import Path

SRC = Path(r"D:\Code\Learn\WRF\source\WRFv4.8.0\WRFV4.8.0")

for rel in sys.argv[1:]:
    p = SRC / rel
    data = p.read_bytes()
    lines = data.decode("latin-1").split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    md5 = hashlib.md5(b"\n".join(ln.encode("latin-1") for ln in lines) + b"\n").hexdigest()
    print(f"{rel}  |  {len(lines)}  |  {md5}")
