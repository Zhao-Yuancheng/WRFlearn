#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""集群操作统一入口（避免 PowerShell/ssh 多层引号问题）。

用法（用绝对路径的 python 执行，PS 下参数用单引号包裹）:
  python cluster.py run  '远程命令'                     # 登录节点执行
  python cluster.py srun '远程命令' [-n 1] [-c 1] [-t 00:20:00]   # 经 srun 到计算节点执行
  python cluster.py salloc '远程命令' [-n 4] [-t 12:00:00]       # salloc 包裹（同 srun 语义，遵循用户建议模板）
  python cluster.py get  '远程路径' '本地路径'           # scp 拉取
  python cluster.py put  '本地路径' '远程路径'           # scp 推送
"""
import argparse
import shlex
import subprocess
import sys

HOST = "202.201.1.198"
PORT = "25192"
USER = "zhyuancheng2025"
PARTITION = "cpu"  # 用户规则：小任务 <=8 核，大任务整节点；不得写 mem 参数

BASE = ["-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
        "-o", "StrictHostKeyChecking=accept-new"]
SSH = ["ssh"] + BASE + ["-p", PORT, f"{USER}@{HOST}"]
SCP = ["scp"] + BASE + ["-P", PORT]

NOISE = ("miniforge3/bin/activate",)  # 远程 bashrc 的已知噪音行


def show(cp):
    for line in (cp.stdout or "").splitlines():
        print(line)
    for line in (cp.stderr or "").splitlines():
        if not any(n in line for n in NOISE):
            print(line, file=sys.stderr)
    return cp.returncode


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run")
    r.add_argument("command")

    s = sub.add_parser("srun")
    s.add_argument("command")
    s.add_argument("-n", type=int, default=1)
    s.add_argument("-c", type=int, default=None)
    s.add_argument("-t", default="00:20:00")

    a = sub.add_parser("salloc")
    a.add_argument("command")
    a.add_argument("-n", type=int, default=4)
    a.add_argument("-c", type=int, default=None)
    a.add_argument("-t", default="12:00:00")

    g = sub.add_parser("get")
    g.add_argument("remote")
    g.add_argument("local")

    pu = sub.add_parser("put")
    pu.add_argument("local")
    pu.add_argument("remote")

    rf = sub.add_parser("runfile")
    rf.add_argument("script")          # 本地 shell 脚本路径
    rf.add_argument("--srun", action="store_true", help="经 srun 在计算节点执行")
    rf.add_argument("-n", type=int, default=1)
    rf.add_argument("-c", type=int, default=None)
    rf.add_argument("-t", default="00:20:00")
    rf.add_argument("--keep", action="store_true", help="不在远程删除暂存脚本")

    args = p.parse_args()

    if args.cmd == "run":
        return show(subprocess.run(SSH + [args.command], capture_output=True,
                                   text=True, encoding="utf-8", errors="replace"))
    if args.cmd in ("srun", "salloc"):
        opts = [args.cmd, "-p", PARTITION, "-N1", f"-n{args.n}"]
        if args.c:
            opts.append(f"-c{args.c}")
        opts.append(f"-t{args.t}")
        remote = " ".join(opts) + " bash -c " + shlex.quote(args.command)
        return show(subprocess.run(SSH + [remote], capture_output=True,
                                   text=True, encoding="utf-8", errors="replace"))
    if args.cmd == "get":
        return show(subprocess.run(SCP + [f"{USER}@{HOST}:{args.remote}", args.local],
                                   capture_output=True, text=True, encoding="utf-8", errors="replace"))
    if args.cmd == "put":
        return show(subprocess.run(SCP + [args.local, f"{USER}@{HOST}:{args.remote}"],
                                   capture_output=True, text=True, encoding="utf-8", errors="replace"))
    if args.cmd == "runfile":
        import os
        import uuid
        base = "IceLake/scripts_staging"
        name = f"{os.path.basename(args.script)}.{uuid.uuid4().hex[:6]}.sh"
        remote_sh = f"/users/{USER}/{base}/{name}"
        subprocess.run(SSH + [f"mkdir -p /users/{USER}/{base}"], capture_output=True, text=True)
        cp = subprocess.run(SCP + [args.script, f"{USER}@{HOST}:{remote_sh}"],
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
        if cp.returncode != 0:
            print(cp.stdout + cp.stderr, file=sys.stderr)
            return cp.returncode
        if args.srun:
            opts = ["srun", "-p", PARTITION, "-N1", f"-n{args.n}"]
            if args.c:
                opts.append(f"-c{args.c}")
            opts.append(f"-t{args.t}")
            remote = " ".join(opts) + " bash " + shlex.quote(remote_sh)
        else:
            remote = "bash " + shlex.quote(remote_sh)
        if not args.keep:
            remote += " ; rc=$? ; rm -f " + shlex.quote(remote_sh) + " ; exit $rc"
        return show(subprocess.run(SSH + [remote], capture_output=True,
                                   text=True, encoding="utf-8", errors="replace"))
    return 2


if __name__ == "__main__":
    sys.exit(main())
