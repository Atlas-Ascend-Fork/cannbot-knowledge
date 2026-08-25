---
type: API
title: Clamp接口
description: 提供Clamp数值截断接口及其变体ClampMax、ClampMin，以及GetClampMaxMinTmpSize等Tiling临时空间大小查询接口。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Clamp_interface/Clamp_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Clamp接口

提供数值截断（Clamp）操作的 Kernel 侧接口及变体，用于将张量元素限制在指定范围内。
包含 Clamp 双向截断、ClampMax 上界截断、ClampMin 下界截断三种计算接口，以及 GetClampMaxMinTmpSize 和 GetClampTmpBufferFactorSize 用于查询 Tiling 临时空间大小与因子。

<!-- cannbot:related:start -->
## 相关

- [exp 输入 clamp 上界用 threshold 用户参数致溢出](../../../../../runbooks/precision/exp_clamp_upper_bound_must_decouple_from_user_threshold.md)（`exemplifies`）：exp 输入 clamp 上界用 threshold 用户参数致溢出 与《Clamp接口》的实质衔接是：故障由用户 threshold 充当 Exp 安全上界导致；Exp、Clamp/Mins、Sigmoid 公式及溢出/FTZ/Softplus 分支案例共同限定固定上界和极值验收。
- [ClampMax](clamp_max.md)（`related`）：ClampMax 是只施加上界的变体，用户可依据是否需要双边截断在它与 Clamp 之间选型。
- [ClampMin](clamp_min.md)（`related`）：ClampMin 是只施加下界的变体，补充总览中单边截断的选择边界。
- [GetClampMaxMinTmpSize](get_clamp_max_min_tmp_size.md)（`related`）：执行 Clamp 前需在 Host 侧查询最小和最大临时空间，查询结果决定 Kernel 可用 workspace。
- [Clamp（数学计算）](clamp.md)（`same_topic`）：《Clamp（数学计算）》说明将输入中除nan值以外大于max的数替换为max，小于min的数替换为min，小于等于max和大于等于min的数保持不变，作为输出。当min大于max时，将除nan值外所有值替换为max。min和max可以为标量或LocalTensor。；《Clamp接口》说明提供Clamp数值截断接口及其变体ClampMax、ClampMin，以及GetClampMaxMinTmpSize等Tiling临时空间大小查询接口。。二者在Clamp、ClampMin/Max及workspace查询共享上下界替换合同，exp相关故障直接说明错误clamp边界对数值的影响上存在可执行的直接衔接。
- [GetClampTmpBufferFactorSize](get_clamp_tmp_buffer_factor_size.md)（`same_topic`）：“GetClampTmpBufferFactorSize”处理获取ClampMax/ClampMin/Clamp接口所需的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。；“Clamp接口”明确提供Clamp数值截断接口及其变体ClampMax、ClampMin，以及GetClampMaxMinTmpSize等Tiling临时空间大小查询接口。。实质衔接：该因子函数正文明确服务于 Clamp、ClampMax、ClampMin，并与 Host 侧最大/最小临时空间查询形成两种 Tiling 预算方法。
<!-- cannbot:related:end -->
