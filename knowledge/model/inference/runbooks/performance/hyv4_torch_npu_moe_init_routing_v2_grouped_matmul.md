---
{
  "type": "Runbook",
  "title": "HYV4 五点 torch_npu 融合替换（MoE init_routing_v2→grouped_matmul→clipped_swiglu→grouped_matmul→finalize_routing 等）的模块级/整网验证与同会话 A/B 性能",
  "description": "将 HYV4Experts 逐专家 Python 循环替换为 npu_moe_init_routing_v2→npu_grouped_matmul→npu_clipped_swiglu→npu_grouped_matmul→npu_moe_finalize_routing 链路，并以 npu_moe_gating_top_k、npu_rms_norm、合并 gate_up+npu_swiglu、npu_rotary_mul(half) 替换 router/RMSNorm/MLP/RoPE，每点独立开关可回退。模块级 cos≥0.99998（router 索引逐位一致），整网 Paged 默认路径全开 prefill cos 0.999912 且 greedy token 与阶段 0 eager 基线逐位一致；同会话 A/B（reps=16 中位数）prefill 242.745→28.721 ms、decode 58.104→20.751 ms。",
  "tags": [
    "task.implementation",
    "topic.model_serving",
    "topic.mixture_of_experts"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-06T09:40:40Z",
  "platforms": [
    "950"
  ]
}
---

# HYV4 五点 torch_npu 融合替换（MoE init_routing_v2→grouped_matmul→clipped_swiglu→grouped_matmul→finalize_routing 等）的模块级/整网验证与同会话 A/B 性能

## 适用场景

- 模型/框架：HYV4（`hy_v4`）独立部署推理，vendored `models/modeling_hy_v4.py`；4 层缩减配置（6.039B，固定种子随机权重 seed=1234，无 checkpoint）、Paged MLA + FA v2 路径（`use_paged_fa=true`）。参考链路：`cann-recipes-infer/models/hy3`（同族单卡 TP MoE 融合）、`deepseek_v4`（gate_topk noaux_tc）、`gemma_4`。
- 平台/版本：Ascend950PR_9589 单卡、CANN 9.1.0、torch 2.12.0+cpu、torch_npu 2.12.0；venv `${LOCAL_PATH_1}`。
- 目标与工作负载：消除 MoE 逐专家 Python 循环（`nonzero`/`where`/`index_add_` 的 host 同步与上百次小算子发射）及其余四个次级模块的小算子开销；负载为 13 token 固定 prompt、batch=1、max_new_tokens=8、bf16。
- 五个融合点（每点独立开关，默认 off，Runner 经 `custom_params`/env 开启）：#1 MoE experts（本文主体）、#2 MoE router（`npu_moe_gating_top_k`）、#3 RMSNorm（`npu_rms_norm`）、#4 MLP/SwiGLU（合并 gate_up + `npu_swiglu`）、#5 RoPE（`npu_rotary_mul(half)`，含 Paged 路径 `_apply_rotary_half_packed` 的 BSND 4D reshape）。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

阶段 3.1 只读探针已定位 MoE 专家循环为 prefill/decode 首要瓶颈：单层（E=256/H=2816/I=768/top-8）loop 17.037 ms（decode 1 token）/ 139.363 ms（prefill 13 token）vs 融合路径 0.522 / 0.698 ms（来源记录 事件 211，单次观测）。阶段 3.2 实施并验证；阶段 3.4 reviewer 独立复核。

## 探针与操作

MoE experts 融合链路核心实现（`models/modeling_hy_v4.py`，最终状态，来源记录 事件 281 原文）：

```
831:     def _forward_fused(
832:         self, hidden_states: torch.Tensor, top_k_index: torch.Tensor, top_k_weights: torch.Tensor
833:     ) -> torch.Tensor:
834:         import torch_npu
835:
836:         num_rows = hidden_states.shape[0]
837:         top_k = top_k_index.shape[-1]
838:         gate_up_kn, down_kn = self.grouped_matmul_weights()
839:
840:         # scatter tokens to experts (gather-type row idx), then two grouped
841:         # matmuls with the clamped-SwiGLU in between.
842:         expanded, row_idx, tokens_per_expert, _ = torch_npu.npu_moe_init_routing_v2(
843:             hidden_states,
844:             expert_idx=top_k_index.to(torch.int32),
845:             active_num=num_rows * top_k,
846:             expert_num=self.num_experts,
847:             expert_tokens_num_type=1,
848:             expert_tokens_num_flag=True,
849:             active_expert_range=[0, self.num_experts],
850:             quant_mode=-1,
851:         )
852:         hidden = torch_npu.npu_grouped_matmul(
853:             [expanded], [gate_up_kn], group_list=tokens_per_expert,
854:             group_type=0, group_list_type=1, split_item=3,
855:         )[0]
856:         # Exactly HYV4Experts._apply_gate: clamp in swish (alpha=1) then gate*up.
857:         hidden = torch_npu.npu_clipped_swiglu(
858:             hidden, dim=-1, alpha=1.0, limit=self.swiglu_limit, bias=0.0, interleaved=False
859:         )
860:         hidden = torch_npu.npu_grouped_matmul(
861:             [hidden], [down_kn], group_list=tokens_per_expert,
862:             group_type=0, group_list_type=1, split_item=3,
863:         )[0]
864:         return torch_npu.npu_moe_finalize_routing(
865:             hidden,
866:             skip1=None,
867:             skip2=None,
868:             bias=None,
869:             scales=top_k_weights.to(hidden.dtype),
870:             expanded_src_to_dst_row=row_idx,
871:             export_for_source_row=None,
872:             drop_pad_mode=2,
873:         )
```

`init_routing_v2(active_num=T*K, expert_tokens_num_type=1, drop_pad_mode=2 的 finalize 配套)` 的语义配套性与 `npu_clipped_swiglu` 等价性是 implementer 自列的 reviewer 检查项，reviewer 独立复核通过（见下）。router 融合调用（单组 sigmoid 路径，来源记录 事件 64 原文）：

```
740:             topk_weights, topk_indices, _ = torch_npu.npu_moe_gating_top_k(
741:                 router_logits,
742:                 self.top_k,
743:                 bias=self.e_score_correction_bias,
744:                 k_group=self.topk_group,
745:                 group_count=self.num_group,
746:                 group_select_mode=1,
747:                 renorm=0,
748:                 norm_type=1,
749:                 routed_scaling_factor=self.routed_scaling_factor,
750:                 eps=1e-20,
751:             )
752:             return router_logits, topk_weights, topk_indices
```

（`k_group=1/group_count=1` 对应 `n_group=1/topk_group=1` 退化为单组全局 top-k 的参数映射；多组配置下该守卫会静默回退 eager。）

验证工具：`tools/verify_fusion_modules.py`（模块级，真实维度）、`tools/verify_fusion_network.py`（整网精度 + 同会话交替 A/B 计时，模型只构建一次、`--reps 16`）、`infer.sh`（端到端 token 级）、reviewer 的算子计数插桩（见 [融合主开关 use_fused_ops=0 被逐点 fuse_* 配置覆盖失效：改为硬主闸 AND 语义的修复](../runtime/use_fused_ops_fuse_.md)）。

## 机制与判别

- 模块级精度（真实维度，阈值 cos≥0.9999）：MoE experts decode cos 0.99998409 / prefill 0.99998295；router 索引集合逐位一致、权重 maxdiff 5.96e-8；RMSNorm cos 0.99999624；MLP shared-768 0.99999344 / dense-6912 0.99999356；RoPE 三路径 cos_q/cos_k 均 ≥0.999995。锚点：来源记录 事件 238（`agentic/golden/fusion_modules.json`）；信号：同事件 + reviewer 复跑 来源记录 事件 148（数字逐位一致）。
- 整网精度（Paged 默认路径，同会话 vs 未融合基线）：单点 prefill cos 0.999913–1.000002、argmax 全一致；全开 prefill cos 0.999912、decode cos_min 0.992923、argmax 一致。锚点：来源记录 事件 242；信号：事件 285（`fusion_network.json`）+ reviewer 复跑 来源记录 事件 164（数值逐位复现）。
- 整网输出一致性：全融合默认 Paged 路径 greedy 输出 [101453, 58721, 70389, 70389, 76480, 76480, 76480, 76480] 与阶段 0 eager 基线逐位一致；HYV4_USE_FUSED_OPS=0 全关后逐位复现阶段 2 paged 基线 token [101453, 76480, 13901, 65000, 40554, 58506, 105246, 58506]。锚点：来源记录 事件 250、189；信号：同事件 + reviewer env 路径复跑 来源记录 事件 188。
- 性能结论（同会话 A/B，模型只构建一次、reps=16、中位数）：同会话 A/B（模型只构建一次、reps=16、中位数）：五点全融合后 prefill 242.745→28.721 ms（约 8.5×）。锚点/信号：来源记录 事件 242（implementer，`fusion_network.json` timing_ms）；reviewer 独立复跑 来源记录 事件 164 得 211.188→22.337 ms（比值 0.1058，同一口径下复现）。
- 可区分解释：融合点各自逐点独立开关（`HYV4_FUSE_<NAME>=0`），逐点关闭后行为变化可观测（来源记录 事件 277：`HYV4_FUSE_MLP_SWIGLU=0 HYV4_FUSE_MOE_ROUTER=0` 后构建日志变为对应 False）；算子计数插桩证明每个开关只触发其融合算子、all_off 时计数全 0（来源记录 事件 184）。eager attention + 全融合组合的 logits 相关性下降另有判别（见 [随机权重网络上融合组合整网 logits 相关性下降（eager all 0.9966、argmax 翻转）的判别：组合探针定位 + 逐层 hidden 跟踪区分 bf16 传播放大与算子错误](../precision/logits_eager_argmax_hidden_bf16.md)），不影响默认 Paged 路径。
- 未验证推断：整网收益主要来自 MoE experts 点（逐点关闭 `moe_experts` 时 prefill 显著回升，来源记录 事件 171 同会话逐开关 A/B：`paged_moe_experts_off pre=188.9` vs `paged_all_on pre=19.3`），但未做逐点收益的正式同口径中位数统计。

## 验证信号

以下均为本组来源观测轨迹内客观观测（平台 Ascend950PR_9589 单卡、bf16、seed=1234、batch=1、13 token prompt）：

- 模块级：来源记录 事件 238 / 来源记录 事件 148（`fusion_modules.json` 数字逐位一致：moe_experts 0.99998409/0.99998295、router index_set_match true + 5.96e-8、rms_norm 0.99999624、mlp 0.99999344/0.99999356、rope 三路径 ≥0.999995）。
- 整网精度：来源记录 事件 285（`fusion_network.json`）与 来源记录 事件 164（reviewer 独立复跑，paged 单点/all 数值逐位一致；eager all 0.996563 见 [随机权重网络上融合组合整网 logits 相关性下降（eager all 0.9966、argmax 翻转）的判别：组合探针定位 + 逐层 hidden 跟踪区分 bf16 传播放大与算子错误](../precision/logits_eager_argmax_hidden_bf16.md)）。
- 端到端 token：${PRIVATE_CREDENTIAL_1} 事件 250（`bash infer.sh` 全融合：prefill 20.05 ms、decode 18.39–18.88 ms、token 逐位一致）；事件 189（master-off 逐位复现阶段 2 基线）；来源记录 事件 188（两条 env 路径 token 复现）。
- 性能（同会话 A/B，reps=16 中位数）：来源记录 事件 242：prefill eager_fusion 242.745（min 210.883 / max 254.889）vs fused 28.721（min 21.389 / max 31.581），`fused_over_eager=0.1183`；decode 58.104（min 54.633 / max 63.394）vs 20.751（min 18.678 / max 21.305），`fused_over_eager=0.3571`。reviewer 复跑（来源记录 事件 164）：prefill 211.188→22.337（0.1058）、decode 56.392→19.525（0.3462）。两轮绝对值随宿主负载漂移（本机 loadavg 波动），比值稳定在 prefill ÷8.5–9.5 / decode ÷2.8–2.9。注意：绝对耗时只在该单卡宿主空闲窗口成立，跨时段比较不可用（阶段 2.5 已证跨时段比较是假象，见 `stage2_paged_metadata.json` 的 `_notes`）。
- 显存：全融合后 NPU used 17.68 GiB / 123.25 GiB（事件 250 日志行 `NPU memory after load`），GMM 权重零拷贝视图额外 ~0.04 GiB（见 [npu_grouped_matmul 直接消费 permute(0,2,1) 非连续转置视图，免除 [E,K,N] 专家权重的 contiguous 拷贝（约 10 GiB/4 层）](npu_grouped_matmul_permute_contiguous_gib.md)）。

## 适用与失效边界

- 边际精度项（reviewer 独立测得，来源记录 事件 207）：融合 Paged 对 CPU golden prefill cos 0.99988，略低于任务放宽口径 0.9999（未融合基线 0.99993、融合 vs 未融合 0.999912、双方 argmax 均为 101453）；接受该口径或要求逐位一致时需重新评估。
- 本组来源观测为固定种子随机权重（无 checkpoint）下的等价性与性能验证；真实权重精度未验证。`npu_clipped_swiglu`/`npu_grouped_matmul` docstring 仅列 A2/A3，本结论以 ascend950 kernel 目录存在 + 运行时数值复核为准（来源记录 事件 163/171），换芯片需重跑最小冒烟。
- eager attention + 全融合组合的整网 logits cos 0.996563/argmax 翻转（见 [随机权重网络上融合组合整网 logits 相关性下降（eager all 0.9966、argmax 翻转）的判别：组合探针定位 + 逐层 hidden 跟踪区分 bf16 传播放大与算子错误](../precision/logits_eager_argmax_hidden_bf16.md)）；该组合仅作回退诊断路径，默认 Paged 路径不受影响。
- 逐专家循环回退路径保留（`use_fused_ops=0` 或逐点 `HYV4_FUSE_<NAME>=0`）；router 融合的 `num_group==1/topk_group==1` 守卫在多组路由配置下会静默走 eager（implementer 自列检查项 3）。
- 34 层完整配置的绝对耗时与显存未测量（4 层单卡可行性配置）；多卡 EP（AllToAll/re_routing/MC2）路径不在本卡范围。
- decode 58.104→20.751 ms 为同一 A/B 产物的同口径中位数（reps=16），单次会话观测，未跨会话重复。
