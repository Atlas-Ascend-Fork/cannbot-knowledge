---
type: Optimization
title: "X50: 融合 decode MLA kernel — 5→2 kernel + (j,head-block) 并行 + KV tile 跨 head 复用"
description: "decode 稀疏 MLA（QK^T→softmax→PV→epilogue 链）若为多个串行 AIV kernel 且中间结果物化到 GM，并行粒度只有 j，decode 单 token 时核利用率极低；融合 kernel、按 (j, head-block) 扁平并行并让 KV tile 跨 head 复用，可消除 GM 往返并吃满 AIV 核。"
tags:
  - task.optimization
  - topic.attention
  - topic.compute.normalization
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# X50: 融合 decode MLA kernel — 5→2 kernel + (j,head-block) 并行 + KV tile 跨 head 复用

## 核心思路
decode 稀疏 MLA（QK^T→softmax→PV→epilogue 链）若基线为 5 个串行 AIV kernel，
每个 kernel 把中间结果（scores/probs/out）物化到 GM，且并行粒度仅 j
（decode 单 token sumQ=1 时只有单核工作）。三重组合拳：

1. **kernel 融合**：qk_vec+softmax+pv_vec+epilogue 4 个 kernel 合成 1 个，整体从
   5 个串行 kernel 收缩为 2 个。scores/probs/out 全部驻留 UB（head 块 nH×capPad 与
   head_dim 维输出均远小于 UB 容量），消除 3 个 GM workspace 往返 + 3 次 launch。
2. **(j, head-block) 扁平并行**：每工作项处理 (j, hb) 一个 head 块，核数自适应
   （sumQ>=48 时按 head 分块，否则 numHB=round(48/sumQ) 上限 hPad），decode 单 token
   高 H 场景从单核 → 吃满全部 48 个 AIV 核。
3. **KV tile 跨 head 复用**：循环序反转为 `[kv_tile][head]` —— 每个 16 行 kv tile
   只从 KV workspace 读一次，在 UB 内被该 head 块所有 head 复用，消除 H 倍冗余 GM 读
   （单 token 高 H 场景 QK+PV 各搬 KV 多遍是 memory-bound 主因）。

数值语义与 reference 完全一致（两遍法 softmax：scores 存 UB 原地转 probs，
probs=exp(s-max)/(sum+exp(sink-max))；无效列 KV 零填充 + validF32 在 exp 后乘 0；
max 为常数平移，softmax 平移不变性保证全无效行输出 0）。

## 适用场景
- decode 稀疏注意力（MLA/MQA/GQA，q_len=1，head_dim 大、head 数多）
- 多 kernel 串行物化中间结果的注意力链（GM 往返成为 launch-latency/MTE2 主成本）
- 单 token 时核利用率极低（按 j 并行只能上单核）的 decode 形态

## 实现要点
- UB 预算：head 块 nH≤8 × capPad≤384 fp32 scores + probs + out 行，须 ≤192KB，
  超出则缩 head 块大小（numHB 自适应）。
- sink 路径：按 nH 直接 DataCopy 时，nH 非 16 倍数会违反 MTE2 32B 对齐，
  必须整行 [hPad] 对齐搬运 + 标量 gather 到连续缓冲再向量 Sub/Exp/Add。
- 数值稳定：无效列必须 -1e30 mask 注入（仅靠 KV 零填充会让某 head 全零概率在
  fp32 exp 下溢时出现除 0/NaN），exp 前保留行 max 减法。
- V→S 时序：softmax 行归约结果被标量读取时需 PipeBarrier<PIPE_ALL> 或 TQue 事件同步。

## 验证方法
- **同设备 A/B 对比**：固定设备型号、CANN 版本、输入 shape 与 dtype，优化前后各跑多轮（含 warmup），取 kernel Duration 中位数对比；不跨设备或跨版本混合测量。
- **全精度校验**：用 PyTorch/参考实现逐元素比对，覆盖 sumQ/head 数/head_dim 边界与全无效行，满足对应 dtype 的 rtol/atol，且无 NaN/Inf。
- **容量审计**：核算 L0C/L1/UB 占用与 scores/probs/out 全 UB 驻留需求，确认 nH×capPad 组合 ≤192KB；检查 32B 对齐、16 行 KV tile 与 sink 整行对齐。
