---
type: Guide
title: 原生损失的NPU边界：标签、梯度与文档版本
description: 对照标签边界、梯度回流与文档版本差异，保留MultiMargin/CTC/多标签的类型表。并含 KL/BCE/L1/SoftMargin 的生成直发规格与反向接线。并含 multi_margin_loss 的负向确认：主线与发布两版本 yaml 与源树均无注册/实现，文档表支持不能由来源源码认证。并含BCEWithLogits aclops 回退与 custom 反向实现层。
tags:
- task.implementation
- topic.precision
- topic.compilation
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
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/NLLLossKernelNpuOpApi.cpp
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
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MseLossKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SmoothL1LossKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SmoothL1LossBackwrdKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MseLossKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/SmoothL1LossKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/SmoothL1LossBackwrdKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/CtcLossKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/CtcLossKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/CtcLossBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/CtcLossKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/CtcLossKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/CtcLossBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SoftMarginLossKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SoftMarginLossKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SoftMarginLossBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SoftMarginLossBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LossKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LossKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/BinaryCrossEntropyWithLogitsKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/BinaryCrossEntropyWithLogitsKernelNpu.cpp
  role: implementation
created_at: '2026-11-09T10:11:05Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# 原生损失的NPU边界：标签、梯度与文档版本

## 固定版本与范围

依据TorchNPU固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 中PyTorch2.7.1、2.9至2.14的完整条目，产品为A2/A3训练系列与950DT，不扩大950PR或发布基线。它们是同一提交中的分版本文档，差异不直接证明发行历史或实际包回归；具体版本按下文区分。未执行上游、设备、精度或性能实验，文档所称“已验证”属于上游口径。

损失的input类型、target类型/范围、reduction和梯度需求必须分别核对。清单允许某种整数input不代表整数能求导；同名类与functional的表述也不能直接并成同一支持集合。

## 标签与目标梯度先于性能调优

NLLLoss类在七版本列FP16/FP32，F.nll_loss仅列FP32；普通类别target需≥0且小于类别数。2.13/2.14的functional页额外明确：越界可能返回错误结果而非报错；旧页没有该提示不证明旧实现会主动抛错。不能以loss是有限值作为标签合法的唯一验收。

OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的NLLLoss包装将ignore_index独立转发给aclnnNLLLoss，不在框架这层遍历target做全部类别范围检查。调用方应区分真实类别和约定的ignore_index，不能把任意负值都视为忽略，亦不由“target≥0”一句删除模型合法的忽略标签。具体忽略值、空有效样本与归约行为按实际包另行核对；两主线不视为已配套运行。

CTCLoss与F.ctc_loss的log_probs列FP32/FP64；类不支持2D log_probs，functional的target_lengths不得含0。不能通过随意将0改1或增添假标签规避限制，这会改变任务定义。

KLDivLoss/F.kl_div仅支持log_target=False，functional明确target不支持求导。BCEWithLogitsLoss也明确target不支持反向计算，不能用于需要对目标分支反传的配方而不核对实现；类条目缺少某句限制不意味着functional与类的任意梯度需求均获支持。

## 类型表与版本差异

| 入口 | 主要input限制 |
| --- | --- |
| CrossEntropyLoss / F.cross_entropy、MSELoss | FP16/FP32 |
| F.mse_loss（2.11..2.14页） | FP16/FP32 |
| F.mse_loss（2.7.1、2.9、2.10页） | BF16、FP16/32/64、UINT8、INT8/16/32/64、complex64/128 |
| BCELoss | FP16/FP32 |
| F.binary_cross_entropy及F.binary_cross_entropy_with_logits、BCEWithLogitsLoss | BF16/FP16/FP32 |
| L1Loss | FP16/FP32/INT64 |
| F.l1_loss、PoissonNLLLoss及F.poisson_nll_loss | BF16/FP16/FP32/INT64 |
| GaussianNLLLoss | BF16/FP16/FP32、INT16/32/64 |
| F.gaussian_nll_loss | 上一行再列UINT8/INT8；不扩展类入口 |
| MultiLabelSoftMarginLoss | FP16/FP32 |
| F.multilabel_soft_margin_loss、SmoothL1Loss及F.smooth_l1_loss | BF16/FP16/FP32 |
| F.soft_margin_loss | BF16/FP16/FP32，明确排除double/complex |

F.mse_loss的版本差异来自同一提交的页面，不据此声称设备上的历史回归或版本升级必然改善。按目标版本和实际Kernel核对，不把旧页宽类型表套到2.14。

MarginRankingLoss列input1/input2/target为BF16、FP16/FP32、INT8/INT32/INT64；functional只列前三种浮点，分别消费。HingeEmbeddingLoss类列BF16、FP16/FP32、UINT8、INT8/16/32/64；同名functional未给同一表，不外推。

F.multilabel_margin_loss列FP16/FP32且输入Tensor元素数≤100000；MultiLabelMarginLoss类未重复该上限，不能靠改用类规避底层限制。AdaptiveLogSoftmaxWithLoss及log_prob/predict、CosineEmbeddingLoss及functional、F.huber_loss、SoftMarginLoss类、F.triplet_margin_loss/with_distance等只列产品或未给额外dtype细表，不据省略补齐未确认组合。

## 可能CPU回退的路径

F.poisson_nll_loss明确可能CPU回退，而PoissonNLLLoss类未重复该句。HuberLoss类input为FP32/FP64，target为BF16、FP16/32/64、UINT8、INT8/16/32/64、BOOL，且可能CPU回退；MultiMarginLoss类input为FP32/FP64、target仅INT64，也可能CPU回退。

TripletMarginLoss类anchor/positive/negative列FP16/FP32、UINT8、INT8/16/32/64并可能CPU回退；TripletMarginWithDistanceLoss只对anchor列BF16/FP16/FP32。不能把这些类的回退描述、dtype和自定义距离函数可用性互相推广。

## 验证边界

覆盖合法/越界标签、ignore_index、空目标、需要/不需要目标梯度、reduction及训练/推理；核对实际CPU/NPU路径，再比较误差、梯度、内存与耗时。未运行损失计算，不把forward成功当成全部反向或性能已验证。

- [CPU回退门控](../../inference/guides/optimization/torch_npu/torch_npu_cpu_fallback_and_compatible_impl.md)
- [词表并行融合损失](torch_npu_vocab_parallel_loss_contract.md)：另有分布式统计与反向交付，不等同本卡原生接口。

## MultiMargin的functional入口

F.multi_margin_loss在七版本页列三类产品，但未重复nn.MultiMarginLoss类的dtype/CPU回退文字。保留类与函数各自条目，不能把省略解释成所有input/target类型、全部梯度或完全没有CPU路径；类的FP32/FP64 input、INT64 target及可能回退提示继续按前文消费。

## BCEWithLogits aclops 回退与 custom 反向实现层

上文 KL/BCE 节核对了 gen 直发规格与反向接线；本节补 aclops 侧 `BinaryCrossEntropyWithLogitsKernelNpu.cpp`（132 行，主线与发布两版本 去空白等价）。前向 nocheck：`reduction==None` 输出取 self.sizes()、否则标量且结果格式 ND；**weight/pos_weight 未定义时以 `at::ones(self.sizes())` 物化**，定义时 `format_contiguous` 且 dtype 不同则 `_npu_dtype_cast` 到 self dtype；reduction 转字符串属性后发 ACE `SigmoidCrossEntropyWithLogitsV2`。custom 反向 `npu_binary_cross_entropy_with_logits_backward`（与 gen 直发 `aclnnBinaryCrossEntropyWithLogitsBackward` 并存，见上文接线行）：aclops 实现为 grad_output 先 `npu_broadcast` 到 self.sizes()，再按前向同款 weight/pos_weight 物化/cast，发 ACE `SigmoidCrossEntropyWithLogitsGradV2`（reduction 字符串属性）产出 grad_input。ones 物化与广播副本是 host 侧额外分配点；两条路径输出 dtype 差异未逐项对照（soft_margin 节存在先例），设备侧命令语义未核对。

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
- [固定来源 15](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/NLLLossKernelNpuOpApi.cpp)（implementation）

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


- [BinaryCrossEntropyWithLogitsKernelNpu.cpp 主线与发布两版本](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/BinaryCrossEntropyWithLogitsKernelNpu.cpp)（implementation）：全文 132 行；发布去空白等价。
## MSE与SmoothL1：广播、输出dtype与beta窄化

普通MSE/SmoothL1的functional和out准备不同，返回out引用也不表示省去输出检查；SmoothL1反向另按广播shape申请梯度。以下对应OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`、发布`dedc316708372c9a8bfde4527abd2a94b74840f5`，不扩大前述产品支持表。

| 入口 | 局部输出准备 | 优化定位点 |
|---|---|---|
| MSE functional | reduction=None按self/target广播shape，其余shape{}；result_type(self,target)申请 | 输出高类型不等于预先cast输入 |
| MSE out | 同一shape规则，check_tensor取result自身dtype | 不重用functional的result_type选择 |
| SmoothL1 functional | None取self原shape，其余shape{}；result_type申请 | 该前向helper没有计算self/target广播shape |
| SmoothL1 out | 取同一前向shape、out自身dtype检查，再check_memory | functional没有同样显式check_memory |
| SmoothL1 backward | 先广播self/target，再与grad_out广播 | functional按self选项申请，out按grad_input自身dtype检查 |

三份手写包装都先执行对应DO_COMPATIBILITY，实际传原输入给SDK，没有在这些函数统一materialize广播后的输入或先做dtype转换。broadcast helper只调用infer_size；不能把shape推导当作底层已完成广播复制。MSE out保存广播helper结果的局部类型为IntArrayRef，本节不把这段静态语句外推成所有生命周期与shape组合已运行验证。

SmoothL1前后向将double beta显式static_cast<float>为sigma，再传aclnnSmoothL1Loss/aclnnSmoothL1LossBackward；不能据Python参数外观或最终输出dtype声称保留任意double beta精度。这里没有额外beta==0捷径、负值完整检查或异常后重跑协议，SDK数值边界另核。

MSE backward由两版Schema的gen_opapi配置描述，而非本组某个不存在的MseLossBackward CPP：functional输出size为嵌套广播(grad_output,self,target)，dtype=self，exec=aclnnMseLossBackward；grad_input重载声明同一size，没有同一显式dtype配置。生成配置的通用解释见[OpPlugin适配](../../inference/guides/optimization/torch_npu/torch_npu_opplugin_adaptation.md)，本卡没有执行生成器或据配置推导完整反向支持。

两版这三份完整CPP主体与非namespace注释相同；所列八个Schema入口均acl_op/op_api all_version。模型比较应固定reduction、self/target/grad形状、out dtype和beta实际数值，验证广播/数值/梯度后，再比较高类型结果申请与检查成本。仅静态来源审阅，没有损失、设备或性能运行记录，不新增verified或平台承诺。

### 损失执行证据

- [MseLossKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MseLossKernelNpuOpApi.cpp)（implementation）：1–45。
- [SmoothL1LossKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SmoothL1LossKernelNpuOpApi.cpp)（implementation）：1–47。
- [SmoothL1LossBackwrdKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SmoothL1LossBackwrdKernelNpuOpApi.cpp)（implementation）：1–56。
- [KernelNpuOutputSize.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：115–125、1409–1415。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：3610–3633、4785–4799。
- [MseLossKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MseLossKernelNpuOpApi.cpp)（implementation）：1–52。
- [SmoothL1LossKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/SmoothL1LossKernelNpuOpApi.cpp)（implementation）：1–45。
- [SmoothL1LossBackwrdKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/SmoothL1LossBackwrdKernelNpuOpApi.cpp)（implementation）：1–58。
- [KernelNpuOutputSize.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：112–125、1250–1257。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：3502–3525、4631–4645。

## CTC前后向：辅助空间、FP16转换与旧ACL分支

CTC的代价不止输出loss。两版都按Host侧`target_lengths`列表最大值申请log_alpha；旧ACL前后向还会执行FP16→FP32及结果回转，反向另创建length张量。

| 路线 | 可见准备与输出行为 | 关键边界 |
| --- | --- | --- |
| OpAPI `_ctc_loss` | 扫target_lengths，max_length初始0，仅被更大的值更新；按log_probs options申请NLL和log_alpha，交aclnnCtcLoss，length仍作为IntArrayRef参数 | 主线在兼容宏前要求log_probs.numel()>0，发布没有该本地前置检查；没有在此包装内强制Half转Float。兼容宏指向旧ACL实现，其缺符号边界按[兼容门控](../../inference/guides/optimization/torch_npu/torch_npu_cpu_fallback_and_compatible_impl.md)核对，不等于CPU回退 |
| 旧ACL前向 | 要求log_probs为2或3维；Half先转Float，再按转换后的options和原生格式申请两输出；2维输入reshape为[T,1,C]；执行CTCLossV2后原log_probs为Half时两输出都cast回Half | 主线num_classes按3维取shape[2]、2维取shape[1]；发布虽然先允许2维，后面仍在reshape前直接读取shape[2]。保留这项静态差异，不据此宣称已运行复现 |
| 旧ACL反向 | grad、log_probs、NLL、log_alpha各自为Half时分别转Float；由两个Host长度列表按targets.options创建Tensor；按转换后的log_probs申请梯度，交CTCLossV2Grad | targets不在这些Half转换之列；**最终是否转回Half取grad.dtype**，不是log_probs.dtype。length张量创建表示准备/复制请求，不能仅凭这两行推断一次设备同步 |
| 生成OpAPI反向Schema | 输出size取log_probs、dtype取grad，执行aclnnCtcLossBackward | 这是生成配置，不能把上面旧ACL命令的每项转换成本套给它 |

形状helper取T=log_probs.size(0)，2维B=1，其他读size(1)；NLL在2维返回标量shape，其余为[B]。log_alpha为`[B,T,A]`，`A0=2*max_length+1`，静态缓存SoC≥Ascend950时A=A0，否则A向上取8的倍数。这里是**元素维度的舍入**，不能改写成任意dtype指针地址都已32字节对齐；max_length增长会直接扩大这块辅助输出。helper不独立验证负长度、溢出或所有rank合法性。

旧ACL前向将`blank`编码为`blank + max_length*num_classes`后放入CTCLossV2属性；发布用shape[2]做同一表达式。旧ACL反向仍传入原blank，OpAPI aclnnCtcLoss也直接传原blank，不能把前向旧命令的编码扩展到SDK接口。后者在两固定点都保持NPU命令路线，没有本地CPU路径；类型转换及辅助分配属于可见成本，未实测性能。

### CTC补充证据

- [CtcLossKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/CtcLossKernelNpuOpApi.cpp)（implementation）：1–65。
- [CtcLossKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/CtcLossKernelNpu.cpp)（implementation）：1–83。
- [CtcLossBackwardKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/CtcLossBackwardKernelNpu.cpp)（implementation）：1–67。
- [KernelNpuOutputSize.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：752–776。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：146–157。
- [CtcLossKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/CtcLossKernelNpuOpApi.cpp)（implementation）：1–56。
- [CtcLossKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/CtcLossKernelNpu.cpp)（implementation）：1–77。
- [CtcLossBackwardKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/CtcLossBackwardKernelNpu.cpp)（implementation）：1–65。
- [KernelNpuOutputSize.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：604–628。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：146–157。

## KL/BCE/L1/SoftMargin 的生成直发规格与反向接线

本节把损失家族中 KL/BCE/L1/SoftMargin 四组此前只有文档表与目标梯度约束的入口核对到 op-plugin 注册/生成层；NLL/CTC/MSE/SmoothL1 的既有小节保持不变。yaml 除注明外均 acl_op+op_api all_version + gen_opapi 直发；生成模板与 out 类缺省 dtype 自洽规则复用 _add_relu 先例已核对的结构（激活卡证据），此处不重复。前向/反向 out 规格中的 `broadcast_*`/`result_type` 均为 host 生成层的申请/校验表达式，不构成 device 内核对混合 dtype 的支持承诺。

| 入口 | gen_opapi out 规格（主线与发布两版本 同语义） | 反向接线（derivatives.yaml，主线与发布两版本 相同） |
| --- | --- | --- |
| kl_div | size=`reduction==None ? broadcast(self,target) : 标量`；**dtype=`result_type(self,target)`**；exec aclnnKlDiv | self→kl_div_backward（custom，out size/dtype=self，exec aclnnKlDivBackward）；**target→kl_div_target_backward**（custom，仅 op_api，out size/dtype=target，exec aclnnKlDivTargetBackward） |
| binary_cross_entropy | size=`reduction==None ? self.sizes() : 标量`；dtype=self；exec aclnnBinaryCrossEntropy；`.out` 重载只注 exec（check_tensor 自洽） | backward：out size/dtype=self、exec aclnnBinaryCrossEntropyBackward；`.grad_input` 重载只注 exec |
| binary_cross_entropy_with_logits | size=`reduction==None ? input_same_output_size(target) : 标量`；**dtype=target**；exec aclnnBinaryCrossEntropyWithLogits | self→npu_binary_cross_entropy_with_logits_backward（custom，out size/dtype=target，exec aclnnBinaryCrossEntropyWithLogitsBackward）；target: non_differentiable |
| l1_loss | size=`reduction==None ? broadcast(self,target) : 标量`；**dtype=`result_type(target,self)`**；exec aclnnL1Loss | self→l1_loss_backward；target→`l1_loss_backward(...) * -1`（公式层符号翻转）；l1_loss_backward 的 grad_input size=broadcast(broadcast(self,target),grad_output.sizes())、dtype=`promoteTypes(grad_output.scalar_type(), result_type(target,self))`，exec aclnnL1LossBackward |
| soft_margin_loss | size=`reduction==None ? broadcast(self,target) : 标量`；dtype=self；exec aclnnSoftMarginLoss；`.out/.backward/.grad_input` 同族登记 | backward 的 grad_input size=broadcast(broadcast(grad_output.sizes(),self.sizes()),target.sizes())、dtype=self；exec aclnnSoftMarginLossBackward |

三条跨层口径需要单独记录：

1. **文档与注册面的 target 梯度张力**：前文按文档写「F.kl_div 明确 target 不支持求导」；op-plugin derivatives.yaml 却为 kl_div 登记了 target→kl_div_target_backward 的反向公式（[v2.1,newest]，主线与发布两版本 相同），而 BCEWithLogits 的 target 显式 non_differentiable。注册面存在 target 反向入口与文档面「不支持」并存：该公式在公开 API 上是否可达、kl_div_target_backward 实际可用性未运行验证；不能据注册面推翻文档口径，也不能据文档断言注册面失效。
2. **输出 dtype 来源互不相同**：kl_div/l1_loss 按 result_type 提升，bce_with_logits 取 target dtype，bce/soft_margin 取 self dtype——同为二元损失，显式 out/grad_input 重载缺 dtype 注时按生成器缺省自洽，不自动继承同族其他入口的提升规则。
3. **soft_margin_loss 的两条路径输出形状可不同**：aclops 回退先 `npu_broadcast(target, self.sizes())` 物化 target（host 广播副本），输出按 `soft_margin_loss_npu_output_size`（None 时=input_same_output_size(self)，**self 形状**）；gen 直发路径输出取 broadcast(self,target)。self 与 target 形状不同且广播形状大于 self 时，两条路径输出 shape 不同。aclops 反向以 `apply_tensor(input)` 申请、无逐输入广播校验；gen 反向按三输入广播定形。aclops 另把 reduction 转字符串 attr 传命令、非 None 时 `result.reshape({})`；gen 直发把 int reduction 原样传 aclnn。

multilabel_margin_loss 的 aclops 实现是纯 aten 组合（委托 multilabel_margin_loss_forward，is_target 按 target 申请），与 MultiMargin 小节的 functional 入口提示互补；multi_margin_loss 实现未核对，不在本节核对。主线与发布两版本 差异：四组损失的 yaml/derivatives 条目同语义；SoftMarginLoss/SoftMarginLossBackward/LossKernelNpu 的 aclops 文件仅排版差异。

### KL/BCE/L1/SoftMargin 补充证据

- [SoftMarginLossKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SoftMarginLossKernelNpu.cpp)（implementation）：1–66；完整本地小文件。
- [SoftMarginLossKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SoftMarginLossKernelNpu.cpp)（implementation）：1–68；仅排版差异。
- [SoftMarginLossBackwardKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SoftMarginLossBackwardKernelNpu.cpp)（implementation）：1–72；完整本地小文件。
- [SoftMarginLossBackwardKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SoftMarginLossBackwardKernelNpu.cpp)（implementation）：1–74；仅排版差异。
- [LossKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LossKernelNpu.cpp)（implementation）：1–35；完整本地小文件（multilabel_margin_loss 组合）。
- [LossKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LossKernelNpu.cpp)（implementation）：1–31；仅排版差异。
- [derivatives.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml)（implementation）：42–63；仅 bce_with_logits/kl_div/l1_loss 三条反向公式。
- [derivatives.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml)（implementation）：42–63；同三条，与主线文字相同。
- [KernelNpuOutputSize.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：1355–1365；仅 soft_margin_loss_npu_output_size helper（该文件已列于 frontmatter 来源）。
- [KernelNpuOutputSize.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：1204–1214；同 helper，语义相同（该文件已列于 frontmatter 来源）。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：1404–1441、2863–2876、2890–2897、4801–4831、5795–5810、5983–5990；仅本节四组损失 Schema 条目（该文件已列于 frontmatter 来源）。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：1354–1387、2777–2786、2804–2811、4647–4680、5555–5580、5734–5741；同组条目（该文件已列于 frontmatter 来源）。

## multi_margin_loss 的负向确认：OpPlugin 主线与发布两版本 无实现无注册

据实定案：`multi_margin_loss` 在主线与发布两版本 的 `op_plugin_functions.yaml`（official/custom/autograd/symint/quant 各节）**均无任何条目**；主线与发布两版本 的 `op_plugin/` 与 `torchnpugen/` 源树全树 rg 亦无 `multi_margin` 字符串（无 aclops/opapi 手写或生成条目）。因此 OpPlugin 层不存在该算子的 NPU 实现或注册，前文 MultiMargin 小节的文档表结论（F.multi_margin_loss 列三类产品、类的 FP32/FP64 input 与可能回退提示）**不能由来源源码认证为 NPU 直执行**；其实际分派路径（ATen 组合、CPU 回退或其他后端）未核对，不在此推断。同名前缀的 multilabel_margin_loss（前向/反向四名）已由前节核对，两者不能互推。

### multi_margin_loss 负向证据

- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：全文件条目名扫描（entry parser 覆盖 official/autograd/custom/symint/quant 各节）；multi_margin_loss 零命中，multilabel_margin_loss 族位于 3660–3673（该文件已列于 frontmatter 来源）。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：同扫描，multi_margin_loss 零命中（该文件已列于 frontmatter 来源）。
- 主线与发布两版本 `op_plugin/`、`torchnpugen/` 树 `rg 'multi_margin'` 零命中（负向扫描，无对应源文件可列）。
