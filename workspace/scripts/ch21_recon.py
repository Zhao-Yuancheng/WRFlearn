# -*- coding: utf-8 -*-
"""ch21 侦察：抽取 solve_em.F 与动力内核文件的调用结构。输出到 workspace/tmp/。"""
import re
import io
import os

ROOT = r'd:/Code/Learn/WRF/source/WRFv4.8.0/WRFV4.8.0'
OUT = r'd:/Code/Learn/WRF/workspace/tmp'
os.makedirs(OUT, exist_ok=True)


def extract_calls(fname, maxline=None):
    """返回 (行号, 语句) 列表：CALL 语句 + 主 DO/ENDDO 标记。"""
    path = os.path.join(ROOT, fname)
    res = []
    with io.open(path, encoding='utf-8', errors='replace') as f:
        for i, l in enumerate(f, 1):
            if maxline and i > maxline:
                break
            s = l.strip()
            s = s.split('!')[0].strip() if not s.startswith('!') else ''
            if not s:
                continue
            if re.match(r'CALL\s+[A-Za-z_]\w*', s, re.I):
                res.append((i, s))
            elif re.match(r'(DO\s+\w+\s*=|END\s?DO\b)', s, re.I):
                res.append((i, '>> ' + s))
    return res


def write_map(fname, maxline=None):
    tag = os.path.basename(fname).replace('.', '_')
    calls = extract_calls(fname, maxline)
    outp = os.path.join(OUT, 'ch21_' + tag + '_calls.txt')
    with io.open(outp, 'w', encoding='utf-8') as f:
        f.write('# %s  (%d entries)\n' % (fname, len(calls)))
        for i, s in calls:
            f.write('%5d  %s\n' % (i, s))
    print(fname, len(calls), '->', outp)


if __name__ == '__main__':
    write_map('dyn_em/solve_em.F')
    write_map('dyn_em/module_first_rk_step_part1.F')
    write_map('dyn_em/module_first_rk_step_part2.F')
    write_map('dyn_em/module_after_all_rk_steps.F')
    write_map('dyn_em/module_small_step_em.F', maxline=400)
    # 主文件头部注释（结构说明）单独抽 100 行
    with io.open(os.path.join(ROOT, 'dyn_em/solve_em.F'), encoding='utf-8', errors='replace') as f:
        head = ''.join(f.readlines()[:120])
    with io.open(os.path.join(OUT, 'ch21_solve_em_head.txt'), 'w', encoding='utf-8') as f:
        f.write(head)
    print('head written')
