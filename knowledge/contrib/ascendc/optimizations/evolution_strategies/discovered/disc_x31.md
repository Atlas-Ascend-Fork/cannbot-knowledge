---
type: Optimization
title: "X31: bounded logits softmax 去 max 减法（平移不变 + 数值有界时跳过 max-trick）"
description: "softmax(z)=softmax(z-max(z)) 的平移不变性使 max 减法仅用于防 exp 溢出；当 logits 上界可证明且远低于溢出阈值时，可删除 WholeReduceMax+Brcb 广播+Sub，直接缩放后 Exp，并配合行求和 chunk 化与树形合并降低 barrier。"
tags:
  - task.optimization
  - topic.compute.normalization
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

# Strategy X31: bounded logits softmax 去 max 减法（平移不变 + 数值有界时跳过 max-trick）

## 核心思路
softmax(z) = softmax(z - max(z)) 是平移不变式。max 减法（WholeReduceMax + Brcb 广播 + Sub，约 3 个 pass 与每 tile 约 8 个 barrier）仅用于防止 exp 溢出：fp32 exp 的溢出点约 88，fp16 约 11.5。当 logits 可证明严格有界且远低于溢出阈值（经验安全线约 |z| < 30~40，并留余量）时，max 减法是纯开销——删除后直接 Muls(invDiv) + Exp，pass 数与 barrier 数相应减少。配合行求和 chunk 化 WholeReduceSum 全发出 + log-depth 成对树合并（大 S 时 barrier 从 O(C) 降到 O(log C)），可降低 softmax 单 kernel 的固定开销。

## 适用场景
- 输入域有界的 softmax（经有限范围投影后 logits 有界，如 x∈[-5,5] 经 nn.Linear 投影）
- 实现者能给出并验证 logits 上界（可在注释中记录推导/验证依据），并保留恢复 max 减法的开关
- 与 X30（head-minor 布局）正交可叠加；是 A5（max-trick）的条件反向优化
- **边界**：P 矩阵需 cast 回 fp16/bf16 时要额外小心——fp16 exp 溢出点仅约 11.5，删除 max 减法后必须对 logits 做 clamp 或确认上界远低于该阈值；fp32 中间累加域最安全

## 实现要点
1. 前提验证：确认 logits 上界 |z|max（如 q·k/sqrt(hd) 经权重投影后的范围），并保证其远低于 fp32 exp 溢出点 88。
2. 删除 WholeReduceMax + Brcb 广播 + Sub 三阶段；logits 先 Muls(invDiv) 再直接 Exp。
3. 除数用标量 Muls 替代 Div，并去掉重复 divisor 的 UB 缓冲，释放全 tile fp32 slot；tile 行数可随 UB 容量提升，使固定 barrier 摊到更多行。
4. 行求和：chunk 化 WholeReduceSum 先全部发出（相互独立），再做 log-depth 成对树合并（barrier O(C) -> O(log C)）。
5. 注释中记录 logits 上界的证明/验证依据与恢复开关；若输入范围未来可能无界，须加 clamp 或恢复 max 减法。
6. **失效回滚**：若后续把 online-softmax 改为行归一化、或 logits 缩放/输入分布变化导致上界突破阈值，必须恢复 max 减法；保留单 bool/编译开关，避免代码重构时丢失安全路径。

## 验证方法
- **同设备 A/B**：固定 shape/dtype 与输入分布，在开启/关闭去 max 路径之间交替运行，取多次 warmup 后的中位数对比。
- **全量精度**：对全部 shape 与参考 softmax 逐元素比对，覆盖上界附近的极值输入、尾块与非对齐长度；同时验证 fp16/bf16 cast 后不出现 Inf/NaN。
- **容量审计**：核算去 max 后 UB 中释放的 slot 与增大后的 tile 行数，确认不超过 UB 容量且满足 32B 对齐；保留 max 路径开关，确认可回退运行。
