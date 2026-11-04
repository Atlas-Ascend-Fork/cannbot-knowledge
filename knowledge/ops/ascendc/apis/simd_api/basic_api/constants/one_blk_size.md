---
type: API
title: ONE_BLK_SIZE
description: ONE_BLK_SIZE 是 AscendC 的 DataBlock 字节数常量，值为 32，是以 DataBlock 为单位的 blockLen/srcGap/dstGap/dstStride
  与字节数之间的换算基准。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.alignment
status: draft
sources:
- resource: https://gitcode.com/cann/asc-devkit/blob/016ba4a159eda090c4d60a1cdcd1ccca2a36cb0a/impl/basic_api/utils/kernel_utils_constants.h
  role: primary
- resource: https://gitcode.com/cann/asc-devkit/blob/016ba4a159eda090c4d60a1cdcd1ccca2a36cb0a/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_store/DataCopy_L0CToL1.md
  role: example
- resource: https://gitcode.com/cann/asc-devkit/blob/016ba4a159eda090c4d60a1cdcd1ccca2a36cb0a/include/adv_api/transpose/confusion_transpose_tiling.h
  role: header
created_at: '2026-10-29T07:13:47Z'
updated_at: '2026-10-29T07:13:47Z'
platforms:
- agnostic
---

# ONE_BLK_SIZE

ONE_BLK_SIZE 是 AscendC 的 DataBlock（数据块）字节数常量，值为 32。它是 `DataCopyParams.blockLen`/`srcGap`/`dstGap`、`DataCopyEnhancedParams.dstStride` 等"以 DataBlock 计"的参数的换算基准，也用于把字节数换算成块数（如 `baseM * c0Size * sizeof(T) / ONE_BLK_SIZE`）。

定义位置：`impl/basic_api/utils/kernel_utils_constants.h:255`（device 侧）与 `:272`（host 侧）。该常量不单独出现在公开 `include/` 头文件的顶层声明里，而是由 `include/basic_api/kernel_struct_data_copy.h:28` 等公开头文件间接引入。固定 commit `016ba4a159eda090c4d60a1cdcd1ccca2a36cb0a`。

## 常量定义

```cpp
#if !defined(__NPU_HOST__) && !defined(__ASCC_HOST__)

#ifndef ASCC_PARAM_BLOCK_CUBE
#define ASCC_PARAM_BLOCK_CUBE
const int32_t BLOCK_CUBE = 16;
#endif

#ifndef ASCC_PARAM_ONE_BLK_SIZE
#define ASCC_PARAM_ONE_BLK_SIZE
const uint16_t ONE_BLK_SIZE = 32;
#endif

#ifndef ASCC_PARAM_CUBE_MAX_SIZE
#define ASCC_PARAM_CUBE_MAX_SIZE
const int32_t CUBE_MAX_SIZE = 256;
#endif

#else // defined(__NPU_HOST__) || defined(__ASCC_HOST__)

#ifndef ASCC_PARAM_BLOCK_CUBE
#define ASCC_PARAM_BLOCK_CUBE
constexpr uint32_t BLOCK_CUBE = 16;
#endif

#ifndef ASCC_PARAM_ONE_BLK_SIZE
#define ASCC_PARAM_ONE_BLK_SIZE
constexpr uint32_t ONE_BLK_SIZE = 32;
#endif

#ifndef ASCC_PARAM_CUBE_MAX_SIZE

// :388-389（派生常量）
const uint32_t ONE_BLK_HALF_NUM = ONE_BLK_SIZE / B16_BYTE_SIZE;
const uint32_t ONE_BLK_FLOAT_NUM = ONE_BLK_SIZE / B32_BYTE_SIZE;

// include/adv_api/transpose/confusion_transpose_tiling.h:29-32（host 侧重复定义）
#ifndef ASCC_PARAM_ONE_BLK_SIZE
#define ASCC_PARAM_ONE_BLK_SIZE
constexpr uint32_t ONE_BLK_SIZE = 32;
#endif

// include/adv_api/transpose/confusion_transpose_tiling.h:46-49（device 侧重复定义）
#ifndef ASCC_PARAM_ONE_BLK_SIZE
#define ASCC_PARAM_ONE_BLK_SIZE
const uint16_t ONE_BLK_SIZE = 32;
#endif
```

同一常量在 `include/adv_api/transpose/confusion_transpose_tiling.h` 中有一份重复定义（host `:31` 为 `constexpr uint32_t`、device `:48` 为 `const uint16_t`），两处都由 `ASCC_PARAM_ONE_BLK_SIZE` 保护，取值一致。

## 取值说明

| 属性 | 值 |
| --- | --- |
| 取值 | 32 |
| 单位 | 字节（B） |
| device 侧类型 | `const uint16_t` |
| host 侧类型 | `constexpr uint32_t` |
| 派生常量 | `ONE_BLK_HALF_NUM = ONE_BLK_SIZE / B16_BYTE_SIZE`、`ONE_BLK_FLOAT_NUM = ONE_BLK_SIZE / B32_BYTE_SIZE`（`:388-389`） |

## 约束与注意事项

- 32 字节是**字节数**，不是元素个数：一个 DataBlock 能装 16 个 half、8 个 float、32 个 int8。
- 以 DataBlock 为单位的参数（blockLen/srcGap/dstGap/dstStride）与以字节为单位的参数（DataCopyExtParams.blockLen/srcStride）使用不同的换算基准，混用会差 32 倍。
- device 与 host 两侧的类型不同（`const uint16_t` 与 `constexpr uint32_t`），在模板元编程或常量表达式位置使用时需按侧选择。
- 该常量在文档中没有独立的"产品支持情况"节，其可用性由所在头文件与架构宏决定，不构成单一产品的专属能力。

## 来源锚点

- 定义：`impl/basic_api/utils/kernel_utils_constants.h:255`（device）、`:272`（host）、派生量 `:388-389`；重复定义 `include/adv_api/transpose/confusion_transpose_tiling.h:31`、`:48`。
- 用法证据：`docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_store/DataCopy_L0CToL1.md:214`、同目录 `Fixpipe_L0CToL1.md:270`、`docs/zh/api/SIMD-API/basic_api/aux_data_structures/TensorTrait/more_examples.md:183`。

## 相关 runbook

- [Ascend 950 DMA 最小 32B 块粒度](../../../../runbooks/compilation/ascend950_dma_32b_minimum_block_granularity.md)
- [DataCopyParams.blockLen 以 32B 块为单位](../../../../runbooks/precision/datacopyparams_blocklen_is_32b_blocks.md)
