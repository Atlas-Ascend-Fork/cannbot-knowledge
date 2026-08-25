---
type: API
title: Clamp（数学计算）
description: 将输入中除nan值以外大于max的数替换为max，小于min的数替换为min，小于等于max和大于等于min的数保持不变，作为输出。当min大于max时，将除nan值外所有值替换为max。min和max可以为标量或LocalTensor。
  ! !
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Clamp_interface/Clamp.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Clamp（数学计算）

将输入中除nan值以外大于max的数替换为max，小于min的数替换为min，小于等于max和大于等于min的数保持不变，作为输出。当min大于max时，将除nan值外所有值替换为max。min和max可以为标量或LocalTensor。

函数原型：
template <const ClampConfig& config = DEFAULT_CLAMP_CONFIG, typename T, typename U, typename S>
__aicore__ inline void Clamp(const LocalTensor<T>& dst, const LocalTensor<T>& src, const U& min, const S& max, const uint32_t count)

参数：
- config：Clamp算法的相关配置。此参数可选配，ClampConfig类型，具体定义如下方代码所示，其中参数的含义为： isReuseSource：该参数预留，传入默认值false即可。
- T：操作数的数据类型。支持的数据类型为：int8_t、uint8_t、int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float、int64_t、uint64_t。
- U：LocalTensor类型或标量类型。根据输入参数min自动推导类型，开发者无需配置该参数，保证min满足数据类型的约束即可。 支持的数据类型为：int8_t、uint8_t、int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float、int64_t、uint64_t。
- S：LocalTensor类型或标量类型。根据输入参数max自动推导类型，开发者无需配置该参数，保证max满足数据类型的约束即可。 支持的数据类型为：int8_t、uint8_t、int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float、int64_t、uint64_t。
- dst（输出）：目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。

约束：
- 不支持源操作数与目的操作数地址重叠。
- 操作数地址对齐要求请参见通用地址对齐约束。

支持：Ascend 950PR/Ascend 950DT。不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [Max/Min 逐元素非标量广播 须 Duplicate 至同长 buffer](../../../../../runbooks/precision/count_based_max_min_is_element_wise_not_scalar_broadcast.md)（`exemplifies`）：《Clamp（数学计算）》说明将输入中除nan值以外大于max的数替换为max，小于min的数替换为min，小于等于max和大于等于min的数保持不变，作为输出。当min大于max时，将除nan值外所有值替换为max。min和max可以为标量或LocalTensor。；《Max/Min 逐元素非标量广播 须 Duplicate 至同长 buffer》说明AscendC count-based Max/Min(dst,src0,src1,count) 是逐元素比较，src1 必须是与 src0 同长度的完整 tensor，不做标量广播；要用标量做 clamp 须先 Duplicate(scalar) 填充同长度 tensor，且该 buffer 容量须 ≥ N×sizeof(float)（32B clampBuf 远不够），应复用阶段内已空闲的 N×float buffer。。二者在Clamp、ClampMin/Max及workspace查询共享上下界替换合同，exp相关故障直接说明错误clamp边界对数值的影响上存在可执行的直接衔接。
- [Maxs 下限 clamp 阻止 exp 自然下溢残留](../../../../../runbooks/precision/maxs_clamp_exp.md)（`exemplifies`）：《Clamp（数学计算）》说明将输入中除nan值以外大于max的数替换为max，小于min的数替换为min，小于等于max和大于等于min的数保持不变，作为输出。当min大于max时，将除nan值外所有值替换为max。min和max可以为标量或LocalTensor。；《Maxs 下限 clamp 阻止 exp 自然下溢残留》说明sigmoid 类算子 grad 分支对 exp 输入做 Maxs(bx,-50) 下限 clamp 会阻止 z 极负时 exp(z) 自然下溢为 0，残留 exp(-50)≈1.9e-22 与 FLT_MAX 量级 grad 相乘得可见非零偏差，而 golden=0。判别要点是 exp 输入的下限 clamp 与大 grad 的乘积放大。。二者在Clamp、ClampMin/Max及workspace查询共享上下界替换合同，exp相关故障直接说明错误clamp边界对数值的影响上存在可执行的直接衔接。
- [exp 下界 clamp -50 破坏 sigmoid 大负数下溢](../../../../../runbooks/precision/exp_clamp_50_sigmoid.md)（`exemplifies`）：《Clamp（数学计算）》说明将输入中除nan值以外大于max的数替换为max，小于min的数替换为min，小于等于max和大于等于min的数保持不变，作为输出。当min大于max时，将除nan值外所有值替换为max。min和max可以为标量或LocalTensor。；《exp 下界 clamp -50 破坏 sigmoid 大负数下溢》说明SoftplusV2Grad kernel 对 exp 输入做 max(bx,-50) 下界 clamp，把大负数 z 的 exp(z)→0 正确下溢值抬高为 exp(-50)≈1.9e-22，gradOutput 大时被放大；判别：NPU 输出≈gradOutput×exp(-50) 即命中下界 clamp bug。。二者在Clamp、ClampMin/Max及workspace查询共享上下界替换合同，exp相关故障直接说明错误clamp边界对数值的影响上存在可执行的直接衔接。
- [exp 输入 clamp 上界用 threshold 用户参数致溢出](../../../../../runbooks/precision/exp_clamp_upper_bound_must_decouple_from_user_threshold.md)（`exemplifies`）：《Clamp（数学计算）》说明将输入中除nan值以外大于max的数替换为max，小于min的数替换为min，小于等于max和大于等于min的数保持不变，作为输出。当min大于max时，将除nan值外所有值替换为max。min和max可以为标量或LocalTensor。；《exp 输入 clamp 上界用 threshold 用户参数致溢出》说明arch35 kernel 用算子用户参数 threshold 作 exp 输入 clamp 上界，threshold 可达 3.4e38 使 exp(100)→inf→Actual=3.4e38；clamp 上界改固定 50.0f 与 threshold 解耦修复。。二者在Clamp、ClampMin/Max及workspace查询共享上下界替换合同，exp相关故障直接说明错误clamp边界对数值的影响上存在可执行的直接衔接。
- [Min](../../../basic_api/reg_vector_compute/basic_arithmetic/min.md)（`related`）：《Min》说明根据mask对源操作数srcReg0、srcReg1按元素求最小值，将结果写入目的操作数dstReg。；《Clamp（数学计算）》说明将输入中除nan值以外大于max的数替换为max，小于min的数替换为min，小于等于max和大于等于min的数保持不变，作为输出。当min大于max时，将除nan值外所有值替换为max。min和max可以为标量或LocalTensor。。二者在Reg Min与Max、标量Mins及Memory/C/SIMT等价接口的操作数形态不同，Clamp则直接组合最小/最大边界上存在可执行的直接衔接。
- [ClampMax](clamp_max.md)（`same_topic`）：《Clamp（数学计算）》说明将输入中除nan值以外大于max的数替换为max，小于min的数替换为min，小于等于max和大于等于min的数保持不变，作为输出。当min大于max时，将除nan值外所有值替换为max。min和max可以为标量或LocalTensor。；《ClampMax》说明将srcTensor中大于scalar的数替换为scalar，小于等于scalar的数保持不变，作为dstTensor输出。。二者在Clamp、ClampMin/Max及workspace查询共享上下界替换合同，exp相关故障直接说明错误clamp边界对数值的影响上存在可执行的直接衔接。
- [ClampMin](clamp_min.md)（`same_topic`）：《Clamp（数学计算）》说明将输入中除nan值以外大于max的数替换为max，小于min的数替换为min，小于等于max和大于等于min的数保持不变，作为输出。当min大于max时，将除nan值外所有值替换为max。min和max可以为标量或LocalTensor。；《ClampMin》说明将srcTensor中小于scalar的数替换为scalar，大于等于scalar的数保持不变，作为dstTensor输出。。二者在Clamp、ClampMin/Max及workspace查询共享上下界替换合同，exp相关故障直接说明错误clamp边界对数值的影响上存在可执行的直接衔接。
- [Clamp接口](clamp_interface.md)（`same_topic`）：《Clamp（数学计算）》说明将输入中除nan值以外大于max的数替换为max，小于min的数替换为min，小于等于max和大于等于min的数保持不变，作为输出。当min大于max时，将除nan值外所有值替换为max。min和max可以为标量或LocalTensor。；《Clamp接口》说明提供Clamp数值截断接口及其变体ClampMax、ClampMin，以及GetClampMaxMinTmpSize等Tiling临时空间大小查询接口。。二者在Clamp、ClampMin/Max及workspace查询共享上下界替换合同，exp相关故障直接说明错误clamp边界对数值的影响上存在可执行的直接衔接。
- [GetClampMaxMinTmpSize](get_clamp_max_min_tmp_size.md)（`same_topic`）：《Clamp（数学计算）》说明将输入中除nan值以外大于max的数替换为max，小于min的数替换为min，小于等于max和大于等于min的数保持不变，作为输出。当min大于max时，将除nan值外所有值替换为max。min和max可以为标量或LocalTensor。；《GetClampMaxMinTmpSize》说明在host侧获取ClampMax/ClampMin/Clamp接口所需的最大和最小临时空间大小，供开发者选择合适的Tiling参数传入kernel侧。。二者在Clamp、ClampMin/Max及workspace查询共享上下界替换合同，exp相关故障直接说明错误clamp边界对数值的影响上存在可执行的直接衔接。
- [GetClampTmpBufferFactorSize](get_clamp_tmp_buffer_factor_size.md)（`same_topic`）：“GetClampTmpBufferFactorSize”处理获取ClampMax/ClampMin/Clamp接口所需的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。；“Clamp（数学计算）”明确将输入中除nan值以外大于max的数替换为max，小于min的数替换为min，小于等于max和大于等于min的数保持不变，作为输出。当min大于max时，将除nan值外所有值替换为max。min和max可以为标量或LocalTensor。 ! !。实质衔接：该因子函数正文明确服务于 Clamp、ClampMax、ClampMin，并与 Host 侧最大/最小临时空间查询形成两种 Tiling 预算方法。
<!-- cannbot:related:end -->
