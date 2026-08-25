---
type: API
title: AscCopyGm2l1Align
description: 对矩阵数据进行实时padding后从GM搬运到L1 Buffer，需配合asc_set_gm2l1系列接口使用。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_gm2l1_align.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscCopyGm2l1Align

对矩阵数据进行实时padding，完成padding后将数据从Global Memory搬运到L1 Buffer。需要与asc_set_gm2l1_loop_size、asc_set_gm2l1_loop1_stride、asc_set_gm2l1_loop2_stride和asc_set_gm2l1_pad配合使用。

参数：dst(输出): 目的操作数（矢量）的起始地址。；src(输入): 源操作数（矢量）的起始地址。；n_burst(输入): 待搬运的连续传输数据块个数。；len_burst(输入): 待搬运的每个连续传输数据块的长度，单位为字节。；left_padding_count(输入): 数据左侧的padding元素数。对位宽为8的数据类型，该参数的最大值为32，对位宽为16的数据类型，该参数的最大值为16，对位宽为32的数据类型，该参数的最大值为8。；right_padding_count(输入): 数据右侧的padding元素数。对位宽为8的数据类型，该参数的最大值为32，对位宽为16的数据类型，该参数的最大值为16，对位宽为32的数据类型，该参数的最大值为8。；data_select_bit(输入): padding数据选择位，当前只支持设置为false，将padding值设置为数据块的第一个元素。

约束：- 各存储单元的空间大小和对齐要求
- 目的操作数不得存在地址重叠。对于存在地址重叠的操作，硬件将不返回任何警告或错误，也无法保证地址重叠数据的正确性。

仅 Ascend 950PR/Ascend 950DT 支持。
