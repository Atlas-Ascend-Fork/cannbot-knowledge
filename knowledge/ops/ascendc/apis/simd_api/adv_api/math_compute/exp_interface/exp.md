---
type: API
title: Exp
description: 按元素取自然指数，可选择是否使用泰勒展开公式进行计算
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Exp_interface/Exp.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Exp

按元素取自然指数e^x。可通过模板参数taylorExpandLevel选择是否使用泰勒展开公式：项数为0表示不使用泰勒公式，项数不为0时使用泰勒展开（将输入拆分为整数部分xA和小数部分xB分别处理）。模板参数T支持half/float。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetExpMaxMinTmpSize获取。

模板参数taylorExpandLevel为泰勒展开项数，取值范围[0, 255]，推荐[10, 15]；项数越多精度越高但性能越差，项数太少会有精度误差。isReuseSource仅在float时生效，true表示允许复用srcLocal内存空间。接口参数：dstLocal为输出操作数；srcLocal为输入操作数，TPosition支持VECIN/VECCALC/VECOUT，数据类型需与dstLocal一致；sharedTmpBuffer为临时缓存；calCount为参与计算元素个数。

约束：不支持源操作数与目的操作数地址重叠；不支持sharedTmpBuffer与源/目的操作数地址重叠；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [Ascend950 向量管 FTZ 刷新次正规 exp 为零](../../../../../runbooks/precision/ascend950_ftz_exp.md)（`exemplifies`）：Ascend950 向量管 FTZ 刷新次正规 exp 为零 与《Exp》的实质衔接是：该卡锁定 Ascend950 Exp 次正规输出 FTZ；Exp 接口、clamp/overflow/subnormal 姊妹故障和 softplus 极值用例共同验证硬件边界与可修软件因素。
- [Exp 默认 INTRINSIC FTZ 致 subnormal 残留失配](../../../../../runbooks/precision/exp_intrinsic_ftz_subnormal.md)（`exemplifies`）：Exp 与《Exp 默认 INTRINSIC FTZ 致 subnormal 残留失配》的实质衔接是：这些卡直接给出 Exp 的高阶、基础、Reg 与 C 入口及其临时空间契约；所连排障卡均以 Exp 的溢出、下溢、FTZ 或 clamp 行为作为精度根因和修复对象。
- [Maxs 下限 clamp 阻止 exp 自然下溢残留](../../../../../runbooks/precision/maxs_clamp_exp.md)（`exemplifies`）：Exp 与《Maxs 下限 clamp 阻止 exp 自然下溢残留》的实质衔接是：这些卡直接给出 Exp 的高阶、基础、Reg 与 C 入口及其临时空间契约；所连排障卡均以 Exp 的溢出、下溢、FTZ 或 clamp 行为作为精度根因和修复对象。
- [Reciprocal 低精度致 sigmoid 比对失败](../../../../../runbooks/precision/reciprocal_sigmoid.md)（`exemplifies`）：《Reciprocal 低精度致 sigmoid 比对失败》说明AscendC::Reciprocal 为低精度查表近似指令（相对误差约 1e-3），sigmoid 的 1/(1+exp(-x)) 用其求倒数会让 verify_result.py 报 max_diff≈0.00179、16384/16384 全 mismatch；判别方法：把最后一步 Reciprocal 换成 Duplicate+Div 高精度除法后 max_diff 降为 0，即可单点归因到 Reciprocal 的低精度近似。；《Exp》说明按元素取自然指数，可选择是否使用泰勒展开公式进行计算。二者在该失败由Reciprocal近似误差进入sigmoid末步；高精度Div替换及Exp溢出/FTZ变体用于单点归因上存在可执行的直接衔接。
- [SoftplusV2Grad VF Form B exp 溢出判别](../../../../../runbooks/precision/softplusv2grad_vf_form_b_exp.md)（`exemplifies`）：Exp 与《SoftplusV2Grad VF Form B exp 溢出判别》的实质衔接是：这些卡直接给出 Exp 的高阶、基础、Reg 与 C 入口及其临时空间契约；所连排障卡均以 Exp 的溢出、下溢、FTZ 或 clamp 行为作为精度根因和修复对象。
- [arch35 sigmoid 大负 z 下 exp 溢出 inf 致 sig=0](../../../../../runbooks/precision/arch35_sigmoid_z_exp_inf_sig_0.md)（`exemplifies`）：arch35 sigmoid 大负 z 下 exp 溢出 inf 致 sig=0 与《Exp》的实质衔接是：该 sigmoid 失败由 exp(-z) 溢出和 subnormal FTZ 共同造成；Exp/Reciprocal/Clamp 接口及同类数值故障分别提供溢出阈值、稳定式和直接除法验证边界。
- [exp 下界 clamp -50 破坏 sigmoid 大负数下溢](../../../../../runbooks/precision/exp_clamp_50_sigmoid.md)（`exemplifies`）：Exp 与《exp 下界 clamp -50 破坏 sigmoid 大负数下溢》的实质衔接是：这些卡直接给出 Exp 的高阶、基础、Reg 与 C 入口及其临时空间契约；所连排障卡均以 Exp 的溢出、下溢、FTZ 或 clamp 行为作为精度根因和修复对象。
- [exp 输入 clamp 上界用 threshold 用户参数致溢出](../../../../../runbooks/precision/exp_clamp_upper_bound_must_decouple_from_user_threshold.md)（`exemplifies`）：exp 输入 clamp 上界用 threshold 用户参数致溢出 与《Exp》的实质衔接是：故障由用户 threshold 充当 Exp 安全上界导致；Exp、Clamp/Mins、Sigmoid 公式及溢出/FTZ/Softplus 分支案例共同限定固定上界和极值验收。
- [Exp](../../../basic_api/reg_vector_compute/basic_arithmetic/exp.md)（`related`）：高阶 Exp 可选泰勒展开并管理临时空间，和基础 Reg Exp 的显式寄存器实现形成抽象层与 workspace 的选型边界。
- [更多样例（数学计算）](../more_examples.md)（`related`）：样例四直接以 Exp 展示 isReuseSource=false/true 对源 Tensor 保留与复用的差异；Exp 卡给出这一模板参数和临时空间重载的完整契约。
- [AscExp](../../../c_api/reg/arithmetic_compute/asc_exp.md)（`same_topic`）：AscExp 与《Exp》的实质衔接是：这些入口都执行逐元素自然指数；高阶/Memory/Reg/C Vector 对应接口给出不同数据承载方式，FTZ 与 sigmoid 溢出卡直接验证次正规和大指数边界。
- [AscExp](../../../c_api/vector_compute/asc_exp.md)（`same_topic`）：Exp 与《AscExp》的实质衔接是：这些卡直接给出 Exp 的高阶、基础、Reg 与 C 入口及其临时空间契约；所连排障卡均以 Exp 的溢出、下溢、FTZ 或 clamp 行为作为精度根因和修复对象。
- [Exp](../../../basic_api/memory_vector_compute/basic_arithmetic/exp.md)（`same_topic`）：Exp 与《Exp》的实质衔接是：这些卡直接给出 Exp 的高阶、基础、Reg 与 C 入口及其临时空间契约；所连排障卡均以 Exp 的溢出、下溢、FTZ 或 clamp 行为作为精度根因和修复对象。
- [Exp接口](exp_interface.md)（`same_topic`）：Exp 与《Exp接口》的实质衔接是：这些卡直接给出 Exp 的高阶、基础、Reg 与 C 入口及其临时空间契约；所连排障卡均以 Exp 的溢出、下溢、FTZ 或 clamp 行为作为精度根因和修复对象。
- [GetExpMaxMinTmpSize](get_exp_max_min_tmp_size.md)（`same_topic`）：Exp 与《GetExpMaxMinTmpSize》的实质衔接是：这些卡直接给出 Exp 的高阶、基础、Reg 与 C 入口及其临时空间契约；所连排障卡均以 Exp 的溢出、下溢、FTZ 或 clamp 行为作为精度根因和修复对象。
- [GetExpTmpBufferFactorSize](get_exp_tmp_buffer_factor_size.md)（`same_topic`）：Exp 与《GetExpTmpBufferFactorSize》的实质衔接是：这些卡直接给出 Exp 的高阶、基础、Reg 与 C 入口及其临时空间契约；所连排障卡均以 Exp 的溢出、下溢、FTZ 或 clamp 行为作为精度根因和修复对象。
<!-- cannbot:related:end -->
