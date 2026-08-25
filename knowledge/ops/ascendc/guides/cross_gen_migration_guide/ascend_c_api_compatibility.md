---
type: Guide
title: Ascend C API兼容性策略
description: 本兼容性说明仅适用于Ascend C算子开发的兼容性迁移指导。总体兼容性策略见表1，兼容性范围不包含编译器BuiltIn API、Ascend
  C内部实现接口等。文档中涉及的兼容性分为两类：一是功能兼容，包括数据类型兼容、接口原型兼容和常量兼容；二是性能兼容，指对于同等数据量，新架构上执行API耗时不高于旧架构。
tags: [task.lookup, topic.quality.compatibility.version_migration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/cross_gen_migration_guide/ascend_c_api_compatibility.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# Ascend C API兼容性策略

本兼容性说明仅适用于Ascend C算子开发的兼容性迁移指导。总体兼容性策略见[表1](#table18109729593)，兼容性范围不包含编译器BuiltIn API、Ascend C内部实现接口等。文档中涉及的兼容性分为两类：一是功能兼容，包括数据类型兼容、接口原型兼容和常量兼容；二是性能兼容，指对于同等数据量，新架构上执行API耗时不高于旧架构。

若开发者希望在NPU架构版本3510下运行原本在NPU架构版本2201上开发的Ascend C程序，需在3510架构上重新编译并运行，并可能需要根据迁移指导进行代码调整。

**图1**  Ascend C API层次结构

**表1**  Ascend C API兼容策略

<table><thead align="left"><tr id="row810952912919"><th class="cellrowborder" valign="top" width="18.01%" id="mcps1.2.3.1.1"><p id="p141091429991">API层级</p>
</th>
<th class="cellrowborder" valign="top" width="81.99%" id="mcps1.2.3.1.2"><p id="p0109162915915">兼容策略</p>
</th>
</tr>
</thead>
<tbody><tr id="row171096295916"><td class="cellrowborder" valign="top" width="18.01%" headers="mcps1.2.3.1.1 "><p id="p101091029492">高阶API</p>
</td>
<td class="cellrowborder" valign="top" width="81.99%" headers="mcps1.2.3.1.2 "><p id="p16109829497">高阶API在同领域内可保证兼容，特定领域扩展特性不保证兼容。</p>
</td>
</tr>
<tr id="row1110915291898"><td class="cellrowborder" valign="top" width="18.01%" headers="mcps1.2.3.1.1 "><p id="p31097291995">基础API</p>
</td>
<td class="cellrowborder" valign="top" width="81.99%" headers="mcps1.2.3.1.2 "><p id="p31097296914">基础API分为可兼容的基础API和ISASI基础API；兼容的API在所有架构上均能兼容；ISASI API为体系架构相关的API，不保证跨架构版本的兼容性，例如CUBE侧的计算接口LoadData、Mmad等。

<!-- cannbot:related:start -->
## 相关

- [PlatformAscendC简介](../../apis/utils_api/platform_info/platform_ascend_c/platform_ascend_c_intro.md)（`explains`）：《PlatformAscendC简介》的任务是“在实现Host侧的Tiling函数时，可能需要获取一些硬件平台的信息，来支撑Tiling的计算，比如获取硬件平台的核数等信息。PlatformAscendC类提供获取这些平台信息的功能。”。《Ascend C API兼容性策略》具体提供“本兼容性说明仅适用于Ascend C算子开发的兼容性迁移指导。总体兼容性策略见表1，兼容性范围不包含编译器BuiltIn API、Ascend C内部实现接口等。文档中涉及的兼容性分为两类：一是功能兼容，包括数据类型兼容、接口原型兼容和常量兼容；二是性能兼容，指对于同等数据量，新架构上执行API耗时不高于旧架构。”，它直接用于PlatformAscendC 的获取入口、兼容性和链接/SoC 枚举故障。
- [2201到3510架构变更](3510_arch_migration/2201_to_3510_arch_changes.md)（`related`）：架构变化解释兼容表中接口变化/不支持的硬件原因。
- [Ascend C多层级编程接口选择参考](../asc_how_to_choose_api.md)（`related`）：Ascend C多层级编程接口选择参考 与《Ascend C API兼容性策略》的实质衔接是：概述/快速开始解释学习入口，TPipe/TQue 原理与范式对应 choice guide 的易编程层，兼容性策略说明跨代选择接口层时的稳定性成本。
- [基础API迁移指导](3510_arch_migration/2201_to_3510_guide/basic_api_migration.md)（`related`）：兼容性总览先判定接口状态，基础 API 迁移页再给出具体 2201→3510 替换。
- [算子编译迁移指导](3510_arch_migration/2201_to_3510_guide/op_compilation_migration.md)（`related`）：接口兼容后仍需迁移编译配置和产物注册，构成工程下游步骤。
- [高阶API迁移指导](3510_arch_migration/2201_to_3510_guide/advanced_api_migration.md)（`related`）：高阶 API 有独立临时空间、tiling 和签名变化，不能仅依赖基础 API 兼容结论。
- [NPU架构版本2201](../programming_guide/advanced_programming/hardware_implementation/architecture_spec/npu_arch_2201.md)（`same_topic`）：Ascend C API兼容性策略说明本兼容性说明仅适用于Ascend C算子开发的兼容性迁移指导。总体兼容性策略见表1，兼容性范围不包含编译器BuiltIn API、Ascend C内部实现接口等。文档中涉及的兼容性分为两类：一是功能兼容，包括数据类型兼容、接口原型兼容和常量兼容；二是性能兼容，指对于同等数据量，新架构上执行API耗时不高于旧架构。
- [跨代迁移指南概述](overview.md)（`same_topic`）：跨代迁移指南概述 与《Ascend C API兼容性策略》的实质衔接是：迁移概述把兼容性判断、架构差异、基础/高阶 API 修改和算子编译迁移串成同一套 2201→3510 决策流程。
<!-- cannbot:related:end -->
