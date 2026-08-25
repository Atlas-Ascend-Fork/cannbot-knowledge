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
