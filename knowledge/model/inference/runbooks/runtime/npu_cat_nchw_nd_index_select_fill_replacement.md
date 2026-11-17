---
{
  "type": "Runbook",
  "title": "NPU cos/sin padding 的格式冲突：用完整索引选择替代跨格式拼接",
  "description": "针对 cos/sin padding 的 NCHW/ND 拼接报错，保留补齐索引后单次 index_select、再填充 padding 的代码改动；本记录只有静态检查和用户反馈，未绑定设备终验。",
  "tags": [
    "task.debugging",
    "topic.graph_execution"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-14T18:00:00Z",
  "updated_at": "2026-11-16T05:50:55Z",
  "platforms": []
}
---
# NPU cos/sin padding 的格式冲突：用完整索引选择替代跨格式拼接

## 适用场景

vllm-ascend 的 DSV4 compressor cos/sin 预计算；已有张量与新建 padding 张量的 NPU 格式不同。具体芯片和 CANN 版本未确认。

## 触发与观测

原代码将 index_select 的输出与 ones/zeros 拼接，出现格式不兼容。源码中 cos/sin 经 unsqueeze 成为四维张量。

## 探针与操作

分别核对两个输入的格式、shape 和 padding 长度。下面是记录中的修改单元；迁移前须确认 total_valid、num_compressed_tokens 与索引范围一致。

完整相关改动：替换 cos/sin 路径、删除旧 cat、保留 slot_mapping padding：

```text
--- before
+++ after
@@ -1,6 +1,17 @@
         rope_indices = compressed_pos * cmp_ratio
-        compress_cos = full_compress_cos.index_select(0, rope_indices.long())
-        compress_sin = full_compress_sin.index_select(0, rope_indices.long())
+        # Pad rope_indices to num_compressed_tokens before index_select to avoid
+        # torch.cat between NCHW (from index_select) and ND (from torch.ones) tensors.
+        num_pad = num_compressed_tokens - total_valid
+        if num_pad > 0:
+            padded_indices = torch.zeros(num_compressed_tokens, dtype=torch.long, device=device)
+            padded_indices[:total_valid] = rope_indices
+            compress_cos = full_compress_cos.index_select(0, padded_indices)
+            compress_sin = full_compress_sin.index_select(0, padded_indices)
+            compress_cos[total_valid:].fill_(1.0)
+            compress_sin[total_valid:].fill_(0.0)
+        else:
+            compress_cos = full_compress_cos.index_select(0, rope_indices)
+            compress_sin = full_compress_sin.index_select(0, rope_indices)

         block_id_col = compressed_pos // block_size
         block_offset = compressed_pos % block_size
@@ -17,12 +28,8 @@
             slot_col1 = torch.where(invalid_mask, torch.full_like(block_offset, block_size - 1), block_offset)
             compress_slot_mapping = torch.stack([slot_col0, slot_col1], dim=-1).to(torch.int32)

-        num_pad = num_compressed_tokens - total_valid
+        # Pad slot_mapping to num_compressed_tokens
         if num_pad > 0:
-            pad_cos = torch.ones((num_pad, rope_dim), dtype=full_compress_cos.dtype, device=device)
-            pad_sin = torch.zeros((num_pad, rope_dim), dtype=full_compress_sin.dtype, device=device)
-            compress_cos = torch.cat([compress_cos, pad_cos], dim=0)
-            compress_sin = torch.cat([compress_sin, pad_sin], dim=0)
             if slot_mapping_format == 1:
                 pad_slots = torch.full((num_pad,), -1, dtype=torch.int32, device=device)
             else:
```

## 机制与判别

把索引补到完整长度后只做一次 index_select，再把尾部 padding 的 cos 填为 1、sin 填为 0，可在该改动中避开两种格式张量的 cat。该代码结构不等于设备执行或数值一致性已经通过。

## 验证信号

工具记录证明编辑已应用且 ruff 返回 All checks passed。用户随后反馈工作正常；这是用户复测陈述，没有对应的原始设备输出，故本卡不记为 device_functional。

## 适用与失效边界

尚未核验整理后片段的真实设备执行、图捕获与下游精度。需检查空输入、索引越界、padding 是否被消费，以及原地填充是否符合模型语义。
