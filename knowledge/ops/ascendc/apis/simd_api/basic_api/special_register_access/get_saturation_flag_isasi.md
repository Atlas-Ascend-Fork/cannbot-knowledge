---
type: API
title: GetSaturationFlag
description: 获取计算或精度转换时饱和模式的开启状态。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/special_register_access/GetSaturationFlag_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---
# GetSaturationFlag

头文件路径为："basic_api/kernel_operator_common_intf.h"。

获取计算/精度转换时饱和模式的开启状态。

参数：mode: 配置的对应饱和模式。 当mode配置为FLOAT时，开启饱和模式，inf输出会被饱和为±MAX，NaN输出会被饱和为0；关闭饱和模式，inf/NaN保持原。

仅 Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [SetSaturationFlag](set_saturation_flag_isasi.md)（`same_topic`）：SetSaturationFlag说明设置饱和开关的标志位，控制计算或精度转换时饱和模式的开启与关闭；对GetSaturationFlag而言，GetSaturationFlag 读取的正是 SetSaturationFlag 写入的全局饱和状态，二者构成可验证的设置—读取闭环。
<!-- cannbot:related:end -->
