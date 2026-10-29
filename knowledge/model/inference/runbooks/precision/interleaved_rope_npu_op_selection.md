---
type: Runbook
title: 交错 RoPE 必须用 npu_interleave_rope，通用 RoPE 融合算子替换会破精度（cos_sim≈0）
description: 交错 RoPE 必须用 npu_interleave_rope，通用 RoPE 融合算子替换会破精度（cos_sim≈0）。在昇腾上做融合算子替换时，把手写的交错（interleaved）RoPE 换成通用 RoPE 融合算子 torch_npu.npu_rotary_mul / npu_apply_rotary_pos_emb，输出完全对不上——评估报告观测替换后 cos_sim ≈ 0（相当于随机），token 匹配失败。这不是算子 bug，是算子选型错：通用 RoPE 算子不支持交错排布。
tags:
- task.debugging
- topic.attention
- topic.precision
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/328
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-22T10:43:19Z'
platforms:
- agnostic
---

# 交错 RoPE 必须用 npu_interleave_rope，通用 RoPE 融合算子替换会破精度（cos_sim≈0）

## 信号（现象）

在昇腾上做融合算子替换时，把手写的**交错（interleaved）RoPE** 换成通用 RoPE 融合算子 `torch_npu.npu_rotary_mul` / `npu_apply_rotary_pos_emb`，输出**完全对不上**——评估报告观测替换后 `cos_sim ≈ 0`（相当于随机），token 匹配失败。这不是算子 bug，是**算子选型错**：通用 RoPE 算子不支持交错排布。

## 触发条件

模型用交错 RoPE（interleaved：相邻维两两配对旋转），排布与常规 rotate_half RoPE 不同。凡把这类 RoPE 替换成假设 rotate_half 排布的通用融合算子，就会算错。观测于 LongCat-Flash-Lite 的优化报告（`RoPE(interleaved)` 尝试用 `npu_rotary_mul` / `npu_apply_rotary_pos_emb` 替换 → 均不支持本模型交错 RoPE、cos_sim 约 0，故跳过）。

## 根因

交错 RoPE 与 rotate_half RoPE 的维度配对/旋转排布不同。通用 RoPE 融合算子按 rotate_half 语义实现，喂交错排布的 Q/K 会做错误的两两旋转，结果发散。

## 修法（算子选型规则）

- **交错 RoPE → 用专用算子 `torch_npu.npu_interleave_rope`**（针对单输入 `x` 的旋转位置编码，op-plugin 7.3.0 起）。[MLA](../../concepts/modules/mla.md) absorb 路径的 Q RoPE 即用它：

  ```python
  # module-attention-mla-absorb.md, Prefill 链路
  q_pe = npu_interleave_rope(q_pe, cos, sin)
  ```

- **不要**用 `npu_rotary_mul`（通用 RoPE，二维平面旋转）/ `npu_apply_rotary_pos_emb` 去替换交错 RoPE。
- 正例：LongCat-Flash-Lite「使用 skill」优化报告记录 `apply_rotary_pos_emb_interleave → npu_interleave_rope` 替换成功（cos_sim 0.9998，token 20/20 匹配）。
- 相关算子（MLA 场景）：`npu_kv_rmsnorm_rope_cache`（MLA 的 RMSNorm+RoPE+KVCache 三合一）。

## correctness 验证

替换任何 RoPE 融合算子后，都用小样本比对 cos_sim / token 匹配：固定 LongCat-Flash-Lite 缩减模型报告的 cos_sim≈0.9998 仅是来源个例，不作通用阈值。应在明确输入、dtype、形状和模型条件下对照参考实现，预先定义数值误差与任务质量验收标准；明显偏离时回查交错布局及算子参数。

## 适用边界

限交错 RoPE 模型的 NPU 算子选型（[deepseek-r1](../../concepts/models/deepseek_r1.md)、[longcat-flash-lite](../../concepts/models/longcat_flash_lite.md) 等 MLA/interleaved-RoPE 族）。正向断言（交错 RoPE 用 `npu_interleave_rope`）为 diff 事实 + 算子文档；负向失败观测（通用算子 cos_sim≈0）来自 PR 附带的 LongCat 评估报告（作者 agent 自述观测、缩减模型、无独立复测）。

## 相关经验
- [昇腾多模态 M-RoPE 优先走 triton-ascend triton_mrope，de](../../optimizations/rules/mrope_triton_ascend_vs_npu_mrope_decode.md)

## Evidence

- **代码事实**（clone `@73ed847`）：`.agent/skills/torch-npu-fusion-optimizer/references/module-attention-mla-absorb.md` 实际用 `npu_interleave_rope`；`torch_npu_API/torch_npu_list.md` 列 `npu_interleave_rope`（专用交错 RoPE）、`npu_rotary_mul`（通用 RoPE 二维平面旋转）。正向断言为 diff 事实 + 算子清单。
- **报告披露**：负向 cos_sim≈0 来自 PR 附带的 LongCat-Flash-Lite 评估报告（作者 agent 自述观测、缩减模型、无独立复测）。
- 溯源下探：[cann-recipes-infer-pr-328-feat-add-agent-optimization-skills-and-evaluation-reports](https://gitcode.com/cann/cann-recipes-infer/merge_requests/328)