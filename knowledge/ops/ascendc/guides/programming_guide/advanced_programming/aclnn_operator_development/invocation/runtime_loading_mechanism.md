---
type: Guide
title: 运行时加载机制
description: 本文是扩展内容，介绍算子开发完成后，编译产物如何被加载和执行，以及开发时的设计决策如何影响运行表现。本文从算子开发者视角梳理运行时调用的基本模型和代码写法对运行行为的影响。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/aclnn_operator_development/invocation/runtime_loading_mechanism.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 运行时加载机制

本文是扩展内容，介绍算子开发完成后，编译产物如何被加载和执行，以及开发时的设计决策如何影响运行表现。本文从算子开发者视角梳理运行时调用的基本模型和代码写法对运行行为的影响。
## 1. 算子是如何被调用的
### 二段式接口
单算子API采用二段式调用：aclnnXxxGetWorkspaceSize和aclnnXxx。
第一阶段：GetWorkspaceSize
此阶段主要在Host侧完成执行前准备：
1. 根据OpType、SoC、输入输出dtype/format/shape、属性等信息，优先尝试匹配aclnn参数缓存；缓存命中时复用已保存的binary和Tiling执行信息，跳过后续binary匹配和TilingFunc调用。
2. 缓存未命中时，根据算子注册信息和当前参数匹配可用的Kernel binary，或者调用算子注册的TilingFunc计算当前输入对应的TilingData、TilingKey、BlockDim。
3. 根据匹配到的binary配置和TilingKey，确定本次执行的Kernel入口。
4. 返回workspaceSize（需要分配的Device内存大小）和executor（承载调度上下文）。
此阶段可能触发的耗时操作：
- TilingFunc调用：执行Host侧C++函数。
- Binary查找：在文件系统中检索.o文件，涉及文件I/O。
第二阶段：Execute
此阶段将第一阶段准备好的全部信息打包提交到stream上执行。
### 为什么分两阶段
两阶段接口的目的是将执行前准备和执行下发分离：调用方可以先获取workspaceSize和executor，再根据自身资源管理方式选择按算子申请、统一内存池分配或复用已有workspace，并在提交Kernel前完成内存预算，可以减少频繁申请内存的开销和减少内存碎片。
### Binary匹配机制
运行时框架会基于OpType、目标芯片型号、输入输出dtype/format、shape支持范围、属性以及TilingKey/模板参数组合等信息匹配预编译的Kernel binary。
binary查找的优先级顺序：
- 运行时会先加载ASCEND_CUSTOM_OPP_PATH配置路径下的算子包，再查找默认CANN路径下的算子包。
- 默认安装到$ASCEND_OPP_PATH/vendors/的场景下，算子包优先级根据opp/vendors/config.ini中的load_priority决定，排在前面的算子包优先级更高。
- 动态库/静态库集成场景的加载方式与RUN包不同，应用直接链接或通过ASCEND_CUSTOM_OPP_PATH配置动态库时，应按算子动态库和静态库编译中的优先级规则处理。
## 2. 代码写法如何影响运行行为
开发者在编写算子代码时做出的选择，会直接影响编译产物的形态和运行时的表现。以下按影响阶段分为三类。
### 影响编译产物形态的写法
#### TilingKey / Kernel模板的分支数量
算子有两种分支策略可选：数字TilingKey或命名Kernel模板参数，两者互斥。

<!-- cannbot:related:start -->
## 相关

- [ACLNN 361001 — tilingKey 与 funcEntry 映射失](../../../../../runbooks/compilation/aclnn_361001_tilingkey_funcentry_sel_position.md)（`related`）：ACLNN 361001 — tilingKey 与 funcEntry 映射失 与《运行时加载机制》的实质衔接是：361001 由 host tilingKey 与 kernel funcEntry/SEL 位置不一致造成；key 宏、TPL 注册、struct include、运行时加载和相邻路由案例直接用于探测及修复。
- [ACLNN 507035 — opType 与内置 ops_legacy 同名碰](../../../../../runbooks/compilation/aclnn_optype_collision_built_in_ops_legacy_507035.md)（`related`）：ACLNN 507035 — opType 与内置 ops_legacy 同名碰 与《运行时加载机制》的实质衔接是：507035 此例由自定义 opType 与内置符号同名触发；OpDef/注册/launcher/kernel/CMake 六处改名及同名碰撞 runbook 共同构成完整修复链。
- [Aclnn算子工程化开发快速入门](../aclnn_quick_start.md)（`related`）：aclnn 快速入门把原型、Host Tiling、Kernel、编译部署和 API 调用串成端到端流程，可定位运行时加载所在阶段。
- [CMake函数参考（附录）](../appendix/cmake_function_reference.md)（`related`）：CMake函数参考（附录） 与《运行时加载机制》的实质衔接是：CMake 函数参考中的工程函数由算子开发、编译选项、编译脚本、库编译和 UT 指南实际消费；FAQ 卡验证其构建阶段失败信号。
- [extern 预编译 kernel 自定义包致 aclnn 161001](../../../../../runbooks/compilation/extern_kernel_aclnn_161001.md)（`related`）：extern 预编译 kernel 自定义包致 aclnn 161001 与《运行时加载机制》的衔接是：该打包故障的验证链是 ACLNN 错误→检查 binary.json/二进制入口→探测符号→确认运行时加载；候选正好覆盖各个可执行检查点。
- [单算子API调用](single_operator_api_call.md)（`related`）：单算子 API 调用给出 aclnnXxxGetWorkspaceSize/aclnnXxx 二段式调用代码，是运行时加载机制最终暴露给应用的执行入口。
- [多算子包组织](../compilation_and_deployment/multi_operator_package.md)（`related`）：多算子包组织影响注册信息、库拆分和加载顺序，可解释多个 op 同包时运行时如何定位正确实现。
- [算子动态库和静态库编译](../compilation_and_deployment/dynamic_static_lib_compilation.md)（`related`）：《算子动态库和静态库编译》说明介绍将自定义算子工程编译为动态库或静态库的方法，支持应用直接链接或集成到其他工程中。；《运行时加载机制》说明本文是扩展内容，介绍算子开发完成后，编译产物如何被加载和执行，以及开发时的设计决策如何影响运行表现。本文从算子开发者视角梳理运行时调用的基本模型和代码写法对运行行为的影响。。二者在SHARED/STATIC产物通过npu_op_package与CMake生成，并分别进入直接链接、运行时加载和常规部署流程上存在可执行的直接衔接。
- [编译与部署基本流程](../compilation_and_deployment/basic_process.md)（`related`）：编译与部署基本流程决定 .so、算子包和配置文件的落盘位置，直接影响运行时按路径发现并加载算子实现。
- [适配插件开发](../../ai_framework_adaptation/onnx_framework/adaptation_plugin_development.md)（`related`）：插件 so 通过环境路径进入运行时发现链，加载机制解释文件布局和查找时机。
- [高级编程交叉编译](../compilation_and_deployment/cross_compilation.md)（`same_topic`）：高级编程交叉编译 与《运行时加载机制》的实质衔接是：交叉编译需先生成本机 tiling 库再构建目标包；基本编译、CMake、runtime、compiler/RTC/compile-log 接口共同支撑配置和诊断。
<!-- cannbot:related:end -->
