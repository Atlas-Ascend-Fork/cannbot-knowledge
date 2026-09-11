---
type: API
title: GetClampMaxMinTmpSize
description: 在host侧获取ClampMax/ClampMin/Clamp接口所需的最大和最小临时空间大小，供开发者选择合适的Tiling参数传入kernel侧。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.compute.elementwise.math_function
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Clamp_interface/GetClampMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
source_headers:
- include/adv_api/math/clamp_tiling.h
---

# GetClampMaxMinTmpSize

## 功能说明

kernel侧ClampMax/ClampMin/Clamp接口的计算需要开发者预留/申请临时空间，本接口用于在host侧获取预留/申请的最大和最小临时空间大小，开发者基于此范围选择合适的空间大小作为Tiling参数传递到kernel侧使用。

-   为保证功能正确，预留/申请的临时空间大小不能小于最小临时空间大小；
-   在最小临时空间-最大临时空间范围内，随着临时空间增大，kernel侧接口计算性能会有一定程度的优化提升。为了达到更好的性能，开发者可以根据实际的内存使用情况进行空间预留/申请。

## 函数原型

```
void GetClampMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)
```

## 参数说明

**表1**  参数列表

| 参数名 | 输入/输出 | 功能 |
| --- | --- | --- |
| srcShape | 输入 | 输入的shape信息，参数类型为[AscendC::TensorShape](../../data_structures/tensor_shape.md)。 |
| typeSize | 输入 | 输入的数据类型大小，单位为字节。比如输入的数据类型为half，此处应传入2。 |
| isReuseSource | 输入 | 是否复用源操作数输入的空间，与ClampMax/ClampMin接口一致。 |
| maxValue | 输出 | ClampMax/ClampMin/Clamp接口能完成计算所需的最大临时空间大小，超出该值的空间不会被该接口使用。在最小临时空间-最大临时空间范围内，随着临时空间增大，kernel侧接口计算性能会有一定程度的优化提升。为了达到更好的性能，开发者可以根据实际的内存使用情况进行空间预留/申请。最大空间大小为0表示计算不需要临时空间。<br><br>请注意，maxValue仅作为参考值，有可能大于Unified Buffer（UB）剩余空间的大小，该场景下，开发者需要根据UB剩余空间的大小来选取合适的临时空间大小。 |
| minValue | 输出 | ClampMax/ClampMin/Clamp接口能完成计算所需最小临时空间大小。为保证功能正确，接口计算时预留/申请的临时空间不能小于该数值。最小空间大小为0表示计算不需要临时空间。 |

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
AscendC::GetClampMaxMinTmpSize(shape, 2, false, maxValue, minValue);
```


<!-- cannbot:related:start -->
## 相关

- [ClampMax](clamp_max.md)（`related`）：临时空间大小BufferSize的获取方式请参考GetClampMaxMinTmpSize。；host侧Tiling接口，用于获取ClampMax/ClampMin/Clamp接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。。ClampMax 的执行需要右侧公共 Clamp 家族接口给出的临时空间范围，但该 Host 接口同时服务 ClampMin 与 Clamp，因此是直接依赖而不是仅属于 ClampMax 的单一合同。
- [ClampMin](clamp_min.md)（`related`）：提供两种重载：通过sharedTmpBuffer入参传入临时空间（开发者自行管理，可复用，内存利用率高），或由接口框架申请临时空间（需预留空间，大小通过GetClampMaxMinTmpSize获取）。；host侧Tiling接口，用于获取ClampMax/ClampMin/Clamp接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。。ClampMin 的框架申请重载明确使用右侧公共接口确定预留大小，但右侧还覆盖另外两个 Clamp 操作，所以保持相关关系。
- [Clamp（数学计算）](clamp.md)（`related`）：“host侧Tiling接口，用于获取ClampMax/ClampMin/Clamp接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。”；“将输入中除nan值以外大于max的数替换为max，小于min的数替换为min，小于等于max和大于等于min的数保持不变，作为输出。当min大于max时，将除nan值外所有值替换为max。min和max可以为标量或LocalTensor。”。焦点 Host 接口为 Clamp kernel 计算临时空间上下界，连接 kernel 语义与 workspace 选择。
- [GetClampTmpBufferFactorSize](get_clamp_tmp_buffer_factor_size.md)（`related`）：“host侧Tiling接口，用于获取ClampMax/ClampMin/Clamp接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。”；“推算公式：currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。”。焦点接口从 shape 求可用空间范围，factor 接口反向从固定缓冲求单次处理元素数，二者共同完成 Clamp workspace 与 tile 大小设计。
<!-- cannbot:related:end -->
