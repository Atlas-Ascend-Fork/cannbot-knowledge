---
type: API
title: AscLoadImageToCbuf
description: 将图像数据从Global Memory搬运到L1 Buffer。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_load_image_to_cbuf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---
# AscLoadImageToCbuf

将图像数据从Global Memory搬运到L1 Buffer。

参数：dst(输出): 目的操作数（矢量）的起始地址。；hor_size(输入): 从源图中加载图片的水平宽度，单位为像素。取值范围：[1, 4094]。；ver_size(输入): 从源图中加载图片的垂直高度，单位为像素。取值范围：[1, 4094]。；hor_start_pos(输入): 加载图片在源图片上的水平起始地址，单位为像素。取值范围：[0, 4095]。；ver_start_pos(输入): 加载图片在源图片上的垂直起始地址，单位为像素。取值范围：[0, 4095]。；src_hor_size(输入): 源图片水平宽度，单位为像素。取值范围：[1, 4094]。；top_pad_size(输入): 目的图片顶部填充的像素数。取值范围：[0, 32]。；bot_pad_size(输入): 目的图片底部填充的像素数。取值范围：[0, 32]。

约束：- 各存储单元的空间大小和对齐要求
- 操作数地址重叠约束

仅 Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [LoadImageToLocal](../../basic_api/cube_compute/cube_load_aux_config/load_image_to_local.md)（`related`）：LoadImageToLocal 与《AscLoadImageToCbuf》的实质衔接是：LoadImageToLocal 的 AIPP 配置由边界填充、重复、尺寸和 fmatrix 参数共同决定，C/C++ 入口消费同一搬入契约。
<!-- cannbot:related:end -->
