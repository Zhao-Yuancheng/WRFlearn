"""诊断 ch06 和 ch21_05 的 subgraph/container cell"""
import pathlib, xml.etree.ElementTree as ET

for stem in ["ch06_wps_pipeline_01", "ch21_solve_em_dynamics_05"]:
    print(f"\n{'='*60}")
    print(f"{stem}")
    print(f"{'='*60}")
    drawio = pathlib.Path(r"d:\Code\Learn\WRF\workspace\tmp\mermaid\drawio") / f"{stem}.drawio"
    text = drawio.read_text(encoding="utf-8")
    root = ET.fromstring(text)
    
    # 收集所有 mxCell（不限 vertex），看 subgraph/container
    for cell in root.iter('mxCell'):
        style = cell.get('style', '') or ''
        geom = cell.find('mxGeometry')
        is_group = cell.get('group') == '1'
        value = (cell.get('value', '') or '')[:60]
        id_ = cell.get('id', '')
        parent = cell.get('parent', '')
        
        if geom is not None:
            try:
                x = float(geom.get('x', '0'))
                y = float(geom.get('y', '0'))
                w = float(geom.get('width', '0'))
                h = float(geom.get('height', '0'))
            except:
                x=y=w=h=0
        else:
            x=y=w=h=0
        
        # subgraph / container 特征：style 含 group / container / shape
        is_container = any(k in style for k in ['container', 'shape=rect', 'swimlane', 'group=1'])
        # 或者是 mermaid subgraph 的样式
        is_mermaid_subgraph = 'swimlane' in style or 'startSize' in style
        
        if is_container or is_mermaid_subgraph or is_group or 'subgraph' in value.lower() or 'input' in value.lower() or 'wps' in value.lower():
            print(f"  id={id_:<4} parent={parent:<4} vertex={cell.get('vertex')} group={is_group}")
            print(f"    x={x:.0f} y={y:.0f} w={w:.0f} h={h:.0f}")
            print(f"    style={style[:100]}")
            print(f"    value=\"{value}\"")
