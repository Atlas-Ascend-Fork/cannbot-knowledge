---
type: API
title: TransData
description: 将输入数据的排布格式转换为目标排布格式，支持NCDHW与NDC1HWC0、FRACTAL_Z_3D之间的转换。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.layout_transform]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/tensor_transform/TransData.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# TransData

将输入数据的排布格式转换为目标排布格式。支持四种转换场景：NCDHW->NDC1HWC0、NCDHW->NDC1HWC0（带D轴拆分）、NZ->ND（1/2轴互换）、ND->NZ（1/2轴互换）。涉及C轴拆分为C1/C0和N轴拆分为N1/N0，位宽16的数据类型C0和N0固定为16。仅Ascend 950PR/950DT支持。

提供通过sharedTmpBuffer传入临时空间或由接口框架申请两种重载。临时空间大小通过GetTransDataMaxMinTmpSize获取。接口参数：dstTensor输出转换结果；srcTensor输入数据；sharedTmpBuffer临时缓存；transDataInfo含源/目标格式和shape信息。TPosition支持VECIN/VECCALC/VECOUT。

约束：遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [GetTransDataMaxMinTmpSize](get_trans_data_max_min_tmp_size.md)（`related`）：TransData is the kernel transform whose temporary-space bounds the focal host query calculates.
- [TransDataTo5HD](../../basic_api/memory_vector_compute/data_layout_conversion/trans_data_to5_hd.md)（`related`）：TransData 描述通用布局转换能力，TransDataTo5HD 是把输入专门转换到 5HD 的低层路径；选择 5HD 目标布局时后者落实前者的一种转换方向。
- [Transpose](transpose.md)（`same_topic`）：《Transpose》处理“对输入数据进行数据排布及Reshape操作，支持NZ与ND格式间的多种轴互换和转置场景。”。《TransData》明确提供“将输入数据的排布格式转换为目标排布格式，支持NCDHW与NDC1HWC0、FRACTAL_Z_3D之间的转换。”，其参数、调用或验证步骤直接接入Transpose 的 Tiling、转置搬运、布局转换和轴顺序验证。
<!-- cannbot:related:end -->
