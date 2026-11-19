---
type: Guide
title: Lightning Indexer训练的稠密与稀疏阶段契约
description: 分开warmup稠密统计与稀疏KL路径，避免交换teacher/Indexer归一化信息或推导端到端图支持。
tags:
- task.implementation
- topic.attention
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dense_lightning_indexer_grad_kl_loss.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dense_lightning_indexer_softmax_lse.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_sparse_lightning_indexer_grad_kl_loss.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-09T07:18:58Z'
updated_at: '2026-11-09T07:18:58Z'
platforms:
- a2
- a3
- '950'
---

# Lightning Indexer训练的稠密与稀疏阶段契约

## 固定版本与范围

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的产品页、Schema和同提交C++/Meta；未执行上游实现、训练、图编译或设备实验，不回推发布基线。

## 选择训练阶段

稠密warmup使用[Indexer max/sum预计算](../apis/torch_npu/npu_dense_lightning_indexer_softmax_lse.md)，再把这两份统计连同主Attention的max/sum交给[稠密KL梯度接口](../apis/torch_npu/npu_dense_lightning_indexer_grad_kl_loss.md)。稀疏阶段则将实际稀疏索引和teacher统计交给[稀疏KL梯度接口](../apis/torch_npu/npu_sparse_lightning_indexer_grad_kl_loss.md)，后者没有那两份独立Indexer统计入参。

两条路径的规格不同：稠密teacher D=128且Nq=Nk；稀疏teacher D=512、Nk=1，Indexer D均128。不能只通过添加sparse_indices就把同一组teacher张量无条件切换两个接口。

## 统计属于哪一个评分空间

teacher max/sum对应主Attention评分，Indexer max/sum对应加权ReLU的Index评分。虽然都叫max/sum，二者shape、头聚合和归一化对象不同；先确认mask、左右因果对齐、RoPE、实际长度和scale一致，不能拿其他batch、稀疏集合或旧输入的统计复用。

max/sum是稳定Softmax的统计，不是argmax位置与token计数。若在上下文分片间合并，还需统一最大值参考点再汇总指数和，不能直接SUM不同局部参考点下的sum；本卡不提供这些接口未声明的CP通信配方。

## 梯度接线与图边界

两个KL入口显式返回dQindex、dKindex、dWeights及FP32[1] loss，teacher Q/K没有对应返回梯度。训练集成须对照实际自动微分适配核对梯度接线，不把一份数值loss视为完整主Attention反向已连通。

稀疏融合KL产品页明确不支持图；前置Indexer、Meta存在或别的Attention可成图，都不能推出整条训练流水可成图。长度也不是通用参数：这些KL/稠密LSE用SymInt[]累计列表，推理Indexer用INT32 Tensor累计/独立长度，按接口分别转换并核对每请求边界。

## 验证与收益验收

固定teacher与Indexer输入，比较两种评分归一化、KL和三份梯度，包含不等长、掩码尾部和精度组合；之后接真实训练检查梯度尺度与loss reduction。显存优化来自算子融合/统计拆分的设计目的，实际峰值需包括保存的teacher统计、临时空间、重计算和图开销，不能从输出只有四项估算收益。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dense_lightning_indexer_grad_kl_loss.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dense_lightning_indexer_softmax_lse.md)（supporting）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_sparse_lightning_indexer_grad_kl_loss.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
