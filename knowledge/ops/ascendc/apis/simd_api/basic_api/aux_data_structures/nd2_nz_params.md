---
type: API
title: Nd2NzParams
description: Nd2NzParams 是 ND→NZ 布局转换搬运的参数结构体，描述源 ND 矩阵个数/行数/列数、相邻矩阵间隔，以及目的 NZ 矩阵在
  C0、N、矩阵三个方向的步长。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.data_movement.layout_transform
status: draft
sources:
- resource: https://gitcode.com/cann/asc-devkit/blob/016ba4a159eda090c4d60a1cdcd1ccca2a36cb0a/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/DataCopy_GMToL1_ND2NZ.md
  role: primary
- resource: https://gitcode.com/cann/asc-devkit/blob/016ba4a159eda090c4d60a1cdcd1ccca2a36cb0a/include/basic_api/kernel_struct_data_copy.h
  role: header
created_at: '2026-10-29T07:13:45Z'
updated_at: '2026-10-29T07:13:45Z'
platforms:
- '950'
- a2
- a3
- 310p
- kirin_x90
- kirin_9030
source_headers:
- include/basic_api/kernel_struct_data_copy.h
---

# Nd2NzParams

Nd2NzParams 是 ND→NZ 布局转换搬运（GM→L1 的 `DataCopy` ND2NZ 通路）的参数结构体，描述源 ND 矩阵的个数、行数、列数、相邻 ND 矩阵间隔，以及目的 NZ 矩阵在 C0、N、矩阵三个方向上的起始地址步长。它把"行优先的 ND 数据"按 32B 的 C0 分形重排成 NZ 布局。

头文件：`include/basic_api/kernel_struct_data_copy.h`。结构体声明位于 `:280-336`（固定 commit `016ba4a159eda090c4d60a1cdcd1ccca2a36cb0a`）。

## 结构体定义

```cpp
struct Nd2NzParams {
    __aicore__ Nd2NzParams(){}

#if defined(__NPU_ARCH__) &&                                                                                 \
    ((__NPU_ARCH__ == 3510) || (__NPU_ARCH__ == 5102) || (__NPU_ARCH__ == 5162) || (__NPU_ARCH__ == 5101) || \
     (__NPU_ARCH__ == 5161) || (__NPU_ARCH__ == 5165) || (__NPU_ARCH__ == 5163))
    __aicore__ Nd2NzParams(
        const uint16_t ndNumIn, const uint16_t nValueIn, const uint32_t dValueIn, const uint64_t srcNdMatrixStrideIn,
        const uint64_t srcDValueIn, const uint16_t dstNzC0StrideIn, const uint16_t dstNzNStrideIn,
        const uint32_t dstNzMatrixStrideIn)
        : ndNum(ndNumIn),
          nValue(nValueIn),
          dValue(dValueIn),
          srcNdMatrixStride(srcNdMatrixStrideIn),
          srcDValue(srcDValueIn),
          dstNzC0Stride(dstNzC0StrideIn),
          dstNzNStride(dstNzNStrideIn),
          dstNzMatrixStride(dstNzMatrixStrideIn)
    {}

    uint16_t ndNum = 0;
    uint16_t nValue = 0;
    uint32_t dValue = 0;
    uint64_t srcNdMatrixStride = 0;
    uint64_t srcDValue = 0;
    uint16_t dstNzC0Stride = 0;
    uint16_t dstNzNStride = 0;
    uint32_t dstNzMatrixStride = 0;
#ifdef CANN_ASC_ENABLE_SID
    uint8_t sid = 0;
#endif
#else
    __aicore__ Nd2NzParams(
        const uint16_t ndNumIn, const uint16_t nValueIn, const uint16_t dValueIn, const uint16_t srcNdMatrixStrideIn,
        const uint16_t srcDValueIn, const uint16_t dstNzC0StrideIn, const uint16_t dstNzNStrideIn,
        const uint16_t dstNzMatrixStrideIn)
        : ndNum(ndNumIn),
          nValue(nValueIn),
          dValue(dValueIn),
          srcNdMatrixStride(srcNdMatrixStrideIn),
          srcDValue(srcDValueIn),
          dstNzC0Stride(dstNzC0StrideIn),
          dstNzNStride(dstNzNStrideIn),
          dstNzMatrixStride(dstNzMatrixStrideIn)
    {
    }

    uint16_t ndNum = 0;
    uint16_t nValue = 0;
    uint16_t dValue = 0;
    uint16_t srcNdMatrixStride = 0;
    uint16_t srcDValue = 0;
    uint16_t dstNzC0Stride = 0;
    uint16_t dstNzNStride = 0;
    uint16_t dstNzMatrixStride = 0;
#endif
};
```

同一结构体在两套架构分支下字段宽度不同：3510/5101/5102/5161/5162/5163/5165 用 `uint32_t dValue`、`uint64_t srcNdMatrixStride`/`srcDValue`/`dstNzMatrixStride`，并额外带 `sid`；其余架构全部为 `uint16_t` 且无 `sid`。

## 字段说明

| 字段 | 类型 | 语义 |
| --- | --- | --- |
| ndNum | uint16_t | 源矩阵中 ND 矩阵的个数，取值 [0, 4095]；0 表示不搬运（NOP）。 |
| nValue | uint16_t | 源 ND 矩阵的行数，取值 [0, 16384]；0 表示不搬运（NOP）。 |
| dValue | uint32_t / uint16_t | 源 ND 矩阵的列数，取值 [0, 65535]；`dValue * sizeof(T)` 不足 32B 对齐时，目的矩阵补 0 到 32B；0 表示不搬运（NOP）。 |
| srcNdMatrixStride | uint64_t / uint16_t | 相邻源 ND 矩阵起始地址偏移，单位元素个数；`ndNum = 1` 时无意义置 0，`ndNum != 1` 时置 0 表示重复搬第一个 ND 矩阵。 |
| srcDValue | uint64_t / uint16_t | 源矩阵一行包含的元素个数，取值 [1, 65535]，单位元素个数。 |
| dstNzC0Stride | uint16_t | 转换后目的 NZ 矩阵中相邻 Z 矩阵起始地址偏移，取值 [1, 16384]，单位 C0_SIZE（32 字节）。 |
| dstNzNStride | uint16_t | 目的 NZ 矩阵中相邻行起始地址偏移，取值 [1, 16384]，单位 C0_SIZE（32 字节）。 |
| dstNzMatrixStride | uint32_t / uint16_t | 目的矩阵中相邻 NZ 矩阵起始地址偏移，单位元素个数；`ndNum = 1` 时置 0，置 0 时每个 NZ 矩阵覆盖第一个 NZ 矩阵。 |
| sid | uint8_t | 仅在 `CANN_ASC_ENABLE_SID`（5101/5161/5163/5165）下存在；语义：unknown（文档未说明）。 |

## 约束与注意事项

- 三组 stride 语义不同：`srcNdMatrixStride`/`srcDValue`/`dstNzMatrixStride` 以元素个数计，`dstNzC0Stride`/`dstNzNStride` 以 32B C0_SIZE 计。
- `ndNum`、`nValue`、`dValue` 任一为 0 都会把整次搬运退化为空操作，配置侧不要用 0 表达"全量"。
- `dValue` 未按 32B 对齐时，目的侧会自动补 0，目的矩阵容量需按对齐后的列宽预留。
- 文档只给出一张取值范围表；两套架构分支的字段宽度差异来自头文件，文档未分别说明（宽度差异本身不是语义差异）。

## 来源锚点

- 声明：`include/basic_api/kernel_struct_data_copy.h:280-336`。
- 字段语义：`docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/DataCopy_GMToL1_ND2NZ.md` 表3（`:87-99`）、产品支持情况 `:3-33`。

## 相关 runbook

- [V220 逐分形手工 3D im2col/L0A 装载](../../../../runbooks/compilation/ol_197_v220_manual_per_fractal_3d_im2col_cube_operand_loa.md)
