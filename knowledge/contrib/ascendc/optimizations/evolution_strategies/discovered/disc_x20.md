---
type: Optimization
title: "X20: Host 侧权重预打包结果 LRU 缓存（Weight Repack Cache）"
description: "权重布局变换（K-major repack、fractal 重排、量化打包等）的输出是（weight 内容, shape, dtype, 目标布局）的确定函数；host 侧做 LRU 缓存，命中时跳过整个 repack kernel 发射。"
tags:
  - task.optimization
  - topic.compute.quantization
  - topic.data_movement.layout_transform
status: deprecated
replaced_by: contrib/ascendc/optimizations/evolution_strategies/cards/p131_weight_repack_lru_cache
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X20: Host 侧权重预打包结果 LRU 缓存（Weight Repack Cache）

> **已晋升为 P131**：策略卡见 [../cards/p131_weight_repack_lru_cache.md](../cards/p131_weight_repack_lru_cache.md)，Playbook 见 [../../../runbooks/performance/p131_weight_repack_lru_cache.md](../../../runbooks/performance/p131_weight_repack_lru_cache.md)，precondition YAML 见 cannbot-skills 仓 `community/ops/ascendc-evolution-strategies/references/preconditions/`。本文件保留该策略的详细机制说明，卡片内容以 P131 为准。

## 核心思路
权重布局变换（K-major repack、fractal 重排、量化打包等）的输出是
（weight 内容, shape, dtype, 目标布局）的**确定函数**。推理场景同一权重张量
被反复卷积/矩阵乘，repack 结果逐 bit 相同——host 侧做 LRU 缓存，命中时
**跳过整个 repack kernel 发射**，直接复用缓存的 workspace。

## 适用场景
- **算子类型**: 任何带权重预打包步骤的算子（conv、matmul、quant matmul），
  推理式重复调用模式
- **瓶颈类型**: launch-bound；或 repack kernel 本身耗时占比可测
- **前提条件**: repack 无随机性、无输入数据依赖；same-stream 执行
  （workspace 的流序复用假设，与 per-call workspace 相同）

## 实现要点
1. 缓存键：`data_ptr + sizes + dtype + version counter`——**version 必需**：
   in-place 修改（`copy_`/`fill_` 等）会 bump version 强制重打包，否则脏数据
2. **条目内持有 weight 强引用**：防止 allocator 回收 data_ptr 后被新张量
   复用地址造成 stale 命中
3. 缓存的 workspace 张量由条目持活，miss 时整体重写；LRU 容量小（个位数条目）
4. 多目标布局（如 normal k 序 vs fused k 序）时**布局标志进缓存键**
5. 留环境变量开关便于 A/B 与排障
6. 纯 host C++/ATen 逻辑，无 device 侧改动，全平台可移植

## 验证方法
- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；用全量精度门禁与逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带。
