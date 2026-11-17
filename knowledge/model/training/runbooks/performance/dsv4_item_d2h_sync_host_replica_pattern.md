---
{
  "type": "Runbook",
  "title": "DSV4 host 元数据缓存：用生成代码核对 compiled region 的标量回读",
  "description": "在 eager 元数据构建处缓存 host 标量，并检查生成代码中的 _local_scalar_dense；记录中单卡结果无可测收益，不外推多卡加速。",
  "tags": [
    "task.implementation",
    "topic.data_movement"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-14T18:00:00Z",
  "updated_at": "2026-11-16T05:50:55Z",
  "platforms": []
}
---
# DSV4 host 元数据缓存：用生成代码核对 compiled region 的标量回读

## 适用场景

torchtitan-npu DSV4 压缩注意力元数据路径；host 已知的总长度或压缩块数被 compiled region 反复读取。

## 触发与观测

基线生成代码含 cu_seqlens 相关 _local_scalar_dense，提示存在设备标量回读。

## 探针与操作

对照元数据构建边界、缓存字段和所有消费点。下方差分只用于定位修改位置；完整迁移须核对 dataclass 构造、更新及缓存生命周期，再逐个统计生成代码。

原始源码差分或测试输出（用于核对）：

```text
diff --git a/torchtitan_npu/models/deepseek_v4/metadata.py b/torchtitan_npu/models/deepseek_v4/metadata.py
index bc3df71..74c7581 100644
--- a/torchtitan_npu/models/deepseek_v4/metadata.py
+++ b/torchtitan_npu/models/deepseek_v4/metadata.py
@@ -87,6 +87,11 @@ class CompressedBlockLayout:
     ``[n_seqs + 1]``.  Entry ``i`` is the global start index of sequence
     ``i``'s compressed blocks.  ``None`` for ratio-1 plans."""

+    n_cmp_blocks_host: int | None = None
+    """Host-cached ``cu_seqlens_cmp_k[-1]`` (total compressed blocks), set at
+    the eager plan-build boundary so ``_assemble_tnd`` avoids a per-layer
+    ``.item()`` D2H sync inside the compiled region."""
+
     block_remainder: torch.Tensor | None
     """Per-sequence block remainder (int32), ``[n_seqs]``: ``len[i] % ratio``
     trailing tokens of sequence ``i`` fall short of one full block and
@@ -172,6 +177,11 @@ class CompressedVarlenMetadata:
     independent window exchange + ori-stream assembly the Attention's
     ``swa_k`` gather consumes (``token_dispatcher.WindowPlan``)."""

+    seq_len_host: int | None = None
+    """Host-cached total token count (``cu_seq_q[-1]``), set once at the eager
+    ``build_compressed_varlen_metadata`` boundary so the ``seq_len`` property
+    avoids a per-layer ``.item()`` D2H sync inside the compiled region."""
+
     @property
     def batch_size(self) -> int:
         """Container batch size (``1`` for the current packed scenario)."""
@@ -180,6 +190,8 @@ class CompressedVarlenMetadata:
     @property
     def seq_len(self) -> int:
         """Container sequence length (the total token count)."""
+        if self.seq_len_host is not None:
+            return self.seq_len_host
         return int(self.varlen.cu_seq_q[-1].item())


@@ -271,6 +283,7 @@ def build_kernel_layout(
         first_indices = cu_seqs[:-1][torch.diff(cu_seqs) > 0].to(torch.int64)
         plans[ratio] = CompressedBlockLayout(
             cu_seqlens_cmp_k=cu_seqs,
+            n_cmp_blocks_host=int(cu_seqs[-1].item()),
             block_remainder=torch.tensor(
                 [length % ratio for length in lengths],
                 dtype=torch.int32,
@@ -302,7 +315,11 @@ def build_compressed_varlen_metadata(
         compress_ratios: Compression ratios present in the model.
     """
     plans = build_kernel_layout(varlen, compress_ratios)
+    # Cache the total token count on the host so the ``seq_len`` property
+    # avoids a per-layer ``.item()`` D2H sync inside the compiled region.
+    # Built once here (eager boundary) from ``cu_seq_q[-1]``.
     return CompressedVarlenMetadata(
         varlen=varlen,
         plans=plans,
+        seq_len_host=int(varlen.cu_seq_q[-1].item()),
     )
```

原始源码差分或测试输出（用于核对）：

```text
diff --git a/torchtitan_npu/override/deepseek_v4/sparse_attn/cann.py b/torchtitan_npu/override/deepseek_v4/sparse_attn/cann.py
index eb5c4eb..dca764c 100644
--- a/torchtitan_npu/override/deepseek_v4/sparse_attn/cann.py
+++ b/torchtitan_npu/override/deepseek_v4/sparse_attn/cann.py
@@ -577,7 +577,12 @@ class CANNCompressedSparseInnerAttention(CompressedSparseInnerAttention):
         TND stream (``[T_cmp, 1, D]``)."""
         asm = plan.cmp_k_global_gather_indices
         flat = container.flatten(0, 1)
-        return (flat[asm] if asm is not None else flat[: plan.cu_seqlens_cmp_k[-1]]).unsqueeze(1).contiguous()
+        if asm is not None:
+            return flat[asm].unsqueeze(1).contiguous()
+        n = plan.n_cmp_blocks_host
+        if n is None:
+            n = int(plan.cu_seqlens_cmp_k[-1].item())
+        return flat[:n].unsqueeze(1).contiguous()
```

## 机制与判别

记录中的实现增加 n_cmp_blocks_host 和 seq_len_host，在 eager 构建时获取并供 compiled region 消费。该方案需要保证 host 副本与设备元数据同版本；不能只替换一个 .item() 而忽略其他消费点或动态更新。

## 验证信号

截断输出显示 19 个修改版 output_code.py 样本的 _local_scalar_dense 计数为 0，排序后前 10 个基线样本为 3；不能据此断言总文件数或所有文件均如此。单卡浅 stream 的稳定 fwd_bwd 观测两边均约 1.61s，不支持加速。

## 适用与失效边界

不采纳单位未核定的其他 profiling 时长作为本次收益。长序列、多卡、动态元数据及 backward 深队列需要各自复测；缓存失效策略必须随源元数据更新。
