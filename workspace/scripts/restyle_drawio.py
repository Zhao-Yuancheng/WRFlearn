"""
批量美化 workspace/tmp/mermaid/drawio/*.drawio。
风格参考 FDS-UNeXT 架构图：
- 干净白背景、无网格
- 节点：圆角矩形 + 阴影 + Helvetica + 13pt + 灰色边框 1px + 内部 padding
- 容器/子图：虚线边框 + 淡色填充 + 大 padding + 顶对齐标题
- 连线：曲线 + 细 1.2px + 中灰 + 经典箭头
- Edge 标签：白底灰边的小胶囊 + 11pt

颜色分类（基于 label 关键词）：
  * 源码/.F/.exe → 白色填充 + 深蓝边框（工程感）
  * 物理参数化/radiation/microphysics/pbl/cumulus/surface → 橙色填充（醒目标记）
  * 容器/subgraph/group → 淡色填充 + 虚线边框
  * 其他普通节点 → 白色 + 深灰边框

使用：
  python restyle_drawio.py [--test N]   # N=代表图数量，默认全部 36
"""
import xml.etree.ElementTree as ET
import pathlib, re, sys, shutil, subprocess

ROOT = pathlib.Path(r"d:\Code\Learn\WRF")
DRAWIO_DIR = ROOT / "workspace" / "tmp" / "mermaid" / "drawio"
PNG_DIR = ROOT / "doc" / "figs" / "mermaid"
DRAWIO_EXE = r"C:\Program Files\draw.io\draw.io.exe"

# --- 基础样式常量 ---
# 字号策略：参考 FDS-UNeXT 架构图（核心节点 13-15pt，子标签 10-11pt）
# 教材 PNG 通常在 1500-3000px 宽，对应放大 2× 后字号要显著大
BASE_VERTEX = (
    "rounded=1;whiteSpace=wrap;html=1;strokeWidth=1;curved=1;"
    "fontFamily=Helvetica,Arial,'Microsoft YaHei',sans-serif;"
    "fontSize=18;fontColor=#222222;"
    "shadow=1;spacingLeft=12;spacingRight=12;spacingTop=8;spacingBottom=8;"
    "verticalAlign=middle;align=center;"
)
EDGE_BASE = (
    "curved=1;strokeWidth=1.4;strokeColor=#555555;"
    "endArrow=classic;endFill=1;endSize=12;startArrow=none;"
    "exitX=1;exitY=0.5;entryX=0;entryY=0.5;"
    # 边标签样式直接并入：本转换器把标签放在边 value 上（无独立 edgeLabel 单元）
    # 用户裁决（2026-10-12）：labelBorderColor 灰描边=灰框，禁用；白色 bg 保留遮线
    "html=1;fontSize=28;fontFamily=Helvetica,Arial,'Microsoft YaHei',sans-serif;"
    "fontColor=#555555;labelBackgroundColor=#ffffff;"
    "verticalAlign=middle;align=center;"
)
EDGE_LABEL = (
    "html=1;fontSize=28;fontFamily=Helvetica,Arial,'Microsoft YaHei',sans-serif;"
    "fontColor=#555555;labelBackgroundColor=#ffffff;"
    "rounded=1;strokeWidth=0;verticalAlign=middle;align=center;"
    "spacingLeft=8;spacingRight=8;spacingTop=4;spacingBottom=4;"
)

# 容器样式（虚线 + 淡色）
def container_style(fill="#fdf4f4", stroke="#e8a0a0"):
    return (
        f"rounded=1;whiteSpace=wrap;html=1;strokeWidth=1.2;strokeColor={stroke};"
        f"fillColor={fill};dashed=1;dashPattern=6 6;curved=1;"
        f"fontFamily=Helvetica,Arial,'Microsoft YaHei',sans-serif;"
        f"fontSize=20;fontColor=#333333;fontStyle=1;"
        f"shadow=0;spacingLeft=20;spacingRight=20;spacingTop=36;spacingBottom=20;"
        f"verticalAlign=top;align=left;"
    )

# 彩色节点样式（按类别）
# 设计原则：参考 FDS-UNeXT 架构图——节点用**浅色填充 + 中深边框**，白底白框=隐形
# 主色板（全部是淡色填充，边框饱和）：
#   源码/模块 → 淡青  #d4e8f5 / #4a7fa8
#   物理参数化 → 淡橙  #ffd9b3 / #cc6633
#   初始化/输入 → 淡蓝  #dbe8f5 / #3a6ea5
#   输出/诊断 → 淡绿  #d6ead6 / #4a8b4a
#   时间积分/RK → 淡紫  #ede0f5 / #7a4db3
#   边界/嵌套 → 淡粉  #f5d9d9 / #b85858
#   默认 → 米白  #f5f0e8 / #8a7a6a  （不再用纯白！）

def vertex_style_by_label(label):
    """根据节点文本选配色"""
    l = label.lower().replace("&#xa;", "\n")

    # 物理过程 / 关键节点 → 淡橙填充（醒目）
    orange_kw = ["radiation", "microphysics", "pbl", "cumulus", "shallowcu",
                 "surface", "boundary", "forcing", "fdda", "diagnostic",
                 "物理", "参数化", "辐射", "微物理", "边界层", "积云"]
    if any(k in l for k in orange_kw):
        return (BASE_VERTEX +
                "fillColor=#ffd9b3;strokeColor=#cc6633;")

    # 边界/嵌套 → 淡粉
    boundary_kw = ["bc", "boundary", "lbc", "nest", "relax", "spec_bdy", "halo",
                   "边界", "嵌套"]
    if any(k in l for k in boundary_kw):
        return (BASE_VERTEX +
                "fillColor=#f5d9d9;strokeColor=#b85858;")

    # 源码文件 → 淡青 + 青灰边框（不再白色！）
    source_kw = [".f", ".exe", "module_", "share/", "dyn_em/", "phys/",
                 "solve_em", "wrf.exe", "real.exe", "ideal.exe", "ndown.exe",
                 "geogrid", "ungrib", "metgrid"]
    if any(k in l for k in source_kw):
        return (BASE_VERTEX +
                "fillColor=#d4e8f5;strokeColor=#4a7fa8;strokeWidth=1.2;")

    # 初始化/输入 → 淡蓝
    init_kw = ["input", "init", "start", "begin", "read", "open", "初始化", "输入", "起"]
    if any(k in l for k in init_kw):
        return (BASE_VERTEX +
                "fillColor=#dbe8f5;strokeColor=#3a6ea5;")

    # 输出/诊断 → 淡绿
    out_kw = ["output", "write", "end", "finish", "diagnose", "wrfout", "out_", "输出", "结束"]
    if any(k in l for k in out_kw):
        return (BASE_VERTEX +
                "fillColor=#d6ead6;strokeColor=#4a8b4a;")

    # 时间积分/RK → 淡紫
    rk_kw = ["rk", "runge", "kutta", "small_step", "big_step", "advance", "rk_step",
             "time_step", "integrat", "trajectory"]
    if any(k in l for k in rk_kw):
        return (BASE_VERTEX +
                "fillColor=#ede0f5;strokeColor=#7a4db3;")

    # 诊断/中间产物 → 米黄
    diag_kw = ["med_", "mediation", "output_wrf", "input_wrf", "config", "statevar",
               "allocs", "deallocs"]
    if any(k in l for k in diag_kw):
        return (BASE_VERTEX +
                "fillColor=#f5ecd4;strokeColor=#b89a45;")

    # 默认：米白 + 深棕灰边框（保证白底不隐形）
    return (BASE_VERTEX + "fillColor=#f5f0e8;strokeColor=#8a7a6a;strokeWidth=1.2;")


def restyle_drawio(xml_text: str) -> str:
    """改写一个 .drawio 文件的样式"""
    # draw.io 用的是 mxfile 根节点
    # 我们用简单的正则 + 字符串替换比 ElementTree 更安全（draw.io XML 可能不严格）

    # 先把 light-dark(...) 表达式全部剥掉（我们不用暗黑模式）
    xml_text = re.sub(r'light-dark\([^)]+\)', '#ffffff', xml_text)
    xml_text = re.sub(r'light-dark\([^)]+\)', '#333333', xml_text)

    # 改写 gridModel 的全局属性：grid=0（关网格）, 页面背景白
    xml_text = re.sub(
        r'<mxGraphModel([^>]*)>',
        lambda m: '<mxGraphModel' + m.group(1).replace('grid="1"', 'grid="0"') + ' background="#ffffff">',
        xml_text
    )
    # 兜底：如果没有 background 加上
    if 'background=' not in xml_text[:500]:
        xml_text = xml_text.replace(
            '<mxGraphModel',
            '<mxGraphModel background="#ffffff"',
            1
        )

    # 逐个 mxCell 重写 style
    # draw.io 里每个 UserObject 下有一对 style 属性（UserObject 的和内部 mxCell 的），
    # 两处都要改才生效

    # 先把所有 mxCell 拿出来处理
    cells = list(re.finditer(r'<mxCell\b([^>]*)>', xml_text))
    # 倒序替换以免索引变化
    for m in reversed(cells):
        attrs_str = m.group(1)
        new_attrs = rewrite_cell_attrs(attrs_str)
        if new_attrs != attrs_str:
            xml_text = xml_text[:m.start()] + '<mxCell' + new_attrs + '>' + xml_text[m.end():]

    # 关键：draw.io 渲染优先读 UserObject 的 style 属性（内层 mxCell 的会被覆盖），
    # 把内层改好的 style 同步到 UserObject 上
    def sync_uo(m):
        uo_attrs, inner_attrs = m.group(1), m.group(2)
        sm = re.search(r' style="([^"]*)"', inner_attrs)
        if not sm:
            return m.group(0)
        inner_style = sm.group(1)
        if ' style="' in uo_attrs:
            uo_attrs = re.sub(r' style="[^"]*"', ' style="' + inner_style + '"', uo_attrs, count=1)
        else:
            uo_attrs = uo_attrs + ' style="' + inner_style + '"'
        return '<UserObject' + uo_attrs + '><mxCell' + inner_attrs + '>'

    xml_text = re.sub(r'<UserObject([^>]*)>\s*<mxCell([^>]*)>', sync_uo, xml_text)

    return xml_text


def rewrite_cell_attrs(attrs_str: str) -> str:
    """重写单个 mxCell 的属性字符串"""
    is_vertex = 'vertex="1"' in attrs_str
    is_edge = 'edge="1"' in attrs_str
    has_style = ' style="' in attrs_str

    if not has_style:
        return attrs_str

    # 提取 style 值
    sm = re.search(r' style="([^"]*)"', attrs_str)
    if not sm:
        return attrs_str

    old_style = sm.group(1)

    # edge label 单元（edgeLabel 样式、relative geometry）单独处理，
    # 不能走普通 vertex 分支（否则会被换成节点样式导致标签丢失）
    if 'edgeLabel' in old_style:
        new_style = 'edgeLabel;' + EDGE_LABEL
        return attrs_str.replace(' style="' + old_style + '"', ' style="' + new_style + '"')

    new_style = compute_new_style(attrs_str, old_style, is_vertex, is_edge)

    return attrs_str.replace(' style="' + old_style + '"', ' style="' + new_style + '"')


# draw.io 形状关键字（从 old_style 提取保留）
SHAPE_KEYWORDS = [
    "rhombus", "ellipse", "circle", "cylinder", "hexagon", "triangle",
    "parallelogram", "trapezoid", "cloud", "document", "process",
    "suitcase", "box", "note", "callout", "internalStorage", "partialRectangle",
    "line", "arrow", "diamond", "rect=1", "rounded=1",
    "shape=", "exitX=", "exitY=", "entryX=", "entryY=",
]

def extract_shape_props(old_style: str) -> str:
    """从旧 style 里抽取必须保留的形状属性"""
    kept = []
    # 精确匹配形状关键字（独立 token）
    tokens = old_style.split(";")
    for tok in tokens:
        t = tok.strip()
        if not t:
            continue
        # 保留形状类关键字
        if any(t.startswith(kw) for kw in SHAPE_KEYWORDS
               if not kw.endswith("=")):
            kept.append(t)
        elif "shape=" in t or "rhombus" in t or "ellipse" in t or "cylinder" in t:
            kept.append(t)
    # 去掉重复的 rounded=1（我们会自己加）
    kept = [t for t in kept if t != "rounded=1"]
    return ";".join(kept) + (";" if kept else "")


def compute_new_style(attrs_str, old_style, is_vertex, is_edge):
    """根据类型选新样式"""
    # 判断是否容器/子图（大尺寸节点，或有 mermaidId 以 "n:" 开头但 label 是容器名）
    # 更简单的：看是否有 "mermaidBaseValue" 里包含子图标记，或者看 mxGeometry 尺寸
    shape_prefix = extract_shape_props(old_style)

    # mermaid 里 subgraph 也是 vertex，但 parent 指向 1（根），且有子节点
    # 这里简化：如果 parent="1" 且 vertex，且 label 包含 "家族"/"结构"/"流程"/"管道"/"子图" → 容器
    label_match = re.search(r'label="([^"]*)"', attrs_str)
    label = label_match.group(1) if label_match else ""

    if is_edge:
        # 判断 edge 是否有 label
        has_label = bool(label)
        if has_label:
            new = EDGE_BASE + EDGE_LABEL
        else:
            new = EDGE_BASE
        # 保留原有的 exit/entry 方向（可能 mermaid 自动算的更准）
        # 但我们已经写死 exitX=1;exitY=0.5;entryX=0;entryY=0.5，这对大多数情况够用
        # 如果原来有更精确的方向，就用原来的 exitX/Y entryX/Y
        for key in ['exitX', 'exitY', 'entryX', 'entryY']:
            km = re.search(rf'{key}=([0-9.]+)', old_style)
            if km:
                new = re.sub(rf'{key}=[0-9.]+', f'{key}={km.group(1)}', new)
        return new

    if is_vertex:
        # 判断是否容器/子图
        container_kw = ['家族', '结构', '流程', '管道', '子图', '架构',
                        'framework', 'structure', 'pipeline', 'wps']
        # 更关键的判断：parent="1" + geometry 面积大（mermaid subgraph）
        gm = re.search(r'<mxGeometry[^>]*width="([^"]*)"[^>]*height="([^"]*)"',
                       attrs_str + old_style)
        is_big = False
        if gm:
            try:
                w = float(gm.group(1).replace('"', ''))
                h = float(gm.group(2).replace('"', ''))
                is_big = w > 200 and h > 150  # mermaid subgraph 一般比普通节点大
            except ValueError:
                pass

        parent_root = 'parent="1"' in attrs_str
        looks_like_container = is_big and parent_root

        if looks_like_container:
            # 根据 label 选容器颜色
            label_lower = label.lower()
            if 'wps' in label_lower or '预处理' in label or 'preprocess' in label_lower:
                fill, stroke = '#fdf4f4', '#e8a0a0'  # 浅粉
            elif '运行' in label or 'run' in label_lower or '积分' in label or '时间' in label:
                fill, stroke = '#eaf0f7', '#7a9fcc'  # 浅蓝
            elif '物理' in label or 'phys' in label_lower or 'physics' in label_lower:
                fill, stroke = '#f5ebe0', '#c99566'  # 浅棕
            elif '源码' in label or '架构' in label or 'framework' in label_lower or 'structure' in label_lower:
                fill, stroke = '#ede0f5', '#a780d1'  # 浅紫
            else:
                fill, stroke = '#f5f5f5', '#bbbbbb'  # 默认浅灰
            return shape_prefix + container_style(fill, stroke)

        # 普通节点：拼 shape_prefix 保留原形状
        return shape_prefix + vertex_style_by_label(label)

    # 其他（id="0" 或 id="1" 的根节点）不动
    return old_style


def process_file(drawio_path: pathlib.Path, out_dir: pathlib.Path):
    """处理单个 .drawio → 重写样式 → 保存"""
    text = drawio_path.read_text(encoding="utf-8")
    new_text = restyle_drawio(text)
    out_path = out_dir / drawio_path.name
    out_path.write_text(new_text, encoding="utf-8")
    return out_path


def export_png(drawio_path: pathlib.Path, png_path: pathlib.Path,
               scale: int = 2, max_width: int = 4000):
    """用 draw.io CLI 导出 PNG。
    只用 --scale 等比导出。实测 --width 与 --scale 同传（或 --width 单传且内容
    宽×scale 未达上限时）会触发 CLI 非等比 bug：画布虚高、底部内容截断
    （例：445x1277 逻辑图输出 4000x8135，内容仅渲染 73%）。
    max_width 参数保留仅为兼容旧调用，已不传入 CLI。"""
    cmd = [DRAWIO_EXE, "-x", "--timeout", "60", "-f", "png",
           "--border", "10",
           "--scale", str(scale),
           "-o", str(png_path), str(drawio_path)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return png_path.exists() and png_path.stat().st_size > 500


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", type=int, default=0,
                    help="只处理前 N 个文件测试；0=全部")
    ap.add_argument("--overwrite", action="store_true",
                    help="直接覆盖原 drawio 文件；否则写 restyled/ 子目录")
    args = ap.parse_args()

    out_dir = DRAWIO_DIR if args.overwrite else DRAWIO_DIR / "restyled"
    out_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(DRAWIO_DIR.glob("*.drawio"))
    # 跳过 restyled 子目录里的（仅当非 overwrite 时）
    if not args.overwrite:
        files = [f for f in files if f.parent != out_dir]

    if args.test > 0:
        files = files[:args.test]

    print(f"处理 {len(files)} 个 .drawio → {out_dir}")
    print("-" * 60)

    ok = fail = 0
    for i, f in enumerate(files):
        try:
            out = process_file(f, out_dir)
            png_out = PNG_DIR / f"{out.stem}.png"
            png_ok = export_png(out, png_out)
            status = "✓" if png_ok else "✗ PNG_FAIL"
            sz = out.stat().st_size
            print(f"[{i+1}/{len(files)}] {f.stem}: {status}  (xml={sz}B)")
            if png_ok:
                ok += 1
            else:
                fail += 1
        except Exception as e:
            print(f"[{i+1}/{len(files)}] {f.stem}: ERROR {e}")
            fail += 1

    print("-" * 60)
    print(f"完成：成功 {ok}，失败 {fail}")
    print(f"样式化 drawio 源：{out_dir}")
    print(f"PNG 输出：{PNG_DIR}")


if __name__ == "__main__":
    main()
