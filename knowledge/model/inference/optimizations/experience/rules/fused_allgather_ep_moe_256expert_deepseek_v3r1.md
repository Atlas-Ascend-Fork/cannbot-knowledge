---
type: Optimization
title: 256-expert MoE 的融合 allgather-EP 专家链（四算子融合，硬门控在 finalize-routing 算子 + w2 须 FRACTAL_NZ）
description: 该规则把 EP MoE 的路由排序、w1 grouped matmul、反量化+SwiGLU+重量化、w2 grouped matmul 与 top-k 权重聚合压成四算子融合链，减少 decode 小 batch 下中间张量反复访问 HBM。vLLM-Ascend 的 W8A8 dynamic 路径仅在环境开关启用、ep_size>1 且模型为 256 专家的 DeepSeek V3/R1 时生效，因为 finalize-routing 融合算子不支持通用 MoE。启用前还须将 w2 转为 ACL_FORMAT_FRACTAL_NZ，并按 active_expert_range 切分本 rank 专家；AllGatherEP 路径跳过 TP pad 和常规 all_gather。当前只有 UT 覆盖，没有可信性能对比；关闭开关即可回退通用 MoE 实现。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.parallelism
- topic.precision
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/1335
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 256-expert MoE 的融合 allgather-EP 专家链（四算子融合，硬门控在 finalize-routing 算子 + w2 须 FRACTAL_NZ）

## 适用场景

在昇腾 NPU 上跑 **专家并行（EP）的 MoE 推理**，W8A8-dynamic 量化，`ep_size>1`，且遇到「路由 + 分组 matmul + 激活 + 按 topk 权重聚合」这一段用小算子拼接、中间张量在 HBM 反复往返、开销偏高的问题。可迁移的判断是：MoE 专家段这四步（token 路由排序 → grouped-matmul 上投影 → dequant+SwiGLU+重量化 → grouped-matmul 下投影并按路由权重加权聚合）在语义上可以合成一条**融合算子链**，省掉中间张量的落盘/回读；decode 这种 batch 小、访存受限的场景方向性收益更明显（未经实测量化，见 benchmark 节）。

关键前提是：能否用这条融合链，取决于是否存在一个**能把"下投影 + 按路由权重 finalize 聚合"融进单算子的融合算子**，以及权重布局是否满足该算子的约束。这条经验的可迁移内核是「四算子融合的思想 + 其硬门控/权重布局约束的存在性」；具体到当前唯一已知的参考实现，它被硬门控到极窄的模型/配置面上（见下节），所以判断是否落在本页范围内，先核对三点：EP 且 `ep_size>1`、W8A8-dynamic、以及模型是否落在参考实现支持的专家数上。

## 技术：四算子融合的专家链（通用知识）

标准 MoE 专家段在小算子实现下是一串独立算子，每步都要把中间张量写回 HBM 再读出：

1. **token 路由排序 / permute**：按每个 token 选中的 expert 把 token 重排、分组，得到每组的 token 段；EP 下每个 rank 只持有 `local_num_experts = global_num_experts / ep_size` 个专家，需要只对本 rank 负责的 expert 区间做路由切分。
2. **上投影 grouped-matmul（w1）**：对每组用对应专家的 w1 做分组 matmul。
3. **激活重量化**：dequant → SwiGLU → 重新量化，为下投影准备 int8 输入。
4. **下投影 grouped-matmul（w2）+ finalize 聚合**：对每组用 w2 做分组 matmul，再按 token 的 topk 路由权重把该 token 命中的多个专家输出加权求和、还原回原 token 顺序（finalize-routing）。

融合的思想是把这四步压成一条算子链，让每一步的输出直接留在片上/以内部形式流入下一步，尤其把"下投影 + 按路由权重聚合 + 还原 token 序"合进**一个 finalize-routing 融合算子**，从而消掉分组 matmul 输出和聚合中间量的 HBM 往返。为什么有效：MoE decode 段访存受限，中间张量的落盘/回读是主要开销，融合链把它们变成算子内部数据流；据此在 decode/小 batch 这类访存受限场景方向性收益更明显（未经实测量化，见 benchmark 节）。

这条技术不是免费的通用替换，它对**权重布局**和**finalize-routing 算子的能力面**有硬约束——下节的参考实现把这两个约束具象化，且明确它们是"该实现/该算子"的限制，不是融合思想本身的限制。

## 参考实现及其约束（vllm-ascend，W8A8-dynamic）

vllm-project/vllm-ascend 的 W8A8-dynamic 路径提供了一个可对照的实现：`fused_experts_with_allgather`，四算子链为

```
npu_dynamic_quant
  → npu_moe_init_routing_v2   # active_expert_range 做 EP 本 rank 切分, local_num_experts = global // ep_size
  → npu_grouped_matmul        # w1, 输出 int32
  → npu_dequant_swiglu_quant  # dequant + SwiGLU + 重量化
  → npu_grouped_matmul_finalize_routing  # w2; shared_input=zeros, logit=sorted_topk_weight, row_index, output_bs
```

通信侧：新增 `FusedMoEState.AllGatherEP`，与 `AllGather` 一样**跳过 TP pad 与 `dist.all_gather`**，forward 末尾走 `tensor_model_parallel_all_reduce`。

启用由 env `VLLM_ENABLE_FUSED_EXPERTS_ALLGATHER_EP`（默认 0）显式打开，且 `get_fused_moe_state(ep_size, with_prefill, is_deepseek_v3_r1)` 有三条门控：env 开、`ep_size>1`、`is_deepseek_v3_r1`（该实现里 `is_deepseek_v3_r1 = (global_num_experts == 256)`）。

**这些是该参考实现 / 其所用算子的约束，不是四算子融合思想本身的限制：**

- **模型面硬门控 = 算子能力面**：整条链的门控根因是它依赖的 `npu_grouped_matmul_finalize_routing` 融合算子**只支持 DeepSeek V3/R1**（代码注释原文），因此该路径不是通用 MoE 优化，被硬门控到 256-expert 的 DeepSeek V3/R1。换到别的 MoE 模型/专家数，得先确认有一个覆盖该配置的 finalize-routing 融合算子，否则这条链不成立。
- **量化面**：仅在 **W8A8-dynamic** 量化路径接入。
- **权重布局约束（易漏）**：启用前必须把 **w2_weight** 用 `npu_format_cast_` cast 成 **`ACL_FORMAT_FRACTAL_NZ`**（即 [weight NZ](../../../concepts/techniques/weight_nz.md) 布局），这是下投影融合算子对权重内存排布的前置要求；不做则算子不接受该权重。
- **开关面**：`ep_size>1` 且 env 显式打开，默认关闭。

## correctness 验证

参考实现随 PR 只给了单元测试（UT），配置为 DeepSeek-V3-Pruning、TP=16、`enable_expert_parallel`、`expert_tensor_parallel_size=1`、`enforce_eager`、V1 引擎。迁移或开启时，用同规格的 EP + W8A8-dynamic 配置跑 UT / 与非融合小算子路径逐 token 对拍输出，确认路由权重聚合与 token 还原顺序一致。

## benchmark

该参考实现**未提供 before→after 性能数据**（仅 UT，无 baseline/optimized 吞吐或时延）。收益方向来自"消掉 MoE 专家段中间张量 HBM 往返"的机理判断，落地时需自行在目标平台实测确认。

## 风险与 rollback

- 门控极窄：非 256-expert DeepSeek V3/R1 / 非 W8A8-dynamic / `ep_size==1` 时该路径本就不生效，不应强行接入。
- 忘记把 w2 cast 成 FRACTAL_NZ 会在算子入口失败，是最常见的接入错误。
- rollback 直接：env `VLLM_ENABLE_FUSED_EXPERTS_ALLGATHER_EP=0`（默认即关），门控回落到通用 MoE 专家路径，无需改权重加载逻辑（NZ cast 仅在该路径启用时才需要）。

## Evidence

- [vllm-ascend-fused-allgather-ep-moe-path-4-op-torch-npu-fusio](https://github.com/vllm-project/vllm-ascend/pull/1335) — 簇内 accept claim（原始事件源 [vllm-ascend-pr-1335-support-fused-moe-allgather-ep](https://github.com/vllm-project/vllm-ascend/pull/1335)）。
- vllm-project/vllm-ascend `@5177bef87a21331dcca11159d3d1438075cbd74e`：
  - `vllm_ascend/quantization/w8a8_dynamic.py::fused_experts_with_allgather` — 四算子链 `npu_moe_init_routing_v2 + npu_grouped_matmul + npu_dequant_swiglu_quant + npu_grouped_matmul_finalize_routing`；`process_weights_after_loading` 中 `npu_format_cast_(w2_weight, ACL_FORMAT_FRACTAL_NZ)`。
  - `vllm_ascend/utils.py::get_fused_moe_state` — `FusedMoEState.AllGatherEP`，门控 `VLLM_ENABLE_FUSED_EXPERTS_ALLGATHER_EP and ep_size>1 and is_deepseek_v3_r1`；注释「finalize-routing 算子 only supports deepseek v3/r1」。
  - `vllm_ascend/ops/fused_moe.py` — `is_deepseek_v3_r1 = (global_num_experts == 256)`；AllGatherEP forward 跳过 TP pad / all_gather，末尾 all_reduce。
  - `vllm_ascend/envs.py` — `VLLM_ENABLE_FUSED_EXPERTS_ALLGATHER_EP` 默认 0。

## Links

- [expert-parallel](../../../concepts/parallelism/expert_parallel.md) — EP 本 rank 专家切分（`local_num_experts = global // ep_size`）与 AllGatherEP 通信。
- [w8a8c8](../../../concepts/quantization/w8a8c8.md) — W8A8-dynamic 量化路径，本融合链的量化前提。
- [weight-nz](../../../concepts/techniques/weight_nz.md) — w2 须 cast 成 FRACTAL_NZ 才能进下投影融合算子。
- [fused-op-hardware-conditional-fallback](fused_op_hardware_conditional_fallback.md) — 同类：昇腾融合算子按硬件/模型条件门控、须有非融合 fallback。
- [moe-ep-dispatch-path-by-stage](moe_ep_dispatch_path_by_stage.md) — MoE-EP dispatch 路径按阶段选择的相关经验。
