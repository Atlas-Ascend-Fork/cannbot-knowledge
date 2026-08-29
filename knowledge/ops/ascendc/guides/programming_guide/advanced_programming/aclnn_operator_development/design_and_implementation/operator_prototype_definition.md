---
type: Guide
title: 算子原型定义
description: 本文属于基础内容，介绍如何通过算子原型定义描述算子对外暴露的接口和支持范围。本文承接算子功能设计的结论，说明如何将功能设计中的输入输出、属性、dtype/format和Tiling函数关联落地为OpDef代码，并介绍图模式下的输出shape和dtype推导配置。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/operator_prototype_definition.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# 算子原型定义

本文属于基础内容，介绍如何通过算子原型定义描述算子对外暴露的接口和支持范围。本文承接算子功能设计的结论，说明如何将功能设计中的输入输出、属性、dtype/format和Tiling函数关联落地为OpDef代码，并介绍图模式下的输出shape和dtype推导配置。
## 原型定义放在哪里
在AddCustom样例工程中，算子原型定义位于Host侧实现文件：
该文件中同时包含三类内容：
内容：作用
TilingFunc：Host侧Tiling函数，负责计算Kernel启动和分块参数
InferShape、InferDataType：图模式下的输出shape和dtype推导函数，仅在需要支持图模式时编写
class AddCustom : public OpDef：算子原型定义，描述输入、输出、属性、Tiling关联
本文重点讲class AddCustom : public OpDef中的原型定义内容，同时说明它和Tiling函数之间的连接关系，并补充图模式下关联推导函数的方法。
## 定义OpDef类并注册算子
算子原型通过一个继承自OpDef的C++类承载。类名通常与算子类型保持一致。AddCustom的算子类型为AddCustom，因此定义AddCustom类。
这里有两个关键点：
- 构造函数通过OpDef(name)初始化基类，后续的Input、Output、Attr、AICore等声明都写在构造函数中。
- 文件末尾通过OP_ADD(AddCustom)注册算子类型，编译工具据此识别算子原型，并生成aclnn接口、图模式原型等相关代码。
## 定义输入和输出
输入输出定义来自功能设计阶段的结论。AddCustom有两个输入x、y，一个输出z，三个Tensor共同表达z = x + y的计算语义，因此都声明为REQUIRED。基础样例没有属性，输入输出声明就是原型定义中最先落地的接口内容。
输入输出参数说明如下：
原型项：参数：作用
Input/Output：输入输出名称：声明输入输出名称，名称需要和功能设计中的参数名称一致。声明顺序会影响aclnn接口参数顺序和Kernel入口参数顺序。
Input/Output：ParamType：声明参数提供方式。REQUIRED表示每次调用都必须提供，OPTIONAL表示部分场景可以省略，DYNAMIC表示数量随调用变化。
Input/Output：DataType：声明输入输出支持的dtype。多个dtype按列表顺序和format列表一一对应。
Input/Output：Format：声明输入输出支持的format。多个format按列表顺序和dtype列表一一对应。
同一个输入或输出支持多组dtype/format时，DataType和Format列表需要按位置对应。例如下面的写法表示支持DT_FLOAT16 + FORMAT_ND、DT_FLOAT + FORMAT_ND和DT_INT32 + FORMAT_ND三组组合。

<!-- cannbot:related:start -->
## 相关

- [原型注册接口（OP_ADD）](../../../../../apis/utils_api/prototype_register_management/op_add.md)（`explains`）：完成算子的原型定义等操作后，需要调用OP_ADD接口，传入算子类型（自定义算子类的类名），进行算子原型注册。；文件末尾通过OP_ADD(AddCustom)注册算子类型，编译工具据此识别算子原型，并生成aclnn接口、图模式原型等相关代码。API 合同由指南的 AddCustom 放置位置与编译产物具体化。
<!-- cannbot:related:end -->
