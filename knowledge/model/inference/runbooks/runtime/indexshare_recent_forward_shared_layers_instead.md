---
{
  "type": "Runbook",
  "title": "GLM-5.2 IndexShare 适配的最小改动集：按 config.indexer_types[layer_idx] 决定 full 层建 indexer / shared 层 indexer=None，并把 prev_topk_indices 经 prepare_qkv→forward_absorb(_cp)→Attention.forward→DecoderLayer.forward→模型层循环（modeling_glm.py:1791）跨层线程化，各层返回 (output, topk_indices)；MTP 层为 full 但保持原 (residual, hidden_states) 二元组契约",
  "description": "在 cann-recipes-infer 类 NPU 推理仓中，把按「每层自带 indexer」实现的 GLM-5/DeepSeek-DSA 代码适配为 GLM-5.2 的 **IndexShare** 结构：仅 `indexer_types=\"full\"` 的层计算 top-k，后续 `\"shared\"` 层复用最近 full 层的 `topk_indices`。",
  "tags": [
    "task.implementation",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:04Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": [
    "a3"
  ]
}
---

# GLM-5.2 IndexShare 适配的最小改动集：按 config.indexer_types[layer_idx] 决定 full 层建 indexer / shared 层 indexer=None，并把 prev_topk_indices 经 prepare_qkv→forward_absorb(_cp)→Attention.forward→DecoderLayer.forward→模型层循环（modeling_glm.py:1791）跨层线程化，各层返回 (output, topk_indices)；MTP 层为 full 但保持原 (residual, hidden_states) 二元组契约

## 适用场景

- 平台范围依据：source 0 seq 845、source 0 seq 846、source 0 seq 1412的实际环境/设备记录确认本次为Atlas A3；这里不扩展未记录的产品或版本。

在 cann-recipes-infer 类 NPU 推理仓中，把按「每层自带 indexer」实现的 GLM-5/DeepSeek-DSA 代码适配为 GLM-5.2 的 **IndexShare** 结构：仅 `indexer_types="full"` 的层计算 top-k，后续 `"shared"` 层复用最近 full 层的 `topk_indices`，不构建 indexer 模块。GLM-5.2 真实结构（HF config/index 交叉锁定）：78 主层 + 1 MTP 层；indexer 权重仅在 22 层（full={0,1,2,6,10,…,74} + MTP），`index_topk_freq=4`、`index_skip_topk_offset=3`、`index_share_for_mtp_iteration=true`、`hidden_size=6144`。

## 触发与观测

GLM-5 NPU 代码假设 indexer 逐层存在（`generate_ignore_item`/`generate_li_hadamard_matrix` 逐层迭代 indexer），对 GLM-5.2 权重会因 shared 层缺 indexer 权重而无法加载/前向。适配后需验证：① shared 层不建 indexer 也能完成整网前向；② top-k 在层间正确传递。

## 探针与操作

实现为 8 处协同编辑（source 0 seq 549–603，编辑 diff 全文已在证据页核验）：

1. Attention `__init__`：按 `config.indexer_types[layer_idx]` 选择 full（建 indexer）/ shared（`indexer=None`）；MTP 以 `layer_idx = num_hidden_layers` 落入 full 分支。
2. `prepare_qkv`：签名加 `prev_topk_indices`；shared 层复用传入值。
3. `forward_absorb`/`forward_absorb_cp`：接收 `prev_topk_indices`、返回 `(output, topk_indices)`（CP 路径返回 `(prev, next)` 二元组）。
4. Attention `forward` 与 DecoderLayer `forward`：透传并返回 `topk_indices`。
5. 模型层循环（modeling_glm.py:1791）：`residual, hidden_states, prev_topk_indices = decoder_layer(...)` 跨层携带。
6. MTP forward：丢弃返回 top-k，保持原 `(residual, hidden_states)` 二元组契约。

验证素材：按 HF 真实 safetensors header 逐张量类核对 shape/dtype 后生成裁剪随机权重（decoder layer 0–7、experts 256→32、728 张量、22 GB；MTP 层含 eh_proj/enorm/hnorm/shared_head.norm）。

## 机制与判别

IndexShare 的机制区分点：top-k 由 full 层计算一次、shared 层消费（省去 shared 层 indexer 计算）；MTP 为 full 但单层无需共享。运行时结构判据：构建后模块树显示 `(0-2): 3x` full、`(3-5): 3x` shared、`(6)` full、`(7)` shared（source 0 seq 1359 区，digest）；失败 traceback 的调用链 model-loop:1793 → decoder:1571 → forward_absorb:966 → prepare_qkv:988 → `npu_mla_prolog_v3` 证明线程化路径实际执行（source 0 seq 1103）。

## 验证信号

端到端跑通（source 0 seq 1410/1412，A3 4 rank、CANN 9.0.0 兼容维度 q_lora=1536/qk_nope=128/v_head=128、NZ 权重）：

- `model run success`，日志 0 错误；整网前向覆盖 mla_prolog → IndexShare full/shared indexer → sparse flash attention → MoE EP；
- prefill 首编 1449.93 ms、warm 23.39 ms；decode ~35.8 ms/step；
- 输出为乱码 token——随机权重下的预期行为，验证层次为**结构执行正确**，非权重精度。

## 适用与失效边界

- 验证用的是裁剪 8 层 + 32 专家 + CANN-9.0.0 兼容注意力维度的随机权重；真实 78 层/256 专家/2048-192 维度需 CANN 9.1（见 w10-misc-s3-1），IndexShare 逻辑本身与维度无关但未在真实权重上复验。
- 共享粒度由 `index_topk_freq`/`index_skip_topk_offset` 决定（本例 4/3）；其它取值未测。
- `index_share_for_mtp_iteration` 的 MTP 迭代共享语义未单独实现/验证（本轨迹 next_n=0）。
- 精度对齐（与 HF 参考输出比对）未做，适配正确性的证据限于结构、加载与执行链。

## 附：断言存档

- GLM-5.2 IndexShare 适配的最小改动集：按 config.indexer_types[layer_idx] 决定 full 层建 indexer / shared 层 indexer=None，并把 prev_topk_indices 经 prepare_qkv→forward_absorb(_cp)→Attention.forward→DecoderLayer.forward→模型层循环（modeling_glm.py:1791）跨层线程化，各层返回 (output, topk_indices)；MTP 层为 full 但保持原 (residual, hidden_states) 二元组契约

```text
# GLM-5.2 IndexShare: carry the most recent "full" layer's top-k forward so that
        # "shared" layers can reuse it instead of running their own indexer.
        prev_topk_indices = None
        with superkernel_scope(self.enable_superkernel and not is_prefill, label, option):
            for decoder_layer in self.layers:
                residual, hidden_states, prev_topk_indices = decoder_layer(
                    hidden_states,
                    kv_len,
                    actual_seq_lengths_kv,
                    cos_sin=cos_sin,
                    actual_seq_lengths_q=actual_seq_lengths_q,
                    past_residual=residual,
                    position_ids=position_ids,
                    past_key_value=past_key_values,
                    past_key_values_indexer=past_key_values_indexer,
                    past_key_scales_indexer=past_key_scales_indexer,
                    is_prefill=is_prefill,
                    cur_topk_list=cur_topk_list,
                    slot_mapping=slot_mapping,
                    prefill_extra_input_dict=prefill_extra_input_dict,
                    offload_cache=offload_cache,
                    prev_topk_indices=prev_topk_indices,
                )
```

```text
        # Self Attention (returns this layer's top-k for GLM-5.2 IndexShare propagation)
        hidden_states, topk_indices = self.self_attn(
            hidden_states=hidden_states,
            kv_len=kv_len,
            actual_seq_lengths_kv=actual_seq_lengths_kv,
            cos_sin=cos_sin,
            actual_seq_lengths_q=actual_seq_lengths_q,
            position_ids=position_ids,
            past_key_value=past_key_value,
            past_key_values_indexer=past_key_values_indexer,
            past_key_scales_indexer=past_key_scales_indexer,
            is_prefill=is_prefill,
            slot_mapping=slot_mapping,
            prefill_extra_input_dict=prefill_extra_input_dict,
            offload_cache=offload_cache,
            prev_topk_indices=prev_topk_indices,
        )
```

```text
        # The MTP layer is a "full" indexer layer (computes its own top-k); there is a single
        # MTP layer so no cross-layer sharing is needed. Drop its returned top-k and keep the
        # existing (residual, hidden_states) contract.
        residual, hidden_states, _ = self.layers[str(self.mtp_start_layer_idx + mtp_layer_idx)](
```
