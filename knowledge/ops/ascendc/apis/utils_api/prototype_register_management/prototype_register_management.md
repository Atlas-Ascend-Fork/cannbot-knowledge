---
type: API
title: 原型注册与管理
description: 算子原型注册与管理接口索引。
tags: [task.lookup, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/prototype_register_management.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 原型注册与管理

算子原型注册与管理接口的总入口，包含注册宏（OP_ADD、REGISTER_OP_AICORE_CONFIG）和算子定义类（OpDef、OpParamDef、OpAttrDef）。通过 OpAICoreDef、OpAICPUDef、OpHostCPUDef 分别定义不同执行引擎的行为，OpAICoreConfig 配置编译选项，OpMC2Def 支持多机通信场景。这些接口共同构成 Ascend C 算子注册的完整框架。

<!-- cannbot:related:start -->
## 相关

- [缺 OP_PROTO_LIB 致空 axes 命中内置 InferShape](../../../runbooks/compilation/op_proto_lib_axes_infershape.md)（`exemplifies`）：《缺 OP_PROTO_LIB 致空 axes 命中内置 InferShape》的任务是“cust_proto_obj 未加 OP_PROTO_LIB 时 OP_ADD 走默认分支，自定义 V2 gert InferShape 不注入 rt2 registry，框架回落 CANN 内置 EuclideanNormInferShape（reduce_ops.cc），全局 first-wins 使 COMMON_INFER_FUNC_REG 无法覆盖；内置把空 axes(shape=[0]) 当 passthrough 而非 full reduce，输出 shape 错误。”。《原型注册与管理》具体提供“算子原型注册与管理接口索引。”，它直接用于OP_PROTO_LIB、OP_ADD 和 InferShape 注册路由对空 axes shape 的影响。
- [算子原型定义](../../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/operator_prototype_definition.md)（`explains`）：《算子原型定义》给出“本文属于基础内容，介绍如何通过算子原型定义描述算子对外暴露的接口和支持范围。本文承接算子功能设计的结论，说明如何将功能设计中的输入输出、属性、dtype/format和Tiling函数关联落地为OpDef代码，并介绍图模式下的输出shape和dtype推导配置。”；该约束/探针可直接复现、解释或前置验证《原型注册与管理》中的“算子原型注册与管理接口索引。”。
- [Comment](op_param_def/comment.md)（`same_topic`）：Comment 与《原型注册与管理》的实质衔接是：Comment 写入 OpParamDef 的 input/output 注释并传播到自动生成原型和文档；构造、Input/Output、OpDef 与另一注册层 Comment 是同一元数据链。
<!-- cannbot:related:end -->
