import matplotlib.font_manager as fm
names = sorted(set(f.name for f in fm.fontManager.ttflist))
cands = [n for n in names if any(k in n for k in ("Hei", "YaHei", "Song", "Kai", "Fang"))]
print("candidate fonts:", cands[:30])
print("total:", len(names))
# 检查一个具体字体文件是否存在
import os
for p in [r"C:\Windows\Fonts\simhei.ttf", r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simsun.ttc"]:
    print(p, os.path.exists(p))