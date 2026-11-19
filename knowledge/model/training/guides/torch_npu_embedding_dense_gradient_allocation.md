---
type: Guide
title: 原生Embedding稠密梯度：整表分配与索引宽度
description: 区分Embedding稠密反向的整表输出、ACL索引INT32转换与OpAPI生成声明，避免从前向或稀疏参数外推梯度能力。
tags:
- task.optimization
- topic.memory
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/EmbeddingDenseBackwardKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/EmbeddingDenseBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-10T14:15:58Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 原生Embedding稠密梯度：整表分配与索引宽度

## 固定入口与去重边界

本卡针对OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`和发布`dedc316708372c9a8bfde4527abd2a94b74840f5`的`embedding_dense_backward`，补充大词表训练中的实际输出准备与索引转换。两版所选ACL C++去注释、空白并拼接续行后token相同；Schema的对应生成描述相同。没有据此认证完整runtime或kernel一致。

[原生Embedding/Linear限制](torch_npu_native_embedding_linear_constraints.md)已有前向类型、同设备及输出形状；[GE索引与Scatter](../../inference/guides/optimization/torchair/torchair_ge_index_scatter_lowering.md)已有图转换。本卡单独核对Eager稠密反向；平台和安装配套未知，保持draft、空平台，未运行上游、生成器、自动求导或设备实验。

## 输出按词表全量申请

ACL入口只在本地显式检查`grad_output.dim()>=1`，随后按`{num_weights, grad_output.size(-1)}`调用`apply_tensor(grad_output, output_size)`。若词表为V、向量宽度为D，申请形状是V×D，不能用本卡索引数量或去重后行数代替输出规模估算。它没有按触及的行构造稀疏输出，也没有在该入口添加空索引直接返回稀疏结果的分支。

这个准备调用以grad_output为参照，没有显式把结果强制成FP32。不能仅凭输出申请dtype认证kernel累加精度、未触及行如何置零、实际显存峰值或所有格式保持不变；这些还依赖准备函数与底层算子。所读入口没有在调用前另做`contiguous`，也不能因此保证所有非连续stride都无代价或受支持。

## ACL在调用前转INT32索引

局部代码无条件调用`_npu_dtype_cast(indices, at::kInt)`，再将结果与grad_output交给`EmbeddingDenseGrad`，传递`num_weights`、`padding_idx`、`scale_grad_by_freq`三个属性。这里没有先检查INT64值能否无损落入INT32；大词表或大索引场景需要保留真实索引范围作为验证条件，不能从前向接受INT64直接推导这次反向全程保持64位索引。

源注释关于NPU只支持INT32是该转换的局部说明，不是本卡已核对的全产品、全入口能力矩阵。该入口也没有完整校验indices与grad_output形状、设备、索引上下界及padding语义；条件缺失不能当作任意输入被支持。

## OpAPI这里只核对生成描述

两版Schema均为该入口声明ACL/OpAPI候选和`[v2.1,newest]`范围，`gen_opapi`指定输出size为`{num_weights, grad_output.size(-1)}`、dtype取grad_output、exec为`aclnnEmbeddingDenseBackward`。这说明固定源码中的生成意图；本卡没有执行生成器、加载生成注册或核对安装包生成物。

因此不能把ACL的显式INT32转换套到尚未展开的生成OpAPI调用，也不能凭exec名字断言目标设备支持或没有Host搬运。若要比较两路性能，应先确认实际dispatcher选择和生成消费者，再记录两路输入、输出、格式与临时量。

## 稠密入口不替代完整稀疏训练分析

`embedding_dense_backward`签名没有sparse参数。本卡证明的是进入该准确稠密入口之后的准备和调用；上层Embedding如何按sparse选择自动求导路径、稀疏梯度后续如何交给optimizer，仍需对应ATen/自动求导消费者证据。不能因前向有sparse参数、局部没有使用某参数，或此处申请了整表，就宣称所有Embedding训练都强制稠密或稀疏模式不可用。

验证时先区分普通Embedding权重梯度与EmbeddingBag的per-sample weights梯度，后者另见[EmbeddingBag辅助缓冲与CPU反向](torch_npu_embedding_bag_aux_buffers_and_cpu_backward.md)。记录准确入口、V/D、索引dtype及最大值、频次缩放、padding、空索引和实际后端，再核数值及内存；本卡未给出性能数字或verified记录。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/EmbeddingDenseBackwardKernelNpu.cpp)（primary）：19–47。
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/EmbeddingDenseBackwardKernelNpu.cpp)（implementation）：19–47。
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：2035–2046。
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：1972–1983。
