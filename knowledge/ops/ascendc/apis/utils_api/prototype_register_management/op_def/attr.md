---
type: API
title: Attr（OpDef）
description: 注册算子属性参数。 当需要设置的参数不参与kernel侧计算时，可以将该参数注册为算子属性参数。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpDef/Attr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# Attr

## 功能说明
注册算子属性参数。
当需要设置的参数不参与kernel侧计算时，可以将该参数注册为算子属性参数。
## 函数原型
## 参数说明
## 返回值说明
算子属性定义，OpAttrDef请参考OpAttrDef。
## 约束说明
Attr属性名不能与以下python关键字及内置变量名相同，否则会导致未定义错误。
-   常见python关键字参考
and、 as、 assert、 break、 class、 continue、 def、 del、 elif、 else、 except、 finally、 for、 from、 global、 if、 import、 in、 is、 lambda、 not、 or、 pass、 raise、 return、 try、 while、 with、 yield、 False、 None、 True、 nonlocal、 arg。
-   内置变量名
__inputs__、 __outputs__、 __attrs__、 options、 bisheng、 bisheng_path、 tikcpp_path、 impl_mode、 custom_compile_options、 custom_all_compile_options、 soc_version、 soc_short、 custom_compile_options_soc、 custom_all_compile_options_soc、 origin_func_name、 ascendc_src_dir_ex、 ascendc_src_dir、 ascendc_src_file、 src、 op_type、 code_channel、 op_info、 compile_op、 get_code_channel、 result、 isinstance、 attr、 get_current_build_config、 _build_args、 get_dtype_fmt_options、 shutil、 os、 get_kernel_source、ascendc_api_version_header_path、ascendc_api_version_file、ascendc_api_version、re。

<!-- cannbot:related:start -->
## 相关

- [aclnn TilingData 缓存致 runtime attr 陈旧](../../../../runbooks/precision/aclnn_tilingdata_runtime_attr.md)（`exemplifies`）：运行卡说明每次调用变化的 Attr 若经 TilingData 传给 Kernel，会受 aclnn repeat cache 影响而变陈旧，给出属性从原型进入运行时后的缓存边界。
- [算子属性默认值 stringstream 截断致 FP32 标量误差](../../../../runbooks/precision/stringstream_fp32.md)（`exemplifies`）：算子属性默认值 stringstream 截断致 FP32 标量误差 与《Attr（OpDef）》的实质衔接是：OpDef Attr是默认 float 字面量进入 op_build 序列化的起点，GET_TILING_DATA_WITH_STRUCT是 device 读取终点；TilingData缓存与 numpy标量提升是相同稳定ULP现象的关键差分根因。
- [算子原型定义](../../../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/operator_prototype_definition.md)（`explains`）：原型定义指南展示 Attr 如何与输入输出、dtype/format、TilingFunc 一起落到 OpDef 构造函数，并说明声明顺序和生成接口的关系。
- [通过TilingData传递属性信息](../../../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/tiling_data_attributes.md)（`explains`）：“通过TilingData传递属性信息”处理本文属于扩展内容，介绍算子属性参与Kernel计算时所需的数据传递方法。算子属性在Host侧保存，Kernel不能直接读取。属性需要参与Kernel计算时，Host侧Tiling函数先读取属性值，再把Kernel真正需要的数据写入TilingD…；“Attr（OpDef）”明确注册算子属性参数。 当需要设置的参数不参与kernel侧计算时，可以将该参数注册为算子属性参数。。实质衔接：属性从 OpDef 声明，经 Host Tiling 读取并写入注册的 TilingData，再由 Kernel 宏解析；故障卡验证类型契约与跨调用缓存边界。
- [OpAttrDef](../op_attr_def/op_attr_def.md)（`related`）：OpAttrDef 与《Attr（OpDef）》的实质衔接是：OpAttrDef 定义属性名、类型、OPTIONAL/REQUIRED、默认值和 Version；Comment 生成原型注释，OpDef::Attr 挂载属性，Host TilingData 传递与缓存故障说明 runtime 属性进入 kernel 时的后续契约。
- [OpAttrDef](../op_attr_def/op_attr_def_functions.md)（`related`）：《OpAttrDef》说明class OpAttrDef {；《Attr（OpDef）》说明注册算子属性参数。 当需要设置的参数不参与kernel侧计算时，可以将该参数注册为算子属性参数。。二者在OpDef::Attr注册属性时使用OpAttrDef描述属性定义，二者共同确定原型属性的类型与对外接口上存在可执行的直接衔接。
- [OpDef](op_def.md)（`related`）：OpDef 核心类用 Input、Output 与 Attr 声明算子外部契约，Attr 是其中的属性注册成员。
- [原型注册接口（OP_ADD）](../op_add.md)（`related`）：Attr 写入 OpDef 类后还需由 OP_ADD 注册整个算子原型，才能让框架生成并识别对外接口。
<!-- cannbot:related:end -->
