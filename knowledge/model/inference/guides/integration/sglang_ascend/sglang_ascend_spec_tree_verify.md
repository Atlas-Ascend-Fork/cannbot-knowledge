---
type: Guide
title: SGLang Ascend Eagle树验证：树元数据与采样能力分派
description: 说明NPU树构建、贪心验证及可选采样kernel的调用契约，区分topk树路线、线性rejection和DFlash额外限制。
tags:
- task.implementation
- topic.speculative_decoding
- topic.model_adaptation
- topic.precision
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/kernels/ops/speculative/spec_tree.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/kernels/ops/speculative/verify_sampling.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/speculative/eagle_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/arg_groups/speculative_hook.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/speculative/dflash_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/sample/verify_tree_greedy.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/speculative/eagle_info.py
  role: implementation
created_at: '2026-11-08T12:08:04Z'
updated_at: '2026-11-09T04:33:25Z'
platforms: []
aliases:
- build_tree_kernel_efficient NPU
- verify_tree_greedy NPU
---

# SGLang Ascend Eagle树验证：树元数据与采样能力分派

## 树构建与贪心验证

NPU树构建调用torch.ops.npu.build_tree_kernel_efficient，将parent_list转int64，传入top_scores_index、seq_lens、tree_mask、positions及retrieve index/token/sibling可变buffer。topk、spec_steps、num_verify_tokens和tree_mask_mode共同决定树几何，不能只调整候选token数而不重建树索引。

贪心验证导入sgl_kernel_npu.sample.verify_tree_greedy，写predicts、accept_index与accept_token_num；外部ABI保留拼写retrive_*，仓内变量可叫retrieve_*，不能因拼写统一而破坏关键字调用。accepted index 是 flat 行，accept 长度与后续 bonus 位置仍需上层解释。两个固定源码快照配套静态核对存在限制：sgl-kernel-npu kernel 仅顺序比较 candidates[i] 与 target[i-1]，不沿子节点/兄弟指针遍历，且以 num_draft_tokens 作为 accept_index 行跨度；SGLang 按 max_tree_depth=spec_steps+1 分配该输出。分叉树节点数可不同于深度，存在遍历语义与输出布局风险。可确认的匹配语义应限定在线性链且节点排列、输出行宽与 kernel 跨度一致的条件，不能视为通用树验证。这两个快照没有已确认的发布 wheel 绑定，实际安装版本与输出 ABI 须单独核对。

## 可选采样与拒绝边界

verify_sampling在NPU尝试导入chain_speculative_sampling_triton与tree_speculative_sampling_target_only，缺包时设None，不伪造可用能力。采样流程须先应用请求temperature/top_k/top_p等目标分布调整，再按实际算法选择target-only或经典rejection；经典rejection flag被启动guard限制为topk1线性链，不能用于树。

DFlash即使能导入target-only kernel，也在自己的utils明确禁止NPU非贪心验证；DSpark有独立链采样路径。不能用“同一个sample包存在”推断不同worker的产品语义一样。block verification同样有设备guard，NPU拒绝。

## 验证

对线性与树分别核对mask允许语义、parent/sibling可达性、flat accepted index、bonus和后续cache提交；覆盖缺可选kernel、全接受/首步拒绝及grammar mask。仅本轮token匹配不够，需比较下轮状态。本次未运行采样分布或树算子测试，未声称完整Device实现闭包。
