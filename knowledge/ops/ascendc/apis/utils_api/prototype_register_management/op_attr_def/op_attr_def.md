---
type: API
title: OpAttrDef
description: OpAttrDef算子属性定义接口索引。
tags: [task.lookup, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpAttrDef/OpAttrDef.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# OpAttrDef

OpAttrDef 用于定义算子属性，支持通过链式调用设置属性名称、数据类型（Bool/Float/Int/String 及对应 List 变体）、属性类型（OPTIONAL 或 REQUIRED）、默认值、版本号和注释。OPTIONAL 属性必须设置默认值。Version 接口用于新增可选属性时保持 aclnn 接口兼容性，版本号从 1 开始连续配置。
Comment 接口用于设置算子属性注释，在自动生成算子原型头文件时同步生成注释，辅助理解算子原型并自动生成文档说明。
本入口包含 OpAttrDef 类成员函数说明与 Comment 接口说明两部分导航。

<!-- cannbot:related:start -->
## 相关

- [AICPU launcher 缺 OP_ATTR_NAMES 编译错](../../../../runbooks/compilation/aicpu_launcher_op_attr_names.md)（`exemplifies`）：《AICPU launcher 缺 OP_ATTR_NAMES 编译错》的任务是“无属性 regbase 算子的 ADD_TO_LAUNCHER_LIST_AICPU 调用若照搬 AICORE 写法省略 OP_ATTR_NAMES()，AICPU 宏会把第二个形参位（op::FVector<std::string>&，属性名向量）错绑到 OP_INPUT(...)，触发引用类型不匹配编译错。判别=build.sh --pkg 编译期报 invalid initialization of reference of type 'op::FVector<std::basic_string<char> >&' from expression of type 'op::OpInput<...>'，定位行紧随算子名后缺 OP_ATTR_NAMES()。AICORE 变体无该形参位，省略合法，二者宏签名不可互换。”。《OpAttrDef》具体提供“OpAttrDef算子属性定义接口索引。”，它直接用于AICPU launcher 的 OP_ATTR_NAMES 形参、属性定义和 AICPU 原型。
- [TilingKey 缓存 correction 致 tilingdata 复用](../../../../runbooks/compilation/ge_tilingkey_cache_reuse_per_call_attr_pollution.md)（`exemplifies`）：OpAttrDef 与《TilingKey 缓存 correction 致 tilingdata 复用》的实质衔接是：OpAttrDef 定义属性名、类型、OPTIONAL/REQUIRED、默认值和 Version；Comment 生成原型注释，OpDef::Attr 挂载属性，Host TilingData 传递与缓存故障说明 runtime 属性进入 kernel 时的后续契约。
- [aclnn TilingData 缓存致 runtime attr 陈旧](../../../../runbooks/precision/aclnn_tilingdata_runtime_attr.md)（`exemplifies`）：OpAttrDef 与《aclnn TilingData 缓存致 runtime attr 陈旧》的实质衔接是：OpAttrDef 定义属性名、类型、OPTIONAL/REQUIRED、默认值和 Version；Comment 生成原型注释，OpDef::Attr 挂载属性，Host TilingData 传递与缓存故障说明 runtime 属性进入 kernel 时的后续契约。
- [算子原型定义](../../../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/operator_prototype_definition.md)（`explains`）：OpAttrDef 与《算子原型定义》的实质衔接是：OpAttrDef 定义属性名、类型、OPTIONAL/REQUIRED、默认值和 Version；Comment 生成原型注释，OpDef::Attr 挂载属性，Host TilingData 传递与缓存故障说明 runtime 属性进入 kernel 时的后续契约。
- [通过TilingData传递属性信息](../../../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/tiling_data_attributes.md)（`explains`）：OpAttrDef 与《通过TilingData传递属性信息》的实质衔接是：OpAttrDef 定义属性名、类型、OPTIONAL/REQUIRED、默认值和 Version；Comment 生成原型注释，OpDef::Attr 挂载属性，Host TilingData 传递与缓存故障说明 runtime 属性进入 kernel 时的后续契约。
- [AddAttr](../../tiling_tuning/context_builder/add_attr.md)（`related`）：AddAttr 与《OpAttrDef》的实质衔接是：AddAttr 是 ContextBuilder 链式构造 tiling/kernel 上下文的一环；构造、I/O、算子名、平台、CompileInfo 和 Build 方法共同决定属性如何进入 KernelRunContext。
- [Attr（OpDef）](../op_def/attr.md)（`related`）：OpAttrDef 与《Attr（OpDef）》的实质衔接是：OpAttrDef 定义属性名、类型、OPTIONAL/REQUIRED、默认值和 Version；Comment 生成原型注释，OpDef::Attr 挂载属性，Host TilingData 传递与缓存故障说明 runtime 属性进入 kernel 时的后续契约。
- [Comment（原型注册管理）](comment.md)（`same_topic`）：OpAttrDef 与《Comment（原型注册管理）》的实质衔接是：OpAttrDef 定义属性名、类型、OPTIONAL/REQUIRED、默认值和 Version；Comment 生成原型注释，OpDef::Attr 挂载属性，Host TilingData 传递与缓存故障说明 runtime 属性进入 kernel 时的后续契约。
- [OpAttrDef](op_attr_def_functions.md)（`same_topic`）：OpAttrDef 与《OpAttrDef》的实质衔接是：OpAttrDef 定义属性名、类型、OPTIONAL/REQUIRED、默认值和 Version；Comment 生成原型注释，OpDef::Attr 挂载属性，Host TilingData 传递与缓存故障说明 runtime 属性进入 kernel 时的后续契约。
- [Version](../op_param_def/version.md)（`same_topic`）：OpAttrDef 与《Version》的实质衔接是：OpAttrDef 定义属性名、类型、OPTIONAL/REQUIRED、默认值和 Version；Comment 生成原型注释，OpDef::Attr 挂载属性，Host TilingData 传递与缓存故障说明 runtime 属性进入 kernel 时的后续契约。
<!-- cannbot:related:end -->
