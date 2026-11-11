---
type: Optimization
title: "X15: 递归拆分-并行投影外提 (Recurrent Split: Hoist Parallel Projection)"
description: "对 RNN/LSTM/GRU/scan 类含串行循环的算子，将计算拆为\"非递归部分\"与\"严格串行部分\"：非递归投影（如全部时间步的 x@W_ih）与循环无关，可一次性合并为单个大 GEMM，外提到 host 侧调用框架/库的高性能 GEMM（自动走 Cube 单元）；自定义内核只保留严格串行的递归残差（如每步 h@W_hh + 门激活 + 状态更新），并将递归权重（W_hh）在 UB 常驻、超规格时回退分块。串行链上的计算量从 O(seq×(I+H)×4H) 降到 O(seq×H×4H)，且大头走了 Cube。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.tiling
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X15: 递归拆分-并行投影外提 (Recurrent Split: Hoist Parallel Projection)

## 核心思路
对 RNN/LSTM/GRU/scan 类含串行循环的算子，将计算拆为"非递归部分"与"严格串行部分"：
非递归投影（如全部时间步的 x@W_ih）与循环无关，可一次性合并为单个大 GEMM，外提到 host 侧
调用框架/库的高性能 GEMM（自动走 Cube 单元）；自定义内核只保留严格串行的递归残差
（如每步 h@W_hh + 门激活 + 状态更新），并将递归权重（W_hh）在 UB 常驻、超规格时回退分块。
串行链上的计算量从 O(seq×(I+H)×4H) 降到 O(seq×H×4H)，且大头走了 Cube。

## 适用场景
- 含时间步/序列串行依赖的算子（LSTM/GRU/RNN/线性 scan/指数衰减累加）
- 每步同时含"只依赖当前输入的投影"与"依赖上步状态的递归投影"
- 小 batch 场景自定义 Vector AXPY 模拟 GEMV 远低于框架 GEMM 效率时收益最大

## 实现要点
- 外提部分：将 x 重排为 (seq×batch, I) 单次 matmul，输出 permute 成 gate-major [seq,4,batch,H]
  便于内核按门连续访问；fp16 输入建议 fp32 累保精度
- 内核部分：递归权重 W_hh (H×4H) 按 UB 余量切 chunk 常驻；超规格时回退分块
- 每步只做 gates += h @ W_hh^T（向量 AXPY 或小块 matmul）+ sigmoid/tanh + c/h 更新
- 回退路径：W_hh 超 UB 容量时按 chunk 双缓冲轮转重载，或回退 host 分步 GEMM
- 外提 GEMM 必须保持完整数学等价，不得改变递归语义

## 验证方法
- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；用全量精度门禁与逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带。
