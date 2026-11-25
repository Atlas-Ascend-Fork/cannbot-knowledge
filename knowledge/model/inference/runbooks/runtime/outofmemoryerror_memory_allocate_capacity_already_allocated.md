---
{
  "type": "Runbook",
  "title": "BF16 295B MoE（hy3_preview）@32k/8batch/16die 静态显存墙负结果：moe_chunk_max_len 与 max_prefill_tokens 激活类缓解均无效",
  "description": "模型/任务：hy3_preview（HYV3ForCausalLM，295B MoE / ~21B 激活，80 层）离线推理，输入 32768 tokens/请求、batch=8、BF16、ge_graph、greedy（argmax）解码、max_new_tokens=32。",
  "tags": [
    "task.testing",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:05Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": [
    "a3"
  ]
}
---

# BF16 295B MoE（hy3_preview）@32k/8batch/16die 静态显存墙负结果：moe_chunk_max_len 与 max_prefill_tokens 激活类缓解均无效

## 适用场景

- 平台范围依据：source 0 seq 23、source 0 seq 24、source 0 seq 191的实际环境/设备记录确认本次为Atlas A3；这里不扩展未记录的产品或版本。

- 模型/任务：hy3_preview（HYV3ForCausalLM，295B MoE / ~21B 激活，80 层）离线推理，输入 32768 tokens/请求、batch=8、BF16、ge_graph、greedy（argmax）解码、max_new_tokens=32。
- 并行：world_size=16，attn_tp=4 / attn_dp=4，moe_ep=16，dense_tp=4，batch_size_per_dp_rank=2，block_size=128，mem_fraction_static=0.85。
- 平台：16 die（65536 MB/die，可用 61.28 GiB/die），CANN 9.1.0-beta.1，torch_npu 2.8.0.post4，enable_online_split_weight / enable_superkernel=true / enable_weight_nz=true。
- 场景来源：sota_32k_8batch 优化任务 round0（构造 32k 精确输入并建立 BF16 基线）。

## 触发与观测

环境修复（见 w23-s1-c2）后，warm-up prefill 阶段全 16 rank OOM（source 0 seq 191/194，tool_observed）：

```
[rank1]:     cos = self.cos_cached[position_ids]
[rank1]: torch.OutOfMemoryError: NPU out of memory. Tried to allocate 66.00 MiB (NPU 1; 61.28 GiB total capacity; 60.03 GiB already allocated; 60.03 GiB current active; 20.55 MiB free; 60.18 GiB reserved in total by PyTorch).
```

OOM 点在 RoPE `cos_cached[position_ids]` 索引——首个 prefill 激活分配即失败，说明 ~60GB 已被静态占用。HBM 实测（seq 248）：warmup 阶段全 16 die ~63.8-64.5GB/65536MB（97%+）。

## 探针与操作

锁定 batch=8 / 32k / 16die 不动，按序三次尝试（YAML `config/hy3_preview_rank16_4tp_16ep_gegraph_bf16_32k_b8.yaml`）：

1. 基线配置（max_prefill_tokens=65536=2 req/prefill cycle 打包）：OOM-1，60.03GB allocated / 20.55MiB free / 首个 66MiB 激活失败。
2. OOM-mitigate-1：加 `moe_chunk_max_len: 1024` → 仍 OOM，签名完全相同（60.03GB / 20.68MiB free / 66MiB 失败；seq 225 agent 汇报，对应运行日志）。
3. OOM-mitigate-2：再加 `max_prefill_tokens: 32768`（1 req/cycle）→ 仍 OOM 但签名前移：59.72GB allocated / 341.71MiB free / 失败在更大 514MiB 分配；跨 rank 汇总（seq 251）`13×59.72 GiB already allocated`、free 326-345MiB。
4. 机制查证（源码读取）：warmup 形状由 `_get_warmup_shape` 决定（seq 227 源码逐字）：
   ```
   seq_len = self.input_truncated_len
   max_prefill_tokens = self.infer_config.scheduler_config.max_prefill_tokens
   if max_prefill_tokens > 0:
       seq_len = min(seq_len, max_prefill_tokens)
       prefill_batch_size = max(1, max_prefill_tokens // seq_len)
   ```
   即降 max_prefill_tokens 会等比例缩小 warmup 激活（65536→32768 tokens），解释签名前移。
5. KV/权重测算（seq 239-240，脚本计算）：offline KV block 数=ceil(32800/128)×2+1=515 → KV ~5.03 GiB/die；weights 估 ~39.8GB/die → 静态合计 ~44.8GB，与观测 60.03GB 有 ~15GB 差（NZ 转换副本/HCCL/graph workspace 等未逐项拆分，Agent 推断权重实际 ~50GB/die）。

## 机制与判别

- 结论：该 OOM 由静态墙（权重+KV+框架静态）主导，激活类缓解无效。判别证据：moe_chunk 只压 MoE 激活峰值，失败点却在 MoE 之前的 RoPE 首激活（签名不变）；1 req/cycle 使 free 20MiB→341MiB、OOM 点后移到 514MiB 分配，说明激活确实减半，但静态墙 ~59.7GB 只留 <0.4GB，而单请求 32k prefill 需数 GB 激活，不可能塞下。
- `enable_prefill_multi_cycle` 在本框架无实现（grep 仅 progress.md 提及），不可用作第四种尝试。
- Agent 推算（假设，非直接观测）：MoE 专家权重占参数 97.6%，W8A8 可省 ~17GB/die，把静态降到 ~43GB 后预计可跑通；此为量化建议依据，未在本轨迹验证。

## 验证信号

- OOM-1（tool_observed，seq 191/194）：全 16 rank OOM，60.03GB/61.28GB，首个 66MiB 激活失败。
- OOM-2（seq 225，与运行日志对照的 agent 判读 + 监控事件）：moe_chunk_max_len=1024 无效，签名不变。
- OOM-3（tool_observed，seq 249-251）：max_prefill_tokens=32768 仍 OOM，签名前移；HBM 97%+（seq 248）。
- InferenceConfig 运行时逐字确认（seq 191）：`dtype='bfloat16', exe_mode='ge_graph', input_truncated_len=32768, batch_size=8, max_prefill_tokens=65536, batch_size_per_dp_rank=2, mem_fraction_static=0.85, moe_ep_size=16`。

## 适用与失效边界

- 适用边界：295B MoE BF16、32k/8batch、16×64GB die、上述并行切分。结论是"该锁定场景下 BF16 不可行、激活类缓解到头"，不是"该模型任何场景都 OOM"。
- 失效/不覆盖：更短输入（8k）或更小 batch 的 BF16 未测试；量化（W8A8/W4A8）路径未执行；静态 60.03GB 的逐项拆分（权重 vs NZ 副本 vs HCCL/graph workspace）未完成，~15GB 差额为 unknown。
- 停止条件：若 mem_fraction_static/静态 KV 预留策略变化（本框架 offline 分支按请求长度精确预留而非按比例），该测算需重做。

## 附：断言存档

- BF16 hy3_preview(295B MoE) @32k/8batch/16die(64GB) warm-up prefill 首个激活（RoPE cos_cached[position_ids] 66MiB）即 OOM：61.28 GiB total / 60.03 GiB already allocated / 20.55 MiB free，全 16 rank 一致——静态墙主导。
- 激活类缓解无效/有限：moe_chunk_max_len=1024 签名不变（OOM 仍在 RoPE 首激活）；max_prefill_tokens=32768（1 req/cycle）使 free 20MiB→341MiB、失败点后移到 514MiB 分配但仍 OOM（13 rank 59.72 GiB already allocated）。机制：_get_warmup_shape 按 max_prefill_tokens//seq_len 打包 warmup 激活。
- 结论边界：锁定 batch=8/32k/16die 全程未动，BF16 基线在本场景不可建立；HBM warmup 实测全 16 die ~64GB/65.5GB（97%+）；需量化（W8A8 起，MoE 专家权重占 97.6% 参数，Agent 推算省 ~17GB/die）才可能跑通（推算未验证）。

```text
[rank1]: torch.OutOfMemoryError: NPU out of memory. Tried to allocate 66.00 MiB (NPU 1; 61.28 GiB total capacity; 60.03 GiB already allocated; 60.03 GiB current active; 20.55 MiB free; 60.18 GiB reserved in total by PyTorch).If reserved memory is >> allocated memory try setting max_split_size_mb to avoid fragmentation.
```

```text
    def _get_warmup_shape(self):
        """Calculate warm-up input shapes based on current packed prefill/decode config."""
        prefill_batch_size = self.infer_config.scheduler_config.batch_size_per_dp_rank
        decode_batch_size = self.infer_config.scheduler_config.batch_size_per_dp_rank
        seq_len = self.input_truncated_len

        max_prefill_tokens = self.infer_config.scheduler_config.max_prefill_tokens
        if max_prefill_tokens > 0:
            seq_len = min(seq_len, max_prefill_tokens)
            prefill_batch_size = max(1, max_prefill_tokens // seq_len)

        return prefill_batch_size, decode_batch_size, seq_len
```

```text
KV reserved tokens/die: 65920 (blocks=515)
KV cache /die: 5.03 GiB
weights/die (est from progress): 39.8 GiB
=> static (weights+KV) ~ 44.8 GiB / 61.28 GiB capacity
observed allocated at OOM: 60.03 GiB ; free: ~0.02 GiB
```
