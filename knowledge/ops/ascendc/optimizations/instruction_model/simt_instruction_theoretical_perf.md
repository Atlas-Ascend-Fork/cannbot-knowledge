---
type: Optimization
title: SIMT 指令理论性能口径与有效吞吐判定
description: SIMT 理论值的单位是“单个 Vector Core 每 cycle 元素数”，且只对单一硬件指令实现的接口给出。按 128/64/32/16 四档识别待测瓶颈候选；实际主导时延与否须结合调用频次、依赖和调度实测。
tags:
- task.optimization
- topic.performance.analysis
- topic.programming_model.execution_model.simt
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/SIMT_instruction_theoretical_perf_summary.md
  role: primary
created_at: '2026-10-28T07:35:00Z'
updated_at: '2026-10-28T07:35:00Z'
platforms:
- '950'
---

# SIMT 指令理论性能口径与有效吞吐判定

文档把 SIMT 指令的理论性能统一表达为**理论并行度**：单个 Vector Core 在一个 cycle 内可处理的理论最大元素数量。本卡说明这个口径能回答什么、不能回答什么，以及如何据此判断“继续调 SIMT”还是“换 SIMD/RegBase”。文中数值均为文档给出的**理论值，非实测**。

## 适用范围

- 仅 Ascend 950PR&950DT 系列产品（平台 `950`）。
- 只覆盖由**单一硬件指令**实现的接口。软仿接口以及由多条硬件指令拼接实现的接口，文档不提供理论性能——对这些接口既拿不到上限，也就不能用它做瓶颈初判。

## 口径的边界：度量什么、不度量什么

定义里只有两个限定词：“单个 Vector Core”与“一个 cycle”。由此可直接推出三条边界：

1. **是元素数，不是指令数。** 同一接口在不同 dtype 下的元素数不同，跨 dtype 直接比较接口快慢没有意义。
2. **是单核值，不含并行规模。** 它不回答开多少核、多少线程的问题，占用率与负载均衡都在口径之外。
3. **是单指令值，不含指令间成本。** 访存、同步、分支发散、地址计算均不在口径内。

因此理论并行度可用于**同一算子内不同实现的单指令口径比较**与**待测瓶颈候选识别**，不能当作端到端时延预测或程序瓶颈证明。文档未量化调用频次、依赖、发射、混合指令调度以及发散与访存合并的折损比例，这类差距只能按[基准测试方法论](../bench_methodology_profiling_first.md)实测确认，不能由本表推算。

## 四档并行度：跨接口存在 8 倍落差

文档中带数值的记录共 298 条，全部落在 **128 / 64 / 32 / 16** 四个档位（理论值，非实测），且分布并不均匀——64 档占多数，128 档次之，32 与 16 档各有数十条：

| 档位 | 典型接口族（举例，非全量） |
|---|---|
| 128 | half/bfloat16 的加、减、乘、取负、fma；多数精度转换；warp vote；整型 max/min |
| 64 | warp reduce、lane id；rint/floor/ceil；大部分 int↔float 转换 |
| 32 | 除法（`__hdiv`、`__fdividef`）；exp/log/sqrt 类数学库；地址空间转换 `__cvta_*`；64 位整型转换 |
| 16 | warp shfl 全族；half2/bfloat16x2 的 exp/log/sqrt；half2 除法 |

判读要点：**热路径上的低档接口是待测瓶颈候选，不因出现就成为该段的吞吐上限**。跨档理论并行度最大相差 8 倍，但是否影响整段时延、是否值得优先于 tiling 调优，取决于执行次数、依赖与实际调度；先做档位归属，再实测归因。

## 三个容易判断错的点

**宽向量类型不自动提高该口径吞吐。** `__haddx2`/`__hmulx2` 与 `__hadd`/`__hmul` 同为 128 elements/cycle；但 `__hdivx2` 只有 16，低于 `__hdiv` 的 32；`h2exp`/`h2log`/`h2sqrt` 为 16，低于 `hexp`/`hlog`/`hsqrt` 的 32。宽类型在逐元素算术上持平、在超越函数与除法上反而更低，不能用“位宽翻倍”推断吞吐翻倍。

**warp 集合操作的理论档位差距明显。** warp vote 为 128，但 warp reduce 降到 64、warp shfl 全族降到 16。若 warp 内规约或洗牌落在关键路径，应将集合指令列为待测瓶颈候选，不能仅凭档位断定它主导该段时延。

**精度模式会改变前提。** `hexp`、`hlog`、`h2exp`、`h2log`、`expf`、`sqrtf` 的表中数值明确是**非高精度模式**下的理论性能。一旦要求高精度实现，这些数字不能继续当作判据。

## 从理论值到判定

按顺序回答四个问题：

1. **是否访存受限？** 先用 [Roofline 模型](../../concepts/roofline_model.md) 或 [DataCopy 对齐与搬运过冲](../ol_45_simt_solves_datacopy_alignment_overrun.md) 判断瓶颈是否已在访存侧。若是，理论并行度不参与判定。
2. **关键段是否有低档接口？** 存在 shfl（16）、数学库与除法（32）、`__cvta_*`（32）时，将其列为候选并测量执行频次与关键路径贡献；确认主导时再评估消除或移出热路径。
3. **关键段接口多为 128 档却仍不达预期？** 单指令档位不能解释整段时延；需测量访存、同步、发散、占用率和指令依赖，再决定是否改造访存、流水或指令选择。
4. **选型本身是否合适？** 若算子本质是散写、原子累加或逐元素间接寻址，选型由 [SIMD/SIMT 选型决策](../../concepts/simt_vs_simd_decision.md) 与 [P-P9 选型规则](../p_p9_simd_vs_simt_selection.md) 决定；SIMT 已选对但吞吐仍低时，再评估切换到 SIMD 的另一条实现（[Membase vs Regbase](../ol_196_membase_vs_regbase_simd_vf_selection.md)）。

## 失效边界

- 平台仅 `950`；其他产品型号不适用本卡档位结论。
- 软仿与多指令拼接接口没有理论值，本卡不对其给出上限判断。
- 理论并行度不含访存、同步、发散、占用率、调用频次与混合指令调度，不能用于端到端时延预测或单凭低档接口证明瓶颈。
- 高精度模式下的超越函数不能套用非高精度数值。
- 文档未提供任何实测标定，本卡也不给“理论达成率”结论。

## 相邻卡分工与明细

| 卡片 | 分工 |
|---|---|
| [SIMT 指令理论性能汇总（镜像卡）](../../apis/appendix/simt_instruction_theoretical_perf_summary.md) | 逐接口完整数值，本卡不复述 |
| [SIMT (L3) 编程模型](../ol_150_simt_l3_programming_model.md) | 线程组织、`LAUNCH_BOUND`、`VF_CALL` 写法 |
| [SIMD/SIMT 选型决策](../../concepts/simt_vs_simd_decision.md) | 何时选 SIMT 而非 SIMD |
| [Membase vs Regbase](../ol_196_membase_vs_regbase_simd_vf_selection.md) | SIMD 内部两条实现的取舍 |
| [基准测试方法论](../bench_methodology_profiling_first.md) | 理论值与实测的差距如何同条件验证 |
