---
type: API
title: CreateVecIndex
description: 创建指定起始值的向量索引接口，支持前n个数据计算和高维切分计算两种方式。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.execution_unit.vector
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_padding/CreateVecIndex.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
source_headers:
- include/basic_api/kernel_operator_vec_createvecindex_intf.h
---

# CreateVecIndex<a name="ZH-CN_TOPIC_0000002573904793"></a>

## 功能说明<a name="section618mcpsimp"></a>

头文件路径为：`"basic_api/kernel_operator_vec_createvecindex_intf.h"`。

CreateVecIndex接口创建指定起始值的向量索引。

接口支持使用前n个数据计算和高维切分计算的方式，前n个数据计算原理和参考伪代码如下：

```python
import numpy as np

def CreateVecIndex(dst, firstValue, count):
    dst = np.arange(firstValue, firstValue + count, dtype=np.float16)
```

## 函数原型<a name="section620mcpsimp"></a>

- tensor前n个数据计算

    ```cpp
    template <typename T>
    __aicore__ inline void CreateVecIndex(LocalTensor<T> dst, const T &firstValue, uint32_t count)
    ```

- tensor高维切分计算
    - mask逐bit模式

        ```cpp
        template <typename T>
        __aicore__ inline void CreateVecIndex(LocalTensor<T> &dst, const T &firstValue, uint64_t mask[], uint8_t repeatTime, uint16_t dstBlkStride, uint8_t dstRepStride)
        ```

    - mask连续模式

        ```cpp
        template <typename T>
        __aicore__ inline void CreateVecIndex(LocalTensor<T> &dst, const T &firstValue, uint64_t mask, uint8_t repeatTime, uint16_t dstBlkStride, uint8_t dstRepStride)
        ```

## 参数说明<a name="section622mcpsimp"></a>

**表1**  模板参数说明

| 参数名称 | 描述 |
| ------ | ------ |
| T | 操作数数据类型。 |

**表2**  接口参数说明
| 参数说明 | 输入/输出 | 含义 |
| ------ | ------ | ------ |
| dst | 输出 | 目的操作数，类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。LocalTensor的起始地址需要按照32字节对齐。|
| firstValue | 输入 | 索引的第一个数值，数据类型需与dst中元素的数据类型保持一致。|
| count | 输入 | 参与计算的元素个数。关于该参数的具体说明请参考[连续计算](../simd_compute/continuous_compute.md)。|
| mask/mask[] | 输入 | mask用于控制每次迭代内参与计算的元素。<br>设置详见[掩码操作](../mask_operations/index.md)。 |
| repeatTime | 输入 | 指令迭代次数，每次迭代完成8个DataBlock的数据收集，取值范围：repeatTime∈[0,255]。|
| dstBlkStride | 输入 | 单次迭代内，矢量目的操作数不同DataBlock间地址步长，单位为DataBlock。 |
| dstRepStride | 输入 | 相邻迭代间，矢量目的操作数相同DataBlock地址步长，单位为DataBlock。 |

## 数据类型


- 针对Ascend 950PR/Ascend 950DT，T支持的数据类型为：int8_t、int16_t、half、int32_t、float、int64_t。其中，int8_t/int64_t数据类型仅支持tensor前n个数据计算接口。


- 针对Atlas A3 训练系列产品/Atlas A3 推理系列产品，T支持的数据类型为：int16_t、half、int32_t、float。


- 针对Atlas A2 训练系列产品/Atlas A2 推理系列产品，T支持的数据类型为：int16_t、half、int32_t、float。


- 针对Atlas 200I/500 A2 推理产品，T支持的数据类型为：int16_t、half、int32_t、float。


- 针对Atlas 推理系列产品 AI Core，T支持的数据类型为：int16_t、half、int32_t、float。


## 返回值说明<a name="section640mcpsimp"></a>

无

## 约束说明<a name="section633mcpsimp"></a>

- 操作数地址对齐要求请参见[通用地址对齐约束](../../../general_description_and_constraints.md#section796754519912)。
- firstValue需保证不超出dst中元素数据类型对应的大小范围。

- 当参数count或repeatTime取值为0时，该接口的行为如下：
  
  - 针对如下型号，该接口不会执行计算操作，不会对目的操作数进行写入，该接口将被视为NOP（空操作）。
    
    - Atlas A3 训练系列产品/Atlas A3 推理系列产品
    
    
    - Atlas A2 训练系列产品/Atlas A2 推理系列产品
    
  
  
  - 针对Ascend 950PR/Ascend 950DT，该接口通过VF调用[Reg矢量计算API](../../reg_vector_compute/index.md)实现兼容，当参数count或repeatTime取值为0时，不保证该接口将被视为NOP（空操作）。
  


## 调用示例<a name="section642mcpsimp"></a>

本调用示例中只展示完整样例中的接口部分代码。如果您需要运行示例代码，请直接参考完整样例[CreateVecIndex样例](https://gitcode.com/cann/asc-devkit/tree/885973fe9fd42a600e3551af9bc11a279e6f183b/examples/01_simd_cpp_api/03_basic_api/01_memory_vector_compute/create_vec_index)进行编译执行。

- tensor高维切分计算样例-mask连续模式

    ```cpp
    // repeatTime = 1, mask = 128, 128 elements one repeat, 128 elements total
    // firstValue数据类型为int16_t，dstLocal数据类型为int16_t
    // dstBlkStride = 1,单次迭代内数据连续写入
    // dstRepStride = 8,相邻迭代内数据连续写入
    AscendC::CreateVecIndex(dstLocal, (int16_t)0, mask, repeatTime, dstBlkStride, dstRepStride);
    ```

- tensor高维切分计算样例-mask逐bit模式

    ```cpp
    uint64_t mask[2] = { UINT64_MAX, UINT64_MAX };
    // repeatTime = 1, 128 elements one repeat, 128 elements total
    // firstValue数据类型为int16_t，dstLocal数据类型为int16_t
    // dstBlkStride = 1,单次迭代内数据连续写入
    // dstRepStride = 8,相邻迭代内数据连续写入
    AscendC::CreateVecIndex(dstLocal, (int16_t)0, mask, repeatTime, dstBlkStride, dstRepStride);
    ```

- tensor前n个数据计算样例

    ```cpp
    uint32_t count = 128;    // 参与计算的元素个数
    AscendC::CreateVecIndex(dstLocal, (int16_t)0, count);
    ```

结果示例如下：

```plain
输入数据（firstValue）：0
输出数据（dstLocal）：[0 1 2 ... 127]
```


<!-- cannbot:related:start -->
## 相关

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 19 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Cumsum 950 ACLNN 算子知识](../../../../../operators/aclnn/math/math/cumsum_950.md)（`related`）：算子声明的固定版本源码包含对 `CreateVecIndex(...)` 的直接调用（第 532 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/cumsum/op_kernel/arch35/cumsum_base/cumsum_core_sklansky.h#L532)
- [ExpandIntoJaggedPermute A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/index/expand_into_jagged_permute.md)（`related`）：算子声明的固定版本源码包含对 `CreateVecIndex(...)` 的直接调用（第 134 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/index/expand_into_jagged_permute/op_kernel/expand_into_jagged_permute.h#L134)
- [BlockSparseAttention A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/block_sparse_attention.md)（`related`）：算子声明的固定版本源码包含对 `CreateVecIndex(...)` 的直接调用（第 158 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/block_sparse_attention/op_kernel/block_sparse_attention_kernel_regular_arch22.h#L158)
- [GroupedBiasAddGrad A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/math/math/grouped_bias_add_grad.md)（`related`）：算子声明的固定版本源码包含对 `CreateVecIndex(...)` 的直接调用（第 126 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/grouped_bias_add_grad/op_kernel/arch32/grouped_bias_add_grad_unequal_c_perf.h#L126)
- [ScatterNd A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/index/scatter_nd.md)（`related`）：算子声明的固定版本源码包含对 `CreateVecIndex(...)` 的直接调用（第 105 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/index/scatter_nd_update/op_kernel/arch32/scatter_nd_update_common.h#L105)
- [BlockSparseAttention 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/block_sparse_attention_950.md)（`related`）：算子声明的固定版本源码包含对 `CreateVecIndex(...)` 的直接调用（第 103 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/block_sparse_attention/op_kernel/attn_infra/epilogue/block/block_epilogue_mask2idx_arch35.hpp#L103)
- [ScatterNdUpdate A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/index/scatter_nd_update.md)（`related`）：算子声明的固定版本源码包含对 `CreateVecIndex(...)` 的直接调用（第 105 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/index/scatter_nd_update/op_kernel/arch32/scatter_nd_update_common.h#L105)
- [QuantLightningIndexer 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/quant_lightning_indexer_950.md)（`related`）：算子声明的固定版本源码包含对 `CreateVecIndex(...)` 的直接调用（第 537 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/quant_lightning_indexer/op_kernel/arch35/quant_lightning_indexer_service_vector.h#L537)
- [FusedLinearOnlineMaxSum A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/matmul/fused_linear_online_max_sum.md)（`related`）：算子声明的固定版本源码包含对 `CreateVecIndex(...)` 的直接调用（第 911 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/matmul/fused_linear_online_max_sum/op_kernel/fused_linear_online_max_sum.h#L911)
- [MoeDistributeCombine A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/moe_distribute_combine.md)（`related`）：算子声明的固定版本源码包含对 `CreateVecIndex(...)` 的直接调用（第 355 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/moe_distribute_combine_v2/op_kernel/moe_distribute_combine_v2.h#L355)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
