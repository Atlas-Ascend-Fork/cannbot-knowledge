---
type: Optimization
title: as_strided 窄视图直返，消除非对齐输出的回拷 kernel
description: 将非对齐输出的回拷分支改为 as_strided 窄视图直接返回
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.synchronization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-strided-view-output-eliminate-copyback.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：as_strided 窄视图直返，消除非对齐输出的回拷 kernel

> 单一优化点：当 UB→GM 的 32B 对齐写约束迫使 host 分配 padded workspace 并在 launch 后用 `narrow+copy_` 回拷到精确 shape 的输出时，改为直接返回 padded workspace 的 `as_strided` 窄视图——省掉第二次输出分配与整条回拷 kernel，每个非对齐输出 case -30~75us wall。

## 1. 原理

- AscendC `DataCopyPad` UB→GM 要求目标 32B 对齐（非对齐目标被静默丢弃），常规做法 = per-plane stride padded workspace + launch 后 `view/narrow + copy_` 回拷——多 1 次 alloc + 1 个 elementwise copy kernel launch（aclnnInplaceCopy_Slice）；
- `at::as_strided(workspace, {N,C,Ho,Wo}, {C*stride, stride, Wo, 1}, 0)` 显式声明"plane 间 padded、plane 内连续"的合法 stride，torch 下游（allclose/逐元素/打印）对非连续视图完全兼容；
- 视图共享 storage 引用，Python GC 释放后 caching allocator 的复用是 stream-safe 的（同 stream 排队序保证）。

## 2. 性能问题模式

**触发场景**：
- host 代码含 `if (planeBytes % 32 != 0) { workspace=empty(padded); ...; output.copy_(srcView); }` 形态；
- profiling：仅"输出 plane 字节数非 32 倍数"的 case 比同规模对齐 case 慢 +40~100us，op_summary 里出现 `aclnnInplaceCopy_Slice` 行。

**不适用**：
- 调用方硬性要求 contiguous 输出（等价于回拷，无法省）；
- 输出会被原位写回/跨 stream 消费的场景（需保证消费在同一 stream 语义下）。

## 3. 正确性红线

- **padded 布局是 plane 尾 padding，不是行间 padding**：`view({N,C,Ho,stride}).narrow(3,0,Wo)` 是错误语义（会把 stride 当行宽），触发 shape 校验崩溃或错位；必须用 `as_strided` 显式给 `{C*stride, stride, Wo, 1}`；
- workspace 的 paddedElems 必须 = totalBlocks × strideElems（kernel 的 StoreTile 以此为 planeBase）；
- 返回非连续 tensor 属语义变化：验收若做 `torch.equal`/`contiguous()` 断言需确认。

## 4. 泛化条件

- **适用**：任何"对齐 workspace + 回拷"形态的直调算子（输出末维/中间维导致 plane 非对齐的卷积类、采样类、切片类）；通用动作：回拷分支 → as_strided 窄视图直返。
- **不适用**：见 §2（硬性要求 contiguous 输出；输出被原位写回/跨 stream 消费）。

## 5. 实施步骤

1. 保留 kernel 写 padded workspace 的逻辑不变；
2. host：非对齐分支删掉 `output = empty(exact)` 与 `copy_`，改为
   `output = at::as_strided(workspace, {dims...}, {stride...}, 0);`
3. stride 推导：plane 间 = padded stride；plane 内最内两维 = {innerDim, 1}；
4. 压力验证：500+ 次快速调用并立即丢弃输出（验证 async 写 + allocator 复用稳定）；
5. 精度验证照常（allclose 对非连续视图无影响）。

## 6. LLM 前置问题

- 回拷分支是否只为满足"精确 shape 输出"而非下游硬约束？
- padded 布局的 padding 位置（plane 尾 or 行间）是否已确认？
- 是否可接受非连续返回值（与验收/下游确认）？

## 7. 验收标准

- build + 精度全过；每个非对齐输出 case -30~75us wall；op_summary 中不再出现 `aclnnInplaceCopy_Slice` 行；500+ 次快速调用并立即丢弃输出的压力验证无 UB 越界/数据错位。

## 检索卡（短卡）

动作：将非对齐输出的回拷分支改为 as_strided 窄视图直接返回
适用：存在对齐 workspace 加回拷的直调算子，且输出维度导致 plane 非对齐
限制：padded 布局必须是 plane 尾部 padding，不得是行间 padding
范围：plane 非对齐输出的卷积、采样、切片类直调算子
检索词：DataCopyPad、UB→GM、32B 对齐、padded workspace、as_strided、narrow、copy_
机会：host 在 planeBytes 非 32B 倍数时分配 padded workspace 并 copy_
代价：原回拷方案多一次分配和一次逐元素 copy kernel launch
