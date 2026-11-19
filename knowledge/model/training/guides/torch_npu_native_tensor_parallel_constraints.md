---
type: Guide
title: 原生张量并行的dtype与950损失精度边界
description: 说明ColwiseParallel和loss_parallel支持表条件，区分整数输入名单与logits类型、模块布局和产品遗漏。
tags:
- task.optimization
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-distributed-tensor-parallel.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-distributed-tensor-parallel.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-distributed-tensor-parallel.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-distributed-tensor-parallel.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-distributed-tensor-parallel.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-distributed-tensor-parallel.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-distributed-tensor-parallel.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/dtensor_supported_apis.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-distributed-tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-distributed-tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-distributed-tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-distributed-tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-distributed-tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-distributed-tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-distributed-tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-distributed-tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-distributed-tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-distributed-tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-distributed-tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-distributed-tensor.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-distributed-tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-distributed-tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-distributed-tensor-parallel.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-distributed-tensor-parallel.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-distributed-tensor-parallel.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-distributed-tensor-parallel.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-distributed-tensor-parallel.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-distributed-tensor-parallel.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-distributed-tensor-parallel.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/private_apis.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/private_apis.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/dtensor_supported_apis.md
  role: constraint
created_at: '2026-11-09T07:31:16Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# 原生张量并行的dtype与950损失精度边界

## 固定来源与版本边界

依据PyTorch仓主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的原生支持页。页面分别对应PyTorch 2.7.1、2.9.0、2.10.0、2.11.0、2.12.0、2.13.0、2.14.0，相关条目的限制文本已逐版本提取核对；这不是同一安装包同时兼容所有版本的证明，也不补出未列出的2.8行为。

产品页确认A2/A3训练系列及950DT的下列条目。仅以固定来源记录已声明范围与实现边界，未运行上游代码、训练或设备实验；来源文档的“已验证”不作为本卡新增 verified 事件。

## 核对具体并行入口

七个版本ColwiseParallel条目均只列BF16/FP16/FP32 input；不能因为RowwiseParallel或parallelize_module相邻条目无同一句限制，就推定所有组合的dtype、布局与分片均相同。支持表不是一个可直接执行的完整TP方案，需要与模型分片和通信域一起核对。

loss_parallel条目的input名单为BF16/FP16/FP32/INT64。它是并行损失上下文，并非每个输入位置都可任意选择该名单：尤其不能据INT64出现在总名单就宣称整数logits支持，或对浮点logits、目标索引统一做dtype转换。该页未给出更细的参数位置映射，不补造。

## 大logits与产品范围

七个版本均提示950DT在logits数值特别大时，精度可能与A2/A3训练系列不同；来源没有给定通用数值阈值或误差上限。不能从某次小logits测试通过推出大数值区间也一致，跨产品验收需要保留logits范围、dtype与loss/梯度误差。

2.14的parallelize_module、RowwiseParallel、SequenceParallel、ColwiseParallel及loss_parallel列A2/A3/950DT；PrepareModuleOutput仅列A2/A3。中文未列950表示该清单未纳入该产品验证，英文的显式排除另见后文；不能由其他TP组件列支持就自动补全。

## 验证与集成

按目标PyTorch版本固定DeviceMesh、参数/输入分片、局部输出与损失reduction，再与单卡或非分片参考比较前向及梯度。覆盖正常与大幅度logits、BF16/FP16/FP32及整数目标索引，分别记录通信时间与端到端收益。

支持表说明不定义进程组资源/生命周期和端到端图支持；[FSDP/DDP适配](torch_npu_ddp_fsdp_adaptation.md)和[原生集合通信限制](torch_npu_native_collective_constraints.md)中的条件应分别核对，不能只因同属distributed就相互替代。

## DTensor名单不等于任意分片组合

同一主线dtensor_supported_apis页把DTensor定义为基于DeviceMesh与Shard/Replicate/Partial的SPMD张量抽象，并列出已经纳入来源验证的API；未列入口只是尚未纳入，不能直接视为不支持。这个名单未逐项给产品/dtype/layout矩阵，因此也不能用一张统一名单给所有产品补全这些条件。

与模型优化相关的已列入口包括matmul/mm/bmm、linear、embedding、layer_norm及原生torch._fused_adamw_，自定义入口包括npu_apply_adam_w、npu_add_rms_norm/npu_rms_norm、npu_fusion_attention、npu_all_gather_base_mm/npu_mm_reduce_scatter_base、npu_grouped_matmul及npu_grouped_matmul_add_、npu_moe_token_permute/unpermute、npu_rotary_mul和npu_swiglu。名字在名单中不证明所有Shard/Partial组合、本地shape、梯度、图模式和下游融合都有效；依旧按具体接口与模型布局核对。

该页的“已验证”是上游支持声明，本卡没有执行 DTensor 测试，也不因此添加本地verified事件；本文按名单与具体接口分别记录消费边界，完整名称交叉表见后文；名单完整不等于全部API组合已验证。

## DTensor对象与分发操作的独立类型表

同一主线七版本中英文torch.distributed.tensor页对DTensor及from_local列BF16/FP16/FP32/FP64、UINT8/INT8/INT16/INT32/INT64、BOOL、COMPLEX64/128；Shard的表少INT16。redistribute、distribute_tensor及_StridedShard则只列BF16/FP16/FP32/FP64、UINT8/INT8/INT32/INT64、BOOL，没有INT16和复数。不能由构造器或局部Tensor的较宽表推定分发/重分布支持同样类型；distribute_module的input仅列BF16/FP16/FP32。

DTensor主条目及from_local/redistribute、Shard/Placement及is_replicate/is_shard、分发函数均列三类产品。中文还列full_tensor/to_local、Replicate和debug.CommDebugMode的三类产品，英文未全部收录；placements属性中文仅列A2/A3，不由对象父表补950。_StridedShard只在2.11..2.14收录；名字为私有形式，清单不保证跨版本稳定。

experimental.context_parallel在中英文七版本只允许NPU fused SDPA，q/k/v限定BNSD；不支持pse、padding_mask、prefix、actual_seq_qlen、actual_seq_kvlen、sink及任意非causal attention mask；开启load balance要求causal attention，不支持torch.compile成计算图。这是该context_parallel入口的限制，不推广到所有上下文并行框架，也不能从DTensor整体支持推导其可编译。

上述对象表不定义DeviceMesh和本地shape/布局的完整合法组合。与其他TP、FSDP、SDPA路线组合时，分别检查分片通信、实际接口、输出与梯度，不能以类支持或创建成功作为通信和训练等价的证明。

## 英文TP输入准备和输出范围

同提交七份英文TP页对PrepareModuleInput明确三类产品均不支持，中文未列；PrepareModuleOutput中文仅列A2/A3，英文明确950不支持，不能由parallelize_module或RowwiseParallel支持补这两个准备对象。SequenceParallel只在中文列三类产品，英文未收录。前述ColwiseParallel和loss_parallel局部dtype与大logits精度说明两侧一致，不由语言缺项扩展任意分片或预处理组合。

## 完整DTensor名单与私有局部对象

中英文DTensor清单均完整列186个入口；与181项入图名单的逐名交叉及所有差集已归于[入图与DTensor能力表](../../inference/guides/optimization/torch_npu/torch_npu_native_graph_dtensor_capabilities.md)。这补齐名单本身，不证明未列出的placement、形状、反向或组合合同；两种支持声明仍独立。

同提交private_apis对distributed.tensor._redistribute.redistribute_local_tensor列BF16/FP16/FP32/FP64、UINT8、INT8/32/64、BOOL，对DTensor._local_tensor另加INT16和COMPLEX64/128，两侧列三产品。placement_types._StridedShard列前一较窄类型，中文列三产品、英文明确950不支持，并称自PyTorch2.11开始改为公开接口。保留这条版本说明及私有拼法，不由公开Shard或父类支持消除双语分歧，也不将局部Tensor表扩大到重分布。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-distributed-tensor-parallel.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-distributed-tensor-parallel.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-distributed-tensor-parallel.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-distributed-tensor-parallel.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-distributed-tensor-parallel.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-distributed-tensor-parallel.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-distributed-tensor-parallel.md)（primary）

- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/dtensor_supported_apis.md)（constraint）

- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-distributed-tensor.md)（constraint）

- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-distributed-tensor.md)（constraint）

- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-distributed-tensor.md)（constraint）

- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-distributed-tensor.md)（constraint）

- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-distributed-tensor.md)（constraint）

- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-distributed-tensor.md)（constraint）

- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-distributed-tensor.md)（constraint）

- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-distributed-tensor.md)（constraint）

- [固定来源 17](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-distributed-tensor.md)（constraint）

- [固定来源 18](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-distributed-tensor.md)（constraint）

- [固定来源 19](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-distributed-tensor.md)（constraint）

- [固定来源 20](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-distributed-tensor.md)（primary）

- [固定来源 21](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-distributed-tensor.md)（constraint）

- [固定来源 22](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-distributed-tensor.md)（constraint）

- [固定来源 23](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-distributed-tensor-parallel.md)（constraint）

- [固定来源 24](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-distributed-tensor-parallel.md)（constraint）

- [固定来源 25](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-distributed-tensor-parallel.md)（constraint）

- [固定来源 26](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-distributed-tensor-parallel.md)（constraint）

- [固定来源 27](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-distributed-tensor-parallel.md)（constraint）

- [固定来源 28](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-distributed-tensor-parallel.md)（constraint）

- [固定来源 29](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-distributed-tensor-parallel.md)（constraint）

- [固定来源 30](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/private_apis.md)（primary）

- [固定来源 31](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/private_apis.md)（constraint）

- [固定来源 32](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/dtensor_supported_apis.md)（constraint）
