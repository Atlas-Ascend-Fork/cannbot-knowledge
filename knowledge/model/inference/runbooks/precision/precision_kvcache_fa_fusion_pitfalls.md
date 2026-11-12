---
type: Runbook
title: KVCache 静态化 + FA / FIA 融合算子替换的精度陷阱
description: FA/FIA 替换与 KVCache 写入的精度排查：区分连续缓存 kv_len_offset 与分页 block_table 寻址，按模型、GQA/TND、滑窗、MTP、量化分支核对 mask、长度和 MLA RoPE 旧版维度。
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
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-kvcache/SKILL.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_moe/models/modeling_qwen3_moe.py
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gpt_oss/models/modeling_gpt_oss.py
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/models/modeling_deepseek.py
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen/models/modeling_qwen.py
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-precision-debug/references/fa_debug_utils.md
  role: supporting
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-11-10T12:21:07Z'
platforms:
- agnostic
aliases:
- Decode mask 与 MTP 因果精度
- FA v1/v2 参数误用
- KVCache 写入与长度错位
- debug_fa_all_params
- MLA rope 维度约束
- 旧版 MLA query 512/128 与 RoPE 64 维约束
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

1. **按模型、缓存消费者和量化分支核对 mask**：Qwen Dense 的两阶段及 Qwen3-MoE BF16 Decode 用 `sparse_mode=3`+causal mask；Qwen3-MoE 的 **float8 KV Decode** 则用 `0`+`None` 并传对应反量化 scale。GPT-OSS 滑窗保留 band；R1 absorb/prolog 单 token 与 MTP 另分支。完整参数和长度见 [FIA 调用表](../../concepts/kernels/fused_infer_attention_score.md#按调用路径选择-sparse_mode-与-mask)。不能把“所有 Decode mask 置空”作为修复。
2. **kv_len 层内只读**：`kv_len` 在 attention/cache 内部不得被修改（禁层内递增），否则各层写入位置错位、精度彻底损坏。
3. **scatter_update_ 的 axis 须匹配 layout**：BSH → `axis=1`，TND → `axis=0`；不匹配则缓存写入偏移。
4. **多 batch 先区分连续与分页缓存**：`kv_len_offset = arange(0, batch*max_seq_len, max_seq_len)` 仅适用于按请求固定切片、每个切片跨度为 `max_seq_len` 的连续缓存，配合请求内位置形成线性写入索引；须检查位置没有越过对应切片。普通未压缩分页缓存应按 `block_table` 将逻辑块映射到物理块，不能用该线性偏移替代块表寻址；写入的 `slot_mapping` 与 FA 读取的块表须指向同一分组和分配。公式、非连续块反例及 RingCache/压缩缓存/Mamba 边界见 [普通分页缓存的物理槽位](../../concepts/frameworks/kv_cache_manager.md#普通分页缓存的物理槽位)。
5. **FA v1 vs v2 参数名不可混用**：`scale`↔`softmax_scale`、`num_heads`↔`num_query_heads`、`actual_seq_lengths`↔`actual_seq_qlen`、`actual_seq_lengths_kv`↔`actual_seq_kvlen`；量化参数要按两个接口独立核对，不能机械重命名。包装层可能报错，也可能改变缺省值，不能假定一定静默兜底。
6. **普通长度、累计边界和类型分开核对**：TND Query 常用 cumsum，单 token Decode 可为 `[1,2,...,B]`；Qwen Dense 的分页 Prefill 和 Decode 都取普通 KV 长度，Qwen3-MoE 直读当前 K/V 的 Prefill 才取累计 KV；不能按 TND 一律累加。host list/Tensor 也取决于重载与后端——见 [长度类型诊断](../runtime/fia_actual_seq_lengths_kv_backend_type.md)。用不等长 batch 验证请求隔离，等长测试不能发现全部错误。
7. **MLA absorb 模式**：key/value 共用 latent `cache_nope`，rope 分离。旧 Skill 表的 query D=512/128、rope D=64 和 sparse_mode 限制只作为特定版本的排查线索；先核对当前算子、模型及编译重载，不提升为所有 MLA API 的限制。YaRN 模型还需核对真实 scaling 和 mscale，不能只套 head_dim 的平方根。
8. **PA / NZ 格式**：MLA 写入的 `cache_mode="PA_NZ"` 与五维 NZ view 要匹配；普通 GQA 缓存不必套同一物理布局。block_table 的 dtype/块容量按接口确认，索引落在合法已分配块内，列数足以覆盖当前请求；使用上取整处理非整块长度，不能强制 `max_seq_len // block_size` 的下取整等式。压缩 causal/band mask 也不能直接按完整 KV 长度约束扩大。

全遮蔽行、`inner_precise` 与 BSH `Q_S=1` 的旧版接口边界见 [FIA v1 6.0 专节](../../concepts/kernels/fused_infer_attention_score.md#v1-60-的单-query-与全遮蔽行边界)，只在对应版本和产品约束内使用。

## 旧 FA 入参检查器的限制

旧 `debug_fa_all_params` / debug_atten_mask 材料对部分 Decode 分支统一要求 sparse_mode=0，并按默认布局推断 mask、长度或块数。这些假设不能覆盖当前 Qwen Dense/MoE、滑窗和 MTP；工具告警不替代本卡按模型分支的判断。使用默认参数还可能与真实调用不一致，诊断应记录实际 kwargs 和版本。

这里只保留检查器的失效边界与替代参数表，不把旧脚本原样搬进执行工作流。设备到 host 的 mask 校验会同步，排查“加探针现象改变”的内存/时序问题时不应机械插入它。

## 陷阱专例：PD 分离下 FIA 分支 KV item 长度漏乘 page_size

[SGLang](../../concepts/frameworks/sglang.md) 昇腾 [PD 分离](../../concepts/quantization/w8a8c8.md) 场景走 FIA 分支时，`kv_item_lens` 若对所有分支统一用 `get_key_buffer(i)[0].nbytes`，会漏乘 `page_size`——FIA 分支下 KV item 实际按 page_size 分页，单 item 长度应为 `nbytes * page_size`。长度算错使跨节点 KV item 传输错位、表现为精度问题。修法按 `use_fia` 分支：

```python
if self.use_fia:
    kv_item_lens = [self.get_key_buffer(i)[0].nbytes * self.page_size for i in ...] \
                 + [self.get_value_buffer(i)[0].nbytes * self.page_size for i in ...]
```

## 参考实现及其约束

- 陷阱清单来自固定模型和 Skill 的调试说明。旧工具把所有 Decode mode、TND 长度和 PA mask 统一判定的规则不能代替当前实现；容差须按算子、dtype、近零分母与任务精度确定，不把 BF16 `1e-3`、量化 `1e-2` 当统一验收线。
- PD 分离 kv_item_len 参考实现：cann-recipes-infer 的 qwen3-moe-sglang patch（`AscendTokenToKVPool.get_contiguous_buf_infos`）。
- 边界：固定参考的 FA 版本、路径和布局见 [FIA 参数卡](../../concepts/kernels/fused_infer_attention_score.md)。本卡不替代完整官方 API 规格，也没有执行 NPU 数值测试。

## Evidence

- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/328)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/205)（evidence）

- [.agents/skills/model-infer-kvcache/SKILL.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-kvcache/SKILL.md)（supporting）

- [models/qwen3_moe/models/modeling_qwen3_moe.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_moe/models/modeling_qwen3_moe.py)（supporting）

- [models/gpt_oss/models/modeling_gpt_oss.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gpt_oss/models/modeling_gpt_oss.py)（supporting）

- [models/deepseek_r1/models/modeling_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/models/modeling_deepseek.py)（supporting）

- [modeling_qwen.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen/models/modeling_qwen.py)（supporting）

- [.agents/skills/model-infer-precision-debug/references/fa_debug_utils.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-precision-debug/references/fa_debug_utils.md)（supporting）
