---
type: Optimization
title: "纯向量 AIV 注意力全重构 + 最小跨管同步纪律（AIC/MIX 注册不可用时）"
description: "当目标环境 AIC/MIX（AIC+AIV 双核）内核注册不可用、MIX 路径无法 launch 时，不要死守 Cube 路径：把整个注意力前向（QK^T → SiLU/scaling → mask → @V）压到 AIV 向量管，并配套最小跨管同步纪律与数据竞争防护。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.compute.reduction
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# X71: 纯向量 AIV 注意力全重构 + 最小跨管同步纪律

## 核心思路
当环境检测到 AIC/MIX（AIC+AIV 双核）kernel 注册**不可用**（MIX 路径无法 launch）时，
不要死守 Cube 路径：把整个注意力前向（QK^T → SiLU/scaling → mask → @V）全部压到
AIV 向量管，做**纯向量 AIV 全重构**，并配套两条关键纪律：

1. **同步纪律最小化**：利用同 PIPE_V 指令保序，每 tile 只保留 **3 个跨管同步点**
   （K 载后 / V 载前+后），消除基线每 (i,j) 多次 `PipeBarrier<PIPE_ALL>` 的全管道
   排空。跨管（V→MTE3、ReduceSum WAR）屏障一个不能少，同管（V→V）用 PIPE_V 即可。
2. **正确性硬约束（数据竞争 3 处 + 缓冲溢出 + 激活精度）**：
   - `ReduceSum(i)` 读 red 与 `Adds(i+1)` 写 red 之间必须 `PIPE_ALL`（ReduceSum 非普通
     V 管指令，仅 PIPE_V 不足）；sAct（V 写）→ GetValue（标量读）、oAcc（V 写）→
     WriteBack（MTE3 读）同样必须 `PIPE_ALL`。
   - 归约缓冲按 `64×dimAlign_`（非 64×64）分配，否则越界写坏相邻 UB。
   - SiLU 用硬件 `Silu` 指令而非 Sigmoid+Mul 组合（后者精度带不达标）。

## 适用场景
- 注意力前向/backward 算子，且**当前环境 AIC/MIX 注册不可用**（内核注册/启动返回不支持或失败）——
  先探测 `GetCoreNumAic()` / kernel 注册返回值，确认 Cube 路径真的起不来再重构
- 基线为 MIX AIC+AIV 经 GM workspace 握手、DEPTH=1 锁步空泡严重的实现
- causal / maxAttnLen 窗口用例占比高（结构稀疏跳过收益大）

## 实现要点
- 每 tile 同步点收敛到 3 个：K 载后（MTE2→V 可见）、V 载前、V 载后（V→后续读）
- `ComputeS` 去掉每行 `Duplicate`：归约缓冲每任务清零一次 + 尾行 Cast 后清零，
  保证 0*0=0 无 NaN 传播
- PV 用 `Axpy`（dst += src*scalar）替代 `Muls+Add`，向量指令减半；`GetValue` 在 V 管
  排空后批量读
- causal/maxAttnLen **结构稀疏跳过**：causal 时 `t>qbLocal` 的 tile 全掩码；
  `mlen>0` 窗口外 tile 跳过；含 contextual 行（rowId==0 可远端解禁）的 q 块保守回退全量
- Q/K/V 行装载与 O 写回改用**单次跨步 DataCopy**（行 stride=heads*D），把逐行指令合并为单条

## 约束 / Trade-off
- 纯向量路径放弃 Cube 算力，对**去 softmax、无行归一化**的注意力类算子收益最大
  （QK^T 无需降维中间结果）；标准 softmax 注意力需在线/分块 softmax，向量管成本更高
- 同步屏障是正确性硬约束：缺失 `PIPE_ALL` 会导致边界行随机错，调试代价高——
  用确定性复验（同用例多次 bit 一致）定位
- 收益集中在消除 AIC/AIV 锁步空泡 + 结构稀疏跳过；若环境支持 MIX 且 pipeline 已重叠，
  纯向量重构未必更优

## 验证方法
- **性能**：在目标设备上对父变体与变体做同一时间窗口的 A/B（正反序至少两轮），
  以绝对时延和配对差值判断，不用跨窗口比值。
- **精度**：跑全量精度用例，逐元素对比参考实现（必要时用 fp64 参考），要求容差内通过；
  对依赖同步/并发的改动，同一用例重复多次要求 bit 一致以排除竞态。
- **容量**：核对 UB/L1/L0C/workspace 预算（含归约缓冲按 `64×dimAlign_` 的分配），
  确认无越界或静默覆写。
