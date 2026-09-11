---
type: Runbook
title: CUDA 原生 vLLM 多模态模型移植 vllm-ascend NPU：三处固定后端不兼容点与修法
description: MoE：import 期或前向命中 torch.ops._moe_C（CUDA 专有算子）缺失——vLLM 原生 fused_topk / fused_moe 依赖它，NPU 无此 op，MoE 层无法在 NPU 执行。 视觉注意力：视觉编码器顶部 from flash_attn ... 导入失败——FlashAttention 是 CUDA 专用包，NPU 无此依赖，import 即报错。 引擎 / 图：vLLM V1 引擎 + CUDA graph 捕获（enforce_eager=False）在此 NPU bringup 不适用。
tags:
- task.debugging
- topic.attention
- topic.mixture_of_experts
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/260
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/275
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-07-06T00:00:00Z'
platforms:
- a2
---

# CUDA 原生 vLLM 多模态模型移植 vllm-ascend NPU：三处固定后端不兼容点与修法

## 信号（现象）

把上游按 CUDA 假设写好的 vLLM 多模态模型（观测实例 DeepSeek-OCR-2：视觉编码器 = SAM-ViT + Qwen2-decoder-as-encoder，语言侧含 MoE）搬到昇腾 Atlas A2 的 vllm-ascend（v0.8.5rc1 / vLLM 0.8.5）时，有三处后端不兼容会各自阻断启动，且互相独立、须同时打通：

1. **MoE**：`import` 期或前向命中 `torch.ops._moe_C`（CUDA 专有算子）缺失——vLLM 原生 `fused_topk` / `fused_moe` 依赖它，NPU 无此 op，MoE 层无法在 NPU 执行。
2. **视觉注意力**：视觉编码器顶部 `from flash_attn ...` 导入失败——FlashAttention 是 CUDA 专用包，NPU 无此依赖，import 即报错。
3. **引擎 / 图**：vLLM V1 引擎 + CUDA graph 捕获（`enforce_eager=False`）在此 NPU bringup 不适用。

三处任一未处理，模型都起不来或落 CPU 回退。

## 触发条件

上游 vLLM 建模按 CUDA 写死 + 目标运行时是 vllm-ascend（NPU）。定位是**非侵入式移植**——不改 vllm / vllm-ascend 源码，只把适配包放进 vllm 环境（补丁式原地改拷贝目录，rollback = 删目录重跑）。因此下面三处修法对同类 CUDA-only vLLM 模型的 NPU bringup 可迁移。

## 根因 + 修法

### 1. MoE：monkey-patch `fused_moe` 到 vllm-ascend

import 期把 vLLM 的 `fused_moe` 换成 vllm-ascend 原生实现——用 `select_experts` 取代依赖 `torch.ops._moe_C` 的 `fused_topk`，再走 `fused_experts`；保留原实现兜底：

```python
def _apply_moe_patch():
    from vllm_ascend.ops.fused_moe import fused_experts, select_experts
    import vllm.model_executor.layers.fused_moe as moe_module
    _original_fused_moe = moe_module.fused_moe            # 兜底

    def ascend_fused_moe(hidden_states, w1, w2, gating_output, topk,
                         renormalize=False, inplace=False, **kwargs):
        topk_weights, topk_ids = select_experts(          # 替代 fused_topk，避开 torch.ops._moe_C
            hidden_states=hidden_states, router_logits=gating_output, top_k=topk,
            use_grouped_topk=False, renormalize=renormalize, topk_group=None,
            num_expert_group=None, custom_routing_function=None,
            scoring_func="softmax", e_score_correction_bias=None)
        return fused_experts(hidden_states=hidden_states, w1=w1, w2=w2,
                             topk_weights=topk_weights, topk_ids=topk_ids,
                             top_k=topk, expert_map=None)

    moe_module.fused_moe = ascend_fused_moe               # 模块级替换生效
    return True
```

- **关键调用约定（维护者确认）**：该 ascend 适配包**必须在 `import vllm` 之前导入**，补丁才生效——模块级函数替换要早于 vllm 加载它对 `fused_moe` 的引用。入口脚本刻意打破标准 import 顺序；reviewer 曾建议改回标准序，被此说明驳回。
- `vllm_ascend` / `vllm` / `torch_npu` 缺失时补丁打 WARNING 并 `return False`、不硬崩。routing 用 `use_grouped_topk=False` + `scoring_func="softmax"` 简单模式，按目标模型 MoE 结构调整。
- 该模式对任何在 vllm-ascend 上命中 `torch.ops._moe_C` 的 [MoE](../../concepts/parallelism/expert_parallel.md) 模型可迁移。

### 2. 视觉注意力：flash_attn → SDPA

视觉编码器（`deepencoderv2/sam_vary_sdpa.py`）文件内本已备有 SDPA 路径。注释掉顶部 `from flash_attn ...` 导入，注意力即回落到文件内既有的 `torch.nn.functional.scaled_dot_product_attention`（带相对位置偏置走 `attn_mask=attn_bias` 分支、无 mask 走无参分支），无需引入新算子。

### 3. 引擎 / 图：关 V1 + 强制 eager + NPU 后端

```bash
export VLLM_ATTENTION_BACKEND=NPU     # attention 走 NPU 后端（底层 npu_fused_infer_attention_score）
export VLLM_USE_TRITON_FLASH_ATTN=0   # 关 triton flash-attn 后端，与 flash_attn→SDPA 配套
export VLLM_USE_V1=0                   # 退回 V0 引擎
# 构造引擎时 enforce_eager=True         # 关 CUDA graph 捕获
```

`VLLM_ATTENTION_BACKEND=NPU` 把 vLLM 的 paged/decode attention 切到昇腾后端（底层 [npu_fused_infer_attention_score](../../concepts/kernels/fused_infer_attention_score.md)），与视觉侧 flash_attn→SDPA 的回落是两处独立的 attention 后端替换。

## Outcome / correctness

三处同时打通后，README 自述"模型可完全在 NPU 上运行，无需 CPU 回退"。均为 correctness 型 bringup，源未给 NPU 上独立复测的功能/精度数字，也未给性能对比。注意 env 脚本模板里 `GRAPH_OP_RUN=1` 与 config `ENFORCE_EAGER=True` 存在张力（env 脚本更像通用模板），不据此外推图模式行为。

## 风险 / rollback

- 补丁式原地改，rollback = 删补丁目录重跑，不污染上游源码，也不改 vllm/vllm-ascend。
- MoE monkey-patch 依赖"补丁先于 vllm 导入"这条脆弱约定——入口脚本 import 顺序被改动时须复核补丁是否仍生效。

## 相关经验
- [昇腾多模态模型 bringup 的结构失配：框架侧 config 扫描盲区与 OOT 算子秩](mm_bringup_config_scan_and_oot_op_rank_contract.md)

## Evidence

- **代码事实**（clone `@3dd4acdbeebf`）：`deepseek_ocr2_npu.py` 的 `ascend_fused_moe` 模块级替换、`sam_vary_sdpa.py` 的 SDPA 两分支、`set_env_reliable.sh` 的 `VLLM_ATTENTION_BACKEND=NPU`——monkey-patch、SDPA 回落、env 开关均为 diff 事实。
- **代码事实**（clone `@5f55072604f4`）：补丁从 `vllm-deepseek-ocr2/` 重构到 `vllm-deepseek-ocr-2/npu_patch/` 并包成 `_apply_moe_patch`；含 `deepseek_ocr2_npu.py` 的 `ascend_fused_moe`/`_apply_moe_patch`、注释 flash_attn 导入、`VLLM_USE_V1=0`/`enforce_eager=True`、`set_env.sh` 的 `VLLM_ATTENTION_BACKEND=NPU`/`VLLM_USE_TRITON_FLASH_ATTN=0`。
- **维护者确认**：「补丁须在 vllm 前导入」「fused_moe 依赖 torch.ops._moe_C」为维护者/作者代码注释 + README 记述。施动者为本仓 contrib 适配包，非 DeepSeek 上游。
- 溯源下探：[cann-recipes-infer-pr-260-support-deepseek-ocr-2-on-a2](https://gitcode.com/cann/cann-recipes-infer/merge_requests/260)、[cann-recipes-infer-pr-275-update-vllm-deepseek-ocr-2](https://gitcode.com/cann/cann-recipes-infer/merge_requests/275)