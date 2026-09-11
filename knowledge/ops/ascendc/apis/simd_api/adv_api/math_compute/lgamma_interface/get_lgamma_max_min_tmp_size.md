---
type: API
title: GetLgammaMaxMinTmpSize
description: 在host侧获取Lgamma接口预留或申请临时空间的最大和最小值，用于Tiling参数传递
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.compute.elementwise.math_function
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Lgamma_interface/GetLgammaMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
source_headers:
- include/adv_api/math/lgamma_tiling.h
---

# GetLgammaMaxMinTmpSize

## 功能说明

kernel侧Lgamma接口的计算需要开发者预留/申请临时空间，本接口用于在host侧获取预留/申请的最大和最小临时空间大小，开发者基于此范围选择合适的空间大小作为Tiling参数传递到kernel侧使用。

-   为保证功能正确，预留/申请的临时空间大小不能小于最小临时空间大小；
-   在最小临时空间-最大临时空间范围内，随着临时空间增大，kernel侧接口计算性能会有一定程度的优化提升。为了达到更好的性能，开发者可以根据实际的内存使用情况进行空间预留/申请。

## 函数原型

```
void GetLgammaMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)
```

## 参数说明

**表1**  接口参数列表

| 参数名 | 输入/输出 | 功能 |
| --- | --- | --- |
| srcShape | 输入 | 输入的shape信息，参数类型为[AscendC::TensorShape](../../data_structures/tensor_shape.md)。 |
| typeSize | 输入 | 输入的数据类型大小，单位为字节。比如输入的数据类型为half，此处应传入2。 |
| isReuseSource | 输入 | 是否复用源操作数输入的空间，与Lgamma接口一致。 |
| maxValue | 输出 | Lgamma接口能完成计算所需的最大临时空间大小，超出该值的空间不会被该接口使用。在最小临时空间-最大临时空间范围内，随着临时空间增大，kernel侧接口计算性能会有一定程度的优化提升。为了达到更好的性能，开发者可以根据实际的内存使用情况进行空间预留/申请。最大空间大小为0表示计算不需要临时空间。<br><br>请注意，maxValue仅作为参考值，有可能大于Unified Buffer（UB）剩余空间的大小，该场景下，开发者需要根据UB剩余空间的大小来选取合适的临时空间大小。 |
| minValue | 输出 | Lgamma接口能完成计算所需最小临时空间大小。为保证功能正确，接口计算时预留/申请的临时空间不能小于该数值。最小空间大小为0表示计算不需要临时空间。 |

## 返回值说明

无

## 约束说明

无

## 调用示例

完整的调用样例请参考[更多样例](../more_examples.md)。

```
// 输入shape信息为1024;算子输入的数据类型为half;不允许修改源操作数
std::vector<int64_t> shape_vec = {1024};
AscendC::TensorShape shape(shape_vec);
uint32_t maxValue = 0;
uint32_t minValue = 0;
AscendC::GetLgammaMaxMinTmpSize(shape, 2, false, maxValue, minValue);
```


<!-- cannbot:related:start -->
## 相关

- [GetLgammaTmpBufferFactorSize](get_lgamma_tmp_buffer_factor_size.md)（`related`）：参数：typeSize为输入数据类型字节数（half传2）；maxLiveNodeCount输出最大存活节点数；extraBuffer输出额外临时空间大小。推算公式：currentShapeSize = (currBuff - extraBuffer) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。调用多个高阶API时取各接口推算结果的最小值。maxLiveNodeCount可能为0，计算时需判断避免除零错误。；host侧Tiling接口，用于获取Lgamma接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。。两接口从 shape 到空间上下界和空间到可处理 shape 两个方向闭合 Lgamma 的 Host 临时空间规划。
- [Lgamma](lgamma.md)（`related`）：提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetLgammaMaxMinTmpSize获取。；host侧Tiling接口，用于获取Lgamma接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。。Lgamma 的 sharedTmpBuffer 重载消费 Host Tiling 接口给出的容量上下界，二者构成明确的临时空间生产与消费合同。
<!-- cannbot:related:end -->
