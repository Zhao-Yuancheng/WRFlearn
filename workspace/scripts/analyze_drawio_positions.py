"""解析 drawio XML 的节点 x/y/width，打印位置分布"""
import pathlib, re, xml.etree.ElementTree as ET

def analyze(drawio_path):
    tree = ET.parse(drawio_path)
    root = tree.getroot()
    ns = {'mx': 'http://www.w3.org/1999/xhtml'}
    
    nodes = []
    for cell in root.iter('mxCell'):
        is_vertex = cell.get('vertex') == '1'
        is_edge = cell.get('edge') == '1'
        geom = cell.find('mxGeometry')
        if geom is None:
            continue
        try:
            x = float(geom.get('x', '0'))
            y = float(geom.get('y', '0'))
            w = float(geom.get('width', '0'))
            h = float(geom.get('height', '0'))
        except:
            continue
        
        val = cell.get('value', '') or ''
        val = val.replace('&#xa;', ' ').replace('<br/>', ' ')[:50]
        
        if is_vertex:
            nodes.append({
                'id': cell.get('id', ''),
                'value': val,
                'x': x, 'y': y, 'w': w, 'h': h,
                'cx': x + w/2,
                'cy': y + h/2,
            })
    
    xs = [n['x'] for n in nodes]
    xmax = max(n['x'] + n['w'] for n in nodes)
    ys = [n['y'] for n in nodes]
    ymax = max(n['y'] + n['h'] for n in nodes)
    
    # 横向分桶：按 cx 分 5 列看节点分布
    if nodes:
        span = xmax - min(xs)
        ncols = 5
        buckets = [[] for _ in range(ncols)]
        for n in nodes:
            col = min(int((n['cx'] - min(xs)) / span * ncols), ncols - 1) if span > 0 else 0
            buckets[col].append(n)
        
        col_widths = []
        for b in buckets:
            if b:
                col_x = min(n['x'] for n in b)
                col_right = max(n['x'] + n['w'] for n in b)
                col_widths.append(col_right - col_x)
            else:
                col_widths.append(0)
    
    return {
        'n_nodes': len(nodes),
        'x_span': xmax - min(xs) if xs else 0,
        'y_span': ymax - min(ys) if ys else 0,
        'node_w_max': max((n['w'] for n in nodes), default=0),
        'node_w_min': min((n['w'] for n in nodes), default=0),
        'nodes': nodes,
    }

OVERSIZE = [
    "ch02_wrf_evolution_01", "ch03_architecture_overview_02",
    "ch04_registry_mechanism_02", "ch06_wps_pipeline_01",
    "ch08_running_wrf_01", "ch15_cumulus_family_02",
    "ch17_urban_canopy_01", "ch17_urban_canopy_02",
    "ch21_solve_em_dynamics_05",
]

DRAWIO = pathlib.Path(r"d:\Code\Learn\WRF\workspace\tmp\mermaid\drawio")

for stem in OVERSIZE:
    d = analyze(DRAWIO / f"{stem}.drawio")
    print(f"\n{'='*60}")
    print(f"{stem}: {d['n_nodes']} 节点, x跨={d['x_span']:.0f}px, y跨={d['y_span']:.0f}px")
    print(f"  节点宽: min={d['node_w_min']:.0f}  max={d['node_w_max']:.0f}")
    # 前 5 个节点位置
    for n in sorted(d['nodes'], key=lambda x: x['x'])[:5]:
        print(f"    id={n['id'][:3]:>3} x={n['x']:>6.0f} w={n['w']:>5.0f} \"{n['value'][:40]}\"")
    if len(d['nodes']) > 5:
        last = sorted(d['nodes'], key=lambda x: x['x'])[-1]
        print(f"    ...")
        print(f"    id={last['id'][:3]:>3} x={last['x']:>6.0f} w={last['w']:>5.0f} \"{last['value'][:40]}\"")
