---
type: API
title: ClampMin
description: 将srcTensor中小于scalar的数替换为scalar，大于等于scalar的数保持不变，作为dstTensor输出。 ! !
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Clamp_interface/ClampMin.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# ClampMin

将srcTensor中小于scalar的元素替换为scalar，大于等于scalar的元素保持不变，输出到dstTensor。模板参数T支持half/float。

提供两种重载：通过sharedTmpBuffer入参传入临时空间（开发者自行管理，可复用，内存利用率高），或由接口框架申请临时空间（需预留空间，大小通过GetClampMaxMinTmpSize获取）。接口内部涉及复杂数学计算，需要额外临时空间存储中间变量。

模板参数isReuseSource预留，传入false即可。接口参数：dstTensor为输出操作数；srcTensor为输入操作数，TPosition支持VECIN/VECCALC/VECOUT，数据类型需与dstTensor一致；sharedTmpBuffer为临时缓存；scalar为下限阈值，类型与srcTensor一致；calCount为参与计算的元素个数。

约束：不支持源操作数与目的操作数地址重叠；不支持sharedTmpBuffer与源/目的操作数地址重叠；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [Maxs 下限 clamp 阻止 exp 自然下溢残留](../../../../../runbooks/precision/maxs_clamp_exp.md)（`exemplifies`）：《ClampMin》说明将srcTensor中小于scalar的数替换为scalar，大于等于scalar的数保持不变，作为dstTensor输出。；《Maxs 下限 clamp 阻止 exp 自然下溢残留》说明sigmoid 类算子 grad 分支对 exp 输入做 Maxs(bx,-50) 下限 clamp 会阻止 z 极负时 exp(z) 自然下溢为 0，残留 exp(-50)≈1.9e-22 与 FLT_MAX 量级 grad 相乘得可见非零偏差，而 golden=0。判别要点是 exp 输入的下限 clamp 与大 grad 的乘积放大。。二者在ClampMin与ClampMax共同定义上下界替换，workspace查询决定分块，exp下溢故障则直接验证错误下界的数值后果上存在可执行的直接衔接。
- [exp 下界 clamp -50 破坏 sigmoid 大负数下溢](../../../../../runbooks/precision/exp_clamp_50_sigmoid.md)（`exemplifies`）：《ClampMin》说明将srcTensor中小于scalar的数替换为scalar，大于等于scalar的数保持不变，作为dstTensor输出。；《exp 下界 clamp -50 破坏 sigmoid 大负数下溢》说明SoftplusV2Grad kernel 对 exp 输入做 max(bx,-50) 下界 clamp，把大负数 z 的 exp(z)→0 正确下溢值抬高为 exp(-50)≈1.9e-22，gradOutput 大时被放大；判别：NPU 输出≈gradOutput×exp(-50) 即命中下界 clamp bug。。二者在ClampMin与ClampMax共同定义上下界替换，workspace查询决定分块，exp下溢故障则直接验证错误下界的数值后果上存在可执行的直接衔接。
- [Clamp接口](clamp_interface.md)（`related`）：ClampMin 是只施加下界的变体，补充总览中单边截断的选择边界。
- [GetClampMaxMinTmpSize](get_clamp_max_min_tmp_size.md)（`related`）：《ClampMin》说明将srcTensor中小于scalar的数替换为scalar，大于等于scalar的数保持不变，作为dstTensor输出。；《GetClampMaxMinTmpSize》说明在host侧获取ClampMax/ClampMin/Clamp接口所需的最大和最小临时空间大小，供开发者选择合适的Tiling参数传入kernel侧。。二者在ClampMin与ClampMax共同定义上下界替换，workspace查询决定分块，exp下溢故障则直接验证错误下界的数值后果上存在可执行的直接衔接。
- [ClampMax](clamp_max.md)（`same_topic`）：《ClampMin》说明将srcTensor中小于scalar的数替换为scalar，大于等于scalar的数保持不变，作为dstTensor输出。；《ClampMax》说明将srcTensor中大于scalar的数替换为scalar，小于等于scalar的数保持不变，作为dstTensor输出。。二者在ClampMin与ClampMax共同定义上下界替换，workspace查询决定分块，exp下溢故障则直接验证错误下界的数值后果上存在可执行的直接衔接。
- [Clamp（数学计算）](clamp.md)（`same_topic`）：《Clamp（数学计算）》说明将输入中除nan值以外大于max的数替换为max，小于min的数替换为min，小于等于max和大于等于min的数保持不变，作为输出。当min大于max时，将除nan值外所有值替换为max。min和max可以为标量或LocalTensor。；《ClampMin》说明将srcTensor中小于scalar的数替换为scalar，大于等于scalar的数保持不变，作为dstTensor输出。。二者在Clamp、ClampMin/Max及workspace查询共享上下界替换合同，exp相关故障直接说明错误clamp边界对数值的影响上存在可执行的直接衔接。
- [GetClampTmpBufferFactorSize](get_clamp_tmp_buffer_factor_size.md)（`same_topic`）：“GetClampTmpBufferFactorSize”处理获取ClampMax/ClampMin/Clamp接口所需的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。；“ClampMin”明确将srcTensor中小于scalar的数替换为scalar，大于等于scalar的数保持不变，作为dstTensor输出。 ! !。实质衔接：该因子函数正文明确服务于 Clamp、ClampMax、ClampMin，并与 Host 侧最大/最小临时空间查询形成两种 Tiling 预算方法。
<!-- cannbot:related:end -->
