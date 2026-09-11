---
type: API
title: GetSumMaxMinTmpSize
description: 在host侧获取Sum接口所需的最大和最小临时空间大小，当前最大值等于最小值，供开发者选择Tiling参数。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.compute.reduction
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/reduction_operations/Sum_interface/GetSumMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
source_headers:
- include/adv_api/reduce/sum_tiling.h
---

# GetSumMaxMinTmpSize

## 功能说明

kernel侧Sum接口的计算需要开发者预留/申请临时空间，本接口用于在host侧获取预留/申请的最大最小临时空间大小，开发者基于此范围选择合适的空间大小作为Tiling参数传递到kernel侧使用。

-   为保证功能正确，预留/申请的临时空间大小不能小于最小临时空间大小。
-   在最小临时空间-最大临时空间范围内，随着临时空间增大，kernel侧接口计算性能会有一定程度的优化提升。为了达到更好的性能，开发者可以根据实际的内存使用情况进行空间预留/申请。该接口**最大临时空间当前等于最小临时空间**。

## 函数原型

```
inline void GetSumMaxMinTmpSize(const uint32_t n, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxSize, uint32_t& minSize)
```

## 参数说明

**表1**  接口参数列表

| 参数名 | 输入/输出 | 功能 |
| --- | --- | --- |
| n | 输入 | 输入数据每行的实际计算个数。 |
| typeSize | 输入 | 输入的数据类型大小，单位为字节。比如输入的数据类型为half，此处应传入2。 |
| isReuseSource | 输入 | 是否复用源操作数输入的空间，与Sum接口一致，此处预留。 |
| maxValue | 输出 | Sum接口能完成计算所需的最大临时空间大小，超出该值的空间不会被该接口使用。<br> 说明： <br>maxValue仅作为参考值，有可能大于UB剩余空间的大小，该场景下，开发者需要根据UB剩余空间的大小来选取合适的临时空间大小。 |
| minValue | 输出 | Sum接口能完成计算所需最小临时空间大小。为保证功能正确，接口计算时预留/申请的临时空间不能小于该数值。 |

## 返回值说明

无

## 约束说明

无

## 调用示例

```
// 输入shape为2*3的矩阵，则n = 3;算子输入的数据类型为half;isReuseSource传入默认值false
uint32_t n = 3;
uint32_t maxValue = 0;
uint32_t minValue = 0;
AscendC::GetSumMaxMinTmpSize(n, 2, false, maxValue, minValue);
```


<!-- cannbot:related:start -->
## 相关

- [Sum](sum.md)（`related`）：提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetSumMaxMinTmpSize获取。模板参数isReuseSource预留（传false）；isBasicBlock在满足基本块要求时可提升性能；reduceDim指定reduce维度（默认-1为最后一轴）。；host侧Tiling接口，用于获取Sum接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。。Sum 本体明确临时空间通过 GetSumMaxMinTmpSize 获取，目标 API 给出 host 侧最大/最小预算，形成直接调用合同。
<!-- cannbot:related:end -->
