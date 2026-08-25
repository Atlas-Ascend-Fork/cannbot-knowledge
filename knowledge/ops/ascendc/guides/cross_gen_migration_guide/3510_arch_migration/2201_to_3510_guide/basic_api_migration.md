---
type: Guide
title: 基础API迁移指导
description: 本节针对NPU架构版本3510的芯片变更对基础API兼容性产生的影响进行说明，并提供基础API的兼容性适配方案。
tags: [task.lookup, topic.quality.compatibility.version_migration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/cross_gen_migration_guide/3510_arch_migration/2201_to_3510_guide/basic_api_migration.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 基础API迁移指导

本节针对NPU架构版本3510的芯片变更对基础API兼容性产生的影响进行说明，并提供基础API的兼容性适配方案。
## 矢量计算
-   3510架构默认不支持Subnormal功能。
说明：SubNormal浮点数指的是指数位全为0、尾数不为0的浮点数，用于表示比最小正常数更小的值，避免“下溢为0”。3510版本默认不支持Subnormal，Subnormal浮点数在计算中被视为0。
兼容方案：通过设置config模板参数来配置Subnormal计算模式。软件模拟对Subnormal数据的处理，通过精度扩展等处理方式来避免Subnormal浮点数下溢为0。
涉及Subnormal的API和config参数说明
可以参考以下代码片段：
## 数据搬运
-   DataCopy接口不支持L1 Buffer->GM通路。
说明：硬件删除L1 Buffer到GM的通路，无法将数据从L1 Buffer直接搬运到GM中。现有接口不支持L1 Buffer到GM的直接搬运。
兼容方案：对于纯Cube计算场景：在GM多分配一个单位矩阵，通过Mmad矩阵乘法计算输出到L0C Buffer，再从L0C Buffer通过Fixpipe搬运到GM。对于Vector和Cube计算融合场景，可以通过L1 Buffer搬运到UB，再搬运到GM。以下以纯Cube计算场景为例进行说明，介绍算子核心流程，具体可参考L1到GM搬运兼容性样例。
1.  将矩阵A从GM搬运到L1 Buffer。
2.  将矩阵B（矩阵B为单位矩阵）从GM搬运到L1 Buffer。
3.  将矩阵A从L1 Buffer搬运到L0A Buffer。
4.  将矩阵B从L1 Buffer搬运到L0B Buffer。
5.  进行Mmad矩阵计算，结果输出到L0C Buffer。
6.  通过FixPipe将矩阵C从L0C Buffer拷贝到GM。
-   不支持SetLoadDataBoundary接口。
说明：3510架构硬件删除了L1 Buffer的边界值设定相关寄存器，不再支持SetLoadDataBoundary接口。该接口用于设置LoadData（卷积数据搬运）时L1 Buffer的边界值。如果指令在处理源操作数时，源操作数在L1 Buffer上的地址超出设置的边界，则会从L1 Buffer的起始地址开始读取数据。设置为0表示无边界，可以使用整个L1 Buffer。
兼容方案：
-   NPU架构版本2201的接口参数boundaryValue设置为0时与3510架构版本等价。
-   如果需要在L1 Buffer上循环读取操作数，需要将对应的LoadData（卷积数据搬运）接口手动拆分成多条指令，手动绕回。具体代码可参考SetLoadDataBoundary兼容性样例。
如上图所示，以L1 Buffer到L0A Buffer的搬运为例。

<!-- cannbot:related:start -->
## 相关

- [AscCopyL12gm](../../../../apis/simd_api/c_api/cube_data_move/asc_copy_l12gm.md)（`explains`）：AscCopyL12gm 在 2201 上提供 L1→GM 直达搬运，而《基础API迁移指导》明确 3510 不再支持该路径并要求改为 L1→UB→GM；这是迁移该调用所必需的替代契约。
- [SetLoadDataBoundary](../../../../apis/simd_api/basic_api/cube_compute/cube_load_aux_config/set_load_data_boundary.md)（`explains`）：基础API迁移指导 与《SetLoadDataBoundary》的实质衔接是：基础 API 迁移与架构变化、兼容策略及编译/高阶迁移共同组成 2201 到 3510 的改造流程；所连具体卡验证被删除接口、硬件约束和替代调用。
- [2201到3510架构变更](../2201_to_3510_arch_changes.md)（`related`）：架构变更卡列出删除/新增数据通路、Regbase 和 Subnormal 差异；基础 API 迁移卡把这些变化落实为 DataCopy、LoadData、SetLoadDataBoundary 等替代方案。
- [Ascend C API兼容性策略](../../ascend_c_api_compatibility.md)（`related`）：兼容性总览先判定接口状态，基础 API 迁移页再给出具体 2201→3510 替换。
- [NPU架构版本2201](../../../programming_guide/advanced_programming/hardware_implementation/architecture_spec/npu_arch_2201.md)（`related`）：基础API迁移指导 与《NPU架构版本2201》的实质衔接是：基础 API 迁移与架构变化、兼容策略及编译/高阶迁移共同组成 2201 到 3510 的改造流程；所连具体卡验证被删除接口、硬件约束和替代调用。
- [NPU架构版本2201](../../../programming_guide/advanced_programming/hardware_implementation/hardware_constraints/npu_arch_2201.md)（`related`）：基础API迁移指导 与《NPU架构版本2201》的实质衔接是：基础 API 迁移与架构变化、兼容策略及编译/高阶迁移共同组成 2201 到 3510 的改造流程；所连具体卡验证被删除接口、硬件约束和替代调用。
- [dav-2201 Rsqrt 精度不足 — 改用 Sqrt 加标量倒数](../../../../runbooks/precision/rsqrt_fast_approximation_use_sqrt_reciprocal.md)（`related`）：基础API迁移指导 与《dav-2201 Rsqrt 精度不足 — 改用 Sqrt 加标量倒数》的实质衔接是：基础 API 迁移与架构变化、兼容策略及编译/高阶迁移共同组成 2201 到 3510 的改造流程；所连具体卡验证被删除接口、硬件约束和替代调用。
- [算子编译迁移指导](op_compilation_migration.md)（`related`）：基础API迁移指导 与《算子编译迁移指导》的实质衔接是：基础 API 迁移与架构变化、兼容策略及编译/高阶迁移共同组成 2201 到 3510 的改造流程；所连具体卡验证被删除接口、硬件约束和替代调用。
- [跨代迁移指南概述](../../overview.md)（`related`）：基础API迁移指导 与《跨代迁移指南概述》的实质衔接是：基础 API 迁移与架构变化、兼容策略及编译/高阶迁移共同组成 2201 到 3510 的改造流程；所连具体卡验证被删除接口、硬件约束和替代调用。
- [高阶API迁移指导](advanced_api_migration.md)（`related`）：高级 API 与基础 API 迁移分别处理封装层和底层签名；混合实现需同时执行两份检查。
<!-- cannbot:related:end -->
