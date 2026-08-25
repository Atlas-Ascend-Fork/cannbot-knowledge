---
type: API
title: LoadImageToLocal
description: 将图像数据从Global Memory搬运到Local Memory。搬运过程中可以完成图像预处理操作：包括图像翻转，改变图像尺寸（抠图，裁边，缩放，伸展），以及色域转换，类型转换等。图像预处理的相关参数通过SetAippFunctions进行配置。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_load_aux_config/LoadImageToLocal.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# LoadImageToLocal

将图像数据从 Global Memory 搬运到 Local Memory，搬运过程中可完成图像预处理（翻转、抠图、裁边、缩放、伸展、色域转换、类型转换）。预处理参数通过 SetAippFunctions 配置。

参数：dst 为 LocalTensor（32B 对齐）；loadDataParams 为 LoadImageToLocalParams。关键字段：horizSize[2,4095]加载宽度、vertSize[2,4095]加载高度、horizStartPos[0,4095]水平起始、vertStartPos[0,4095]垂直起始、srcHorizSize[2,4095]源图宽度、topPadSize/botPadSize/leftPadSize/rightPadSize[0,32]各方向填充像素数。YUV420SP 格式时 horizStartPos/vertStartPos/srcHorizSize 须为偶数；XRGB8888/RGB888/YUV400 格式时 horizStartPos 须为偶数。

支持 950/a2/a3/Atlas 200I/500 A2/Atlas 推理 AI Core，不支持 Vector Core 和 Atlas 训练系列。

<!-- cannbot:related:start -->
## 相关

- [AscLoadImageToCbuf](../../../c_api/cube_data_move/asc_load_image_to_cbuf.md)（`related`）：LoadImageToLocal 与《AscLoadImageToCbuf》的实质衔接是：LoadImageToLocal 的 AIPP 配置由边界填充、重复、尺寸和 fmatrix 参数共同决定，C/C++ 入口消费同一搬入契约。
- [SetAippFunctions](set_aipp_functions.md)（`related`）：SetAippFunctions 配置的裁剪、填充与色彩转换参数由 LoadImageToLocal 在图像搬入时消费，二者构成配置到执行的直接链路。
- [SetFmatrix](set_fmatrix.md)（`related`）：LoadImageToLocal 与《SetFmatrix》的实质衔接是：LoadImageToLocal 的 AIPP 配置由边界填充、重复、尺寸和 fmatrix 参数共同决定，C/C++ 入口消费同一搬入契约。
- [SetFmatrixBitMode](set_fmatrix_bit_mode.md)（`related`）：LoadImageToLocal 与《SetFmatrixBitMode》的实质衔接是：LoadImageToLocal 的 AIPP 配置由边界填充、重复、尺寸和 fmatrix 参数共同决定，C/C++ 入口消费同一搬入契约。
- [SetLoadDataRepeat](set_load_data_repeat.md)（`related`）：《SetLoadDataRepeat》说明设置LoadData（卷积数据搬运）接口的repeat参数，通过一次调用完成多个迭代的数据搬运，支持配置迭代次数、步长、方向和K轴偏移。；《LoadImageToLocal》说明将图像数据从Global Memory搬运到Local Memory。搬运过程中可以完成图像预处理操作：包括图像翻转，改变图像尺寸（抠图，裁边，缩放，伸展），以及色域转换，类型转换等。图像预处理的相关参数通过SetAippFunctions进行配置。。二者在SetLoadDataRepeat配置的repeat、步长和方向直接控制后续LoadData搬入循环上存在可执行的直接衔接。
- [SetLoadDataRepeatWithStride](set_load_data_repeat_with_stride.md)（`related`）：LoadImageToLocal 与《SetLoadDataRepeatWithStride》的实质衔接是：LoadImageToLocal 的 AIPP 配置由边界填充、重复、尺寸和 fmatrix 参数共同决定，C/C++ 入口消费同一搬入契约。
- [SetLoadDataBoundary](set_load_data_boundary.md)（`same_topic`）：LoadImageToLocal 与《SetLoadDataBoundary》的实质衔接是：LoadImageToLocal 的 AIPP 配置由边界填充、重复、尺寸和 fmatrix 参数共同决定，C/C++ 入口消费同一搬入契约。
- [SetLoadDataPaddingValue](set_load_data_padding_value.md)（`same_topic`）：LoadImageToLocal 与《SetLoadDataPaddingValue》的实质衔接是：LoadImageToLocal 的 AIPP 配置由边界填充、重复、尺寸和 fmatrix 参数共同决定，C/C++ 入口消费同一搬入契约。
- [矩阵搬入辅助配置接口](cube_load_aux_config.md)（`same_topic`）：LoadImageToLocal 与《矩阵搬入辅助配置接口》的实质衔接是：LoadImageToLocal 的 AIPP 配置由边界填充、重复、尺寸和 fmatrix 参数共同决定，C/C++ 入口消费同一搬入契约。
<!-- cannbot:related:end -->
