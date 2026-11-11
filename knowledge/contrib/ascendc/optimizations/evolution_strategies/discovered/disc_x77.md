---
type: Optimization
title: "输出依赖图驱动的 stage/barrier 消除（intra-only 判定 + layout-only stage 折叠 + 全局 barrier 换组内握手）"
description: "对「算得多、但调用方只要一部分输出」的通用 kernel，先画输出依赖图，从调用方真正读取的输出反推依赖闭包：删除闭包外的 stage、折叠 layout-only stage，并用组内握手替代全局 barrier，算术完全不变。"
tags:
  - task.optimization
  - topic.data_movement.layout_transform
  - topic.implementation.synchronization
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X77: 输出依赖图驱动的 stage/barrier 消除

## 核心思路

对一个「算得多、但调用方只要一部分输出」的通用 kernel，**不要先去优化每个 stage 内部的算子**，而是先画
**输出依赖图**：从调用方真正读取的输出出发，反推哪些 stage/中间量在它的依赖闭包内。

一个典型 chunk-scan/SSM 类算子的总结构是 5 段串行
`gate(identity) → prepare → post_wu → 跨 chunk 状态递推 → finalize`，
段间 4 次全 grid SyncAll。但调用方只读 chunk-local 中间量 `w,u,qg,kg,Aqk,Akk`，
它们**全部由前两段 front end 产出**（`attn_out/final_state/v_new/h` 一个都不读）——
即数据流上**根本不存在跨 chunk / 跨单元依赖**，而 kernel 却用「单 launch + 通用 5 段 + 4 次全 grid barrier」
去算它。时延随 (chunk×head) 单元数近似线性、固定项占比高，且 AIC MAC 利用率很低，
**即瓶颈是阶段串行 + 握手延迟，不是算力/带宽**。

于是三步走，**算术完全不动**：

1. **删掉依赖闭包外的 stage**：加 intra 判定（`!storeH && !storeVNew &&
   !storeFinalState && !useGateInKernel && !computeGateInPrepare`），跳过 backend
   （状态递推 + finalize）→ 省 2 stage + 2 次全 grid barrier + 常驻 Catlass 流水建立开销。
2. **折叠「layout-only stage」**：identity gate 段（`useGateInKernel=false`）**不是纯 copy** ——
   它的真实作用是 **BSND → head-major 布局转换**（输入偏移只吃 BSND、输出偏移只写 head-major）。
   既然下游每个 (chunk,head) 单元自带 AIV0/AIV1，就让下游**按源张量自身行距直读**
   （新增行偏移/行距访问器，把下游各处 gk 读改成行距感知读）
   → 省 1 stage + 1 barrier + 一整套 `[T,HV,K]` fp32 的读+写。
3. **全局 barrier 换组内握手**：prepare→post_wu 的全局 SyncAll 替换为两条组内同步
   —— AIV→AIC 用 `CrossCoreSetFlag<0x2, PIPE_MTE3>`（MTE3 语义保证导出写落地后才抬 flag）
   + **AIV0↔AIV1 子块 barrier** `CrossCoreBarrier<0x1, PIPE_MTE3>()`。
   第二条**必须保留**：短尾 chunk 的导出行全归 AIV0，而 AIV1 的 tail 累加要读 AIV0 刚写的行，
   原全局 barrier 顺带承担了这个组内序，去掉它会暴露成 read-before-write。

## 适用场景

- **上层调用方只取算子部分输出**的场景（intra-only、块内量、中间量导出类算子）
- 通用 kernel 用「多 stage + 全局 SyncAll」实现，但被调用时实际依赖图远小于实现结构
- SSM/chunk-scan/线性注意力系（GDN-KDA/GLA）的 **intra** 变体；任何「导出中间量」的融合算子
- 判定信号：**AIC MAC 利用率很低但各 pipe 都不饱和**、时延随「单元数」近似线性且固定项占比高

## 实现要点（含两条硬纪律）

- **门控必须走 tiling，且只能复用已存在的字段**：新增判定最好用已存在的 `storeFinalState/storeVNew/storeH`
  组合，**不要往 tiling 结构体尾部追加字段** —— 若 host tiling 库与 device 二进制没有同步重建，
  追加字段会让 host 写旧布局 / device 读新布局，**无编译错误、静默读越界垃圾**。
  同时判定要写成「不满足就退回原路径」，保证泛化 shape 不回归。
- **layout-only stage 折叠前先确认它的真实作用**（identity gate 可能承担布局转置）；
  折叠后必须逐元素比对，且**先跑一次基线自比**区分「基线自带竞态」与「变体缺陷」
  （基线可能在尾部 chunk 的 `w` 上有 AIV 就地覆写竞态：自比出现不确定用例，
  变体与 golden 位一致，且差异是基线不确定用例的子集）。

## 边界与残留风险

- 尾部 chunk 的 `w` 上可能存在基线自带的 AIV 就地覆写竞态，比较时必须把基线不确定
  用例单独区分。
- solve 段仍有多轮 AIC↔AIV 往返；纯 cube 合并解存在，但切换需要把多处 `if constexpr`
  改成运行时分支，握手计数不匹配会挂死。

## 验证方法
- **性能**：在目标设备上对父变体与变体做同一时间窗口的 A/B（正反序至少两轮），
  以绝对时延和配对差值判断，不用跨窗口比值。
- **精度**：跑全量精度用例并逐元素对比参考实现；同时做基线自比，区分基线自带竞态与变体缺陷。
- **容量**：折叠 stage 或改布局后先审计 UB/L1/L0C/workspace 预算（含新增行距访问的缓冲），
  用 `static_assert`/越界检查确认无静默覆写。
