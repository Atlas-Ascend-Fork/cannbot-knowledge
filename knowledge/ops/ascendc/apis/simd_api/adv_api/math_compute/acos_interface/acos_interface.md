---
type: API
title: Acos接口
description: 提供Acos反余弦计算接口及其Tiling临时空间大小查询接口，包含Acos、GetAcosMaxMinTmpSize等。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Acos_interface/Acos_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Acos接口

提供Acos反余弦计算接口及其Tiling临时空间大小查询接口，包含Acos、GetAcosMaxMinTmpSize等。

按元素做反余弦函数计算，计算公式如下：

本接口组包含 Acos。

本接口属于高阶数学计算接口。

支持的数据类型为 half、float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：输入源数据需保持值域在[-1, 1]。若输入不在范围内，输出结果无效。；不支持源操作数与目的操作数地址重叠。；不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。；操作数地址对齐要求请参见通用地址对齐约束。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品AI Core, Kirin X90。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [GetAcosMaxMinTmpSize](get_acos_max_min_tmp_size.md)（`related`）：GetAcosMaxMinTmpSize 与《Acos接口》的实质衔接是：Acos 的 host 临时空间查询必须与 kernel Acos、接口封装及 factor-size 推算使用同一 shape/typeSize/复用策略。
- [GetAcosTmpBufferFactorSize](get_acos_tmp_buffer_factor_size.md)（`related`）：Acos接口 负责“提供Acos反余弦计算接口及其Tiling临时空间大小查询接口，包含Acos、GetAcosMaxMinTmpSize等”；GetAcosTmpBufferFactorSize 负责“获取Acos接口的maxLiveNodeCount和extraBuf，用于推算固定空间下单次最大计算元素数”。
- [Acos](acos.md)（`same_topic`）：Acos接口 的核心契约是“提供Acos反余弦计算接口及其Tiling临时空间大小查询接口，包含Acos、GetAcosMaxMinTmpSize等”；Acos 补充“按元素做反余弦函数计算，输入值域需在-1到1范围内”。
- [Acosf](../../../../simt_api/math_functions/float_math_functions/acosf.md)（`same_topic`）：高阶 Tensor Acos 与 SIMT acosf 完成同一反余弦任务。
<!-- cannbot:related:end -->
