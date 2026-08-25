---
type: Guide
title: Aclnn算子工程化开发快速入门
description: 本文是基础内容，通过一个完整的AddCustom算子示例，帮助您在5分钟内跑通从创建工程、补充算子实现、编译部署到单算子API调用验证的端到端流程。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/aclnn_operator_development/aclnn_quick_start.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# Aclnn算子工程化开发快速入门

本文是基础内容，通过一个完整的AddCustom算子示例，帮助您在5分钟内跑通从创建工程、补充算子实现、编译部署到单算子API调用验证的端到端流程。
## 前置环境准备
### 编译工具链
在开始之前，请确保系统中已安装以下工具：
工具：版本建议：说明
CMake：≥ 3.19：构建系统生成器。
GCC / G++：≥ 7.5：C++编译器。
Python：≥ 3.9：msOpGen工具运行依赖。
Make：—：构建执行工具。
msOpGen是CANN软件包提供的算子工程生成工具。加载CANN环境变量后，可通过msopgen --help验证工具是否可用；如果命令不在PATH中，也可使用${INSTALL_DIR}/python/site-packages/bin/msopgen调用，其中${INSTALL_DIR}为CANN软件安装路径。
可通过以下命令检查工具版本：
### CANN环境变量
编译和运行均依赖CANN提供的环境变量，在开始任何步骤前，先加载环境变量：
> 每次打开新终端时都需要重新执行该命令。后续步骤中不再重复提示。
## 快速入门流程
### 步骤概览
步骤：内容：预计时间
步骤1：创建工程：1分钟
步骤2：查看目录结构：—
步骤3：修改Kernel侧代码：1分钟
步骤4：修改Host侧Tiling：1分钟
步骤5：编译：1分钟
步骤6：部署：—
步骤7：调用算子：1分钟
### 创建工程
编写算子原型定义文件add_custom.json（建议放在全英文路径下），然后使用msOpGen工具生成工程骨架。JSON中每个输入/输出的format和type列表长度必须一致，保持一一对应关系。
-   -i：指定算子原型定义文件add_custom_.json所在路径，请根据实际情况修改。
-   -c：ai_core-ascendxxyy代表算子在AI Core上执行，ascendxxyy为昇腾AI处理器的型号soc_version。JSON中的type/format列表定义算子支持的数据类型和格式组合。msOpGen会基于这些信息生成对应的Kernel编译配置。
-   -lan：参数cpp代表算子基于Ascend C编程框架，使用C/C++编程语言开发。
-   -out：生成文件所在路径，可配置为绝对路径或者相对路径，并且工具执行用户对路径具有可读写权限。若不配置，则默认生成在执行命令的当前路径。
将ascendxxyy替换为您的AI处理器型号soc_version。msOpGen会自动将芯片型号映射为框架统一标识，并写入CMakePresets.json的ASCEND_COMPUTE_UNIT和原型定义的AddConfig中。
### 查看目录结构
msOpGen生成的工程目录结构如下：
需要修改的文件已用[需修改]标注，后续步骤将逐一修改这些文件。

<!-- cannbot:related:start -->
## 相关

- [PyTorch框架](../ai_framework_adaptation/pytorch_framework.md)（`related`）：PyTorch 自定义算子适配的一条主要落地路线是 ACLNN 工程化；快速入门把工程创建、实现、部署和单算子调用验证串成闭环。
- [算子功能设计](design_and_implementation/operator_function_design.md)（`related`）：《算子功能设计》说明本文属于基础内容，介绍在编写自定义算子代码前需要完成的功能设计，包括将计算语义转换为工程实现，以及明确需要编写的工程文件。；《Aclnn算子工程化开发快速入门》说明本文是基础内容，通过一个完整的AddCustom算子示例，帮助您在5分钟内跑通从创建工程、补充算子实现、编译部署到单算子API调用验证的端到端流程。。二者在功能设计明确拆成原型、Host Tiling和Kernel三类代码，后续章节分别落实属性、多分支、输出shape、编译部署与快速入门上存在可执行的直接衔接。
- [算子动态库和静态库编译](compilation_and_deployment/dynamic_static_lib_compilation.md)（`related`）：《算子动态库和静态库编译》说明介绍将自定义算子工程编译为动态库或静态库的方法，支持应用直接链接或集成到其他工程中。；《Aclnn算子工程化开发快速入门》说明本文是基础内容，通过一个完整的AddCustom算子示例，帮助您在5分钟内跑通从创建工程、补充算子实现、编译部署到单算子API调用验证的端到端流程。。二者在SHARED/STATIC产物通过npu_op_package与CMake生成，并分别进入直接链接、运行时加载和常规部署流程上存在可执行的直接衔接。
- [缓存一致性](../memory_model/cache_coherence.md)（`related`）：aclnn Host/Kernel 调用边界涉及数据生产和消费时机，一致性指南可用于判断同步和 cache 维护位置。
- [编译与部署基本流程](compilation_and_deployment/basic_process.md)（`related`）：编译与部署基本流程 与《Aclnn算子工程化开发快速入门》的实质衔接是：编译部署流程直接分支到动态/静态库、交叉编译、调试、加速、多算子包、CMake 和运行时加载；arch 子目录故障验证 SoC 专属源码必须在构建期隔离。
- [运行时加载机制](invocation/runtime_loading_mechanism.md)（`related`）：aclnn 快速入门把原型、Host Tiling、Kernel、编译部署和 API 调用串成端到端流程，可定位运行时加载所在阶段。
- [高级编程基本流程](design_and_implementation/kernel_operator_implementation.md)（`related`）：《高级编程基本流程》说明本文属于基础内容，介绍aclnn工程化算子开发方式中Kernel侧的基本接入流程，重点说明Kernel入口函数格式、参数顺序、TilingData处理和编译期信息获取方式。Global Memory地址绑定、UB管理、数据搬运、计算和同步等Kernel核心实现方法，请参考核函数。；《Aclnn算子工程化开发快速入门》说明本文是基础内容，通过一个完整的AddCustom算子示例，帮助您在5分钟内跑通从创建工程、补充算子实现、编译部署到单算子API调用验证的端到端流程。。二者在Kernel侧基本接入的参数顺序、TilingData和编译期信息必须与原型、Host Tiling、编译部署及动态输入设计一致上存在可执行的直接衔接。
- [高级编程概述](overview.md)（`related`）：概述明确把跑通 AddCustom 快速入门作为进入工程化开发的第一验证门槛，二者形成推荐执行顺序。
- [单算子API调用](invocation/single_operator_api_call.md)（`same_topic`）：焦点处理aclnn 两段式单算子调用的编译、部署和运行流程；Aclnn算子工程化开发快速入门正文界定“本文是基础内容，通过一个完整的AddCustom算子示例，帮助您在5分钟内跑通从创建工程、补充算子实现、编译部署到单算子API调用验证的端到端流程”。候选覆盖单算子调用前的编译部署、动态加载、调用样例、stream 缓存一致性和延迟回调生命周期。
<!-- cannbot:related:end -->
