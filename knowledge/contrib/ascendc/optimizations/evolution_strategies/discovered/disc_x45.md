---
type: Optimization
title: "X45: 融合管线 GM 往返消除（split-into-GEMM-load + B 侧 weight-stationary + attention 软件流水）"
description: "大 fp32 投影 GEMM 可能受 MTE2(GM→L1) 喂给率限制（cube/fixpipe idle）；融合管线中每个中间张量落 GM 再读回都是纯浪费，可从 A 侧 split-into-GEMM-load、B 侧 weight-stationary 混合网格、attention 软件流水三个方向消除 GM 往返。"
tags:
  - task.optimization
  - topic.attention
  - topic.programming_model.execution_unit.cube
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X45: 融合管线 GM 往返消除（split-into-GEMM-load + B 侧 weight-stationary + attention 软件流水）

## 核心思路
大 fp32 投影 GEMM 可能受 **MTE2(GM→L1) 喂给率限制**（cube/fixpipe idle）。
融合管线里每一趟中间张量落 GM 再读回都是纯浪费。三个独立有效的 GM 往返消除杠杆：

1. **A 侧 split-into-GEMM-load**：fp32 激活的 fp16 hi/lo 拆分不再先写 xHi/xLo 到 GM
   再读回（2写2读），而是 MIX kernel（AIV 在 UB 就地拆，经 workspace ring 交给 AIC；
   AIC 把整 [64,kPad] A tile 驻留 L1 跨 column-task 复用）。A 侧 MTE2 从
   nNum/row-block 降到 1/row-block。**关键工程教训**：按每 task 的 producer/consumer
   粒度会让 AIV 对同一 A tile 每 by 重拆 nNum 次，抵消收益；必须改 bx（行块）粒度
   并配合 L1 A-stationary 才生效。

2. **B 侧 weight-stationary 混合网格**（MGROUP=6）：
   任务网格 (bx,by) -> (by, M-group)。B tile（hi/lo 两平面）每 k-step 从 GM->L1 只载一次，
   跨 MGROUP=6 个 M 块复用（B GM->L1 流量降为 1/MGROUP；B:A 流量高时 B 是 MTE2 主体）。
   **混合门槛**：仅当 mNum>MGROUP 且 wsTasks>=核数 才用 WS 网格，小 shape 回退扁平
   网格（WS 额外 MTE1_MTE2 屏障对非 MTE2-bound 是纯开销）。
   L0C 128KB 硬约束 MGROUP*64*64*4B <= L0C，MGROUP=6（96KB）为安全值，MGROUP=7（112KB）
   因 M-group 尾块不均而不稳。

3. **attention 软件流水 + ws3 O-ring 消除**：
   - **ws3 O-ring 消除**：AIC PV fixpipe 直接写 O 到 attnOut（quantPre F322F16/F322BF16），
     删除 ws3 GM 写+读往返与 AIV ComputeOutput stage，attention 3-ring -> 2-ring 流水。
   - **AIC 软件流水**：AIC 每迭代先发 QK^T(task+1) 再算 PV(task)，
     使 QK^T 的 cube 在 PV 等 P 槽期间已进流水；批量 mmad（FireMmad3/2，一次 MTE1_M sync
     发 3 个 hi/lo mmad）消除 per-mmad 标量同步（标量同步占比高是 attention
     latency-bound 的主因）。workspace RING_DEPTH 2->3 让 AIV softmax 更早跑。

## 关键负结果（避免重复）
- **A+B 双驻留融合失败**：把 A 侧 split-ring 与 B 侧 weight-stationary 融合成单 MIX
  kernel 的 gridMode=1 路径会回归——WS 网格把 N-group 分到各核，每 column-task
  从 ring 重读 A row-block（A 侧 MTE2 随 nGroups 放大），抵消 A 驻留收益；
  L1(512KB) 无法同时驻留 R>1 个 [64,kPad] A tile 与 B tile。**结论：A 驻留与 B
  驻留需分别用扁平/WS 网格，不能在同一网格内同时做**。
- **MGROUP>6**（7）：L0C 112KB 近满 + M-group 尾块不均，收益回归。

## 适用场景
- GQA/FA prefill 融合管线，中间张量（split hi/lo、qkv、attnOut、workspace）落 GM 再读回。
- 投影 GEMM MTE2-bound：A 侧 over-read 严重 -> split-into-load + L1 A-stationary；
  B 侧重拉 -> weight-stationary 混合网格（MGROUP 由 L0C 决定）。
- attention latency-bound（cube 利用率低且标量同步占比高）-> 软件流水 + 批量 mmad + 深 ring。
- workspace 往返 -> 直接消费 cube 输出（fixpipe quantPre 直写终态）。

## 实现要点
- split-into-load 必须按行块（bx）粒度做，A tile L1 驻留跨 column-task 复用；MIX kernel 的
  AIV split 用 mode2 硬件配对（两 AIV 各 set 一次 -> AIC wait 一次）。
- WS 网格的混合门槛是形状自适应（mNum>MGROUP 且 wsTasks>=核数），小 shape 必须回退扁平。
- L0C 预算：MGROUP*64*64*4B <= 128KB，MGROUP=6（96KB）安全。
- attention 软件流水需 RING_DEPTH>=3 给 AIV 超前空间；批量 mmad 背靠背依赖硬件 RAW scoreboard。
- 全部改动保持算子签名不变；精度用 fp16 hi/lo 分解并做全量精度验证。

## 验证方法
- **同设备 A/B 对比**：固定设备型号、CANN 版本、输入 shape 与 dtype，优化前后各跑多轮（含 warmup），取 kernel Duration 中位数对比；不跨设备或跨版本混合测量。
- **全精度校验**：用 PyTorch/参考实现逐元素比对，覆盖大 fp32 投影与 attention 边界 shape，满足对应 dtype 的 rtol/atol，且无 NaN/Inf。
- **容量审计**：核算 L0C（128KB）/L1（512KB）/UB 占用与 A/B 双驻留、workspace ring 需求，确认 MGROUP 与 RING_DEPTH 在容量内；检查 32B 对齐、16×16 fractal 与尾块处理。

## 补充判据（跨算子复核）

- **acc 循环内的重复 GM→UB 读要去重**：每行重复 `copy_gm_to_ub(ao_new, [D,HB])` 时，把它提到 `g` 循环外只读一次，循环内按 `ao_new[g*D]` 索引，可省掉每行一次 GM 读。
- **收益衰减**：同一修复在较慢的基座上 +4%，换到更快冠军后只有 +0.8%（进入 5–7% 噪声）；衰减本身说明固定开销已接近榨干，不要继续在同一层叠微优化。
