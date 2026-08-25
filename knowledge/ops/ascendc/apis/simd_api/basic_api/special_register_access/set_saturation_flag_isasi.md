---
type: API
title: SetSaturationFlag
description: 设置饱和开关的标志位，控制计算或精度转换时饱和模式的开启与关闭。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/special_register_access/SetSaturationFlag_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---
# SetSaturationFlag

头文件路径为："basic_api/kernel_operator_common_intf.h"。

设置饱和开关的标志位，以控制计算/精度转换时饱和模式的开启与关闭。

参数：mode: 配置的对应饱和模式。 当mode配置为FLOAT时，开启饱和模式，inf输出会被饱和为±MAX，NaN输出会被饱和为0；关闭饱和模式，inf/NaN保持原输出。 当mode配置为CAST时，开启饱和模式，溢出值会被饱和为±MAX；关闭饱和模式，溢出值会按目标数据类型位数截断，保留低位，舍弃高位。 enum class SaturationMode : uint8_t { FLOAT, // 控制浮点数计算和浮点数精度转换时的饱和模式,浮点数数据类型仅支持half、bfloat16_t; CAST // 控制浮点数转整数或整数转整数时的精度转换饱和模式; };；enableSat(输入): 是否开启对应饱和模式。true表示开启饱和模式，false表示关闭饱和模式。

仅 Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [ResetCtrlSpr](reset_ctrl_spr_isasi.md)（`related`）：“SetSaturationFlag”定义：设置饱和开关的标志位，控制计算或精度转换时饱和模式的开启与关闭。；“ResetCtrlSpr”定义：对CTRL寄存器的特定比特位做重置，恢复为默认值。。实质衔接：SetSaturationFlag 修改饱和状态，Get 用于验证当前值；通用 CTRL SPR set/reset 提供底层控制位管理和恢复默认值的契约。
- [SetCtrlSpr](set_ctrl_spr_isasi.md)（`related`）：“SetSaturationFlag”定义：设置饱和开关的标志位，控制计算或精度转换时饱和模式的开启与关闭。；“SetCtrlSpr”定义：对CTRL寄存器的特定比特位进行设置，通过模板参数指定比特位范围并写入对应值。。实质衔接：SetSaturationFlag 修改饱和状态，Get 用于验证当前值；通用 CTRL SPR set/reset 提供底层控制位管理和恢复默认值的契约。
- [GetSaturationFlag](get_saturation_flag_isasi.md)（`same_topic`）：SetSaturationFlag说明设置饱和开关的标志位，控制计算或精度转换时饱和模式的开启与关闭；对GetSaturationFlag而言，GetSaturationFlag 读取的正是 SetSaturationFlag 写入的全局饱和状态，二者构成可验证的设置—读取闭环。
<!-- cannbot:related:end -->
