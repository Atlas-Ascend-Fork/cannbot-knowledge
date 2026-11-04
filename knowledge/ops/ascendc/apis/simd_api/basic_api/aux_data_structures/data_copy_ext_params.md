---
type: API
title: DataCopyExtParams
description: DataCopyExtParams 是 DataCopyPad 等扩展搬运的参数结构体，单位按搬运方向不对称：GM→UB 时
  blockLen/srcStride 以字节计、dstStride 以 32B DataBlock 计；UB→GM 时 srcStride 以 32B
  DataBlock 计、dstStride 以字节计；blockLen 两个方向都以字节计。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.data_movement.memory_access
status: draft
sources:
- resource: https://gitcode.com/cann/asc-devkit/blob/016ba4a159eda090c4d60a1cdcd1ccca2a36cb0a/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopyPad_GMToUB.md
  role: primary
- resource: https://gitcode.com/cann/asc-devkit/blob/016ba4a159eda090c4d60a1cdcd1ccca2a36cb0a/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopyPad_UBToGM.md
  role: primary
- resource: https://gitcode.com/cann/asc-devkit/blob/016ba4a159eda090c4d60a1cdcd1ccca2a36cb0a/include/basic_api/kernel_struct_data_copy.h
  role: header
created_at: '2026-10-29T07:13:45Z'
updated_at: "2026-11-02T07:57:34Z"
platforms:
- '950'
- a2
- a3
- 310b
source_headers:
- include/basic_api/kernel_struct_data_copy.h
---

# DataCopyExtParams

DataCopyExtParams 是 `DataCopyPad`（GM↔UB 带 padding 搬运）等扩展搬运接口的搬运参数结构体。与 DataCopyParams 的 32B DataBlock 语义不同，它的间隔单位**按搬运方向不对称**：GM→UB 时 `blockLen`/`srcStride` 以字节为单位、`dstStride` 以 DataBlock（32B）为单位；UB→GM 时正好反过来（`srcStride` 按 DataBlock、`dstStride` 按字节）；`blockLen` 两个方向都以字节计。它还可在高维场景跨越 UB 之外的大间隔。

头文件：`include/basic_api/kernel_struct_data_copy.h`。结构体声明位于 `:206-238`（固定 commit `016ba4a159eda090c4d60a1cdcd1ccca2a36cb0a`）。

## 结构体定义

```cpp
struct DataCopyExtParams {
    __aicore__ DataCopyExtParams(){}

#if defined(__NPU_ARCH__) &&                                                                                 \
    ((__NPU_ARCH__ == 3510) || (__NPU_ARCH__ == 5102) || (__NPU_ARCH__ == 5162) || (__NPU_ARCH__ == 5101) || \
     (__NPU_ARCH__ == 5161) || (__NPU_ARCH__ == 5165) || (__NPU_ARCH__ == 5163))
    __aicore__ __callee__ DataCopyExtParams(
        const uint16_t count, const uint32_t len, const int64_t srcStrideIn, const int64_t dstStrideIn,
        const uint32_t rsvIn)
#else
    __aicore__ __callee__ DataCopyExtParams(
        const uint16_t count, const uint32_t len, const uint32_t srcStrideIn, const uint32_t dstStrideIn,
        const uint32_t rsvIn)
#endif
        : blockCount(count), blockLen(len), srcStride(srcStrideIn), dstStride(dstStrideIn), rsv(rsvIn)
    {}

    uint16_t blockCount = DEFAULT_DATA_COPY_NBURST;
    uint32_t blockLen = 0;
#if defined(__NPU_ARCH__) &&                                                                                 \
    ((__NPU_ARCH__ == 3510) || (__NPU_ARCH__ == 5102) || (__NPU_ARCH__ == 5162) || (__NPU_ARCH__ == 5101) || \
     (__NPU_ARCH__ == 5161) || (__NPU_ARCH__ == 5165) || (__NPU_ARCH__ == 5163))
    int64_t srcStride = static_cast<int64_t>(DEFAULT_DATA_COPY_STRIDE);
    int64_t dstStride = static_cast<int64_t>(DEFAULT_DATA_COPY_STRIDE);
#else
    uint32_t srcStride = DEFAULT_DATA_COPY_STRIDE;
    uint32_t dstStride = DEFAULT_DATA_COPY_STRIDE;
#endif
    uint32_t rsv = 0; // reserved information
#ifdef CANN_ASC_ENABLE_SID
    uint8_t sid = 0;
#endif
};
```

`srcStride`/`dstStride` 的类型与构造函数签名按 `__NPU_ARCH__` 分支：3510/5101/5102/5161/5162/5163/5165 为 `int64_t`，其余架构为 `uint32_t`。

## 字段说明

同一结构体在不同产品上的取值域不同，且**间隔字段单位随搬运方向翻转**，文档按方向分表给出。

GM→UB（`DataCopyPad_GMToUB.md`）：

| 字段 | 类型 | 语义（950 分支，文档表3） | 语义（A3/A2/310b 分支，文档表4） |
| --- | --- | --- | --- |
| blockCount | uint16_t | 数据块个数，取值 [0, 65535]，默认 1 | 数据块个数，取值 [0, 4095]，默认 1 |
| blockLen | uint32_t | 每个数据块长度，取值 [0, 2^21-1]，单位 1B；必须是 `sizeof(T)` 的整数倍，且不得超过 UB 空间 | 同左 |
| srcStride | int64_t / uint32_t | 源（GM 侧）相邻数据块间隔，取值 [-blockLen, 2^40-1]，单位 1B；取 `-blockLen` 表示每次重复搬运同一块 | 取值 [0, 2^32-1]，单位 1B |
| dstStride | int64_t / uint32_t | 目的（UB 侧）相邻数据块间隔，取值 [0, 65535]，单位 DataBlock（32B）；PaddingMode 为 Compact 时无效，默认 0 | 取值 [0, 2^32-1]，单位 DataBlock（32B） |
| rsv | uint32_t | 预留参数，当前需设置为 0 | 同左 |
| sid | uint8_t | 仅在 `CANN_ASC_ENABLE_SID` 下存在；语义：unknown（文档未说明） | 同左 |

UB→GM（`DataCopyPad_UBToGM.md`，间隔单位与 GM→UB 相反）：

| 字段 | 类型 | 语义（950 分支，文档表3） | 语义（A3/A2/310b 分支，文档表4） |
| --- | --- | --- | --- |
| blockCount | uint16_t | 数据块个数，取值 [0, 65535] | 数据块个数，取值 [0, 4095] |
| blockLen | uint32_t | 每个数据块长度，单位 1B；必须是 `sizeof(T)` 的整数倍 | 同左 |
| srcStride | int64_t / uint32_t | 源（VECIN/VECOUT，UB 侧）相邻数据块间隔，取值 [0, 65535]，单位 DataBlock（32B） | 取值 [0, 2^32-1]，单位 DataBlock（32B） |
| dstStride | int64_t / uint32_t | 目的（GM 侧）相邻数据块间隔，取值 [0, 2^40-1]，单位 1B（字节） | 取值 [0, 2^32-1]，单位 1B（字节） |

## 约束与注意事项

- **间隔单位按方向不对称，把 GM→UB 的单位表套到 UB→GM 会直接错位**：GM→UB 时"长度与源间隔是字节（1B）、目的间隔是 DataBlock（32B）"；UB→GM 时源间隔（UB 侧）是 DataBlock（32B）、目的间隔（GM 侧）是字节（1B）；`blockLen` 两个方向都以字节计。例：UB→GM 想让 UB 源块间隔 32B、GM 目的块间隔 32B，应填 `srcStride=1, dstStride=32`。
- GM→UB 的 `srcStride=-blockLen`（重复搬运同一块）只在 GM 源侧定义；UB→GM 文档未给出该取法。
- 不要与 `DataCopyParams`（高维切分搬运）混淆：后者 `srcGap`/`dstGap` 在 GM→UB 与 UB→GM 两个方向都以 DataBlock（32B）计，见 [DataCopyParams](data_copy_params.md)。
- `blockLen` 必须是 `sizeof(T)` 的整数倍，且搬运量不得超过 UB 空间；这两点文档以注记形式显式给出。
- 结构体本身不携带 padding 值：左/右 padding 与填充值由相邻的 `DataCopyPadExtParams<T>` 承载，两者配合使用。
- `dstStride` 在 Compact 模式下被忽略，保持默认 0 即可。

## 来源锚点

- 声明：`include/basic_api/kernel_struct_data_copy.h:206-238`。
- 字段语义与产品分支（GM→UB）：`docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopyPad_GMToUB.md` 表3（`:126-152`）、表4（`:152-163`）、产品支持情况 `:3-54`。
- 字段语义与产品分支（UB→GM）：`docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopyPad_UBToGM.md` 参数表（`:119-121`、`:145-147`）。

## 相关 runbook

- [DataCopyPad/DataCopyExtParams 在某代产品不可用](../../../../runbooks/compilation/pb_105_datacopypad_datacopyextparams_are_not_supported.md)
- [DataCopyPad 间隔字段按 32B DataBlock 计](../../../../runbooks/precision/datacopypad_stride_fields_use_32_byte_block_units.md)
