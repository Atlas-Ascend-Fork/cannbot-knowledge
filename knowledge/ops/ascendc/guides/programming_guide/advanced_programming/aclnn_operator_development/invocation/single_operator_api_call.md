---
type: Guide
title: 单算子API调用
description: 本文是基础内容，介绍单算子API调用——即通过C/C++调用aclnn接口完成异构计算的过程。aclnn接口和实现已经随自定义算子包交付，因此调用前需要先完成自定义算子包部署。运行时需要可用NPU环境；计算过程中使用的输入输出Tensor、Device内存、workspace、stream等资源由调用方负责申请和释放。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/aclnn_operator_development/invocation/single_operator_api_call.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 单算子API调用

本文是基础内容，介绍单算子API调用——即通过C/C++调用aclnn接口完成异构计算的过程。aclnn接口和实现已经随自定义算子包交付，因此调用前需要先完成自定义算子包部署。运行时需要可用NPU环境；计算过程中使用的输入输出Tensor、Device内存、workspace、stream等资源由调用方负责申请和释放。
## 调用前检查
调用单算子API前，先确认以下条件已经满足：
-   调用算子的运行环境有NPU设备。
-   完成自定义算子工程的创建。
-   完成算子原型定义、Kernel侧实现和Host侧Tiling实现。
-   对于算子包编译场景，参考算子工程编译与部署完成算子包的编译部署。算子二进制编译开关ENABLE_BINARY_PACKAGE默认开启；如果工程中显式设置为False，需要改为True后重新编译部署。
算子编译部署后，会在算子包安装目录下的op_api目录生成单算子调用的头文件aclnn_.h和动态库libcust_opapi.so。
以默认安装场景为例，单算子调用的头文件和动态库所在的目录结构如下所示：
-   对于算子动态库或静态库编译场景，参考算子动态库和静态库编译完成算子的编译安装。其中CMAKE_INSTALL_PREFIX为开发者在cmake文件中配置的安装路径。
-   动态库路径：${CMAKE_INSTALL_PREFIX}/lib/libcust_opapi.so
-   静态库路径：${CMAKE_INSTALL_PREFIX}/lib/lib${vendor_name}.a
-   头文件路径：${CMAKE_INSTALL_PREFIX}/include
## 基本原理
完成自定义算子编译后，算子工程会基于算子原型定义自动生成单算子API头文件aclnn_.h，并编译生成单算子API动态库libcust_opapi.so。调用时导入该头文件、链接该动态库后，就可以直接调用自定义算子。
单算子API一般是“两段式接口”：
其中：
- aclnnXxxGetWorkspaceSize是第一段接口，用于计算本次调用需要的workspace大小，按照workspaceSize申请NPU内存。
- aclnnXxx是第二段接口，使用第一段接口得到的workspaceSize、executor以及调用方申请的workspace，在指定stream上执行实际计算。
- Xxx来自算子原型注册时传入的算子类型。例如AddCustom算子生成的接口名为aclnnAddCustomGetWorkspaceSize和aclnnAddCustom。
## 准备调用工程
本节以AddCustom自定义算子调用为例，介绍如何编写单算子调用的代码逻辑。其他算子的调用逻辑与AddCustom算子类似，请根据实际情况自行修改代码。该工程包含两个文件：
以下是关键步骤的代码示例，不可以直接拷贝编译运行，仅供参考，调用接口后，需增加异常处理的分支，并记录报错日志、提示日志，此处不一一列举。

<!-- cannbot:related:start -->
## 相关

- [RunOpApi 延迟回调需按值捕获局部 launch vector](../../../../../runbooks/compilation/runopapi_callbacks_capture_launch_state_by_value.md)（`related`）：焦点处理aclnn 两段式单算子调用的编译、部署和运行流程；RunOpApi 延迟回调需按值捕获局部 launch vector正文界定“多 tensor 合并到一个 RunOpApi lambda 时，引用捕获局部 pointer/tiling vector 会悬空；按值捕获保住提交参数”。候选覆盖单算子调用前的编译部署、动态加载、调用样例、stream 缓存一致性和延迟回调生命周期。
- [算子动态库和静态库编译](../compilation_and_deployment/dynamic_static_lib_compilation.md)（`related`）：《算子动态库和静态库编译》说明介绍将自定义算子工程编译为动态库或静态库的方法，支持应用直接链接或集成到其他工程中。；《单算子API调用》说明本文是基础内容，介绍单算子API调用——即通过C/C++调用aclnn接口完成异构计算的过程。aclnn接口和实现已经随自定义算子包交付，因此调用前需要先完成自定义算子包部署。运行时需要可用NPU环境；计算过程中使用的输入输出Tensor、Device内存、workspace、stream等资源由调用方负责申请和释放。。二者在SHARED/STATIC产物通过npu_op_package与CMake生成，并分别进入直接链接、运行时加载和常规部署流程上存在可执行的直接衔接。
- [缓存一致性](../../memory_model/cache_coherence.md)（`related`）：焦点处理aclnn 两段式单算子调用的编译、部署和运行流程；缓存一致性正文界定“本文介绍NPU编程中常见的缓存一致性问题，说明DCache、ICache、SIMT DCache与GM的数据一致性”。候选覆盖单算子调用前的编译部署、动态加载、调用样例、stream 缓存一致性和延迟回调生命周期。
- [编译与部署基本流程](../compilation_and_deployment/basic_process.md)（`related`）：编译与部署基本流程 与《单算子API调用》的实质衔接是：编译部署流程直接分支到动态/静态库、交叉编译、调试、加速、多算子包、CMake 和运行时加载；arch 子目录故障验证 SoC 专属源码必须在构建期隔离。
- [运行时加载机制](runtime_loading_mechanism.md)（`related`）：单算子 API 调用给出 aclnnXxxGetWorkspaceSize/aclnnXxx 二段式调用代码，是运行时加载机制最终暴露给应用的执行入口。
- [Aclnn算子工程化开发快速入门](../aclnn_quick_start.md)（`same_topic`）：焦点处理aclnn 两段式单算子调用的编译、部署和运行流程；Aclnn算子工程化开发快速入门正文界定“本文是基础内容，通过一个完整的AddCustom算子示例，帮助您在5分钟内跑通从创建工程、补充算子实现、编译部署到单算子API调用验证的端到端流程”。候选覆盖单算子调用前的编译部署、动态加载、调用样例、stream 缓存一致性和延迟回调生命周期。
- [基本开发流程](../../operator_graph_development/basic_development_flow.md)（`same_topic`）：焦点处理aclnn 两段式单算子调用的编译、部署和运行流程；基本开发流程正文界定“该开发流程以工程化算子开发为基础，除了需要提供工程化算子开发中的算子实现文件外，还需要额外交付算子入图的代码文件。本节仅提供算子入图代码文件的开发指导”。候选覆盖单算子调用前的编译部署、动态加载、调用样例、stream 缓存一致性和延迟回调生命周期。
- [高级编程调用样例](../../ai_framework_adaptation/onnx_framework/call_examples.md)（`same_topic`）：焦点处理aclnn 两段式单算子调用的编译、部署和运行流程；高级编程调用样例正文界定“完成了ONNX框架的适配插件开发后，即可实现从ONNX框架调用Ascend C自定义算子。下面以一个仅包含LeakyRelu算子的ONNX框架网络为例（该网络中的LeakyRelu算子通过适配插件映射为自定义的LeakyRelu算子），呈现”。候选覆盖单算子调用前的编译部署、动态加载、调用样例、stream 缓存一致性和延迟回调生命周期。
<!-- cannbot:related:end -->
