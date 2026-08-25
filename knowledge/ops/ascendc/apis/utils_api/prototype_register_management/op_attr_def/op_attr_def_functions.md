---
type: API
title: OpAttrDef
description: class OpAttrDef {
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpAttrDef/OpAttrDef_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---
# OpAttrDef

## 功能说明
定义算子属性。
## 函数原型
## 函数说明
OpAttrDef类成员函数说明
函数名称：入参说明：功能说明
OpAttrDef：name: 算子属性名称。：构造算子属性定义OpAttrDef，并设置属性名称。
OpAttrDef：attr_def: 已构造完成的算子属性OpAttrDef。：拷贝构造OpAttrDef，复制被拷贝对象的属性名称、属性数据类型、属性类型、默认值、版本号和注释等配置。
AttrType：attr_type: 属性类型：设置算子属性类型，取值为：OPTIONAL（可选）、REQUIRED（必选）。
Bool：无：设置算子属性数据类型为Bool
Bool：value：设置算子属性数据类型为Bool，并设置属性默认值为value。属性类型设置为OPTIONAL时必须调用该类接口设置默认值。
Float：无：设置算子属性数据类型为Float
Float：value：设置算子属性数据类型为Float，并设置属性默认值为value。属性类型设置为OPTIONAL时必须调用该类接口设置默认值。
Int：无：设置算子属性数据类型为Int
Int：value：设置算子属性数据类型为Int，并设置属性默认值为value。属性类型设置为OPTIONAL时必须调用该类接口设置默认值。
String：无：设置算子属性数据类型为String
String：value：设置算子属性数据类型为String，并设置属性默认值为value。属性类型设置为OPTIONAL时必须调用该类接口设置默认值。
ListBool：无：设置算子属性数据类型为ListBool
ListBool：value：设置算子属性数据类型为ListBool，并设置属性默认值为value。属性类型设置为OPTIONAL时必须调用该类接口设置默认值。
ListFloat：无：设置算子属性数据类型为ListFloat
ListFloat：value：设置算子属性数据类型为ListFloat，并设置属性默认值为value。属性类型设置为OPTIONAL时必须调用该类接口设置默认值。
ListInt：无：设置算子属性数据类型为ListInt
ListInt：value：设置算子属性数据类型为ListInt，并设置属性默认值为value。属性类型设置为OPTIONAL时必须调用该类接口设置默认值。
ListListInt：无：设置算子属性数据类型为ListListInt
ListListInt：value

<!-- cannbot:related:start -->
## 相关

- [AICPU launcher 缺 OP_ATTR_NAMES 编译错](../../../../runbooks/compilation/aicpu_launcher_op_attr_names.md)（`exemplifies`）：《AICPU launcher 缺 OP_ATTR_NAMES 编译错》的任务是“无属性 regbase 算子的 ADD_TO_LAUNCHER_LIST_AICPU 调用若照搬 AICORE 写法省略 OP_ATTR_NAMES()，AICPU 宏会把第二个形参位（op::FVector<std::string>&，属性名向量）错绑到 OP_INPUT(...)，触发引用类型不匹配编译错。判别=build.sh --pkg 编译期报 invalid initialization of reference of type 'op::FVector<std::basic_string<char> >&' from expression of type 'op::OpInput<...>'，定位行紧随算子名后缺 OP_ATTR_NAMES()。AICORE 变体无该形参位，省略合法，二者宏签名不可互换。”。《OpAttrDef》具体提供“class OpAttrDef {”，它直接用于AICPU launcher 的 OP_ATTR_NAMES 形参、属性定义和 AICPU 原型。
- [Attr（OpDef）](../op_def/attr.md)（`related`）：《OpAttrDef》说明class OpAttrDef {；《Attr（OpDef）》说明注册算子属性参数。 当需要设置的参数不参与kernel侧计算时，可以将该参数注册为算子属性参数。。二者在OpDef::Attr注册属性时使用OpAttrDef描述属性定义，二者共同确定原型属性的类型与对外接口上存在可执行的直接衔接。
- [OpAttrDef](op_attr_def.md)（`same_topic`）：OpAttrDef 与《OpAttrDef》的实质衔接是：OpAttrDef 定义属性名、类型、OPTIONAL/REQUIRED、默认值和 Version；Comment 生成原型注释，OpDef::Attr 挂载属性，Host TilingData 传递与缓存故障说明 runtime 属性进入 kernel 时的后续契约。
<!-- cannbot:related:end -->
