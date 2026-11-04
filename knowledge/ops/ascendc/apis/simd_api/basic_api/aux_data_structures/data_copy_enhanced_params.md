---
type: API
title: DataCopyEnhancedParams
description: DataCopyEnhancedParams 是 L0C→UB 搬运的增强参数结构体，配置搬运分形模式 blockMode、随路量化 deqScale/deqValue/deqTensorAddr、随路
  ReLU 与 padding 模式。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.compute.quantization
status: draft
sources:
- resource: https://gitcode.com/cann/asc-devkit/blob/016ba4a159eda090c4d60a1cdcd1ccca2a36cb0a/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_store/DataCopy_L0CToUB.md
  role: primary
- resource: https://gitcode.com/cann/asc-devkit/blob/016ba4a159eda090c4d60a1cdcd1ccca2a36cb0a/include/basic_api/kernel_struct_data_copy.h
  role: header
created_at: '2026-10-29T07:13:45Z'
updated_at: '2026-10-29T07:13:45Z'
platforms:
- 310p
source_headers:
- include/basic_api/kernel_struct_data_copy.h
---

# DataCopyEnhancedParams

DataCopyEnhancedParams 是 L0C→UB 搬运接口的增强参数结构体：在基本搬运参数之上补充搬运分形模式（`blockMode`）、随路量化（`deqScale`/`deqValue`/`deqTensorAddr`）、随路 ReLU（`isRelu`）以及 padding 模式（`padMode`/`padValue`）。文档中该结构体只随 L0C→UB（CO1→CO2）通路出现，且该通路的搬运功能仅在 310P AI Core 上生效。

头文件：`include/basic_api/kernel_struct_data_copy.h`。结构体声明位于 `:137-160`（固定 commit `016ba4a159eda090c4d60a1cdcd1ccca2a36cb0a`）。

## 结构体定义

```cpp
struct DataCopyEnhancedParams {
    __aicore__ DataCopyEnhancedParams() {}

    __aicore__ DataCopyEnhancedParams(
        const BlockMode blockModeIn, const DeqScale deqScaleIn, const uint64_t deqValueIn, const uint8_t sidStoreModeIn,
        const bool isReluIn, const pad_t padModeIn, const uint64_t padValueIn)
        : blockMode(blockModeIn),
          deqScale(deqScaleIn),
          deqValue(deqValueIn),
          sidStoreMode(sidStoreModeIn),
          isRelu(isReluIn),
          padMode(padModeIn),
          padValue(padValueIn)
    {}

    BlockMode blockMode = BlockMode::BLOCK_MODE_NORMAL;
    DeqScale deqScale = DeqScale::DEQ_NONE;
    uint64_t deqValue = 0;
    uint8_t sidStoreMode = 0;
    bool isRelu = false;
    pad_t padMode = pad_t::PAD_NONE;
    uint64_t padValue = 0;
    uint64_t deqTensorAddr = 0;
};
```

## 字段说明

| 字段 | 类型 | 语义 |
| --- | --- | --- |
| blockMode | BlockMode | 搬运基本分形：`BLOCK_MODE_MATRIX` 为一个 16\*16 cube 分形，`BLOCK_MODE_VECTOR` 为一个 1\*16 cube 分形；`BLOCK_MODE_NORMAL`、`BLOCK_MODE_SMALL_CHANNEL`、`BLOCK_MODE_DEPTHWISE` 文档标注"当前暂不支持"。默认值 `BLOCK_MODE_NORMAL`。 |
| deqScale | DeqScale | 随路精度转换（量化）模式，默认 `DEQ_NONE`；`DEQ`/`DEQ8`/`DEQ16` 需配 `deqValue`，`VDEQ`/`VDEQ8`/`VDEQ16` 需配 `deqTensorAddr` 指向的反量化参数向量。 |
| deqValue | uint64_t | 量化系数，按 `deqScale` 模式对应的比特位配置，默认 0。 |
| sidStoreMode | uint8_t | `deqScale` 为 `DEQ8`/`VDEQ8` 时的结果存储模式：0 存每个 DataBlock 高 16 字节，1 存低 16 字节，2 存完整 32 字节。默认 0。 |
| isRelu | bool | 是否随路做线性整流；配置 `deqValue` 时置 true 会刷新量化系数的 ReLU 标志位，配置 `deqTensorAddr` 时以本字段为准。默认 false。 |
| padMode | pad_t | 文档标注为"预留参数，当前暂不支持"，默认 `PAD_NONE`。 |
| padValue | uint64_t | 文档表3未列出该字段的语义：unknown。 |
| deqTensorAddr | uint64_t | VDEQ 模式下 UB 中反量化参数向量的起始地址，需 32 字节对齐；VDEQ 向量为 32 字节（16 个 half），VDEQ8/VDEQ16 每个元素 64bit、每数据块一个 128 字节向量。默认 0。 |

## 约束与注意事项

- 参数单位随 `blockMode` 变化：MATRIX + half 时 `blockLen`/`srcStride` 为 512B、`dstStride` 为 32B；MATRIX + float 时分别为 1024B/1024B/32B；VECTOR + half 为 32B/512B/32B；VECTOR + float 为 64B/1024B/32B。这些单位是文档表4显式给出的，不能当作字节通用值套用。
- `blockMode` 的三个取值当前标注为暂不支持，可用于生产的实际组合只有 MATRIX 与 VECTOR。
- `padMode`、`padValue` 属预留/未说明字段，不要据字段名推断行为。
- 结构体只在 L0C→UB 增强搬运的参数位置上使用；同通路的功能生效范围受产品支持限制（310P AI Core）。

## 来源锚点

- 声明：`include/basic_api/kernel_struct_data_copy.h:137-160`。
- 字段语义：`docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_store/DataCopy_L0CToUB.md` 表3（`:71-83`）、单位表4（`:83-92`）、量化模式表5（`:92-108`）、产品支持情况 `:3-29`。

## 相关 runbook

- [Cube 几何探针（含 L0C→UB 增强搬运用法）](../../../../runbooks/performance/standalone_probe_kernel_cube_geometry.md)
