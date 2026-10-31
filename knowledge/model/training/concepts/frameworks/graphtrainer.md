---
type: Concept
title: GraphTrainer：联合训练图中的通信与计算调度
description: 区分联合 FX 图、SimpleFSDP、Profile-aware EP 调度和图级 CV 并行，并说明 ChunkLoss 梯度归约合并的适用路径。
tags:
- task.design
- topic.graph_execution
- topic.parallelism
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/ascend950/graphtrainer.md
  role: primary
created_at: '2026-10-29T04:09:06Z'
updated_at: '2026-10-29T15:39:13Z'
platforms:
- '950'
---

# GraphTrainer：联合训练图中的通信与计算调度

## 联合训练图

GraphTrainer 捕获前向、Loss 和反向为联合 FX 图，通过 SimpleFSDP 把参数 AllGather 与梯度 ReduceScatter 显式放入图中，使重计算、激活保存和通算顺序可一并分析。TorchTitan-NPU 在该基础上增加重计算、EP 通信重排和图级 CV 并行 pass。

## 两类调度

EP overlap 将 MoE 划为两个 chunk，让一个 chunk 的计算覆盖另一个的通信。Profile-aware 调度用目标设备的单算子测量建立初始 cost model，再以完整图的并发测量校准，依赖图约束节点移动，各 rank 保持相同通信顺序。单算子成本不能完全预测并发后的资源竞争。

CV 并行把两个 chunk 放到两条计算流，按资源类型、依赖和测得耗时安排 Cube 与 Vector 窗口。它是跨算子的图级调度，不等同于算子内部的 Cube–Vector 融合。

## ChunkLoss 的通信边界

固定文档覆盖使用 FP32 主参数与 FP32 梯度归约、满足约束的一维 SimpleFSDP Linear head 路径：同一 microbatch 的 loss chunk head 梯度先用 FP32 本地累加，再统一一次 ReduceScatter。它保留分块 logits 的显存动机，并减少重复归约；跨 microbatch 的梯度累加语义不变。其他路径继续用原实现，不能把它泛化为任意 Chunk Loss 都只有一次通信。

## 适用边界与验证

新模型先验证 batch/sequence 可拆分性、metadata 和梯度语义，再测资源重叠、通信暴露、显存与实际 TPS。改变模型规模、shape 或算子实现后重新采样。文档中整网吞吐、未掩盖通信降幅和计算并集缩短来自不同实验，不能直接相加。

源文档中的 QoS 自适应带宽调度属于未来规划。本批未执行图编译、训练或性能复测。基础分块损失见 [Chunk Loss](../techniques/chunk_loss.md)。
