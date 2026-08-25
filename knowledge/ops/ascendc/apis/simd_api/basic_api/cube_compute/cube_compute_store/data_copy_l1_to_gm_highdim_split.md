---
type: API
title: DataCopyL1ToGMHighdimSplit
description: 将矩阵从L1 Buffer搬运至Global Memory，通过配置数据块个数、长度和地址偏移实现非连续搬运。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_store/DataCopy_L1ToGM_highdim_split.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# DataCopyL1ToGMHighdimSplit

将矩阵从 L1 Buffer 搬运至 Global Memory，通过配置数据块个数、长度和地址偏移实现非连续搬运，格式和内容保持不变。头文件 `basic_api/kernel_operator_data_copy_intf.h`。

参数：dst 为 GlobalTensor（GM，1 字节对齐）；src 为 LocalTensor（L1，32 字节对齐）；repeatParams 为 DataCopyParams。DataCopyParams 字段：blockCount[0,4095]默认 1、blockLen[0,65535]单位 DataBlock(32B)、srcGap[0,65535]源相邻块间隔、dstGap[0,65535]目的相邻块间隔。blockCount 或 blockLen 为 0 时为 NOP。

数据类型：int8_t、uint8_t、int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float、int64_t、uint64_t、double，源和目的类型一致。

约束：不支持 950；支持 a2/a3、Kirin X90/9030。连续搬运场景推荐使用 DataCopy（L1ToGM 连续搬运）。

<!-- cannbot:related:start -->
## 相关

- [DataCopyL1ToGMContinuous](data_copy_l1_to_gm_continuous.md)（`related`）：HighdimSplit 用 blockCount/blockLen/gap 做非连续 L1→GM，连续版用于无 gap 的整段搬出；正文明确连续场景优先后者。
<!-- cannbot:related:end -->
