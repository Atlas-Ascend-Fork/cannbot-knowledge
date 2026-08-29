---
type: API
title: AscSetGm2l1Pad
description: 设置GM到L1非对齐搬运时数据块左右两侧需要填补的数据值。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_set_gm2l1_pad.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscSetGm2l1Pad

将数据从Global Memory (GM)非对齐搬运到L1 Buffer时，通过调用该接口设置连续搬运数据块左右两侧需要填补的数据值。

参数：pad_val(输入): 左右两侧需要填补的数据值。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscCopyGm2l1Align](asc_copy_gm2l1_align.md)（`same_topic`）：将数据从Global Memory (GM)非对齐搬运到L1 Buffer时，通过调用该接口设置连续搬运数据块左右两侧需要填补的数据值。需要与asc_set_gm2l1_loop_size、asc_set_gm2l1_loop1_stride、asc_set_gm2l1_loop2_stride和asc_set_gm2l1_pad配合使用。两端属于同一次 GM 到 L1 align 搬运调用合同：setter 先定义边界填充值，copy 接口再消费 pad 与 loop/stride 配置执行搬运。
<!-- cannbot:related:end -->
