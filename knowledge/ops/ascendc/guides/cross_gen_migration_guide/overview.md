---
type: Guide
title: 跨代迁移指南概述
description: Ascend C的核心设计目标之一是实现跨代兼容。然而，每一代芯片在微架构上都存在独特的硬件特性，因此无法保证所有接口仅通过重编译就能达成完全的跨代兼容。基于这一前提，本手册旨在为Ascend
  C算子开发者提供系统化指导，帮助将算子Kernel代码从当前芯片平滑移植到目标代际芯片上运行，实现高效、可控的迁移。
tags: [task.lookup, topic.quality.compatibility.version_migration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/cross_gen_migration_guide/overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 概述

Ascend C的核心设计目标之一是实现跨代兼容。然而，每一代芯片在微架构上都存在独特的硬件特性，因此无法保证所有接口仅通过重编译就能达成完全的跨代兼容。基于这一前提，本手册旨在为Ascend C算子开发者提供系统化指导，帮助将算子Kernel代码从当前芯片平滑移植到目标代际芯片上运行，实现高效、可控的迁移。
如SIMD-BuiltIn关键字中所述，__NPU_ARCH__是Device侧AI Core代码中的一个预处理宏，用于标识AI处理器的架构版本。因此，后续章节将以__NPU_ARCH__为主线，重点介绍相邻代际芯片间的平滑迁移方法。
建议开发者采用以下实践：
- 使用兼容的API接口。
- 若涉及特定领域的扩展特性，应在Device侧通过 __NPU_ARCH__编译宏进行隔离，在Host侧通过SocVersion进行隔离。
- 使用>>直调或 Tiling模板编程。
> 💡 请参考昇腾到麒麟迁移指南，了解如何将昇腾平台上开发的算子迁移到麒麟平台。

<!-- cannbot:related:start -->
## 相关

- [基础API迁移指导](3510_arch_migration/2201_to_3510_guide/basic_api_migration.md)（`related`）：基础API迁移指导 与《跨代迁移指南概述》的实质衔接是：基础 API 迁移与架构变化、兼容策略及编译/高阶迁移共同组成 2201 到 3510 的改造流程；所连具体卡验证被删除接口、硬件约束和替代调用。
- [2201到3510架构变更](3510_arch_migration/2201_to_3510_arch_changes.md)（`same_topic`）：跨代迁移指南概述 与《2201到3510架构变更》的实质衔接是：迁移概述把兼容性判断、架构差异、基础/高阶 API 修改和算子编译迁移串成同一套 2201→3510 决策流程。
- [Ascend C API兼容性策略](ascend_c_api_compatibility.md)（`same_topic`）：跨代迁移指南概述 与《Ascend C API兼容性策略》的实质衔接是：迁移概述把兼容性判断、架构差异、基础/高阶 API 修改和算子编译迁移串成同一套 2201→3510 决策流程。
- [算子编译迁移指导](3510_arch_migration/2201_to_3510_guide/op_compilation_migration.md)（`same_topic`）：跨代迁移指南概述 与《算子编译迁移指导》的实质衔接是：迁移概述把兼容性判断、架构差异、基础/高阶 API 修改和算子编译迁移串成同一套 2201→3510 决策流程。
- [高阶API迁移指导](3510_arch_migration/2201_to_3510_guide/advanced_api_migration.md)（`same_topic`）：跨代迁移指南概述 与《高阶API迁移指导》的实质衔接是：迁移概述把兼容性判断、架构差异、基础/高阶 API 修改和算子编译迁移串成同一套 2201→3510 决策流程。
<!-- cannbot:related:end -->
