---
{
  "type": "Runbook",
  "title": "FA v2 learnable_sink 在 MLA absorb（value d=512）下 tiling 失败，用 return_softmax_lse 精确 sink 校正替代",
  "description": "MLA absorb 后 value 维是 kv_lora_rank=512，超过 CANN 9.1.0 learnable_sink 的 value d ≤ 128 约束，fp32/bf16 sink 张量均触发 aclnnFusedInferAttentionScoreV5 tiling 失败（error code 561002）。等价替代：FA v2 传 return_softmax_lse=True 取回 lse，用 out = out / (1 + exp(sink − lse)) 精确恢复 sink（sink 只进 softmax 归一化、不贡献 value）。单点探针校正后 cos 0.999999（未校正 0.949470）。",
  "tags": [
    "task.debugging",
    "topic.graph_execution",
    "topic.model_serving",
    "topic.attention"
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

# FA v2 learnable_sink 在 MLA absorb（value d=512）下 tiling 失败，用 return_softmax_lse 精确 sink 校正替代

## 适用场景

- 模型/框架：MLA + 可学习 sink 的模型在 Ascend NPU 上用 `npu_fused_infer_attention_score_v2` + **MLA absorb**（query 吸收 W_uk、value 维 = `kv_lora_rank`）做 Paged 推理（本例 HYV4：`kv_lora_rank=512`、`qk_nope_head_dim=192`、`qk_rope_head_dim=64`、`v_head_dim=256`、`num_heads=32`）。
- 平台/版本：Ascend950PR_9589 单卡，CANN 9.1.0，torch_npu 2.12.0；`input_layout="TND_NTD"`、`query_rope`/`key_rope` 分离、`block_size=128`。
- 目标：在 absorb 路径上完整保留 sink 语义（sink 只参与 softmax 归一化，不贡献 value）。

## 触发与观测

- 触发：阶段 2 方案 B 要求 FA v2 + learnable_sink + MLA absorb 同时启用。
- 失败观测（事件 237，单点探针 `probe_fa6.py`，N=4 头、T=13、DC=512、BSND paged cache）：

```
B fp32-sink FAIL: RuntimeError: npu_fused_infer_attention_score_v2_symint:.../FusedInferAttentionScoreV2KernelNpuOpApi.cpp:465 NPU function error: call aclnnFusedInferAttentionScoreV5 failed,
C bf16-sink FAIL: RuntimeError: npu_fused_infer_attention_score_v2_symint:.../FusedInferAttentionScoreV2KernelNpuOpApi.cpp:465 NPU function error: call aclnnFusedInferAttentionScoreV5 failed,
```

（伴随 `[ERROR] ... ERR00100 PTA call acl api failed`、`errno[561002] NnopbaseExecutorDoTiling ... Failed to execute tiling function` 链。）

- 文档根因（事件 215，`torch_npu/_op_plugin_docs.py` 原文，行号原样）：

```
8711: learnable_sink的参数约束如下：
8712: 仅支持TND、NTD\_TND；
8713: 仅支持value的d小于等于128；
```

CANN 9.1.0 算子文档约束 learnable_sink 仅支持 TND、NTD_TND 且仅支持 value 的 d 小于等于 128；MLA absorb 场景 value 维为 kv_lora_rank=512（非 absorb 的 v_head=256 同样大于 128），实测 fp32 与 bf16 的 learnable_sink 张量均触发 aclnnFusedInferAttentionScoreV5 tiling 失败（error code 561002）。

## 探针与操作

失败路线（不可采用）：`call({"learnable_sink": sink_f32})` / `call({"learnable_sink": sink_bf16})`——在 absorb（value D=512）配置下直接传 `learnable_sink`。

可用替代（采用）：等价替代路径：npu_fused_infer_attention_score_v2 传 return_softmax_lse=True 取回 lse，再用 out = out / (1 + exp(sink − lse)) 精确恢复 sink 语义（sink 只参与 softmax 归一化、不贡献 value）；单点探针 sink 校正后 cos=0.999999，未校正 cos=0.949470，decode 单步校正后 cos=0.998280。具体调用 `call({"return_softmax_lse": True})` 取回 lse（`lse: [T, N, 1]`，float32），在算子外做精确 sink 校正。生产实现（`models/modeling_hy_v4.py::HYV4Attention._forward_paged`，事件 499 原文，行号原样）：

```
        # Sink semantics: FA v2 has no learnable_sink for value D > 128, so the
        # sink contribution (a softmax normalizer only, dropped from the value
        # average) is applied exactly as out / (1 + exp(sink - lse)).
        correction = 1.0 / (1.0 + torch.exp(self.sinks.to(torch.float32).view(1, self.num_heads, 1) - lse.float()))
        attn_out = attn_out.permute(1, 0, 2).float() * correction  # [T, N, kv_lora]
```

## 机制与判别

- 数学依据（eager 参考实现可核）：eager 中 sink 以一列 logits 拼进 `attn_weights`，softmax 后 `probs[..., :-1]` 丢弃 sink——即 sink 只进入 softmax 分母、绝不贡献 value。设 `Z = Σ_j exp(a_j)`、`s = sink`，则
  - 不带 sink 的 FA 输出 `out_no = Σ_i exp(a_i)·v_i / Z`，`lse = log Z`；
  - 带 sink 的真值 `out = Σ_i exp(a_i)·v_i / (Z + exp(s)) = out_no / (1 + exp(s − lse))`。
  校正是代数精确的，不是近似。
- 判别证据（事件 313，非零 sink 向量 `[-1.5, 0.0, 2.0, 0.3]` 的单点探针，与 CPU 参考逐步对比）：
  - 校正后 cos=0.999999；不校正 cos=0.949470（sink 被整个丢掉的分母差）；
  - decode（q_len=1）单步校正后 cos=0.998280。
  即「未校正 0.949」可判别「丢 sink」与「实现错误」两种分支：校正后回到 ~1.0 说明 FA 主体数值正确，差异只来自 sink 归一化。
- dtype 判别（事件 164，D=64 非 MLA 探针）：`basic_sink`（fp32 sink）同样 tiling 失败而 `basic_sink_bf16` 通过——sink 张量 dtype 也参与 tiling 可行性。

## 验证信号

- 事件 237/244（单点探针，两次运行一致）：fp32/bf16 `learnable_sink` 均 FAIL（561002 tiling）；`return_softmax_lse=True` 路径返回 `out=(4, 13, 512)`、`lse=(13, 4, 1) torch.float32`。
- 事件 313：sink-corrected cos=0.999999 / uncorrected cos=0.949470 / decode sink-corrected cos=0.998280（单点探针，NPU vs CPU float 参考）。
- 事件 471（端到端）：生产 `_forward_paged` 用该校正后，同机 eager↔paged prefill cosine 0.999942、argmax 一致，teacher-forced decode cosine 0.99298–0.99993（见 [独立部署 Paged MLA 压缩缓存 + FA v2 absorb（TND_NTD）+ LSE sink 校正的实施与验证](paged_mla_absorb_tnd_ntd_lse.md)）。
- 事件 215（文档复核）：learnable_sink 约束原文（value d ≤ 128）。
- 证据等级：单机单卡探针 + 生产端到端对照；单点数值为单次观测（两次探针运行输出一致）。

## 适用与失效边界

- 适用：CANN 9.1.0 / ascend950 上 MLA absorb（value 维 = kv_lora_rank > 128）且必须保留 sink 语义的 FA v2 路径；`return_softmax_lse` 增加一个 `[T, N, 1]` fp32 输出与一次逐元素校正，代价比重新设计 attention 小得多。
- 失效/风险：
  - 若 value d ≤ 128 且 layout 命中约束，`learnable_sink` 仍是首选（少一次校正）；边界：在 D=64、query_rope/key_rope 为空的非 MLA 探针中 bf16 的 learnable_sink 可用而 fp32 的 learnable_sink 仍 tiling 失败；sink 张量 dtype 与维度需按算子约束逐一实测，不能凭经验假设。
  - sink 语义必须是「仅归一化、不贡献 value」；若某模型把 sink 当 value 列参与输出，本公式不成立。
  - 校正在 fp32 中做（`lse.float()`、`attn_out.permute(1,0,2).float()`），若降精度会产生额外误差（本轨迹未量化）。
  - CANN 版本升级后 learnable_sink 的 value d 约束可能放宽，需以 `_op_plugin_docs.py` 实测为准。
