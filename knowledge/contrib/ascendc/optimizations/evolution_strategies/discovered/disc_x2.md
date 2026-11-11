---
type: Optimization
title: "X2: 大张量驻留 Device、仅小索引过总线"
description: "host 协调的 gather/scatter/routing 类算子应让大张量驻留 device，仅把小索引张量过总线交给 CPU 排序，再由 NPU kernel 按索引搬运；避免大数据张量 device→host→device 往返。"
tags:
  - task.optimization
  - topic.mixture_of_experts
  - topic.compute.ordering
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/discovered/disc_X2.md
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T15:50:00Z"
platforms:
  - a2
---
# Strategy X2: 大张量驻留 Device、仅小索引过总线

## 核心思路
对于 host 协调的 gather/scatter/routing 类算子（host 预先排序并算好索引、kernel 仅做按索引搬运），
**不要**把大数据张量 (N×H) 做 device→host→device 往返再在 CPU gather，而是让大张量**全程驻留 device**，
只把小的 int32 索引张量 (N×K，比数据小一两个数量级) 过总线交给 CPU 做必须的排序，
然后在 NPU 上用 AscendC kernel 完成实际 gather。这把总线传输量从 O(N·H) 降到 O(N·K)，
对 H 大、K 小的 MoE 路由场景收益巨大（H≫K 时传输量按 H/K 量级下降）。

## 适用场景
- **算子类型**: MoE InitRouting、gather/scatter、embedding lookup 等 host 协调索引、kernel 搬数据的算子
- **瓶颈类型**: 总线传输/PCIe 往返主导（大张量两次跨总线搬运吞掉运行时），而非 kernel 计算
- **前提条件**:
  1. host 已（或可）在 CPU 端完成索引排序/计算，索引张量远小于数据张量
  2. NPU 不支持某些索引操作（如 int32 argsort）时仍需 CPU 排序，但只需传索引
  3. kernel 接口允许大数据张量直接以 device 指针传入（不要求 host 持有 gather 结果）

## 实现要点
- host 侧：仅对小索引张量做 `stable_argsort` 并算 `dst_to_src`，narrow/contiguous 回切输出去掉 padding 列
- kernel 侧多核：`blockDim = min(GetCoreNumAiv(), total_rows)`，每核处理连续 `[start,end)` 目标行片
- 每行 `origRow = dst_to_src[dst] % N`，MTE2 `DataCopyPad` 源 (xGM[origRow*H]) → UB，`isPad=true`、
  `rightPad=alignedH-H` 容忍非 32B 对齐的源字节偏移；MTE3 `DataCopyPad` UB → 输出（行 stride=alignedH 保证 32B 对齐行首）
- **关键正确性约束**: MTE2 加载与 MTE3 写出**必须用两个独立 TQue**（VECIN + VECOUT，中间 DataCopy 中转）。
  复用单个 VECIN 队列会让框架漏插首迭代 MTE2→MTE3 依赖，导致第 0 行写出抢读未完成的加载（row-0 garbage bug）
- `DataCopyExtParams.blockLen` 单位是**字节** (rowBytes = H*sizeof(T))，勿误用元素数

## 已知局限
- 消除大张量往返后，host 侧固定开销（CPU 排序 + 索引 D2H/H2D 同步 + kernel launch）会成为小 shape 的新瓶颈；要进一步突破需把排序/scatter 也搬到 device（on-device counting/bucket sort + 全 device gather/scatter）。

## 验证方法
- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；用全量精度门禁与逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带。
