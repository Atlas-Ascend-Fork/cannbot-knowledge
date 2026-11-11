---
type: Optimization
title: "X140: MIX(CV) per-task 固定成本墙：优先 M 方向合批，而不是加宽 N"
description: "MIX(CV) kernel 中中间量经 GM ring 从 Cube 交给 Vector 时，每个 task 都要付跨核握手、L0C alloc/free、Fixpipe 发射与两侧标量链的固定成本；当该成本与 task 的有效 pipe 时间同量级时，沿天然复用的 M 轴把多行合成一个 task（mGroup）比加宽 N 更可行，因为 N 方向受 L1 tile 双缓冲容量限制。"
tags:
  - task.optimization
  - topic.data_movement
  - topic.parallelism
status: deprecated
replaced_by: contrib/ascendc/optimizations/evolution_strategies/cards/p151_mgroup_batching
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/blob/51687dcbebee726b8c17c282ea6b02e19c6a23dd/knowledge/contrib/ascendc/optimizations/evolution_strategies/cards/p151_mgroup_batching.md
    role: evidence
  - resource: https://gitcode.com/cann/cannbot-skills/blob/9e6774cef47d8bc483ac83de3eb0620a740d042a/community/ops/ascendc-evolution-strategies/references/preconditions/P151.yaml
    role: constraint
created_at: "2026-10-28T01:40:00Z"
updated_at: "2026-11-03T15:14:30Z"
platforms:
  - a2
  - a3
---
# X140: MIX(CV) per-task 固定成本墙：优先 M 方向合批，而不是加宽 N

> 已晋升为 [P151](../cards/p151_mgroup_batching.md)。本卡保留为发现记录。
>
> P 卡当前状态：`draft`（待实际算子正确性/性能验证证据）。

## 核心思路
MIX_AIC_1_2 kernel 里，一个 task = 一次 AIC 产中间量 + 一次 GM ring 交接 + 一次 AIV 消费。当中间量必须经 GM ring 从 Cube 交给 Vector（目标 SoC 没有 L0C→UB 通路）时，**每个 task 都要付**：

- 2 次跨核 0x2 pair 握手；
- L0C alloc/free；
- Fixpipe 发射；
- AIV 侧 acc 清零/输出写；
- 两侧标量链。

当固定成本与 task 的有效 pipe 工作量同量级时，它占据了 wall 的显著比例。按字节摊薄有两条路，**通常只有一条可行**：

- **N 方向加宽（常不可行）**：BLOCK_N 增大需要 K tile `[blockN, dim]` NZ 常驻 L1 且双缓冲。单是 `2 * blockN * dim * sizeof(dtype)` 就可能等于或超过整个 L1，容量直接封死。
- **M 方向合批（可行）**：一个 task 处理 mGroup 个 (b,m) 行，共用同一份 K tile（K 在 L1 里本来就被整条 m-run 复用）。S 的体积按 mGroup 线性增大，而**任务数按 mGroup 线性减少**。

## 适用场景
- CV 融合 kernel，中间量（Cube 产出、Vector 消费）必须走 GM/workspace ring。
- 存在一条**天然被复用**的操作数轴（GEMM 的 A 或 B 中在 task 间不变的那一维）。把这条轴做成 task 内合批，而不是去加宽被 L1 容量限制的那一维。
- 预检：先量 `固定成本/task` 与 `有效 pipe 时间/task`；若固定成本占比很小，合批收益有限。

## 实现要点
1. host tiling 增加 mGroup（1..N）与 chunkN；kernel 里 task 解码改为 `(b, n_tile, m_group)`，内层循环 m 行。
2. ring slot 尺寸 = `mGroup * mAlign * blockN * sizeof(acc_dtype)`；mGroup 放大后必须**同步下调 ring 槽数**，否则 workspace 足迹（槽数 × slot 大小 × 核数）会挤占 L2，反而让 K 的流被赶出缓存。
3. 小 M / M=1 的 case 必须按 mGroup=1 走原路径（host 门控 `mSize >= mGroup` 才启用），否则单 task S 变大反而伤小 shape。
4. 不要同时改 ring 握手计数：0x2 pair 语义下"删掉 free-credit 等待"会立刻 aicore trap。合批只改 task 粒度，不改信用协议。
5. 合批后每个 m 行的 softmax/归约状态要独立保存；不要把多行状态压进同一个标量寄存器组。

## 验证方法
- 先用微基准或插桩量出固定成本/task 与有效 pipe 时间/task。
- 按 mSize 分档做同设备 A/B：小 M、M=mGroup、M>>mGroup 三档。
- 检查 L1/L2 足迹：ring 槽数与 slot 大小的乘积不能超过预算。
- 精度：多行合批不应改变每行语义；逐行对比参考实现。

## 关联
- 与 [X157](disc_x157.md)（0x2 信用批量化）都涉及 CV 环 task 粒度，但 X157 改的是同步信用频率，本卡改的是 task 内行数。
- 与 [X146](disc_x146.md)（墙归属判定）配合：先用 X146 确认墙在 AIC/AIV 链的平衡点，再决定是否合批。

## 补充判据（跨算子复核）

- **task 粒度是双向调节**：固定成本主导时沿 M 轴合批（本卡）；欠并行时反向拆 task。例：融合 grouped matmul 的 `(g,m-block,n-block)` 任务空间展开为 `(g,m-block,n-block,gate|up)`，任务数翻倍，小 shape 利用率从 25% 提到 50%+，大 shape 尾波也被摊薄（+1.15x）。
- **判据**：先看 `totalTasks / coreNum` 与每 task 固定成本；task 数远小于核数 → 拆；固定成本与有效 pipe 时间同量级 → 合。两种方向不要同时用在同一个瓶颈上。
