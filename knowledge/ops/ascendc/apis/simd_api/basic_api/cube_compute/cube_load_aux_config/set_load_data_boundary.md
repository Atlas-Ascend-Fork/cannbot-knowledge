---
type: API
title: SetLoadDataBoundary
description: 设置LoadData（卷积数据搬运）接口所需的L1 Buffer（A1/B1）边界值，源操作数地址超出边界时从起始地址开始读取。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_load_aux_config/SetLoadDataBoundary.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# SetLoadDataBoundary

设置 LoadData（卷积数据搬运）接口的 L1 Buffer（A1/B1）边界值。源操作数在 L1 Buffer 上的地址超出边界时，从起始地址开始读取（环绕）。头文件 `basic_api/kernel_operator_mm_intf.h`。

参数：boundaryValue 为边界值。LoadData v1 指令单位 32B，v2 指令单位 1B。boundaryValue=0 表示无边界，可使用整个 L1 Buffer。配合 LoadData 使用时最小值 1024，设置 1~1023 为未定义行为。LoadData 的 L1 Buffer 初始地址须在边界内。

支持 a2/a3/Atlas 推理 AI Core，不支持 950/Atlas 200I/500 A2/Atlas 训练系列。

<!-- cannbot:related:start -->
## 相关

- [基础API迁移指导](../../../../../guides/cross_gen_migration_guide/3510_arch_migration/2201_to_3510_guide/basic_api_migration.md)（`explains`）：基础API迁移指导 与《SetLoadDataBoundary》的实质衔接是：基础 API 迁移与架构变化、兼容策略及编译/高阶迁移共同组成 2201 到 3510 的改造流程；所连具体卡验证被删除接口、硬件约束和替代调用。
- [LoadData](../cube_compute_load/load_data_3_d.md)（`related`）：《LoadData》的任务是“将NC1HWC0格式的Feature Map完成Image to Column展开后搬入L0A/L0B Buffer，也可用于2D格式数据搬运。”。《SetLoadDataBoundary》具体提供“设置LoadData（卷积数据搬运）接口所需的L1 Buffer（A1/B1）边界值，源操作数地址超出边界时从起始地址开始读取。”，它直接用于3D LoadData 的 Fmatrix、repeat、boundary、padding 与 L1/L0 地址合同。
- [LoadData](../cube_compute_load/load_data_gm_to_l1_2_dv2.md)（`related`）：《LoadData》处理“完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位从Global Memory搬运至L1 Buffer。”。《SetLoadDataBoundary》明确提供“设置LoadData（卷积数据搬运）接口所需的L1 Buffer（A1/B1）边界值，源操作数地址超出边界时从起始地址开始读取。”，其参数、调用或验证步骤直接接入GM 到 L1 二维 LoadData 的 Fmatrix、repeat、边界和地址合同。
- [SetLoadDataRepeat](set_load_data_repeat.md)（`related`）：《SetLoadDataRepeat》说明设置LoadData（卷积数据搬运）接口的repeat参数，通过一次调用完成多个迭代的数据搬运，支持配置迭代次数、步长、方向和K轴偏移。；《SetLoadDataBoundary》说明设置LoadData（卷积数据搬运）接口所需的L1 Buffer（A1/B1）边界值，源操作数地址超出边界时从起始地址开始读取。。二者在SetLoadDataRepeat配置的repeat、步长和方向直接控制后续LoadData搬入循环上存在可执行的直接衔接。
- [LoadImageToLocal](load_image_to_local.md)（`same_topic`）：LoadImageToLocal 与《SetLoadDataBoundary》的实质衔接是：LoadImageToLocal 的 AIPP 配置由边界填充、重复、尺寸和 fmatrix 参数共同决定，C/C++ 入口消费同一搬入契约。
- [SetFmatrix](set_fmatrix.md)（`same_topic`）：SetFmatrix 与《SetLoadDataBoundary》的实质衔接是：SetFmatrix 必须在卷积 LoadData 前声明 H/W/padding/fmatrixMode；BitMode、C API config 与 Cube 搬入材料描述同一配置在数据加载阶段的消费。
<!-- cannbot:related:end -->
