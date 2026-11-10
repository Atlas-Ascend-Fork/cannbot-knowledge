---
{
  "type": "Runbook",
  "title": "CANN 9.1.0/Ascend950 FA 算子能力判别：sink 与 DSA top-k 不可兼得及 DSA no-op 判定",
  "description": "把带可学习 sink + DSA（indexed attention top-k 稀疏）+ MLA 的模型切到融合 FA 算子前，可用三条探针判别：torch_npu 算子注册检查、op schema 打印、CANN kernel 目录核对。实测 npu_fused_infer_attention_score_v2 有 learnable_sink 但无 sparse_indices；npu_sparse_flash_attention 有 sparse_indices 但无 sink 入参；sparse_flash_mla 两者兼备但需 DSv4 式重构。当 index_topk ≥ kv_len 时 DSA 是 no-op（top-k 全选），dense FA 与 eager 等价。",
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

# CANN 9.1.0/Ascend950 FA 算子能力判别：sink 与 DSA top-k 不可兼得及 DSA no-op 判定

## 适用场景

- 模型/框架：带**可学习 attention sink** + **DSA（indexed attention，top-k 稀疏）** + **MLA（rope 分离 / 压缩 latent）** 的模型（本例 HYV4：`index_topk=2048`、`index_head_dim=128`、`kv_lora_rank=512`、`qk_rope_head_dim=64`），要切到 torch_npu 融合 FA 算子（独立部署，Runner 自管 KV）。
- 平台/版本：Ascend950PR_9589 单卡 + CANN 9.1.0 + torch_npu 2.12.0（`${LOCAL_PATH_1}`，系统 `/usr/local/Ascend` 的 CANN 缺 ascend950 ops_nn，不可用）。
- 目标：在动手改造前判别哪个 FA 算子能同时承载 sink 与 DSA 稀疏语义。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_2}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_3}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

- 触发（事件 2，阶段 2.1 任务书）：当前 KV 为自管 concat 动态缓存，需评估「Paged Attention + FA 融合算子」升级方向，并判定 sink、DSA 稀疏 mask、top-k 索引能否与 FA（含 MLA absorb）兼容。
- 关键观测（事件 127，op schema 实测打印）：两个标准 FA 算子的入参集合互斥地缺少对方的关键能力。
  - `npu_fused_infer_attention_score_v2`：有 `Tensor? learnable_sink=None`，**没有** `sparse_indices`；
  - `npu_sparse_flash_attention`：有必选 `Tensor sparse_indices`，**没有** sink 入参。

## 探针与操作

三条可复现探针（在 `. ./env.sh` 后用部署 venv 的 python 执行）：

1. 算子注册检查（事件 110/111）：

```bash
PY=${LOCAL_PATH_2}; "$PY" -c "
import torch, torch_npu
for op in ['npu_fused_infer_attention_score','npu_fused_infer_attention_score_v2','npu_sparse_flash_attention','npu_kv_quant_sparse_flash_attention','npu_lightning_indexer','npu_kv_rmsnorm_rope_cache','npu_scatter_nd_update_']:
    print(f'{op:42s}', hasattr(torch_npu, op))"
```

实测全部 `True`（事件 111）。

2. schema 打印（事件 126/127）：

```bash
"$PY" -c "
import torch, torch_npu
schemas = torch._C._jit_get_all_schemas()
want = ['npu::npu_sparse_flash_attention','npu::npu_fused_infer_attention_score_v2', ...]
for s in schemas:
    if str(s.name) in want:
        print('='*100); print(s)"
```

3. 自定义包与 kernel 目录核对（事件 134/135、146/147、158/159）：

```bash
"$PY" -c "import torch, cann_ops_transformer; print(hasattr(torch.ops.cann_ops_transformer, 'sparse_flash_mla'))"
ls ${LOCAL_PATH_3} | grep -iE "sparse|attention"
```

## 机制与判别

### 算子能力矩阵（CANN 9.1.0 / ascend950，实测 schema + kernel 目录）

| 算子 | sink | DSA top-k | MLA(rope 分离) | Paged |
|---|---|---|---|---|
| `npu_fused_infer_attention_score_v2` | ✅ `learnable_sink`（但受 value d ≤ 128 约束，见本组来源观测 [FA v2 learnable_sink 在 MLA absorb（value d=512）下 tiling 失败，用 return_softmax_lse 精确 sink 校正替代](learnable_sink_mla_absorb_value_tiling.md)） | ❌ 无 `sparse_indices` | ✅ `query_rope`/`key_rope` | ✅ `block_table` |
| `npu_sparse_flash_attention` | ❌ 无 sink 入参 | ✅ `sparse_indices` | ✅ `attention_mode=2` + `query_rope`/`key_rope` | ✅ `PA_BSND` |
| `cann_ops_transformer.sparse_flash_mla` | ✅ `sinks` | ✅ `ori_sparse_indices` | ✅（DSv4 式：rope 并入 q/kv） | ✅ |
| `npu_lightning_indexer` | — | ✅ 产 top-k | — | ✅ |

事件 127 实测 schema 原文（关键两行）：

```
npu::npu_sparse_flash_attention(Tensor query, Tensor key, Tensor value, Tensor sparse_indices, float scale_value, *, Tensor? block_table=None, Tensor? actual_seq_lengths_query=None, Tensor? actual_seq_lengths_kv=None, Tensor? query_rope=None, Tensor? key_rope=None, int sparse_block_size=1, str layout_query="BSND", str layout_kv="BSND", int sparse_mode=3, int pre_tokens=9223372036854775807, int next_tokens=9223372036854775807, int attention_mode=0, bool return_softmax_lse=False) -> (Tensor, Tensor, Tensor)
```

```
npu::npu_fused_infer_attention_score_v2(Tensor query, Tensor key, Tensor value, *, Tensor? query_rope=None, Tensor? key_rope=None, Tensor? pse_shift=None, Tensor? atten_mask=None, SymInt[]? actual_seq_qlen=None, SymInt[]? actual_seq_kvlen=None, Tensor? block_table=None, Tensor? dequant_scale_query=None, Tensor? dequant_scale_key=None, Tensor? dequant_offset_key=None, Tensor? dequant_scale_value=None, Tensor? dequant_offset_value=None, Tensor? dequant_scale_key_rope=None, Tensor? quant_scale_out=None, Tensor? quant_offset_out=None, Tensor? quant_scale_p=None, Tensor? learnable_sink=None, int num_query_heads=1, int num_key_value_heads=0, float softmax_scale=1., int pre_tokens=2147483647, int next_tokens=2147483647, str input_layout="BSH", int sparse_mode=0, int block_size=0, int query_quant_mode=0, int key_quant_mode=0, int value_quant_mode=0, int inner_precise=0, bool return_softmax_lse=False, int? query_dtype=None, int? key_dtype=None, int? value_dtype=None, int? query_rope_dtype=None, int? key_rope_dtype=None, int? key_shared_prefix_dtype=None, int? value_shared_prefix_dtype=None, int? dequant_scale_query_dtype=None, int? dequant_scale_key_dtype=None, int? dequant_scale_value_dtype=None, int? dequant_scale_key_rope_dtype=None, int? out_dtype=None) -> (Tensor, Tensor)
```

### 判别一：sink 与 DSA 不可兼得

sink 与 DSA top-k 稀疏在 CANN 9.1.0 标准 FA 算子上不可兼得：npu_fused_infer_attention_score_v2 提供 learnable_sink 入参但没有 sparse_indices 入参，npu_sparse_flash_attention 提供 sparse_indices 入参但没有 sink 入参。cann_ops_transformer.sparse_flash_mla 在本机已注册且 ascend950 kernel 目录存在，原生同时支持 sinks 与 ori_sparse_indices，但要求 DeepSeek-V4 式投影重构，本组来源观测只确认了算子注册与 kernel 目录存在，未做运行时验证。

参考实现旁证（事件 178）：同款 MLA+DSA 的 `cann-recipes-infer/models/deepseek_v3_2_exp` 在 DSA 路径用 `npu_sparse_flash_attention`（`query_rope=q_pe`、`key_rope=k_pe`、`"attention_mode": 2`），其注意力层 `attn_type = "FullAttention"`、`cache_entries` 为 `nope_cache` + `indexer_key_cache`（+ 非量化 `rope_cache`）。

### 判别二：DSA no-op 判定

当 index_topk ≥ kv_len 时 DSA 为 no-op：模型 topk 取 min(index_topk, kv_len) 全选，dense FA 与 eager 等价；本部署 index_topk 默认 2048，固定 prompt 13 token、8 步 decode 后总长 21，全程全选。代码依据（vendored 模型 `HYV4Indexer.forward`，事件 130 原文）：

```python
        topk = min(self.index_topk, index_scores.shape[-1])
        return index_scores.topk(topk, dim=-1).indices.to(torch.int32)  # [B, S, topk]
```

配置依据（事件 126）：`index_topk: int = 2048` 为默认值；负载依据（事件 170）：`cpu_golden.json` 记录 `input_ids` 13 token、`max_new_tokens=8`、`total_len: 21`。

### 判别三：算子选择分支

对 sink+DSA 模型的算子选择判别：kv_len ≤ index_topk 时选 FA v2 dense + learnable_sink（与 eager 等价且保留 sink）；kv_len > index_topk 的长上下文需 npu_sparse_flash_attention + return_softmax_lse 后置 sink 校正，或改用 sparse_flash_mla；直接使用无 sink 入参的 sparse FA 会静默丢失 sink 语义。

## 验证信号

- 事件 111：`npu_fused_infer_attention_score` / `_v2` / `npu_sparse_flash_attention` / `npu_kv_quant_sparse_flash_attention` / `npu_lightning_indexer` / `npu_quant_lightning_indexer` / `npu_kv_rmsnorm_rope_cache` / `npu_scatter_nd_update_` / `npu_mla_prolog_v3` 注册检查全部 `True`。
- 事件 127：两条 schema 原文（见上）——入参集合差异即为「不可兼得」的直接证据。
- 事件 131/135：`cann_ops_transformer` 可 import；`sparse_flash_mla True`，包内 sparse/mla/attn 类算子共 1 个。
- 事件 147/159：`.../ascend950/ops_transformer/` 下 `sparse_flash_attention`、`sparse_flash_mla`、`block_sparse_attention`、`fused_infer_attention_score_apt` 等 kernel 目录实测存在（.o/.json 就位）。
- 证据等级：全部为单机只读探针（schema/目录/注册表），未运行算子内核本身；本判别为选型判据，不涉及性能结论。

## 适用与失效边界

- 适用：CANN 9.1.0 + ascend950（Ascend950PR）+ torch_npu 2.12.0 上的 FA 算子选型；同代环境可直接复用三条探针。
- 失效/风险：
  - 算子能力随 CANN 版本变化，换版本需重跑 schema/kernel 探针，勿照抄结论。
  - `sparse_flash_mla` 需要 DSv4 式「rope 并入 q/kv」的投影重构；其 kernel 目录存在 ≠ 运行时可用（`cann_ops_transformer` 来自部署 venv 而非 env.sh 的 CANN，引入额外依赖）。
  - 直接用 `npu_sparse_flash_attention` 而不做 sink 补偿会**静默丢 sink**（schema 无 sink 入参），属精度回归而非报错。
  - DSA no-op 判定依赖 `index_topk` 与实际 kv_len 的相对大小：kv_len > index_topk（长上下文）时该判别不再成立，必须切 sparse 路径。
  - `learnable_sink` 即使命中 v2 也受「value d ≤ 128」约束（见 [FA v2 learnable_sink 在 MLA absorb（value d=512）下 tiling 失败，用 return_softmax_lse 精确 sink 校正替代](learnable_sink_mla_absorb_value_tiling.md)），MLA absorb 场景不可用。
