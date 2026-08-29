---
type: Guide
title: 编译过程调试
description: 本文是扩展内容，介绍算子工程编译过程中的调试方法。算子工程编译涉及代码生成、Host侧编译、Kernel侧编译、打包部署四个阶段，默认输出通常不足以定位根因，下文按阶段介绍调试手段，并附常见错误的诊断方法。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/aclnn_operator_development/compilation_and_deployment/compilation_debug.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# 编译过程调试

本文是扩展内容，介绍算子工程编译过程中的调试方法。算子工程编译涉及代码生成、Host侧编译、Kernel侧编译、打包部署四个阶段，默认输出通常不足以定位根因，下文按阶段介绍调试手段，并附常见错误的诊断方法。
## 生成代码调试
npu_op_code_gen在cmake configure阶段自动生成aclnn调用代码和算子原型定义代码。生成产物位于ASCEND_AUTOGEN_PATH目录，默认是/autogen；按本文示例使用build_out时，对应目录为build_out/autogen。当原型定义有误或生成结果与预期不符时，需要检查这些文件。
### 生成产物目录
以AddCustom工程为例，配置完成后build_out/autogen/下会生成aclnn调用代码、算子原型定义代码和若干编译配置文件。下方仅列出排查代码生成问题时常用的关键产物；多算子工程会为每个算子生成对应的aclnn_.cpp和aclnn_.h。
### 常见问题排查场景
问题：查看什么
aclnn接口参数与原型定义不匹配：检查aclnn_.h中的函数签名，确认输入输出和属性参数是否正确映射。
入图场景算子注册信息异常：检查op_proto.cc中的注册宏，确认OpType、dtype/format是否与Host侧定义一致。
某个算子的调用代码未生成：检查npu_op_code_gen的SRC参数是否包含了该算子的Host侧源文件。
JOIN_OP_DEF相关芯片型号异常：JOIN_OP_DEF=True时算子构建阶段不再显式传入ASCEND_COMPUTE_UNIT，需结合configure日志、op_proto.cc中的AddConfig和CMakePresets.json中的芯片型号确认目标型号是否被覆盖。
### 强制重新生成
修改文件后，如果怀疑历史产物残留导致问题，可以手动清理后重新configure：
## Host侧编译调试
Host侧构建时，默认只输出编译目标的摘要信息，不显示实际执行的编译和链接命令。通过VERBOSE机制可以打印完整的命令行，用于排查头文件路径、链接库、编译选项等问题。
### 方式一：构建时开启verbose
在构建命令中指定verbose，打印每条编译和链接命令：
输出示例：
每行输出包含完整的编译器调用，可以看到：
- 实际的编译器路径（如/usr/bin/c++）。
- 宏定义（-D）和头文件搜索路径（-I）。
- 编译选项（如-fvisibility=hidden、-g、-O2）。
- 链接库路径（-L）和链接库（-l）。
### 方式二：cmake配置CMAKE_VERBOSE_MAKEFILE
在cmake configure阶段开启verbose，后续所有make调用都会自动打印完整命令：
与方式一效果相同，区别在于设置持久化在CMakeCache.txt中，无需每次构建时重复指定。
### 常见问题排查场景
问题：查看什么
头文件找不到
