---
type: API
title: FixpipeParams
description: FixpipeParams 是 Cube 结果搬出指令 Fixpipe 的参数族，包含 V220、Arch3510/C310 与模板三种形态，字段单位与量化配置随形态和产品不同。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.execution_unit.cube
status: draft
sources:
- resource: https://gitcode.com/cann/asc-devkit/blob/016ba4a159eda090c4d60a1cdcd1ccca2a36cb0a/include/basic_api/kernel_struct_fixpipe.h
  role: primary
- resource: https://gitcode.com/cann/asc-devkit/blob/016ba4a159eda090c4d60a1cdcd1ccca2a36cb0a/impl/basic_api/utils/kernel_utils_struct_dma_params.h
  role: implementation
- resource: https://gitcode.com/cann/asc-devkit/blob/016ba4a159eda090c4d60a1cdcd1ccca2a36cb0a/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_store/Fixpipe_L0CToGM.md
  role: supporting
- resource: https://gitcode.com/cann/asc-devkit/blob/016ba4a159eda090c4d60a1cdcd1ccca2a36cb0a/impl/tensor_api/legacy/legacy_utils.h
  role: implementation
created_at: '2026-10-29T07:13:46Z'
updated_at: "2026-10-31T09:21:53Z"
platforms:
- '950'
- a2
- a3
- 310b
- kirin_x90
- kirin_9030
source_headers:
- include/basic_api/kernel_struct_fixpipe.h
---

# FixpipeParams

FixpipeParams 是 Cube 结果搬出指令 `Fixpipe` 的参数族。族内不是单一结构体，而是按产品分代的多个类型：

- `FixpipeParamsV220`：V220 形态，`nSize`/`mSize`/`srcStride`/`dstStride` 四项必选，其余为量化、随路 ReLU、NZ2ND 与 channelSplit 的扩展项；`FixpipeParamsM300`、`FixpipeParamsM310` 是它的别名。
- `FixpipeParamsArch3510<format>`：3510 形态，按 `CO2Layout` 模板参数选择随路转换参数类型；`FixpipeParamsC310<format>` 继承它并只固定四个几何参数。
- `FixpipeParams<T>`：`impl` 层的模板形态，字段是 `cburstNum`/`burstLen` 等分形计数语义，与上面几种的字段名完全不同。

头文件：`include/basic_api/kernel_struct_fixpipe.h`（`:107-166` V220、`:190-223` Arch3510、`:225-236` C310 与别名）；模板形态 `impl/basic_api/utils/kernel_utils_struct_dma_params.h:100-129`。固定 commit `016ba4a159eda090c4d60a1cdcd1ccca2a36cb0a`。

## 结构体定义

```cpp
struct FixpipeParamsV220 {
    __aicore__ FixpipeParamsV220() {}

    __aicore__ FixpipeParamsV220(
        const uint16_t nSizeIn, const uint16_t mSizeIn, const uint16_t srcStrideIn, const uint32_t dstStrideIn,
        const bool reluEnIn)
        : nSize(nSizeIn), mSize(mSizeIn), srcStride(srcStrideIn), dstStride(dstStrideIn), reluEn(reluEnIn)
    {}

    __aicore__ FixpipeParamsV220(
        const uint16_t nSizeIn, const uint16_t mSizeIn, const uint16_t srcStrideIn, const uint32_t dstStrideIn,
        const bool reluEnIn, const QuantMode_t quantPreIn, const int64_t deqScalarIn, const uint16_t ndNumIn,
        const uint16_t srcNdStrideIn, const uint16_t dstNdStrideIn, const uint8_t unitFlagIn)
        : nSize(nSizeIn),
          mSize(mSizeIn),
          srcStride(srcStrideIn),
          dstStride(dstStrideIn),
          reluEn(reluEnIn),
          quantPre(quantPreIn),
          deqScalar(deqScalarIn),
          ndNum(ndNumIn),
          srcNdStride(srcNdStrideIn),
          dstNdStride(dstNdStrideIn),
          unitFlag(unitFlagIn)
    {}

    __aicore__ FixpipeParamsV220(
        const uint16_t nSizeIn, const uint16_t mSizeIn, const uint16_t srcStrideIn, const uint32_t dstStrideIn,
        const bool reluEnIn, const QuantMode_t quantPreIn, const int64_t deqScalarIn, const uint16_t ndNumIn,
        const uint16_t srcNdStrideIn, const uint16_t dstNdStrideIn, const uint8_t unitFlagIn,
        const bool isChannelSplitIn)
        : nSize(nSizeIn),
          mSize(mSizeIn),
          srcStride(srcStrideIn),
          dstStride(dstStrideIn),
          reluEn(reluEnIn),
          quantPre(quantPreIn),
          deqScalar(deqScalarIn),
          ndNum(ndNumIn),
          srcNdStride(srcNdStrideIn),
          dstNdStride(dstNdStrideIn),
          unitFlag(unitFlagIn),
          isChannelSplit(isChannelSplitIn)
    {}

    uint16_t nSize = 0;
    uint16_t mSize = 0; // M-DirectionSize
    uint16_t srcStride = 0;
    uint32_t dstStride = 0;
    // Params: used for Quant
    QuantMode_t quantPre = QuantMode_t::NoQuant;
    uint64_t deqScalar;
    // Params: used for nz2nd
    uint16_t ndNum = 1;
    uint16_t srcNdStride = 0;
    uint16_t dstNdStride = 0;
    bool reluEn = false;
    uint8_t unitFlag = 0;
    bool isChannelSplit = false;
};

// FixpipeParamsArch3510 / FixpipeParamsC310 / 别名 :190-236
template <CO2Layout format = CO2Layout::ROW_MAJOR>
struct FixpipeParamsArch3510 {
    __aicore__ FixpipeParamsArch3510() {}

    __aicore__ FixpipeParamsArch3510(
        const uint16_t nSizeIn, const uint16_t mSizeIn, const uint16_t srcStrideIn, const uint32_t dstStrideIn)
    {
        nSize = nSizeIn;
        mSize = mSizeIn;
        srcStride = srcStrideIn;
        dstStride = dstStrideIn;
    }
    ReluMode preReluMode = ReluMode::NO_RELU;
    ClipReluMode preClipReluMode = ClipReluMode::NOCLIP_RELU;
    uint64_t reluScalar;
    uint64_t vectorRelu;
    uint16_t nSize = 0;
    uint16_t mSize = 0; // M-DirectionSize
    uint16_t srcStride = 0;
    uint32_t dstStride = 0;
    // Params: used for Quant
    QuantMode_t quantPre = QuantMode_t::NoQuant;
    uint64_t deqScalar;
    bool reluEn = false;
    uint8_t unitFlag = 0;
    // c310 extend param
    uint8_t dualDstCtl = 0;
    bool subBlockId = false;
    typename TransformParams<format>::PARAMS params;
    bool isChannelSplit = false;
#ifdef CANN_ASC_ENABLE_FIX_SHIFT
    uint8_t fixShiftVal = 0;
#endif
};

template <CO2Layout format = CO2Layout::ROW_MAJOR>
struct FixpipeParamsC310 : FixpipeParamsArch3510<format> {
    __aicore__ FixpipeParamsC310() : FixpipeParamsArch3510<format>() {}

    __aicore__ FixpipeParamsC310(
        const uint16_t nSizeIn, const uint16_t mSizeIn, const uint16_t srcStrideIn, const uint32_t dstStrideIn)
        : FixpipeParamsArch3510<format>(nSizeIn, mSizeIn, srcStrideIn, dstStrideIn)
    {}
};

using FixpipeParamsM300 = FixpipeParamsV220;
using FixpipeParamsM310 = FixpipeParamsV220;
```

```cpp
struct FixpipeParams {
    __aicore__ FixpipeParams()
    {
        cburstNum = DEFAULT_DATA_COPY_NBURST;
        burstLen = 1;
        srcStride = DEFAULT_DATA_COPY_STRIDE;
        dstStride = DEFAULT_DATA_COPY_STRIDE;
        reluEn = false;
        unitFlag = 0;
    }

    __aicore__ FixpipeParams(
        const uint16_t count, const uint16_t len, const uint16_t srcStrideIn, const uint32_t dstStrideIn)
    {
        cburstNum = count;
        burstLen = len;
        dstStride = dstStrideIn;
        srcStride = srcStrideIn;
    }

    uint16_t cburstNum = 0;
    uint16_t burstLen = 0;
    uint32_t dstStride = 0;
    uint16_t srcStride = 0;
    // extend param
    QuantParams quantParams;
    bool reluEn = false;
    Nz2NdParams nz2ndParams;
    uint8_t unitFlag = 0;
};
```

## 字段说明（FixpipeParamsV220）

| 字段 | 类型 | 语义 |
| --- | --- | --- |
| nSize | uint16_t | 源 NZ 矩阵 N 方向大小，取值 [0, 4095]，须为 16 的倍数（float 输出开启 channelSplit 时为 8 的倍数）；0 表示不搬运（NOP）。 |
| mSize | uint16_t | 源 NZ 矩阵 M 方向大小；不开启 NZ2ND 时取值 [0, 65535]，开启 NZ2ND 时 [0, 8192]；0 表示不搬运（NOP）。 |
| srcStride | uint16_t | 源 NZ 矩阵相邻 Z 排布起始地址偏移，取值 [0, 65535]，单位 C0_Size（`16 * sizeof(T)`），应填 `mSize` 对 16 向上取整。 |
| dstStride | uint32_t | 不开启 NZ2ND 时：目的 NZ 矩阵相邻 Z 排布偏移，单位为 DataBlock（32 字节）；开启 NZ2ND 时：目的 ND 矩阵每行元素个数，单位为 element。 |
| quantPre | QuantMode_t | 量化模式，默认 `NoQuant`；float/int32 输出须为 `NoQuant`，half/bfloat16 输出须为 `F322F16`/`F322BF16`。需手动配置，不会自动推导。 |
| deqScalar | uint64_t | scalar 量化参数，随路量化时为单个 scale 值。 |
| reluEn | bool | 是否开启 NormReLU，默认 false。 |
| unitFlag | uint8_t | 与 Mmad 侧的细粒度并行开关，取值 0/2/3，须与 Mmad 保持一致。 |
| isChannelSplit | bool | 是否开启通道拆分，默认 false；仅 L0C→GM 的 NZ float 输出生效。 |
| ndNum | uint16_t | NZ2ND 场景下 L0C 上源 NZ 矩阵个数，默认 1，取值 [0, 65535]；0 表示不搬运。 |
| srcNdStride | uint16_t | 不同 NZ 矩阵起始地址间隔，取值 [0, 512]，单位数据块 `16 * C0_Size`；`ndNum = 1` 时不生效。 |
| dstNdStride | uint16_t | 目的相邻 ND 矩阵起始地址偏移，取值 [0, 65535]，单位 element；`ndNum = 1` 时不生效。 |

`FixpipeParamsArch3510`/`FixpipeParamsC310` 的字段集与 V220 不同（多 `preReluMode`/`preClipReluMode`/`reluScalar`/`vectorRelu`/`dualDstCtl`/`subBlockId`/`params`，`dstStride` 单位为 element 而非 DataBlock），文档表3单独给出。

`FixpipeParams<T>`（模板形态）的 `cburstNum`/`burstLen`/`srcStride`/`dstStride`/`quantParams`/`reluEn`/`nz2ndParams`/`unitFlag` 字段语义：unknown——Fixpipe 文档只覆盖 V220/M300/Arch3510 三种形态，未定义该模板结构体的字段语义。

同一 commit 下还存在第三个同名类型：`impl/tensor_api/legacy/legacy_utils.h:124` 的 `struct FixpipeParams { uint8_t unitFlag; bool subBlockId; };`。它属于 tensor legacy 工具层，字段只有 `unitFlag` 与 `subBlockId`，与上述四种形态都不同——"FixpipeParams"这个名字在源码里同名不同义，定位时必须先确认 include 路径。

## 约束与注意事项

- 同名成员在不同代形态下单位不同：V220 的 `dstStride` 在不开启 NZ2ND 时以 DataBlock（32B）计，Arch3510 的 `dstStride` 以 element 计。跨代迁移时按单位复核，不能只改类型名。
- `quantPre` 必须手动配置：输出 half/bfloat16 却保留 `NoQuant` 会得到未量化的结果。
- 模板成员字段写法（`FixpipeParams<T>` 上直接写 `nSize`/`mSize`）与 V220 的 `nSize`/`mSize` 并非同一结构体；在 V220 上使用模板形态的成员字段形式不可编译（见下方 runbook）。
- `isChannelSplit` 与 NZ2ND 不能同时开启（M300 表5 明确），且 channelSplit 只对 L0C→GM 的 NZ float 输出生效。

## 来源锚点

- 声明：`include/basic_api/kernel_struct_fixpipe.h:107-166`（V220）、`:190-223`（Arch3510）、`:225-236`（C310 与 M300/M310 别名）；模板形态 `impl/basic_api/utils/kernel_utils_struct_dma_params.h:100-129`。
- 字段语义：`docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_store/Fixpipe_L0CToGM.md` 表3（`:128-145`）、表4（`:145-162`）、表5（`:162-179`）、产品支持情况 `:3-33`。

## 相关 runbook

- [FixpipeParams 模板成员字段形式在 V220 上不可编译](../../../../runbooks/compilation/ec_72_fixpipeparams_float_member_field_form_fp_nsize_fp.md)
- [Fixpipe L0C→GM 的 dstStride 单位随格式不同](../../../../runbooks/compilation/ol_279_fixpipe_l0c_gm_dststride_unit_is_per_format_elemen.md)
