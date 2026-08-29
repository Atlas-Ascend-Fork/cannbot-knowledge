---
type: Optimization
title: decode 访存 bound 阶段的权重预取调度：按搬运 bound 大小排布相邻算子的预取顺序
description: decode 访存 bound 阶段的权重预取调度：按搬运 bound 大小排布相邻算子的预取顺序。decode 阶段某些算子（QuantBatchMatmul/QBMM、MLA_Prolog、matmul）性能受权重搬运带宽限制（访存 bound），且当前算子计算时存在可利用的空闲带宽——想用 权重预取 把下一批权重提前搬到 L2 Cache、让后续算子命中缓存而非等 HBM。
tags:
- task.optimization
- topic.attention
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/124
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/pull/3203
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-07-15T00:00:00Z'
platforms:
- a3
---

# decode 访存 bound 阶段的权重预取调度：按搬运 bound 大小排布相邻算子的预取顺序

## 适用场景
- decode 阶段某些算子（QuantBatchMatmul/QBMM、[MLA_Prolog](../../../concepts/kernels/mla_prolog.md)、matmul）性能受权重搬运带宽限制（访存 bound），且当前算子计算时存在可利用的空闲带宽——想用 [权重预取](../../../concepts/techniques/weight_prefetch.md) 把下一批权重提前搬到 L2 Cache、让后续算子命中缓存而非等 HBM。

## 规则（可迁移核心）
- **预取削搬运时延**：`npu_prefetch` 在当前算子计算的同时用空闲带宽把下一批访存 bound 算子的权重提前搬到 L2 Cache。
- **预取顺序按搬运 bound 大小排布，不是无差别每个都预取**：相邻算子共享有限的预取空间，当一个算子（如 MLA_Prolog，内含多个 matmul、搬运 bound 特别大）预取空间紧张时，**把预取空间让给它本身，而提前预取它的前置算子（QBMM）权重**——即「谁搬运 bound 更大谁优先占预取空间」。这是收益的关键判断，不是简单地给每个权重都加一句 prefetch。

## 前置 / 风险 / rollback
- 由 `enable_prefetch` 开关使能。
- 预取大小需按算子权重体量与 L2 容量标定，**过大反而挤占缓存**。
- rollback：`enable_prefetch: False` 关闭。
- 收益为文档定性披露（无独立 before→after 数字），不外推。

## 参考实现及其约束
- 参考 LongCat-Flash（Atlas A3）decode 路径：对搬运 bound 大的 MLA_Prolog 先预取其前置 QBMM 权重、为其腾预取空间。该排布是参考实现细节，迁移时按目标模型各算子的搬运 bound 与 L2 容量重新排预取顺序与大小。

## Evidence
- `diff 事实` + `doc 披露`（@0640521a8170）：`modeling_longcat_flash.py` 存在多处 `npu_prefetch(...)` 及为 MLA_Prolog 前置 QBMM 预取的排布，与优化文档「权重预取」章节一致（MLA_Prolog 搬运 bound 大、提前预取前置 QBMM 腾预取空间的取舍）；性能收益为文档定性披露、无独立数字。
- 溯源下探：[cann-recipes-infer-pr-124-feat-support-longcat-flash-inference](https://gitcode.com/cann/cann-recipes-infer/merge_requests/124)
- 相关：同 decode 阶段用多流 overlap 掩盖串行段见 [decode-multi-stream-overlap-core-balance](decode_multi_stream_overlap_core_balance.md)。

---

## 应用在 MoE：用 router/topk 计算掩盖专家 gate_up 权重预取，按 token 数门控、ratio 可 <1

### 适用场景
- MoE 前向里「路由（topk 选专家）→ 专家 GroupedMatmul」是串行依赖：专家权重体量大，等到 matmul 时才从 HBM 加载会暴露搬运时延；而路由计算本身访存轻、有空闲带宽。想把专家权重（gate_up，即 `w13`）在**路由阶段就发起预取**、在紧随其后的专家 matmul 阶段消费，用路由这段计算掩盖权重 HBM→L2 的搬运——这是把上文「预取削搬运时延」的思想落到 MoE 场景的一个具体排布点。
- 与本页第一段（attention/MLA 的 QBMM·MLA_Prolog 相邻算子预取排序）互补：那里排的是「相邻算子谁优先占预取空间」，这里排的是「预取点选在计算图哪一处发起、哪一处收口」，且引入两个 MoE 特有的门控维度。

### 规则（可迁移核心）
- **预取点 = 前一段访存轻的计算处，收口点 = 紧随其后的重访存 matmul 处**：preprocess（发起预取）挂在路由/选专家阶段开头，postprocess（收口）挂在专家 MLP 矩阵乘阶段开头，从而让权重搬运与路由计算在时间上重叠。
- **按每次 forward 的 token 数门控预取**：只有单次 forward 的 token 数达到阈值时才激活预取（小 token 数场景如极小 batch 的 decode 步不预取）——token 太少时 matmul 本身短、搬运掩盖收益小，预取反而是额外开销。这是 MoE decode 优化里「预取该不该开」的一个可迁移判断维度。
- **ratio 可以 <1，只预取权重的一部分**：`max_weight_size` 只取权重字节数的一个比例（预取部分而非全部），与 attention qkv/o 的整权重预取（ratio=1.0）区分——专家权重更大，预取全部会挤占 L2，只预取一部分即可掩盖到临界点。「预取比例是可调旋钮、不必等于 1」是关键认知。

### 前置 / 风险 / rollback
- 需要 forward context 能提供「当前层号 / 模型实例 / 权重张量」的取用入口，预取才能定位到下一层专家权重。
- 门控阈值与 ratio 都是需按硬件 L2 容量、专家权重体量、典型 token 数标定的旋钮；ratio 过大或阈值过低都会让预取挤占缓存或做无用功。
- 特性可通过预取配置关闭（rollback：关闭 MoE 权重预取即回到 matmul 时按需加载）。
- 收益为参考实现文档定性披露（"reducing L2 cache transfer latency"），无 before→after 数字，不外推加速比。

### 参考实现及其约束
- 参考 vllm-ascend（vLLM 昇腾后端）在量化 MoE 前向对 gate_up 权重加预取，面向 Qwen3MoE（Atlas A2）：
  - preprocess 挂在 `select_experts`（路由）开头调 `maybe_prefetch_moe_weight_preprocess(hidden_states, "gate_up")`，postprocess 挂在 `quant_apply_mlp`（专家 matmul）开头调 `maybe_prefetch_moe_weight_postprocess`；底层落到 `torch_npu.npu_prefetch(...)` 把权重搬进 L2。
  - token 门控固定为 `hidden_states.shape[0] >= 96`（`MOE_PREFETCH_TOKEN_THRESHOLD = 96`）；预取比例固定 `prefetch_ratio["moe"]["gate_up"] = 0.8`（只预取 80%），对比 attn qkv/o 的 ratio=1.0。这两个具体常量（96、0.8）是该参考实现的固定取值、源里无调优依据说明，迁移时应按目标硬件与模型重新标定，不照搬。
  - **可移植性代价**：权重取用走硬编码模块路径 `model_instance.model.layers[layer_idx].mlp.experts.w13_weight`——只对模块树匹配该布局的 MoE 模型生效；换到模块层级/命名不同的 MoE 模型需改这条取用路径。层索引 `layer_idx` 由预取 preprocess 内部 `+= 1` 隐式递进（依赖 forward context 维护的可变状态），扩展到别的调用点时需注意此隐式状态推进。这些都是该参考实现的限制、非「路由掩盖权重预取」这一技术本身固有。

### Evidence
- `merged diff 事实`（vllm-project/vllm-ascend@78777237a9ae95af88ce6068b000635f96aafe25）：`weight_prefetch.py` 新增 `moe` 的 `ModuleWeightPrefetchConfig`；preprocess 在 `experts_selector.py::select_experts`、postprocess 在 `moe_mlp.py::quant_apply_mlp`；`MOE_PREFETCH_TOKEN_THRESHOLD=96`、`gate_up` ratio=0.8、硬编码 `w13_weight` 取用路径、`layer_idx += 1` 均对上。收益为 PR 描述定性说法（"improves performance by reducing L2 cache transfer latency"）、无 benchmark 数字，故只记机制与门控取值、不主张加速比。
- 溯源下探：[vllm-ascend-pr-3203-2-n-feat-attention-and-moe-weight-prefetch-in-qwen3moe-models](https://github.com/vllm-project/vllm-ascend/pull/3203)
- 相关概念：[权重预取](../../../concepts/techniques/weight_prefetch.md)。

<!-- cannbot:related:start -->
## 相关

- [Weight Prefetch (npu_prefetch)](../../../concepts/techniques/weight_prefetch.md)（`related`）：该优化提供网络 weight 预取功能，在算子计算的同时，**利用空闲的带宽，提前将一些访存 bound 算子的权重从 HBM 搬运到 L2 Cache 中**，提升算子性能。；**预取顺序按搬运 bound 大小排布，不是无差别每个都预取**：相邻算子共享有限的预取空间，当一个算子（如 MLA_Prolog，内含多个 matmul、搬运 bound 特别大）预取空间紧张时，**把预取空间让给它本身，而提前预取它的前置算子（QBMM）权重**——即「谁搬运 bound 更大谁优先占预取空间」。这是收益的关键判断，不是简单地给每个权重都加一句 prefetch。前者定义 HBM 到 L2 的预取机制，后者把该机制落实为相邻算子间的空间分配与顺序决策。
- [decode 多流并行 overlap：模块级双流控核平衡 + 前处理子链切流](decode_multi_stream_overlap_core_balance.md)（`related`）：**预取顺序按搬运 bound 大小排布，不是无差别每个都预取**；两种可迁移的切法，按 overlap 粒度选：**模块级双流**（两个完整模块并行，需控核平衡）与**前处理子链切流**（把一个算子链拆到多流，需设计同步点）。；预取排序利用带宽空档，多流切分利用计算流水并行；两卡共同服务 decode 串行段压缩，但分别要求缓存容量排序与跨流依赖设计。
<!-- cannbot:related:end -->
