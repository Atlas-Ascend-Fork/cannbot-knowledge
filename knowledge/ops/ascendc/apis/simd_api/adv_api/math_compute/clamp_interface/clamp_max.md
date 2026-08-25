---
type: API
title: ClampMax
description: 将srcTensor中大于scalar的数替换为scalar，小于等于scalar的数保持不变，作为dstTensor输出。 ! !
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Clamp_interface/ClampMax.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# ClampMax

将srcTensor中大于scalar的数替换为scalar，小于等于scalar的数保持不变，作为dstTensor输出。

函数原型：
template <typename T, bool isReuseSource = false>
__aicore__ inline void ClampMax(const LocalTensor<T>& dstTensor, const LocalTensor<T>& srcTensor, const LocalTensor<uint8_t>& sharedTmpBuffer, const T scalar, const uint32_t calCount)

参数：
- T：操作数的数据类型。支持的数据类型为：half、float。
- isReuseSource：是否允许修改源操作数。该参数预留，传入默认值false即可。
- dstTensor（输出）：目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。
- srcTensor（输入）：源操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 源操作数的数据类型需要与目的操作数保持一致。
- sharedTmpBuffer（输入）：临时缓存。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 用于ClampMax内部复杂计算时存储中间变量，由开发者提供。 临时空间大小BufferSize的获取方式请参考GetClampMaxMinTmpSize。

约束：
- 不支持源操作数与目的操作数地址重叠。
- 不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。
- 操作数地址对齐要求请参见通用地址对齐约束。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [exp 输入 clamp 上界用 threshold 用户参数致溢出](../../../../../runbooks/precision/exp_clamp_upper_bound_must_decouple_from_user_threshold.md)（`exemplifies`）：exp 输入 clamp 上界用 threshold 用户参数致溢出 与《ClampMax》的实质衔接是：故障由用户 threshold 充当 Exp 安全上界导致；Exp、Clamp/Mins、Sigmoid 公式及溢出/FTZ/Softplus 分支案例共同限定固定上界和极值验收。
- [Clamp接口](clamp_interface.md)（`related`）：ClampMax 是只施加上界的变体，用户可依据是否需要双边截断在它与 Clamp 之间选型。
- [ClampMin](clamp_min.md)（`same_topic`）：《ClampMin》说明将srcTensor中小于scalar的数替换为scalar，大于等于scalar的数保持不变，作为dstTensor输出。；《ClampMax》说明将srcTensor中大于scalar的数替换为scalar，小于等于scalar的数保持不变，作为dstTensor输出。。二者在ClampMin与ClampMax共同定义上下界替换，workspace查询决定分块，exp下溢故障则直接验证错误下界的数值后果上存在可执行的直接衔接。
- [Clamp（数学计算）](clamp.md)（`same_topic`）：《Clamp（数学计算）》说明将输入中除nan值以外大于max的数替换为max，小于min的数替换为min，小于等于max和大于等于min的数保持不变，作为输出。当min大于max时，将除nan值外所有值替换为max。min和max可以为标量或LocalTensor。；《ClampMax》说明将srcTensor中大于scalar的数替换为scalar，小于等于scalar的数保持不变，作为dstTensor输出。。二者在Clamp、ClampMin/Max及workspace查询共享上下界替换合同，exp相关故障直接说明错误clamp边界对数值的影响上存在可执行的直接衔接。
- [GetClampMaxMinTmpSize](get_clamp_max_min_tmp_size.md)（`same_topic`）：ClampMax 与《GetClampMaxMinTmpSize》的实质衔接是：ClampMax 的 kernel 临时缓存来自 MaxMin 或 factor 查询，Clamp/ClampMin 是上界、双边和下界形态；exp 上界故障直接用固定 ClampMax 阈值替代用户 threshold，验证其数值边界作用。
- [GetClampTmpBufferFactorSize](get_clamp_tmp_buffer_factor_size.md)（`same_topic`）：“GetClampTmpBufferFactorSize”处理获取ClampMax/ClampMin/Clamp接口所需的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。；“ClampMax”明确将srcTensor中大于scalar的数替换为scalar，小于等于scalar的数保持不变，作为dstTensor输出。 ! !。实质衔接：该因子函数正文明确服务于 Clamp、ClampMax、ClampMin，并与 Host 侧最大/最小临时空间查询形成两种 Tiling 预算方法。
<!-- cannbot:related:end -->
