---
{
  "type": "Runbook",
  "title": "独立部署 Paged Attention + FA v2（TND + sparse_mode=3）改造模板与验证基线（Hunyuan-A13B-Instruct-FP8）",
  "description": "GQA（32/8 头、head_dim 128）非 MLA 模型的独立部署 KVCache 改造完整模板：Runner 自管分页 KV（每层 [total_blocks,128,8,128] bf16 + 静态 block_table=arange）+ npu_scatter_nd_update_ 写入 + FA v2（npu_fused_infer_attention_score_v2，TND + sparse_mode=3 + [2048,2048] bool 因果 mask）读取，hidden_states 全程 [TotalTokens, hidden] 二维，分支用 forward_metadata.is_prefill。验证：FA 隔离对拍误差 ~1e-2、与 CPU BF16 黄金参考贪心 token 完全一致（余弦 0.99976）、多 batch 不等长 packed 路径一致；Prefill 1923→1737 ms（-9.69%），Decode 基本持平（MoE dense dispatch 主导）。",
  "tags": [
    "task.implementation",
    "topic.model_serving",
    "topic.attention"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "950"
  ]
}
---
# 独立部署 Paged Attention + FA v2（TND + sparse_mode=3）改造模板与验证基线（Hunyuan-A13B-Instruct-FP8）

## 适用场景

- 模型：GQA 非 MLA 的标准/MoE Decoder-only LLM（本例 Hunyuan-A13B-Instruct-FP8：32 层、GQA 32 query / 8 KV heads、head_dim 128、`use_qk_norm=true` 且 QK RMSNorm 在 RoPE 之后、全层 FullAttention、无滑窗）。
- 框架/平台：独立部署（不接 cann-recipes-infer/executor/core，Runner 自管 KV 与 forward_metadata）；Ascend950PR_9589 单卡（HBM 123.25 GiB），CANN 9.1.0（需含 ascend950 ops_nn，见[Ascend950 CANN 缺 ops_nn 算子包的判别与 env.sh 双条件自动探测修复](../runtime/ascend950_cann_ops_nn_envsh.md)），torch_npu 2.12.0 / torch 2.12.0+cpu / transformers 5.19.0（vendored 建模）。
- 工作负载：W8A8 FP8（E4M3 权重 + 静态 per-tensor scale，激活 clamp 后量化）、eager、batch 1、输入 21 token、输出 8 token。
- 缺失信息说明：FA v1 与 v2 的性能对比未做（任务指定 v2）；Prefill 全走 block_table vs 直读寄存器 K/V 的对比未做；KV cache bf16 未量化。

## 触发与观测

目标：把 Legacy 连续 KV（BNSD + 标准 indexing + SDPA）改造为 Paged KV + FA v2 融合算子，并保持与 CPU BF16 黄金参考精度一致、性能不回退。改造前的客观基线（阶段 0 baseline_metadata.json，事件 651/13）：Prefill 1923.02 ms、Decode（采集脚本剔除首步）1740.72 ms、显存 79.1 GiB/123.25 GiB；黄金参考（事件 528/118）：固定 21 token 输入贪心生成 [27, 9399, 397, 60704]。

## 探针与操作

第一步：FA v2 隔离对拍（事件 142，逐字；`ref_attn` 为 torch SDPA 全量参考）：

```
mask = ~torch.tril(torch.ones(2048, 2048, dtype=torch.bool, device=dev))

T = 5
q = torch.randn(T, NH, D, dtype=torch.bfloat16, device=dev)
k = torch.randn(T, NKV, D, dtype=torch.bfloat16, device=dev)
v = torch.randn(T, NKV, D, dtype=torch.bfloat16, device=dev)
asq = torch.tensor([T], dtype=torch.int32, device=dev)
askv = torch.tensor([T], dtype=torch.int32, device=dev)
o, _ = torch.ops.npu.npu_fused_infer_attention_score_v2(
    q, k, v, num_query_heads=NH, num_key_value_heads=NKV,
    softmax_scale=1.0 / math.sqrt(D), input_layout="TND", sparse_mode=3,
    atten_mask=mask, actual_seq_qlen=asq, actual_seq_kvlen=askv,
)
oref = ref_attn(q, k, v)
print("prefill direct max diff:", (o.float() - oref.float()).abs().max().item())
```

Decode paged 分支（先 `npu_scatter_nd_update_` 写入再经 block_table 读取）。下例把来源的 `view(NB * BS, BS, -1)` 等价写成 `flatten(2)`，明确从实际 `[total_blocks, BS, NKV, D]` 缓存得到 `[total_blocks, BS, NKV*D]`，避免混淆来源探针过量分配的块数；这项表述修订未重新上板验证：

```
torch_npu.npu_scatter_nd_update_(k_cache.view(-1, NKV, D), torch.tensor([[5]], device=dev), kd.view(-1, NKV, D))
torch_npu.npu_scatter_nd_update_(v_cache.view(-1, NKV, D), torch.tensor([[5]], device=dev), vd.view(-1, NKV, D))

od, _ = torch.ops.npu.npu_fused_infer_attention_score_v2(
    qd, k_cache.flatten(2), v_cache.flatten(2),
    num_query_heads=NH, num_key_value_heads=NKV,
    softmax_scale=1.0 / math.sqrt(D), input_layout="TND", sparse_mode=3,
    atten_mask=mask,
    actual_seq_qlen=torch.tensor([1], dtype=torch.int32, device=dev),
    actual_seq_kvlen=torch.tensor([6], dtype=torch.int32, device=dev),
    block_table=block_table, block_size=BS,
)
```

第二步：建模侧改造（事件 156/169/173/176）。cache 写入（`models/modeling_hunyuan.py`，逐字含原始行号，事件 359）：

```
361:     def _write_cache(self, slot_mapping, key_states, value_states, k_cache, v_cache):
362:         """Write the new K/V rows to their physical slots (paged cache)."""
363:         num_kv_heads, head_dim = self.num_key_value_heads, self.head_dim
364:         slot = slot_mapping.reshape(-1).to(torch.int32)
365:         torch_npu.npu_scatter_nd_update_(
366:             k_cache.view(-1, num_kv_heads, head_dim),
367:             slot.view(-1, 1),
368:             key_states.reshape(-1, num_kv_heads, head_dim),
369:         )
370:         torch_npu.npu_scatter_nd_update_(
371:             v_cache.view(-1, num_kv_heads, head_dim),
372:             slot.view(-1, 1),
373:             value_states.reshape(-1, num_kv_heads, head_dim),
374:         )
```

FA 长度语义（逐字含原始行号，事件 359；Prefill 直读寄存器 K/V 后写 cache，Decode 先写 cache 再传 block_table + block_size）：

```
415:     def _fa_forward(self, query_states, key_states, value_states, k_cache, v_cache, fm):
416:         # FA wants cumulative Q lengths and (cumulative prefill / direct decode) KV lengths.
417:         actual_seq_qlen = torch.cumsum(fm.q_lens, dim=0).to(torch.int32)
418:         if fm.is_prefill:
419:             actual_seq_kvlen = torch.cumsum(fm.kv_lens, dim=0).to(torch.int32)
420:         else:
421:             actual_seq_kvlen = fm.kv_lens.to(torch.int32)
```

第三步：Runner 侧改造（事件 190，逐字；`BLOCK_SIZE = 128`、`ATTN_MASK_LEN = 2048`、bool 因果 mask `~tril(ones(2048,2048))`）：

```
    def init_paged_kvcache(self, batch_size, max_seq_len):
        """Per-layer paged KV cache + statically pre-allocated ``block_table``.

        Physical cache per layer: ``[total_blocks, block_size, num_kv_heads, head_dim]``.
        ``block_table`` is a static ``arange`` (never changes during inference), so
        the physical slot of logical position ``pos`` of request ``b`` is simply
        ``b * max_seq_len + pos``.
        """
        num_layers = self.config.num_hidden_layers
        num_kv_heads = self.config.num_key_value_heads
        head_dim = self.config.attention_head_dim

        assert max_seq_len % BLOCK_SIZE == 0, "max_seq_len must be a multiple of block_size"
        num_blocks_per_seq = max_seq_len // BLOCK_SIZE
        total_blocks = batch_size * num_blocks_per_seq
        self.num_blocks_per_seq = num_blocks_per_seq
        self.total_blocks = total_blocks

        cache = []
        for _ in range(num_layers):
            k = torch.zeros(total_blocks, BLOCK_SIZE, num_kv_heads, head_dim,
                            dtype=torch.bfloat16, device=self.device)
            v = torch.zeros_like(k)
            cache.append((k, v))

        self.block_table = torch.arange(
            0, total_blocks, dtype=torch.int32, device=self.device
        ).reshape(batch_size, num_blocks_per_seq)
        return cache

    def _slot_mapping_prefill(self, kv_len, max_seq_len):
        """Packed write slots for Prefill: request ``i`` occupies [i*stride, i*stride+len)."""
        parts = []
        for i, seq_len in enumerate(kv_len.tolist()):
            start = i * max_seq_len
            parts.append(torch.arange(start, start + seq_len, dtype=torch.int32, device=self.device))
        return torch.cat(parts)

    def _slot_mapping_decode(self, kv_len, max_seq_len):
        """Per-request write slot for Decode: ``kv_len[b]`` is the next position."""
        offsets = torch.arange(0, kv_len.shape[0] * max_seq_len, max_seq_len,
                               dtype=torch.int32, device=self.device)
        return (kv_len.to(torch.int32) + offsets)
```

配套要点（事件 156/163/165/166/214）：`ForwardMetaData` dataclass（`is_prefill`/`q_lens`/`kv_lens`/`slot_mapping`/`block_table`/`attention_mask`/`block_size`）；`hidden_states` 全程 `[TotalTokens, hidden_size]` 二维；MoE/gate/layer/model 全部 packed 二维化；保留 `RoPE → per-head QK RMSNorm` 的 Hunyuan 顺序（与 qwen3 的 norm→RoPE 相反，勿照搬）；保留 `_sdpa_forward` CPU 参考回退（同构分页 cache）供黄金参考与小配置冒烟。失败路线（不可采用）：Decode 复用 prefill 的 [2048,2048] mask（batch 维不匹配）；q_len≠kv_len 时把 actual_seq_kvlen 也取 cumsum（Decode 必须直接传 kv_lens）。

## 机制与判别

- 结论 a1：FA v2（npu_fused_infer_attention_score_v2）TND + sparse_mode=3 先经隔离脚本对拍：Prefill 直读分支与 Decode paged 分支相对 torch SDPA 参考最大误差分别为 0.0086 与 0.0046（bf16 随机数据、单次观测）。（证据：事件 142 探针，事件 153 `prefill direct max diff: 0.008593082427978516` / `decode paged max diff: 0.004647493362426758`）
- 结论 a2：全模型按分页 KV（每层 [total_blocks,128,8,128] bf16 + 静态 block_table）+ npu_scatter_nd_update_ 写入 + FA v2 读取 + packed 二维协议 + forward_metadata.is_prefill 分支改造后，与 CPU BF16 黄金参考贪心 token 完全一致 [27, 9399, 397, 60704]（token_match=true），prefill logits 余弦 0.99976、argmax 一致、top-10 命中 8/10。（证据：事件 333 与复跑事件 71/60）
- 结论 a3：多 batch 不等长 packed 路径：batch1 / batch2（2 请求）/ batch3（3 请求不等长）下同一 prompt 的贪心 token 与单独运行完全一致（RESULT: PASS，单次观测）。（证据：事件 82 测试脚本，事件 88 五组 check 全 match=True）
- 结论 a4：同机同配置同负载（单卡 Ascend950PR_9589、eager、batch 1、输入 21 token、输出 8 token、W8A8 FP8）下，Paged KV + FA v2 改造后 Prefill 从 Legacy SDPA 基线 1923.02 ms 降至 1736.67 ms（-9.69%，两侧各为 warmup 后单次正式观测）。（证据：基线事件 647/651，改造后事件 56）
- 结论 a5：Decode 单步耗时基本持平：两侧均取 7 步算术平均时为 1748.09 ms → 1730.48 ms（约 -1.0%）；审查报告的 1740.72 → 1730.48 ms（-0.59%）混用了基线采集脚本剔除首步后的 6 步平均（1740.72）与 7 步平均（1730.48）口径。该模型 decode 由 MoE dense dispatch（64 专家全量 + 共享 MLP）主导，attention 占比小，FA 收益被摊薄。（证据：事件 56 decode 7 步 1726.00–1735.94 ms；基线事件 647 decode 7 步 1722.50–1792.34 ms；MoE 主导为审查者解释性归因，未做分解 profile）
- 可区分解释：prefill 收益与 FA 融合（替代 QKᵀ/softmax/·V 多算子）时序一致；decode 不动与该模型 decode 步骤中 MoE（每步 64 专家 dense 计算）占大头一致；两者方向相反可互相印证"收益集中在 attention 占比高的 prefill"。但缺少按算子分解的 profile，MoE 主导的解释为假设。
- 混杂变量声明：改造同时更换了 KV 布局（BNSD→分页 TND）、写入算子（indexing→npu_scatter_nd_update_）与注意力算子（SDPA→FA v2），-9.69% 是三者的合并效果，不能全归因于 FA 算子本身。

## 验证信号

- FA 隔离对拍（事件 153，单次观测）：`prefill direct max diff: 0.008593082427978516`、`decode paged max diff: 0.004647493362426758`、`OK`。
- 小配置 CPU 冒烟（事件 211/234）：`SMOKE OK`（packed 协议 + slot/block_table 逻辑在 CPU 参考路径下正确）。
- 全模型精度（事件 333 与审查复跑事件 71，均单次运行）：`token_match: true`、`prefill_cosine: 0.9997637271881104`、`prefill_top10_overlap: 8`、`first_divergence_step: null`；输出 `<answer>\nParis.\n</answer>`（可读、不重复、非全零、不提前 EOS）。
- 多 batch packed（事件 88，单次观测）：`RESULT: PASS`（batch1/2/3 共 5 组对比全 match=True）。
- 性能（事件 56，审查会话复跑，单次正式运行）：`prefill is 1736.67 ms`；decode 7 步 1726.00–1735.94 ms（均值 1730.48 ms）；显存 `used 79.45 GiB / total 123.25 GiB`。
- 基线（事件 647/651，阶段 0 同机同负载，单次正式运行）：`prefill is 1923.02 ms`；decode 7 步 1722.50–1792.34 ms（均值 1748.09 ms；采集脚本剔除首步口径 1740.72 ms）。
- 证据等级：单机单卡；精度为两次独立运行一致（实施者 + 审查者）；性能为前后各一次正式运行（无重复实验）。

## 适用与失效边界

- 适用：GQA（非 MLA）+ 全层 FullAttention + 独立部署自管 KV 的 eager 推理；block_size=128 需整除 max_seq_len（实现内 assert）。
- 关键约束：block_size / sparse_mode / input_layout / mask / block_table / slot_mapping 必须严格自洽；Prefill 直读（不传 block_table、cumsum 长度）与 Decode（传 block_table、直接 kv_lens）两分支语义不同，写反会在多 batch 不等长下出错（用 batch1/2/3 对拍可暴露）。
- Hunyuan 特有顺序必须保留：RoPE 在 per-head QK RMSNorm 之前（`use_qk_norm=true` 模型）；V 不归一化；FA 原生 GQA，不再需要 repeat_kv。
- KV cache 容量：bf16 下 128 KiB/token（32 层×8 KV head×128 dim×2×2B）；max_seq_len=4096/batch 1 时全层 KV 约 512 MiB，非瓶颈。
- 不适用/未验证：MLA（需 TND_NTD + absorb）、滑窗层（需 sparse_mode=4 与 sliding_window 约束）、KV 量化（fp8 KV 需换 sparse_mode=0 路径并传 dequant scale）、图模式（本验证仅 eager）。审查会话中 `sh` 不支持 `source`，须 `bash -c 'source env.sh; ...'` 或 `bash infer.sh` 执行。
- 停止/回退条件：若多 batch packed 对拍失败或 token_match=false，先查 slot_mapping/block_table 与 kv_len 语义（kv_len=已缓存数，写入位置=kv_len），不要先动 FA 参数。
