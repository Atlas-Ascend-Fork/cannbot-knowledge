---
{
  "type": "Runbook",
  "title": "DSV4 npu_rope interleaved cos/sin 预计算缓存（PR#407/issue#72）",
  "description": "torchtitan-npu 的 DeepSeek-V4 训练使用 npu_rope converter（npu_rotary_mul interleave 模式）且开启 activation checkpoint / recompute 的场景：原实现每次 forward 都从 complex cache 临时展开 cos/sin（repeat_interleave），在 full-size 模型（v4_flash 43 层、rope_head_dim=64）上造成 forward/recompute 劣化。合并 PR#401 global TND 后需重验证 rope cache 与 TND 路径的兼容性。",
  "tags": [
    "task.implementation",
    "topic.precision"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# DSV4 npu_rope interleaved cos/sin 预计算缓存（PR#407/issue#72）

## 适用场景
torchtitan-npu 的 DeepSeek-V4 训练使用 npu_rope converter（npu_rotary_mul interleave 模式）且开启 activation checkpoint / recompute 的场景：原实现每次 forward 都从 complex cache 临时展开 cos/sin（repeat_interleave），在 full-size 模型（v4_flash 43 层、rope_head_dim=64）上造成 forward/recompute 劣化。合并 PR#401 global TND 后需重验证 rope cache 与 TND 路径的兼容性。

## 触发与观测
- 触发：issue#72 报告 npu_rope converter 的 repeat_interleave 开销（PR 引用：修复前 q_rope forward -22%~-27%、kv_rope forward -82%~-93% vs rope OFF）；本任务为 PR#407 rebase 到含 PR#401 的 master 后的重新验证（TND 场景分析 + 单测 + 训练对比 + 曲线图 + PR 描述更新）。
- 观测：
  - 在模型初始化时一次性预计算 interleaved cos/sin cache 并注册为 buffer，converter 运行时将 complex freqs_cis 替换为预计算 real cache，rope 函数检测到 real 输入后直接切片使用（_select_cos_sin_cache/_split_cos_sin_cache），跳过每次 forward/recompute 的 repeat_interleave 开销；PostAttention 的 inverse RoPE 通过新增 inverse kwarg 在 real cache 路径取 sin=-sin。

## 探针与操作

来源计划运行 cache/complex 路径的 CPU 等价性单测，以及同机 8 卡 rope ON/OFF 各 20 步训练对比。下列目标可用于后续复测：`tests/unit_tests/converters/test_rope_cos_sin_cache.py`、`tests/unit_tests/models/test_deepseek_v4_tnd.py`、`tests/unit_tests/converters/test_rope.py`。本卡没有这些命令的运行结果，也不声称图表或 PR 更新已经完成。

## 机制与判别
- 新增 helper（完整机制单元）：
```
+def _select_cos_sin_cache(
+    cache: torch.Tensor,
+    positions: torch.Tensor | None,
+    seqlen: int,
+) -> torch.Tensor:
+    if positions is None:
+        return cache[0:seqlen]
+    pos = positions[0] if positions.dim() > 1 else positions
+    return cache[pos]
+
+
+def _split_cos_sin_cache(
+    cache: torch.Tensor,
+    dtype: torch.dtype,
+) -> tuple[torch.Tensor, torch.Tensor]:
+    head_dim = cache.shape[-1] // 2
+    cos = cache[..., :head_dim].unsqueeze(0).unsqueeze(2).to(dtype)
+    sin = cache[..., head_dim:].unsqueeze(0).unsqueeze(2).to(dtype)
+    return cos, sin
```
- real cache 快速路径（complex 路径保留为 fallback，完整 diff hunk）：
```
-    freqs_cis = _select_freqs_cis(freqs_cis_local, positions, seqlen)

     xq_f = xq_local.float()
     xk_f = xk_local.float()

-    cos, sin = _complex_to_interleaved_cos_sin(freqs_cis, xq_f.dtype)
+    if not freqs_cis_local.is_complex():
+        cache = _select_cos_sin_cache(freqs_cis_local, positions, seqlen)
+        cos, sin = _split_cos_sin_cache(cache, xq_f.dtype)
+    else:
+        freqs_cis = _select_freqs_cis(freqs_cis_local, positions, seqlen)
+        cos, sin = _complex_to_interleaved_cos_sin(freqs_cis, xq_f.dtype)
```
- 判别设计：单测覆盖 cache 路径 vs complex 路径数值等价（assert_close）与 cache 路径不调用 repeat_interleave；inverse 路径用 sin=-sin 替代 freqs_cis.conj()。单测与训练对比的运行结果未进入账本证据。

## 验证信号

已核对的是预计算 buffer、real/complex 分支与 inverse sin 取负的源码机制。没有对应 CPU 单测、8 卡 ON/OFF 训练或性能结果，因此验证范围仅为 source_read。PR/Issue 引用中的百分比是来源材料中的报告，不是本轨迹重新测得的收益。

## 适用与失效边界
- 适用于 use_npu_rope=True 的 DSV4/兼容模型；buffer 在模型初始化注册，freqs_cis 形状随 max_seqlen 确定，超长序列需重建 buffer。
- real/complex 双路径并存：converter 未替换（仍传 complex freqs_cis）时源码设计保留原 complex 路径，运行等价性仍须复测。
- TND fake-batch 路径的兼容机制未被账本采纳，本卡不作断言。
