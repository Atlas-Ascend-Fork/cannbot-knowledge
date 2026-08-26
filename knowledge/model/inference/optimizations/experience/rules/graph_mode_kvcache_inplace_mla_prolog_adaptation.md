---
type: Optimization
title: 图模式下 KV cache 就地更新与 MLA-prolog 入参适配：静态预分配 / 就地写 cache 算子 / inplace 看护 / 空 kr_cache
description: 图模式下 KV cache 就地更新与 MLA-prolog 入参适配：静态预分配 / 就地写 cache 算子 / inplace 看护 / 空 kr_cache。把 MLA + paged KV cache 的注意力路径接图模式（aclgraph / ge_graph 捕获执行）时，eager 下惯用的"每前向动态升维 KV cache、从算子返回值取 K、现造小张量"写法会破坏静态图捕获或多做无谓 tensormove。图模式 capture 时固化算子输入/输出形状、运行期不能每前向改形，KV cache 的读写要按图模式重排。
tags:
- task.optimization
- topic.attention
- topic.graph_execution
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/206
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/179
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/64
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 图模式下 KV cache 就地更新与 MLA-prolog 入参适配：静态预分配 / 就地写 cache 算子 / inplace 看护 / 空 kr_cache

## 适用场景

把 [MLA](../../../concepts/modules/mla.md) + paged KV cache 的注意力路径接图模式（aclgraph / ge_graph 捕获执行）时，eager 下惯用的"每前向动态升维 KV cache、从算子返回值取 K、现造小张量"写法会破坏静态图捕获或多做无谓 tensormove。图模式 capture 时固化算子输入/输出形状、运行期不能每前向改形，KV cache 的读写要按图模式重排。

## 规则 1：KV cache 预分配为静态形状 + 用就地写 cache 的算子版本

- **静态预分配**：nope/rope 两路 KV cache 建为**比 eager 多一维 `1` 占位的定形张量**（如 `(kv_cache_num_block, block_size, 1, dim)`）；各 attention 前向**直接索引该 cache**，不再逐前向 `.unsqueeze(2)` 动态升维。
- **就地写 cache 算子**：prefill/decode 改用把 K/V **就地写进传入 cache** 的算子版本（[MLA-prolog](../../../concepts/kernels/mla_prolog.md) 的 v3 变体、`npu_kv_rmsnorm_rope_cache_v2`），cache 张量作入参传入；**decode 从 cache 张量读回 K**，而非从算子返回值取形状可变的 K。
- **为何**：逐前向 unsqueeze 升维、或依赖算子返回可变形状的 K 都会破坏静态图；预分配静态 cache + 就地写把形状固定在建 cache 时，前向只做定形读写。
- 与量化正交：该改法在 BF16 / A8W8 / A8W8C8 上一致；激活量化门控用子串 `"a8" in mm_quant_mode`（不按 `== "W8A8"` 精确匹配、否则漏 W4A8 类），KV cache 量化模式经算子显式入参传（per-tensor=1）。

## 规则 2：C8 分支下 MLA-prolog 的 `kr_cache` 传预分配空 tensor

在昇腾 C8（KV-cache int8 量化）场景调 `npu_mla_prolog_v3` 时：
- C8 打开时 nope_cache/rope_cache/scales 会拼接后经 `k_nope` 入参送进算子，因此 `k_rope`（`kr_cache`）入参应当是**空 tensor**——shape 任意、**只要任一维为 0**（元素数为 0）、dtype `int8`、`device="npu"`。
- 把该空 tensor 放 `__init__` **预分配、forward 复用同一对象**：`torch.empty((1,2,1,0), dtype=torch.int8, device="npu")`。
- **不要**每次 forward 现造（尤其别对真实 `hidden_states` 做 `unsqueeze(0)` 顶替）——那每步多一次 tensormove。改预分配复用后该 tensormove 被消除，且把空 tensor 初始化放 `__init__`（每层各一个 data 节点）经 profiling 确认对性能基本无影响。
- 「因 nope/rope/scales 拼进 k_nope 故 k_rope 须为空」为代码注释级依据，按 code-comment 理解、不外推为算子硬合约。

## 规则 3：图模式下 inplace 更新 KV cache 的算子须 `add+0` 看护输出

torchair 图模式下，自定义融合算子（本例 PyPTO `npu_lightning_indexer_prolog_pto`）若对 KV-cache 输入做 **inplace 更新**（`idx_k_cache` int8、`idx_k_scale_cache` fp16 反量化因子），图不会自动捕获这些 inplace 输入的更新结果 / 下游读不到。修法：算子调用后对每个 inplace 输入各做一次 `torch.add(x, 0)` 并**作为输出返回**来"看护"：
```python
res = torch.ops.custom_pypto.npu_lightning_indexer_prolog_pto(..., idx_k_cache=idx_k_cache, idx_k_scale_cache=idx_k_scale_cache, ...)
res1 = torch.add(idx_k_cache, 0)
res2 = torch.add(idx_k_scale_cache, 0)
return res, res1, res2      # 让图观测到 inplace 更新后的 cache
```
维护者确认此意图："这两个输入是 inplace 的，需要通过 add+0 去看护这两个输入更新的结果"。PyPTO 算子只走 GE 入图见 [custom-op-framework-graph-backend-compat](custom_op_framework_graph_backend_compat.md)；C8 与 PyPTO Lightning Indexer 互斥见 [c8-kvcache-disables-pypto-lightning-indexer](../anti_patterns/c8_kvcache_disables_pypto_lightning_indexer.md)。

## 参考实现及其约束

参考实现：DeepSeek-R1 的 `forward_page_attention_mla_prolog` / `init_cache`（4 维静态 cache + 就地写）、DeepSeek-V3.2-Exp 的 `DeepseekIndexerAttention` C8 分支（空 kr_cache 预分配）、PyPTO Indexer Prolog 融合算子（add+0 看护）。"aclgraph 要求 4 维"是作者归因、"k_rope 须空"是 code-comment 级、算子版本以各模型建模为准；"图模式下 KV cache 预分配静态定形 + 就地写 cache 算子 + 从 cache 读回 + inplace 输出 add+0 看护"是可迁移的 MLA/paged-attention 图 bring-up 手段。

## Evidence

- diff 事实（@1a16834994ef）：4 维预分配 cache、去逐前向 unsqueeze、就地写 cache 算子、decode 从 cache 读回 K、`"a8" in` 子串门控；"aclgraph 要求 4 维"为作者归因、测试覆盖为作者自报。溯源下探 [cann-recipes-infer-pr-206-fix-ds-r1-replace-non-standard-inplace-ops-with-standard-ops](https://gitcode.com/cann/cann-recipes-infer/merge_requests/206)
- diff 事实 + 维护者确认（@deb929389f32）：C8 `kr_cache` 由 forward `hidden_states.unsqueeze(0)` 改 `__init__` 预分配 `torch.empty((1,2,1,0),int8,npu)` 复用；任一维为 0 即可 / tensormove 消除 / 基本无性能影响为维护者确认。溯源下探 [cann-recipes-infer-pr-179-fix-c8-mlaprolog-kr-cache-tensor](https://gitcode.com/cann/cann-recipes-infer/merge_requests/179)
- diff 事实 + 维护者确认（@87f244c）：PyPTO 融合算子后对 `idx_k_cache`/`idx_k_scale_cache` 各 `torch.add(x,0)` 并返回以看护 inplace 更新。溯源下探 [cann-recipes-infer-pr-64-feat-lip-li-dia-pypto](https://gitcode.com/cann/cann-recipes-infer/merge_requests/64)
