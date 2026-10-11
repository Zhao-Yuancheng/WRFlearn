# -*- coding: utf-8 -*-
"""ch21 实验：重演 solve_em.F 的时间步进账本（num_sound_steps / dts / 各 RK stage 小步数），
并与 ch08 生产运行 439419 的实测步数交叉验证。

用法:
    D:/Code/miniforge3/envs/WRFlearn/python.exe scripts/ch21_timestep_audit.py
"""
import io
import re
import os

CASE = r'd:/Code/Learn/WRF/workspace/cases/lanzhou2025/namelist.input'
OUT_LOG = r'd:/Code/Learn/WRF/workspace/logs/ch21_timestep_audit.log'


def read_namelist_record(path, group):
    """极简 namelist 解析：返回指定 &group 内 key -> [values] 的字典（去掉注释）。"""
    rec = {}
    in_group = False
    with io.open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            s = line.split('!')[0].strip()
            if not s:
                continue
            m = re.match(r'&(\w+)', s)
            if m:
                in_group = (m.group(1).lower() == group.lower())
                continue
            if s.startswith('/'):
                in_group = False
                continue
            if in_group and '=' in s:
                key, vals = s.split('=', 1)
                key = key.strip().lower()
                vals = [v.strip().strip("'\"") for v in vals.split(',')]
                vals = [v for v in vals if v]
                rec.setdefault(key, []).extend(vals)
    return rec


def num_sound_steps(dt, spacing, max_msft=1.0):
    """solve_em 配置段 (time_step_sound==0 分支) 的重演。"""
    if max_msft == 1.0:
        expr = 300.0 * dt / spacing
    else:
        expr = 300.0 * dt / (spacing / max_msft)
    return max(2 * (int(expr - 0.01) + 1), 4)


def main():
    doms = read_namelist_record(CASE, 'domains')
    dt_d01 = float(doms['time_step'][0])
    ratio = float(doms.get('parent_time_step_ratio', ['3', '3'])[1])
    dx_d01 = float(doms.get('dx', ['9000', '3000'])[0])
    dx_d02 = float(doms.get('dx', ['9000', '3000'])[1])
    dt_d02 = dt_d01 / ratio

    lines = []
    lines.append('== ch21 时间步进账本（重演 solve_em.F 配置段公式） ==')
    lines.append('namelist: %s' % CASE)
    lines.append('time_step(d01) = %g s, parent_time_step_ratio = %g' % (dt_d01, ratio))
    lines.append('dx d01 = %g m, dx d02 = %g m' % (dx_d01, dx_d02))

    for name, dt, dx in (('d01', dt_d01, dx_d01), ('d02', dt_d02, dx_d02)):
        n = num_sound_steps(dt, dx)
        dts = dt / n
        lines.append('')
        lines.append('--- %s: dt=%g s, dx=%g m ---' % (name, dt, dx))
        lines.append('num_sound_steps = max(2*(int(300*dt/dx-0.01)+1),4) = %d' % n)
        lines.append('dts = dt/num_sound_steps = %g s' % dts)
        lines.append('RK3 各 stage（rk_ord=3）:')
        for step, dt_rk, dts_rk, ns in (
                (1, dt/3.0, dts if False else dt/3.0, 1),
                (2, dt/2.0, dts, n//2),
                (3, dt,     dts, n)):
            lines.append('  rk_step=%d: dt_rk=%8.4f s, dts_rk=%8.4f s, small_steps=%d'
                         % (step, dt_rk, dts_rk, ns))
        lines.append('每时间步声波小步总数 = %d + %d + %d = %d'
                     % (1, n//2, n, 1 + n//2 + n))

    lines.append('')
    lines.append('== 与 ch08 生产运行 439419 实测交叉验证 ==')
    days = 5
    total_sec = days * 86400
    n_small_d01 = 1 + num_sound_steps(dt_d01, dx_d01)//2 + num_sound_steps(dt_d01, dx_d01)
    n_small_d02 = 1 + num_sound_steps(dt_d02, dx_d02)//2 + num_sound_steps(dt_d02, dx_d02)
    lines.append('432000 s / dt_d01(%g) = %g 步  (439419 实测 d01 = 8000 步)'
                 % (dt_d01, total_sec / dt_d01))
    lines.append('432000 s / dt_d02(%g) = %g 步  (439419 实测 d02 = 24000 步)'
                 % (dt_d02, total_sec / dt_d02))
    lines.append('d01 每步小步数 %d → 5 天累计 %d 个声波小步'
                 % (n_small_d01, 8000 * n_small_d01))
    lines.append('d02 每步小步数 %d → 5 天累计 %d 个声波小步'
                 % (n_small_d02, 24000 * n_small_d02))

    out = '\n'.join(lines) + '\n'
    print(out)
    with io.open(OUT_LOG, 'w', encoding='utf-8') as f:
        f.write(out)
    print('log ->', OUT_LOG)


if __name__ == '__main__':
    main()
