---
type: Guide
title: 2201到3510架构变更
description: NPU架构版本3510的架构图如图1所示，总体来看，3510架构新增了以下特性：
tags: [task.lookup, topic.quality.compatibility.version_migration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/cross_gen_migration_guide/3510_arch_migration/2201_to_3510_arch_changes.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---
# 2201到3510架构变更

NPU架构版本3510的架构图如图1所示，总体来看，3510架构新增了以下特性：
-   新增多条数据通路。
-   AI Core核数增加。
-   UB容量提升。
-   新增SSBuffer核内存储单元，支持AIC核和AIV核通过Scalar访问。
-   SIMD编程基础上，支持SIMT编程、SIMD与SIMT混合编程。
-   AIV核采用Regbase架构，与NPU架构版本2201的Membase架构相比，可以直接对芯片的Vector寄存器Register进行操作，实现更大的灵活性和更好的性能。
具体来说，3510架构的主要变更如下各表所示。除此之外，3510架构还扩展了支持的数据类型，具体可参考数据类型介绍。
- 搬运单元
搬运单元变更
3510变更：产生的影响：影响的API接口
删除L1 Buffer到GM的数据通路。：现有接口不支持从L1 Buffer直接搬运数据到GM。开发者需要在L1 Buffer分配一块空间存放单位矩阵，利用MMAD矩阵乘法计算输出到L0C Buffer，从L0C Buffer通过Fixpipe（L0C到GM数据搬运）将数据搬运到GM。：DataCopy/DumpTensor
删除GM到L0A Buffer、L0B Buffer的数据通路。：原GM到L0A Buffer和L0B Buffer的数据搬运需要拆分为两步，即从GM到L1 Buffer的数据搬运和从L1 Buffer到L0A Buffer、L0B Buffer的数据搬运。：LoadData
新增UB到L1 Buffer的数据通路。：支持将数据直接从UB搬运到L1 Buffer，而无需先从UB搬运到GM，再从GM搬运到L1 Buffer，使用方式具体可参考DataCopy（UBToL1连续数据搬运）。：DataCopy
新增ND-DMA指令。：扩展DataCopy数据搬运接口的能力，相比基础数据搬运接口，可更加自由地配置搬入数据的维度信息及Stride，使用方式具体可参考DataCopy（GMToUB多维数据搬运NDDMA）。：DataCopy
新增L0C Buffer到UB的单向数据通路。：支持将数据直接从L0C Buffer搬运到UB，而无需先从L0C Buffer搬运到GM，再从GM搬运到UB，使用方式具体可参考Fixpipe（L0C到GM数据搬运）。：Fixpipe
扩展LoadData搬运指令。：新增支持MicroScaling（MX）场景的数据搬运，使用方式具体可参考LoadData。：LoadData
新增DN分型、L1Buffer->L0A Buffer不再支持transpose。：使用新特性具体可参考LoadDataWithTranspose。：LoadDataWithTranspose
Fixpipe新增NZ2DN随路转换（实现NZ到DN数据格式的随路变换）。

<!-- cannbot:related:start -->
## 相关

- [高阶API迁移指导](2201_to_3510_guide/advanced_api_migration.md)（`related`）：焦点卡写明“AIV核采用Regbase架构，与NPU架构版本2201的Membase架构相比”，候选卡写明“当前3510架构不支持卷积计算类高阶API”。架构卡解释底层代际差异，迁移卡给出高阶 API 兼容例外，把架构变化落实到接口检查。
<!-- cannbot:related:end -->
