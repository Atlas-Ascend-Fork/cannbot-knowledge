---
type: API
title: PipeBarrier
description: 完成同一流水线内的同步控制，保证前序指令中所有数据的读写工作全部完成后，后序指令才能执行。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.implementation.synchronization
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/PipeBarrier_ISASI.md
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
- include/basic_api/kernel_operator_block_sync_intf.h
---

# PipeBarrier\(ISASI\)<a name="ZH-CN_TOPIC_0000001835308877"></a>

## 功能说明<a name="section618mcpsimp"></a>

头文件路径为：`"basic_api/kernel_operator_block_sync_intf.h"`。

如下图1所示，完成同一流水线内的同步控制，用于在同一流水线内部约束执行顺序。其作用是，保证前序指令中所有数据的读写工作全部完成，后序指令才能执行。

**图1**  PipeBarrier接口功能示意图<a name="zh-cn_topic_0000002549838971_fig7681194617307"></a>  
![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/pipebarrier_function_diagram.png "PipeBarrier_接口功能示意图")

## 函数原型<a name="section620mcpsimp"></a>

```cpp
template <pipe_t pipe>
__aicore__ inline void PipeBarrier()
```

## 参数说明<a name="section622mcpsimp"></a>

**表1** 模板参数说明

| 参数名 | 描述 |
| -------- | -------- |
| pipe | 模板参数，表示阻塞的流水类别。<br>支持的流水参考[硬件流水类型](intra_core_sync_overview.md#zh-cn_topic_0000002542725361_section1272612276459)，其中不支持PIPE_S。<br>如果不关注流水类别，希望阻塞所有流水，可以传入PIPE_ALL。 |

## 返回值说明<a name="section640mcpsimp"></a>

无

## 约束说明<a name="section633mcpsimp"></a>

- Scalar流水之间的同步由硬件自动保证，PipeBarrier接口不支持PIPE\_S单流水的同步。

- `PipeBarrier<PIPE_ALL>()`会等待所有流水线中所有先前提交的接口完成，这会对性能产生影响。若仅阻塞单条流水线即可解决问题，应避免随意调用`PipeBarrier<PIPE_ALL>()`。

- PIPE\_MTE2/PIPE\_MTE3在搬运地址有重叠的情况下需要开发者插入同步。例如，当需要执行多个DataCopy指令，且DataCopy的目的地址存在重叠时，需要调用PipeBarrier接口插入单流水同步指令，保证多个DataCopy指令的串行化，防止出现异常数据。如下图左侧示意图，执行两个DataCopy指令，搬运的目的GM地址存在重叠，两条搬运指令之间需要通过调用`PipeBarrier<PIPE_MTE3>()`添加MTE3搬出流水的同步；如下图右侧示意图所示，搬运的目的地址Unified Buffer（UB）存在重叠，两条搬运指令之间需要调用`PipeBarrier<PIPE_MTE2>()`添加MTE2搬入流水的同步。

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/datacopy_address_overlap_pipebarrier.png "DataCopy_地址重叠_PipeBarrier_同步示意图")

## 调用示例<a name="section837496171220"></a>

如下示例，Mul指令的输入dst0Local是Add指令的输出，两个矢量运算指令产生依赖，需要插入PipeBarrier保证两条指令的执行顺序。

注：仅作为示例参考，以下情况下PIPE\_V同步无需开发者手动插入：

- 开启[cce-auto-sync编译选项](key_features.md#cce-compiler-auto-sync)时，毕昇编译器自动插入PIPE\_V之间的同步。


- 针对Ascend 950PR/Ascend 950DT，PIPE\_V之间的同步由硬件保证。


**图2**  Mul指令和Add指令是串行关系，必须等待Add指令执行完成后，才能执行Mul指令。<a name="fig1359216580459"></a>  
![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/mul_add_pipebarrier_sync_diagram.png "Mul_Add_指令_串行依赖_PipeBarrier_同步示意图")

```cpp
AscendC::LocalTensor<half> src0Local;
AscendC::LocalTensor<half> src1Local;
AscendC::LocalTensor<half> src2Local;
AscendC::LocalTensor<half> dst0Local;
AscendC::LocalTensor<half> dst1Local;

AscendC::Add(dst0Local, src0Local, src1Local, 512);
AscendC::PipeBarrier<PIPE_V>();
AscendC::Mul(dst1Local, dst0Local, src2Local, 512);
```


<!-- cannbot:related:start -->
## 相关

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 305 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Rasterizer A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/rasterizer.md)（`related`）：算子声明的固定版本源码包含对 `PipeBarrier(...)` 的直接调用（第 176 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/rasterizer/op_kernel/barycentric_from_imgcoord_kernel.h#L176)
- [ChunkCat A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/chunk_cat.md)（`related`）：算子声明的固定版本源码包含对 `PipeBarrier(...)` 的直接调用（第 123 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/chunk_cat/op_kernel/chunk_cat.h#L123)
- [Celu 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/celu_950.md)（`related`）：算子声明的固定版本源码包含对 `PipeBarrier(...)` 的直接调用（第 114 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/celu_v2/op_kernel/arch35/celu_v2.h#L114)
- [AttentionUpdate A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/attention_update.md)（`related`）：算子声明的固定版本源码包含对 `PipeBarrier(...)` 的直接调用（第 200 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/attention_update/op_kernel/decode_update.h#L200)
- [ThreeInterpolateBackward A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/three_interpolate_backward.md)（`related`）：算子声明的固定版本源码包含对 `PipeBarrier(...)` 的直接调用（第 327 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/three_interpolate_backward/op_kernel/three_interpolate_backward.cpp#L327)
- [CircularPad2d A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/circular_pad_2d.md)（`related`）：算子声明的固定版本源码包含对 `PipeBarrier(...)` 的直接调用（第 64 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/circular_pad/op_kernel/circular_pad.h#L64)
- [ClippedSwiglu A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/clipped_swiglu.md)（`related`）：算子声明的固定版本源码包含对 `PipeBarrier(...)` 的直接调用（第 223 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/clipped_swiglu/op_kernel/clipped_swiglu.hpp#L223)
- [BlockSparseAttention A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/block_sparse_attention.md)（`related`）：算子声明的固定版本源码包含对 `PipeBarrier(...)` 的直接调用（第 155 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/block_sparse_attention/op_kernel/attn_infra/epilogue/block/bsa_block_epilogue_online_softmax.hpp#L155)
- [UpsampleBicubic2dAAGrad A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/upsample_bicubic_2d_aa_grad.md)（`related`）：算子声明的固定版本源码包含对 `PipeBarrier(...)` 的直接调用（第 384 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/upsample_bicubic2d_aa_grad/op_kernel/upsample_bicubic2d_aa_grad.h#L384)
- [CircularPad2dBackward A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/circular_pad_2d_backward.md)（`related`）：算子声明的固定版本源码包含对 `PipeBarrier(...)` 的直接调用（第 187 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/circular_pad_grad/op_kernel/arch32/circular_pad_grad.h#L187)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
