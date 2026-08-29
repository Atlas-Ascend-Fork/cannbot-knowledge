---
type: API
title: 原型注册接口（OP_ADD）
description: 注册算子的原型定义，从而确保算子能够被框架正确识别、编译和执行。 算子原型主要描述了算子的输入输出、属性等信息以及算子在AI处理器上相关实现信息，并关联tiling实现等函数。算子原型通过自定义的算子类来承载，该算子类继承自OpDef类。完成算子的原型定义等操作后，需要调用OP_ADD接口，传入算子类型（自定义算子类的类名），进行算子原型注册。详细内容请参考算子原型定义。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OP_ADD.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 原型注册接口（OP_ADD）

## 功能说明
注册算子的原型定义，从而确保算子能够被框架正确识别、编译和执行。
算子原型主要描述了算子的输入输出、属性等信息以及算子在AI处理器上相关实现信息，并关联tiling实现等函数。算子原型通过自定义的算子类来承载，该算子类继承自OpDef类。完成算子的原型定义等操作后，需要调用OP_ADD接口，传入算子类型（自定义算子类的类名），进行算子原型注册。详细内容请参考算子原型定义。
## 函数原型
## 参数说明
## 返回值说明
无
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [ACLNN 507035 — opType 与内置 ops_legacy 同名碰](../../../runbooks/compilation/aclnn_optype_collision_built_in_ops_legacy_507035.md)（`exemplifies`）：将 opType 从 `SoftplusV2Grad` 重命名为 `SoftplusV2GradCustom`，涉及 6 处注册点同步修改。；完成算子的原型定义等操作后，需要调用OP_ADD接口，传入算子类型（自定义算子类的类名），进行算子原型注册。。该 runbook 用内置 opType 碰撞复现说明 OP_ADD 注册类名参与运行时算子身份，修复必须同步重命名注册点而保持 ACLNN 接口名不变。
- [ACLNN 561102 单 dtype 原型注册与 opbuild 字节约束](../../../runbooks/compilation/aclnn_561102_dtype_opbuild.md)（`exemplifies`）：`OP_ADD` 同样受字节约束，不能只拆 `REG_OP` 而把所有 dtype 塞进单个 `OP_ADD`。；注册算子的原型定义，从而确保算子能够被框架正确识别、编译和执行。。运行手册展示 OP_ADD 原型中的 input dtype 字节数约束如何导致运行时 SelectBin 失败并要求拆分原型，API 卡定义 OP_ADD 的算子原型注册职责，是注册接口合同的具体故障实例。
- [缺 OP_PROTO_LIB 致空 axes 命中内置 InferShape](../../../runbooks/compilation/op_proto_lib_axes_infershape.md)（`exemplifies`）：完成算子的原型定义等操作后，需要调用OP_ADD接口，传入算子类型（自定义算子类的类名），进行算子原型注册。；**`cust_proto_obj` 未定义 `OP_PROTO_LIB`**：标准 CANN 模板（`npu_op_library` GRAPH 编译源时）会给 proto 目标加 `OP_PROTO_LIB`，使 `OP_ADD` 经 `OpImplRegisterV2` 把 OpDef 上 `SetInferShape`/`SetInferDataType` 注册的 gert V2 InferShape 注入 rt2 registry。接口卡给出注册动作，runbook 给出编译宏缺失导致 InferShape 不注入的具体故障。
- [算子原型定义](../../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/operator_prototype_definition.md)（`explains`）：完成算子的原型定义等操作后，需要调用OP_ADD接口，传入算子类型（自定义算子类的类名），进行算子原型注册。；文件末尾通过OP_ADD(AddCustom)注册算子类型，编译工具据此识别算子原型，并生成aclnn接口、图模式原型等相关代码。API 合同由指南的 AddCustom 放置位置与编译产物具体化。
<!-- cannbot:related:end -->
