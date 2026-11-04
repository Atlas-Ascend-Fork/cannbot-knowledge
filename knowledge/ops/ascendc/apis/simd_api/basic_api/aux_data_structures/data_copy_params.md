---
type: API
title: DataCopyParams
description: DataCopyParams 是高维切分搬运的参数结构体，用 blockCount/blockLen 描述搬运块数与每块长度（单位 32B
  DataBlock），用 srcGap/dstGap 描述相邻数据块间隔，覆盖连续与非连续搬运。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.data_movement.data_copy
status: draft
sources:
- resource: https://gitcode.com/cann/asc-devkit/blob/016ba4a159eda090c4d60a1cdcd1ccca2a36cb0a/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopy_GMAndUB_highdim_split.md
  role: primary
- resource: https://gitcode.com/cann/asc-devkit/blob/016ba4a159eda090c4d60a1cdcd1ccca2a36cb0a/include/basic_api/kernel_struct_data_copy.h
  role: header
created_at: '2026-10-29T07:13:44Z'
updated_at: "2026-10-31T09:21:53Z"
platforms:
- '950'
- a2
- a3
- 310p
- 310b
- '910'
- kirin_x90
- kirin_9030
source_headers:
- include/basic_api/kernel_struct_data_copy.h
---

# DataCopyParams

DataCopyParams 是 AscendC 高维切分搬运接口的搬运参数结构体：用 `blockCount`/`blockLen` 描述"搬几块、每块多长"，用 `srcGap`/`dstGap` 描述相邻数据块之间的间隔，因此同时覆盖连续搬运与非连续（strided）搬运。GM↔UB 高维切分 DataCopy 及 GM→L1 的高维切分搬运都以该结构体作为 `repeatParams`/搬运参数入参。

头文件：`include/basic_api/kernel_struct_data_copy.h`。结构体声明位于 `:63-94`（固定 commit `016ba4a159eda090c4d60a1cdcd1ccca2a36cb0a`）。

## 结构体定义

```cpp
struct DataCopyParams {
    __aicore__ DataCopyParams() {}

    __aicore__ DataCopyParams(
        const uint16_t count, const uint16_t len, const uint16_t srcStrideIn, const uint16_t dstStrideIn)
        : blockCount(count), blockLen(len), srcStride(srcStrideIn), dstStride(dstStrideIn)
    {}

    uint16_t blockCount = DEFAULT_DATA_COPY_NBURST;
    uint16_t blockLen = 0;
    // srcStride and dstStride will be deprecated, use srcGap and dstGap instead.
    union {
        uint16_t srcGap = 0;
        // srcStride will be deprecated, use srcGap instead
        uint16_t srcStride;
    };

    union {
        uint16_t dstGap = 0;
        // dstStride will be deprecated, use dstGap instead
        uint16_t dstStride;
    };
#ifdef CANN_ASC_ENABLE_FIX_SHIFT
    uint8_t fixShiftVal = 0;
#endif
#ifdef CANN_ASC_ENABLE_POST_PROC_BUF
    uint8_t postProcBufBlock = 0;
#endif
#ifdef CANN_ASC_ENABLE_SID
    uint8_t sid = 0;
#endif
};
```

其中 `CANN_ASC_ENABLE_FIX_SHIFT`、`CANN_ASC_ENABLE_POST_PROC_BUF`、`CANN_ASC_ENABLE_SID` 三个宏在同一头文件 `:53-61` 按 `__NPU_ARCH__` 打开，决定结构体尾部是否存在对应字段。

## 字段说明

文档只给出下表四项的语义（`DataCopy_GMAndUB_highdim_split.md` 表3）；联合体别名与条件字段的语义在文档中缺失，按 `unknown` 标注。

| 字段 | 类型 | 语义 |
| --- | --- | --- |
| blockCount | uint16_t | 搬运的数据块个数，取值 [0, 4095]，默认值 1（`DEFAULT_DATA_COPY_NBURST`）。 |
| blockLen | uint16_t | 每个数据块长度，取值 [0, 65535]，单位 DataBlock（32B）。 |
| srcGap | uint16_t | 源操作数相邻数据块间隔，即前一个数据块结束地址与后一个数据块起始地址之差，取值 [0, 65535]，单位 DataBlock（32B）；`blockCount = 1` 时无意义，置 0。 |
| dstGap | uint16_t | 目的操作数相邻数据块间隔，即前一个数据块结束地址与后一个数据块起始地址之差，取值 [0, 65535]，单位 DataBlock（32B）；`blockCount = 1` 时无意义，置 0。 |
| srcStride | uint16_t | 与 `srcGap` 共用同一 union 存储的旧名；头文件注释标注 "srcStride will be deprecated, use srcGap instead"。文档表3只描述 `srcGap`，别名侧的独立语义未单独定义（按同义处理，不另立语义）。 |
| dstStride | uint16_t | 与 `dstGap` 共用同一 union 存储的旧名；头文件注释标注 "dstStride will be deprecated, use dstGap instead"。 |
| fixShiftVal | uint8_t | 仅在 `CANN_ASC_ENABLE_FIX_SHIFT` 下存在（`__NPU_ARCH__` 为 5101/5102/5161/5162/5163/5165）；语义：unknown（文档未说明）。 |
| postProcBufBlock | uint8_t | 仅在 `CANN_ASC_ENABLE_POST_PROC_BUF` 下存在（5101/5161/5163/5165）；语义：unknown。 |
| sid | uint8_t | 仅在 `CANN_ASC_ENABLE_SID` 下存在（5101/5161/5163/5165）；语义：unknown。 |

## 约束与注意事项

- `blockLen`、`srcGap`、`dstGap` 的长度单位都是 32B 的 DataBlock，不是元素个数、也不是字节数；例如 64 个 float 的连续数据是 8 个 DataBlock（`blockLen = 8`）。
- 结构体不自带元素类型信息，按元素计的搬运量需要调用方按 `sizeof(T)` 折算成 DataBlock 数。
- 非连续搬运时 `srcGap`/`dstGap` 是"块与块之间的空洞"，不是"块间距"；`blockCount = 1` 时两者不参与地址计算。
- 条件字段只影响结构体布局，不改变上述四个必要字段的语义。

## 来源锚点

- 声明：`include/basic_api/kernel_struct_data_copy.h:63-94`；条件宏 `:53-61`。
- 字段语义：`docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopy_GMAndUB_highdim_split.md` 表3（`:86-92`）、产品支持情况 `:3-33`。

## 相关 runbook

- [DataCopyParams.blockLen 以 32B 块为单位](../../../../runbooks/precision/datacopyparams_blocklen_is_32b_blocks.md)
- [DataCopyParams.blockLen 32B 块单位换算](../../../../runbooks/precision/datacopyparams_block_len_32b_block_units.md)
