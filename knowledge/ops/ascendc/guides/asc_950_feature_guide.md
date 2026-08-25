---
type: Guide
title: Ascend 950PR/Ascend 950DT新增特性导航
description: 本文档索引Ascend 950PR/Ascend 950DT（NPU架构版本3510）相比上一代（2201）新增的硬件特性，以及每个特性对应的编程模型、API接口和算子实践资料链接。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/asc_950_feature_guide.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Ascend 950PR/Ascend 950DT新增特性导航

本文档索引 Ascend 950PR/Ascend 950DT（NPU 架构版本 3510）相比上一代（2201）新增的硬件特性，以及每个特性对应的编程模型、API 接口和算子实践资料链接。
新增特性包括 RegBase 架构（Vector 计算从 MemBase 切换到 RegBase）、SIMT 编程模型（线程级并行）、SIMD 与 SIMT 混合编程、HiF8 数据类型、UB 到 L1 Buffer 通路、L0C 到 UB 通路、ND-DMA 搬运指令、SSBuffer 核间存储、Mutex 同步、CrossCore 核间同步、MX 数据类型、Fixpipe 增强、UB bank 结构变化等。
适用于 __NPU_ARCH__ 为 3510 的芯片，架构变更详情参考 2201 到 3510 架构变更文档。

<!-- cannbot:related:start -->
## 相关

- [关键特性说明](../apis/simd_api/basic_api/reg_vector_compute/key_features/key_features.md)（`explains`）：RegBase 关键特性页说明 3510 上寄存器编程能力，是 Ascend950 特性指南中的具体编程模型落点。
- [Ascend arch 变体查证链路 SoC→ini→NpuArch→dispa](../runbooks/compilation/arch_variant_lookup_chain_soc_ini_npuarch_dispatcher.md)（`related`）：该指南从 SoC 配置追到 __NPU_ARCH__ 分支，能验证特性指南中 3510 能力实际命中的头文件实现。
- [Ascend950 向量管 FTZ 刷新次正规 exp 为零](../runbooks/precision/ascend950_ftz_exp.md)（`related`）：该卡实测 3510 Exp 的次正规数 FTZ 行为，为特性指南之外的数值边界提供验证实例。
- [AscendC:: 前缀致全局符号编译失败](../runbooks/compilation/ascendc.md)（`related`）：该构建卡给出 Ascend950 编译链与架构宏的实际约束，可把特性指南落实到工程配置。
<!-- cannbot:related:end -->
