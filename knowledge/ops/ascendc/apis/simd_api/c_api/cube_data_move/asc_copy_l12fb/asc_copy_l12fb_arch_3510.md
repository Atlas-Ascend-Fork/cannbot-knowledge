---
type: API
title: asc_copy_l12fb
description: 将数据从L1 Buffer搬运到Fixpipe Buffer中，Fixpipe Buffer用于存放量化参数。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_l12fb/asc_copy_l12fb_arch_3510.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# asc_copy_l12fb

将数据从L1 Buffer搬运到Fixpipe Buffer中，Fixpipe Buffer用于存放量化参数。

参数：dst(输出): 目的操作数起始地址。；src(输入): 源操作数起始地址。；size(输入): 搬运数据大小（字节）。；n_burst(输入): 待搬运的连续传输数据块个数。取值范围：[1, 4095]。；len_burst(输入): 待搬运的每个连续传输数据块的长度，单位为64B。取值范围：[1, 65535]。；src_gap_size(输入): 源操作数相邻连续数据块的间隔（前面一个数据块的尾与后面一个数据块的头的间隔）。 单位为DataBlock（32字节）。；dst_gap_size(输入): 目的操作数相邻连续数据块的间隔（前面一个数据块的尾与后面一个数据块的头的间隔）。 单位为64B。

约束：- 各存储单元的空间大小和对齐要求
- 操作数地址重叠约束

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [asc_copy_l12bt](../asc_copy_l12bt/asc_copy_l12bt_arch_3510.md)（`related`）：L12BT 和 L12FB 的源同为 L1，但目标辅助 buffer 不同，决定后续 cube 单元消费路径。
- [AscCopyL12Fb](asc_copy_l12fb.md)（`same_topic`）：AscCopyL12Fb 与《asc_copy_l12fb》的实质衔接是：两张架构实现卡是 AscCopyL12Fb 集合实际可调用的入口，分别给出 2201/3510 的参数和对齐契约。
- [asc_copy_l12fb](asc_copy_l12fb_arch_2201.md)（`same_topic`）：两卡是同一 L1→Fixpipe Buffer 量化参数搬运接口的 2201/3510 版本；3510 将 len_burst/dst_gap 改为 64B 口径，必须在迁移时对照。
<!-- cannbot:related:end -->
