---
type: API
title: AscCopyL12Bt
description: L1到Bt Buffer数据搬运接口集合，包含不同架构版本。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_l12bt/asc_copy_l12bt.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscCopyL12Bt

L1到Bt Buffer数据搬运接口集合，包含不同架构版本。

将数据从L1 Buffer搬运到BiasTable Buffer中，BiasTable Buffer用于存放矩阵计算中的Bias。

本接口组包含 asc_copy_l12bt_arch_2201, asc_copy_l12bt_arch_3510。

约束：各存储单元的空间大小和对齐要求请参考存储单元说明。；操作数地址重叠约束请参考通用地址重叠约束。；当采用前n个数据搬运接口时，搬运数据大小要求32字节对齐。

支持的硬件型号：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [AscCopyL12Fb](../asc_copy_l12fb/asc_copy_l12fb.md)（`same_topic`）：AscCopyL12Bt 与《AscCopyL12Fb》的衔接是：AscCopyL12Bt 与架构变体及反向表搬运共同定义 L1 与 BiasTable 间的数据布局；BiasTable 指南解释目的表格式和对齐要求。
- [L1与BiasTable Buffer数据搬运](../../../basic_api/data_move_guide/l1_bias_table_data_move.md)（`same_topic`）：《L1与BiasTable Buffer数据搬运》说明DataCopy能够实现L1 Buffer至BiasTable Buffer的连续数据搬运，数据搬运时格式和内容保持不变。；《AscCopyL12Bt》说明L1到Bt Buffer数据搬运接口集合，包含不同架构版本。。二者在L1到BiasTable的连续搬运由C++/Tensor/C三层等价接口实现，并受Bias类型和数据通路约束上存在可执行的直接衔接。
- [asc_copy_l12bt](asc_copy_l12bt_arch_2201.md)（`same_topic`）：AscCopyL12Bt 与《asc_copy_l12bt》的衔接是：AscCopyL12Bt 与架构变体及反向表搬运共同定义 L1 与 BiasTable 间的数据布局；BiasTable 指南解释目的表格式和对齐要求。
- [asc_copy_l12bt](asc_copy_l12bt_arch_3510.md)（`same_topic`）：AscCopyL12Bt 与《asc_copy_l12bt》的衔接是：AscCopyL12Bt 与架构变体及反向表搬运共同定义 L1 与 BiasTable 间的数据布局；BiasTable 指南解释目的表格式和对齐要求。
<!-- cannbot:related:end -->
