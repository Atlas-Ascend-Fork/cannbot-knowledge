---
type: Optimization
title: 大 MoE 昇腾部署选型：并行形态/模型变体按集群规模选 + 非默认平台(310P/950)的算子与 HCCL 适配
description: 大 MoE 昇腾部署选型：并行形态/模型变体按集群规模选 + 非默认平台(310P/950)的算子与 HCCL 适配。在昇腾上部署大 MoE 模型时，两类决策要先定：(1) 并行形态与模型变体按「时延 vs 吞吐 vs 集群规模/显存」选；(2) 若目标平台不是 recipe 官方目标（A3/950），要预判该平台的算子路径与 HCCL 适配点。310P 侧另含：多模态视觉 encoder 的非因果 attention 须避开 torch_npu._npu_flash_attention_unpad（该算子在 310P 有精度问题），改按 cu_seqlens 逐段调 npu_prompt_flash_attention(BSND)。
tags:
- task.optimization
- topic.attention
- topic.mixture_of_experts
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/4
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/179
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/128
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/366
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/pull/5776
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-07-15T00:00:00Z'
platforms:
- a3
- '950'
- 310p
---

# 大 MoE 昇腾部署选型：并行形态/模型变体按集群规模选 + 非默认平台(310P/950)的算子与 HCCL 适配

## 条件 → 优先尝试什么

在昇腾上部署大 MoE 模型时，两类决策要先定：(1) 并行形态与模型变体按「时延 vs 吞吐 vs 集群规模/显存」选；(2) 若目标平台不是 recipe 官方目标（A3/950），要预判该平台的算子路径与 HCCL 适配点。

## 一、并行形态 / 模型变体选型

### 并行形态：低时延全 TP vs 高吞吐 DP+EP

- **小 batch / 低时延 / 单机** → Attention + MoE 全 [TP](../../../concepts/parallelism/tensor_parallel.md)：无专家负载不均、时延低。
- **高吞吐 / 大集群** → Attention [DP](../../../concepts/parallelism/data_parallel.md) + MoE [EP](../../../concepts/parallelism/expert_parallel.md)：避免 TP 把专家权重切得过小。

### 模型变体：卡数/显存受限选轻量变体

- 部署 DeepSeek-V4 时，仓内 recipe 官方仅面向 Atlas A3 Pod 与 950PR/DT，无 910B 原生路径；对卡数/显存受限集群（如 2×8 卡 910B2、单卡 64GB、共 16 chips），维护者建议选 **DeepSeek-V4 Flash** 变体、参考 A3 部署方式在 910B 上自行适配（社区试跑、非官方验证路径）。
- 通则：目标平台无某模型原生 recipe 时，先看有无**更轻的同族变体** + 参考最接近平台的部署方式做适配尝试，而非硬套满配 recipe。

## 二、非默认平台的算子 / HCCL 适配

### Ascend 310P（无标准 MLA/FIA 算子路径）

- **MLA decode 改用 MQA 形态算子承载**：310P 无标准 [MLA](../../../concepts/modules/mla.md)/[FIA](../../../concepts/kernels/fused_infer_attention_score.md) 算子路径，可把 MLA 压缩隐向量 `cCache` + rope 分量 `kPeCache` 当作 MQA 的 KV 输入喂入，用 MQA 算子承载 MLA decode。
- **多卡需定制/打补丁 HCCL**：310P 多卡（如 20 卡/world32）部署 671B MoE 需要定制/打补丁的 HCCL——HCCL 的拓扑控制与建链模块尚未完全开源，未打补丁多卡通信无法启用。

#### 310P 视觉 encoder attention 避开 `_npu_flash_attention_unpad`（该算子在 310P 有精度问题）

**场景**：在 310P 上跑多模态模型（如 qwen2.5-VL）时，视觉 encoder 的非因果 attention 若选用 `torch_npu._npu_flash_attention_unpad`（变长序列免 pad 的 flash attention）会撞到精度问题——这是系于 **310P 硬件 + 该具体算子**的固有行为，不是某次 bringup 的一次性 bug；下一个在 310P 上做 encoder / prefill 类 attention 的人若沿用同一算子会重现同样的精度劣化。

**规避技术（通用）**：放弃「一次调用吃整个 unpad 变长 batch」的路径，改按 `cu_seqlens` 把打平的序列切成逐段等长子序列，**逐段**用换算子的稠密 attention 承载，再把各段输出写回原打平缓冲。思想是用「已验证精度可靠的稠密 prompt-attention + 手工分段」换掉「精度不可靠的融合 unpad 变长 kernel」——牺牲一次算子调用的 batch 打包便利，换 310P 上的数值正确性。

**参考实现及其约束**（vllm-ascend 310P 多模态 encoder attention，dtype fp16、eager 模式；类 `AscendMMEncoderAttention310`，路径 `vllm_ascend/_310p/ops/mm_encoder_attention.py`）：

- 先把 q/k/v reshape 到 3D 并按需 pad：`head_size` 落在 `(MIN_PAD_SIZE, MAX_PAD_SIZE)` 之间且开启优化模型时先 pad 到 `MAX_PAD_SIZE`，再补齐到 **16 的倍数**；
- 按 `cu_seqlens` 每段序列长度逐段调用，每段 q_i/k_i/v_i 形状 `[1, S, H, D]`：

```python
out_i = torch_npu.npu_prompt_flash_attention(
    q_i, k_i, v_i,
    input_layout="BSND",
    num_heads=self.num_heads,
    num_key_value_heads=self.num_kv_heads,
    scale_value=self.head_size**-0.5,
    pre_tokens=qs, next_tokens=kvs,
)
```

- 输出写回打平缓冲 `context_flat[st:ed]`，最后切回原始 `head_dim` 并 `rearrange` 回 `[b, s, h, d]`。

约束是该参考实现的、非技术本身的：head_size 的 pad 到 `MAX_PAD_SIZE` / 16 倍数补齐、`BSND` 布局、fp16 + eager 都是该 310P 实现路径的限定；`npu_prompt_flash_attention` 逐段替换 unpad 的规避思想本身可迁移到 310P 上任何 encoder/prefill 变长 attention。源未给具体精度 before→after 数字，且该实现的多模态 vl e2e 测试被 `pytest.mark.skip(reason="310P: multimodal test skipped, offline is ok")` 跳过、仅 dense offline 通过，故收益是「避开已知精度问题」而非「已量化的精度提升」。

### Ascend 950（HCCL 算子展开模式与 A3 不同）

- executor 在 950 上部署时，HCCL 算子展开模式**不沿用 910c/A3 的 `HCCL_OP_EXPANSION_MODE=AIV`**，而在建默认通信组时用 `hccl_config={"hccl_op_expansion_mode": 5}`（ccu_ms），并显式设 `HCCL_BUFFSIZE`；单机芯片数按 **8**（A3 为 16）计算 `SERVER_NUM` / `MA_NUM_GPUS`。这组 950-vs-A3 差异由 `platform_version` 配置门控，对任意模型的 950 bringup 通用。

## 风险 / 边界

- 910B 上跑 DeepSeek-V4 Flash 是社区试跑路径，非官方验证——功能可试，精度/性能须自行回归。
- 310P 定制 HCCL 依赖尚未完全开源的建链模块，迁移成本高。
- 上述并行选型是「低时延↔高吞吐」的定性权衡，非受控 benchmark 排序，不外推「TP 一定更快」这类单调规律。

## 相关经验
- [昇腾 bringup 初始化/HCCL 报错的根因常在环境/驱动/平台层，顶层 ACL/HC](../../../runbooks/runtime/bringup_error_root_cause_env_driver_platform.md)

- HCCL AIV 展开与 prefill micro-batch 的互斥见 [hccl-aiv-expansion-vs-prefill-micro-batch](hccl_aiv_expansion_vs_prefill_micro_batch.md)；MC2 融合通信兼容性见 [mc2-fused-comm-op-compatibility-fallback](../../../runbooks/runtime/mc2_fused_comm_op_compatibility_fallback.md)。
- DP-attention + TP-oproj/MLP 混合并行见 [dp-attention-tp-oproj-mlp-hybrid](dp_attention_tp_oproj_mlp_hybrid.md)。
- 310P 这类 FP16-only 平台部署 BF16 模型的权重 cast 精度回归（代码生成类坍塌、须按生成完整性验收）见 [precision-fp16-only-platform-bf16-weight-cast](../../../runbooks/precision/precision_fp16_only_platform_bf16_weight_cast.md)。

## Evidence

- `维护者确认`（@e8eb697）：MoE 部署 TP vs DP+EP 的时延/吞吐权衡（RFC 答复）。
- `维护者确认`（@2c45117）：DeepSeek-V4 无 910B 原生路径、建议 Flash 变体自行适配。
- `diff 事实`（@938a6c2）：310P MLA decode 用 MQA 算子承载、多卡需定制 HCCL。
- `diff 事实`（@524914b）：950 用 `hccl_op_expansion_mode:5` + `HCCL_BUFFSIZE`、单机 8 芯，由 platform_version 门控。
- `维护者确认 + diff 事实`（@1ffca86）：310P 上 `_npu_flash_attention_unpad` 有精度问题（作者 review 明确陈述）；合并态 `mm_encoder_attention.py` 改用逐段 `npu_prompt_flash_attention`（BSND），diff 中未再出现 unpad 算子。
- 溯源下探：[cann-recipes-infer-issue-4-rfc-qwen3-moe-model-inference-support](https://gitcode.com/cann/cann-recipes-infer/issues/4)、[cann-recipes-infer-issue-179-question-8-910b2-64gb-deepseekv4](https://gitcode.com/cann/cann-recipes-infer/issues/179)、[cann-recipes-infer-pr-128-feat-support-deepseekv3-on-ascend310p-20](https://gitcode.com/cann/cann-recipes-infer/merge_requests/128)、[cann-recipes-infer-pr-366-support-deepseek-v4](https://gitcode.com/cann/cann-recipes-infer/merge_requests/366)、[vllm-ascend-pr-5776-feature-support-310p-device-run-qwen2-5-3-dense-and-qwen2-5vl-models](https://github.com/vllm-project/vllm-ascend/pull/5776)