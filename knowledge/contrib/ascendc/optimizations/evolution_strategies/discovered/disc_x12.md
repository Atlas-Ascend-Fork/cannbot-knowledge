---
type: Optimization
title: "X12: 量化 GEMV 纯 VEC 流式路径（小 M 分流）"
description: "对 weight-quant matmul（y = x @ ((w+o)*s) + b，w 为 int8），当 M 小（1-8，GEMV 类）时放弃 cube，走纯 VEC streaming：代数重构把 per-N scale 提出 K 循环，int8 weight 仅 cast 到 half 并用 mixed-precision Axpy 直接累加 fp32；大 M 受 VEC 指令发射延迟上限约束，必须分流到 cube 路径。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.compute.quantization
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X12: 量化 GEMV 纯 VEC 流式路径（小 M 分流）

## 核心思路
对 weight-quant matmul（y = x @ ((w+o)*s) + b，w 为 int8），当 M 小（1-8，GEMV 类）时放弃 cube，走纯 VEC streaming：代数重构把 per-N scale 提出 K 循环（y[m,n] = s[n]*(sum_k x[m,k]*w[k,n] + o[n]*rowsum(x[m])) + b[n]，热 K 循环内零反量化乘加），int8 weight 仅 cast 到 half，用 c220 mixed-precision Axpy（dst=float, src=half, Tuple<float,half>）直接累加 fp32，省掉 fp32 weight tile 和二次 cast。大 M（>=32）纯 VEC 受 VEC 指令发射延迟硬上限（~30cyc/Axpy 固定开销，总指令数 M*N*K/W）必然退化，必须分流到 cube 路径——小 M VEC / 大 M cube 的 M 阈值混合分流是该类算子的最优结构。

## 适用场景
- weight-quant / 反量化类 matmul（int8/int4 weight + per-N scale/offset），M 维度跨度大（1 到 128+）
- 小 M GEMV 类：带宽充裕、cube 网格利用率低（单核 M tile 极小）时，纯 VEC 显著优于 cube
- 瓶颈判定：aiv_vec_ratio 低且 mte2 未饱和 → 指令发射/依赖延迟瓶颈，不是带宽瓶颈

## 实现要点
1. **代数重构**（与 X9 deferred scaling 同源）：s/o/bias 全部折叠出 K 循环；rowsum(x[m]) 在 K 循环内对已提取的 x 标量做 fp32 标量累加（标量/向量双发射，零额外向量指令，避免 WholeReduceSum——c220 vcadd 仅支持 half/float，bf16 非法）
2. **mixed-precision Axpy**：fp16 路径 Axpy dst=float src=half；bf16 路径保持 fp32（wS 为 fp32 时 BK 粒度可放宽到 16 以开大 W）
3. **确定性两阶段 K-split 归约**（关键踩坑）：c220 `SetAtomicAdd+DataCopy` 原子加存在丢更新（多次调用结果不一致），host zeros 与 RunOpApi 启动流也无法可靠保序。禁止用原子加做 K-split；改为各 split 写 fp32 部分和到 per-call workspace + 同 stream 第二 kernel 求和 cast，精度反而更好。host 守卫：kSplit>1 要求 N%16==0（fp32 store 32B 行对齐）
4. **指令发射延迟隐藏**：8 路批量标量提取（背靠背发射 UB 标量读再发 8 个 Axpy）+ r+1 标量预取双缓冲；宽 tile（W=512, 8 repeats/Axpy）摊薄发射固定开销
5. **occupancy-aware host tiling**：makespan 模型（含指令发射成本、block 固定开销与 DMA 项）在 (MT, W, BK, kSplit) 空间搜索；blocks0<48 AIV 时自动加大 kSplit∈{1,2,4,8,16}
6. **窄尾块**：cM<5 走 8 独立部分累加器 narrow 路径，host 校验 8*tail*W <= acc 预算

## 验证方法
- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；用全量精度门禁与逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带。
