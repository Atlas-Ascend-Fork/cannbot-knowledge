---
{
  "type": "Runbook",
  "title": "独立部署 Paged MLA 压缩缓存 + FA v2 absorb（TND_NTD）+ LSE sink 校正的实施与验证",
  "description": "HYV4 独立部署上用 Runner 自管 HyV4PagedCache（nope/rope/indexer 三 entry、ND 布局、npu_scatter_nd_update_ 写入、静态 block_table）配合 npu_fused_infer_attention_score_v2（TND_NTD、num_key_value_heads=1、return_softmax_lse=True）与惰性 W_uk/W_uv absorb，实现 Paged MLA + FA v2 dense 路径。端到端跑通且输出非退化；paged vs CPU golden prefill cosine 0.99993、eager↔paged 0.999942；use_paged_fa 一键回退逐位复现阶段 0 基线 token。",
  "tags": [
    "task.implementation",
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

# 独立部署 Paged MLA 压缩缓存 + FA v2 absorb（TND_NTD）+ LSE sink 校正的实施与验证

## 适用场景

- 模型/框架：HYV4（MLA + DSA indexer + 可学习 sink + 逐头 sigmoid 输出门控 + MoE + iHC），独立部署（Runner 自管 KV / block_table / slot_mapping / forward 元数据，不依赖 `cann-recipes-infer/executor/core/`），vendored `models/modeling_hy_v4.py`，L=4（6.039B）固定种子随机权重（seed=1234）。
- 平台/版本：Ascend950PR_9589 单卡，CANN 9.1.0，torch_npu 2.12.0，bf16。
- 目标：把 concat 动态 KV + eager attention 升级为 Paged MLA 压缩缓存 + `npu_fused_infer_attention_score_v2`（dense + MLA absorb + sink 语义保留），并提供一键回退。
- 缺失信息说明：batch=1 单请求、prompt 13 token、8 步 decode；多 batch 变长 packed 与 kv_len>2048（DSA 真正稀疏）场景未验证。

## 触发与观测

- 触发（任务书，方案 B 已确认）：KV 模式升级 Paged MLA 三 entry，FA v2 `TND_NTD`，启用 MLA absorb，放宽精度口径（cosine/top-k），保留回退开关。
- 实施后观测（事件 390）：`bash infer.sh`（`paged_fa=True`）无 crash，prefill 168.52 ms、decode 52.37–54.50 ms，输出 `...池Allocate religionoggled.sk metropolitan▁无 metropolitan`，token `[101453, 76480, 13901, 65000, 40554, 58506, 105246, 58506]`（可读、非全零、非全同、不提前 EOS、首 token 与基线一致）。（该 168.52 ms 为跨时段测量，性能结论见 [共享宿主上跨时段性能比较假象的判别与同会话交替 A/B 计时法](../performance/hyv4_stage0_2.md)，本卡不引用为收益。）

## 探针与操作

实施前置探针（失败路线已标注不可采用）：

1. FA v2 MLA-absorb 布局探测（事件 152–326）：`TND_NTD` + D=128 被算子拒绝（plog：Prefill MLA 场景 allowed layouts 不含 TND_NTD）；**D=512（kv_lora_rank）+ rope d=64 才是可用组合**。ND 3D `[NB, BS, D]` 与 NZ 5D 两种 paged cache 均被接受，数值一致（事件 322/326）。
2. 因果 mask 极性探测（事件 295/306）：`sparse_mode=3` 的 `atten_mask` 语义为 **True=屏蔽**；用 `tril`（下三角 True）时 cos≈0（静默全错，不可采用），改 `~tril` 后 cos=1.0。
3. `learnable_sink` 探测（事件 237）：absorb（value D=512）下 fp32/bf16 均失败 → 改 LSE 校正（详见 [FA v2 learnable_sink 在 MLA absorb（value d=512）下 tiling 失败，用 return_softmax_lse 精确 sink 校正替代](learnable_sink_mla_absorb_value_tiling.md)）。

生产实现（`models/modeling_hy_v4.py`，事件 335/499 原文）：

缓存结构（`HyV4PagedCache`）：

```
class HyV4PagedCache:
    """Runner-managed Paged MLA cache for the fused-attention (FA v2) path.

    Physical layout (independent-deployment / ND form accepted by FA v2
    ``input_layout="TND_NTD"`` with an MLA rope-separated query):

    * ``nope[i]``    : ``[total_blocks, block_size, 1, kv_lora_rank]``  (``=512``)
    * ``rope[i]``    : ``[total_blocks, block_size, 1, qk_rope_head_dim]`` (``=64``)
    * ``indexer[i]`` : ``[total_blocks, block_size, 1, index_head_dim]`` (``=128``,
      only allocated on ``"full"`` DSA indexer layers; ``"shared"`` layers reuse
      the previous full layer's top-k and keep ``None`` here)

    ``nope``/``rope`` are passed to FA as a 3-D ``[total_blocks, block_size, D]``
    view; ``indexer`` is written/read as a flat ``[total_blocks*block_size, D]``.
    ``block_table`` is a static ``arange`` (single request, sequential blocks),
    matching the reference independent-deployment skeleton.

    All per-step state (``slot_mapping`` / ``actual_seq_qlen`` /
    ``actual_seq_kvlen`` / ``is_prefill`` / ``kv_len``) is set by the Runner
    before each forward call; the model only reads it. ``kv_len`` is the total
    number of keys *after* the current tokens have been written to the cache.
    """
```

`_forward_paged` 核心（FA 调用 + sink 校正 + W_uv 回投 + 门控 + o_proj，事件 499 原文，行号原样）：

```
        is_prefill = paged_cache.is_prefill
        fa_mask = paged_cache.fa_mask if is_prefill else None
        attn_out, lse = torch_npu.npu_fused_infer_attention_score_v2(
            q_nope_abs, nope_view, nope_view,
            query_rope=q_rot, key_rope=rope_view,
            atten_mask=fa_mask,
            actual_seq_qlen=paged_cache.actual_seq_qlen,
            actual_seq_kvlen=paged_cache.actual_seq_kvlen,
            block_table=paged_cache.block_table,
            num_query_heads=self.num_heads,
            num_key_value_heads=1,
            softmax_scale=self.scaling,
            input_layout="TND_NTD",
            sparse_mode=3 if is_prefill else 0,
            block_size=block_size,
            return_softmax_lse=True,
        )  # attn_out: [N, T, kv_lora], lse: [T, N, 1]

        # Sink semantics: FA v2 has no learnable_sink for value D > 128, so the
        # sink contribution (a softmax normalizer only, dropped from the value
        # average) is applied exactly as out / (1 + exp(sink - lse)).
        correction = 1.0 / (1.0 + torch.exp(self.sinks.to(torch.float32).view(1, self.num_heads, 1) - lse.float()))
        attn_out = attn_out.permute(1, 0, 2).float() * correction  # [T, N, kv_lora]

        # Project back to v_head_dim, then apply the per-head sigmoid output gate.
        attn_out = torch.bmm(attn_out.to(w_uv.dtype).transpose(0, 1), w_uv.transpose(1, 2)).transpose(0, 1)
        attn_out = attn_out * torch.sigmoid(gate_states)
        attn_out = self.o_proj(attn_out.reshape(total_tokens, self.num_heads * self.v_head_dim))
```

配套改动：

- `absorb_weights`：惰性从已 cast 的 `kv_b_proj.weight` 拆 `W_uk[N,192,512]` / `W_uv[N,256,512]`（不注册 buffer、不消耗 RNG，CPU golden 路径逐位不变）；行序与 `expand_kv` 的 per-head 交错 `view(N, qk_nope+v_head)` 严格一致。
- 写入：`npu_scatter_nd_update_` 按 `slot_mapping` 写 nope/rope（ND 布局）。
- W_uv **未**折入 o_proj（中间夹逐头 sigmoid 门控非线性，无法线性折叠）；等价顺序为 FA 输出 → W_uv → 门控 → o_proj，absorb 消 O(T) `kv_b_proj` 全量展开的收益保留。
- Runner：`use_paged_fa` 开关（YAML 默认 true，env `HYV4_USE_PAGED_FA` 覆盖）；prompt>16 token 时首段 ≤16 prefill、余量 q_len=1 兜底。

## 机制与判别

- 独立部署 Paged MLA + FA v2 absorb 路径可端到端跑通：HyV4PagedCache 三 entry（nope[total_blocks,block_size,1,512]、rope[...,1,64]、indexer[...,1,128] 仅 full indexer 层）、block_table 静态 arange、npu_fused_infer_attention_score_v2（input_layout=TND_NTD、num_key_value_heads=1、block_size=128、prefill sparse_mode=3 + ~tril 因果 mask、decode sparse_mode=0 无 mask、return_softmax_lse=True）加 MLA absorb（惰性拆 kv_b_proj.weight 为 W_uk[N,192,512] / W_uv[N,256,512]），bash infer.sh 无 crash、输出非退化。
- 分流机制：`past_key_values` 是 `HyV4PagedCache` 走 FA，否则走阶段 0 eager——回退路径完全不触碰 paged/torch_npu FA 代码。
- 关键实现边界：paged KV 缓存用 ND 布局 [blockNum, blockSize, D] 与 NZ 5D 数值等价（同一探针 cos=1.000001），且可直接 npu_scatter_nd_update_ 写入；FA v2 absorb prefill 每 batch query S ≤ 16（文档约束），超过 16 token 的 prompt 以首段 ≤16 prefill + 余量 q_len=1 兜底。（S≤16 出处：事件 215 文档行 8655「query_rope配置时要求query的s为1-16」；ND/NZ 等价：事件 322/326。）
- DSA indexer 在 paged 路径保留语义但当前规模 no-op（index_topk=2048 ≥ kv_len），见 [CANN 9.1.0/Ascend950 FA 算子能力判别：sink 与 DSA top-k 不可兼得及 DSA no-op 判定](cann_ascend950_sink_dsa_top.md)。

## 验证信号

- 事件 390（实施方）：`bash infer.sh` paged 跑通，输出与 token 非退化（见触发与观测）。
- 事件 435：paged vs CPU golden——prefill cosine 0.99993、max abs 0.017624、top-1 一致、top-10 重叠 9/10；teacher-forced decode 逐步 cosine 最小 0.992977、argmax 6/7。
- 事件 471：同机 eager↔paged（teacher-force 同一 CPU 轨迹）——prefill cosine 0.999942、argmax 一致；decode 逐步 cosine 0.99298–0.99993。
- 事件 87/92（reviewer 独立复现）：`compare_golden_npu --use-paged-fa` 与 `compare_eager_paged` 重跑结果与实施方记录完全一致。
- 事件 439 + 83（回退）：`HYV4_USE_PAGED_FA=0 bash infer.sh` 输出 token `[101453, 58721, 70389, 70389, 76480, 76480, 76480, 76480]`，与阶段 0 基线逐位一致（两轨迹各自独立验证）。use_paged_fa=false 或 HYV4_USE_PAGED_FA=0 一键回退阶段 0 eager 路径，输出 token 逐位复现基线 [101453, 58721, 70389, 70389, 76480, 76480, 76480, 76480]；paged 路径跨会话多次独立运行 greedy token 逐位一致。（逐位一致的跨会话证据：事件 390 与事件 75 两次独立会话 token 完全相同。）
- 精度结论（放宽口径，独立复现两次）：paged vs CPU golden prefill cosine 0.99993、top-1 一致、top-10 重叠 9/10，teacher-forced decode 逐步 cosine ≥ 0.992977、argmax 6/7；同机 eager↔paged prefill cosine 0.999942、teacher-forced decode cosine 0.99298–0.99993。
- 性能：本卡不声明性能收益；同会话交替 A/B 显示当前规模中性（见 [共享宿主上跨时段性能比较假象的判别与同会话交替 A/B 计时法](../performance/hyv4_stage0_2.md)）。
- 证据等级：单机单卡、L=4 随机权重、batch=1；精度数值两次独立复现一致；回退逐位一致两次独立验证。

## 适用与失效边界

- 适用：CANN 9.1.0 / ascend950 独立部署 MLA 模型的 Paged 化 + FA v2 absorb；为图模式提供静态 shape（block_size 固定）。
- 失效/风险：
  - FA absorb prefill 每 batch S ≤ 16：长 prompt 走「首段 ≤16 + 余量 q_len=1」兜底，正确但慢；需 chunked prefill 才能高效。
  - DSA 在 kv_len ≤ 2048 时 no-op：长上下文（kv_len > index_topk）必须切 sparse 路径（`npu_sparse_flash_attention` + LSE sink 校正或 `sparse_flash_mla`），本卡未验证。
  - `atten_mask` 极性 True=屏蔽：mask 写反不报错、输出静默全错（探针期已踩过）。
  - indexer 读 `[:kv_len]` 依赖 batch=1 静态连续分配；多 batch 变长 packed 需另行设计。
  - 数值与 eager 存在 FA tiling + bf16 差异（prefill cosine 0.99993 vs eager 0.999971），只满足放宽口径，不满足逐位一致要求。
  - 随机权重基线：结论不携带绝对精度意义；真实权重到位后需重建 golden 与阈值。
