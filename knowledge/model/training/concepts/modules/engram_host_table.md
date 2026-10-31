---
type: Concept
title: Engram 训练：Host 记忆表、稀疏更新与联合分片
description: 说明 950 Engram 训练的按行访问、CPU SparseAdam、EP×EFSDP 分片及 MXFP8 查表副本，区分稀疏计算和完整优化器状态内存。
tags:
- task.design
- topic.memory
- topic.optimizer
- topic.model_architecture
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/ascend950/engram.md
  role: primary
created_at: '2026-10-29T04:09:05Z'
updated_at: '2026-10-29T15:39:13Z'
platforms:
- '950'
---

# Engram 训练：Host 记忆表、稀疏更新与联合分片

## 数据与职责

固定文档中的 Engram 由局部 N-gram 和多头哈希生成行 ID，检索向量经投影、上下文门控后加入隐状态。packed sequence 的 N-gram 构造须遵守文档边界。

FP32 主表与 CPU SparseAdam 状态驻留 Host；前向只取命中行，反向按所属分片归并行梯度，计入全局范数和裁剪，再更新命中行。AscendC Fetch/FetchGrad 负责查表与梯度通信，哈希、门控、优化器和量化副本刷新由框架承担。训练态的稳定锁页表地址注册不表示后续查表无需搬运。

## 分片与内存

默认沿 EP 切表、沿 EFSDP 保留副本；联合分片把持有比例从 1/EP 降为 1/(EP×EFSDP)。额外的数据并行维度仍可能复制表。超节点互联规模不等于单个算子的通信域上限。

设表元素数 P、分片数 S，每 rank 的 FP32 主表为 4P/S 字节，SparseAdam 两份 moment 为 8P/S。虽然只更新 K 个命中行，两份 moment 仍按完整本地表分配；初始化成本也保留。

## MXFP8 与版本边界

MXFP8 后端保留 FP32 主表，额外存储 E4M3 数据和每 32 元素共享的 E8M0 scale；格式平均约 1.03125 字节/元素。该比例是查表数据大小，不能当作训练总 Host 内存降幅。更新后仅刷新变化行，初始化及恢复时重建量化副本。

Torch、AscendC FP32、AscendC MXFP8 是不同访问后端，复用主表更新语义。950 文档中的 UB 表示 Unified Bus 系统互联，不是片上 Unified Buffer。

## 验证

核对重复行梯度合并、分片归属、主表/副本一致性、全局裁剪和同布局 checkpoint 恢复。来源将查表预取与计算重叠列为未来优化，本卡不把它作为已实现能力。本批未执行训练。
