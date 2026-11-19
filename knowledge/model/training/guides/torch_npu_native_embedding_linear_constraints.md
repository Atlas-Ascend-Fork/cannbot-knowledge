---
type: Guide
title: 原生Embedding与Linear：索引、权重和精度边界
description: 分开Embedding的input/weight及子方法限制、Linear类函数dtype差异与950DT精度开关，避免误读参数表。并含 embedding_renorm_ 双路维护路径。
tags:
- task.optimization
- topic.precision
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-nn.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-nn-functional.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/EmbeddingKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/npu_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/EmbeddingRenormKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/EmbeddingRenormKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/EmbeddingRenormKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/EmbeddingRenormKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h
  role: implementation
created_at: '2026-11-09T10:11:05Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
- '950'
---

# 原生Embedding与Linear：索引、权重和精度边界

## 固定来源

依据TorchNPU固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 中PyTorch2.7.1、2.9至2.14的完整条目，产品为A2/A3训练系列与950DT，不扩大950PR或发布基线。它们是同一提交中的分版本文档，差异不直接证明发行历史或实际包回归；具体版本按下文区分。未执行上游、设备、精度或性能实验，文档所称“已验证”属于上游口径。

## Embedding的两个数据角色

nn.Embedding input只列INT32/INT64，max_norm非负且不支持NaN；F.embedding却把input列成BF16/FP16/FP32/INT32/INT64，并同样要求max_norm非负。这处表述不能直接解释为浮点索引合法。

OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的embedding_symint把weight与indices分开，要求同设备，输出shape为indices.shape再追加weight末维，输出dtype取weight；将两者直接转发给aclnnEmbedding，没有把浮点indices转换成整数。保守按索引角色核对INT32/INT64与权重浮点类型，函数页的浮点input含义仍待确认，不以表格并集制造新支持组合。该源码也不证明padding_idx、sparse等全部参数或反向都由这段前向处理。

nn.Embedding.from_pretrained的embeddings子条目只列FP64；这是权重数据，与父类input索引限制不同。不能因此把权重转整数，或把一般Embedding权重dtype错误限制为只允许FP64；子方法其他类型应按实际版本另行确认。

## EmbeddingBag的类、forward和functional

EmbeddingBag类input列INT32/INT64、max_norm≥0；forward子条目却把input/offsets仅列INT64，保留窄范围，不用父类的INT32条目替代forward验收。from_pretrained子方法及F.embedding_bag仅列产品，没有一份完整dtype/参数细表；不据省略补齐全部模式、offset、per-sample weight和梯度组合。

## Linear/Bilinear精度与950DT

nn.Linear与LazyLinear的input只列FP16/FP32，F.linear另列BF16；LazyLinear.cls_to_become另列三类产品支持，不表示所有初始化后精度自动等价。nn.Bilinear的input1/input2及F.bilinear的input1/input2/weight/bias列BF16/FP16/FP32，不能据输入支持推导其他仿射或反向的任意混合类型。

Linear类、F.linear和F.bilinear的950DT段提示默认高性能FP32/complex64可能有精度差异，cube_math_type=4可切换高精度但有性能代价；同页类型表未列complex64，不能因这句说明就将其加入已确认dtype。实际setter要求CubeMathType枚举，数值4对应USE_FP32_ADD，见[卷积与精度配置](torch_npu_native_convolution_constraints.md)；不把文档数字直接赋给枚举属性，也不将这类全局策略等同于任意量化Linear的控制。

## 验证边界

分别检查索引范围/类型、weight、offsets、max_norm、子方法、Sparse/梯度需求和实际底层路径，保持模型语义后再比较数值、梯度和端到端耗时。类型表冲突是待确认项，未据调用成功或源码分配张量宣称所有组合可用。

## OneHot输入的文档版本差异

F.one_hot在七版本页均列A2/A3训练系列与950DT。2.7.1、2.9、2.10页input仅INT64，2.11..2.14页列INT32/INT64；按目标文档版本区分，不据新页扩展旧页，也不据同为类别索引把Embedding、OneHot的类型和输出协议混为一谈。该条目未给完整类别范围/num_classes/输出dtype，不能从输入列表补造返回类型或越界处理。

## 英文EmbeddingBag权重子项

英文七版本对EmbeddingBag.from_pretrained把embeddings列为INT64，中文对应子方法只列产品；与Embedding.from_pretrained的FP64条目又是不同接口。保留这个语言/方法差异，不能据此把一般可训练EmbeddingBag权重强制转整数，或将索引input和embeddings权重的角色合并。实际权重类型、返回参数与梯度仍需具体包证据。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-nn.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-nn.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-nn.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-nn.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-nn.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-nn.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-nn.md)（primary）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-nn-functional.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-nn-functional.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-nn-functional.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-nn-functional.md)（constraint）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-nn-functional.md)（constraint）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-nn-functional.md)（constraint）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-nn-functional.md)（primary）
- [固定来源 15](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/EmbeddingKernelNpuOpApi.cpp)（implementation）
- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/npu_config.py)（implementation）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-nn.md)（constraint）

- [EmbeddingRenormKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/EmbeddingRenormKernelNpuOpApi.cpp)（implementation）：1–39；完整本地文件。
- [EmbeddingRenormKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/EmbeddingRenormKernelNpuOpApi.cpp)（implementation）：1–44；完整本地文件，与主线排版+尾部注释差异（发布侧无 `} // namespace op_api` 尾注释），逻辑一致。
- [EmbeddingRenormKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/EmbeddingRenormKernelNpu.cpp)（implementation）：1–114；完整本地文件。
- [EmbeddingRenormKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/EmbeddingRenormKernelNpu.cpp)（implementation）：1–133；完整本地文件，与主线去空白字符流相同。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：2048–2050；仅所列Schema片段。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：1985–1987；仅所列Schema片段。
- [op_api_common.h d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h)（implementation）：94–118；DO_COMPATIBILITY 宏定义（符号探测+ACLNN-only 门）。
- [op_api_common.h dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h)（implementation）：96–113；对应 DO_COMPATIBILITY 宏，与主线同构（仅排版不同）。

## embedding_renorm_ 的 max_norm 维护路径

max_norm 训练维护动作在 ATen 内部落到 aten::embedding_renorm_（acl_op+op_api all_version，主线 2048–2050、发布 1985–1987），与上文『Embedding的两个数据角色』的前向 entry 互补。主线与发布两版本 各有一条 opapi 包装与一条 aclops 旧实现，构成 DO_COMPATIBILITY 双路：

| 路径 | 实际门槛与动作 |
| --- | --- |
| opapi（EmbeddingRenormKernelNpuOpApi.cpp，主线 39 行/发布 44 行，排版+尾部注释差异，逻辑一致） | `DO_COMPATIBILITY(aclnnEmbeddingRenorm, acl_op::embedding_renorm_(…))`；host 检查 self 2 维（at::checkDim）、indices 为 Long **或 Int**（at::checkScalarTypes）；对 **indices.clone()** resize_(numel) 展平后单次 `aclnnEmbeddingRenorm(self, indices_copy, max_norm, norm_type)` 原地改写 self；不改动调用方 indices |
| aclops 回退（EmbeddingRenormKernelNpu.cpp，主线 114 行/发布 133 行，去空白等值） | indices 仅接受 Long；num_indices≥1 TORCH_CHECK；对**传入的 indices 原张量** resize_(numel)（原地改形，调用方可见）；CheckMemory 后 check_match/format_contiguous，再四条 ACE 命令组合：GatherV2D(axis=0) 取行 → Renorm(p=norm_type, dim=0, maxnorm) → 以 range(0,num_indices-1) 索引的 GatherV2D 取逐行缩放系数 → `mid_input * scalar_out` → ScatterUpdate(use_locking=false) 写回 |

两路的设计意图同为 max_norm 维护（把按 norm_type 计算超出 max_norm 的行重整），但设备 kernel 边值与数值等价性未验证，不据此宣称两路结果一致。可观察差异有三处：indices dtype 范围（Long/Int 对 仅 Long）、indices 是否被原地改形（clone 对原张量）、host 侧包装形态（opapi 为单次 aclnn 调用；aclops 为四条 ACE OpCommand——GatherV2D、Renorm、以 range 索引的 GatherV2D、ScatterUpdate——外加 ATen 侧 mid_input*scalar_out 乘法与 at::zeros/at::range/_npu_dtype_cast 辅助；这是 host 命令与 ATen 操作的计数口径，不等于设备 kernel 数，中间内存与同步形态未验证）。走哪一路由 DO_COMPATIBILITY 的静态符号+模式门决定（op_api_common.h 主线 94–118/发布 96–113）：探测 aclnnEmbeddingRenorm 与其 GetWorkspaceSize 两符号，任一缺失且 ACLNN-only 模式下 TORCH_CHECK 直接抛错、不回退，仅非 ACLNN-only 模式才回退 acl_op 旧实现，符号齐全则走 aclnn；该分派与各版本文档的 max_norm 类型表无关。文档「max_norm 非负且不支持 NaN」仍是 host 之外的约束，这两条包装里没有本地 NaN 检查。设备侧 Renorm/ScatterUpdate/aclnnEmbeddingRenorm 的 norm_type=0、inf 等边值行为不在这些 host 源内，未执行数值验证。
