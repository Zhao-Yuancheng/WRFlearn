# -*- coding: utf-8 -*-
"""解包 AtmosphericPhysics\ppt 下所有 pptx（解包到同名 *_unpack 子目录），
并把每页幻灯片文本（含备注）抽取到 workspace\ppt_text\<标题>.md。
"""
import html
import os
import re
import zipfile

PPT_DIR = r"d:\Code\Learn\WRF\AtmosphericPhysics\ppt"
TEXT_DIR = r"d:\Code\Learn\WRF\workspace\ppt_text"
os.makedirs(TEXT_DIR, exist_ok=True)

TAG = re.compile(r"<a:t>(.*?)</a:t>", re.S)
SLIDE_NUM = re.compile(r"(?:slide|notesSlide)(\d+)\.xml$")


def slide_texts(xml_dir, prefix):
    """返回 [(编号, 文本列表)]，按编号排序。"""
    out = []
    if not os.path.isdir(xml_dir):
        return out
    for fn in os.listdir(xml_dir):
        m = SLIDE_NUM.search(fn)
        if not m or not fn.endswith(".xml"):
            continue
        with open(os.path.join(xml_dir, fn), encoding="utf-8") as f:
            xml = f.read()
        texts = [html.unescape(t).strip() for t in TAG.findall(xml)]
        texts = [t for t in texts if t]
        out.append((int(m.group(1)), texts))
    out.sort()
    return out


for name in sorted(os.listdir(PPT_DIR)):
    if not name.lower().endswith(".pptx"):
        continue
    stem = os.path.splitext(name)[0]
    src = os.path.join(PPT_DIR, name)
    dest = os.path.join(PPT_DIR, stem + "_unpack")

    if os.path.isdir(dest):
        print("exists, skip unpack: %s" % name)
    else:
        with zipfile.ZipFile(src) as z:
            z.extractall(dest)
        print("unpacked: %s" % name)

    slides = slide_texts(os.path.join(dest, "ppt", "slides"), "slide")
    notes = dict(slide_texts(os.path.join(dest, "ppt", "notesSlides"), "notesSlide"))

    lines = ["# %s" % name, ""]
    for num, texts in slides:
        lines.append("## slide %d" % num)
        for t in texts:
            lines.append("- " + t)
        if num in notes and notes[num]:
            lines.append("- [备注] " + " | ".join(notes[num]))
        lines.append("")

    md = os.path.join(TEXT_DIR, stem + ".md")
    with open(md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("text: %s.md slides=%d notes=%d" % (stem, len(slides), sum(1 for k in notes if notes.get(k))))

print("ALL DONE")
