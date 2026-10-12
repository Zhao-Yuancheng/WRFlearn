import xml.etree.ElementTree as ET, pathlib
p = pathlib.Path(r'd:\Code\Learn\WRF\workspace\tmp\mermaid\drawio\ch02_wrf_evolution_01.drawio')
text = p.read_text(encoding='utf-8')
print('file size:', len(text))
print('raw <mxCell count:', text.count('<mxCell'))
print('raw vertex="1" count:', text.count('vertex="1"'))
root = ET.fromstring(text)
print('root tag:', root.tag)
all_cells = list(root.iter('mxCell'))
print('iter mxCell:', len(all_cells))
for c in all_cells[:6]:
    g = c.find('mxGeometry')
    print('  id=%s vertex=%s edge=%s geom=%s parent=%s' % (
        c.get('id'), c.get('vertex'), c.get('edge'), g is not None, c.get('parent')))
# 找 UserObject
uos = list(root.iter('UserObject'))
print('UserObject count:', len(uos))
if uos:
    u = uos[0]
    inner = u.find('mxCell')
    print('  first UO: label=%s id=%s, inner mxCell vertex=%s geom=%s' % (
        (u.get('label') or '')[:30], u.get('id'),
        inner.get('vertex') if inner is not None else None,
        inner is not None and inner.find('mxGeometry') is not None))
