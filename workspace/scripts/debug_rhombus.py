"""Debug rhombus preservation."""
import sys, pathlib, re
sys.path.insert(0, r'd:\Code\Learn\WRF\workspace\scripts')
from restyle_drawio import process_file, extract_shape_props

src = pathlib.Path(r'd:\Code\Learn\WRF\workspace\tmp\mermaid\drawio\ch01_from_atmosphere_to_models_01.drawio')
out_dir = pathlib.Path(r'd:\Code\Learn\WRF\workspace\tmp\mermaid\drawio\testbatch\restyled2')
out_dir.mkdir(exist_ok=True)
out = process_file(src, out_dir)
print(f"Processed: {out}")

text = out.read_text(encoding='utf-8')

# 找到原始 style 里有 rhombus 的 mxCell
# 从原始文件看：mermaidBaseStyle="rhombus;..." 然后嵌套 mxCell 的 style 也以 rhombus; 开头
# 检查 restyled 里 id=5 附近的 mxCell style
# draw.io XML 里 UserObject 包 mxCell
# 搜索 rhombus
rhombus_count = text.count('rhombus')
print(f"Total 'rhombus' occurrences: {rhombus_count}")

# 搜索 vertex mxCell style
vertex_styles = re.findall(r'<mxCell\b[^>]*vertex="1"[^>]*style="([^"]+)"', text)
print(f"\nVertex count: {len(vertex_styles)}")
for i, s in enumerate(vertex_styles):
    has_rhombus = 'rhombus' in s
    has_rounded = 'rounded=1' in s
    print(f"  vertex[{i}]: rhombus={'YES' if has_rhombus else 'no'}, style_head={s[:80]}")

# 直接测试 extract_shape_props
old = "rhombus;html=1;strokeWidth=1;whiteSpace=wrap;fillColor=#ECECFF;strokeColor=#9370DB"
result = extract_shape_props(old)
print(f"\nextract_shape_props('{old[:60]}...') = '{result}'")
