"""
Drawio 布局收敛器：把超宽图的节点重新排布，使 drawio 内部 x 跨度 ≤ target_drawio_width
（这样 --scale 2 后 PNG ≤ target_png_width）。

算法：
1. 解析 mxCell（vertex + edge），用 id → cell 的 dict
2. 用聚类把 vertex 按 y 分成 layer（y 差 < LAYER_GAP 视为同层）
3. 每层内按 x 排序，紧凑排列（固定间距 H_GAP）
4. 层与层之间留 V_GAP
5. 所有 mxGeometry 的 x/y 更新；edge 的 geometry 通常只有 width/height，
   draw.io 渲染器会自动根据 source/target 节点重新连线，无需手调
6. 可选：pageWidth/pageHeight 也更新

用法：
  python tighten_drawio.py [--dir PATH] [--target-png-width 3500] [--scale 2] [--overwrite]
"""
import pathlib, re, argparse, xml.etree.ElementTree as ET
from copy import deepcopy

# 常量
LAYER_GAP = 80       # y 差 < 此值视为同层
H_GAP = 30           # 同层节点间水平间距
V_GAP = 60           # 层间垂直间距
MARGIN_X = 40        # 画布左右留白
MARGIN_Y = 40        # 画布上下留白

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--dir", default=r"d:\Code\Learn\WRF\workspace\tmp\mermaid\drawio")
    p.add_argument("--target-png-width", type=int, default=3500)
    p.add_argument("--scale", type=int, default=2)
    p.add_argument("--overwrite", action="store_true")
    p.add_argument("--only", nargs="*", help="只处理指定 stem (不含 .drawio)")
    return p.parse_args()

def get_geometry(cell):
    g = cell.find('mxGeometry')
    if g is None:
        return None
    try:
        return {
            'x': float(g.get('x', '0')),
            'y': float(g.get('y', '0')),
            'w': float(g.get('width', '0')),
            'h': float(g.get('height', '0')),
            'elem': g,
        }
    except:
        return None

def set_geometry(g, x=None, y=None):
    if x is not None:
        g['elem'].set('x', str(x))
        g['x'] = x
    if y is not None:
        g['elem'].set('y', str(y))
        g['y'] = y

def cluster_layers(nodes, gap=LAYER_GAP):
    """按 y 坐标聚类分 layer"""
    if not nodes:
        return []
    sorted_nodes = sorted(nodes, key=lambda n: n['y'])
    layers = [[sorted_nodes[0]]]
    for n in sorted_nodes[1:]:
        last = layers[-1][-1]
        if abs(n['y'] - last['y']) <= gap:
            layers[-1].append(n)
        else:
            layers.append([n])
    return layers

def tighten(drawio_path, target_drawio_width):
    """压缩单张 drawio"""
    text = drawio_path.read_text(encoding="utf-8")
    root = ET.fromstring(text)
    
    # 收集所有 vertex
    nodes = []
    for cell in root.iter('mxCell'):
        if cell.get('vertex') != '1':
            continue
        g = get_geometry(cell)
        if g is None:
            continue
        g['cell'] = cell
        nodes.append(g)
    
    if not nodes:
        return False, 0, 0, "no vertices"
    
    # 分 layer
    layers = cluster_layers(nodes)
    
    # 每层内紧凑排列（按 x 排序）
    # 先不整体压缩，只做层内紧凑化——这样能保证语义顺序不变
    # 然后检查总跨度，如果还超 target，再整体按比例缩
    
    for layer in layers:
        layer.sort(key=lambda n: n['x'])
        x = MARGIN_X
        for n in layer:
            set_geometry(n, x=x)
            x += n['w'] + H_GAP
    
    # 层间垂直排列
    y = MARGIN_Y
    for layer in layers:
        max_h = max(n['h'] for n in layer)
        for n in layer:
            set_geometry(n, y=y)
        y += max_h + V_GAP
    
    # 计算当前总跨度
    if nodes:
        cur_x_max = max(n['x'] + n['w'] for n in nodes)
        cur_y_max = max(n['y'] + n['h'] for n in nodes)
    else:
        cur_x_max = cur_y_max = 0
    
    # 如果还是超 target_drawio_width，等比压缩所有 x（只压水平，不动 y）
    scale_x = 1.0
    if cur_x_max > target_drawio_width:
        scale_x = target_drawio_width / cur_x_max
        for n in nodes:
            new_x = n['x'] * scale_x
            new_w = n['w'] * scale_x
            set_geometry(n, x=new_x)
            n['elem'].set('width', str(new_w))
    
    # 更新 pageWidth/pageHeight
    new_x_max = max(n['x'] + n['w'] for n in nodes)
    new_y_max = max(n['y'] + n['h'] for n in nodes)
    
    for mgm in root.iter('mxGraphModel'):
        old_page_w = mgm.get('pageWidth')
        old_page_h = mgm.get('pageHeight')
        if old_page_w:
            # pageWidth 可能是固定值 827（A4），改成 auto
            # 但 draw.io 如果 pageWidth 设置固定值会裁剪内容
            # 用足够大的值防止裁剪
            mgm.set('pageWidth', str(int(new_x_max) + MARGIN_X))
            mgm.set('pageHeight', str(int(new_y_max) + MARGIN_Y))
            # page 不要固定尺寸，让内容决定
            mgm.set('page', '0')  # page=0 表示不显示分页
    
    new_text = ET.tostring(root, encoding="unicode", xml_declaration=True)
    
    # 统计
    orig_span = 0
    try:
        orig_root = ET.fromstring(text)
        for cell in orig_root.iter('mxCell'):
            if cell.get('vertex') == '1':
                g = cell.find('mxGeometry')
                if g is not None:
                    x = float(g.get('x', 0))
                    w = float(g.get('width', 0))
                    orig_span = max(orig_span, x + w)
    except:
        pass
    
    new_span = max(n['x'] + n['w'] for n in nodes)
    
    return True, orig_span, new_span, new_text

def main():
    args = parse_args()
    drawio_dir = pathlib.Path(args.dir)
    target_drawio_w = args.target_png_width // args.scale
    
    print(f"目标：PNG ≤ {args.target_png_width}px → drawio 内部 ≤ {target_drawio_w}px")
    print(f"LAYER_GAP={LAYER_GAP}, H_GAP={H_GAP}, V_GAP={V_GAP}\n")
    
    files = sorted(drawio_dir.glob("*.drawio"))
    if args.only:
        only_set = set(args.only)
        files = [f for f in files if f.stem in only_set]
    
    results = []
    for f in files:
        ok, orig, new, info = tighten(f, target_drawio_w)
        if ok:
            if args.overwrite:
                f.write_text(info, encoding="utf-8")
            # 预估 PNG 宽
            est_png = int(new * args.scale)
            status = "✓" if est_png <= args.target_png_width else "⚠"
            print(f"{status} {f.stem:<48} drawio: {orig:>6.0f} → {new:>6.0f}  (预估 PNG: {est_png}px)")
        else:
            print(f"✗ {f.stem:<48} {info}")
        results.append((f.stem, ok, orig, new))
    
    # 汇总
    print(f"\n{'='*60}")
    oversize_after = [(s, o, n) for s, ok, o, n in results if ok and n * args.scale > args.target_png_width]
    print(f"处理后仍超宽：{len(oversize_after)} 张")
    for s, o, n in oversize_after:
        print(f"  {s}: drawio={n:.0f}, PNG预估={int(n*args.scale)}")

if __name__ == "__main__":
    main()
