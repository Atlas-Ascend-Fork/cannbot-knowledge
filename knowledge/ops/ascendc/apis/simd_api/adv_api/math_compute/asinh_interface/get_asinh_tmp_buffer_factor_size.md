---
type: API
title: GetAsinhTmpBufferFactorSize
description: 获取Asinh接口的maxLiveNodeCount和extraBuffer，用于推算固定空间下单次最大计算元素数
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.compute.elementwise.math_function
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Asinh_interface/GetAsinhTmpBufferFactorSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
source_headers:
- include/adv_api/math/asinh_tiling.h
---

# GetAsinhTmpBufferFactorSize

## 功能说明

kernel侧Asinh接口的计算需要开发者预留/申请临时空间，最大临时空间（maxTmpBuffer）和输入所占空间（inputSize \* typeSize）存在以下关系：

**maxTmpBuffer = maxLiveNodeCount \* inputSize \* typeSize + extraBuffer**

其中maxLiveNodeCount表示最大临时空间是输入所占空间的多少倍；extraBuffer表示使用的额外临时空间大小。

该接口用于获取maxLiveNodeCount和extraBuffer，在固定空间大小的情况下，通过maxLiveNodeCount和extraBuffer可以推算算子单次最大计算元素数量；另外，接口获取的maxLiveNodeCount值可能为0，计算时需要判断该值非0，避免除零错误。

示例如下：

算子实现需要调用Asinh接口，开发者为其预留currBuff大小的空间，利用GetAsinhTmpBufferFactorSize接口得到maxLiveNodeCount、extraBuffer输出值，反推Asinh算子单次最大计算元素数量为：

**currentShapeSize = \(currBuff - extraBuffer\) / maxLiveNodeCount / typeSize**

## 函数原型

```
void GetAsinhTmpBufferFactorSize(const uint32_t typeSize, uint32_t& maxLiveNodeCount, uint32_t& extraBuf)
```

## 参数说明

**表1**  参数列表

| 参数名 | 输入/输出 | 功能 |
| --- | --- | --- |
| typeSize | 输入 | 输入的数据类型大小，单位为字节。比如输入的数据类型为half，此处应传入2。 |
| maxLiveNodeCount | 输出 | 最大存活节点数，最大临时空间是输入所占空间的多少倍。 |
| extraBuf | 输出 | 使用的额外临时空间大小，单位为字节。 |

## 返回值说明

无

## 约束说明

当利用maxLiveNodeCount，extraBuf反推出的currentShapeSize  \* typeSize < 256B时，currentShapeSize按照256B/typeSize的值向上取整。

## 调用示例

```
// 获取输入类型为half的Asinh操作的maxLiveNodeCount和extraBuffer
uint32_t typeSize = sizeof(half);
uint32_t maxLiveNodeCount = 0;
uint32_t extraBuffer = 0;

AscendC::GetAsinhTmpBufferFactorSize(typeSize, maxLiveNodeCount, extraBuffer);
```


<!-- cannbot:related:start -->
## 相关

- [GetAsinhMaxMinTmpSize](get_asinh_max_min_tmp_size.md)（`related`）：本接口用于在host侧获取预留 申请的最大和最小临时空间大小，开发者基于此范围选择合适的空间大小作为Tiling参数传递到kernel侧使用；maxTmpBuffer = maxLiveNodeCount * inputSize * typeSize + extraBuffer。前者给出 Asinh 临时空间合法范围，后者给出空间与单次输入规模的换算公式，直接服务同一 Host Tiling 预算。
<!-- cannbot:related:end -->
