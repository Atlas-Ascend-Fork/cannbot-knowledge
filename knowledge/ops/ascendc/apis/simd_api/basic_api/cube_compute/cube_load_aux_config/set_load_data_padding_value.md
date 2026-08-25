---
type: API
title: SetLoadDataPaddingValue
description: 调用LoadData（卷积数据搬运）接口时设置Pad填充的数值，当LoadData模板参数isSetPadding为false时通过本接口设置。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_load_aux_config/SetLoadDataPaddingValue.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetLoadDataPaddingValue

设置 LoadData（卷积数据搬运）接口的 Pad 填充值。当 LoadData 模板参数 isSetPadding 为 false 时须通过本接口设置；为 true 时本接口不生效。头文件 `basic_api/kernel_operator_mm_intf.h`。

参数：padValue 为填充值，模板类型 T 须与 LoadData 源操作数数据类型一致。支持 950/a2/a3/Atlas 200I/500 A2/Atlas 推理 AI Core/Kirin X90/9030，不支持 Vector Core 和 Atlas 训练系列。

<!-- cannbot:related:start -->
## 相关

- [AscSetL12l0PaddingVal](../../../c_api/sys_var/asc_set_l12l0_padding_val.md)（`related`）：SetLoadDataPaddingValue 与《AscSetL12l0PaddingVal》的实质衔接是：该配置在卷积 LoadData 前设定 padValue，Fmatrix/配置总览与 C API setter 是配置端；padding 参与数故障说明填充值不得进入有效 reduce count。
- [LoadData](../cube_compute_load/load_data_3_d.md)（`related`）：《LoadData》的任务是“将NC1HWC0格式的Feature Map完成Image to Column展开后搬入L0A/L0B Buffer，也可用于2D格式数据搬运。”。《SetLoadDataPaddingValue》具体提供“调用LoadData（卷积数据搬运）接口时设置Pad填充的数值，当LoadData模板参数isSetPadding为false时通过本接口设置。”，它直接用于3D LoadData 的 Fmatrix、repeat、boundary、padding 与 L1/L0 地址合同。
- [LoadData](../cube_compute_load/load_data_gm_to_l1_2_dv2.md)（`related`）：《LoadData》处理“完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位从Global Memory搬运至L1 Buffer。”。《SetLoadDataPaddingValue》明确提供“调用LoadData（卷积数据搬运）接口时设置Pad填充的数值，当LoadData模板参数isSetPadding为false时通过本接口设置。”，其参数、调用或验证步骤直接接入GM 到 L1 二维 LoadData 的 Fmatrix、repeat、边界和地址合同。
- [LoadData（BitMode卷积数据搬运）](../cube_compute_load/load_data_3_d_bit_mode.md)（`related`）：SetLoadDataPaddingValue 与《LoadData（BitMode卷积数据搬运）》的实质衔接是：该配置在卷积 LoadData 前设定 padValue，Fmatrix/配置总览与 C API setter 是配置端；padding 参与数故障说明填充值不得进入有效 reduce count。
- [SetLoadDataRepeat](set_load_data_repeat.md)（`related`）：《SetLoadDataRepeat》说明设置LoadData（卷积数据搬运）接口的repeat参数，通过一次调用完成多个迭代的数据搬运，支持配置迭代次数、步长、方向和K轴偏移。；《SetLoadDataPaddingValue》说明调用LoadData（卷积数据搬运）接口时设置Pad填充的数值，当LoadData模板参数isSetPadding为false时通过本接口设置。。二者在SetLoadDataRepeat配置的repeat、步长和方向直接控制后续LoadData搬入循环上存在可执行的直接衔接。
- [SetPadValue](../../memory_vector_compute/data_move_aux_config/set_pad_value_isasi.md)（`related`）：SetLoadDataPaddingValue 与《SetPadValue》的实质衔接是：该配置在卷积 LoadData 前设定 padValue，Fmatrix/配置总览与 C API setter 是配置端；padding 参与数故障说明填充值不得进入有效 reduce count。
- [LoadData](../cube_compute_load/load_data_2_d.md)（`same_topic`）：SetLoadDataPaddingValue 与《LoadData》的实质衔接是：该配置在卷积 LoadData 前设定 padValue，Fmatrix/配置总览与 C API setter 是配置端；padding 参与数故障说明填充值不得进入有效 reduce count。
- [LoadImageToLocal](load_image_to_local.md)（`same_topic`）：LoadImageToLocal 与《SetLoadDataPaddingValue》的实质衔接是：LoadImageToLocal 的 AIPP 配置由边界填充、重复、尺寸和 fmatrix 参数共同决定，C/C++ 入口消费同一搬入契约。
- [SetFmatrix](set_fmatrix.md)（`same_topic`）：SetFmatrix 与《SetLoadDataPaddingValue》的实质衔接是：SetFmatrix 必须在卷积 LoadData 前声明 H/W/padding/fmatrixMode；BitMode、C API config 与 Cube 搬入材料描述同一配置在数据加载阶段的消费。
- [矩阵搬入辅助配置接口](cube_load_aux_config.md)（`same_topic`）：SetLoadDataPaddingValue 与《矩阵搬入辅助配置接口》的实质衔接是：该配置在卷积 LoadData 前设定 padValue，Fmatrix/配置总览与 C API setter 是配置端；padding 参与数故障说明填充值不得进入有效 reduce count。
<!-- cannbot:related:end -->
