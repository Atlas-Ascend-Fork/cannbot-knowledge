---
type: API
title: DataCopyL1ToGMContinuous
description: 将矩阵从L1 Buffer连续搬运至Global Memory，数据搬运时格式和内容保持不变。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_store/DataCopy_L1ToGM_continuous.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# DataCopyL1ToGMContinuous

将矩阵从 L1 Buffer 连续搬运至 Global Memory，格式和内容保持不变。头文件 `basic_api/kernel_operator_data_copy_intf.h`。

参数：dst 为 GlobalTensor（GM，1 字节对齐）；src 为 LocalTensor（L1，32 字节对齐）；count 为搬运元素个数，count×sizeof(T) 须 32 字节对齐，未对齐时向下取整到 32 字节。

数据类型：int8_t、uint8_t、int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float、int64_t、uint64_t、double，源和目的类型一致。

约束：不支持 950；支持 a2/a3、Kirin X90/9030。非连续搬运场景请使用 DataCopy（L1ToGM 高维切分）。

<!-- cannbot:related:start -->
## 相关

- [DataCopyL1ToGMHighdimSplit](data_copy_l1_to_gm_highdim_split.md)（`related`）：约束：不支持 950；支持 a2/a3、Kirin X90/9030。连续搬运场景推荐使用 DataCopy（L1ToGM 连续搬运）。；将矩阵从 L1 Buffer 连续搬运至 Global Memory，格式和内容保持不变。头文件 `basic_api/kernel_operator_data_copy_intf.h`。。高维切分卡明确连续场景改用 DataCopy，目标卡给出推荐接口的 L1 到 GM 数据合同。
<!-- cannbot:related:end -->
