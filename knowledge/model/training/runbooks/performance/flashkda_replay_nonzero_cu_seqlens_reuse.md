---
{
  "type": "Runbook",
  "title": "flashkda replay 路径修复——npu_kda 复用缓存边界 + TND cu_seqlens（不走 BSND wrapper、不重做 nonzero）",
  "description": "torchtitan-npu 上 kimi_k3 模型训练开启 FlashKDA offload 后 replay 路径的修复：KDAKernel 直接复用 InnerKDA 已算好的 _query_start_loc 缓存并把 q/k/v/gate/beta 展平成 TND、直接传 cu_seqlens，不再走 BSND wrapper（不调用 _npu_kda_packed_boundaries、不重做 nonzero）。",
  "tags": [
    "task.implementation",
    "topic.checkpointing"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# flashkda replay 路径修复——npu_kda 复用缓存边界 + TND cu_seqlens（不走 BSND wrapper、不重做 nonzero）

torchtitan-npu 上 kimi_k3 训练开启 FlashKDA offload 后，本卡记录「复用缓存边界 + TND cu_seqlens」修复（npu_kda 不再走 BSND wrapper/不重做 nonzero）。

## 适用场景

torchtitan-npu 上 kimi_k3 训练开启 FlashKDA activation/cache offload 后，让 fused 算子（npu_kda）复用已缓存的文档边界、避免 BSND wrapper 同步 nonzero 的修复场景。

## 触发与观测

触发：用户提供 profiling 目录，询问「当前是否开启了 flashkda 的 offload，并且消除了 flashkda 的重计算」；随后指出「重算的时候出现了大空泡，导致现在这个优化没有收益」。

## 探针与操作

- trace_view.json 按流拆解：中心点 ±50ms 打印 DEVICE/CPU >100us 事件（pid/tid/args 全量），识别 EVENT_WAIT 与 UBDMA/SDMA 通道重合。
- CPU 侧 acl_memcpy_host_to_device 与 NPU MEMCPY_ASYNC 关联统计：与 16 个 tensor shape 对账。
- 代码侧对照：torchtitan_npu/models/kimi_k3/kda.py:526 的 NPU 快路径、ops/ascendc/kda.py:292 `_npu_kda_packed_boundaries`（每次调用 `positions.eq(0).nonzero()`）与 kda.py 内已缓存的 `_query_start_loc`。
- 单测（不依赖真实 NPU）：FakeNpuTensor/FakeOutput + monkeypatch 捕获 npu_kda 收到的参数。

## 机制与判别

生产修复 diff：

```diff
diff --git a/torchtitan_npu/models/kimi_k3/kda.py b/torchtitan_npu/models/kimi_k3/kda.py
index 01c2206..e6041ea 100644
--- a/torchtitan_npu/models/kimi_k3/kda.py
+++ b/torchtitan_npu/models/kimi_k3/kda.py
@@ -523,18 +523,27 @@ class KDAKernel(Module):
         positions_BL: torch.Tensor | None = None,
     ) -> torch.Tensor:
         if query_BLHK.device.type == "npu" and self.chunk_size == _KDA_CHUNK_SIZE:
+            # Reuse the cached packed-document boundaries; the BSND wrapper
+            # would otherwise rebuild them with a synchronizing nonzero.
+            if positions_BL is not None:
+                cu_seqlens = _query_start_loc(positions_BL)
+            else:
+                batch, tokens = query_BLHK.shape[:2]
+                cu_seqlens = torch.arange(
+                    batch + 1, device=query_BLHK.device, dtype=torch.int32
+                ) * tokens
             return npu_kda(
-                query_BLHK,
-                key_BLHK,
-                value_BLHV,
-                raw_gate_BLHK,
-                raw_beta_BLH,
+                query_BLHK.flatten(0, 1),
+                key_BLHK.flatten(0, 1),
+                value_BLHV.flatten(0, 1),
+                raw_gate_BLHK.flatten(0, 1),
+                raw_beta_BLH.flatten(0, 1),
                 A_log_H,
                 dt_bias_HK,
                 self.lower_bound,
-                positions=positions_BL,
+                cu_seqlens=cu_seqlens,
                 scale=query_BLHK.shape[-1] ** -0.5,
-            )
+            ).reshape(query_BLHK.shape[:2] + value_BLHV.shape[2:])

         log_decay = kda_log_decay(
             raw_gate_BLHK,
```

配套单测：

```
*** Begin Patch
*** Update File: tests/unit_tests/models/test_kimi_k3_fused_op_backwards.py
@@
 def test_causal_conv1d_metadata_tracks_position_updates():
     positions = torch.tensor([[0, 1, 2, 3]])
     torch.testing.assert_close(kda._query_start_loc(positions), torch.tensor([0, 4], dtype=torch.int32))
     positions[:, 2:] -= 2
     torch.testing.assert_close(kda._query_start_loc(positions), torch.tensor([0, 2, 4], dtype=torch.int32))


+def test_npu_kernel_reuses_positions_boundaries(monkeypatch):
+    class FakeNpuTensor:
+        def __init__(self, shape, marker):
+            self.device = types.SimpleNamespace(type="npu")
+            self.shape = shape
+            self.marker = marker
+
+        def flatten(self, start_dim, end_dim):
+            assert (start_dim, end_dim) == (0, 1)
+            return self.marker
+
+    class FakeOutput:
+        def reshape(self, shape):
+            return ("reshaped", shape)
+
+    captured = {}
+
+    def fake_npu_kda(
+        query, key, value, raw_gate, raw_beta, a_log, dt_bias,
+        lower_bound, *, positions=None, scale=None, cu_seqlens=None,
+    ):
+        captured.update(
+            query=query,
+            key=key,
+            value=value,
+            raw_gate=raw_gate,
+            raw_beta=raw_beta,
+            a_log=a_log,
+            dt_bias=dt_bias,
+            lower_bound=lower_bound,
+            positions=positions,
+            scale=scale,
+            cu_seqlens=cu_seqlens,
+        )
+        return FakeOutput()
+
+    monkeypatch.setattr(kda, "npu_kda", fake_npu_kda)
+    kernel = kda.KDAKernel(kda.KDAKernel.Config(chunk_size=64))
+    positions = torch.tensor([[0, 1, 2, 3], [0, 1, 2, 3]])
+    query = FakeNpuTensor((2, 4, 3, 8), "q_flat")
+    key = FakeNpuTensor((2, 4, 3, 8), "k_flat")
+    value = FakeNpuTensor((2, 4, 3, 8), "v_flat")
+    raw_gate = FakeNpuTensor((2, 4, 3, 8), "gate_flat")
+    raw_beta = FakeNpuTensor((2, 4, 3), "beta_flat")
+
+    result = kernel(
+        query,
+        key,
+        value,
+        raw_gate,
+        raw_beta,
+        "a_log",
+        "dt_bias",
+        positions_BL=positions,
+    )
+
+    assert result == ("reshaped", (2, 4, 3, 8))
+    assert captured["query"] == "q_flat"
+    assert captured["key"] == "k_flat"
+    assert captured["value"] == "v_flat"
+    assert captured["raw_gate"] == "gate_flat"
+    assert captured["raw_beta"] == "beta_flat"
+    assert captured["a_log"] == "a_log"
+    assert captured["dt_bias"] == "dt_bias"
+    assert captured["lower_bound"] == -5.0
+    assert captured["positions"] is None
+    assert captured["scale"] == 8 ** -0.5
+    torch.testing.assert_close(
+        captured["cu_seqlens"], torch.tensor([0, 4, 8], dtype=torch.int32)
+    )
+
+
 # ---------------------------------------------------------------------------
 # attention residual import contract
 # ---------------------------------------------------------------------------
*** End Patch
```

判别要点：

- 修复为 KDAKernel 直接复用 InnerKDA 已算好的 _query_start_loc 缓存并把 q/k/v/gate/beta 展平成 TND、直接传 cu_seqlens，不再走 BSND wrapper（不调用 _npu_kda_packed_boundaries、不重做 nonzero）；新单测验证 npu_kda 收到 flatten 输入与同一 cu_seqlens（[0,4,8]），相关 27 个测试通过。

## 验证信号

- 单测：test_npu_kernel_reuses_positions_boundaries 单独跑 PASS（`.` 100%，）；两条相关测试 `..` 100%；全套 `-q` 仅 1 个无关 KimiRMSNormGated CPU stub 测试失败（MagicMock 导致，未改动，）。
- 静态检查：py_compile、ruff check --select F821,E9 "All checks passed!"、git diff --check 均通过（-#12955、#13000 记录格式问题后修复）。
- 验证层级：cpu_reference（Windows CPU venv torch 2.5.1 的单测）+ source_read（既有 NPU profiling 数据的归因）；设备侧复测未做。

## 适用与失效边界

- 适用条件：chunk_size == _KDA_CHUNK_SIZE 的 NPU 快路径、positions_BL 可得；positions 为 None 时回退 arange 边界（batch 内等长假设）。
- 修复范围：消除 BSND wrapper 的同步 nonzero 路径（不再调用 _npu_kda_packed_boundaries、不重做 nonzero）；offload/恢复流水本身的其他开销不在本修复范围。
