---
type: Runbook
title: 'P131 Playbook: 权重 Repack LRU 缓存落地 SOP'
description: 纯 host 侧改动。
tags:
- task.optimization
- topic.programming_model.execution_unit.cube
- topic.compute.composite
- topic.compute.quantization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/playbooks/P131_weight_repack_lru_cache.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-09T00:00:00Z'
platforms:
- a2
aliases:
- P131
---

# P131 Playbook: 权重 Repack LRU 缓存落地 SOP

> 占位符约定：`{KERNEL_DIR}` = 算子 kernel 源目录（原 shared/original/op_kernel），`{HOST_DIR}` = host 源目录，`{OP_SRC_DIR}` = 算子源码根，`{NOTE_FILE}` = 实现笔记文件（原 implementation_note.txt）。


> **强制流程**。纯 host 侧改动。完整实战记录见 [../../optimizations/evolution_strategies/discovered/disc_x20.md](../../optimizations/evolution_strategies/discovered/disc_x20.md)。

## Step 1: 取证

```bash
grep -nE "repack|wrepack|Repack" op_host/*.cpp op_kernel/*.{cpp,h} > /tmp/p131_locations.txt
```
确认：repack kernel 每次调用都发射？权重在评测/推理循环中是否不变？

## Step 2: 缓存实现（host C++/ATen）

1. 缓存键：`data_ptr + sizes + dtype + version counter`——**version 必需**（in-place 修改 bump version 强制重打包，否则脏数据）
2. 条目持有 weight **强引用**（防 allocator 回收地址被复用造成 stale 命中）；workspace 张量由条目持活
3. LRU 容量个位数条目；miss 时整体重写
4. 多目标布局（normal k 序 vs fused k 序）→ **布局标志进缓存键**
5. 留环境变量开关（`*_WREPACK_CACHE=0`）便于 A/B 与排障

## Step 3: 验证

- 权重不变反复调用：第二次起 repack kernel 零发射
- in-place 改权重（`copy_`/`fill_`）后必须重打包（version 机制生效）
- 多布局混用时结果正确（布局标志在键中）
