---
type: API
title: LoadTilingLibrary
description: 根据输入路径加载Tiling动态库，支持算子包编译或动态库编译方式获取的so文件，返回加载是否成功。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/OpTilingRegistry/LoadTilingLibrary.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# LoadTilingLibrary

## 功能说明
根据输入的路径，加载对应的Tiling动态库。开发者基于工程化算子开发开发方式完成算子实现后，可通过算子包编译或算子动态库编译获取对应的Tiling动态库文件。
-   算子包编译：Tiling实现对应的动态库为算子包部署目录下的liboptiling.so。具体路径可参考算子包部署。
-   动态库编译：Tiling实现集成在算子动态库libcust_opapi.so中。具体路径可参考算子动态库和静态库编译。
## 函数原型
## 参数说明
## 返回值说明
true：Tiling动态库加载成功；false：Tiling动态库加载失败。具体错误可参考Log信息。
关于日志配置和查看，请参考《环境变量参考》中日志相关环境变量。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [专用 kernel 路径输出不变时先核对共享库是否真的包含目标符号](../../../../runbooks/precision/specialized_npu_kernel_symbol_presence_probe.md)（`exemplifies`）：专用 kernel 路径输出不变时先核对共享库是否真的包含目标符号说明Host 源码已有专用 launch 分支但 targeted 输出仍保持输入值时，用 nm 同时核对共享库专用符号与通用实例，先判别目标 kernel 是否被产入二进制；对LoadTilingLibrary而言，LoadTilingLibrary 完成共享库装载后由 GetTilingFunc 取函数；链接缺符号和产物不含目标符号是两个可操作的验证分支。
- [直调共享库加载未定义平台符号—补齐CANN链接依赖](../../../../runbooks/compilation/platform_manager_shared_library_link_dependencies.md)（`exemplifies`）：直调共享库加载未定义平台符号—补齐CANN链接依赖说明Ascend C 直调共享库可链接却在加载时缺 PlatformAscendCManager 符号；为目标补齐 CANN 平台运行依赖集与库目录；对LoadTilingLibrary而言，LoadTilingLibrary 完成共享库装载后由 GetTilingFunc 取函数；链接缺符号和产物不含目标符号是两个可操作的验证分支。
- [TilingDebug](../../../../guides/programming_guide/appendix/common_operations/tiling_debug.md)（`explains`）：TilingDebug 首先加载算子包的 liboptiling.so 或自定义算子动态库；LoadTilingLibrary 给出路径和成功/失败判据。
- [构造和析构函数](constructor_and_destructor.md)（`related`）：构造和析构函数说明创建与释放OpTilingRegistry对象；对LoadTilingLibrary而言，LoadTilingLibrary 完成共享库装载后由 GetTilingFunc 取函数；链接缺符号和产物不含目标符号是两个可操作的验证分支。
- [GetTilingFunc](get_tiling_func.md)（`same_topic`）：焦点处理OpTilingRegistry 加载动态库并取得 TilingFunc 的调测流程；LoadTilingLibrary正文界定“根据输入路径加载Tiling动态库，支持算子包编译或动态库编译方式获取的so文件，返回加载是否成功”。候选承担 Registry 加载、对象构造、opName 设置、ContextBuilder 与 GetTilingFunc 调测，runbook复现函数依赖错误。
<!-- cannbot:related:end -->
