---
type: API
title: asc_copy_gm2l1
description: 将矩阵数据从Global Memory搬运到L1 Buffer中，支持以下两种搬运模式： - 填充模式：搬运过程中可以对数据进行填充或移除填充值。
  - 2D搬运模式：支持2D矩阵数据搬运，支持压缩能力。（NPU_ARCH 220x版本不支持.）
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_gm2l1/asc_copy_gm2l1_arch_3510.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# asc_copy_gm2l1

将矩阵数据从Global Memory搬运到L1 Buffer中，支持以下两种搬运模式
- 填充模式：搬运过程中可以对数据进行填充或移除填充值。
- 2D搬运模式：支持2D矩阵数据搬运，支持压缩能力。（NPU_ARCH 220x版本不支持.）

参数：dst(输出): 目的操作数（矢量）的起始地址。；src(输入): 源操作数（矢量）的起始地址。；n_burst(输入): 待搬运的连续传输数据块个数。；len_burst(输入): 待搬运的每个连续传输数据块的长度，单位为32个字节。；pad_func_mode(输入): 一个4Bit的值，用于指示通道上的padding功能，他会在32个字节的数据中填充数据；或从每个32个字节的读取数据中移除padding值。 • 0：不做padding。 • 1：每有1个字节的数据，插入31个padding值。 • 2：每有2个字节的数据，插入15个padding值。 • 3：每有4个字节的数据，插入14个padding值。 • 4：每有8个字节的数据，插入12个padding值。 • 5：每有16个字节的数据，插入8个padding值。 • 6：每有32个字节的数据，移除28个最高有效位数据，只保留4个最低有效位元素。 • 7：每有32个字节的数据，移除24个最高有效位数据，只保留8个最低有效位元素。 • 8：每有32个字节的数据，移除16个最高有效位数据，只保留16个最低有效位元素。；src_stride(输入): 输入数据中两个相邻连续数据块之间的距离。；dst_stride(输入): 输出数据中两个相邻连续数据块之间的距离。；dst(输出): 目的操作数（矢量）的起始地址。

约束：各存储单元的空间大小和对齐要求

### 填充模式约束

- 对于插入padding值的场景
    - len_burst的单位为32个字节的指的是写入L1 Buffer的实际数据数，它必须设置为1，此时一次仅从GM里读取1/2/4/8/16个字节的数据。
    - 每一次burst都是从GM中连续读取，因此不需要设置src_stride。
    - dst_stride以32个字节为单位。
- 对于移除padding值的场景
    - 源操作数中一次burst操作的数据为len_burst * 32个字节，目的操作数中一次burst的实际数据为len_burst * 4/8/16个字节。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscCopyGm2l1Align](../asc_copy_gm2l1_align.md)（`same_topic`）：将矩阵数据从Global Memory搬运到L1 Buffer中，支持以下两种搬运模式；对矩阵数据进行实时padding，完成padding后将数据从Global Memory搬运到L1 Buffer。需要与asc_set_gm2l1_loop_size、asc_set_gm2l1_loop1_stride、asc_set_gm2l1_loop2_stride和asc_set_gm2l1_pad配合使用。。两接口共享 GM 到 L1 的矩阵搬运对象，Align 变体把基础接口的 padding 能力具体化为实时 padding 并增加配套配置调用。
<!-- cannbot:related:end -->
