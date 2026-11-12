---
type: Guide
title: W8A8 MLP：gate_up、SwiGLU、down 与 MoE scale 链
description: W8A8 MLP 的 gate_up/down 与 SwiGLU 量化 scale 传递；post-load 的 smooth_scales、NZ 与 dtype 处理，以及 MoE 路由/通信侧
  scale 对齐。
tags:
- task.implementation
- topic.precision
- topic.mixture_of_experts
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-quantization/references/quantization-structure-cards.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-quantization/references/quantization-contract.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen/models/modeling_qwen.py
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen/README.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/README.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/modeling_longcat_flash.py
  role: supporting
created_at: '2026-11-09T09:23:47Z'
updated_at: '2026-11-10T01:23:11Z'
platforms:
- a2
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - cann_executor
aliases:
- gate_up/down SwiGLU 量化链
- W8A8 post-load smooth_scales
- MoE A8 scale side channel
---

# W8A8 MLP：gate_up、SwiGLU、down 与 MoE scale 链

## 适用范围

固定版本 Qwen Dense 和 MoE/MLA 模型的 compressed-tensors W8A8 接线经验。Qwen 与 LongCat-Flash-Lite 样例声明 A2/A3 支持，具体融合内核、图模式和模型组合仍须按其 README 验证；这不是任意量化格式的统一实现。

## Dense 与 Shared MLP

Qwen 根据 mm_quant_mode == "w8a8int8" 选择 _forward_w8a8int8。gate_up_proj 生成 int32 累加结果及 pertoken_scale；npu_dequant_swiglu_quant 同时消费该 scale、gate_up_proj.weight_scale 与 down_proj.smooth_scales，返回新的量化激活与 per-token scale，再传给 down_proj。公共 Linear 量化不会自动把模型里的浮点 npu_swiglu 链改成这一分支。

post-load 核对 weight scale 和 down_proj smooth scale 的 float 适配、转置与 NZ 门控。若 checkpoint 把 gate/up 或 q/k/v 拆开，可在加载期恢复大粒度 matmul，但需 shape/dtype 兼容、量化方案一致、smooth_scales 完全相同，并同步拼接 weight/scale；先合并再按实际后端处理格式。该恢复方法是条件性设计，不代表所有参考模型都采用 post-load 融合。

## MoE 的两种 scale 路径

A8 scale 是与 token 排列绑定的 side channel。一路由 routing/dispatch 直接输出 INT8 token 与 scale，并在 all-to-all、rerouting 后一起传给 experts；另一路保持 BF16 dispatch，在本 rank 重排后本地 dynamic quant，再把 pertoken_scale 传给 GMM。先确认采用哪条路径，不能强制所有 Prefill all-to-all 都传量化 scale。

全局 smooth scale 量化路由可能需要 EP post-load all-gather smooth_scale_1；本地量化路径不自动需要这一步。routing 的 expert_tokens_num_type 与 GMM group_list_type 必须采用同一 count/cumsum/key-value 编码，不能把 1/count 当成唯一合法格式。LongCat 的 zero/copy expert 贡献另按 identity 语义处理。

运行配置解析见 [compressed-tensors 加载契约](compressed_tensors_runtime_loading_contract.md)，LI cache 的模型开关、配套 scale 缓存和 CP 重排见 [LI 量化闭环](lightning_indexer_quantization_scale_cache.md)。

## 验证与回退

追踪 routing→dispatch→rerouting→experts→combine 的 token 排列、dtype 和 scale，确认实际执行了目标量化 kernel；覆盖空专家、多 rank、真实权重及 Prefill/Decode。分别比较浮点基线的输出、峰值显存、不开 profiler 的时延。KV C8 与 LI cache 是独立量化闭环，不能只凭专家权重为 int8 认定启用。失败时恢复对应浮点模块或原非融合量化路径，保留目标量化产物语义。

相关：[C8 接线](../../optimizations/rules/mla_c8_int8_kv_cache_op_wiring.md)、[低比特专家布局](../../optimizations/rules/moe_expert_gmm_weight_lowbit_prep.md)、[后处理钩子](../../runbooks/runtime/moe_post_load_hook_missing.md)。

## Evidence

- [.agents/skills/model-infer-quantization/references/quantization-structure-cards.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-quantization/references/quantization-structure-cards.md)
- [.agents/skills/model-infer-quantization/references/quantization-contract.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-quantization/references/quantization-contract.md)
- [models/qwen/models/modeling_qwen.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen/models/modeling_qwen.py)
- [models/qwen/README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen/README.md)
- [models/longcat_flash_lite/README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/README.md)
- [models/longcat_flash/models/modeling_longcat_flash.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/modeling_longcat_flash.py)
