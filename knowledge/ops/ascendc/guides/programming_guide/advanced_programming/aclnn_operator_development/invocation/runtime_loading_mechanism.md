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
