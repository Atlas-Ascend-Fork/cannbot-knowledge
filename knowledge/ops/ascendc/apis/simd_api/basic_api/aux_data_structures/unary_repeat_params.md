---
type: API
title: UnaryRepeatParams
description: UnaryRepeatParams为用于控制操作数地址步长的数据结构。结构体内包含操作数相邻迭代间相同DataBlock的地址步长，操作数同一迭代内不同DataBlock的地址步长等参数。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.development_mode.tensor_programming
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/UnaryRepeatParams.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
source_headers:
- include/basic_api/kernel_struct_unary.h
---

# UnaryRepeatParams<a name="ZH-CN_TOPIC_0000001487959374"></a>

UnaryRepeatParams为用于控制操作数地址步长的数据结构。结构体内包含操作数相邻迭代间相同DataBlock的地址步长，操作数同一迭代内不同DataBlock的地址步长等参数。

相邻迭代间的地址步长参数说明请参考[repeatStride](../memory_vector_compute/simd_compute/high_dim_split.md#地址间隔配置)；同一迭代内DataBlock的地址步长参数说明请参考[dataBlockStride](../memory_vector_compute/simd_compute/high_dim_split.md#地址间隔配置)。

结构体具体定义为：

```cpp
const int32_t DEFAULT_BLK_NUM = 8;
const int32_t DEFAULT_BLK_STRIDE = 1;
const uint8_t DEFAULT_REPEAT_STRIDE = 8;

struct UnaryRepeatParams {
    __aicore__ UnaryRepeatParams() {}
    __aicore__ UnaryRepeatParams(const uint16_t dstBlkStrideIn, const uint16_t srcBlkStrideIn,
        const uint8_t dstRepStrideIn, const uint8_t srcRepStrideIn)
        : dstBlkStride(dstBlkStrideIn),
          srcBlkStride(srcBlkStrideIn),
          dstRepStride(dstRepStrideIn),
          srcRepStride(srcRepStrideIn)
    {}
    __aicore__ UnaryRepeatParams(const uint16_t dstBlkStrideIn, const uint16_t srcBlkStrideIn,
        const uint8_t dstRepStrideIn, const uint8_t srcRepStrideIn, const bool halfBlockIn)
        : dstBlkStride(dstBlkStrideIn),
          srcBlkStride(srcBlkStrideIn),
          dstRepStride(dstRepStrideIn),
          srcRepStride(srcRepStrideIn),
          halfBlock(halfBlockIn)
    {}
    uint32_t blockNumber = DEFAULT_BLK_NUM;
    uint16_t dstBlkStride = DEFAULT_BLK_STRIDE;
    uint16_t srcBlkStride = DEFAULT_BLK_STRIDE;
    uint8_t dstRepStride = DEFAULT_REPEAT_STRIDE;
    uint8_t srcRepStride = DEFAULT_REPEAT_STRIDE;
    bool repeatStrideMode = false;
    bool strideSizeMode = false;
    bool halfBlock = false;
};
```

其中，blockNumber，repeatStrideMode，strideSizeMode为保留参数，用户无需关心，使用默认值即可。halfBlock表示CastDequant指令的结果写入对应Unified Buffer（UB）的上半（halfBlock = true）还是下半（halfBlock = false）部分。用户需要自行定义DataBlock Stride参数，包含dstBlkStride，srcBlkStride，以及Repeat Stride参数，包含dstRepStride，srcRepStride。


<!-- cannbot:related:start -->
## 相关

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 1 / 1 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [BlockSparseAttention A2/A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/block_sparse_attention.md)（`related`）：算子声明的固定版本源码包含对 `UnaryRepeatParams(...)` 的直接调用（第 544 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/block_sparse_attention/op_kernel/attn_infra/epilogue/block/bsa_block_epilogue_online_softmax.hpp#L544)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
