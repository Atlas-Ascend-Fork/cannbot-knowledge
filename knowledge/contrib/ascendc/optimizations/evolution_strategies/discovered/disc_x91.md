---
type: Optimization
title: "X91: 参考舍入同源 (Reference Rounding Co-sourcing)"
description: "当算子的精度门是「与一个自身带内部舍入的参考实现逐点比对」，且该门的同精度兜底通道不可用（例如参考是 NPU-only 算子，其 CPU 同精度副本必然加载失败 ⇒ 判定退化为严格）时，"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.compute.normalization
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-10-13T00:00:00Z"
platforms:
  - a2
---

# Strategy X91: 参考舍入同源 (Reference Rounding Co-sourcing)

> 进化发现元数据（迁移自 cannbot-skills `references/discovered/` 原始 frontmatter）：
>
> ```yaml
> id: X91
> origin: discovered
> discovered_round: 1
> discovered_from: round_1/parallel_2
> base_speedup: 0.1405x
> ```

## 核心思路
当算子的精度门是「与一个**自身带内部舍入**的参考实现逐点比对」，且该门的**同精度兜底通道不可用**
（例如参考是 NPU-only 算子，其 CPU 同精度副本必然加载失败 ⇒ 判定退化为严格）时，
**提高自身计算精度不仅无益，反而更差**。正确做法是让本实现的**中间量舍入序列与参考同源**：
把在线 softmax 的统计块宽、中间量在进入下一次 matmul 前的 dtype 舍入点，对齐到参考内核的结构，
使两边误差**相消**而非**叠加**。

## 适用场景
- 精度判据是逐元素（MERE/MARE 两阶段）+ 值域兜底，且兜底所需的「同精度 CPU 参考」不可用
  （参考 forward 调用 NPU-only 算子、CUDA/NPU-only 库，或依赖硬件特性）。
- 失败例的指纹是：`max_abs_diff` 只有 1~2 ulp、`matched_ratio` 0.9x~0.9999、
  MERE 已在阈值内而 **MARE 被极少量近零元素支配** —— 即"算得没错，但误差来源与参考不同"。
- 参考本身是融合/分块内核（online softmax、chunked GEMM），因此其舍入点由内部块宽决定。
- 反例：参考是朴素全精度实现（无内部块结构）时，同源对齐无意义，应正常提高精度。

## 实现要点
- **可扫描的结构自由度很少**：(a) 在线 softmax / 归约的**统计块宽**（每多少 key 做一次
  max/sum 与 rescale）；(b) 中间量（如 P=softmax 结果）在进入下一次 matmul 前是否**落回输出 dtype**。
  用离线探针只扫这两个维度，比反复重跑整 kernel 快几个数量级。
- 判据用「越界点数」而非平均误差：小值域/相消域的允许量在被压成常数后，**点数**才是决定性统计量。
- 结论方向常与直觉相反：把中间量保留 fp32（"算得更准"）会使越界点比落 dtype 差 1~2 个数量级，
  因为那等于把参考自身的 dtype 舍入误差整个暴露出来。
- 对齐后仍会剩余少量不可达 case（统计块宽增大到参考宽度时，K/V tile 可能装不进 L1）；
  应记录为已知上限，而不是继续在精度上投入。

## 来源
自动发现于第 1 轮进化，算子 7_FusedInferAttentionScore，speedup 0.1405x（geomean vs PyTorch）。
实测证据：仅扫（块宽 × P dtype）两维，12 例探针上 128/256/768/1024/全长度 × 输出 dtype 全部失败
（越界点 1e2~1e4），512 × 输出 dtype 越界点 0（MARE 0.007~0.04，阈值 fp16 0.0098 / bf16 0.078），
任意块宽 × P 保 fp32 越界点 1e3~1e4；落到全量 50 例官方 gate 上由同一算子的其它变体 16/50 提升到 22/50。
