---
{
  "type": "Runbook",
  "title": "DSV4.1 尾窗 tail qsl 与消费端 padded batch 维度错位的双层修复（plan 预填充 + 消费端防御补齐）",
  "description": "DSV4.1 尾窗特性的 tail_query_start_loc_full 只有真实请求条数（num_real_reqs+1），而消费端 batch_size 仍取含 graph/DP padding 请求的行数——DP padding/对齐步会错位调度，impl 侧 replace 后的 query_start_loc 同样偏短。修复双层结构：plan 构造时预填充到 padded_num_reqs=len(common.seq_lens)（尾值重复=padding 请求零长度 span，与全量契约一致）+ 消费端 _padded_tail_query_start_loc 按 cache_seq_lens.shape[0] 防御性补齐（正常路径 no-op）。",
  "tags": [
    "task.implementation",
    "topic.attention"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# DSV4.1 尾窗 tail qsl 与消费端 padded batch 维度错位的双层修复（plan 预填充 + 消费端防御补齐）


## 摘要

DSV4.1 尾窗特性的 tail_query_start_loc_full 只有真实请求条数（num_real_reqs+1），而消费端 batch_size 仍取含 graph/DP padding 请求的行数——DP padding/对齐步会错位调度，impl 侧 replace 后的 query_start_loc 同样偏短。修复双层结构：plan 构造时预填充到 padded_num_reqs=len(common.seq_lens)（尾值重复=padding 请求零长度 span，与全量契约一致）+ 消费端 _padded_tail_query_start_loc 按 cache_seq_lens.shape[0] 防御性补齐（正常路径 no-op）。

## 适用场景

vllm-ascend-dsnext wzc_indexer 新基线下，DSV4.1 尾窗特性（尾部层只算每请求最后 W 个 token）的错位审查与修复。任何“tail 行几何 vs 全量批几何”并存、且消费端 batch 维度含 padding 行的元数据构造都适用。

## 触发与观测

触发：分支切换并 pick indexer 改动（新提交 23c5ae08c/4127ce72a 把 QLI/QSLI 预计算进 builder），尾窗需要 tail 变体元数据。
观测（审查发现的错位）：全量版 cu_seqlens_q 与 batch_size=cache_seq_lens 行数一致；tail 版只有 num_real_reqs+1 条而 batch_size 含 padding 行——DP padding/graph 对齐步 batch 维度错位（静默）。

## 探针与操作

审查 tail_query_start_loc_full 的条数（num_real_reqs+1）与消费端 batch_size（cache_seq_lens.shape[0]）是否一致；在 DP padding/graph 对齐步核对 plan 侧与消费端的请求计数。

## 机制与判别

双层修复结构：
- plan 侧预填充：构造 tail_query_start_loc_full 时补齐到 padded_num_reqs=len(common.seq_lens)，尾值重复 = padding 请求零长度 span（与其 cache_seq_lens 清零行、block_table 占位行一致，与全量契约相同）。
- 消费端防御：`_padded_tail_query_start_loc(plan, batch_size)` 按 cache_seq_lens.shape[0] 补齐，正常路径 no-op。

## 适用与失效边界

- 轨迹内未执行设备复测。

## 验证信号

### 来源结论b

> 审查发现的真问题——padding 步 batch 维度错位：全量版 cu_seqlens_q=qsl[:common.num_reqs+1] 与 batch_size=cache_seq_lens.shape[0]=common.num_reqs 一致；tail 版 tail_query_start_loc_full 只有 num_real_reqs+1 条（plan builder 里 num_reqs=min(len(seq_values), num_real_reqs) 截断），而 batch_size 仍取含 graph/DP padding 请求的行数——DP padding/对齐步会错位调度且 impl 侧 replace 后的 query_start_loc 同样偏短，直连 select_quantized。修复双层结构：plan 构造时预填充到 padded_num_reqs=len(common.seq_lens)（尾值重复=padding 请求零长度 span，与全量契约一致）；消费端 _padded_tail_query_start_loc 按 cache_seq_lens.shape[0] 防御性补齐（正常路径 no-op）。


## 补充机制片段

### 机制片段

```
diff --git a/vllm_ascend/attention/dsa_v41.py b/vllm_ascend/attention/dsa_v41.py
index 721fb5383..9743c05d6 100644
--- a/vllm_ascend/attention/dsa_v41.py
+++ b/vllm_ascend/attention/dsa_v41.py
@@ -188,6 +188,22 @@ def _assert_decode_rows_first(common: Any, num_reqs: int, num_decodes: int) -> N
         )


+def _padded_tail_query_start_loc(plan: dict, batch_size: int) -> torch.Tensor:
+    """Tail-window query layout padded to ``batch_size + 1`` entries.
+
+    The plan clips to the real requests, while the operators take the batch
+    size from the cache-side tensors (which include DP/graph padding rows).
+    The phantom rows are appended with a constant cumulative value, i.e. as
+    zero-length requests, mirroring the DSpark drafter's tail padding.
+    """
+    qsl = plan["tail_query_start_loc_full"]
+    if qsl.shape[0] >= batch_size + 1:
+        return qsl
+    return torch.cat(
+        [qsl, qsl.new_full((batch_size + 1 - qsl.shape[0],), qsl[-1])]
+    )
+
+
 def _prepare_private_circle_plan(
     common: Any,
     shared: dict,
@@ -214,6 +230,7 @@ def _prepare_private_circle_plan(
     qsl_values = qsl.tolist()
     seq_values = common.seq_lens.tolist()
     num_reqs = len(seq_values)
+    padded_num_reqs = num_reqs
     if num_real_reqs is not None:
         # common.seq_lens carries padded rows on graph/DP-aligned steps;
         # padding rows hold no allocations and must not enter the plan.
@@ -410,8 +427,17 @@ def _prepare_private_circle_plan(
                 torch.tensor(tail_qsl_values[num_decodes:], dtype=qsl.dtype, device=device)
                 - tail_qsl_values[num_decodes]
             ).contiguous(),
+            # The full tail batch spans the real requests only, but consumers
+            # pair it with batch-dimension tensors that keep the padded
+            # request count (cache_seq_lens for the QLI/QSLI builds, the
+            # impl's replaced query_start_loc feeding select_quantized).
+            # Pad with the trailing value so padding requests carry
+            # zero-length spans, mirroring how the full-batch query_start_loc
+            # stays consistent with batch_size on graph/DP-aligned steps.
             "tail_query_start_loc_full": torch.tensor(
-                tail_qsl_values, dtype=qsl.dtype, device=device
+                tail_qsl_values + [tail_qsl_values[-1]] * (padded_num_reqs - num_reqs),
+                dtype=qsl.dtype,
+                device=device
             ),
             "tail_max_query_len": max(all_keeps, default=1),
             # Workspace-local start of the kept rows per prefill request.
@@ -1353,7 +1379,9 @@ class DeepseekV41EagerAttentionImpl:
                 )
             source_metadata = replace(
                 source_metadata,
-                query_start_loc=plan["tail_query_start_loc_full"],
+                query_start_loc=_padded_tail_query_start_loc(
+                    plan, int(source_metadata.cache_seq_lens.shape[0])
+                ),
                 max_query_len=plan["tail_max_query_len"],
                 qli_metadata=source_metadata.qli_metadata_tail,
                 qsli_metadata=source_metadata.qsli_metadata_tail,
@@ -2796,9 +2824,14 @@ class DeepseekV41MetadataBuilder(AttentionMetadataBuilder[DeepseekV41Metadata]):
                 # Index sources above the KV-source boundary run on the gathered
                 # tail rows, so their scheduling metadata (cu_seqlens_q, and the
                 # per-row candidate_block_length) must describe the tail layout.
+                # The query layout is padded to the cache-side batch size so the
+                # operators see one request per seqused_k row.
+                tail_qsl = _padded_tail_query_start_loc(
+                    step_plan, int(coordinates["cache_seq_lens"].shape[0])
+                )
                 qli_metadata_tail = self._build_qli_metadata(
                     shared,
-                    step_plan["tail_query_start_loc_full"],
+                    tail_qsl,
                     coordinates["cache_seq_lens"],
                     cmp_residual_buffer,
                     ratio,
@@ -2812,7 +2845,7 @@ class DeepseekV41MetadataBuilder(AttentionMetadataBuilder[DeepseekV41Metadata]):
                         positions.index_select(0, tail_idx),
                         int(tail_idx.numel()),
                         int(tail_idx.numel()),
-                        step_plan["tail_query_start_loc_full"],
+                        tail_qsl,
                         coordinates["cache_seq_lens"],
                         ratio,
                         max_seqlen_q,
```
