---
type: Runbook
title: cache_compile / 图缓存失败：动态构建（KV cache 初始化 / row_idx 生成）落在编译区——挪出或 @dynamo.disable 隔离
description: cache_compile / 图缓存失败：动态构建（KV cache 初始化 / row_idx 生成）落在编译区——挪出或 @dynamo.disable 隔离。开 enable_cache_compile（torchair cache_compile）后出现：cachecompile 出错，或首轮执行需要 warmup 两次 + cache 无法生成。症状根子不在 cache_compile 本身，而在被编译路径里混进了只在首次/条件触发的动态构建——它让每次进入编译区的图形态不一致，破坏 cache_compile 缓存已编译图的前提。
tags:
- task.debugging
- topic.mixture_of_experts
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/186
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/284
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# cache_compile / 图缓存失败：动态构建（KV cache 初始化 / row_idx 生成）落在编译区——挪出或 @dynamo.disable 隔离

## 信号（现象）

开 `enable_cache_compile`（[torchair cache_compile](../../optimizations/experience/rules/torchair_cache_compile_persisted_graph.md)）后出现：**cachecompile 出错**，或**首轮执行需要 warmup 两次 + cache 无法生成**。症状根子不在 cache_compile 本身，而在**被编译路径里混进了只在首次/条件触发的动态构建**——它让每次进入编译区的图形态不一致，破坏 cache_compile 缓存已编译图的前提。

## 根因与两种典型触发

被编译的 decode 路径里若含"惰性初始化 / 首轮才建 / 每步换新对象"的动态构建，会与"缓存同一张已编译图"冲突：

- **KV cache 惰性初始化在编译路径内**：`prepare_inputs_for_generation` 在 `past_key_values is None` 时自己 `init_cache`，且每步把 `past_key_values` 拆开重组成一个**全新的**嵌套元组再塞回——缓存对象每步都换新，编译路径每步看到不同结构。
- **首轮生成索引张量在图内**：MoE 前处理需要 `row_idx`（`npu_moe_init_routing` 的行索引，`arange(0, num_tokens*top_k).view(...).permute(...).contiguous()`）；首轮执行时额外存在该生成过程，导致需要 warmup 两次，进而 cache_compile **无法生成 cache**。

## 修法（把动态构建移出编译区 / 隔离出图，保持编译图与 cache 对象稳定）

- **把 cache 生命周期上提到 runner 层（编译区之外），并保持对象稳定**：
  ```python
  # runner.model_input_prepare —— 首次在编译区外初始化，跨步复用同一对象
  if past_key_values is None:
      self.past_key_values = self.model.init_cache(input_ids)
      input_dict["past_key_values"] = self.past_key_values
  ```
  模型侧编译路径**不再惰性建 cache，改防御性抛错**（保证编译路径内绝不触发 init_cache）：`if past_key_values is None: raise ValueError("past_key_values should be initialized first!")`；`model_output_process` 删掉每步重建 `past_key_values` 元组的循环，直接复用同一对象（不换新）。
- **用 `@torch._dynamo.disable` 把构建隔离出图 + 按 key 缓存结果**：让 cache-build 路径 graph break 到 eager、不被编进 `torch.compile` 的图，编译图内只保留 cache-hit 路径：
  ```python
  @torch._dynamo.disable
  def _ensure_row_idx_outside_compile(self, num_tokens, top_k, device):
      # Never compiled: graph only contains cache-hit path; avoids double warmup & cache_compile failure.
      row_idx = self._build_row_idx(num_tokens, top_k, device)
      self._row_idx_cache[num_tokens] = row_idx     # key=num_tokens
      return row_idx
  row_idx = self._row_idx_cache.get(num_tokens) or self._ensure_row_idx_outside_compile(num_tokens, top_k, device)
  ```

## 可迁移原则与验证

**编译区内不应含只在首次/条件触发的动态构建**（cache 初始化、索引表生成、每步换新的容器）——它们要么上提到编译区外一次性做并复用稳定对象，要么用 `@torch._dynamo.disable` 隔离出图使编译图只含稳定的 cache-hit 路径。验证：acl_graph 下能开 cache_compile 且不再二次 warmup / cache 能生成（源多为定性，未给报错栈与前后数字）。相关：输入签名稳定 [graph-mode-stable-input-signature-recompile](../performance/graph_mode_stable_input_signature_recompile.md)、消除图中断 [graph-break-elimination-host-sync-unsupported-ops](../../guides/experience/interventions/graph_break_elimination_host_sync_unsupported_ops.md)。

## 参考实现及其约束

参考实现：Qwen3-MoE runner（`init_cache` 上提 runner 层 + 防御性抛错 + 去每步重建 cache 元组）、LLaDA2.x-sglang 的 `UnquantizedFusedMoEMethod.forward_npu`（`_row_idx_cache` + `@torch._dynamo.disable` 的 `_ensure_row_idx_outside_compile`）。具体函数名/字段是本仓落点；"动态构建落编译区破坏 cache_compile、须挪出或 dynamo.disable 隔离"是可迁移的失败签名。

## Evidence

- diff 事实（@8b7977e4b3d4）：`init_cache` 上提 runner 层 + 编译路径防御性抛错 + 删每步重建 cache 元组；"aclgraph 时 cachecompile 出错"来自 PR 描述，根因-修法机制部分为对 diff 结构与 cache_compile 语义推断、已标注。溯源下探 [cann-recipes-infer-pr-186-feat-chat-template-r1-eplb](https://gitcode.com/cann/cann-recipes-infer/merge_requests/186)
- diff 事实 + 维护者往返确认（@8cd85a87af03）：`_row_idx_cache` 按 `num_tokens` 缓存 + `@torch._dynamo.disable` 隔离构建，避免二次 warmup / cache_compile 无法生成。溯源下探 [cann-recipes-infer-pr-284-feat-llada2-x-sglang-ascend](https://gitcode.com/cann/cann-recipes-infer/merge_requests/284)
