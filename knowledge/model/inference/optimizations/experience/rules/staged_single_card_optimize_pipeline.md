---
type: Optimization
title: 单卡 NPU 推理优化的三阶段固定流程：KVCache 静态化+FA 替换 → torch_npu 融合算子替换 → GE 图模式(仅 decode)，每阶段精度+性能 gate
description: 单卡 NPU 推理优化的三阶段固定流程：KVCache 静态化+FA 替换 → torch_npu 融合算子替换 → GE 图模式(仅 decode)，每阶段精度+性能 gate。对一个已能在昇腾单卡跑通的模型做推理优化（提性能、不破精度）时，按一条固定分阶段流程推进——每阶段有独立的精度+性能验证 gate，按序不可跳过/不可并行。这给优化 agent 一个可复用的动作序列与验收关口，避免一次性堆改动导致精度/性能问题难定位。
tags:
- task.optimization
- topic.attention
- topic.graph_execution
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/328
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 单卡 NPU 推理优化的三阶段固定流程：KVCache 静态化+FA 替换 → torch_npu 融合算子替换 → GE 图模式(仅 decode)，每阶段精度+性能 gate

## 适用场景

对一个已能在昇腾单卡跑通的模型做**推理优化**（提性能、不破精度）时，按一条**固定分阶段流程**推进——每阶段有独立的精度+性能验证 gate，**按序不可跳过/不可并行**。这给优化 agent 一个可复用的动作序列与验收关口，避免一次性堆改动导致精度/性能问题难定位。

## 三阶段（按序、每阶段过 gate 才进下一阶段）

1. **阶段一：KVCache 静态化 + FA 替换**。把 KV cache 改为静态形状、注意力换成昇腾 [FlashAttention 融合算子](../../../concepts/kernels/fused_infer_attention_score.md)。过精度 gate（与基线对齐）+ 性能 gate 后进下一阶段。
2. **阶段二：torch_npu 融合算子替换（Attention 之外）**。把 Attention 以外的原生小算子（norm/rope/激活/matmul 组合等）换成 torch_npu 融合算子。同样过精度+性能 gate。
3. **阶段三：GE 图模式适配（仅 Decode）**。把 decode 路径适配到 [GE 图模式](../../../concepts/techniques/npu_graph_mode.md)（prefill 不做）。过 gate 收尾。

## 为何分阶段 + gate

- 每阶段只引入一类改动，出问题能立刻定位到该阶段；
- 精度 gate 防止某步优化静默破精度被后续阶段掩盖；
- 顺序有依赖（先静态化/FA 才好上融合算子，先融合算子稳定再上图模式），故不可跳过/并行。

## 参考实现

参考 cann-recipes-infer 的 `model-optimize` agent skill——它把上述三阶段流程与每阶段的精度/性能验证固化为可执行的优化脚本序列。

## 风险 / 边界

- 阶段三仅 Decode 适配图模式；prefill 上图模式不在此流程内。
- 这是单卡推理优化流程；多卡并行优化是另一套（并行选型见相关经验）。

## 相关经验

- 注意力换 FIA 的 sparse_mode 细节见 [attention-to-fia-sparse-mode-sink-window](attention_to_fia_sparse_mode_sink_window.md)。
- 多卡并行/平台部署选型见 [ascend-deploy-parallel-variant-and-nondefault-platform](ascend_deploy_parallel_variant_and_nondefault_platform.md)。

## Evidence

- `diff 事实`（@73ed847）：`model-optimize` skill 规定三阶段（KVCache 静态化+FA → torch_npu 融合算子替换 → GE 图模式仅 Decode）、每阶段精度+性能 gate、按序不可跳过/并行。
- 溯源下探：[cann-recipes-infer-pr-328-feat-add-agent-optimization-skills-and-evaluation-reports](https://gitcode.com/cann/cann-recipes-infer/merge_requests/328)

<!-- cannbot:related:start -->
## 相关

- [KVCache 静态化 + FA / FIA 融合算子替换的精度陷阱](../../../runbooks/precision/precision_kvcache_fa_fusion_pitfalls.md)（`related`）：# 单卡 NPU 推理优化的三阶段固定流程：KVCache 静态化+FA 替换 → torch_npu 融合算子替换 → GE 图模式(仅 decode)，每阶段精度+性能 gate；把手写 attention 换成 ［npu_fused_infer_attention_score］(../../concepts/kernels/fused_infer_attention_score.md)(FA/FIA) 融合算子 + 静态 KVCache 后，Prefill 对但 Decode 偏、输出全重复 token / 乱码、多 batch 部分样本错、量化模式偏差放大。这类精度问题几乎都出在 **FA 入参与 layout 约定、KVCache 写入位置、KV 长度语义**上，而非注意力数学本身。按症状对号入座定位。。三阶段流程把静态 KVCache 与 FA 替换列为第一阶段，精度 Runbook 给出替换后 Decode 偏差、重复 token 等症状及其入参、layout 和写入位置根因，构成该阶段精度 gate 的排障依据。
- [NPU LLM 图模式启用骨架：decode-only 编译 + ge_graph / acl_graph / npugraph_ex 后端编译入口与配置约束](graph_mode_decode_only_compile_backends.md)（`related`）：# 单卡 NPU 推理优化的三阶段固定流程：KVCache 静态化+FA 替换 → torch_npu 融合算子替换 → GE 图模式(仅 decode)，每阶段精度+性能 gate；实现上把 prefill / decode 的 forward 拆成不同方法，**只对 decode 方法** `torch.compile(...)`，prefill 保持 eager。前置条件：decode 侧须为静态 shape——KV cache 预分配为连续张量、batch 定形填充、前向用就地写（`scatter_update_` 等）更新 KV。连续 KV + 定形 batch 是图捕获的前提。。三阶段流程把 GE 图模式限定在 Decode，候选进一步给出拆分 forward、仅编译 Decode 及连续 KV 与定形 batch 的捕获前置条件，可直接落实第三阶段。
- [把注意力映射到昇腾 FIA：attention sink / 滑窗 / 全窗的 sparse_mode 选择 + 推理 FIA vs 训练 FA + GQA 头数](attention_to_fia_sparse_mode_sink_window.md)（`related`）：# 单卡 NPU 推理优化的三阶段固定流程：KVCache 静态化+FA 替换 → torch_npu 融合算子替换 → GE 图模式(仅 decode)，每阶段精度+性能 gate；在昇腾上把各类注意力（含 attention sink、滑动窗口、全窗因果）落到融合算子时，优先整段映射到 ［FIA］(../../../concepts/kernels/fused_infer_attention_score.md)（`npu_fused_infer_attention_score` / `_v2`），用 `sparse_mode` + 入参承接各种注意力变体，而不是在 softmax 前后手拼逻辑。。三阶段流程要求先替换 FA/FIA 融合算子，候选给出 attention sink、滑窗和全窗因果映射到 FIA 时的 sparse_mode 与入参承接原则，补充第一阶段的具体算子落地。
<!-- cannbot:related:end -->
