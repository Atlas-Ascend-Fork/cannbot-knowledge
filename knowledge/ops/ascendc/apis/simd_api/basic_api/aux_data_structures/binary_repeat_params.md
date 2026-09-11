---
type: API
title: BinaryRepeatParams
description: BinaryRepeatParams为用于控制操作数地址步长的数据结构。结构体内包含操作数相邻迭代间相同DataBlock的地址步长，操作数同一迭代内不同DataBlock的地址步长等参数。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.development_mode.tensor_programming
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/BinaryRepeatParams.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
source_headers:
- include/basic_api/kernel_struct_binary.h
---

# BinaryRepeatParams<a name="ZH-CN_TOPIC_0000001533390357"></a>

BinaryRepeatParams为用于控制操作数地址步长的数据结构。结构体内包含操作数相邻迭代间相同DataBlock的地址步长，操作数同一迭代内不同DataBlock的地址步长等参数。

相邻迭代间的地址步长参数说明请参考[repeatStride](../memory_vector_compute/simd_compute/high_dim_split.md#地址间隔配置)；同一迭代内DataBlock的地址步长参数说明请参考[dataBlockStride](../memory_vector_compute/simd_compute/high_dim_split.md#地址间隔配置)。

结构体具体定义为：

```cpp
const int32_t DEFAULT_BLK_NUM = 8;
const int32_t DEFAULT_BLK_STRIDE = 1;
const uint8_t DEFAULT_REPEAT_STRIDE = 8;

struct BinaryRepeatParams {
    __aicore__ BinaryRepeatParams() {}
    __aicore__ BinaryRepeatParams(const uint8_t dstBlkStrideIn, const uint8_t src0BlkStrideIn,
        const uint8_t src1BlkStrideIn, const uint8_t dstRepStrideIn, const uint8_t src0RepStrideIn,
        const uint8_t src1RepStrideIn)
        : dstBlkStride(dstBlkStrideIn),
          src0BlkStride(src0BlkStrideIn),
          src1BlkStride(src1BlkStrideIn),
          dstRepStride(dstRepStrideIn),
          src0RepStride(src0RepStrideIn),
          src1RepStride(src1RepStrideIn)
    {}
    uint32_t blockNumber = DEFAULT_BLK_NUM;
    uint8_t dstBlkStride = DEFAULT_BLK_STRIDE;
    uint8_t src0BlkStride = DEFAULT_BLK_STRIDE;
    uint8_t src1BlkStride = DEFAULT_BLK_STRIDE;
    uint8_t dstRepStride = DEFAULT_REPEAT_STRIDE;
    uint8_t src0RepStride = DEFAULT_REPEAT_STRIDE;
    uint8_t src1RepStride = DEFAULT_REPEAT_STRIDE;
    bool repeatStrideMode = false;
    bool strideSizeMode = false;
};
```

其中，blockNumber，repeatStrideMode和strideSizeMode为保留参数，用户无需关心，使用默认值即可。用户需要自行定义DataBlock Stride参数，包含dstBlkStride，src0BlkStride和src1BlkStride，以及Repeat Stride参数，包含dstRepStride，src0RepStride和src1RepStride。


<!-- cannbot:related:start -->
## 相关

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 1 / 1 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [BlockSparseAttention A2/A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/block_sparse_attention.md)（`related`）：算子声明的固定版本源码包含对 `BinaryRepeatParams(...)` 的直接调用（第 272 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/block_sparse_attention/op_kernel/attn_infra/epilogue/block/bsa_block_epilogue_online_softmax.hpp#L272)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
