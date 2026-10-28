---
type: Optimization
title: Reg矢量计算接口的发射能力与理论吞吐口径（Ascend 950PR/950DT）
description: 在 Ascend 950PR/950DT 上按接口、类型和工作量选取单指令理论并行度，筛查单双发模式及端口约束；同位宽单 VL 的拍数换算和循环成本合成仅为附加假设下的推导参考，不构成实际耗时界限，瓶颈须实测。
tags:
- task.optimization
- topic.performance.analysis
- topic.programming_model.execution_model.simd
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/reg_vector_compute_interface_theoretical_perf_summary.md
  role: primary
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/reg_vector_compute_interface_instruction_single_dual_issue_summary.md
  role: primary
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/c_api_reg_vector_compute_theoretical_perf_summary.md
  role: supporting
created_at: '2026-10-23T02:00:00Z'
updated_at: '2026-10-23T08:55:34Z'
platforms:
- '950'
---

# Reg矢量计算接口的发射能力与理论吞吐口径（Ascend 950PR/950DT）

本卡引用的两份理论性能表与一份单双发表都声明仅对 **Ascend 950PR&950DT 系列产品**生效；理论性能表不提供软仿实现的接口和数据类型的理论性能，单双发表不包含软仿类接口。表中 `P` 与 MaskReg 耗时是来源的单指令理论值；下文的每 VL 拍数与循环成本是按假设推导的示例值，均非实测。

## 触发条件：什么时候该用本卡而不是直接调参

- 你在写或改一条 RegBase / MicroAPI（`RegTensor` + `LoadAlign`/`Add`/`StoreAlign` 形态）的 VF 循环，想比较接口、类型或搬入模式的理论吞吐口径。
- 你已经排除或尚未排除访存受限，需要一个**理论吞吐成本参考值**作为对照基线。
- 你在两个写法之间选型（换接口、换 dtype、换对齐/搬入模式），想知道哪个改动动的是"每拍能出多少元素"这一档，而不是靠试。

如果问题是"这两个相邻的 Load/Compute 到底会不会真的同拍发射"，来源给不出保证，只有本卡第 2 节的类别判定与端口约束；不要把它当成承诺。

## 优化方法

### 1) 先用理论并行度把每个接口折算成"每 VL 拍数"

来源对大部分 RegTensor 接口给出**理论并行度（elements/cycle）**，另对 MaskReg 搬入/搬出/计算的指定行给出**理论耗时（cycle）**；`Compare`、`Unsqueeze` 等涉及 MaskReg 的行仍按表列的 elements/cycle 读取，不能仅按类型名混算。

单双发表明确 `1 个 VL 为 256B`。对工作量确实为单个同位宽 VL 的行，可用 `256 / sizeof(dtype)` 计算元素数；跨位宽、双寄存器或其他模式必须先确认实际工作量。以下仅是吞吐等效换算，非来源报告的指令延迟或占用：

```
每个 VL 的占用拍数 c = (256 / sizeof(dtype)) / P
```

其中 `P` 是该 (接口, 源dtype, 目的dtype) 行的理论并行度。在上述单 VL 假设下，`c = 1` 或 `8` 分别表示工作量除以理论并行度所得的 1 或 8 cycle 等效成本；不证明指令实际执行了相应拍数。

只对同位宽单 VL 的代表行展示换算；`P` 来自来源，`c` 为本卡推导值，不能外推到其他模式：

| 每 VL 拍数 | 代表行（接口 / 源 dtype → P） |
| --- | --- |
| 1 | 连续对齐 `LoadAlign` / `StoreAlign`（b8 → 256、b16 → 128、b32 → 64）；`Add`（half → 128、float → 64）；`Max`（int8_t → 256、half → 128、float → 64）；`Move`（b64 → 32）；`Compare`（int8_t → MaskReg，P = 256；按 256 个 int8_t 输入元素计算） |
| 2 | 非连续对齐 `LoadAlign`（b8 → 128、b16 → 64、b32 → 32）；`GatherB`（b8 → 128、b16 → 64、b32 → 32、b64 → 16）；`Add`（int8_t → 128、int16_t → 64、int32_t → 32）；`Mull`（int32_t → 32）；`Arange`（int8_t → 128） |
| 4 | `Div` / `Exp`（float → 16） |
| 5 | `Squeeze`（int8 → 51.2、int16 → 25.6、int32 → 12.8，三档折算后**恰好都是 5**） |
| 8 | `Div` / `Exp`（half → 16）；`StoreUnAlignPost` 与 `LoadUnAlignPre`（b8 → 32、b16 → 16、b32 → 8，仅假设相应阶段各处理一个完整 VL） |

三条容易踩的读表规则：

- **跨 dtype 比较必须回到 `P`，不要比 `c`。** Exp 在 half 与 float 下 `P` 都是 16 elements/cycle，元素吞吐完全相同；`c` 却是 8 与 4，差别只来自一个 VL 装了多少元素。只有当你关心"要发多少条指令、占多少拍"时才用 `c`。
- **`Cast` 必须同时核对源/目的位宽及工作量。** 未确认每次转换覆盖的元素数前，只引用来源的 elements/cycle，不把它换算为每条指令的固定拍数。
- **跨位宽不能套上表的 `c`。** `Pack`、`UnPack`、`Unsqueeze`、`Histograms`、`ExpSub`（half→float）及 `Reduce` SUM（int16→int32）只按来源的源/目的类型和 P 读表；若已知处理 `n` 个元素，才能算 `n / P`，不得默认输入和输出均为一个 VL。
- **`Gather` 依赖调用形态与源/目的组合**：离散搬入表 b8→b16、b16→b16、b32→b32 的 P 分别为 64、64、32；离散操作表 b8→b8、b16→b16、b32→b32 的 P 为 64、32、16。两表未声明相同工作量，不能直接判定互相矛盾。

MaskReg 类接口单独记账：MaskReg 搬入（LoadAlign）1 cycle、MaskGenWithRegTensor 4 cycles、MaskReg 搬出（StoreAlign / 非对齐 StoreUnAlign）各 1 cycle，以及 MaskReg 计算的 Move / Interleave / DeInterleave / Select / Pack / UnPack / MoveMask 各 1 cycle。这些不再做 `c` 折算。

### 2) 再用单发/双发分类筛选可折半的候选成本

来源的定义：**单发 = 1 个 Cycle 能执行一条指令；双发 = 1 个 Cycle 能执行两条指令。** 同一个来源还给了两条端口级硬约束：

- **寄存器：1 个 Cycle 只能写两个 Reg 寄存器**；
- **Unified Buffer（UB）：1 个 Cycle 只能读两个 VL，或者 1 个 Cycle 读一个 VL 和写一个 VL。**

来源没有给出"写两个 VL"的端口容量；不能假定两条写 UB 的搬出能同时占用这个端口。Reg 数据搬出类的接口（连续/非连续对齐搬出、连续非对齐搬出、StoreUnAlignPost、MaskReg 的 StoreAlign 与 StoreUnAlign、Scatter）也都列在单发表中；但单发分类与端口说明没有逐对列出指令组合，不据此断言任意两条搬出指令的实际同拍行为。

来源按硬件指令名和接口形态列出两类。这只是候选分类，不等于当前 VF 循环一定能同拍发射，也不等于可把该接口的 `c_i` 直接折半：还必须核对实际工作量、数据依赖、端口资源和指令映射。下列是表中适用模式的摘要，不表示某接口的所有重载、类型和调用模式均属于同一类。

**可双发（表 1 摘要）**：`CreateMask`、`UpdateMask`；**连续对齐搬入（LoadAlign）的单搬入模式**（`DIST_DS_B8`、`DIST_DS_B16` 分布模式除外）；连续非对齐搬入初始化（LoadUnAlignPre）与搬入（LoadUnAlign）；MaskReg 搬入；Move（Reg 数据搬入）；MaskReg 计算的 Move / Select / MoveMask；表列基础算术、逻辑计算、复合计算、比较与选择、类型转换、数据填充与 Arange 指令。须回表按硬件指令名确认具体形态。

**只能单发（表 2 摘要）**：非连续对齐搬入（LoadAlign）；**连续对齐搬入的双搬入模式，以及单搬入模式下的 `DIST_DS_B8`、`DIST_DS_B16` 分布模式**；MaskGenWithRegTensor；GatherB；全部 Reg 数据搬出（连续/非连续对齐搬出、连续非对齐搬出与其后处理）与 MaskReg 搬出；Scatter；MaskReg 计算的 Interleave / DeInterleave / Pack / UnPack；**全部归约**（Reduce 的 SUM/MAX/MIN、ReduceDataBlock 的 SUM/MAX/MIN、PairReduceElem）；Squeeze；数据重排的 Interleave / DeInterleave；数据压缩的 Unsqueeze / Pack / UnPack；Histograms。

`Gather` 的 `VGATHER2`（Reg 数据搬入）与 `VSELR`（离散操作）**均列在表 2 的单发表中**，不能把 `VGATHER2` 误读为可双发；两条路径与理论表的离散搬入/离散操作分别对应，但不能把两组数值跨形态混用。`LoadAlign` 连续对齐搬入的**单搬入模式（排除两种 DIST_DS 模式）**列为可双发，双搬入模式及这两种 DIST_DS 模式列为单发；选型时先确认真实调用模式，不能由接口名推定分类或收益。

### 3) 不把吞吐换算误作调度上下界

仅当循环体中每条指令的元素工作量 `n_i` 已核实、其理论表行给出 `P_i`、且所有工作量可按同一循环迭代归一化时，记等效成本 `c_i = n_i / P_i`。MaskReg 理论耗时单列，只有确认其对应每次循环的操作次数、与元素工作量的归一化口径后才可参与粗略比较。记 `S` 为表 2 的单发形态子集，`D` 为表 1 的双发形态子集：

```
串行吞吐成本参考值 = Σ c_i
假设 D 内成本可完美折半的参考值 = (Σ_{i∈D} c_i) / 2 + Σ_{i∈S} c_i
```

来源只说“理论性能均为单指令理论性能，实际性能还需考虑指令单双发情况”，**没有给出把两者合并的公式**。上面两式是本卡自建的工作量加权比较指标，不能作为实际耗时的上下界：折半式还额外假设 D 中指令可独立配对、双发后 P 所表示的执行吞吐也能叠加、端口不冲突、没有其他共享资源瓶颈；单发项与双发项的实际时间也不一定串行相加。单指令 P 不等于延迟或发射间隔，分类不证明不同类别不能重叠。只在相同假设下比较候选写法，不据此预测实际 cycle 数。

### 4) 决策规则：先核对工作量和语义，再比较候选成本

- 只能在保持任务语义、精度合同和元素工作量相同的前提下比较 P。跨接口的 12.8 与 256 不能直接解释为可替代实现的 20 倍收益；双发收益也须实测。
- 低 P 的指令（`Div`、`Exp`、`Sqrt`、`Ln`、`Log` 及 `ExpSub` 的表列行 P = 16，其中 `ExpSub` 有 half→float 形态）**也在双发表里**；但来源没有定义两条这类指令配对时是否共享执行资源、整体元素吞吐能否叠加，也没有给出换算法的收益或精度保证。不能仅凭分类按 `2 × P` 估算收益；改写或减少调用次数须另行验证语义、精度与性能。
- 表列归约、数据重排、数据压缩、直方图以及 RegTensor/MaskReg 搬出形态均在 `S` 中；这不证明它们与其他执行资源绝不重叠。两种 `Gather` 路径均列为单发。不能把任何一类默认视作免费或必然串行的开销。
- 例如 `int32_t` 的 `Add` 与 `Max` 分别为 P = 32 和 64 elements/cycle；同位宽并不意味着同吞吐，但语义不同，不可仅为 P 更高而互相替换。

## 验证方式

来源没有给出测量方法，只给了理论口径。可执行的核对步骤：

1. 用计算工具按已确认的处理元素数 `n_i` 复算 `n_i / P_i`；不同位宽转换须先确认源、目的各覆盖多少元素。留存所选原表行、单位和循环迭代工作量；上述合成式不是已验证的调度模型。
2. 读取实际指令、依赖和性能数据后再归因；实测高于参考值本身不足以排除发射受限，也可能是指令映射、工作量或双发假设不成立。
3. 复算跨 dtype 的结论时回到 `P`；复算 MaskReg 类接口时回到来源的 cycle 数，不要混算。
4. 寄存器数量上限与超限后果见[Reg数据类型定义](../../apis/simd_api/c_api/defs/type/data_type_definition.md)：RegTensor、MaskReg 超限可能写入预留 UB 并劣化性能，非对齐寄存器超限会报错，`addr_reg` 超限可能劣化性能；不能统一描述为换入换出并插入同步指令。

指标口径本身有陷阱（哪些 tick 才算"未发射"、分母跨核重复统计等），先把采集范围核对清楚再谈发射，见[SIMD VF 指标的分母、发射停顿与代码形态](../../guides/performance/simd_vf_metric_denominators_and_issue_stalls.md)。

## 失效边界

- **平台**：两份理论性能表与单双发表都只声明对 Ascend 950PR&950DT 生效。本卡的任何数字都不可外推到其它型号。
- **软仿**：软仿实现的接口和数据类型不提供理论性能；单双发表也不包含软仿类接口。软仿路径不适用本卡。
- **理论≠实测**：`P` 与单双发属于不同维度的单指令理论信息。实际耗时还受访存、同步、依赖、寄存器容量及指令映射影响；本卡的自建合成式不提供实际耗时界限或收益保证。
- **局部与整体不同**：局部链的假设成本变化不等于整体 kernel 收益；[ol_245 的实测记录](../ol_245_simd_chains_regbase_vs_membase.md)只说明该实验的摊销与占比情况，不能移植其倍率。
- **Gather 形态**：理论表将离散搬入（b8→b16 64、b16→b16 64、b32→b32 32）与离散操作（b8→b8 64、b16→b16 32、b32→b32 16）分列；单双发表分别将 Reg 数据搬入 `VGATHER2` 和离散操作 `VSELR` 列为单发。按形态、源/目的类型选行，不跨表合并 P 或假定同一工作量。
- **不要按对称性推定缺失行**：C-API 表中 `asc_max_scalar` 列出了 `bfloat16_t`，而 `asc_min_scalar` 的 `bfloat16_t` 行在来源中不存在。这类缺行应按"来源未声明"处理，回源核对后再用。
- **非整数 `P`**：`Squeeze` 的表列 P 为 51.2 / 25.6 / 12.8 elements/cycle；假设相应同位宽单 VL，算术换算均为 5 cycle 等效成本，不是来源保证的指令耗时。不要提前取整 P。
- **口径不可跨源混算**：核级算力天花板（按核数 × 每拍 FLOPS × 频率推出）与本卡的"每指令 elements/cycle"不是同一口径，本卡不做换算；要核级天花板请看[Roofline Model](../../concepts/roofline_model.md)。
- **本卡不做重复卡**：单双发的完整接口明细在[Reg矢量计算接口指令单双发汇总](../../apis/appendix/reg_vector_compute_interface_instruction_single_dual_issue_summary.md)，理论性能的完整数值表在[Reg矢量计算接口理论性能汇总](../../apis/appendix/reg_vector_compute_interface_theoretical_perf_summary.md)与[C-API-Reg矢量计算接口理论性能汇总](../../apis/appendix/c_api_reg_vector_compute_theoretical_perf_summary.md)。本卡只给"怎么读取这两张表并避免错误合成耗时界限"的方法与边界，不复述明细。

## 与相邻卡的分工

- [VF 融合、存活寄存器与循环展开的取舍](../vector/fusion_liveness_and_unrolling.md)：它讲融合/展开/寄存器存活的定性取舍，并明确拒绝承诺"展开就能双发"和具体倍数。**分工**：本卡补上它刻意不断言的那一半——官方给出的单双发类别与每指令理论并行度，以及由此可算的吞吐成本参考；至于展开后到底能不能配对成功，仍以那张卡的"看实际产物与量测"为准。
- [ol_245：regbase 与 membase 的 SIMD 链选型](../ol_245_simd_chains_regbase_vs_membase.md)：其中的测量只适用于其记录的测试条件；本卡给单指令理论读表方法，比较整体收益仍需在目标场景量测。
- [指令双发优化（指南镜像）](../../guides/operator_practice/simd_operator_optimization/vector_compute/vf_optimization/dual_issue_optimization.md)：它讲编程手法（拆分 VF 循环、手动展开、布尔代数省寄存器）。**分工**：它回答"代码怎么写"，本卡回答"写完之后吞吐成本怎么估、哪些指令根本不进双发预算"。
- [SIMD VF 指标的分母、发射停顿与代码形态](../../guides/performance/simd_vf_metric_denominators_and_issue_stalls.md)：它约束"指标怎么读"。**分工**：本卡是理论侧，它是测量侧；先按它的要求核对分母与采集范围，再来和本卡的理论吞吐参考对照。
- [issue-bound 下 work-efficient scan 反模式](../../runbooks/performance/work_efficient_scan_loses_on_issue_bound_vector_unit.md)：该 draft Runbook 的观测不证明本卡合成式是硬件调度模型；本卡只提供固定官方表的读表边界。
- [Reg数据类型定义](../../apis/simd_api/c_api/defs/type/data_type_definition.md)：它给 `VL = 256B` 的寄存器类型划分、`256/sizeof(dtype)` 的换算依据，以及 RegTensor/MaskReg/`addr_reg`/非对齐寄存器的数量上限。**分工**：本卡用它的换算做 `c` 折算，寄存器上限与复用规则以那张卡为准。
