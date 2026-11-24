---
type: Optimization
title: GM↔UB 搬运引擎替换：NDDMA MultiCopy → burst DataCopyPad
description: 把 GM↔UB 规则切片搬运从 NDDMA MultiCopy 换成 burst DataCopyPad(ExtParams)，删 DCI 刷新，两侧连续时塌缩成 1D burst
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.synchronization
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/nddma-to-burst-engine-substitution.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：GM↔UB 搬运引擎替换：NDDMA MultiCopy → burst DataCopyPad

在同一份字节数下，把 GM↔UB 的规则切片搬运从 NDDMA `DataCopy<T,N>(MultiCopyParams)` 改为 burst `DataCopyPad(DataCopyExtParams)`。在“规则切片搬运”这一维上，引擎选择往往就是那个没被质疑过的杠杆。

## 1. 原理

NDDMA（`MultiCopy` / `DataCopy<N>`）是为“多维坐标 + 描述符缓存”设计的通用搬运器，它的成本模型里有一项与字节数无关的**每描述符固定开销**（解码、跨步跳转、DCI 缓存维护）。burst `DataCopyPad` 是更薄的引擎：一次 `DataCopyExtParams` 直接描述 blockCount/blockLen/srcStride/dstStride，没有多维坐标与描述符缓存。

当切片是**规则形态**（块长一致、行距可用固定 stride 表达）时，两种引擎搬的是同一份字节，但 burst 的固定开销显著更低，同字节下的有效吞吐更高。

为什么这条容易被漏掉：**范式文档通常把 NDDMA 写成规范路径**（例如 Broadcast 范式要求 “TBuf + NDDMA DataCopy + 多维坐标”），于是实现者不会去质疑默认引擎。常见实现正是全程 NDDMA、块长只有 64B/128B；在同样字节数下换成 burst 往往能显著提高同字节吞吐。

实现机制：把 `DataCopy<T,N>(dst, src, MultiCopyParams)` 改写为 `DataCopyPad(dst, src, DataCopyExtParams, DataCopyPadExtParams)`：
`blockCount = 行数`、`blockLen = 行字节数`、`srcStride = GM 行间字节间隔`、`dstStride = UB 行距（32B 块数）`；当两侧都连续时塌缩为 `blockCount = 1` 的 1D burst。同时删除原 NDDMA 路径专用的描述符缓存刷新（DCI flush）代码。

常与引擎替换一起做的一条：把“一行拆两段搬”改成**整行单段** —— 当行内两侧连续（`jt == h`）时，一行 D 个元素在 GM 连续，整个 `[tr][D]` tile 可以塌缩成一条 1D burst，读占空从 50% 提升到 100%（行 pitch = D）。它自身收益有限，价值在于两点：① 读占空是 burst 之后唯一剩下的搬运侧问题；② dense 行（pitch = D）是 `shared-entry-register-hoist-run-loop` 能按行建立 run 循环的前提。

## 2. 性能问题模式

- 优化目标：在字节数不变的前提下，降低 MTE2 的每描述符固定开销，提升有效搬运吞吐。
- 适用数据流：所有 GM↔UB 的规则切片搬运：elementwise 行式流、位置编码类算子的两半、reduce 的 strided 输入、layout-transform 的规则切片。

## 3. 正确性红线

- `DataCopyExtParams` 的 `blockLen/srcStride` 单位是**字节**，`dstStride` 是 **32B 块数**；NDDMA 的 `loopDstStride` 单位是**元素**，两者不可混算
- `blockCount ≤ 4095`、`blockLen ≤ 65535`；超限须拆多描述符或降行数
- `DataCopyPad` 会把每个 block 垫到 32B；若 UB 行距恰为 `ceil32(行长)`，则 `dstStride = 0`
- NDDMA 独有的 stride-0 广播语义（如 cos/sin 的 b 广播）burst 无法表达，必须保留 NDDMA 或改用显式循环
- 切换后必须删除原 NDDMA 的 DCI/描述符缓存刷新代码，否则留下无效开销

## 4. 泛化条件

- 策略作用域：所有 GM↔UB 的规则切片搬运：elementwise 行式流、位置编码类算子的两半、reduce 的 strided 输入、layout-transform 的规则切片。

适用：

- 切片是规则形态：块长一致、行距可用固定 stride 表达
- aiv_mte2 为主导 pipe，或块长 < 128B（描述符开销占比高）
- 块数 ≤ 4095、块长 ≤ 65535

不适用：

- 需要 stride-0 广播语义（多维广播）—— burst 表达不了
- 切片高度不规则（列下标不连续），需 gather
- 块长已很大且连续（≥512B），此时两者差异被带宽稀释
- 后端不提供 DataCopyPad
- 与 `2d-bulk-data-copy` 的分工：那张卡解决“逐行多条描述符 → 一条多块描述符”（**描述符条数**）；本卡解决“多块描述符仍在 NDDMA 引擎上，换成 burst 引擎固定开销更低”（**引擎选择**）。两者可叠加：先换引擎，两侧连续时再把块数塌缩成 1。
- 与 `2d-rowpair-datacopy-mte2-saturation-boundary` 的边界一致：描述符/引擎收益只在 MTE2 尚未带宽饱和时兑现；满核 MTE2-bound 时无收益。

## 5. 实施步骤

1. 先算当前路径的有效带宽：`字节 / MTE2 时间`；若已接近峰值则收益有限，但仍可试
2. 把每个 `DataCopy<T,N>(MultiCopyParams)` 逐条改写成 `DataCopyPad(DataCopyExtParams)`
3. 确认 stride 单位换算（字节 vs 元素 vs 32B 块）
4. 两侧连续时把 `blockCount` 塌缩为 1
5. 删除 NDDMA 专用的描述符缓存/DCI 刷新代码
6. 用 profiler 的 MTE2 时间与字节数核对“同字节吞吐”是否提升，再看墙钟

## 6. LLM 前置问题

- 目标路径的搬运是 NDDMA 还是 burst？块长多少字节？
- 切片是规则形态吗（块长一致、行距固定 stride）？
- 是否有 stride-0 广播语义需要保留？
- 切换后 UB 行距会变（32B 垫齐），VF 的 pitch 同步了吗？

## 7. 分类与关联

- Classification：`validated_strategy`
- Generality：`common`
- 相关策略：`2d-bulk-data-copy`（同族正向卡）、`2d-rowpair-datacopy-mte2-saturation-boundary`（饱和边界）

## 检索卡（短卡）

动作：把 GM↔UB 规则切片搬运从 NDDMA MultiCopy 换成 burst DataCopyPad(ExtParams)，删 DCI 刷新，两侧连续时塌缩成 1D burst
适用：切片规则且行距可用固定 stride；aiv_mte2 主导或块长<128B；块数≤4095、块长≤65535
限制：blockLen/srcStride 是字节、dstStride 是 32B 块数；stride-0 广播不成立；超上限须拆描述符
范围：GM↔UB 规则切片搬运（行式流、strided 读、layout 变换）
检索词：NDDMA、MultiCopy、DataCopyPad、DataCopyExtParams、burst 引擎、DCI flush、描述符开销
机会：块长只有 64B/128B 时每描述符固定开销压过有效带宽，MTE2 占用降不下来
代价：切换后 UB 行距按 32B 垫齐，VF 的 pitch 必须同步
