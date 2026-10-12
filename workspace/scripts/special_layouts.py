"""
对已 restyle 的 drawio 做结构级重排（在主 drawio 目录就地修改）：
- snake:  线性链分行（ch02 每行3个、ch08 每行4个），换行边从底部出、顶部入
- grid:   星形树分行（ch21_05：root 在顶，其余每行3个），边正交化
- rhombus: 菱形压扁（ch12_01 / ch13_01）
- compact: 容器贴合子节点 + 顶层容器紧凑竖排（ch18_01）

注意：edge label 单元（relative=1）一律跳过，不动。
"""
import pathlib, re
import xml.etree.ElementTree as ET
import subprocess, time

ROOT = pathlib.Path(r"d:\Code\Learn\WRF")
DIR = ROOT / "workspace" / "tmp" / "mermaid" / "drawio"
PNG = ROOT / "doc" / "figs" / "mermaid"
EXE = r"C:\Program Files\draw.io\draw.io.exe"

H_GAP, V_GAP, MARGIN = 40, 80, 40


def parse(stem):
    p = DIR / f"{stem}.drawio"
    tree = ET.parse(p)
    return p, tree, tree.getroot()


def cells_of(root):
    # UserObject 包装：内层 mxCell 常无 id，id 在 UserObject 上
    parent_map = {ch: par for par in root.iter() for ch in par}
    verts, edges = {}, {}
    for c in root.iter('mxCell'):
        st = c.get('style') or ''
        g = c.find('mxGeometry')
        cid = c.get('id')
        uo = parent_map.get(c)
        if cid is None and uo is not None and uo.tag == 'UserObject':
            cid = uo.get('id')
        if c.get('vertex') == '1':
            if 'edgeLabel' in st:
                continue
            if g is None or g.get('relative') == '1':
                continue
            try:
                v = dict(c=c, uo=uo if (uo is not None and uo.tag == 'UserObject') else None,
                         g=g, id=cid,
                         x=float(g.get('x', '0')), y=float(g.get('y', '0')),
                         w=float(g.get('width', '0')), h=float(g.get('height', '0')),
                         parent=c.get('parent', '1'))
            except (ValueError, TypeError):
                continue
            if cid is not None:
                verts[cid] = v
        elif c.get('edge') == '1':
            edges[cid] = dict(c=c, uo=uo if (uo is not None and uo.tag == 'UserObject') else None,
                              id=cid, src=c.get('source'), dst=c.get('target'), st=st)
    return verts, list(edges.values())


def setxy(v, x=None, y=None):
    if x is not None:
        v['g'].set('x', f"{x:.0f}"); v['x'] = x
    if y is not None:
        v['g'].set('y', f"{y:.0f}"); v['y'] = y


def _apply_style(e):
    e['c'].set('style', e['st'])
    if e.get('uo') is not None and e['uo'].get('style') is not None:
        e['uo'].set('style', e['st'])


def set_hint(e, hint):
    e['st'] = re.sub(r'(exitX|exitY|entryX|entryY)=[0-9.]+;?', '', e['st']) + hint
    _apply_style(e)


STRIP = "curved=1;strokeWidth=1.4;strokeColor=#555555;endArrow=classic;endFill=1;endSize=12;html=1;"
STRIP_ORTH = "strokeWidth=1.4;strokeColor=#555555;endArrow=classic;endFill=1;endSize=12;html=1;"

def clean_edge_style(e, orthogonal=False, hint=""):
    # orthogonal 时必须去掉 curved=1，否则曲线渲染压过 edgeStyle=orthogonalEdgeStyle
    e['st'] = (STRIP_ORTH if orthogonal else STRIP) + \
              ("edgeStyle=orthogonalEdgeStyle;rounded=0;" if orthogonal else "") + hint
    _apply_style(e)
    # 删除旧的绝对坐标点：sourcePoint/targetPoint/waypoints
    # （节点重排后这些点不更新会把导出包围盒撑到旧布局大小）
    if e['src'] and e['dst']:
        g = e['c'].find('mxGeometry')
        if g is not None:
            for pt in list(g.findall('mxPoint')):
                if pt.get('as') in ('sourcePoint', 'targetPoint'):
                    g.remove(pt)
            for arr in list(g.findall('Array')):
                if arr.get('as') == 'points':
                    g.remove(arr)


def save(p, tree):
    tree.write(p, encoding='utf-8', xml_declaration=True)


# ---------- snake：线性链分行 ----------
def snake(stem, per_row):
    p, tree, root = parse(stem)
    verts, edges = cells_of(root)
    order = sorted(verts.values(), key=lambda v: (round(v['y'] / 60), v['x']))
    rows = [order[i:i + per_row] for i in range(0, len(order), per_row)]
    row_of = {}
    y = MARGIN
    for ri, row in enumerate(rows):
        maxh = max(v['h'] for v in row)
        x = MARGIN
        for v in row:
            setxy(v, x=x, y=y + (maxh - v['h']) / 2)
            row_of[v['c'].get('id')] = ri
            x += v['w'] + H_GAP
        y += maxh + V_GAP
    for e in edges:
        if e['src'] in row_of and e['dst'] in row_of:
            rs, rd = row_of[e['src']], row_of[e['dst']]
            if rs == rd:
                clean_edge_style(e, hint="exitX=1;exitY=0.5;entryX=0;entryY=0.5;")
            elif rd == rs + 1:
                clean_edge_style(e, hint="exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
            else:
                clean_edge_style(e)
    save(p, tree)
    nrows = len(rows)
    row_w = max(sum(v['w'] for v in r) + H_GAP * (len(r) - 1) for r in rows)
    print(f"  {stem}: {len(order)} 节点 → {nrows} 行, 行宽≈{row_w:.0f}")


# ---------- grid：星形树分行 ----------
def grid_tree(stem, per_row=3):
    p, tree, root = parse(stem)
    verts, edges = cells_of(root)
    outdeg = {vid: 0 for vid in verts}
    for e in edges:
        if e['src'] in outdeg:
            outdeg[e['src']] += 1
    root_id = max(outdeg, key=outdeg.get)
    rootv = verts[root_id]
    others = sorted((v for k, v in verts.items() if k != root_id),
                    key=lambda v: (round(v['y'] / 60), v['x']))
    rows = [others[i:i + per_row] for i in range(0, len(others), per_row)]
    row_ws = [sum(v['w'] for v in r) + H_GAP * (len(r) - 1) for r in rows]
    gw = max(row_ws)
    setxy(rootv, x=MARGIN + (gw - rootv['w']) / 2, y=MARGIN)
    y = MARGIN + rootv['h'] + 90
    for ri, row in enumerate(rows):
        x = MARGIN + (gw - row_ws[ri]) / 2
        for v in row:
            setxy(v, x=x, y=y)
            x += v['w'] + H_GAP
        y += max(v['h'] for v in row) + V_GAP
    for e in edges:
        clean_edge_style(e, orthogonal=True)
    save(p, tree)
    print(f"  {stem}: root={root_id}, 其余 {len(others)} 节点 → {len(rows)} 行, 网格宽≈{gw:.0f}")


# ---------- rhombus 压扁 ----------
def flatten_rhombus(stem, wf=1.25, hf=0.60):
    p, tree, root = parse(stem)
    n = 0
    for c in root.iter('mxCell'):
        st = c.get('style') or ''
        if c.get('vertex') != '1' or 'rhombus' not in st or 'edgeLabel' in st:
            continue
        g = c.find('mxGeometry')
        if g is None or g.get('relative') == '1':
            continue
        w, h = float(g.get('width')), float(g.get('height'))
        nw, nh = w * wf, h * hf
        g.set('width', f"{nw:.0f}")
        g.set('height', f"{nh:.0f}")
        g.set('x', f"{float(g.get('x', '0')) + (w - nw) / 2:.0f}")
        g.set('y', f"{float(g.get('y', '0')) + (h - nh) / 2:.0f}")
        n += 1
        print(f"    rhombus: {w:.0f}x{h:.0f} → {nw:.0f}x{nh:.0f}")
    save(p, tree)
    print(f"  {stem}: 压扁 {n} 个菱形")


# ---------- compact：容器贴合 + 顶层紧凑 ----------
def compact_containers(stem, vgap=32, bottom_pad=20):
    p, tree, root = parse(stem)
    verts, edges = cells_of(root)
    kids = {}
    for v in verts.values():
        if v['parent'] in verts:
            kids.setdefault(v['parent'], []).append(v)
    # 容器高度贴合子节点（仅当能缩）
    for vid, ch in kids.items():
        c = verts[vid]
        maxyb = max(k['y'] + k['h'] for k in ch)
        newh = maxyb + bottom_pad
        if newh < c['h']:
            print(f"    container {vid}: h {c['h']:.0f} → {newh:.0f}")
            c['g'].set('height', f"{newh:.0f}")
            c['h'] = newh
    top = sorted((v for v in verts.values() if v['parent'] in ('0', '1')),
                 key=lambda v: v['y'])
    y = min(v['y'] for v in top) if top else MARGIN
    for v in top:
        setxy(v, y=y)
        y += v['h'] + vgap
    save(p, tree)
    print(f"  {stem}: 顶层 {len(top)} 个元素紧凑竖排, 总高≈{y - vgap:.0f}")


# ---------- rows_in_containers：容器内竖排链改横排 + 容器贴合 ----------
def rows_in_containers(stem, h_gap=30, pad_x=24, title_pad=64, bottom_pad=24):
    p, tree, root = parse(stem)
    verts, edges = cells_of(root)
    kids = {}
    for v in verts.values():
        if v['parent'] in verts:
            kids.setdefault(v['parent'], []).append(v)
    edge_by_pair = {(e['src'], e['dst']): e for e in edges}
    for cid, ch in kids.items():
        c = verts[cid]
        ch.sort(key=lambda v: (round(v['y'] / 60), v['x']))
        # 横排（子坐标相对父容器）
        x = pad_x
        row_h = max(v['h'] for v in ch)
        ids_row = set()
        for v in ch:
            setxy(v, x=x, y=title_pad + (row_h - v['h']) / 2)
            ids_row.add(v['id'])
            x += v['w'] + h_gap
        row_w = x - h_gap + pad_x
        # 容器贴合
        if row_w > c['w']:
            c['g'].set('width', f"{row_w:.0f}")
            c['w'] = row_w
        newh = title_pad + row_h + bottom_pad
        c['g'].set('height', f"{newh:.0f}")
        c['h'] = newh
        # 行内边 → 水平连接
        for e in edges:
            if e['src'] in ids_row and e['dst'] in ids_row:
                clean_edge_style(e, hint="exitX=1;exitY=0.5;entryX=0;entryY=0.5;")
        print(f"    container {cid}: 行宽={row_w:.0f}, 高={newh:.0f}, {len(ch)} 节点横排")
    # 顶层容器竖排紧凑
    top = sorted((v for v in verts.values() if v['parent'] in ('0', '1')),
                 key=lambda v: v['y'])
    y = min(v['y'] for v in top) if top else MARGIN
    for v in top:
        setxy(v, y=y)
        y += v['h'] + 40
    save(p, tree)
    print(f"  {stem}: 容器横排完成, 总高≈{y - 40:.0f}")


# ---------- fix_containers：容器样式修复（verticalAlign=top，标题不再叠节点） ----------
CONTAINER_TMPL = ("rounded=1;whiteSpace=wrap;html=1;strokeWidth=1.2;strokeColor={stroke};"
                  "fillColor={fill};dashed=1;dashPattern=6 6;"
                  "fontFamily=Helvetica,Arial,'Microsoft YaHei',sans-serif;"
                  "fontSize=20;fontColor=#333333;fontStyle=1;"
                  "shadow=0;spacingLeft=20;spacingRight=20;spacingTop=36;spacingBottom=20;"
                  "verticalAlign=top;align=left;")


def container_colors(label):
    l = label.lower()
    if 'wps' in l or '预处理' in label or 'preprocess' in l:
        return '#fdf4f4', '#e8a0a0'
    if any(k in label for k in ('运行', '积分', '时间')) or 'run' in l or 'time' in l:
        return '#eaf0f7', '#7a9fcc'
    if any(k in label for k in ('物理', 'phys')):
        return '#f5ebe0', '#c99566'
    if any(k in label for k in ('源码', '架构')) or 'framework' in l or 'structure' in l:
        return '#ede0f5', '#a780d1'
    if '链' in label or 'chain' in l:
        return '#eaf3ea', '#7aa87a'
    return '#f5f5f5', '#bbbbbb'


def fix_containers(stem):
    """有子节点的 vertex = 容器：重设容器样式（标题顶对齐）"""
    p, tree, root = parse(stem)
    verts, edges = cells_of(root)
    kids = {}
    for v in verts.values():
        if v['parent'] in verts:
            kids.setdefault(v['parent'], []).append(v)
    n = 0
    for cid in kids:
        c = verts[cid]
        uo = c.get('uo')
        label = ''
        if uo is not None:
            label = uo.get('label') or ''
        if not label:
            label = c['c'].get('value') or ''
        fill, stroke = container_colors(label)
        new_style = CONTAINER_TMPL.format(fill=fill, stroke=stroke)
        c['c'].set('style', new_style)
        if uo is not None and uo.get('style') is not None:
            uo.set('style', new_style)
        n += 1
    if n:
        save(p, tree)
    return n


if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    print("== snake 分行 ==")
    snake("ch02_wrf_evolution_01", per_row=3)
    snake("ch08_running_wrf_01", per_row=4)
    print("== grid 分行 ==")
    grid_tree("ch21_solve_em_dynamics_05", per_row=3)
    if mode == "all":
        print("== 菱形压扁 ==")
        flatten_rhombus("ch12_radiation_family_01")
        flatten_rhombus("ch13_microphysics_family_01")
    print("== ch18 容器内横排 ==")
    rows_in_containers("ch18_ideal_cases_01")

    print("\n== 容器样式修复（全部文件扫描）==")
    total = 0
    for f in sorted(DIR.glob('*.drawio')):
        n = fix_containers(f.stem)
        if n:
            print(f"  {f.stem}: {n} 个容器")
            total += n
    print(f"  共修复 {total} 个容器")

    # 全量重导 PNG（EDGE_BASE 字号变更影响所有图）
    print("\n== 重导全部 PNG ==")
    from PIL import Image
    ok = 0
    for drawio in sorted(DIR.glob('*.drawio')):
        png = PNG / f"{drawio.stem}.png"
        cmd = [EXE, "-x", "--timeout", "60", "-f", "png", "--border", "10",
               "--scale", "2", "-o", str(png), str(drawio)]
        subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        time.sleep(0.2)
        try:
            w, h = Image.open(png).size
            print(f"  {drawio.stem}: {w}x{h} ({png.stat().st_size // 1024}KB)")
            ok += 1
        except Exception:
            print(f"  {drawio.stem}: EXPORT FAIL")
    print(f"完成 {ok}/36")
