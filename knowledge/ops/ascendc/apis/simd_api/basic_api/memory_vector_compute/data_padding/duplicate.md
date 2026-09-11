---
type: API
title: Duplicate
description: 将变量或立即数复制多次并填充到向量中，支持前n个数据计算和高维切分计算两种方式。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.execution_unit.vector
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_padding/Duplicate.md
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
- include/basic_api/kernel_operator_vec_duplicate_intf.h
---

# Duplicate<a name="ZH-CN_TOPIC_0000002543264872"></a>

## 功能说明<a name="section618mcpsimp"></a>

头文件路径为：`"basic_api/kernel_operator_vec_duplicate_intf.h"`。

Duplicate接口将一个变量或立即数复制多次并填充到向量中。

接口支持使用前n个数据计算和高维切分计算的方式，前n个数据计算原理和参考伪代码如下：

```python
import numpy as np

def Duplicate(scalarValue, dst, count):
    for i in range(count):     
        dst[i] = scalarValue
```

针对Ascend 950PR/Ascend 950DT，为方便开发者使用，tensor前n个数据计算接口同时也支持直接传入LocalTensor，此时会将LocalTensor的第一个元素复制多次并填充到向量中。


## 函数原型<a name="section620mcpsimp"></a>

- tensor前n个数据计算，源操作数为标量

    ```cpp
    template <typename T>
    __aicore__ inline void Duplicate(const LocalTensor<T>& dst, const T& scalarValue, const int32_t& count)
    ```



- tensor前n个数据计算，源操作数为LocalTensor

    ```cpp
    // 该函数原型，仅支持Ascend 950PR/Ascend 950DT。
    template <typename T>
    __aicore__ inline void Duplicate(const LocalTensor<T>& dst, const LocalTensor<T>& src, const int32_t& count)
    ```


- tensor高维切分计算，mask逐比特模式

    ```cpp
    template <typename T, bool isSetMask = true>
    __aicore__ inline void Duplicate(const LocalTensor<T>& dst, const T& scalarValue, uint64_t mask[], const uint8_t repeatTime, const uint16_t dstBlockStride, const uint8_t dstRepeatStride)
    ```

- tensor高维切分计算，mask连续模式

    ```cpp
    template <typename T, bool isSetMask = true>
    __aicore__ inline void Duplicate(const LocalTensor<T>& dst, const T& scalarValue, uint64_t mask, const uint8_t repeatTime, const uint16_t dstBlockStride, const uint8_t dstRepeatStride)
    ```

## 参数说明<a name="section622mcpsimp"></a>

**表1**  模板参数说明

| 参数说明 | 描述 |
| ------ | ------ |
| T | 操作数数据类型。 |
| isSetMask | 是否在接口内部设置mask。<br>&bull; true，表示在接口内部设置mask。<br>&bull; false，表示在接口外部设置mask，开发者需要使用[SetVectorMask](../mask_operations/set_vector_mask.md)接口设置mask值。这种模式下，接口入参中的mask值设置为占位符`MASK_PLACEHOLDER`，用于占位，无实际含义。 |

**表2**  接口参数说明
| 参数说明 | 输入/输出 | 含义 |
| ------ | ------ | ------ |
| dst | 输出 | 目的操作数，类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。LocalTensor的起始地址需要按照32字节对齐。|
| scalarValue | 输入 | 被复制的源操作数，数据类型需与dst中元素的数据类型保持一致。|
||
| count | 输入 | 参与计算的元素个数。关于该参数的具体说明请参考[连续计算](../simd_compute/continuous_compute.md)。|
| mask/mask[] | 输入 | mask用于控制每次迭代内参与计算的元素。<br>设置详见[掩码操作](../mask_operations/index.md)。 |
| repeatTime | 输入 | 指令迭代次数，每次迭代完成8个DataBlock的数据收集，取值范围：repeatTime∈[0,255]。|
| dstBlockStride | 输入 | 单次迭代内，矢量目的操作数不同datablock间地址步长，单位为DataBlock。 |
| dstRepeatStride | 输入 | 相邻迭代间，矢量目的操作数相同datablock地址步长，单位为DataBlock。 |

## 数据类型


- 针对Ascend 950PR/Ascend 950DT，T支持的数据类型为：bool、int8_t、uint8_t、fp4x2_e2m1_t、fp4x2_e1m2_t、hifloat8_t、fp8_e8m0_t、fp8_e5m2_t、fp8_e4m3fn_t、int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float、complex32、int64_t、uint64_t、complex64。其中，bool、int8_t、uint8_t、fp4x2_e2m1_t、fp4x2_e1m2_t、hifloat8_t、fp8_e5m2_t、fp8_e4m3fn_t、fp8_e8m0_t、complex32、int64_t、uint64_t、complex64数据类型仅支持tensor前n个数据计算接口。


- 针对Atlas A3 训练系列产品/Atlas A3 推理系列产品，T支持的数据类型为：int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float。


- 针对Atlas A2 训练系列产品/Atlas A2 推理系列产品，T支持的数据类型为：int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float。


- 针对Atlas 200I/500 A2 推理产品，T支持的数据类型为：int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float。


- 针对Atlas 推理系列产品AI Core，T支持的数据类型为：int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float。


- 针对Atlas 训练系列产品，T支持的数据类型为：int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float。


- 针对Kirin X90，T支持的数据类型为：half。


- 针对Kirin 9030，T支持的数据类型为：half。


## 返回值说明<a name="section640mcpsimp"></a>	 

无

## 约束说明<a name="section633mcpsimp"></a>

- 操作数地址对齐要求请参见[通用地址对齐约束](../../../general_description_and_constraints.md#section796754519912)。

- 当参数count或repeatTime取值为0时，该接口的行为如下：
  
  - 针对如下型号，该接口不会执行计算操作，不会对目的操作数进行写入，该接口将被视为NOP（空操作）。
    
    - Atlas A3 训练系列产品/Atlas A3 推理系列产品
    
    
    - Atlas A2 训练系列产品/Atlas A2 推理系列产品
    
  
  
  - 针对Ascend 950PR/Ascend 950DT，该接口通过VF调用[Reg矢量计算API](../../reg_vector_compute/index.md)实现兼容，当参数count或repeatTime取值为0时，不保证该接口将被视为NOP（空操作）。
  


## 调用示例<a name="section642mcpsimp"></a>

本调用示例中只展示完整样例中的接口部分代码。如果您需要运行示例代码，请直接参考完整样例[Duplicate样例](https://gitcode.com/cann/asc-devkit/tree/885973fe9fd42a600e3551af9bc11a279e6f183b/examples/01_simd_cpp_api/03_basic_api/01_memory_vector_compute/duplicate)进行编译执行。

- tensor高维切分计算样例，mask连续模式

    ```cpp
    uint64_t mask = 128;
    half scalar = 18.0;
    // repeatTime = 2, 128 elements one repeat, 256 elements total
    // dstBlkStride = 1, no gap between blocks in one repeat
    // dstRepStride = 8, no gap between repeats
    AscendC::Duplicate(dstLocal, scalar, mask, 2, 1, 8 );
    ```

- tensor高维切分计算样例，mask逐bit模式

    ```cpp
    uint64_t mask[2] = { UINT64_MAX, UINT64_MAX };
    half scalar = 18.0;
    // repeatTime = 2, 128 elements one repeat, 256 elements total
    // dstBlkStride = 1, no gap between blocks in one repeat
    // dstRepStride = 8, no gap between repeats
    AscendC::Duplicate(dstLocal, scalar, mask, 2, 1, 8 );
    ```

- tensor前n个数据计算样例，源操作数为标量

    ```cpp
    half inputVal(18.0);
    int32_t srcDataSize = 256; // 参与计算的元素个数
    AscendC::Duplicate<half>(dstLocal, inputVal, srcDataSize);
    ```



- tensor前n个数据计算样例，源操作数为Tensor
    ```cpp
    AscendC::Duplicate<half>(dstLocal, srcLocal, srcDataSize);
    ```

结果示例如下：

```plain
scalar: 18.0
srcLocal: [18.0 1.0 2.0 ... 254.0 255.0]
dstLocal: [18.0 18.0 18.0 ... 18.0 18.0]
```


<!-- cannbot:related:start -->
## 相关

- [Duplicate 全量清零 padding 覆盖有效区 banned](../../../../../runbooks/precision/duplicate_padding_banned.md)（`exemplifies`）：“将变量或立即数复制多次并填充到向量中，支持前n个数据计算和高维切分计算两种方式。”明确给出左端事实；“2. `Duplicate(bG, 0, count_padded)` 同样从 0 开始全量填 0，覆盖了 `bG`（gradOutput）的有效元素——`Duplicate` 不支持 offset 操作，只能从 0 开始填整个 `count_padded`，无法只清 `［count, count_padded)` 区间。”明确给出右端事实。API 从起点连续填充的语义解释了为何试图只清 padding 却覆盖有效区；排障页给出全量 Duplicate 后 ST 回归及源头/区间清零替代方向。
- [InitOutput GM 专用，UB 清零用 Duplicate](../../../../../runbooks/compilation/initoutput_gm_ub_duplicate.md)（`exemplifies`）：“将变量或立即数复制多次并填充到向量中，支持前n个数据计算和高维切分计算两种方式。”明确给出左端事实；“UB 侧 LocalTensor 清零的正确 API 是 `Duplicate`（Vector 通道，按 mask 清零整个/部分 VReg），不是 `InitOutput`。”明确给出右端事实。API 的 LocalTensor 填充值能力正是排障页修复 InitOutput(GlobalTensor) 类型不匹配时采用的 UB 清零路径。
- [UB 预填充 Duplicate 引入 Vector 开销拖慢纯写带宽](../../../../../runbooks/performance/duplicate_ub_prefill_hurts_pure_write_bandwidth.md)（`exemplifies`）：`Duplicate<half>` 是 Vector 流水线指令，执行时占用 Vector 管线把 UB 填成指定值。在纯写探针里，UB 内容对 HBM 写带宽无影响（HBM 控制器按总线事务写，不关心 payload 初值），但 `Duplicate` 与 `DataCopy`（MTE3）在 kernel 里串行执行，`Duplicate` 的 Vector 执行时间被加进 kernel 总时间，拉低写带宽。即"预填充 UB"没有 HBM 侧收益，只有 Vector 侧开销。；将变量或立即数复制多次并填充到向量中，支持前n个数据计算和高维切分计算两种方式。运行手册用纯写 HBM 探针实证该填充 API 会额外占用 Vector 流水线，给出不得为写带宽预填 UB 的具体性能边界。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 29 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [DiagFlat A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/diag_flat.md)（`related`）：算子声明的固定版本源码包含对 `Duplicate(...)` 的直接调用（第 327 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/diag_flat/op_kernel/diag_flat_nd_to_2d.h#L327)
- [GeluQuant 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/gelu_quant_950.md)（`related`）：算子声明的固定版本源码包含对 `Duplicate(...)` 的直接调用（第 193 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/gelu_quant/op_kernel/arch35/gelu_dynamic_quant_regbase.h#L193)
- [BlockSparseAttention A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/block_sparse_attention.md)（`related`）：算子声明的固定版本源码包含对 `Duplicate(...)` 的直接调用（第 187 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/block_sparse_attention/op_kernel/block_sparse_attention_kernel_regular_arch22.h#L187)
- [ReflectionPad2dBackward 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/reflection_pad_2d_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `Duplicate(...)` 的直接调用（第 502 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/pad_v3_grad/op_kernel/arch35/pad_v3_grad_mirror_gather.h#L502)
- [MseLoss A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/loss/mse_loss.md)（`related`）：算子声明的固定版本源码包含对 `Duplicate(...)` 的直接调用（第 33 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/loss/mse_loss_v2/op_kernel/mse_loss_v2_sum.h#L33)
- [FlashAttentionScore 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/flash_attention_score_950.md)（`related`）：算子声明的固定版本源码包含对 `Duplicate(...)` 的直接调用（第 105 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/flash_attention_score/op_kernel/arch35/flash_attention_score_drop_mask_adapter_regbase.h#L105)
- [UnfoldGrad A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/unfold_grad.md)（`related`）：算子声明的固定版本源码包含对 `Duplicate(...)` 的直接调用（第 119 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/unfold_grad/op_kernel/unfold_grad.h#L119)
- [ApplyAdamWQuant A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/optim/apply_adam_w_quant.md)（`related`）：算子声明的固定版本源码包含对 `Duplicate(...)` 的直接调用（第 92 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/optim/apply_adam_w_quant/op_kernel/apply_adam_w_quant_fp16.h#L92)
- [FlashAttentionVarLenScore 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/flash_attention_var_len_score_950.md)（`related`）：算子声明的固定版本源码包含对 `Duplicate(...)` 的直接调用（第 105 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/flash_attention_score/op_kernel/arch35/flash_attention_score_drop_mask_adapter_regbase.h#L105)
- [SimThreadExponential A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/math/random/sim_thread_exponential.md)（`related`）：算子声明的固定版本源码包含对 `Duplicate(...)` 的直接调用（第 95 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/random/sim_thread_exponential/op_kernel/sim_thread_exponential.h#L95)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
