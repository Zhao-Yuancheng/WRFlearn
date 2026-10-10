# Progress — 当前状态（可重写）

时间锚点: 2026-10-10（git 用户管理，方案 v2 待用户 commit）
Python: 本地 WRFlearn（py3.11.17，wrf-python 1.3.4.1，setuptools 钉 80.9.0）；集群 miniforge3 用户修复中（不阻塞写作——教材实操不依赖）
集群操作: 统一 workspace\scripts\cluster.py（run/srun/salloc/get/put/runfile）
阶段: **方案 v2 已交付，待用户审定** → commit 后进入 M2（批次 1：ch03 开写）

## 五轮问答全部收口（决议索引见 notes.md 各 Decisions 节）
- 定位/书名/格式/命名/篇幅/全角引号/考点与引用规范 → 方案 §1、§4
- 21 章目录 + 每章验收要点 + 书 1-6 章考点映射 → 方案 §3
- 贯穿个例定稿（兰州 2025-07-12 起报 / 07-13~16 分析 / 两域 9+3km / 论文2 同构基线）→ 方案 §6.2
- 实验总表（10 组重轨小实验 + ch19 双跑）→ 方案 §6.3
- 批次顺序（II 部先行→III 部→压轴→回填→校阅）与分节粒度 → 方案 §10
- 上下文纪律（handoff 协议/预算红线/工具资产）→ 方案 §8
- 论文2 对接（ch17/ch19 末/ch20 三级；内部使用）→ 方案 §7

## 待办
- [ ] 用户审定 doc\教材编写方案v2.md（重点看：§3.2 ch17 考点节微调、§6.2 个例定稿、§10 批次顺序）
- [ ] 用户 commit 冻结基线
- [ ] M2 开写：新会话启动 ch03 架构总览（按方案 §8.2 启动协议读 notes/progress/chapter_map）
- [ ] 工具：PPT media 索引脚本（ch12 前）、nc→intermediate 转换器（ch06 时）
- [ ] 等通知：集群 miniforge3 修复完成

关键入口: doc\教材编写方案v2.md（基线）→ notes.md → chapter_map.md
