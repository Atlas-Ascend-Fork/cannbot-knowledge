---
type: API
title: GetTanhMaxMinTmpSize
description: 在host侧获取Tanh接口计算所需最大和最小临时空间大小，供Tiling参数选择。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.compute.elementwise.math_function
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Tanh_interface/GetTanhMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
source_headers:
- include/adv_api/math/tanh_tiling.h
---

# GetTanhMaxMinTmpSize

## 功能说明

kernel侧Tanh接口的计算需要开发者预留/申请临时空间，本接口用于在host侧获取预留/申请的最大和最小临时空间大小，开发者基于此范围选择合适的空间大小作为Tiling参数传递到kernel侧使用。

-   为保证功能正确，预留/申请的临时空间大小不能小于最小临时空间大小；
-   在最小临时空间-最大临时空间范围内，随着临时空间增大，kernel侧接口计算性能会有一定程度的优化提升。为了达到更好的性能，开发者可以根据实际的内存使用情况进行空间预留/申请。

## 函数原型

```
void GetTanhMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)
```

## 参数说明

**表1**  接口参数列表

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| srcShape | 输入 | 输入的shape信息，参数类型为[AscendC::TensorShape](../../data_structures/tensor_shape.md)。 |
| typeSize | 输入 | 输入的数据类型大小，单位为字节。比如输入的数据类型为half，此处应传入2。 |
| isReuseSource | 输入 | 是否复用源操作数输入的空间，与Tanh接口一致。 |
| maxValue | 输出 | Tanh接口能完成计算所需的最大临时空间大小，超出该值的空间不会被该接口使用。在min-max范围内，预留/申请空间越大，接口计算性能越好。为了达到更好的性能，开发者可以根据实际的内存使用情况进行空间预留/申请。maxValue为0表示计算不需要临时空间。<br><br>请注意，maxValue仅作为参考值，有可能大于Unified Buffer（UB）剩余空间的大小，该场景下，开发者需要根据UB剩余空间的大小来选取合适的临时空间大小。 |
| minValue | 输出 | Tanh接口能完成计算所需最小临时空间大小。为保证功能正确，接口计算时预留/申请的临时空间不能小于minValue的数值。最小空间为0表示计算不需要临时空间。 |

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
AscendC::GetTanhMaxMinTmpSize(shape, 2, false, maxValue, minValue);
```


<!-- cannbot:related:start -->
## 相关

- [Tanh](tanh.md)（`related`）：Host 接口说明“host侧Tiling接口，用于获取Tanh接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。”；Tanh 卡明确“临时空间大小通过GetTanhMaxMinTmpSize获取。”，两端形成 Tanh sharedTmpBuffer 的容量选择与调用链，但 Host Tiling 规划和 Kernel 双曲正切计算是两个主题。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 3 / 3 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [LSTM A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/rnn/lstm.md)（`related`）：算子声明的固定版本源码包含对 `GetTanhMaxMinTmpSize(...)` 的直接调用（第 144 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/rnn/dynamic_rnn/op_host/dynamic_lstm_tiling.cpp#L144)
- [ThnnFusedLstmCellBackward A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/rnn/thnn_fused_lstm_cell_backward.md)（`related`）：算子声明的固定版本源码包含对 `GetTanhMaxMinTmpSize(...)` 的直接调用（第 267 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/rnn/thnn_fused_lstm_cell_grad/op_host/thnn_fused_lstm_cell_grad_tiling.cpp#L267)
- [LSTM 950 Direct Invoke 算子知识](../../../../../operators/direct/nn/rnn/lstm_950.md)（`related`）：算子声明的固定版本源码包含对 `GetTanhMaxMinTmpSize(...)` 的直接调用（第 144 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/rnn/dynamic_rnn/op_host/dynamic_lstm_tiling.cpp#L144)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
