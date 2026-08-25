---
type: API
title: asc_copy_l12bt
description: 将数据从L1 Buffer搬运到BiasTable Buffer中，BiasTable Buffer用于存放矩阵计算中的Bias。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_l12bt/asc_copy_l12bt_arch_2201.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---
# asc_copy_l12bt

将数据从L1 Buffer搬运到BiasTable Buffer中，BiasTable Buffer用于存放矩阵计算中的Bias。

参数：dst(输出): 目的操作数起始地址。；src(输入): 源操作数起始地址。；size(输入): 搬运数据大小（字节）。；conv_control(输入): 是否开启随路转化。；n_burst(输入): 待搬运的连续传输数据块个数。取值范围：[1, 4095]。；len_burst(输入): 待搬运的每个连续传输数据块的长度，单位为DataBlock（32字节）。取值范围：[1, 65535]。；source_gap(输入): 源操作数相邻连续数据块的间隔（前面一个数据块的尾与后面一个数据块的头的间隔）。 单位为DataBlock（32字节）。；dst_gap(输入): 目的操作数相邻连续数据块的间隔（前面一个数据块的尾与后面一个数据块的头的间隔）。 单位为DataBlock（32字节）。

约束：- 各存储单元的空间大小和对齐要求
- 操作数地址重叠约束
- 当采用前n个数据搬运接口时，搬运数据大小要求32字节对齐。

仅 Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [AscCopyL12Bt](asc_copy_l12bt.md)（`same_topic`）：AscCopyL12Bt 与《asc_copy_l12bt》的衔接是：AscCopyL12Bt 与架构变体及反向表搬运共同定义 L1 与 BiasTable 间的数据布局；BiasTable 指南解释目的表格式和对齐要求。
- [L1与BiasTable Buffer数据搬运](../../../basic_api/data_move_guide/l1_bias_table_data_move.md)（`same_topic`）：《L1与BiasTable Buffer数据搬运》说明DataCopy能够实现L1 Buffer至BiasTable Buffer的连续数据搬运，数据搬运时格式和内容保持不变。；《asc_copy_l12bt》说明将数据从L1 Buffer搬运到BiasTable Buffer中，BiasTable Buffer用于存放矩阵计算中的Bias。。二者在L1到BiasTable的连续搬运由C++/Tensor/C三层等价接口实现，并受Bias类型和数据通路约束上存在可执行的直接衔接。
- [asc_copy_l12bt](asc_copy_l12bt_arch_3510.md)（`same_topic`）：两卡是同一 asc_copy_l12bt 的 2201 与 3510 契约，均把 L1 Bias 搬到 BiasTable，并共享 burst、gap 和 32B 对齐语义。
<!-- cannbot:related:end -->
