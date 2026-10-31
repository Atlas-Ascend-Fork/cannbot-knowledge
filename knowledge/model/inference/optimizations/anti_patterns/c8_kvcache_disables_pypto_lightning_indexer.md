---
type: Optimization
title: C8 KVCache 与 PyPTO Lightning Indexer 互斥，不能叠加
description: 在 DeepSeek-V3.2-Exp（DSA 架构）上，不要期望 C8 KVCache 量化 与 PyPTO 版 Lightning Indexer 加速 同时生效。二者当前互斥：一旦开启 C8（kv_cache_quant_mode == "int8"，早期实现里叫 kv_cache_c8），Lightning Indexer 的 decode 会被强制路由到 C8 量化算子 npu_lightning_indexer_quant，PyPTO 快路 npu_lightning_indexer_pto 永远不可达。想同时吃 C8 的显存收益和 PyPTO 的 LI 加速，会落空。
tags:
- task.debugging
- topic.attention
- topic.precision
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/8
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/7
  role: evidence
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/indexer.py
  role: implementation
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T15:29:24Z'
platforms:
- agnostic
---

# C8 KVCache 与 PyPTO Lightning Indexer 互斥，不能叠加

## 不要做什么

在 DeepSeek-V3.2-Exp（DSA 架构）上，不要期望 **C8 KVCache 量化** 与 **PyPTO 版 Lightning Indexer 加速** 同时生效。二者当前互斥：一旦开启 C8（`kv_cache_quant_mode == "int8"`，早期实现里叫 `kv_cache_c8`），Lightning Indexer 的 decode 会被强制路由到 C8 量化算子 `npu_quant_lightning_indexer`，PyPTO 快路 `npu_lightning_indexer_pto` 永远不可达。想同时吃 C8 的显存收益和 PyPTO 的 LI 加速，会落空。

调优时若配了 `enable_pypto=True` 却发现 Lightning Indexer 没走 PTO 路径，第一嫌疑就是同时开了 C8。

## 为何

[lightning-indexer](../../concepts/kernels/lightning_indexer.md) 在 decode 侧有三条互斥算子路径，由 `is_prefill / enable_pypto / kv_cache_c8` 选路，PyPTO 分支的守卫里带 `not kv_cache_c8`：

```python
# models/deepseek-v3.2-exp/models/indexer.py  forward_fusion
use_pto = enable_pypto and not is_prefill and not kv_cache_c8   # 早期写法 not self.kv_cache_c8，
                                                                # 后重构为 not self.kv_cache_quant_mode == "int8"，语义等价
if kv_cache_c8:
    npu_lightning_indexer_quant(...)   # C8 路：Hadamard 旋转 + 动态 Per-Token Int8 的 Q/K，layout 见下
elif not use_pto:
    npu_lightning_indexer(...)         # BF16 融合，layout_query='TND'
else:
    npu_lightning_indexer_pto(...)     # PyPTO，layout_query='BSND'
```

即 `kv_cache_c8=True` 时 `use_pto` 恒为 False，PyPTO 分支不可达。根因是 [pypto](../../concepts/frameworks/pypto.md) 当前没有 Lightning Indexer 的量化算子变体——C8 必须落到 torch_npu/AscendC 的量化 LI 算子路径，PyPTO 无对应 quant 算子可选。（"因无 PyPTO 量化 LI 变体"是据 diff 路由推断，源未给算子规格；行为约束本身是 diff 事实。）

## C8 路的配套代价（选它就要连带承担）

C8 不是只把 KV 存成 int8 就完事，Lightning Indexer 侧还要额外做量化前处理并多维护一份 scale cache：

- Indexer 的 Q/K 先 `apply_hadamard`（128×128 归一化 Hadamard，`get_had_pow2(128)`）做旋转以压低量化误差，再 `npu_dynamic_quant` 出 int8 + fp16 scale。
- Q 走 Per-Token-Head 量化；K 的 scale 经 `npu_scatter_nd_update_` 写入独立的 `past_key_scales_indexer` cache。
- 因此 C8 除了 KV 的 int8 存储，还额外维护一份 per-token-head 的 fp16 Indexer scale cache。

当前 V3.2 C8 的前置路径使用 packed 与逐token scale，详细接口见[MLA/C8接线](../rules/mla_c8_int8_kv_cache_op_wiring.md)。独立 LI 的 PTO 分支仍与 C8 互斥，但当前 IndexerProlog 的 PTO 前处理恰在enable_pypto且C8的Decode路径启用，不能把“LI单算子不可用”扩大成所有PyPTO都不可用。

## 适用边界

- 限定 DeepSeek-V3.2-Exp / [dsa](../../concepts/modules/dsa.md) 这一族的 Lightning Indexer decode 选路（`indexer.py forward_fusion`）。其他模型须先核实确实复用该 Indexer 选路；Kimi-K2-Thinking 为独立 MLA 建模副本，不属于此 DSA Indexer 示例。
- 运行时选型口径：**C8 与 PyPTO-LI 二选一**。要显存 → 开 C8，LI 固定走 `npu_quant_lightning_indexer`（带 Hadamard 旋转 + 额外 scale cache）；要 PyPTO LI 加速 → 不能开 C8。
- 该互斥是当前实现约束、非算法本质；若后续 PyPTO 补上量化 LI 变体，守卫可能放开——迁移到新版本时以建模代码的 `use_pto` 守卫为准复核。
- 相关量化面板见 [w8a8c8](../../concepts/quantization/w8a8c8.md)（C8 = KVCache int8 那一档）。

## Evidence

- [远程来源](https://gitcode.com/cann/cann-recipes-infer/issues/8)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/7)（evidence）
- [indexer.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/indexer.py)（implementation）
