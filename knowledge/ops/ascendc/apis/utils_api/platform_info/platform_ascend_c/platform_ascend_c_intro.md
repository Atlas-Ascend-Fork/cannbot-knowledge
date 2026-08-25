---
type: API
title: PlatformAscendC简介
description: 在实现Host侧的Tiling函数时，可能需要获取一些硬件平台的信息，来支撑Tiling的计算，比如获取硬件平台的核数等信息。PlatformAscendC类提供获取这些平台信息的功能。
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/platform_info/PlatformAscendC/PlatformAscendC_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# PlatformAscendC简介

在实现Host侧的Tiling函数时，可能需要获取一些硬件平台的信息，来支撑Tiling的计算，比如获取硬件平台的核数等信息。PlatformAscendC类提供获取这些平台信息的功能。

<!-- cannbot:related:start -->
## 相关

- [ASCEND350 非 SocVersion 枚举成员致编译失败](../../../../runbooks/compilation/ascend350_socversion.md)（`exemplifies`）：《PlatformAscendC简介》的任务是“在实现Host侧的Tiling函数时，可能需要获取一些硬件平台的信息，来支撑Tiling的计算，比如获取硬件平台的核数等信息。PlatformAscendC类提供获取这些平台信息的功能。”。《ASCEND350 非 SocVersion 枚举成员致编译失败》具体提供“把 build.sh 的 SOC 别名 ascend350 当 C++ 枚举名 platform_ascendc::SocVersion::ASCEND350 写进 tiling 代码会编译报错；该枚举只有 ASCEND950，build.sh 中 ascend350 与 ascend950 同映射 arch 3510 但 C++ 侧无 ASCEND350 成员。判别=grep platform_ascendc.h 的 SocVersion 枚举确认合法成员名，build.sh SOC 别名不能直接当 C++ 枚举名用。”，它直接用于PlatformAscendC 的获取入口、兼容性和链接/SoC 枚举故障。
- [直调共享库加载未定义平台符号—补齐CANN链接依赖](../../../../runbooks/compilation/platform_manager_shared_library_link_dependencies.md)（`exemplifies`）：《PlatformAscendC简介》的任务是“在实现Host侧的Tiling函数时，可能需要获取一些硬件平台的信息，来支撑Tiling的计算，比如获取硬件平台的核数等信息。PlatformAscendC类提供获取这些平台信息的功能。”。《直调共享库加载未定义平台符号—补齐CANN链接依赖》具体提供“Ascend C 直调共享库可链接却在加载时缺 PlatformAscendCManager 符号；为目标补齐 CANN 平台运行依赖集与库目录。”，它直接用于PlatformAscendC 的获取入口、兼容性和链接/SoC 枚举故障。
- [Ascend C API兼容性策略](../../../../guides/cross_gen_migration_guide/ascend_c_api_compatibility.md)（`explains`）：《PlatformAscendC简介》的任务是“在实现Host侧的Tiling函数时，可能需要获取一些硬件平台的信息，来支撑Tiling的计算，比如获取硬件平台的核数等信息。PlatformAscendC类提供获取这些平台信息的功能。”。《Ascend C API兼容性策略》具体提供“本兼容性说明仅适用于Ascend C算子开发的兼容性迁移指导。总体兼容性策略见表1，兼容性范围不包含编译器BuiltIn API、Ascend C内部实现接口等。文档中涉及的兼容性分为两类：一是功能兼容，包括数据类型兼容、接口原型兼容和常量兼容；二是性能兼容，指对于同等数据量，新架构上执行API耗时不高于旧架构。”，它直接用于PlatformAscendC 的获取入口、兼容性和链接/SoC 枚举故障。
- [AddPlatformInfo](../../tiling_tuning/context_builder/add_platform_info.md)（`related`）：AddPlatformInfo 与《PlatformAscendC简介》的实质衔接是：AddPlatformInfo 把 PlatformInfo 注入 ContextBuilder，随后 BuildTiling/KernelRunContext 消费；PlatformAscendC/Manager 是平台能力信息的来源。
- [GetCoreMemSize](get_core_mem_size.md)（`related`）：GetCoreMemSize 与《PlatformAscendC简介》的实质衔接是：GetCoreMemSize 为 host tiling 提供各层容量；ReserveLocalMemory 会改变可用 UB，Matmul 空间查询与 UB 预算故障直接消费该值。
- [PlatformAscendCManager](../platform_ascend_c_manager.md)（`related`）：《PlatformAscendC简介》的任务是“在实现Host侧的Tiling函数时，可能需要获取一些硬件平台的信息，来支撑Tiling的计算，比如获取硬件平台的核数等信息。PlatformAscendC类提供获取这些平台信息的功能。”。《PlatformAscendCManager》具体提供“Kernel直调场景下获取硬件平台信息的单例管理类，通过GetInstance获取PlatformAscendC指针以访问核数等平台信息。”，它直接用于PlatformAscendC 的获取入口、兼容性和链接/SoC 枚举故障。
- [PlatformAscendC](platform_ascend_c.md)（`same_topic`）：《PlatformAscendC简介》明确“在实现Host侧的Tiling函数时，可能需要获取一些硬件平台的信息，来支撑Tiling的计算，比如获取硬件平台的核数等信息。PlatformAscendC类提供获取这些平台信息的功能。”；它与《PlatformAscendC》的“PlatformAscendC平台信息查询接口索引。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
