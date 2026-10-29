---
type: Runbook
title: Mmad 与 MmadMx 边界值输入验收与失败归类
description: Mmad/MmadMx 在 inf、nan、dtype 极值、零维与量化类型入参下的期望输出口径不同：两族加法阶段的正负 inf 相加结果相反，量化类型会在入参侧折叠 inf/nan。本卡给出按接口族与饱和模式分列的判定步骤、双 oracle 校验法与四类失败归因顺序；来源限定 Mmad 为 950/A3/A2、MmadMx 为 950。
tags:
- task.testing
- topic.precision
- topic.programming_model.execution_unit.cube
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/mmad_interface_boundary_value_summary.md
  role: primary
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/mmad_mx_interface_boundary_value_summary.md
  role: primary
created_at: '2026-10-28T08:00:00Z'
updated_at: '2026-10-28T08:00:00Z'
platforms:
- '950'
- a3
- a2
---

# Mmad 与 MmadMx 边界值输入验收与失败归类

## 适用范围

- **接口族与平台不是同一集合**：`Mmad` 边界值汇总声明对 Ascend 950PR&950DT、Atlas A3、Atlas A2 生效；`MmadMx` 汇总只声明 Ascend 950PR&950DT。把 MmadMx 的条目用到 A2/A3，或反过来，都是越界推断。
- 适用任务：为 MMAD 类矩阵乘接口补特殊值用例、判定一次边界值失败是"输入越界/模式没开对"还是"实现缺陷"。
- **本卡来源只有两份 appendix 汇总**（见 `sources`）。接口约束、地址对齐、尺寸语义来自相邻接口卡，正文中按链接逐条标注，不并入本卡断言；对齐类条款不在本卡来源范围内。

## 第一个变量是"饱和模式"，不是"接口"

两份汇总的表列口径并不相同，混读会直接算错期望值：

- **Mmad 汇总只给 INF/NAN 模式（非饱和模式）一张表**，表注写明"INF/NAN 模式（非饱和模式）下……"。该表**没有**饱和模式列，饱和模式的输出不能从这张表推。
- **MmadMx 汇总同时给两张**：INF/NAN 模式边界值表，以及独立的「饱和模式边界值汇总」段落（先饱和再按数值计算）。
- 饱和开关属于控制寄存器/接口配置，不在本卡表格内；取值与默认值见 [SetSaturationFlag](../../apis/simd_api/basic_api/special_register_access/set_saturation_flag_isasi.md) 与 [Mmad](../../apis/simd_api/basic_api/cube_compute_isasi/mmad_compute/mmad.md) 的「特殊值/边界值约束说明」。验收时必须先记录本次用例跑的是哪种模式。

## 两族最容易互套错的一条：加法阶段的正负 inf

| 场景（加法阶段） | Mmad 期望 dst | MmadMx 期望 dst |
|---|---|---|
| A=+inf，B=-inf | **nan** | **-inf** |
| A=-inf，B=+inf | **nan** | **+inf** |

两族在乘法阶段的口径一致（inf×非零→±inf、inf×0→nan、含 nan→nan、溢出按正负给 ±inf），**差异只在加法阶段**。因此跨接口复用期望值时，乘法点可以复用，加法点必须逐族重取。MmadMx 的这条与 IEEE 754 的"inf + (−inf) = nan"也不一致，不能用 IEEE 754 反推。

## 量化类型：inf/nan 在"入参侧"就被折叠

MmadMx 支持的低精度量化类型没有完整的 inf/nan 表示，边界值会先被换成有限数值，再去计算：

- `fp4x2_e1m2_t` / `fp4x2_e2m1_t` 无 ±inf/nan 定义：+inf → `1.75` / `6`，−inf → `-1.75` / `-6`，nan → `0.0`。
- `fp8_e4m3fn_t` 只有 nan 定义、无 ±inf 定义：+inf / −inf 都被转换为 nan。

验收含义：如果用例在**入参侧**注入 inf 并期望输出 ±inf，量化类型下该期望本来就错——注入点先折叠，实际参与运算的是有限值。这类用例应按"入参折叠后"重新计算期望，而不是记为失败。

## 来源内部存在张力的一处：nan 输入

MmadMx 汇总的边界值表给出"nan 输入 → nan 输出"，但同一份来源的「边界值说明」又写"MmadMx 计算应避免 nan 输入，否则可能会产生执行报错"。二者不能同时当作无条件结论。验收取更严口径：**nan 输入不写成"必须正常输出 nan"的正向用例**；确需覆盖时按"允许报错"单独登记，并记录报错信息，不计入功能失败。

## 判定步骤（按序执行）

1. **先判是不是 NOP**：按 [Mmad](../../apis/simd_api/basic_api/cube_compute_isasi/mmad_compute/mmad.md) 与 [MmadMx](../../apis/simd_api/basic_api/cube_compute_isasi/mmad_compute/mmad_mx.md) 的约束说明，M、K、N 任一为 0 时指令不执行（空操作）。K=0/N=0 用例的期望是"输出保持原值/不被改写"，不是"输出 0"；若 dst 被清零，先查是不是用例自己的预置或清零步骤造成的。
2. **再判模式**：确认饱和开关的实际状态，并与所用表列对齐。用 Mmad 表去核对饱和模式结果，或用 MmadMx 饱和段去核对 INF/NAN 模式结果，都会得到假失败。
3. **再判量化折叠**：确认 A/B 的实际 dtype。若为 `fp4x2_*` 或 `fp8_e4m3fn_t`，先把注入的 inf/nan 按上节折叠，再重算期望。
4. **再判尺寸/分形边界**：M/K/N 非 16 的倍数时，无效数据会占满分形空间但不参与计算（见 [Mmad](../../apis/simd_api/basic_api/cube_compute_isasi/mmad_compute/mmad.md) 约束说明）。期望值只按有效形状算；把无效区数值纳入比对会产生假失败。
5. **最后才判实现缺陷**：以上四项都排除后，才把"逐元素与表列期望不符"记为实现问题，并附上模式、dtype、M/K/N、注入点和期望来源条目。

## 验证方式

- **双 oracle**：期望值有两条独立来源——IEEE 754 与来源表列。两者冲突时以**表列为准**并按族记录（加法阶段正负 inf 即典型冲突点）。两族都一致的点，才可用 IEEE 754 批量生成期望。
- **单元素优先**：先在最小形状（能覆盖一个 16×16 分形的最低维度）上单点注入特殊值，确认该点行为后再放大。放大后若失败，差异必然来自 shape/分形/循环边界而非特殊值语义。
- **一模式一跑**：非饱和与饱和模式各跑一轮同一用例集，两轮结果分开归档；不要把两轮混在同一份通过率里。
- **对齐前置不在本卡**：地址对齐（dst L0C 1024B、A/B 512B、bias 64B）与 K 方向对齐开关 `kDirectionAlign`（仅 float 相关，`ceil(K/8)*8` 或 `ceil(K/16)*16`）见 [Mmad](../../apis/simd_api/basic_api/cube_compute_isasi/mmad_compute/mmad.md) 与 [K方向对齐约束](../../apis/simd_api/basic_api/cube_compute_isasi/mmad_compute_key_features/k_direction_alignment_constraint.md)。本卡只判定"边界值输入"，不判定对齐违规。

## 与相邻卡的分工

- 原文镜像：[Mmad 接口边界值汇总](../../apis/appendix/mmad_interface_boundary_value_summary.md)、[MmadMx 接口边界值汇总](../../apis/appendix/mmad_mx_interface_boundary_value_summary.md)（type=API，逐表原文）。本卡是判定流程与失败归因，不复制全部行。
- 尺寸/对齐/同步等接口约束在 [Mmad](../../apis/simd_api/basic_api/cube_compute_isasi/mmad_compute/mmad.md)、[MmadMx](../../apis/simd_api/basic_api/cube_compute_isasi/mmad_compute/mmad_mx.md) 与 [K方向对齐约束](../../apis/simd_api/basic_api/cube_compute_isasi/mmad_compute_key_features/k_direction_alignment_constraint.md)；本卡不重复其参数表。
- 饱和开关语义见 [SetSaturationFlag](../../apis/simd_api/basic_api/special_register_access/set_saturation_flag_isasi.md)；本卡只用它区分模式，不展开各 `SaturationMode` 的适用范围。
- 用例构造侧限制：[TTK 取值域仅整张量语义，单元素NaN/Inf注入用例壳不物化](ttk_value_range_no_single_element_nan_inf_injection.md) 说明单元素注入在 TTK 下不物化。本卡的"单元素优先"需走 `manual_input_binaries` 或 C++ ST。
- 参考值生成本身会溢出：[case_gen 极端量级分布产 overflow/underflow 参考值](case_gen_extreme_magnitude_distributions_overflow_refs.md) 是 golden 侧问题；本卡是接口侧期望口径。
- 实现侧 inf 传播陷阱（算法引入 inf−inf）见 [Two-Product split 遇 inf 产 NaN 破坏 inf 传播](../precision/two_product_split_inf_nan_pollution.md)，与本卡的接口期望判定互补。

## 失效边界

- 本卡所有期望值来自固定提交中的两份 appendix 汇总，**本卡未做硬件实测**；表值是**文档值**，不是实测上限。
- Mmad 的饱和模式输出**不在本卡来源内**（该汇总只给 INF/NAN 模式表）：饱和模式验收必须回到接口卡与 `SetSaturationFlag`，不能引用本卡表格。
- 上述例外（inf×0、inf+(−inf)）与"溢出按正负取 ±inf"是该两份汇总的声明；接口若另有备注，以接口卡为准。
- 平台范围按族限定：Mmad 为 950/A3/A2，MmadMx 仅 950。MmadMx 条目不可外推到 A2/A3。
- 本卡不覆盖 dtype 转换（Cast）过程中的边界值行为，也不覆盖 Fixpipe 搬出阶段的量化饱和。
