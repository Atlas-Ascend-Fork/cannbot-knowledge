---
type: API
title: GetSigmoidMaxMinTmpSize
description: 用于在host侧获取Sigmoid接口所需的最大最小临时空间大小，作为Tiling参数传递到kernel侧使用。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.compute.elementwise.activation
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/Sigmoid_interface/GetSigmoidMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
source_headers:
- include/adv_api/activation/sigmoid_tiling.h
---

# GetSigmoidMaxMinTmpSize

## 功能说明

kernel侧Sigmoid接口的计算需要开发者预留/申请临时空间，本接口用于在host侧获取预留/申请的最大最小临时空间大小，开发者基于此范围选择合适的空间大小作为Tiling参数传递到kernel侧使用。

-   为保证功能正确，预留/申请的临时空间大小不能小于最小临时空间大小；
-   在最小临时空间-最大临时空间范围内，随着临时空间增大，kernel侧接口计算性能会有一定程度的优化提升。为了达到更好的性能，开发者可以根据实际的内存使用情况进行空间预留/申请。

## 函数原型

```
void GetSigmoidMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)
```

## 参数说明

**表1**  接口参数列表

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| srcShape | 输入 | 输入的shape信息，参数类型为[AscendC::TensorShape](../../data_structures/tensor_shape.md)。 |
| typeSize | 输入 | 输入的数据类型大小，单位为字节。比如输入的数据类型为half，此处应传入2。 |
| isReuseSource | 输入 | 是否复用源操作数输入的空间，与Sigmoid接口一致。 |
| maxValue | 输出 | Sigmoid接口能完成计算所需的最大临时空间大小，超出该值的空间不会被该接口使用。在最小临时空间-最大临时空间范围内，随着临时空间增大，kernel侧接口计算性能会有一定程度的优化提升。为了达到更好的性能，开发者可以根据实际的内存使用情况进行空间预留/申请。最大空间大小为0表示计算不需要临时空间。<br>maxValue仅作为参考值，有可能大于Unified Buffer（UB）剩余空间的大小，该场景下，开发者需要根据UB剩余空间的大小来选取合适的临时空间大小。 |
| minValue | 输出 | Sigmoid接口能完成计算所需最小临时空间大小。为保证功能正确，接口计算时预留/申请的临时空间不能小于该数值。最小空间大小为0表示计算不需要临时空间。 |

## 返回值说明

无

## 约束说明

无

## 调用示例

完整的调用样例请参考[更多样例](../../math_compute/more_examples.md)。

```
// 输入shape信息为1024;算子输入的数据类型为half;不允许修改源操作数
std::vector<int64_t> shape_vec = {1024};
AscendC::TensorShape shape(shape_vec);
uint32_t maxValue = 0;
uint32_t minValue = 0;
AscendC::GetSigmoidMaxMinTmpSize(shape, 2, false, maxValue, minValue);
```


<!-- cannbot:related:start -->
## 相关

- [Sigmoid](sigmoid.md)（`related`）：sharedTmpBuffer（输入）：临时缓存。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 用于Sigmoid内部复杂计算时存储中间变量，由开发者提供。 临时空间大小BufferSize的获取方式请参考GetSigmoidMaxMinTmpSize。；kernel侧Sigmoid接口的计算需要开发者预留 申请临时空间，本接口用于在host侧获取预留 申请的最大最小临时空间大小，开发者基于此范围选择合适的空间大小作为Tiling参数传递到kernel侧使用。；Host 侧容量查询直接为 Kernel 侧 Sigmoid 的 sharedTmpBuffer 选取合法大小，构成同一次调用的 Tiling 与执行链。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 2 / 2 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [LSTM A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/rnn/lstm.md)（`related`）：算子声明的固定版本源码包含对 `GetSigmoidMaxMinTmpSize(...)` 的直接调用（第 143 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/rnn/dynamic_rnn/op_host/dynamic_lstm_tiling.cpp#L143)
- [LSTM 950 Direct Invoke 算子知识](../../../../../operators/direct/nn/rnn/lstm_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSigmoidMaxMinTmpSize(...)` 的直接调用（第 143 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/rnn/dynamic_rnn/op_host/dynamic_lstm_tiling.cpp#L143)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
