---
type: API
title: LoadData3DParamsV2Pro
description: LoadData3DParamsV2Pro 是 LoadData 卷积搬运 v2 Pro 的参数结构体，用 extConfig/filterConfig
  两个位打包参数表达窗口起点、扩展量、filter 尺寸、步长与膨胀。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.compute.neighborhood.convolution
status: draft
sources:
- resource: https://gitcode.com/cann/asc-devkit/blob/016ba4a159eda090c4d60a1cdcd1ccca2a36cb0a/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/LoadData_3D.md
  role: primary
- resource: https://gitcode.com/cann/asc-devkit/blob/016ba4a159eda090c4d60a1cdcd1ccca2a36cb0a/include/basic_api/kernel_struct_mm.h
  role: header
created_at: '2026-10-29T07:13:46Z'
updated_at: "2026-10-31T09:21:53Z"
platforms:
- '950'
- a2
- a3
- 310p
- 310b
- kirin_x90
source_headers:
- include/basic_api/kernel_struct_mm.h
---

# LoadData3DParamsV2Pro

LoadData3DParamsV2Pro 是 `LoadData`（卷积数据搬运）v2 Pro 接口的参数结构体，用于把 L1 上 NC1HWC0 布局的 feature map 与 filter 按滑动窗展开（img2col）搬入 L0A/L0B。它把窗口尺寸、步长、膨胀、起始点、扩展量打包成两个 `uint64_t` 组合参数（`extConfig`、`filterConfig`），而不是逐项字段。

头文件：`include/basic_api/kernel_struct_mm.h`。结构体声明位于 `:356-388`（固定 commit `016ba4a159eda090c4d60a1cdcd1ccca2a36cb0a`）。

## 结构体定义

```cpp
struct LoadData3DParamsV2Pro {
    __aicore__ LoadData3DParamsV2Pro()
    {
#if defined(__NPU_ARCH__) && ((__NPU_ARCH__ == 3003) || (__NPU_ARCH__ == 3113))
        enDualSrc = BM_DISABLE;
#endif
    }

    __aicore__ LoadData3DParamsV2Pro(
        const uint16_t channelSizeIn, const bool enTransposeIn, const bool enSmallKIn, const bool filterSizeWIn,
        const bool filterSizeHIn, const bool fMatrixCtrlIn, const uint64_t extConfigIn, const uint64_t filterConfigIn)
        : channelSize(channelSizeIn),
          enTranspose(enTransposeIn),
          enSmallK(enSmallKIn),
          filterSizeW(filterSizeWIn),
          filterSizeH(filterSizeHIn),
          fMatrixCtrl(fMatrixCtrlIn),
          extConfig(extConfigIn),
          filterConfig(filterConfigIn)
    {}

    uint16_t channelSize = 0;
    bool enTranspose = false;
    bool enSmallK = false;
    bool filterSizeW = false;
    bool filterSizeH = false;
    bool fMatrixCtrl = false;
    uint64_t extConfig = 0;
    uint64_t filterConfig = 0X10101010101;
#if defined(__NPU_ARCH__) && ((__NPU_ARCH__ == 3003) || (__NPU_ARCH__ == 3113))
    bm_t enDualSrc = BM_DISABLE;
#endif
};
```

同文件的 LoadData3DParamsV1（`:230` 附近起）与 LoadData3DParamsV2（`:254` 起）是另外两个类型，字段形态不同，不要与 v2 Pro 混用。

## 字段说明

| 字段 | 类型 | 语义 |
| --- | --- | --- |
| channelSize | uint16_t | 源操作数通道数，取值 [0, 65535]；half 时除以 16 的余数须为 0、4 或 8，int8_t/uint8_t 时除以 32 的余数须为 0、4、8 或 16，int4b_t 时为 8、16、32 或 N\*64 系列值。 |
| enTranspose | bool | 是否对整个目标矩阵转置，默认 false；仅在目的 TPosition 为 A2 且源操作数为 half 时有效。 |
| enSmallK | bool | 是否开启 small K 特性（每个分形 16\*4），默认 false；文档标注当前产品形态下该特性已不再支持。 |
| filterSizeW | bool | 是否在 `filterW` 基础上把卷积核 width 增加 256 个元素，默认 false。 |
| filterSizeH | bool | 是否在 `filterH` 基础上把卷积核 height 增加 256 个元素，默认 false。 |
| fMatrixCtrl | bool | 与 `SetFmatrix` 配合，指定 v2 指令从左矩阵还是右矩阵获取 FeatureMap 属性描述；当前只支持 false（从左矩阵）。 |
| extConfig | uint64_t | 组合参数：`(mStartPt << 48) \| (kStartPt << 32) \| (mExtension << 16) \| kExtension`，默认 0。 |
| filterConfig | uint64_t | 组合参数：`(dilationFilterH << 40) \| (dilationFilterW << 32) \| (filterH << 24) \| (filterW << 16) \| (strideH << 8) \| strideW`，默认 `0X10101010101`。 |
| enDualSrc | bm_t | 仅在 `__NPU_ARCH__` 为 3003 或 3113 时存在（默认 `BM_DISABLE`）；语义：unknown（文档表5未列出）。 |

## 约束与注意事项

- `extConfig`/`filterConfig` 是位打包参数，必须整体赋值；按字段名逐项赋值的写法在该结构体上不存在。
- `enSmallK` 虽仍在结构体中，文档明确"当前产品形态已不再支持"，不要据此设计新实现。
- `fMatrixCtrl` 当前只支持 false，true 分支在文档中不构成可用配置。
- `filterConfig` 默认值 `0X10101010101` 对应各维度取 1（filter 1x1、stride 1、dilation 1）。
- v2/v2 Pro 与 v1 的产品支持范围不同（v1 仅 310P AI Core 与 Atlas 训练系列）。

## 来源锚点

- 声明：`include/basic_api/kernel_struct_mm.h:356-388`。
- 字段语义：`docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/LoadData_3D.md` 表5（`:175-187`）、v1/v2 分节产品支持情况 `:3-66`。

## 相关 runbook

- [DAV M200 上 Cube 仅可经 raw Mmad 使用](../../../../runbooks/compilation/dav_m200_cube_available_via_raw_mmad.md)
- [Cube 操作数 GM 中继打包粒度](../../../../runbooks/performance/cube_operand_gm_relay_packing_granularity.md)
