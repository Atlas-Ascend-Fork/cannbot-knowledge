---
type: Optimization
title: "X47: 融合 attention 的结构消除 + core_softmax 块向量化 + launch 合并"
description: "融合 attention 的可复用正交结构杠杆：消除未被下游消费的中间 GEMM、稠密 per-head 投影 + no-prep 路由、fp32 投影用 SetHF32(false) 单 GEMM 替代 hi/lo 3-GEMM，以及 core_softmax 块向量化与 launch 合并。"
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

# X47: 融合 attention 的结构消除 + core_softmax 块向量化 + launch 合并

## 核心思路
融合 attention 达到参考性能的多个正交结构杠杆（可跨算子复用）：

1. **消除从未被消费的中间 GEMM**：投影同时产出 feature-major 与 row-major 两份中间
   结果，但 cube-core attention 只读 row-major 那份——feature-major 的投影 GEMM 从未
   被消费，消除后显著减少投影 Cube 工作量。**先查中间产物是否真被下游读取**，未被读的
   就是纯浪费。

2. **稠密 per-head 投影 + no-prep 路由**：Q/K/V 直接写稠密 per-head 布局
   [3,BH,S,DHP]（每 head 一个 64-col N-tile），消除一次 re-pack pass；投影直读输入 x
   （transA=false）、out 投影直读权重 Wo（transB=true），整个 prep 的 X^T/Wo^T 转置
   pass 跳过。

3. **fp32 投影用 SetHF32(false) 单 GEMM 替代 hi/lo 3-GEMM**：SetHF32(false) 全精度
   fp32 Cube 满足精度，单 GEMM 的 Cube 工作量少于 hi/lo，并省去 split_hilo AIV pass。

4. **core_softmax 块式向量化**：原实现每行 1 次 DataCopyPad + 逐元素 SetValue 掩码 +
   chunked WholeReduce，并产生大量 per-row PIPE_ALL GM barrier。改为 ROW BLOCK
   处理（P1 整块连续 DataCopy、P3 per-row DataCopyPad 批处理共享单次 barrier）、
   maskRow 向量 Add 替代逐行 SetValue、长行用 Level-2 ReduceMax/Sum 单次 GetValue。

5. **launch 合并**：输出 dtype 转换折入 core epilogue + 多组 split 合并为一次 launch，
   显著减少 launch 数，小 shape 收益明显。

## 适用场景
- 融合 attention 投影（QKV/out）与 attention core 的算子
- 投影同时产出 feature-major 与 row-major 中间结果的（检查消费方）
- 有大量 per-row barrier / 标量掩码的 softmax kernel
- fp32 投影用 hi/lo 3-GEMM 的（改 SetHF32(false) 单 GEMM）

## 实现要点
1. 审计所有中间 GM tensor 的消费方，消除未被读取的（feature-major 中间结果模式）。
2. 投影直写稠密 per-head 布局，跳过 re-pack 与 prep 转置 pass。
3. SetHF32(false) 单 fp32 GEMM（MatmulImpl），满足 fp32 精度校验。
4. softmax 按行块处理，消除 per-row PIPE_ALL barrier；长行用 Level-2 归约。
5. launch 合并：dtype 转换折入 core epilogue、多 split 合并为 multi-slot。

## 验证方法
- **同设备 A/B 对比**：固定设备型号、CANN 版本、输入 shape 与 dtype，优化前后各跑多轮（含 warmup），取 kernel Duration 中位数对比；不跨设备或跨版本混合测量。
- **全精度校验**：用 PyTorch/参考实现逐元素比对，覆盖投影、attention core 与 softmax 长/短行边界，满足对应 dtype 的 rtol/atol，且无 NaN/Inf。
- **容量审计**：核算 L0C/L1/UB 占用与稠密 per-head 布局、softmax 行块缓冲需求，确认在容量内；检查 32B 对齐、16×16 fractal 与 per-row barrier 消除后的同步正确性。
