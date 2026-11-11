---
type: Optimization
title: "Col2im 相位化行归约（stride-s 反卷积散射重构，GEMM 中间矩阵上向量化）"
description: "反卷积 fallback（GEMM + col2im）的瓶颈常不是 im2col 带宽，而是 col2im 散射（逐输出行 undersize 加载 + Gather + parity 过滤 + PIPE_ALL 屏障）。将 col2im 改为按输出相位分解：每相位对相位内 G 行做全长对齐向量 Add 归约，列移位经 DataCopyPad src offset 与 left/rightPadding 落地，最后行粒度批量写回。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.compute.neighborhood.convolution
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# X34: Col2im 相位化行归约

## 核心思路
反卷积 fallback（cube GEMM + col2im）中，**GEMM 中间矩阵 G[mg, ng] 很小、GEMM 本身通常不是瓶颈**；真正瓶颈是 col2im 散射——逐输出行 (n,co,oh) 循环 tap，每 tap 一次 64B undersize GM 加载 + Gather + parity 过滤 + PIPE_ALL 屏障序列化。

把 col2im 重构为 **相位化行归约**：
1. 按输出奇偶拆 s² 个相位（stride-s），每相位只消费相位内 K²/s² 条 G 行
2. 对相位内 G 行做**全长对齐向量 Add 归约**（acc_phase = Σ_{taps} G_row[0:ng]），一次向量 Add 替代逐 tap Gather+Add（P94）
3. 列移位 c0=d_w0-b 经 DataCopyPad src offset + left/rightPadding 落地（P26，AIV 全 32B 对齐——绕开 odd-shift 的对齐封锁）
4. 相位平面 [co, n·hi·wi] 行粒度批量写回（P56）；wo==woA 时多块 DataCopyPad
5. 一次向量 Gather 奇偶交织写回（idx 一次性预计算，固定 SB 布局）

## 适用场景
- **算子类型**: 反卷积/分数步长卷积的 col2im fallback（GEMM + col2im 两 kernel 形态）；任何散射类 col2im/deconv
- **瓶颈类型**: col2im 散射（undersize_transfer + scalar Gather + PIPE_ALL 屏障序列化）主导；mte2_stall
- **前提条件**: GEMM 中间矩阵 G 可复用（常驻 L2）；相位行归约全长对齐（G 行 [0,ng) 连续）
- **收益形态**: 散射占比越高收益越大；剩余下限通常是 G 读带宽与双 kernel launch/AIC-AIV 切换

## 实现要点
1. **tap 表预计算**：rTaps/rDh/cTaps/cDw 启动时算好，消除逐行 parity 过滤
2. **多块加载门控**：多块 DataCopyPad 仅用于 `wi%8==0 && srcCol==0`——非对齐 src 行多块在目标架构上病态（曾回归后修复）
3. **列移位落地**：DataCopyPad src offset + left/rightPadding（勿用 V-pipe 逐元素移位——该架构无元素级 shift，strided 访问会挂死）
4. **G 读带宽是残余 floor**：G 读取 + 双 kernel launch/AIC-AIV 切换 + co 较小时并行度不足（unit=(n,co,po) 可用核数少）
5. **差异化定位**：X26 是流水线级 barrier 优化（3→2/行），本策略是算法级相位归约——更高杠杆，两者可叠加
6. **DataCopyPad(isPad=true) 尾部垃圾陷阱（配套 X26 tap-batch 发现）**：目标架构上 `DataCopyPad(isPad=true)` 在最后一个 32B 块的 `[wi, align8(wi))` 未对齐尾写入 **garbage（非 paddingValue=0）**——若把零 sentinel 放在元素 wi 会被首载 clobber。修复：sentinel 移到 32B 对齐元素 wiA（loads 整 32B 块写 `[0,wiA)`，永不触碰 wiA）+ Gather offset 无效映射从 wi*4 改为 wiA*4 + 一次性 V-pipe `Duplicate(src,0)`

## 关键前提洞察
"im2col GM 往返占大头" 的诊断可能有误导：GEMM 中间 G 很小，col2im 散射才是大头。**col2im 应极薄**（业界共识：ggml/CUTLASS dgrad output-stationary gather）。攻 col2im 自身结构而非 im2col 物化。

## 验证方法
- **同设备 A/B**：固定反卷积 shape/stride/dtype，对比相位化行归约与逐输出行散射的 kernel 时间，取多次 warmup 后的中位数；分别统计 im2col/GEMM/col2im 分段耗时以确认瓶颈位置。
- **全量精度**：覆盖全部 shape、不同 stride、奇偶相位、尾块与非对齐 wi；逐元素与参考反卷积比对。
- **容量审计**：核算相位平面与 G 行缓冲的 UB/L1 占用、DataCopyPad 的 32B 对齐与 padding 语义，确认 sentinel 位于对齐元素且尾块不被 clobber。
