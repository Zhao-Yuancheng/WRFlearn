# -*- coding: utf-8 -*-
"""从扫描版《大气物理学》PDF 提取每页图像（只读源文件，输出到新目录）。

策略：
- 每页若恰好 1 张覆盖页面且格式为 jpg/png/tif 的内嵌图，直接抽取原始字节（无损、不重编码）；
- 否则按 1.6x（约115dpi）渲染为 PNG。
manifest（pdf页码->文件）写入 workspace\book_manifest.csv；日志写入 workspace\logs\。
"""
import csv
import os
import time

try:
    import pymupdf as fitz  # PyMuPDF >= 1.26
except ImportError:
    import fitz  # PyMuPDF

PDF = (r"D:\WPSDisk\5336784\WPS云盘\__Jim__\2 Physics & Chemistry"
       r"\大气物理学 第2版 -- 盛裴轩,毛节泰,李建国等编著 -- 2013_09 -- 北京大学出版社"
       r" -- 13451009 -- ca8b49e1eb27af4c2bf5e7a5320415d5 -- Anna’s Archive.pdf")
OUT = r"d:\Code\Learn\WRF\AtmosphericPhysics\book"
MANIFEST = r"d:\Code\Learn\WRF\workspace\book_manifest.csv"
LOG = r"d:\Code\Learn\WRF\workspace\logs\extract_pdf_pages.log"

os.makedirs(OUT, exist_ok=True)
os.makedirs(os.path.dirname(LOG), exist_ok=True)


def log(msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


GOOD_EXT = {"jpg", "jpeg", "png", "tif", "tiff"}

doc = fitz.open(PDF)
n = doc.page_count
log("open ok pages=%d" % n)

# 检查是否存在文本层（扫描件通常为空，这决定后续能否全文检索）
sample_text = doc[10].get_text().strip()
log("page11 text-layer chars=%d sample=%r" % (len(sample_text), sample_text[:40]))

rows = []
nb_embed = nb_render = 0
t0 = time.time()
for i in range(n):
    page = doc[i]
    pno = i + 1
    try:
        imgs = page.get_images(full=True)
        pr = page.rect
        info = None
        if len(imgs) == 1:
            xref = imgs[0][0]
            base = doc.extract_image(xref)
            ext = base["ext"].lower()
            w, h = base["width"], base["height"]
            if ext in GOOD_EXT and w >= pr.width * 0.7:
                fname = "page_%04d.%s" % (pno, "jpg" if ext in ("jpg", "jpeg") else ext)
                with open(os.path.join(OUT, fname), "wb") as f:
                    f.write(base["image"])
                info = (fname, w, h, "embedded")
                nb_embed += 1
        if info is None:
            zoom = 1.6
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
            fname = "page_%04d.png" % pno
            pix.save(os.path.join(OUT, fname))
            info = (fname, pix.width, pix.height, "render")
            nb_render += 1
    except Exception as e:  # noqa: BLE001
        log("page %d ERROR %s: %s" % (pno, type(e).__name__, e))
        info = ("page_%04d.FAILED" % pno, 0, 0, "error")
    rows.append([pno, info[0], info[1], info[2], info[3]])
    if pno % 50 == 0:
        log("progress %d/%d embed=%d render=%d" % (pno, n, nb_embed, nb_render))

with open(MANIFEST, "w", newline="", encoding="utf-8-sig") as f:
    wtr = csv.writer(f)
    wtr.writerow(["pdf_page", "file", "width", "height", "mode"])
    wtr.writerows(rows)

doc.close()
total_mb = 0.0
for r in rows:
    if r[4] != "error":
        total_mb += os.path.getsize(os.path.join(OUT, r[1])) / 1e6
log("DONE pages=%d embed=%d render=%d total=%.1fMB elapsed=%.0fs"
    % (n, nb_embed, nb_render, total_mb, time.time() - t0))
print("DONE pages=%d embed=%d render=%d total=%.1fMB" % (n, nb_embed, nb_render, total_mb))
