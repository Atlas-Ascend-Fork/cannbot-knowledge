---
type: Optimization
title: "X37: FP32-via-FP16 Hi/Lo 4-GEMM（fp32 精度要求的 Cube 重构路径）"
description: "Cube 的 Mmad 不直接消费 fp32 输入。要求 fp32 allclose 时，bf16 hi/lo 3-GEMM 的误差不够；改用 fp16 hi/lo 拆分并保留 lo@lo 项的 4 次 fp16 Mmad，可在 fp32 L0C 累加下把误差压到约 1e-5 量级，代价是 4 倍 cube FLOPs 与额外的 split 预 pass。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.precision
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X37: FP32-via-FP16 Hi/Lo 4-GEMM（fp32 精度要求的 Cube 重构路径）

## 核心思路
Cube 的 Mmad 不直接消费 fp32 输入（fp32 cube MMA 会产生 NaN）。X17/P128 用 bf16 hi/lo 3-GEMM（~1e-4 相对误差）解决 fp32 GEMM 上 Cube 的问题，但当应用要求 fp32 allclose（atol≈2e-5，如 torch 算子精度校验）时，bf16 3-GEMM 的 ~1e-4 误差不够。

本策略改用 **fp16 hi/lo 拆分 + 4 次 fp16 Mmad**：
```
x = hi + lo + delta，hi = fp16(x)，lo = fp16(x − fp32(hi))，|delta| ≤ 2^-24|x|
A@B ≈ Ah@Bh + Ah@Bl + Al@Bh + Al@Bl   （4 次 fp16 Mmad，fp32 L0C 累加）
```
fp16 有 11 位尾数（vs bf16 的 7 位），hi+lo 捕获 ~23 bit，逼近 fp32 的 24 bit → 最大绝对误差 ~9e-6，落在 fp32 allclose atol=2e-5 内。**4-GEMM 必须保留 lo@lo 项**（fp16 hi/lo 的 lo 分量贡献不可忽略，丢该项误差回到 ~1e-4 量级）。

## 适用场景
- **算子类型**: fp32 输入的 GEMM 类计算（matmul / conv / attention 的 QK^T/PV/K1/K3 投影），Cube 仅支持 fp16/bf16，且精度要求是 fp32 allclose（atol ~2e-5）而非 ~1e-4
- **瓶颈类型**: compute-domain，fp32 被困在 Vector/标量路径（标量 GetValue 内层循环 + 2 向量指令/元素）
- **前提条件**: 容差允许 ~1e-5 相对误差；fp16 动态范围（~6e-5 到 65504）覆盖输入值域（大值溢出需先缩放）；±inf/NaN 语义按 X17 验证
- **收益形态**: 相对标量/向量 FMA 兜底有数量级提升；代价是 4 次 Mmad 与 split 预 pass

## 实现要点
1. **独立 split 预 pass**：纯 AIV kernel（wa_split_fp32）把 fp32 源拆成 fp16 hi/lo 两份（Q 可同时折叠 scale）。**UB 必须用深 ring（8-deep）** 规避 MTE3→V 的 WAR 竞争（单/奇偶缓冲会产生不确定挂起/数据损坏）
2. **K1/K3 GEMM 与 K2 注意力均可套用**：K1/K3 用 bulk-sync（AIC 4-Mmad → fp32 ws → AIV bias+store）；K2 的 S 与 O GEMM 都走 4-Mmad，AIV softmax 全程 fp32，P 在 UB 内拆 hi/lo 再喂 O GEMM
3. **每 k-chunk 的 `cmatrixInitVal` 必须为 true**：每个 KV-chunk 是独立输出 tile（AIV 分别累加 O），用 `(kt==0)` 会 double-count 产生错误结果
4. **4x cube FLOPs 是固有代价**：fp32 需要 4 次 fp16 Mmad（vs fp16/bf16 的 1 次），但对 cube 远快于标量 FMA 的场景可接受
5. **小 shape 会回归**：split 预 pass + 额外 kernel launch 的固定开销主导 tiny GEMM，小 shape 建议保留原向量 FMA 路径（按 M*C 阈值路由）
6. **host 预拆分（绕跨核 workspace bug 的替代 split 方式）**：除独立 AIV split 预 pass 外，也可把 fp32→hi/lo 拆分放到 host（torch `.to(fp16)` + `x − fp32(hi)` 双分量打包），在 kernel launch 边界完成。kernel launch = 全同步，AIC 读预拆分 fp16 面板与读原生数据等价，彻底规避「kernel 内 AIV MTE3 写 → AIC MTE2 读大 workspace 的 L2 可见性非确定」缺陷。代价：host 侧额外 GM 流量 + 丢失 device 侧折叠 scale 的机会；适合 host 侧已做 cast/打包的场景
7. **多次 Mmad 累加间必须 `PipeBarrier<PIPE_ALL>`**：同一 L0C 累加器的 hi·hi / hi·lo / lo·hi / lo·lo 多次 Mmad 之间必须插 `PipeBarrier<PIPE_ALL>`，否则 L0C WAR 依赖导致输出垃圾。这是 3-GEMM/4-GEMM 累加链的通病，与 X17/P128 的 L0C 累加同源

## 与 X17/P128 的关系
| 维度 | X17/P128 (bf16 3-GEMM) | 本策略 (fp16 4-GEMM) |
|---|---|---|
| dtype | bf16（7 尾数位） | fp16（11 尾数位） |
| GEMM 数 | 3（hi·hi + hi·lo + lo·hi） | 4（含 lo·lo） |
| 相对误差 | ~1e-4 | ~9e-6 |
| 通过 fp32 allclose(atol=2e-5) | 否 | 是 |
| split 方式 | 单趟 split-xtrans | 独立 AIV split 预 pass（深 ring UB） |

## 验证方法
- **同设备 A/B**：固定 GEMM/attention shape 与 dtype，对比 fp16 4-GEMM 与 bf16 3-GEMM、向量 FMA 兜底的 kernel 时间，取多次 warmup 后的中位数。
- **全量精度**：覆盖全部 shape，逐元素与 fp64/fp32 参考比对，确认最大绝对误差满足 fp32 allclose(atol≈2e-5)；重点检查 lo@lo 项、近零输出与动态范围边缘。
- **容量审计**：核算 L0C 累加器与 UB 深 ring（8-deep）占用、hi/lo 双分量缓冲与 split 预 pass 的 workspace，确认无 WAR 竞争与越界。
