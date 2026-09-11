---
type: API
title: GetFmodTmpBufferFactorSize
description: 获取Fmod接口的maxLiveNodeCount和extraBuf，用于推算算子单次最大计算元素数量
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.compute.elementwise.math_function
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Fmod_interface/GetFmodTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
source_headers:
- include/adv_api/math/fmod_tiling.h
---

# GetFmodTmpBufferFactorSize

## 功能说明

该接口用于获取maxLiveNodeCount和extraBuf，在固定空间大小的情况下，通过maxLiveNodeCount和extraBuf可以推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的多少倍；extraBuf表示使用的额外临时空间大小。

推算示例如下：

-   算子实现需要调用Fmod接口，开发者为其预留currBuff大小的空间，利用GetFmodTmpBufferFactorSize接口得到maxLiveNodeCount、extraBuf输出值，可推导算子单次最大计算元素数量为：

    **currentShapeSize = \(currBuff - extraBuf\) / maxLiveNodeCount / typeSize**

-   算子实现需要调用两个kernel侧API KernelIntf1、KernelIntf2，利用两个GetXxxTmpBufferFactorSize（其中Xxx为需要调用的两个高阶API）接口的两组输出值\(maxLiveNodeCount、extraBuf\)以及当前现有的临时空间，推导单次最大计算元素数量currentShapeSize为：

    **currentShapeSize1 = \(currBuff - extraBuf1\) / maxLiveNodeCount1 / typeSize**

    **currentShapeSize2 = \(currBuff - extraBuf2\) / maxLiveNodeCount2 / typeSize**

    **currentShapeSize = min\(currentShapeSize1, currentShapeSize2\)**

注意上文中的currBuff表示接口计算可用的空间，需要去除用户输入输出等空间；另外，接口获取的maxLiveNodeCount值可能为0，计算时需要判断该值非0，避免除零错误。

## 函数原型

```
void GetFmodTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuf)
```

## 参数说明

**表1**  参数列表

| 参数名 | 输入/输出 | 功能 |
| --- | --- | --- |
| typeSize | 输入 | 输入的数据类型大小，单位为字节。比如输入的数据类型为half，此处应传入2。 |
| maxLiveNodeCount | 输出 | 最大存活节点数，表示临时空间是单次计算数据量所占空间的多少倍。 |
| extraBuf | 输出 | 使用的额外临时空间大小，单位为字节。 |

## 返回值说明

无

## 约束说明

当利用maxLiveNodeCount，extraBuf反推出的currentShapeSize \* typeSize < 256B时，currentShapeSize按照256B/typeSize的值向上取整。

## 调用示例

完整的调用样例请参考[更多样例](../more_examples.md)。

```
uint32_t maxLiveNodeCount = 0;
uint32_t extraBuf = 0;
AscendC::GetFmodTmpBufferFactorSize(typeSize, maxLiveNodeCount, extraBuf);
```


<!-- cannbot:related:start -->
## 相关

- [Fmod](fmod.md)（`related`）：“获取Fmod接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。”明确给出左端事实；“按元素计算两个浮点数相除后的余数（dst = src0 - Trunc(src0/src1) * src1），其中Trunc为向零取整操作。模板参数T支持half/float。”明确给出右端事实。factor 接口把可用临时空间换算为单次最大元素数，Fmod 计算接口再按该分块执行余数运算，二者衔接 Host 分块规划与 Kernel 调用。
<!-- cannbot:related:end -->
