---
{
  "type": "Runbook",
  "title": "eager RoPE 重复计算与 host 取值同步嫌疑：上移计算后 Decode 时延恢复",
  "description": "Hunyuan-A13B（32 层）Paged Attention + FA v2 改造的首版把 RoPE cos/sin 计算留在每层 HunYuanAttention 内（含 int(position_ids.max().item())），Decode 单步从基线 ~1741 ms 回退到 ~1957–1990 ms。把 cos/sin 上移到 HunYuanModel.forward、每步只算一次并透传各层后，Decode 回到 ~1727 ms、Prefill 1721 ms，回退消除。归因（32 次/步 host-device 同步打断 eager 异步流水）为实施者机制假设，未经 profiler 直接佐证。",
  "tags": [
    "task.debugging",
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
# eager RoPE 重复计算与 host 取值同步嫌疑：上移计算后 Decode 时延恢复

## 适用场景

- 模型/框架：Hunyuan-A13B-Instruct-FP8（32 层 MoE，GQA）独立部署 eager 推理，Paged Attention + FA v2（TND + sparse_mode=3）改造后的首版实现；对任何"逐层内部做 `.item()`/host 侧取值"的 eager Transformer 前向通用。
- 平台：Ascend950PR_9589 单卡，CANN 9.1.0（完整 ops_nn），torch_npu 2.12.0 / torch 2.12.0+cpu。
- 目标工作负载：batch 1、输入 21 token、输出 8 token、W8A8 FP8、eager 模式（torch.npu.synchronize 前后 wall-clock 计时）。
- 缺失信息说明：未做 profiler 分解验证同步开销；未测其他 batch/序列长度下的回退幅度。

## 触发与观测

触发：Paged Attention + FA v2 首版实现（逐层 RoPE，事件 169 引入）跑全量推理。客观观测（事件 281，fa_infer.log 逐字）：

```
2026-10-10 18:27:21,557 INFO hunyuan_a13b_fp8 inference time cost of prefill is 1993.51 ms
2026-10-10 18:27:23,548 INFO hunyuan_a13b_fp8 inference time cost of decode is 1989.73 ms
2026-10-10 18:27:25,530 INFO hunyuan_a13b_fp8 inference time cost of decode is 1981.90 ms
2026-10-10 18:27:27,496 INFO hunyuan_a13b_fp8 inference time cost of decode is 1964.54 ms
2026-10-10 18:27:29,463 INFO hunyuan_a13b_fp8 inference time cost of decode is 1966.32 ms
2026-10-10 18:27:31,427 INFO hunyuan_a13b_fp8 inference time cost of decode is 1963.37 ms
2026-10-10 18:27:33,385 INFO hunyuan_a13b_fp8 inference time cost of decode is 1957.18 ms
2026-10-10 18:27:35,365 INFO hunyuan_a13b_fp8 inference time cost of decode is 1979.91 ms
2026-10-10 18:27:35,366 INFO Request 0: outputs: <answer> <nl> Paris. <nl> </answer>
```

对照基线（同机同负载，阶段 0 Legacy SDPA）：Decode 1740.72 ms（采集口径）/ 1748.09 ms（7 步均值口径）、Prefill 1923.02 ms。即首版 FA 实现输出正确但 Decode 回退约 230 ms/步、Prefill 回退约 70 ms。

## 探针与操作

失败路线（不可采用，首版逐层实现，事件 169 引入，逐字）——每层 attention 内部各自求 RoPE 表：

```
        # RoPE (Hunyuan: applied before the per-head QK RMSNorm).
        seq_len = int(position_ids.max().item()) + 1
        cos, sin = self.rotary_emb(query_states, seq_len=seq_len)
        query_states, key_states = apply_rotary_pos_emb(
            query_states, key_states, cos, sin, position_ids
        )
```

修复（事件 290，逐字）——cos/sin 上移到 `HunYuanModel.forward`，每步只算一次并透传各层：

```
        # Packed 2D protocol: input_ids [TotalTokens], hidden_states [TotalTokens, hidden].
        if inputs_embeds is None:
            inputs_embeds = self.embed_tokens(input_ids)
        hidden_states = inputs_embeds
        # Compute RoPE cos/sin once per forward (all layers share the same rotary
        # table) so the eager path does not sync once per layer.
        seq_len = int(position_ids.max().item()) + 1
        cos_sin = self.layers[0].self_attn.rotary_emb(hidden_states, seq_len=seq_len)
        for idx, decoder_layer in enumerate(self.layers):
            k_cache, v_cache = past_key_values[idx]
            hidden_states = decoder_layer(
                hidden_states,
                position_ids=position_ids,
                cos_sin=cos_sin,
                k_cache=k_cache,
                v_cache=v_cache,
                forward_metadata=forward_metadata,
            )
```

配套改动：`HunYuanAttention.forward` 与 `HunYuanDecoderLayer.forward` 签名增加 `cos_sin` 参数并透传（事件 284/287/288）。修复后先跑小配置冒烟（事件 307 `SMOKE OK`）再全量重跑。

## 机制与判别

- 结论 a1：首版 FA 实现 Decode 单步约 1957–1990 ms、Prefill 1993.51 ms，较同机 Legacy SDPA 基线（Decode 1741 ms 量级）回退约 230 ms/步（同会话单次运行观测）。（证据：事件 281）
- 结论 a2：将 cos/sin 计算从每层 HunYuanAttention 上移到 HunYuanModel.forward、每步只算一次并透传各层后，同负载 Decode 回到约 1718–1741 ms（均值约 1727 ms）、Prefill 1721.04 ms，回退消除（同会话单次运行观测）。（证据：事件 319）
- 结论 a3：实施者把回退归因为每层 RoPE 计算中 int(position_ids.max().item()) 每步触发 32 次 host-device 同步、打断 eager 异步流水；该机制归因未经 profiler 直接佐证，属修复同时落地的假设（混杂单次运行波动）。（证据：事件 169 首版代码 + 事件 281/319 前后计时；归因文字见 progress.md 调试记录）
- 可区分解释：改动唯一（cos/sin 计算位置），前后两次全量运行同负载、输出均正确（`<answer>\nParis.\n</answer>`），排除了精度/输出差异因素；但单次运行无法排除环境波动，且修复后代码仍保留每步一次 `.item()`（1 次/步而非 32 次/步），说明"同步次数 32→1"与"回退消除"一致但非直接证明。
- 判别要点：eager 下 Decode 单步突然回退、且层内存在 `.item()`/`.tolist()` 等同步点时，优先把 host 侧取值上移或改为张量化，而不是先怀疑 FA 算子本身。

## 验证信号

- 事件 281（修复前，单次运行）：Prefill 1993.51 ms；Decode 7 步 1957.18–1989.73 ms。
- 事件 319（修复后，单次运行）：`prefill is 1721.04 ms`；decode 7 步 1718.13–1741.14 ms；输出 `Request 0: outputs: <answer> <nl> Paris. <nl> </answer>`。
- 事件 307：修复后小配置 CPU 冒烟 `SMOKE OK`（功能不回归）。
- 事件 333：修复后与 CPU 黄金参考对齐 `token_match: true`（精度不回归）。
- 证据等级：单机单卡、前后各一次全量运行（warmup 后正式计时）；无重复实验、无 profiler 分解。

## 适用与失效边界

- 适用：eager 模式、层数多（本例 32 层）、每层重复计算只依赖输入元数据（如 position_ids 最大值）的量；上移到模型级一次计算是普适改法。
- 边界：修复后每步仍有一次 `.item()` 同步（seq_len 推导）；要完全消除需把 seq_len 信息由 Runner 直接传入（本轨迹未做）。
- 图模式（ge/npugraph）可能自动消除此类同步，该修复的收益口径仅限 eager。
- 未验证：其他 batch/序列长度下回退幅度是否仍为 ~230 ms/步（回退量与层数、同步开销相关）。
- 停止条件：上移后 Decode 仍回退，则另寻原因（如 FA 算子本身、cache 写入路径），不应继续在此假设上叠加改动。
