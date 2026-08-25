---
type: API
title: AICPU（OpDef）
description: 设置AI CPU的配置信息：包括算子输入输出的名称、支持的数据类型、数据格式等信息。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpDef/AICPU.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# AICPU

## 功能说明
设置AI CPU的配置信息：包括算子输入输出的名称、支持的数据类型、数据格式等信息。
## 函数原型
## 参数说明
无
## 返回值说明
OpAICPUDef请参考OpAICPUDef。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [AICPU launcher 缺 OP_ATTR_NAMES 编译错](../../../../runbooks/compilation/aicpu_launcher_op_attr_names.md)（`exemplifies`）：《AICPU launcher 缺 OP_ATTR_NAMES 编译错》的任务是“无属性 regbase 算子的 ADD_TO_LAUNCHER_LIST_AICPU 调用若照搬 AICORE 写法省略 OP_ATTR_NAMES()，AICPU 宏会把第二个形参位（op::FVector<std::string>&，属性名向量）错绑到 OP_INPUT(...)，触发引用类型不匹配编译错。判别=build.sh --pkg 编译期报 invalid initialization of reference of type 'op::FVector<std::basic_string<char> >&' from expression of type 'op::OpInput<...>'，定位行紧随算子名后缺 OP_ATTR_NAMES()。AICORE 变体无该形参位，省略合法，二者宏签名不可互换。”。《AICPU（OpDef）》具体提供“设置AI CPU的配置信息：包括算子输入输出的名称、支持的数据类型、数据格式等信息。”，它直接用于AICPU launcher 的 OP_ATTR_NAMES 形参、属性定义和 AICPU 原型。
- [AI CPU编程（编程模型）](../../../../guides/programming_guide/programming_model/ai_cpu_programming.md)（`explains`）：AICPU（OpDef）说明设置AI CPU的配置信息：包括算子输入输出的名称、支持的数据类型、数据格式等信息。
- [OpkernelLib](../op_aicpu_def/opkernel_lib.md)（`related`）：OpkernelLib 与《AICPU（OpDef）》的实质衔接是：OpkernelLib 在 OpAICPUDef 固定 CUSTAICPUKernel，必须与 KernelSo、Engine、FunctionName 和 AICPU OpDef/launcher 生成链一致。
- [UserDefined](../op_aicpu_def/user_defined.md)（`related`）：《UserDefined》说明配置该算子是否为用户自定义算子，AICPU自定义算子的userDefined仅支持配置为“True”，若开发者没有配置的情况下，该参数会被默认设置为“True”。；《AICPU（OpDef）》说明设置AI CPU的配置信息：包括算子输入输出的名称、支持的数据类型、数据格式等信息。。二者在UserDefined是AICPU注册属性，与KernelSo、FunctionName、OpkernelLib、OpAICPUDef及编译/launcher合同共同生效上存在可执行的直接衔接。
- [原型注册接口（OP_ADD）](../op_add.md)（`related`）：《原型注册接口（OP_ADD）》处理“注册算子的原型定义，从而确保算子能够被框架正确识别、编译和执行。 算子原型主要描述了算子的输入输出、属性等信息以及算子在AI处理器上相关实现信息，并关联tiling实现等函数。算子原型通过自定义的算子类来承载，该算子类继承自OpDef类。完成算子的原型定义等操作后，需要调用OP_ADD接口，传入算子类型（自定义算子类的类名），进行算子原型注册。详细内容请参考算子原型定义。”。《AICPU（OpDef）》明确提供“设置AI CPU的配置信息：包括算子输入输出的名称、支持的数据类型、数据格式等信息。”，其参数、调用或验证步骤直接接入OP_ADD 宏与 OpDef、注册函数、原型库和注册故障的可执行闭环。
- [OpAICPUDef](../op_aicpu_def/op_aicpu_def.md)（`same_topic`）：“AICPU（OpDef）”处理设置AI CPU的配置信息：包括算子输入输出的名称、支持的数据类型、数据格式等信息。；“OpAICPUDef”明确OpAICPUDef算子定义接口索引。。实质衔接：AICPU() 的返回值就是 OpAICPUDef；后续配置由该对象承载，其他成员归属交给 part_of。
<!-- cannbot:related:end -->
