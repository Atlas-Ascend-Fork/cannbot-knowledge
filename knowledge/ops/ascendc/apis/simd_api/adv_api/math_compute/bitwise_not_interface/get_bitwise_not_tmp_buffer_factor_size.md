---
type: API
title: GetBitwiseNotTmpBufferFactorSize
description: 获取maxLivedNodeCount和extraBuf，在固定空间大小下推算BitwiseNot算子单次最大计算元素数量。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.compute.elementwise.math_function
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/BitwiseNot_interface/GetBitwiseNotTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
source_headers:
- include/adv_api/math/bitwise_not_tiling.h
---

# GetBitwiseNotTmpBufferFactorSize

## 功能说明

该接口用于获取maxLivedNodeCount和extraBuf，在固定空间大小的情况下，通过maxLivedNodeCount和extraBuf可以推算算子单次最大计算元素数量。maxLivedNodeCount表示临时空间是单次计算数据量所占空间的多少倍；extraBuf表示使用的额外临时空间大小。

推算示例如下：

-   算子实现需要调用BitwiseNot接口，开发者为其预留currBuff大小的空间，利用GetBitwiseNotTmpBufferFactorSize接口得到maxLivedNodeCount、extraBuf输出值，可推导算子单次最大计算元素数量为：

    **currentShapeSize = \(currBuff - extraBuf\) / maxLivedNodeCount / typeSize**

-   算子实现需要调用两个kernel侧API KernelIntf1、KernelIntf2，利用两个GetXxxTmpBufferFactorSize（其中Xxx为需要调用的两个高阶API）接口的两组输出值\(maxLivedNodeCount、extraBuf\)以及当前现有的临时空间，推导单次最大计算元素数量currentShapeSize为：

    **currentShapeSize1 = \(currBuff - extraBuf1\) / maxLivedNodeCount1 / typeSize**

    **currentShapeSize2 = \(currBuff - extraBuf2\) / maxLivedNodeCount2 / typeSize**

    **currentShapeSize = min\(currentShapeSize1, currentShapeSize2\)**

注意上文中的currBuff表示接口计算可用的空间，需要去除用户输入输出等空间；另外，接口获取的maxLivedNodeCount值可能为0，计算时需要判断该值非0，避免除零错误。

## 函数原型

```
void GetBitwiseNotTmpBufferFactorSize(const platform_ascendc::PlatformAscendC& ascendcPlatform,const uint32_t typeSize, uint32_t& maxLivedNodeCount, uint32_t& extraBuf)
```

## 参数说明

**表1**  参数列表

| 参数名 | 输入/输出 | 功能 |
| --- | --- | --- |
| ascendcPlatform | 输入 | 输入的平台信息。PlatformAscendC的定义请参见[构造及析构函数](../../../../utils_api/platform_info/platform_ascend_c/constructor_and_destructor.md)。 |
| typeSize | 输入 | 输入的数据类型大小，单位为字节。 |
| maxLivedNodeCount | 输出 | 最大存活节点数，表示临时空间是单次计算数据量所占空间的多少倍。 |
| extraBuf | 输出 | 使用的额外临时空间大小，单位为字节。 |

## 返回值说明

无

## 约束说明

当利用maxLivedNodeCount、extraBuf反推出的currentShapeSize  \* typeSize < 256B时，currentShapeSize按照256B/typeSize的值向上取整。

## 调用示例

完整的调用样例请参考[更多样例](../more_examples.md)。

```
uint32_t maxLivedNodeCount = 0;
uint32_t extraBuf = 0;
auto plat = platform_ascendc::PlatformAscendC(context->GetPlatformInfo());
AscendC::GetBitwiseNotTmpBufferFactorSize(plat, typeSize, maxLivedNodeCount, extraBuf);
```


<!-- cannbot:related:start -->
## 相关

- [BitwiseNot](bitwise_not.md)（`same_topic`）：逐比特对输入进行取反。；该接口用于获取maxLivedNodeCount和extraBuf，在固定空间大小的情况下，通过maxLivedNodeCount和extraBuf可以推算算子单次最大计算元素数量。；BitwiseNot 的 count 决定单次逐比特计算规模，factor 查询把固定临时空间转换成允许的最大元素数量，可用于设计 Kernel 分块。
- [GetBitwiseNotMaxMinTmpSize](get_bitwise_not_max_min_tmp_size.md)（`same_topic`）：“开发者基于此范围选择合适的空间大小作为Tiling参数传递到Kernel侧使用”先确定 BitwiseNot 可用的临时空间；“通过maxLivedNodeCount和extraBuf可以推算算子单次最大计算元素数量”再把选定空间换算成单次分块上限。
<!-- cannbot:related:end -->
