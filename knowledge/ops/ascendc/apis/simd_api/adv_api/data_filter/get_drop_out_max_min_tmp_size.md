---
type: API
title: GetDropOutMaxMinTmpSize
description: 用于获取DropOut Tiling参数。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.data_movement.data_copy
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/data_filter/GetDropOutMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
source_headers:
- include/adv_api/filter/dropout_tiling.h
---

# GetDropOutMaxMinTmpSize

## 功能说明

用于获取DropOut Tiling参数。

## 函数原型

```
uint32_t GetDropOutMaxTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource)
```

```
uint32_t GetDropOutMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource)
```

```
void GetDropOutMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)
```

## 参数说明

**表1**  参数列表

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| srcShape | 输入 | 输入的shape信息，参数类型为[AscendC::TensorShape](../data_structures/tensor_shape.md)。 |
| typeSize | 输入 | 计算的数据类型大小，half=2，float=4。 |
| isReuseSource | 输入 | 预留参数，暂未启用，保持默认值false即可。 |
| maxValue | 输出 | 输出DropOut接口所需的tiling信息（最大临时空间大小）。<br> 说明：maxValue仅作为参考值，有可能大于UB剩余空间的大小，该场景下，开发者需要根据UB剩余空间的大小来选取合适的临时空间大小。 |
| minValue | 输出 | 输出DropOut接口所需的tiling信息（最小临时空间大小）。 |

## 返回值说明

GetDropOutMaxTmpSize返回DropOut接口能完成计算所需最大临时空间大小。

GetDropOutMinTmpSize返回DropOut接口能完成计算所需最小临时空间大小。

GetDropOutMaxMinTmpSize无返回值。

## 约束说明

无

## 调用示例

下文呈现了一个host侧调用**GetDropOutMaxMinTmpSize**接口的使用示例，通过该接口获取DropOut计算所需的最大最小临时空间大小，开发者基于此范围选择合适的空间大小作为Tiling参数传递到kernel侧使用。配套的kernel侧使用样例请参考[调用示例](drop_out.md#section642mcpsimp)。

```
#include <vector>

#include "register/op_def_registry.h"
#include "register/tilingdata_base.h"
#include "tiling/tiling_api.h"

namespace optiling {

BEGIN_TILING_DATA_DEF(DropoutCustomTilingData)
    TILING_DATA_FIELD_DEF(uint32_t, firstAxis);
    TILING_DATA_FIELD_DEF(uint32_t, srcLastAxis);
    TILING_DATA_FIELD_DEF(uint32_t, maskLastAxis);
    TILING_DATA_FIELD_DEF(uint32_t, tmpBufferSize);
END_TILING_DATA_DEF;

static ge::graphStatus TilingFunc(gert::TilingContext* context)
{
    // Input source shapes.
    int64_t firstAxis = 16;
    int64_t srcLastAxis = 64;
    int64_t maskLastAxis = 64;

    std::vector<int64_t> srcDims = {firstAxis, srcLastAxis, maskLastAxis};

    uint32_t typeSize = 2;
    AscendC::TensorShape shape(srcDims);
    uint32_t minValue = 0;
    uint32_t maxValue = 0;
    AscendC::GetDropOutMaxMinTmpSize(shape, typeSize, false, maxValue, minValue);

    auto platformInfo = context->GetPlatformInfo();
    auto ascendcPlatform = platform_ascendc::PlatformAscendC(platformInfo);
    uint64_t tailSize = 0; // ub剩余空间大小
    // 本样例中使用完整的ub空间，实际情况下tailSize需要减掉用户已使用的ub空间
    ascendcPlatform.GetCoreMemSize(
        platform_ascendc::CoreMemType::UB, tailSize); 
    auto tmpSize = tailSize >= maxValue ? maxValue : tailSize;

    DropoutCustomTilingData tiling;
    tiling.set_firstAxis(firstAxis);
    tiling.set_srcLastAxis(srcLastAxis);
    tiling.set_maskLastAxis(maskLastAxis);
    tiling.set_tmpBufferSize(tmpSize);
    context->SetSimdNumBlocks(1);
    tiling.SaveToBuffer(context->GetRawTilingData()->GetData(), context->GetRawTilingData()->GetCapacity());
    context->GetRawTilingData()->SetDataSize(tiling.GetDataSize());
    context->SetTilingKey(1);

    return ge::GRAPH_SUCCESS;
}
} // namespace optiling
```


<!-- cannbot:related:start -->
## 相关

- [DropOut](drop_out.md)（`related`）：“提供根据MaskTensor对SrcTensor（源操作数，输入Tensor）进行过滤的功能，得到DstTensor（目的操作数、输出Tensor）。仅支持输入shape为ND格式。 该过滤功能包括两种模式，字节模式和比特模式。 - 字节模式”明确给出左端事实；“用于获取DropOut Tiling参数。”明确给出右端事实。计算接口依赖 shape 和 UB 临时空间，Tiling 辅助接口返回其最大/最小临时空间，从 Host 规划直接衔接到 Kernel 调用。
<!-- cannbot:related:end -->
