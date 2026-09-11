---
type: API
title: GetBlockNum
description: 获取当前任务配置的逻辑AI Core的数量，用于多核逻辑控制等。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/system_resources_and_variables/GetBlockNum.md
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

# GetBlockNum

## 功能说明

头文件路径为：`"basic_api/kernel_operator_sys_var_intf.h"`。

获取当前任务配置的逻辑AI Core的数量，用于代码内部的多核逻辑控制等。

## 函数原型

```cpp
__aicore__ inline int64_t GetBlockNum()
```

## 参数说明

无

## 返回值说明

返回当前任务配置的逻辑AI Core的数量。

- 返回值与<<<\>\>\>调用时配置的numBlocks一致，为参与计算的逻辑AI Core的数量。
- 当仅启动Cube Core（AIC）或Vector Core（AIV）时，实际启动的AIC或AIV的数量与numBlocks一致。
- 当同时启动Cube Core（AIC）与Vector Core（AIV）时，实际启动的AIC或AIV的数量可以通过[GetTaskRatio\(\)](get_task_ratio.md) \* numBlocks计算得到，在当前支持的配置下：
    - 当AIC与AIV比例为1:2时，AIC启动的数量为numBlocks，AIV启动的数量为2 \* numBlocks；
    - 当AIC与AIV比例为1:1时，AIC启动的数量为numBlocks，AIV启动的数量为numBlocks。

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

- [逐 block 串行启动退化多核并行](../../../../../runbooks/performance/block.md)（`exemplifies`）：改单次 `<<<numBlocks, nullptr, stream>>>` + kernel 内 `GetBlockIdx/GetBlockNum` 自算 `［startRow, endRow)` 后；获取当前任务配置的逻辑AI Core的数量，用于代码内部的多核逻辑控制等。；接口合同直接支撑修复后的 kernel 内多核行区间计算。
- [限制TilingData结构大小](../../../../../guides/operator_practice/simd_operator_optimization/overhead_optimization/limit_tiling_data_size.md)（`explains`）：“NumBlocks信息已经通过SetSimdNumBlocks接口进行设置，可以在Kernel侧调用GetBlockNum接口获取，无需通过TilingData结构传递。”；“获取当前任务配置的逻辑AI Core的数量，用于代码内部的多核逻辑控制等。”。Guide 给出删除冗余 NumBlocks 字段的具体替代调用，API 卡说明 GetBlockNum 返回的是任务逻辑核数。
- [GatherV2 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/index/gather_v2_950.md)（`related`）：“与 R-001 的行/列搬运相同，但分核与 `ubAvailable` 在 Device 用 `GetBlockNum/GetUBSizeInBytes-128KiB` 重算，避免 PCIe 地址由 SIMT 直接解引用。”记录 GatherV2 PCIe 路线的实际调用；“获取当前任务配置的逻辑AI Core的数量，用于代码内部的多核逻辑控制等。”给出 GetBlockNum 的返回语义，直接支撑 Device 分核重算。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 149 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Rasterizer A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/rasterizer.md)（`related`）：算子声明的固定版本源码包含对 `GetBlockNum(...)` 的直接调用（第 47 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/rasterizer/op_kernel/barycentric_from_imgcoord_kernel.h#L47)
- [Cat 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/cat_950.md)（`related`）：算子声明的固定版本源码包含对 `GetBlockNum(...)` 的直接调用（第 79 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/concat/op_kernel/arch35/one_axis_concat_all_align.h#L79)
- [Celu 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/celu_950.md)（`related`）：算子声明的固定版本源码包含对 `GetBlockNum(...)` 的直接调用（第 64 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/celu_v2/op_kernel/arch35/celu_v2.h#L64)
- [BlockSparseAttention A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/block_sparse_attention.md)（`related`）：算子声明的固定版本源码包含对 `GetBlockNum(...)` 的直接调用（第 327 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/block_sparse_attention/op_kernel/block_sparse_attention_kernel_regular_arch22.h#L327)
- [UpsampleBicubic2dAA 950 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/upsample_bicubic_2d_aa_950.md)（`related`）：算子声明的固定版本源码包含对 `GetBlockNum(...)` 的直接调用（第 70 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/upsample_bicubic2d_aa/op_kernel/arch35/upsample_bicubic2d_aa_data_copy.h#L70)
- [CircularPad2dBackward 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/circular_pad_2d_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `GetBlockNum(...)` 的直接调用（第 384 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/pad_v3_grad/op_kernel/arch35/pad_v3_grad_circular_simt.h#L384)
- [InplaceCelu 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/inplace_celu_950.md)（`related`）：算子声明的固定版本源码包含对 `GetBlockNum(...)` 的直接调用（第 64 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/celu_v2/op_kernel/arch35/celu_v2.h#L64)
- [BlockSparseAttention 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/block_sparse_attention_950.md)（`related`）：算子声明的固定版本源码包含对 `GetBlockNum(...)` 的直接调用（第 105 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/block_sparse_attention/op_kernel/arch35/block_sparse_attention_kernel_arch35_full_quant.h#L105)
- [UpsampleBicubic2dAAGrad 950 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/upsample_bicubic_2d_aa_grad_950.md)（`related`）：算子声明的固定版本源码包含对 `GetBlockNum(...)` 的直接调用（第 70 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/upsample_bicubic2d_aa_grad/op_kernel/arch35/upsample_bicubic2d_aa_grad_data_copy.h#L70)
- [MaskedSelect A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/masked_select.md)（`related`）：算子声明的固定版本源码包含对 `GetBlockNum(...)` 的直接调用（第 63 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/masked_select_v3/op_kernel/masked_select_v3.h#L63)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
