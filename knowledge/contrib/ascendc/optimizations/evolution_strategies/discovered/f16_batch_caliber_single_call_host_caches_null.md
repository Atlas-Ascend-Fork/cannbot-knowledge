---
type: Optimization
title: "F16: host 侧跨调用缓存（权重 repack LRU / tiling 缓存）在 batch 口径单次调用测量里零收益"
description: "在 batch 口径单次调用测量里，host 侧跨调用缓存（权重 repack LRU / tiling 缓存）无法命中，收益为零；应改用同窗口 A/B 或改变缓存生命周期来评估。"
tags:
  - task.debugging
  - topic.attention
  - topic.programming_model.execution_unit.cube
  - topic.programming_model.execution_unit.vector
  - topic.memory
  - topic.tiling
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/performance_analysis/collect_performance_data.md
    role: supporting
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/performance_analysis/analyze_performance_data.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/f16_batch_caliber_single_call_host_caches_null.json
    role: evidence
created_at: "2026-10-26T00:00:00Z"
updated_at: "2026-10-26T00:00:00Z"
platforms:
  - a2
---

> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 batch-caliber-single-call-host-caches-null）。
>
> 原始元数据：
>
> ```yaml
> confidence: single_op
> phenomenon: perf_neutral
> severity: medium
> occurrences: 1
> failed_combination: [P54, X35, P143]
> op_families: [matmul, cv-mix]
> operator_type: matmul
> ```

> 证据：基线/变体与逐 case 数据见 [证据包 cases/f16_batch_caliber_single_call_host_caches_null.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/f16_batch_caliber_single_call_host_caches_null.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# F16: host 侧跨调用缓存（权重 repack LRU / tiling 缓存）在 batch 口径单次调用测量里零收益

## 现象
本例算子（10 段 launch 链、每次调用重建 4 个 padded 权重副本 + `z=at::zeros`）：
按 P54/X35/P143 把权重 repack 改为 LRU 缓存（key = device+dtype+C+data_ptr+version counter）、
tiling 与 tiling H2D per-shape 缓存、`z` 改 `at::empty`、小 buffer 复用（`aBuf/a1Buf/a2Buf/wts` 复用）。

## 根因
评测口径是 `--quick --quick-batch`：**每个 case 每个进程只调用一次**（wrapper 里
`model = cls(...)` 后 `for _ in range(1): model(...)`，warmup 与计时是两个独立进程）。
因此每次被计时的调用都是该进程的**首次调用**，跨调用缓存必然全部 miss ——
repack 成本在「有缓存」和「无缓存」两版里都恰好付一次。
亚毫秒 case 的固定开销确实存在，但它是**单次调用内**的成本
（11~12 次 launch + 每次调度的核派发地板 + workspace 分配），只能靠减少 launch / 减少 buffer 来吃，
不能靠跨调用缓存。

## Resolution
1. **先判口径**：缓存类优化只有在「同一进程内同一 shape 反复调用」时才有价值
 （真实推理服务、per-iteration 训练）。评测若每 case 只调一次，直接不要做缓存类改动。
2. 单次调用内的固定开销，改走：合并无依赖的相邻 kernel（注意同 launch GM 写后读不可靠）、
 纯核 task type（`AIC_ONLY`/`AIV_ONLY`）、删掉内容会被完整覆盖的 buffer 的 `zeros`、
 按 shape 减少 grid/blockDim。
3. 若确实要做缓存，实现时必须带 **version counter + data_ptr** 双键（本卡复用该实现即可），
 否则原地改权重会命中脏缓存。

## 证据
本例算子 本轮变体，，Ascend910B2C：

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/f16_batch_caliber_single_call_host_caches_null.json`；引用时请结合上文适用条件与失效边界判断适用范围。

