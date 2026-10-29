---
type: Runbook
title: Memory/Reg 矢量接口边界值输入验收（含原子操作与掩码）
description: Memory 与 Reg 矢量接口、原子操作、Mask 四份边界值来源的平台范围与表列口径各不相同：Memory/Reg 与原子按「INF/NAN 模式 / 饱和模式」双列，Mask 则只给 isSetMask 支持矩阵。本卡给出逐族取期望的判定步骤、按产品、模式和具体接口表取期望的校验法、Normal 连续/逐比特与 Counter 模式的区分，以及「先小数组后真实 shape」的验收顺序。
tags:
- task.testing
- topic.implementation.masking
- topic.alignment
- topic.precision
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/memory_vector_compute_interface_boundary_value_summary.md
  role: primary
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/reg_vector_compute_interface_boundary_value_summary.md
  role: primary
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/atomic_operations_interface_boundary_value_summary.md
  role: supporting
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/Mask_interface_summary.md
  role: supporting
created_at: '2026-10-28T08:00:00Z'
updated_at: '2026-10-28T08:00:00Z'
platforms:
- '950'
- a3
- a2
---

# Memory/Reg 矢量接口边界值输入验收（含原子操作与掩码）

## 适用范围

四份来源的平台声明不是同一个集合，**不能把任一份的行套到另一份的平台上**：

| 来源 | 声明生效平台 | 覆盖内容 |
|---|---|---|
| Memory 矢量边界值汇总 | Atlas A3、Atlas A2 | 各类 Memory 矢量接口的双模式边界值表，另含一张"输出 inf/nan 场景总结" |
| Reg 矢量边界值汇总 | Ascend 950PR&950DT | 各类 Reg 矢量接口的双模式边界值表，**无**汇总场景表，直接按接口族分节 |
| 原子操作边界值汇总 | Atlas A3、Atlas A2 | SetAtomicAdd / SetAtomicMax / SetAtomicMin 三张双模式表 |
| Mask 接口汇总 | Atlas A3、Atlas A2 | 各接口 `isSetMask` 模板参数支持情况矩阵 |

本卡判定"边界值输入下的期望输出与验收顺序"；精度档位、denormal、ulp 与软仿差异另有专卡（见分工）。**source 未涉及 denormal/subnormal**，本卡不写该口径。

## 第一步：先确定跑的是哪种模式

Memory 矢量、Reg 矢量、原子操作三份来源都按同一套二分给出结果，但列名和覆盖程度不同：

- **INF/NAN 模式（非饱和模式）**：计算结果为 inf / -inf / nan 时按原样输出；**输出为整数时**，有限的超范围数值按目标类型位数截断、保留低位。
- **饱和模式**：inf 和 -inf 被饱和为 MAX 和 MIN 输出，nan 被饱和为 0 输出；输出为整数时，超范围有限值被饱和为目标类型的最大值/最小值。
- 饱和模式按数据类型分类设置（`SaturationMode::FLOAT` / `INT` / `CAST` / `FLOAT8` 等），各模式影响的类型与默认开关不同，见 [SetSaturationFlag](../../apis/simd_api/basic_api/special_register_access/set_saturation_flag_isasi.md)。Memory 与 Reg 汇总对此只写"按数据类型分类设置，请参考该接口"；原子操作汇总则直接给出 INF/NAN 与饱和两列。
- 来源明确声明：**绝大部分场景下 INF/NAN 模式输出与 IEEE 754 一致，不一致会在对应接口处备注**。该说明须在对应来源和接口范围内使用，不为其他族提供统一 oracle。

## 第二步：oracle 用三步法，不要单靠 IEEE 754

1. **先定位产品、接口族、dtype 与模式的来源条目**。仅当对应来源明确声明时，才用 IEEE 754 生成非饱和浮点期望；不能对所有 Reg 接口设置统一默认。
2. **核对该族的汇总表与具体接口表**。Memory 汇总有一张"浮点数计算输出 inf/nan 的场景"表，列出的例外包括：`exp(-inf)=0`；`inf * 0 = nan`；`inf + (-inf) = nan`；非 nan 且非 0 的值除以 0（如 Div / Sqrt / Reciprocal 一类）得到 inf；`ln(0.0) = -inf`、`ln(-0.0) = -inf`；`rsqrt(0.0) = inf`、`rsqrt(-0.0) = -inf`；`(-inf) - (-inf) = nan`。另注：nan 不区分正负，inf 区分正负。
3. **再逐接口查备注**：来源把"与 IEEE 754 不一致"的披露责任放在具体接口条目上。只按 1、2 两步批量套，遇到有备注的接口会得到假失败。

注意 Reg 汇总**没有**这张汇总例外表——它的例外只能在各接口族的表内逐条看到。把 Memory 的例外表当成两族共用，会漏掉 Reg 侧接口级差异。

## 第三步：把"掩码"拆成三层再判

**(a) 接口形态**：`isSetMask` 的支持矩阵按「Tensor 前 n 个数计算」与「Tensor 高维切分计算」两种形态分列，同一接口在两种形态下可能一个是"有 isSetMask"、另一个是"无 isSetMask"。表中 `-` 表示**不存在该类型接口**，既不是"不支持"也不是"未声明"。该矩阵只对 Atlas A3/A2 声明。

**(b) 设置方式**：分为接口内已设置 Mask（内部调用 SetMaskCount / SetVectorMask / SetMaskNorm / ResetMask）、由模板参数控制（`isSetMask=true` 接口内设置；`false` 由调用方在接口外设置）、以及接口不支持或无需设置 Mask 三类。逐接口归属见 [Mask 接口汇总](../../apis/appendix/mask_interface_summary.md)。

**(c) 两个易错点**：
- **"有 isSetMask 但不起作用"**：Compare 与 Select 的高维切分形态即属此类。这类接口不能靠外部 `SetVectorMask` 改变参与计算的元素；Select 要在外部设掩码，须改用不传 mask 参数的重载。
- **全 1 与全 0 不对称**：`ResetMask` 把 mask 恢复为默认值**全 1**，语义是"每次迭代内所有元素都参与运算"（见 [ResetMask](../../apis/simd_api/basic_api/memory_vector_compute/mask_operations/reset_mask.md)）。全 0 掩码的专门行为在四份来源中**均无条款**，本卡不给出期望值，需按目标接口文档另行确认。

## 第四步：区分"元素数"与"逐比特"

这不是同一个参数的两种叫法，而是**先选模式、再选含义**：

- **Counter 模式**（[SetMaskCount](../../apis/simd_api/basic_api/memory_vector_compute/mask_operations/set_mask_count.md)）：mask 表示**整个矢量计算参与计算的元素个数**；此模式不需要开发者感知迭代次数、也不需要处理非对齐尾块，迭代次数由 Vector 单元自动推断。
- **Normal 模式**（[SetMaskNorm](../../apis/simd_api/basic_api/memory_vector_compute/mask_operations/set_mask_norm.md)）：系统默认模式，支持开发者配置迭代次数。该模式下 mask 有**两种含义**（[SetVectorMask](../../apis/simd_api/basic_api/memory_vector_compute/mask_operations/set_vector_mask.md)）：
  - **连续模式**：前面连续多少个元素参与计算。取值范围随操作数位宽变化：16 位 `[0,128]`、32 位 `[0,64]`、64 位 `[0,32]`。
  - **逐比特模式**：按位控制，bit=1 参与。16 位时 maskHigh/maskLow ∈ `[0,2^64-1]` 且不同时为 0；32 位时 maskHigh=0、maskLow ∈ `[0,2^64-1]`；64 位时 maskHigh=0、maskLow ∈ `[0,2^32-1]`。

验收含义：**来源推荐使用 Counter 模式处理长度非对齐与尾块**（把元素总数直接传入，由硬件推断迭代），并非所有接口的强制要求。手动管理须先确认目标重载允许 `isSetMask=false`，计算后恢复 Normal 模式。若实现选了 Normal 模式，尾块边界就变成实现责任，必须单独构造尾块用例。

## 第五步：原子操作先预置 dst 再判定

- 三张表分别对应 SetAtomicAdd / SetAtomicMax / SetAtomicMin，各给 INF/NAN 模式与饱和模式两列；表注写明**INF/NAN 模式列结果与 IEEE 754 理论结果一致**。
- 饱和模式的折叠是：inf → MAX、-inf → MIN、nan → 0，其中 MAX/MIN 是该数据类型的最大值/最小值（表中 half 为 `65504.0` / `-65504.0`；例如 `-inf + inf` 在非饱和模式为 nan、在饱和模式为 `0.0`）。
- **来源三张表的 src/dst 数据类型全部是 half**。因此本卡可断言的边界值口径仅限 half；float、整数等类型不在来源范围，不得据此外推。
- 原子语义是"新值与 dst 已有值合成"，所以用例**必须先把 dst 预置成已知边界值并在执行后读回**；否则"预置写错"与"原子计算错"在同一次失败里无法区分。跨块累加还要固定块划分，保证每次读回的 dst 只受一个累加序列影响。

## 验收顺序（先小后大，逐级锁定变量）

1. **最小 shape + 全有限已知值**：锁定 strides、offset、起始地址与读写范围。
2. **最小 shape + 单点特殊值，非饱和模式**：按对应族、dtype、模式和具体接口表取期望（第二步），不能将 Memory 汇总表套到 Reg。此级只应有"表格口径"这一类期望。
3. **同用例开饱和模式重跑**：期望改为 ±MAX / 0 折叠，结果与第 2 级分开归档，不合并通过率。
4. **放大到真实 shape**：此时失败应归因到 shape/分形/循环，而非特殊值语义；尾块按 Counter 模式或显式尾块路径单独覆盖。
5. **跨块原子累加**：预置 dst → 执行 → 读回，仅改变块划分重复一轮，确认结果与块顺序无关（或与来源声明的顺序要求一致）。
6. **掩码矩阵抽检**：全 1（ResetMask 默认）、连续 n、逐比特组合各一条；对"有 isSetMask 但不起作用"的接口单独登记，不记为失败。

## 与相邻卡的分工

- 原文镜像：[Memory 矢量边界值汇总](../../apis/appendix/memory_vector_compute_interface_boundary_value_summary.md)、[Reg 矢量边界值汇总](../../apis/appendix/reg_vector_compute_interface_boundary_value_summary.md)、[原子操作边界值汇总](../../apis/appendix/atomic_operations_interface_boundary_value_summary.md)、[Mask 接口汇总](../../apis/appendix/mask_interface_summary.md)（type=API，逐表原文）。本卡是判定流程，不复制数据表。
- [Reg 矢量接口硬件精度与软仿精度差异](../precision/reg_vector_hardware_vs_soft_simulation_precision.md)：那张卡解**精度档位 / denormal / ulp / 软仿路径**；本卡解**特殊值输入下的输出口径**。前者的 denormal 结论不能替代本卡的 inf/nan 判定，反之亦然。
- 掩码 API 语义在 [SetVectorMask](../../apis/simd_api/basic_api/memory_vector_compute/mask_operations/set_vector_mask.md)、[SetMaskCount](../../apis/simd_api/basic_api/memory_vector_compute/mask_operations/set_mask_count.md)、[SetMaskNorm](../../apis/simd_api/basic_api/memory_vector_compute/mask_operations/set_mask_norm.md)、[ResetMask](../../apis/simd_api/basic_api/memory_vector_compute/mask_operations/reset_mask.md)；本卡只用它们解释 mask 含义，不重复参数表。
- 饱和开关的取值、默认值与数据类型归类见 [SetSaturationFlag](../../apis/simd_api/basic_api/special_register_access/set_saturation_flag_isasi.md)；原子接口本身见 [SetAtomicAdd](../../apis/simd_api/basic_api/atomic_operations/set_atomic_add.md)、[SetAtomicMax](../../apis/simd_api/basic_api/atomic_operations/set_atomic_max_isasi.md)、[SetAtomicMin](../../apis/simd_api/basic_api/atomic_operations/set_atomic_min_isasi.md)。
- 尾块与对齐的搬运侧口径：[完整块与安全尾块分开选搬运路径](aligned_tile_copy_safe_tail.md)；本卡的尾块判据是 Counter 模式的元素数语义，两者互补。
- 单元素特殊值注入的框架限制：[TTK 取值域仅整张量语义](ttk_value_range_no_single_element_nan_inf_injection.md) 说明该注入在 TTK 下不物化；本卡第 2 级需改用 `manual_input_binaries` 或 C++ ST。
- 掩码参数掩盖真实错误码：[aclnn ST 掩盖 execute 错误码](aclnn_st_masks_execute_error_code_probe.md)；本卡判期望值，那张卡判错误码可见性。
- 大累加项数的精度越阈：[fp16 大累加项数跨实现 MERE 越阈边界](../precision/fp16_large_term_accumulation_cross_golden_boundary.md)；本卡只判边界值输出，不判跨实现精度阈值。

## 失效边界

- 本卡所有期望值来自固定提交中的四份 appendix 汇总，**本卡未做硬件实测**；表值是**文档值**。
- 平台范围按来源逐族限定（Memory、原子、Mask 为 A3/A2；Reg 为 950）。跨族搬用条目即越界。
- **denormal / subnormal 与地址对齐在四份来源中均无条款**：本卡不写这两类口径。对齐类问题应查接口卡；尾块口径来自 `SetMaskCount` 的 Counter 模式说明，不是来自边界值汇总。
- 原子表仅覆盖 half；float 与整数类型的边界值期望不在本卡来源内。
- 全 0 掩码无来源条款，本卡不给期望值。
- 饱和模式的默认开关因 `SaturationMode` 与数据类型而异，若用例未显式设置，实际模式可能与假设不同；每次判定都要先记录实际开关状态。
