---
type: Runbook
title: KVCache 静态化 + FA / FIA 融合算子替换的精度陷阱
description: KVCache 静态化 + FA / FIA 融合算子替换的精度陷阱。把手写 attention 换成 npu_fused_infer_attention_score(FA/FIA) 融合算子 + 静态 KVCache 后，Prefill 对但 Decode 偏、输出全重复 token / 乱码、多 batch 部分样本错、量化模式偏差放大。这类精度问题几乎都出在 FA 入参与 layout 约定、KVCache 写入位置、KV 长度语义上，而非注意力数学本身。按症状对号入座定位。
tags:
- task.debugging
- topic.attention
- topic.kv_cache
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/328
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/205
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# KVCache 静态化 + FA / FIA 融合算子替换的精度陷阱

## 适用场景

把手写 attention 换成 [npu_fused_infer_attention_score](../../concepts/kernels/fused_infer_attention_score.md)(FA/FIA) 融合算子 + 静态 KVCache 后，Prefill 对但 Decode 偏、输出全重复 token / 乱码、多 batch 部分样本错、量化模式偏差放大。这类精度问题几乎都出在 **FA 入参与 layout 约定、KVCache 写入位置、KV 长度语义**上，而非注意力数学本身。按症状对号入座定位。

## 症状 → 优先排查

| 症状 | 可能根因 | 优先排查 |
|------|---------|---------|
| 输出全重复 token / 乱码 | KVCache 写入位置错误 | slot_mapping / scatter_update_ 参数 |
| 首 token 正确、后续偏移 | Decode kv_len 更新错误 | kv_len 生命周期 |
| Prefill 正确、Decode 偏差大 | Decode FA 入参错误 | sparse_mode / actual_seq_lengths |
| NaN/Inf | 数值溢出 | scale、dtype |
| 多 batch 部分样本错 | batch 间缓存交叉污染 | block_table / kv_len_offset |
| 量化模式偏差显著放大 | 量化参数不匹配 | dequant_scale / antiquant_mode |

## 关键陷阱与修法

1. **sparse_mode 分 Prefill / Decode**：Prefill=3（rightDownCausal，必传 `(2048,2048)` 下三角 mask），Decode=0（defaultMask，`atten_mask=None`）。Decode 误用 `sparse_mode=3` → 偏差大。
2. **kv_len 层内只读**：`kv_len` 在 attention/cache 内部不得被修改（禁层内递增），否则各层写入位置错位、精度彻底损坏。
3. **scatter_update_ 的 axis 须匹配 layout**：BSH → `axis=1`，TND → `axis=0`；不匹配则缓存写入偏移。
4. **多 batch 缓存交叉**：`kv_len_offset = arange(0, batch*max_seq_len, max_seq_len)` 按 max_seq_len 对齐，避免 batch 间交叉污染。
5. **FA v1 vs v2 参数名不可混用**（传错名精度崩溃 / 被默认值兜底）：`scale`↔`softmax_scale`、`num_heads`↔`num_query_heads`、`actual_seq_lengths`↔`actual_seq_qlen`、`actual_seq_lengths_kv`↔`actual_seq_kvlen`、`antiquant_scale/offset`↔`dequant_scale_key/value`。
6. **actual_seq_lengths 构造随 layout**：TND 用 cumsum，BSH/BNSD 用原始值；Decode 时 `actual_seq_qlen` 每值通常为 1（MTP 除外）。此外 `actual_seq_lengths_kv` 的**类型随后端不同**（host list vs Tensor），传错类型直接 schema 报错——见 [fia-actual-seq-lengths-kv-backend-type](../runtime/fia_actual_seq_lengths_kv_backend_type.md)。
7. **MLA absorb 模式**：FA 中 key 与 value 都传 `cache_nope`（key=value=latent）；rope D 必须 64、query D 仅支持 512/128，D=512 时 sparse_mode 仅支持 0/3/4。
8. **PA / NZ 格式**：`cache_mode="PA_NZ"`；`block_table` dtype 必须 int32、值域 `[0, total_blocks)` 排列且 `numel == batch_size × (max_seq_len // block_size)`；PA mask 末维 ≥ `block_table 第二维 × block_size`。

## 陷阱专例：PD 分离下 FIA 分支 KV item 长度漏乘 page_size

[SGLang](../../concepts/frameworks/sglang.md) 昇腾 [PD 分离](../../concepts/quantization/w8a8c8.md) 场景走 FIA 分支时，`kv_item_lens` 若对所有分支统一用 `get_key_buffer(i)[0].nbytes`，会漏乘 `page_size`——FIA 分支下 KV item 实际按 page_size 分页，单 item 长度应为 `nbytes * page_size`。长度算错使跨节点 KV item 传输错位、表现为精度问题。修法按 `use_fia` 分支：

```python
if self.use_fia:
    kv_item_lens = [self.get_key_buffer(i)[0].nbytes * self.page_size for i in ...] \
                 + [self.get_value_buffer(i)[0].nbytes * self.page_size for i in ...]
```

## 参考实现及其约束

- 陷阱清单参考实现：cann-recipes-infer 的 `.agent/skills/kvcache-fa-precision-debug` skill（配 `debug_fa_all_params()` 一键校验），覆盖 GQA/MHA（qwen3-moe、gpt-oss）与 MLA absorb（deepseek-r1、kimi-k2-thinking），判定阈值 BF16 `max_rel<1e-3`、量化 `<1e-2`。
- PD 分离 kv_item_len 参考实现：cann-recipes-infer 的 qwen3-moe-sglang patch（`AscendTokenToKVPool.get_contiguous_buf_infos`）。
- 边界：MLA rope D 约束、FA v1/v2 参数名为本仓 skill 披露的落地约定，未独立比对上游算子规格；范围限定 KVCache 静态化 + FA/FIA 替换场景。

## Evidence

- diff 事实（@73ed847）：SKILL.md 的症状分类 / 快速验证清单 / 常见精度陷阱表 / 附录 F.1–F.6 逐条对上；本仓 skill 文档。溯源下探 [cann-recipes-infer-pr-328-feat-add-agent-optimization-skills-and-evaluation-reports](https://gitcode.com/cann/cann-recipes-infer/merge_requests/328)
- diff 事实（@50e41b5b8220）：patch 按 `use_fia` 给 `kv_item_lens` 乘 `page_size`（+16/-7），根因由 diff 结构直接可读。溯源下探 [cann-recipes-infer-pr-205-feat-support-qwen3-moe-sglang](https://gitcode.com/cann/cann-recipes-infer/merge_requests/205)
