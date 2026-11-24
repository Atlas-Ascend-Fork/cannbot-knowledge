---
type: Optimization
title: 多行打包摊薄 per-row 标量/流水开销
description: 将每核每次pipeline迭代由处理1行改为打包处理baseRowLen行
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-multirow-packing-perrow-scalar.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：多行打包摊薄 per-row 标量/流水开销

> 单一优化点：把每核每次 pipeline 迭代处理的"1 行"扩展为"baseRowLen 行"，行内所有
> per-row 向量/标量步骤（归约、scale、Cast）作用于整块，指令调用次数和流水循环数随
> baseRowLen 成比例下降。快的原因：指令发射/同步(barrier)开销对"小行宽"算子占比极高，
> 打包后摊薄到更多数据元素上。

本策略适用于任何"按行独立计算、行宽小、行数大、per-row 步骤多"的 kernel（逐行归约、
per-token scale 量化、逐行变换类），与具体算子无关。

---

## 1. 原理

对"每行 32~512 元素、行数数千"的算子，单行 pipeline 的固定开销（逐行 Abs/ReduceMax/
Muls/Maxs/Mins/Cast + 每步 PipeBarrier，再加 per-row GM 标量读）在指令计数上远超数据计算
本身。把 baseRowLen 行打包成一块后：数据量 ×baseRowLen，但 per-row 步骤的调用次数不变
（每块仍各调一次 Abs/ReduceMax/...），等于固定开销摊薄 baseRowLen 倍；同时流水循环数
（行数/baseRowLen）同步下降。baseRowLen 上限由可用 UB ÷ 单行 UB 需求决定。

## 2. 性能问题模式

1. 行宽小（H 几十~几百元素）、行数大（数千~数万），tiling 每次只处理 1 行。
2. 每行有多次向量调用 + 多次 PipeBarrier（标量/归约密集），指令计数 >> 数据量。
3. profiling：kernel 时间远大于"数据量/带宽"下限，V pipe 占不满、S pipe 标量串行。
4. 每行有依赖整行的标量步骤（如 per-token scale 需先归约再变换），无法天然整块向量化。

不适用：行宽大（H 数千）且行数少——单行 UB 需求大，baseRowLen 解不出 >1，打包无空间。

## 3. 正确性红线

- **逐行广播**：行不变的操作数（weight_scale/quant_scale 等）必须对**每一行**都乘，不能只乘第一行
  （经典 bug：`Mul(aF, aF, wsA, perRowLen)` 只覆盖第一行，baseRowLen>1 后其他行漏乘）。
- **逐行 DataCopyPad 而非 2D**：2D 多行 DataCopyPad 的 dst 行间距（按 colCount 对齐）与 UB 行步长
  （按元素对齐）不一致时，第 2 行起数据错位（读到 B 半等）。每行独立 1D DataCopyPad 最稳。
- **行步长统一元素对齐**：in/work/half/out 各 buffer 行偏移必须同一元素对齐粒度（如 32），
  否则连续 Cast 流（aIn→aF、fp32→half→int8）错位。
- **padding 清零**：行宽非对齐（H 非步长倍数）时每行尾部 padding 必须为 0，否则垃圾/NaN
  污染 per-row 归约（0×NaN=NaN）。
- **归约 workspace 串行**：per-row ReduceMax 复用同一 workspace，每行后需 barrier 防竞争。

## 4. 泛化条件

适用（任一）：
- 行数/行宽比大、单行 UB 需求小到能解出 baseRowLen≥2 的算子。
- per-row 有归约 + 标量 + 多步变换（Cast/clamp）的融合算子。

不适用（任一）：
- 行宽大到单行 UB 需求接近 UB 上限（baseRowLen 只能=1）。
- 行内无 per-row 标量/归约步骤的纯 elementwise 算子（打包收益小，但无损失）。

## 5. 实施步骤

1. tiling 用 `baseRowLen = clamp(availUb/perRowBytes, 1, cap)` 解算（仅单 pass 路径）。
2. kernel 的 CopyIn/Cast/归约/变换全部参数化为 curBaseRow（最后一块 curBaseRow < baseRowLen）。
3. 逐行广播修复 + 逐行 1D DataCopyPad + 统一行步长 + padding 清零（对照红线逐条核验）。
4. 全量编译，覆盖"非对齐 H、极小 H、baseRowLen>1"的泛化性 case 验证精度。
5. 多次取样确认大 M 小 H case 提速超噪声，且无 case 退化。

## 6. LLM 前置问题

- 单行 UB 需求是多少？能否解出 baseRowLen≥2？
- 行不变操作数（scale/weight）当前是否只乘了第一行？
- 各 buffer 行步长是否统一元素对齐？H 非对齐时 padding 是否清零？

## 7. 验收标准

- 精度：全量用例（含非对齐/极小 H/baseRowLen>1）通过。
- 性能：大 M 小 H case 加速比提升超噪声（本案例 case17 0.14→0.24、case18 0.51→0.79、case20 0.83→1.24、case6 0.59→0.89）。

## 检索卡（短卡）

动作：将每核每次pipeline迭代由处理1行改为打包处理baseRowLen行
适用：任一：行数/行宽比大且UB允许baseRowLen≥2；或每行含归约、标量及多步变换的融合算子。
限制：weight_scale、quant_scale等行不变操作数必须应用到每一行
范围：单pass的逐行融合kernel与每核pipeline迭代
检索词：baseRowLen、availUb、perRowBytes、ReduceMax、Cast、PipeBarrier
机会：小行宽、大行数且tiling逐行处理，每行多次向量调用和PipeBarrier
代价：受可用UB、每行字节数和打包上限约束
