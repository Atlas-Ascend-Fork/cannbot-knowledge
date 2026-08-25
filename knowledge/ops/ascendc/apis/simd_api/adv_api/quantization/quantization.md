---
type: API
title: 量化操作
description: 量化操作接口导航页，涵盖AscendQuant、AscendDequant、AscendAntiQuant及Quantize系列量化与反量化接口。
tags: [task.lookup, topic.compute.quantization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/quantization/quantization.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 量化操作

-   **AscendQuant**

-   **GetAscendQuantMaxMinTmpSize**

-   **GetAscendQuantTmpBufferFactorSize**

-   **AscendDequant**

-   **GetAscendDequantMaxMinTmpSize**

-   **GetAscendDequantTmpBufferFactorSize**

-   **AscendAntiQuant**

-   **GetAscendAntiQuantMaxMinTmpSize**

-   **GetAscendAntiQuantTmpBufferFactorSize**

-   **Quantize**

-   **GetQuantizeMaxMinTmpSize**

-   **GetQuantizeTmpBufferFactorSize**

-   **Dequantize**

-   **GetDequantizeMaxMinTmpSize**

-   **GetDequantizeTmpBufferFactorSize**

-   **AntiQuantize**

-   **GetAntiQuantizeMaxMinTmpSize**

-   **GetAntiQuantizeTmpBufferFactorSize**

<!-- cannbot:related:start -->
## 相关

- [GetAscendQuantMaxMinTmpSize](get_ascend_quant_max_min_tmp_size.md)（`related`）：《GetAscendQuantMaxMinTmpSize》说明在host侧获取AscendQuant接口计算所需的最大和最小临时空间大小，用于选择合适的空间大小作为Tiling参数传递到kernel侧。；《量化操作》说明量化操作接口导航页，涵盖AscendQuant、AscendDequant、AscendAntiQuant及Quantize系列量化与反量化接口。。二者在AscendQuant的Host侧workspace上界/下界必须与该量化Kernel及factor查询匹配上存在可执行的直接衔接。
- [GetDequantizeTmpBufferFactorSize](get_dequantize_tmp_buffer_factor_size.md)（`related`）：《GetDequantizeTmpBufferFactorSize》说明获取Dequantize接口的maxLiveNodeCount和extraBuf，在固定空间大小下推算算子单次最大计算元素数量。；《量化操作》说明量化操作接口导航页，涵盖AscendQuant、AscendDequant、AscendAntiQuant及Quantize系列量化与反量化接口。。二者在Dequantize的factor和最大/最小workspace查询为同一Kernel反推单次处理规模上存在可执行的直接衔接。
<!-- cannbot:related:end -->
