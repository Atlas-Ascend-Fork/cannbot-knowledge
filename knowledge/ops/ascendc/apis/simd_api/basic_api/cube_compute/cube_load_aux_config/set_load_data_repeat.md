---
type: API
title: SetLoadDataRepeat
description: 设置LoadData（卷积数据搬运）接口的repeat参数，通过一次调用完成多个迭代的数据搬运，支持配置迭代次数、步长、方向和K轴偏移。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_load_aux_config/SetLoadDataRepeat.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetLoadDataRepeat

设置 LoadData（卷积数据搬运）接口的 repeat 参数，通过一次调用完成多个迭代的数据搬运。头文件 `basic_api/kernel_operator_mm_intf.h`。

参数：repeatParams 为 LoadDataRepeatParam。字段：repeatStride[0,65535]相邻迭代起始地址距离（repeatMode=0 时单位 16 元素，repeatMode=1 时单位与型号相关）、repeatTime[0,255]迭代次数（0 为 NOP）、repeatMode(0=height 方向/1=width 方向)、dstStride 输出矩阵 K 轴偏移（512B 分形为单位，仅 950 支持，950 调用时必须配置）。

约束：height 方向 repeatStride 单位 16 元素，width 方向单位 32/sizeof(data_type) 元素。支持 950/a2/a3/Atlas 200I/500 A2，不支持 Atlas 推理 AI Core/Vector Core/Atlas 训练系列。

<!-- cannbot:related:start -->
## 相关

- [LoadData](../cube_compute_load/load_data_2_d.md)（`related`）：《SetLoadDataRepeat》说明设置LoadData（卷积数据搬运）接口的repeat参数，通过一次调用完成多个迭代的数据搬运，支持配置迭代次数、步长、方向和K轴偏移。；《LoadData》说明完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位，支持GM到L0A/L0B Buffer及L1 Buffer到L0A/L0B Buffer通路。。二者在SetLoadDataRepeat配置的repeat、步长和方向直接控制后续LoadData搬入循环上存在可执行的直接衔接。
- [LoadData](../cube_compute_load/load_data_gm_to_l1_2_dv2.md)（`related`）：《LoadData》处理“完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位从Global Memory搬运至L1 Buffer。”。《SetLoadDataRepeat》明确提供“设置LoadData（卷积数据搬运）接口的repeat参数，通过一次调用完成多个迭代的数据搬运，支持配置迭代次数、步长、方向和K轴偏移。”，其参数、调用或验证步骤直接接入GM 到 L1 二维 LoadData 的 Fmatrix、repeat、边界和地址合同。
- [LoadDataWithStride](../cube_compute_load/load_data_with_stride.md)（`related`）：《SetLoadDataRepeat》说明设置LoadData（卷积数据搬运）接口的repeat参数，通过一次调用完成多个迭代的数据搬运，支持配置迭代次数、步长、方向和K轴偏移。；《LoadDataWithStride》说明将NC1HWC0格式的Feature Map完成Image to Column展开后搬入对应内存，支持配置输出矩阵K轴方向偏移量dstStride。。二者在SetLoadDataRepeat配置的repeat、步长和方向直接控制后续LoadData搬入循环上存在可执行的直接衔接。
- [LoadDataWithTranspose](../cube_compute_load/load_data_with_transpose.md)（`related`）：《SetLoadDataRepeat》说明设置LoadData（卷积数据搬运）接口的repeat参数，通过一次调用完成多个迭代的数据搬运，支持配置迭代次数、步长、方向和K轴偏移。；《LoadDataWithTranspose》说明完成普通矩阵计算所需的2D格式数据搬运，搬运过程中伴随转置操作，支持L1 Buffer到L0A/L0B Buffer通路。。二者在SetLoadDataRepeat配置的repeat、步长和方向直接控制后续LoadData搬入循环上存在可执行的直接衔接。
- [LoadImageToLocal](load_image_to_local.md)（`related`）：《SetLoadDataRepeat》说明设置LoadData（卷积数据搬运）接口的repeat参数，通过一次调用完成多个迭代的数据搬运，支持配置迭代次数、步长、方向和K轴偏移。；《LoadImageToLocal》说明将图像数据从Global Memory搬运到Local Memory。搬运过程中可以完成图像预处理操作：包括图像翻转，改变图像尺寸（抠图，裁边，缩放，伸展），以及色域转换，类型转换等。图像预处理的相关参数通过SetAippFunctions进行配置。。二者在SetLoadDataRepeat配置的repeat、步长和方向直接控制后续LoadData搬入循环上存在可执行的直接衔接。
- [SetLoadDataBoundary](set_load_data_boundary.md)（`related`）：《SetLoadDataRepeat》说明设置LoadData（卷积数据搬运）接口的repeat参数，通过一次调用完成多个迭代的数据搬运，支持配置迭代次数、步长、方向和K轴偏移。；《SetLoadDataBoundary》说明设置LoadData（卷积数据搬运）接口所需的L1 Buffer（A1/B1）边界值，源操作数地址超出边界时从起始地址开始读取。。二者在SetLoadDataRepeat配置的repeat、步长和方向直接控制后续LoadData搬入循环上存在可执行的直接衔接。
- [SetLoadDataPaddingValue](set_load_data_padding_value.md)（`related`）：《SetLoadDataRepeat》说明设置LoadData（卷积数据搬运）接口的repeat参数，通过一次调用完成多个迭代的数据搬运，支持配置迭代次数、步长、方向和K轴偏移。；《SetLoadDataPaddingValue》说明调用LoadData（卷积数据搬运）接口时设置Pad填充的数值，当LoadData模板参数isSetPadding为false时通过本接口设置。。二者在SetLoadDataRepeat配置的repeat、步长和方向直接控制后续LoadData搬入循环上存在可执行的直接衔接。
- [Sort32](../../memory_vector_compute/sort_and_merge/sort32.md)（`related`）：《SetLoadDataRepeat》说明设置LoadData（卷积数据搬运）接口的repeat参数，通过一次调用完成多个迭代的数据搬运，支持配置迭代次数、步长、方向和K轴偏移。；《Sort32》说明一次迭代内对32个数按score域降序排列，结果以score和index的结构存储在目的张量中。。二者在SetLoadDataRepeat配置的repeat、步长和方向直接控制后续LoadData搬入循环上存在可执行的直接衔接。
- [矩阵搬入辅助配置接口](cube_load_aux_config.md)（`related`）：《SetLoadDataRepeat》说明设置LoadData（卷积数据搬运）接口的repeat参数，通过一次调用完成多个迭代的数据搬运，支持配置迭代次数、步长、方向和K轴偏移。；《矩阵搬入辅助配置接口》说明矩阵搬入辅助配置接口集，包含 Fill、SetFmatrix、SetLoadDataBoundary、SetLoadDataPaddingValue 等。。二者在SetLoadDataRepeat配置的repeat、步长和方向直接控制后续LoadData搬入循环上存在可执行的直接衔接。
- [LoadData](../cube_compute_load/load_data_3_d.md)（`same_topic`）：《SetLoadDataRepeat》说明设置LoadData（卷积数据搬运）接口的repeat参数，通过一次调用完成多个迭代的数据搬运，支持配置迭代次数、步长、方向和K轴偏移。；《LoadData》说明将NC1HWC0格式的Feature Map完成Image to Column展开后搬入L0A/L0B Buffer，也可用于2D格式数据搬运。。二者在SetLoadDataRepeat配置的repeat、步长和方向直接控制后续LoadData搬入循环上存在可执行的直接衔接。
- [LoadData（BitMode 2D矩阵搬运）](../cube_compute_load/load_data_2_d_bit_mode.md)（`same_topic`）：《SetLoadDataRepeat》说明设置LoadData（卷积数据搬运）接口的repeat参数，通过一次调用完成多个迭代的数据搬运，支持配置迭代次数、步长、方向和K轴偏移。；《LoadData（BitMode 2D矩阵搬运）》说明负责完成普通矩阵计算所需的2D格式数据的搬运，以大小为512字节的数据分形为单位进行搬运，支持的数据通路为：L1 Buffer->L0A Buffer、L1 Buffer->L0B Buffer。 本接口与LoadData（2D矩阵搬运V2）接口的差异在于参数的传入方式不同，本接口传入的是一个联合体结构Load2DBitModeParam。。二者在SetLoadDataRepeat配置的repeat、步长和方向直接控制后续LoadData搬入循环上存在可执行的直接衔接。
- [SetLoadDataRepeatWithStride](set_load_data_repeat_with_stride.md)（`same_topic`）：《SetLoadDataRepeat》说明设置LoadData（卷积数据搬运）接口的repeat参数，通过一次调用完成多个迭代的数据搬运，支持配置迭代次数、步长、方向和K轴偏移。；《SetLoadDataRepeatWithStride》说明设置LoadDataWithStride接口的repeat参数，通过一次调用完成多个迭代的数据搬运，并配置输出矩阵K轴方向偏移。。二者在SetLoadDataRepeat配置的repeat、步长和方向直接控制后续LoadData搬入循环上存在可执行的直接衔接。
<!-- cannbot:related:end -->
