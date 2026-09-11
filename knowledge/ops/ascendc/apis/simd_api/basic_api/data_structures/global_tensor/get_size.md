---
type: API
title: GetSize
description: 获取GlobalTensor的元素个数。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.development_mode.tensor_programming
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/GlobalTensor/GetSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
- '910'
---

# GetSize<a name="ZH-CN_TOPIC_0000002167649065"></a>

## 功能说明<a name="section618mcpsimp"></a>

获取GlobalTensor的元素个数。

## 函数原型<a name="section620mcpsimp"></a>

```cpp
__aicore__ inline uint64_t GetSize() const
```

## 参数说明<a name="section622mcpsimp"></a>

无。

## 返回值说明<a name="section640mcpsimp"></a>

GlobalTensor的元素个数。

## 约束说明<a name="section633mcpsimp"></a>

使用仅传入全局数据指针的[SetGlobalBuffer](set_global_buffer.md)接口对GlobalTensor进行初始化，通过本接口获取到的元素个数为0。

## 调用示例<a name="section17531157161314"></a>

```cpp
AscendC::LocalTensor<uint8_t> stackBuffer;
AscendC::PopStackBuffer<uint8_t, AscendC::TPosition::LCM>(stackBuffer);
uint32_t stackBufferSize = stackBuffer.GetSize();
```



<!-- cannbot:related:start -->
## 相关

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 1 / 1 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [QuantConvolution 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/conv/quant_convolution_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSize(...)` 的直接调用（第 240 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/conv/conv3d_v2/op_kernel/arch35/conv3d_v2_instr_dequant_impl.h#L240)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
