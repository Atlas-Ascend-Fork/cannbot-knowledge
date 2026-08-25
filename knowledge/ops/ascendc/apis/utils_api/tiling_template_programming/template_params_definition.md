---
type: API
title: 模板参数定义
description: 通过以下函数原型进行模板参数ASCENDC_TPL_ARGS_DECL和模板参数组合ASCENDC_TPL_ARGS_SEL（即可使用的模板）的定义。详细内容请参考Tiling模板编程。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_template_programming/template_params_definition.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# 模板参数定义

## 功能说明
通过以下函数原型进行模板参数ASCENDC_TPL_ARGS_DECL和模板参数组合ASCENDC_TPL_ARGS_SEL（即可使用的模板）的定义。详细内容请参考Tiling模板编程。
## 函数原型
## 参数说明
Tiling模板参数定义说明
Tiling模板参数组合定义
## 返回值说明
无。
## 约束说明
对模板参数定义的取值进行修改或新增后，需要重新编译自定义算子包，不能再继续使用之前的算子二进制。

<!-- cannbot:related:start -->
## 相关

- [kernel.h 须 include struct.h 才能识别 TPL](../../../runbooks/compilation/ascendc_tpl_kernel_h_must_include_struct_h.md)（`exemplifies`）：该卡证明模板参数宏若未通过 struct.h 进入 kernel.h 的预处理 include 树，编译会退化为非模板调用，直接补充定义落地时的构建闭环。
- [ASCENDC_TPL_SEL_PARAM](ascendc_tpl_sel_param.md)（`related`）：ASCENDC_TPL_SEL_PARAM 消费已定义的模板参数及组合来生成编译实例，是参数定义后的直接下一步。
- [GET_TPL_TILING_KEY](get_tpl_tiling_key.md)（`related`）：GET_TPL_TILING_KEY 按定义的位宽和顺序编码运行时 TilingKey，必须与模板参数定义保持一致。
- [HCCL模板参数](../../simd_api/adv_api/hccl_communication/hccl_kernel/hccl_template_params.md)（`related`）：模板参数定义解释通用模板配置的编程方式，可帮助核对 HCCL 的 HcclServerType/HcclServerConfig 实参如何在编译期绑定。
- [Conv3D模板参数](../../simd_api/adv_api/convolution_compute/conv3_d_kernel/conv3_d_template_params.md)（`same_topic`）：Conv3D模板参数 与《模板参数定义》的实质衔接是：Conv3D 模板参数决定 Input/Weight/Output/Bias 的位置、格式与类型，必须和 Kernel 构造、Init、Tiling 结构及 Set*Type/SetGroups 配置保持一致。
- [Tiling模板编程](tiling_template_programming.md)（`same_topic`）：Tiling模板编程 与《模板参数定义》的实质衔接是：Tiling 模板编程依赖参数声明、选择宏和 key 获取；所选编译故障直接约束模板类型与分发实例化。
<!-- cannbot:related:end -->
