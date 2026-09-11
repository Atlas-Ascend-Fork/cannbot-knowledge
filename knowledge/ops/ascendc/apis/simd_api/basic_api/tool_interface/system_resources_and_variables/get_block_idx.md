---
type: API
title: GetBlockIdx
description: 获取当前逻辑AI Core的索引，用于多核逻辑控制及偏移量计算等。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/system_resources_and_variables/GetBlockIdx.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
- '910'
- kirin_x90
- kirin_9030
source_headers:
- include/basic_api/kernel_operator_sys_var_intf.h
---

# GetBlockIdx

## 功能说明

头文件路径为：`"basic_api/kernel_operator_sys_var_intf.h"`。

获取当前逻辑AI Core的索引，用于代码内部的多核逻辑控制及多核偏移量计算等。

## 函数原型

```cpp
__aicore__ inline int64_t GetBlockIdx()
```

## 参数说明

无

## 返回值说明

返回当前逻辑AI Core的索引。

- 仅启动AIC或AIV的场景，索引的范围为\[0, numBlocks\)。numBlocks由用户使用<<<\>\>\>调用时配置，可以通过[GetBlockNum](get_block_num.md)获取。
- 同时启动AIC与AIV的场景，在AIC、AIV上索引的取值范围不同，取值范围可以通过[GetTaskRatio\(\)](get_task_ratio.md) \* numBlocks计算得到，在当前支持的配置下：
    - 当AIC与AIV比例为1:2时，AIC上取值范围为\[0, numBlocks\)，AIV上取值范围为\[0, 2 \* numBlocks\)；
    - 当AIC与AIV比例为1:1时，AIC上取值范围为\[0, numBlocks\)，AIV上取值范围为\[0, numBlocks\)。

## 约束说明

无

## 调用示例

```cpp
// srcGm、dstGm为外部输入的gm空间
AscendC::GlobalTensor<float> srcGlobal;
AscendC::GlobalTensor<float> dstGlobal;
int64_t blockNum = AscendC::GetBlockNum(); // 获取当前任务配置的逻辑AI Core的数量
int64_t perBlockSize = srcDataSize / blockNum; // 每个核平分处理相同个数
int64_t blockIdx = AscendC::GetBlockIdx(); // 获取当前工作的核ID
srcGlobal.SetGlobalBuffer(reinterpret_cast<__gm__ float*>(srcGm + blockIdx * perBlockSize * sizeof(float)), perBlockSize);    // 分配每个核上的srcGlobal的内存地址
dstGlobal.SetGlobalBuffer(reinterpret_cast<__gm__ float*>(dstGm + blockIdx * perBlockSize * sizeof(float)), perBlockSize);    // 分配每个核上的dstGlobal的内存地址
```


<!-- cannbot:related:start -->
## 相关

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 484 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Im2colBackward 950 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/im2col_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `GetBlockIdx(...)` 的直接调用（第 41 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/col2im/op_kernel/arch35/col2im_simt.h#L41)
- [Cat 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/cat_950.md)（`related`）：算子声明的固定版本源码包含对 `GetBlockIdx(...)` 的直接调用（第 77 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/concat/op_kernel/arch35/one_axis_concat_all_align.h#L77)
- [Celu 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/celu_950.md)（`related`）：算子声明的固定版本源码包含对 `GetBlockIdx(...)` 的直接调用（第 65 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/celu_v2/op_kernel/arch35/celu_v2.h#L65)
- [AttentionUpdate A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/attention_update.md)（`related`）：算子声明的固定版本源码包含对 `GetBlockIdx(...)` 的直接调用（第 114 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/attention_update/op_kernel/decode_update.h#L114)
- [Rasterizer A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/rasterizer.md)（`related`）：算子声明的固定版本源码包含对 `GetBlockIdx(...)` 的直接调用（第 46 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/rasterizer/op_kernel/barycentric_from_imgcoord_kernel.h#L46)
- [ChunkCat A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/chunk_cat.md)（`related`）：算子声明的固定版本源码包含对 `GetBlockIdx(...)` 的直接调用（第 67 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/chunk_cat/op_kernel/chunk_cat_common.h#L67)
- [ClippedSwiglu A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/clipped_swiglu.md)（`related`）：算子声明的固定版本源码包含对 `GetBlockIdx(...)` 的直接调用（第 63 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/clipped_swiglu/op_kernel/clipped_swiglu.hpp#L63)
- [AttentionUpdate 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/attention_update_950.md)（`related`）：算子声明的固定版本源码包含对 `GetBlockIdx(...)` 的直接调用（第 75 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/attention_update/op_kernel/arch35/attention_update_with_lse_regbase.h#L75)
- [Resize 950 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/resize_950.md)（`related`）：算子声明的固定版本源码包含对 `GetBlockIdx(...)` 的直接调用（第 99 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/resize_bilinear_v2/op_kernel/arch35/resize_bilinear_v2_all_copy.h#L99)
- [ChunkCat 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/chunk_cat_950.md)（`related`）：算子声明的固定版本源码包含对 `GetBlockIdx(...)` 的直接调用（第 67 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/chunk_cat/op_kernel/chunk_cat_common.h#L67)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
