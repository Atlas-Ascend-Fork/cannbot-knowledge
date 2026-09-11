---
type: API
title: Reset
description: 完成资源的释放与eventId等变量的初始化操作，恢复到TPipe的初始化状态。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.implementation.memory_management
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TPipe/Reset.md
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
- include/basic_api/kernel_tpipe.h
---

# Reset<a name="ZH-CN_TOPIC_0000001785898192"></a>

## 功能说明<a name="section618mcpsimp"></a>

头文件路径为：`"basic_api/kernel_tpipe.h"`。

完成资源的释放与eventId等变量的初始化操作，恢复到TPipe的初始化状态。


针对Ascend 950PR/Ascend 950DT，调用该接口后，CTRL\[48\]保持原值，CTRL\[60\]复位为1。CTRL寄存器比特位说明请见[SetCtrlSpr](../../special_register_access/set_ctrl_spr_isasi.md)。


## 函数原型<a name="section620mcpsimp"></a>

```cpp
__aicore__ inline void Reset()
```

## 约束说明<a name="section633mcpsimp"></a>

无

## 返回值说明<a name="section640mcpsimp"></a>

无

## 调用示例<a name="section642mcpsimp"></a>

```cpp
AscendC::TPipe pipe; // Pipe内存管理对象
AscendC::TQue<AscendC::TPosition::VECOUT, 1> que; // 输出数据Queue队列管理对象，TPosition为VECOUT
uint8_t num = 1;
uint32_t len = 192 * 1024;
for (int i = 0; i < 2; i++) {
    pipe.InitBuffer(que, num, len);
    ... // process
    pipe.Reset();
}
```


<!-- cannbot:related:start -->
## 相关

- [Init](init.md)（`related`）：完成资源的释放与eventId等变量的初始化操作，恢复到TPipe的初始化状态。；用于内存和同步流水事件EventID的初始化。；Reset 释放当前资源并恢复 Init 建立的内存与 EventID 状态，两接口构成 TPipe 资源生命周期。
- [SetCtrlSpr](../../special_register_access/set_ctrl_spr_isasi.md)（`related`）：针对Ascend 950PR/Ascend 950DT，调用该接口后，CTRL［48］保持原值，CTRL［60］复位为1。CTRL寄存器比特位说明请见SetCtrlSpr。；对CTRL寄存器（控制寄存器）的特定比特位进行设置。通过模板参数startBit和endBit指定目标比特位范围，将运行参数value（超出比特位范围会出现编译报错）写入CTRL寄存器对应位置。；焦点给出 Reset 对 CTRL 位的副作用，目标提供这些位的显式读取边界与恢复设置入口。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 44 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [MaskedSelect 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/masked_select_950.md)（`related`）：算子声明的固定版本源码包含对 `Reset(...)` 的直接调用（第 120 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/masked_select_v3/op_kernel/arch35/masked_select_v3_apt.h#L120)
- [SwigluGroupQuantGrad 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/swiglu_group_quant_grad_950.md)（`related`）：算子声明的固定版本源码包含对 `Reset(...)` 的直接调用（第 88 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/swiglu_group_quant_grad/op_kernel/swiglu_group_quant_grad_base.h#L88)
- [ChunkGatedDeltaRule A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/chunk_gated_delta_rule.md)（`related`）：算子声明的固定版本源码包含对 `Reset(...)` 的直接调用（第 142 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/chunk_gated_delta_rule/op_kernel/chunk_gated_delta_rule.h#L142)
- [Sort 950 ACLNN 算子知识](../../../../../operators/aclnn/math/math/sort_950.md)（`related`）：算子声明的固定版本源码包含对 `Reset(...)` 的直接调用（第 179 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/sort/op_kernel/arch35/merge_sort_big_size.h#L179)
- [IndexFill 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/index/index_fill_950.md)（`related`）：算子声明的固定版本源码包含对 `Reset(...)` 的直接调用（第 156 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/index/index_fill/op_kernel/arch35/index_fill_simt_dense_indices.h#L156)
- [GroupedMatmul A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/gmm/grouped_matmul.md)（`related`）：算子声明的固定版本源码包含对 `Reset(...)` 的直接调用（第 2024 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/gmm/grouped_matmul/op_kernel/grouped_matmul_autotiling_a8w4.h#L2024)
- [TopK 950 Direct Invoke 算子知识](../../../../../operators/direct/math/math/top_k_950.md)（`related`）：算子声明的固定版本源码包含对 `Reset(...)` 的直接调用（第 332 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/top_k_v2/op_kernel/arch35/radix_sort_top_k.h#L332)
- [IndexFillTensor 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/index/index_fill_tensor_950.md)（`related`）：算子声明的固定版本源码包含对 `Reset(...)` 的直接调用（第 156 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/index/index_fill/op_kernel/arch35/index_fill_simt_dense_indices.h#L156)
- [grouped_matmul_swiglu_quant A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/gmm/grouped_matmul_swiglu_quant.md)（`related`）：算子声明的固定版本源码包含对 `Reset(...)` 的直接调用（第 101 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/gmm/grouped_matmul_swiglu_quant_v2/op_kernel/grouped_matmul_swiglu_quant_v2_a4w4_pipeline.h#L101)
- [InplaceIndexFillTensor 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/index/inplace_index_fill_tensor_950.md)（`related`）：算子声明的固定版本源码包含对 `Reset(...)` 的直接调用（第 156 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/index/index_fill/op_kernel/arch35/index_fill_simt_dense_indices.h#L156)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
