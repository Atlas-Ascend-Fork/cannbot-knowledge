---
type: Optimization
title: attention 走 DP 时对 o_proj / dense-MLP 单独 TP：DP→TP→DP 边界通信省单卡内存与权重搬运
description: attention 走 DP 时对 o_proj / dense-MLP 单独 TP：DP→TP→DP 边界通信省单卡内存与权重搬运。decode 阶段 MLA/attention 因序列/内存布局采用 DP（每卡持全量 attention），但权重大的 o_proj、dense MLP 想做 TP 以省单卡内存、减权重搬运。此时 attention 与 MLP 并行域不同，需在边界插通信做 DP↔TP 域转换。
tags:
- task.optimization
- topic.attention
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/124
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-07-06T00:00:00Z'
platforms:
- a3
---

# attention 走 DP 时对 o_proj / dense-MLP 单独 TP：DP→TP→DP 边界通信省单卡内存与权重搬运

## 适用场景
- decode 阶段 [MLA](../../../concepts/modules/mla.md)/attention 因序列/内存布局采用 [DP](../../../concepts/parallelism/data_parallel.md)（每卡持全量 attention），但权重大的 o_proj、dense MLP 想做 [TP](../../../concepts/parallelism/tensor_parallel.md) 以省单卡内存、减权重搬运。此时 attention 与 MLP 并行域不同，需在边界插通信做 DP↔TP 域转换。

## 规则（可迁移手段）
- **o_proj 沿输入维（K 轴）TP**：o_proj 输入维 = `num_heads * v_head_dim`（需能被 TP size 整除），每 rank 只存一段输入通道权重。前向链路：`all_to_all` 让每 rank 只拿自己负责的输入特征段 → 本地 o_proj 线性 → `reduce_scatter` 按元素求和并在 batch 维切分。**仅在「o_proj TP>1 且 attn TP==1」（attention 在 DP）时启用此路径**。
- **dense MLP TP**：`gate_up_proj` 沿 N 轴切、`down_proj` 沿 K 轴切；因 attention DP、MLP TP，MLP 前 `AllGather`、后 `ReduceScatter`，完成 DP→TP→DP。
- **附带手段**：把 `gate_proj`+`up_proj` 合并为单个 `gate_up_proj` matmul（列并行）减少 matmul 次数。

## 取舍
- DP→TP→DP 引入额外通信，但 TP 化 MLP/o_proj 降单卡内存并减少 matmul 权重搬运，整体为正收益（仓自报、无独立 before→after 数字）。
- 跨模型迁移前须核对两点：o_proj 输入维（`num_heads * v_head_dim`）对 TP size 的整除性；attention↔MLP 的并行域切换点是否与该模型的算子布局吻合。

## 参考实现及其约束
- 参考 LongCat-Flash（Atlas A3）的 MLA + dense-MLP 建模路径：`o_proj_tp_size` 守卫下 `all_to_all_single`→本地 o_proj→`reduce_scatter_tensor` 链路、`gate_up_proj` 列并行合并、MLP 后 `reduce_scatter_tensor(..., group=dense_tp_group)`。适用面按证据限定到本仓该建模路径，不外推为通用规律。

## 相关经验
- [大 MoE 昇腾部署选型：并行形态/模型变体按集群规模选 + 非默认平台(310P/950)](ascend_deploy_parallel_variant_and_nondefault_platform.md)

## Evidence
- `diff 事实`（@0640521a8170）：`modeling_longcat_flash.py` 确认 `o_proj_tp_size` 守卫下 all_to_all→本地 o_proj→reduce_scatter 链路、`gate_up_proj` 列并行合并、MLP 后 `reduce_scatter_tensor`，与优化文档 o_proj_tp / MLP TP 章节一致；收益结论为 `doc 披露`（仓自报、无独立复测）。
- 溯源下探：[cann-recipes-infer-pr-124-feat-support-longcat-flash-inference](https://gitcode.com/cann/cann-recipes-infer/merge_requests/124)
