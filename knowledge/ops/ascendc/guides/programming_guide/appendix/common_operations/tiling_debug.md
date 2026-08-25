---
type: Guide
title: TilingDebug
description: 通过OpTilingRegistry加载编译后的Tiling动态库，使用ContextBuilder构建TilingContext并获取Tiling函数指针进行单独调测。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/appendix/common_operations/tiling_debug.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 如何进行Tiling调测

在工程化算子开发过程中，开发者需实现Tiling函数，该函数原型是固定的，接受TilingContext作为输入。框架负责构造TilingContext并调用Tiling函数。若需单独进行Tiling调测，开发者可通过OpTilingRegistry加载编译后的Tiling动态库，获取Tiling函数的指针并进行调用，调用时Tiling函数的TilingContext入参使用ContextBuilder构建。
以下是具体步骤：
1.  参考工程化算子开发的开发步骤，完成算子实现，并通过算子包编译或算子动态库编译获取对应的Tiling动态库文件。
-   算子包编译：Tiling实现对应的动态库为算子包部署目录下的liboptiling.so。具体路径可参考算子包部署。
-   动态库编译：Tiling实现集成在算子动态库libcust_opapi.so中。具体路径可参考算子动态库和静态库编译。
2.  编写测试代码。
-   使用ContextBuilder配置输入输出Tensor的形状、数据类型、格式及平台信息等，构建TilingContext。
-   通过OpTilingRegistry的LoadTilingLibrary接口加载Tiling动态库；使用GetTilingFunc接口获取Tiling函数指针。
-   执行Tiling函数，验证其正确性。
3.  编译测试代码。
-   ${INSTALL_DIR}请替换为CANN软件安装后文件存储路径。以root用户安装为例，安装后文件默认存储路径为：/usr/local/Ascend/cann。
-   开发者根据需要链接依赖的动态库，必需链接的动态库有：
-   libtiling_api.so：Tiling功能相关的动态库，包含ContextBuilder类、OpTilingRegistry类等。
-   libc_sec.so：安全函数库，libtiling_api.so依赖该库。
-   libgraph_base.so：基础数据结构与接口库，libtiling_api.so依赖该库。
-   libregister.so：业务函数注册相关库（例如Tiling函数注册，算子原型注册等）。
-   libunified_dlog.so：log库，libtiling_api.so依赖该库。
-   libplatform.so：平台信息库，libtiling_api.so依赖该库；Tiling函数中使用硬件平台信息时，需要依赖该库。
4.  执行可执行文件。

<!-- cannbot:related:start -->
## 相关

- [BuildTilingContext](../../../../apis/utils_api/tiling_tuning/context_builder/build_tiling_context.md)（`explains`）：BuildTilingContext 与《TilingDebug》的实质衔接是：BuildTilingContext 由 ContextBuilder 的算子名、属性、输入输出和平台信息构造 KernelRunContextHolder；调测页说明如何执行与检查生成的 tiling context。
- [CompileInfo](../../../../apis/utils_api/tiling_tuning/context_builder/compile_info.md)（`explains`）：CompileInfo 与《TilingDebug》的实质衔接是：CompileInfo 只能在 BuildTilingContext 链中注入；ContextBuilder、Outputs 回退、TilingDebug 及两张空 CompileInfo 故障直接验证上下文排序约束。
- [ContextBuilder](../../../../apis/utils_api/tiling_tuning/context_builder/context_builder.md)（`explains`）：TilingDebug 需在调用函数前构造输入输出描述、属性、平台和 tiling/workspace 容器；ContextBuilder 汇总这些上下文入口。
- [GetTilingFunc](../../../../apis/utils_api/tiling_tuning/op_tiling_registry/get_tiling_func.md)（`explains`）：焦点处理OpTilingRegistry 加载动态库并取得 TilingFunc 的调测流程；TilingDebug正文界定“通过OpTilingRegistry加载编译后的Tiling动态库，使用ContextBuilder构建TilingContext并获取Tiling函数指针进行单独调测”。候选承担 Registry 加载、对象构造、opName 设置、ContextBuilder 与 GetTilingFunc 调测，runbook复现函数依赖错误。
- [LoadTilingLibrary](../../../../apis/utils_api/tiling_tuning/op_tiling_registry/load_tiling_library.md)（`explains`）：TilingDebug 首先加载算子包的 liboptiling.so 或自定义算子动态库；LoadTilingLibrary 给出路径和成功/失败判据。
- [OpTilingRegistry](../../../../apis/utils_api/tiling_tuning/op_tiling_registry/op_tiling_registry.md)（`explains`）：焦点处理OpTilingRegistry 的加载、取函数与 Tiling 调测入口；TilingDebug正文说明“通过OpTilingRegistry加载编译后的Tiling动态库，使用ContextBuilder构建TilingContext并获取Tiling函数指针进行单独调测”。候选把 Registry 类落到可执行的动态库加载、ContextBuilder 构造与 GetTilingFunc 调测流程。
- [PlatformInfo](../../../../apis/utils_api/tiling_tuning/context_builder/platform_info.md)（`explains`）：《PlatformInfo》说明将指向fe::PlatFormInfos的指针传入TilingContext。；《TilingDebug》说明通过OpTilingRegistry加载编译后的Tiling动态库，使用ContextBuilder构建TilingContext并获取Tiling函数指针进行单独调测。。二者在PlatformInfo向ContextBuilder注入fe::PlatFormInfos且只允许BuildTilingContext路径；AddPlatformInfo与Tiling调测流程给出构造和消费闭环上存在可执行的直接衔接。
- [TilingData](../../../../apis/utils_api/tiling_tuning/context_builder/tiling_data.md)（`explains`）：“TilingData”处理传入指向TilingData的void\ 指针；“TilingDebug”明确通过OpTilingRegistry加载编译后的Tiling动态库，使用ContextBuilder构建TilingContext并获取Tiling函数指针进行单独调测。。实质衔接：ContextBuilder::TilingData 只有在 BuildTilingContext 前提下有效，其他 Context 应改用 Outputs；TilingDebug 展示该上下文构造流程。
- [Utils API简介](../../../../apis/utils_api/tiling_tuning/op_tiling_registry/intro.md)（`explains`）：TilingDebug 指南说明如何把 OpTilingRegistry 用于离线调测并检查输出 tiling 数据。
- [如何使用workspace](how_to_use_workspace.md)（`related`）：workspace 大小/偏移通常由 tiling 下发，可用 tiling debug 核对。
- [调用算子时出现无法打开config.ini的报错](../faq/config_ini_open_error.md)（`related`）：调用算子时出现无法打开config.ini的报错 与《TilingDebug》的实质衔接是：config.ini 打开失败要沿文件名、权限、架构配置和构建/调试工具链排查；所保留卡均提供具体检查或恢复动作。
- [NPU域上板调试（功能调试）](../../debug_and_tuning/functional_debug/npu_board_debug.md)（`same_topic`）：《NPU域上板调试（功能调试）》处理“NPU域上板调试手段主要包含上板数据打印、msSanitizer内存异常检测和msDebug单步调试等功能，数据打印包括printf、DumpTensor两种方式，其中，DumpTensor是SIMD编程独有功能，用于打印指定Tensor的数据。”。《TilingDebug》提供“通过OpTilingRegistry加载编译后的Tiling动态库，使用ContextBuilder构建TilingContext并获取Tiling函数指针进行单独调测。”，其具体合同或探针直接接入NPU 上板打印、异常定位、Tiling 调试、精度对比和离线解析流程。
<!-- cannbot:related:end -->
