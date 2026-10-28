---
type: Runbook
title: Reg 矢量接口硬件精度与软仿精度差异
description: Reg 矢量计算接口在「硬件指令路径」与「软仿（编译器/多指令拼接）路径」下精度标准不同：denormal 支持、ulp 档位、bf16 中间位宽与舍入、归约累加顺序、Fma 乘累加结构是差异来源。本卡给出差异清单、软仿阶段的判别步骤，以及实现路径变化必须重验的判定边界；来源限定 Ascend 950PR&950DT。
tags:
- task.debugging
- task.testing
- topic.precision
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/reg_vector_compute_interface_precision_standard_summary.md
  role: primary
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/reg_vector_compute_interface_soft_simulation_summary.md
  role: supporting
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/SIMT_interface_precision_standard_summary.md
  role: supporting
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/SIMT_interface_soft_simulation_summary.md
  role: supporting
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/compilation_and_execution/operator_compilation/ai_core_operator_compilation.md
  role: constraint
created_at: '2026-10-23T02:00:00Z'
updated_at: '2026-10-28T02:11:00Z'
platforms:
- '950'
---

# Reg 矢量接口硬件精度与软仿精度差异

## 适用场景

- 在 Ascend 950PR&950DT 上用 Reg 矢量计算接口开发或迁移算子，需要判断"这条接口在硬件路径与软仿路径下精度是否等价"。
- **来源限定**：Reg 接口的精度标准汇总与软仿情况汇总都写明"本节内容仅针对如下型号生效：Ascend 950PR&950DT 系列产品"。本文所有结论都受此限定。
- **触发信号**：精度用例卡在 0-ulp 或严格相等；输入可能落到 denormal（次正规数）区间；归约结果位级不一致；用了 bf16 算术或 Fma 类复合指令；为过用例改过编译选项。

## 先把"软仿"定义清楚

- 来源对软仿的定义（SIMT 软仿汇总）：**非软仿接口**指使用单一硬件指令完成操作的接口；**软仿接口**指由编译器实现，或由上层接口通过拼接多条硬件指令实现功能的接口。
- Reg 软仿汇总用的是同一口径：把"底层硬件不支持该数据类型"的情况列为软仿，实现方式是"通过其他位宽相同的数据类型支持的搬运指令实现""通过多种接口组合软仿实现""通过双搬入/双搬出模式软仿实现"。
- 因此本文的**硬件精度** = 操作由单条硬件指令完成时的精度标准；**软仿精度** = 同一接口由编译器或多条指令拼接实现时的精度标准。两者的差别是**实现路径**，不是"PC 侧仿真 vs 设备侧执行"。
- 编译期决定走哪条路径的开关（仅 950PR&950DT 支持）：`--cce-ftz` 默认 `true` = 把非规格化数刷为 0，`false` = 保留（精度更高、性能可能下降）；SIMD 与 SIMT 都支持，其中 **SIMD 仅支持 3510**。SIMT 侧另有 `--cce-prec-div`、`--cce-prec-sqrt` 与 `--cce-use-fast-math`（默认 `true`，等价于 `--cce-ftz=true --cce-prec-div=false --cce-prec-sqrt=false`）。
- SIMT 精度汇总明确规定其软仿精度标准在 `--cce-use-fast-math=false` 时获得；这是 SIMT 表的前提，不能外推到 Reg 表。Reg 精度汇总没有给出同一 fast-math 前提，因此 Reg 用例必须记录实际编译选项并按目标路径复核。
- 若把"软仿"理解为**离线仿真模式**（`--run-mode=sim`，链接仿真实现库；CMake 侧对应 `CMAKE_ASC_RUN_MODE` 的 `sim`，会更换链接库与编译选项）：来源只把它声明为查看仿真日志、方便性能调试的用途，没有给出它与硬件等价的任何承诺。仿真模式与 CPU 调试模式下得到的精度结论同样不能直接当作上板证据。

## 差异清单（来源两列直接对照）

下表只列两列**不一致**或只在一列出现的关键接口；"-"表示来源该列未给出标准。

| 接口 | 硬件指令精度标准 | 软仿精度标准 | 差异性质 |
|---|---|---|---|
| Exp | 1ulp, not support denormalized numbers | 1ulp, support denormalized numbers | denormal 支持相反 |
| Sqrt | 1ulp, not support denormalized | float: 0ulp；half/float: 1ulp, support denormalized | 档位 + denormal |
| Div | 1ulp, not support denormalized | complex64: 0ulp, not support denormalized；float: 0ulp, support denormalized；half/float: 1ulp, support denormalized | 档位 + denormal，且软仿按类型分档 |
| Ln / Log | 1ulp, not support denormalized | 1ulp, support denormalized | denormal 支持相反 |
| Log2 / Log10 | - | 1ulp（not support 与 support denormalized 各一条） | 硬件列未给出 |
| Add | half/float: 0ulp, support denormalized；bfloat16_t: `Add(x,y)=rint_to_bf16(Add(cast_to_f32(x),cast_to_f32(y)))` | 0ulp, support denormalized | bf16 的中间位宽语义只写在硬件列 |
| Adds | 同 Add（含 bf16 的 fp32 中间语义） | 0ulp, support denormalized | 同上 |
| Sub | `Sub(x,y)=Add(x,Neg(y))` | 0ulp, support denormalized | 语义按 Add 展开 |
| Mul | half/float: 0ulp, support denormalized；bfloat16_t: `Mul(x,y)=rint_to_bf16(Mul(cast_to_f32(x),cast_to_f32(y)))` | - | 软仿列未给出 |
| Muls | half/float: 0ulp, support denormalized | - | 软仿列未给出 |
| Neg | 符号位取反 | - | 软仿列未给出 |
| AbsSub | 指令串行：`AbsSub(x)=Abs(Sub(x))` | - | 软仿列未给出 |
| ExpSub | 输入 half 输出 float：`Exp(Sub(cast_to_f32(x),cast_to_f32(y)))`；输入 float 输出 float：`Exp(Sub(x,y))` | - | 中间位宽随输入类型切换 |
| Axpy / MulDstAdd / MulAddDst | 乘累加采用高精度计算，同比 `Fma(x,y,z)` | - | 乘累加结构写进语义 |
| MulsCast | `MulsCast(x,y)=cast_to_f16<roundingmode>(x*y)` | - | 舍入模式是语义的一部分 |
| Reduce / ReduceDataBlock | half/float: 0ulp，采用**二叉树结构的成对累加**策略 | - | 累加顺序是 0ulp 的附条件 |
| PairReduceElem | half/float: 0ulp | - | 软仿列未给出 |

## 差异的五个来源（怎么归因）

1. **denormal 支持相反**：硬件列普遍写 `not support denormalized numbers`，软仿列普遍写 `support denormalized numbers`。对应编译期就是 `--cce-ftz`（默认 `true` 刷 0）。
2. **ulp 档位不同**：Sqrt、Div 的软仿列给到 0ulp（float/complex64），比硬件列的 1ulp 更严——**多指令实现的精度标准可能更严**，若目标实际选择单指令实现，沿用另一实现的阈值可能不合适。
3. **中间位宽与舍入语义**：bf16 的 Add/Adds/Mul 在硬件列被写成 `rint_to_bf16(op(cast_to_f32(x), cast_to_f32(y)))`（fp32 中间计算再舍回 bf16）；ExpSub 按输入类型切换中间位宽；MulsCast 把 cast 的舍入模式写进语义。
4. **累加顺序 / 乘累加结构**：Reduce、ReduceDataBlock 的 0ulp 附带"二叉树结构成对累加"这一条件；Axpy、MulDstAdd、MulAddDst 是"高精度乘累加，同比 Fma"。换成顺序累加或拆成 Mul+Add 就改变了语义。
5. **只存在于软仿路径的数据类型**：Reg 软仿汇总把 fp4x2_e2m1_t、fp4x2_e1m2_t、fp8_e5m2_t、fp8_e4m3fn_t、fp8_e8m0_t、hifloat8_t 的 Cast/Duplicate 标注为软仿，另有 int64_t/uint64_t/complex32/complex64 等大量接口标注软仿支持（理由写明是"底层硬件不支持该数据类型"）。这类路径的数值行为来自软件实现，与硬件原生路径不是同一实现。

## 在目标实现路径上核对精度的步骤

1. **按实际实现选列**：先确定目标设备上该 dtype、接口和编译选项对应单指令还是多指令实现，再采用相应列标准。软仿实现同样可在设备上运行，不能一律按硬件列放宽为 1ulp 或 FTZ；若是 SIMT 软仿，还要满足来源规定的 `--cce-use-fast-math=false` 前提。
2. **构造 denormal 用例**：覆盖次正规输入、正常/次正规边界与次正规输出；按实际算法及 FTZ 配置构造 golden，不能将“not support denormalized”简化为“结果必为 0”（例如极小输入的 Exp 结果并非极小数）。
3. **归约合同限定到对应实现**：核对 Reduce / ReduceDataBlock 的硬件路径或复现该硬件合同的 golden 时，按 half/float 的 0ulp 与二叉树成对累加结构做位级核对，不要以顺序累加替代。来源软仿列为 `-`；真正软仿实现须先查其自身合同，不能凭此表强制要求 0ulp 或二叉树累加。
4. **bf16 算术显式复现式子**：按 `rint_to_bf16(cast_to_f32(x) op cast_to_f32(y))` 复核（fp32 中间 + 回舍 bf16），不要用"全程 fp32 再一次性截断"来等价。
5. **复合/Fma 类不要拆开验证**：把 Axpy/MulDstAdd/MulAddDst 拆成 Mul+Add 做等价验证会多引入一次舍入，与来源的"高精度乘累加"语义不符。
6. **核对编译选项与数据类型**：确认 `--cce-ftz`/`--cce-prec-div`/`--cce-prec-sqrt`/`--cce-use-fast-math` 的实际取值；SIMT 软仿精度标准要求 `--cce-use-fast-math=false`；该前提不外推到 Reg 表，Reg 须按实际选项验证。确认用例走的是硬件原生类型还是软仿支持表里的类型。
7. **阈值口径与 golden 对齐**：golden 侧的选择见相邻卡，不要在 golden 与接口标准两侧同时放松。

## 判定边界：某实现通过不证明另一实现通过

以下任一条件成立时，某实现通过**不构成**另一实现通过的证据；此处不是离线仿真与上板的二分：

- 结果路径只有软仿列有标准，或两列标准不同（denormal、ulp 档位）。
- 目标选择了单指令路径，输入落在 denormal 区间，而接口硬件列写 `not support denormalized numbers`（Exp/Sqrt/Div/Ln/Log 等）——须核对输入/输出及 FTZ 算法，不能把所有运算的输出直接置零。
- 阈值按软仿的 0ulp 标定，而硬件列是 1ulp（Sqrt/Div 的相应类型分档）。
- 用了 bf16 的 Add/Adds/Mul：硬件列是 fp32 中间 + `rint_to_bf16` 回舍，软仿列未声明同一式子。
- 归约类结果依赖成对累加结构，而实现改成了别的累加顺序。
- 接口或数据类型只出现在"软仿支持"表里（硬件不支持该类型，或用多接口组合实现）。

反过来说，**两列标准一致**的路径（例如 Add/Adds 的 half/float 两列都是 0ulp 且都 support denormalized numbers）仍只证明同一精度合同，不证明输出相同；可以作为选择测试合同的线索，但仍需上板复测，不能结案。

上板后如何定位差异，按 [上板精度二分定位：恒等搬运+离线数值复现](../runtime/precision_bisection_identity_copy_offline_repro.md) 的流程走。

## 与相邻卡的分工

- 来源原文的镜像卡：[Reg矢量计算接口精度标准汇总](../../apis/appendix/reg_vector_compute_interface_precision_standard_summary.md) 与 [Reg矢量计算接口软仿情况汇总](../../apis/appendix/reg_vector_compute_interface_soft_simulation_summary.md)（type=API，逐表原文）；本卡是从这两张表蒸馏出的判定规则与边界，不重复罗列全部行。
- SIMT 口径的镜像：[SIMT 接口精度标准汇总](../../apis/appendix/simt_interface_precision_standard_summary.md) 与 [SIMT 接口软仿情况汇总](../../apis/appendix/simt_interface_soft_simulation_summary.md)：本卡借用软仿的定义；SIMT 软仿精度表以 `--cce-use-fast-math=false` 为前提，该前提不外推到 Reg，SIMT 接口自身的精度迁移不在本卡。
- [大归约维 fp32 golden 顺序累加致假精度失败](fp32_golden.md)：那张卡解 golden 与 kernel 的**累加顺序/精度**差异（含 double/pairwise golden 判别法）；本卡解**同一接口硬件列与软仿列标准**的差异。两者都与累加顺序有关，但一个在 golden 侧、一个在接口标准侧。
- [bf16 扩精度 Cast 误用 CAST_RINT 产垃圾值判别](bf16_cast_cast_rint.md)：那张卡管 Cast 的 RoundMode 方向语义；本卡管 bf16 **算术指令**的中间位宽声明差异，不重复 RoundMode 选择。
- [FloatToFp16 denormal 路径截断致 1-ULP 偏差](floattofp16_denormal_truncate_1ulp.md)：那是一处具体实例（测试侧软浮点 denormal 分支截断 vs 硬件 Cast）；本卡是汇总表层面的系统性差异与判定边界。
- [Exp 默认 INTRINSIC FTZ 致 subnormal 残留失配](exp_intrinsic_ftz_subnormal.md)：那张卡是 Exp 单接口的实测判别；本卡给通用条目与步骤。
- [数据类型与精度保护（910_95 平台）](../../../triton/optimizations/techniques/data_type_precision.md)：Triton 与 910_95 口径，平台不同，不要互相套用。

## 失效边界

- 本卡所有精度标准都来自固定提交中的来源表，**本卡未做硬件实测**；来源限定 Ascend 950PR&950DT 系列产品，其它平台不适用。
- 来源表中的"-"按"该列未给出标准"处理：既不能读成"两列相同"，也不能读成"该接口不是软仿"。
- SIMT 精度汇总明确要求软仿精度标准使用 `--cce-use-fast-math=false`；Reg 精度汇总没有给出同一统一前提，应记录并核对实际编译选项，不能将 SIMT 表的前提外推到 Reg。
- 精度标准是"标准"，不是实测上限：实现可能优于标准，也不能据此推断某个具体实现的实际误差。
- 同平台的 SIMT API 在 CANN 9.2.0 有过实现层面的精度提升，并提供 `ASCENDC_USE_LEGACY_PRECISION` 回退到旧实现（仅 950PR&950DT）。这说明"接口实现版本"本身也是精度变量；本卡的 Reg 两列标准没有按 CANN 版本分档，跨 CANN 版本比较时要重新确认。
- 本卡聚焦 Reg 矢量计算接口；同一平台上其它接口族的精度行为不在本卡范围。
