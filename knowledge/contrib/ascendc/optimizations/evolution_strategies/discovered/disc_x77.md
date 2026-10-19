---
type: Optimization
title: "输出依赖图驱动的 stage/barrier 消除（intra-only 判定 + layout-only stage 折叠 + 全局 barrier 换组内握手）"
description: "对一个「算得多、但调用方只要一部分输出」的通用 kernel，不要先去优化每个 stage 内部的算子，而是先画"
tags:
  - task.optimization
  - topic.data_movement.layout_transform
  - topic.implementation.synchronization
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-10-13T00:00:00Z"
platforms:
  - a2
---

# Strategy X77: 输出依赖图驱动的 stage/barrier 消除

> 进化发现元数据（迁移自 cannbot-skills `references/discovered/` 原始 frontmatter）：
>
> ```yaml
> schema_version: okf.v1
> kind: discovered_strategy
> id: X77
> title: "输出依赖图驱动的 stage/barrier 消除（intra-only 判定 + layout-only stage 折叠 + 全局 barrier 换组内握手）"
> origin: discovered
> discovered_round: 1
> discovered_from: "ChunkKdaFwdIntra evolution, round_1/parallel_2 (node x0, open_exploration)"
> base_speedup: "同窗口 geomean kernel 0.35009ms -> 0.25093ms（1.395x 相对基线内核；相对 level4 归档基线 0.9338x -> 1.3028x）；50/50 精度；baseline 自比 21/50 不确定 vs 本变体 34/50 与 golden bit-identical"
> confidence: single_op
> status: active
> op_families: [ssm, kda, chunk-scan, linear_attention, delta_rule]
> bottlenecks: [no_overlap, launch_floor, tiling_imbalance, fake_compute_bound]
> tags: [stage-elimination, barrier-removal, dependency-graph, cross-core-flag, layout-only-stage, tiling-guard, chunk-scan, intra-only, 910b2c, dav-c220]
> strategy_ids: [X77, P132, P133, X24]
> ```

## 核心思路

对一个「算得多、但调用方只要一部分输出」的通用 kernel，**不要先去优化每个 stage 内部的算子**，而是先画
**输出依赖图**：从调用方真正读取的输出出发，反推哪些 stage/中间量在它的依赖闭包内。

本算子（ops-ref `chunk_kda_fwd` 的 intra 适配）总结构是 5 段串行
`gate(identity) → prepare → post_wu → RunFwdH(跨 chunk 状态递推) → KdaFinalize(attn_out)`，
段间 4 次全 grid SyncAll。但 benchmark 只读 chunk-local 中间量 `w,u,qg,kg,Aqk,Akk`，
它们**全部由前两段 front end 产出**（`attn_out/final_state/v_new/h` 一个都不读）——
即数据流上**根本不存在跨 chunk / 跨单元依赖**，而 kernel 却用「单 launch + 通用 5 段 + 4 次 72 核 barrier」
去算它。基线时延结构实测拟合为 `T ≈ 115us(固定项) + 2.27us ×(chunk×head) 单元数`，
而 2.27us/单元 ≈ 每单元 ~7 次 AIC↔AIV 跨核握手 × ~0.3us（score 2 + solve 4 + post_wu 1），
**即瓶颈是阶段串行 + 握手延迟，不是算力/带宽**（AIC MAC 利用率仅 4.2%）。

于是三步走，**算术完全不动**：

1. **删掉依赖闭包外的 stage**：`RunGeneric` 里加 intra 判定（`!storeH && !storeVNew &&
   !storeFinalState && !useGateInKernel && !computeGateInPrepare`），跳过 `RunGenericBackEnd`
   （`RunFwdH` + `KdaFinalize`）→ 省 2 stage + 2 次全 grid barrier + FwdH 的常驻 Catlass 流水建立开销。
2. **折叠「layout-only stage」**：identity gate 段（`useGateInKernel=false`）**不是纯 copy** ——
   它的真实作用是 **BSND → head-major 布局转换**（`kda_gate_cumsum_kernel.h` 的 InputOffset 只吃 BSND、
   OutputOffset 只写 head-major）。既然下游每个 (chunk,head) 单元自带 AIV0/AIV1，就让下游
   **按源张量自身行距直读**（新增 `GkRowOffset()/GkRowStride()`，把 prepare 5 处 + post_wu 4 处的 gk 读改成
   行距感知读）→ 省 1 stage + 1 barrier + 一整套 `[T,HV,K]` fp32 的读+写（case49 ≈ 16.8MB）。
3. **全局 barrier 换组内握手**：prepare→post_wu 的全局 SyncAll 替换为两条组内同步
   —— AIV→AIC 用 `CrossCoreSetFlag<0x2, PIPE_MTE3>`（与 op 内既有 syncReady/syncDone 同构，
   MTE3 语义保证导出写落地后才抬 flag）+ **AIV0↔AIV1 子块 barrier** `CrossCoreBarrier<0x1, PIPE_MTE3>()`。
   第二条**必须保留**：短尾 chunk 的导出行全归 AIV0，而 AIV1 的 tail 累加要读 AIV0 刚写的行，
   原全局 barrier 顺带承担了这个组内序，去掉它会暴露成 read-before-write。

## 适用场景

- **benchmark / 上层调用方只取算子部分输出**的场景（intra-only、块内量、中间量导出类算子）
- 通用 kernel 用「多 stage + 全局 SyncAll」实现，但被调用时实际依赖图远小于实现结构
- SSM/chunk-scan/线性注意力系（GDN-KDA/GLA）的 **intra** 变体；任何「导出中间量」的融合算子
- 判定信号：**AIC MAC 利用率极低（<10%）但各 pipe 都不饱和**、时延随「单元数」线性而固定项占比 >30%

## 实现要点（含两条硬纪律）

- **门控必须走 tiling，且只能复用已存在的字段**：新增判定最好用已存在的 `storeFinalState/storeVNew/storeH`
  组合，**不要往 tiling 结构体尾部追加字段** —— 本目录 vendor overlay 的 host tiling 库
  （`op_tiling/lib/linux/x86_64/libcust_opmaster_rt2.0.so`）**不被 rebuild.sh（含 pkg 模式）刷新**，
  追加字段会让 host 写旧布局 / device 读新布局，**无编译错误、静默读越界垃圾**。
  同时判定要写成「不满足就退回原路径」，保证泛化 shape 不回归。
- **layout-only stage 折叠前先确认它的真实作用**（本例的 identity gate 承担布局转置）；
  折叠后必须逐元素比对，且**先跑一次基线自比**区分「基线自带竞态」与「本变体缺陷」
  （本例基线自身在尾部 chunk 的 `w` 上有 AIV 就地覆写竞态：baseline 自比 21/50 不确定，
  本变体 34/50 与 golden bit-identical，差异全是基线不确定 case 的子集）。

## 来源

ChunkKdaFwdIntra evolution round_1/parallel_2（进化基线，open_exploration 节点 x0）：
- 同轮对照：parallel_1（只裁 back end，P132 特化）= 1.1386x；parallel_0（裁 back end + 屏障按需化）= 1.1591x；
  本变体（裁 back end + 折叠 layout-only stage + 全局 barrier 归零）= **1.3028x**（同窗口相对基线 1.395x）。
- 残留风险：尾部 chunk `w` 的基线自带竞态；solve 段仍 4 次 AIC↔AIV 往返（SAFE_GATE 路径已有 2 次往返的纯 cube 合并解，
  但切换需把多处 `if constexpr (SAFE_GATE)` 改运行时分支，握手计数不匹配会挂死）。
