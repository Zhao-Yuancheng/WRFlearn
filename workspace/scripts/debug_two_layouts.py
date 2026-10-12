import xml.etree.ElementTree as ET, pathlib

DIR = pathlib.Path(r'd:\Code\Learn\WRF\workspace\tmp\mermaid\drawio')

for stem in ['ch21_solve_em_dynamics_05', 'ch18_ideal_cases_01']:
    print('=' * 60)
    print(stem)
    root = ET.parse(DIR / f'{stem}.drawio').getroot()
    pmap = {ch: par for par in root.iter() for ch in par}
    for c in root.iter('mxCell'):
        st = c.get('style') or ''
        g = c.find('mxGeometry')
        if g is None:
            continue
        cid = c.get('id')
        uo = pmap.get(c)
        if cid is None and uo is not None and uo.tag == 'UserObject':
            cid = uo.get('id')
        rel = g.get('relative') == '1'
        try:
            x = float(g.get('x', '0')); y = float(g.get('y', '0'))
            w = float(g.get('width', '0')); h = float(g.get('height', '0'))
        except (ValueError, TypeError):
            x = y = w = h = -1
        kind = 'V' if c.get('vertex') == '1' else ('E' if c.get('edge') == '1' else '?')
        lbl = ''
        if uo is not None and uo.tag == 'UserObject':
            lbl = (uo.get('label') or '')[:25].replace('\n', ' ')
        par = c.get('parent', '')
        print(f'  {kind} id={str(cid)[:12]:<12} par={str(par)[:12]:<12} rel={rel} x={x:>7.1f} y={y:>7.1f} w={w:>6.1f} h={h:>6.1f} "{lbl}"')
