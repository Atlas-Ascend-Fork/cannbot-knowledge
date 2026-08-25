---
type: API
title: Atan接口
description: 提供Atan反正切计算接口及其Tiling临时空间大小查询接口，包含Atan、GetAtanMaxMinTmpSize等。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Atan_interface/Atan_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Atan接口

提供Atan反正切计算接口及其Tiling临时空间大小查询接口，包含Atan、GetAtanMaxMinTmpSize等。

按元素做三角函数反正切运算，计算公式如下：

本接口组包含 Atan。

本接口属于高阶数学计算接口。

支持的数据类型为 half、float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：不支持源操作数与目的操作数地址重叠。；不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。；操作数地址对齐要求请参见通用地址对齐约束。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品AI Core, Kirin X90。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Atan2f](../../../../simt_api/math_functions/float_math_functions/atan2f.md)（`related`）：《Atan接口》处理“提供Atan反正切计算接口及其Tiling临时空间大小查询接口，包含Atan、GetAtanMaxMinTmpSize等。”。《Atan2f》明确提供“获取输入数据y/x的反正切值。”，其参数、调用或验证步骤直接接入Atan Kernel 调用、临时空间查询和 SIMT 对应实现。
- [Atanf](../../../../simt_api/math_functions/float_math_functions/atanf.md)（`related`）：《Atan接口》处理“提供Atan反正切计算接口及其Tiling临时空间大小查询接口，包含Atan、GetAtanMaxMinTmpSize等。”。《Atanf》明确提供“获取输入数据的反正切值。”，其参数、调用或验证步骤直接接入Atan Kernel 调用、临时空间查询和 SIMT 对应实现。
- [Atan](atan.md)（`same_topic`）：《Atan接口》处理“提供Atan反正切计算接口及其Tiling临时空间大小查询接口，包含Atan、GetAtanMaxMinTmpSize等。”。《Atan》明确提供“按元素做反正切运算，支持泰勒展开和多项式逼近两种算法配置”，其参数、调用或验证步骤直接接入Atan Kernel 调用、临时空间查询和 SIMT 对应实现。
- [GetAtanMaxMinTmpSize](get_atan_max_min_tmp_size.md)（`same_topic`）：《Atan接口》处理“提供Atan反正切计算接口及其Tiling临时空间大小查询接口，包含Atan、GetAtanMaxMinTmpSize等。”。《GetAtanMaxMinTmpSize》明确提供“在host侧获取Atan接口预留临时空间的最大和最小值，用于Tiling参数选择”，其参数、调用或验证步骤直接接入Atan Kernel 调用、临时空间查询和 SIMT 对应实现。
- [GetAtanTmpBufferFactorSize](get_atan_tmp_buffer_factor_size.md)（`same_topic`）：《Atan接口》处理“提供Atan反正切计算接口及其Tiling临时空间大小查询接口，包含Atan、GetAtanMaxMinTmpSize等。”。《GetAtanTmpBufferFactorSize》明确提供“获取Atan接口的maxLiveNodeCount和extraBuf，用于推算固定空间下单次最大计算元素数”，其参数、调用或验证步骤直接接入Atan Kernel 调用、临时空间查询和 SIMT 对应实现。
- [Tan接口](../tan_interface/tan_interface.md)（`same_topic`）：Tan接口 与《Atan接口》的实质衔接是：Tan 接口由 Tan 和两种临时空间查询组成；Atan 是反函数，Sin/Cos 卡解释 tan=sin/cos 的输入值域与验证关系。
<!-- cannbot:related:end -->
