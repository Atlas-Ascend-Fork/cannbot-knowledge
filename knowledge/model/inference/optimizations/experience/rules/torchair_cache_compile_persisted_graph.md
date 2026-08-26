---
type: Optimization
title: torchair cache_compile 图编译缓存落盘复用：调用约定、缓存失效与后端/版本约束
description: torchair cache_compile 图编译缓存落盘复用：调用约定、缓存失效与后端/版本约束。decode 静态图首次成图编译耗时长（服务重启后首 token 时延被重编译拖高）时，用 torchair tng.inference.cache_compile(...) 把编译产物落盘、服务重启直接加载缓存图，削掉冷启动首次推理时延。用它前先把下面几条会改变动作/踩坑的约定过一遍——它不是"开了就对"的旋钮。
tags:
- task.optimization
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/4
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/205
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/258
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/236
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# torchair cache_compile 图编译缓存落盘复用：调用约定、缓存失效与后端/版本约束

## 适用场景

decode 静态图首次成图编译耗时长（服务重启后首 token 时延被重编译拖高）时，用 torchair `tng.inference.cache_compile(...)` 把编译产物落盘、服务重启直接加载缓存图，削掉冷启动首次推理时延。用它前先把下面几条会改变动作/踩坑的约定过一遍——它不是"开了就对"的旋钮。

## 调用约定与约束

```python
cached_decode = tng.inference.cache_compile(
    cache_model, cache_dir=cache_dir, config=tng_config,
    dynamic=False, fullgraph=True, ge_cache=not use_aclgraph)
```

1. **只对 decode 编（prefill 不编）**：decode 固定重复 shape 适合静态图；prefill 变长收益低。见 [graph-mode-decode-only-compile-backends](graph_mode_decode_only_compile_backends.md)。
2. **`eager` 模式下开缓存无效**：`exe_mode=eager` 时 `enable_cache_compile` 被忽略（`check_model_settings` 记 `does not support cache compile`）。想省编译时间必须先切图模式，别指望 eager 下 cache_compile 生效。
3. **`ge_cache` 仅 ge_graph 路径用**：`ge_cache=not use_aclgraph`——ge_graph 用 GE 图缓存，ACLGraph 路径不并用 GE cache。
4. **ACLGraph + cache_compile 共存的配置**：ACLGraph 路径同时开 cache_compile 时，`tng_config.mode` 必须 `"reduce-overhead"`、`ge_cache` 必须 `False`；`enable_static_kernel` 为真再开 `_aclnn_static_shape_kernel`；`dynamic=False, fullgraph=True` 两路径一致。
5. **缓存目录依赖环境变量**：cache_dir 常以 `CASE_NAME` 拼（`"compile_cache/" + os.getenv("CASE_NAME")`）；未设会把 `None` 拼进路径 → 缓存落错目录。开缓存前先确认 `CASE_NAME` 已设。
6. **MTP/投机解码需独立缓存条目**：spec（draft）模型的 decode 图与主 decode 图必须落到分开的 `cache_dir`（如 `_spec` 后缀）且用各自独立的 callable；靠 `cache_dir` 后缀区分同一函数会撞注册触发重编译（见 [mtp-speculative-decode-graph-mode-prereqs](../../../runbooks/runtime/mtp_speculative_decode_graph_mode_prereqs.md)）。
7. **`torch < 2.5.0` 且 acl_graph**：须 `compiler_config.debug.aclgraph.disable_reinplace_inplaceable_ops_pass = True`，否则 reinplace pass 与 aclgraph 冲突。

## 缓存与"模型结构 + 部署方式"强绑定——变更须手动清缓存

`cache_compile` 以「模型结构 + 部署方式（并行/量化布局）」为隐式 key 缓存已编译图，但**缓存不感知配置变更**：改了结构或并行/部署方式后若不删缓存目录（如 `compile_cache/`），会命中并**静默复用旧配置下编译的图**——错配且无显式报错。排障提示：切换配置后出现与预期不符的图行为，先怀疑残留编译缓存，删目录重编再复现。

## 后端 × 版本可用性（先对照再规划）

- **ge_graph**：cache_compile / `ge_cache=True` 是 GE 图专属能力，成熟可用。
- **ACLGraph 上的 cache_compile 有版本地板**：旧版本未实现——早期建模在 acl_graph 下开 `enable_cache_compile` 会命中硬 `assert not enable_aclgraph, "ACLGraph cache compilation is not implemented"` 直接崩（其未完成的卡点是 `clone_input=True` 存在性能问题）。**该能力后由 CANN 8.3+ / PTA 7.3.0 加入支持**，配置见上第 4 条。跑 ACLGraph + cache_compile 前先确认包版本达到此地板，否则该特性不可用、需退回 ge_graph 或关缓存。

**rollback**：`enable_cache_compile=False` 退回普通 `torch.compile(backend=tng.get_npu_backend(...))`；`exe_mode=eager` 完全关图。

## 参考实现及其约束

参考实现在 cann-recipes-infer 的 Qwen3-MoE runner（`graph_compile` / `model_setting`）、qwen3-moe-sglang patch（`_GE_CACHE_DIR="compile_cache/verify"`、README 附录明列"变更须手动删 compile_cache/"）、DeepSeek-V3.2-Exp 的 `get_cached_graph`。`CASE_NAME`、`compile_cache/verify` 等路径约定与版本地板（CANN 8.3+/PTA 7.3.0）是该框架/版本的落地事实，非 torchair 通用规格；cache_compile 与结构+部署绑定、变更须清缓存这条对任何用它的部署都成立。

## 相关经验

- 另见 [decode ge_graph 低时延融合：SuperKernel 调度融合的启用前提、融合范围坑与冷启动缓存](superkernel_decode_ge_graph_fusion_scope.md)。


## Evidence

- diff 事实（@e8eb6979565c）：`cache_compile` 只编 decode、eager 无效、`torch<2.5.0` 关 reinplace、`CASE_NAME` 拼 cache_dir、`ge_cache=not use_aclgraph`、`TASK_QUEUE_ENABLE` 0/1。溯源下探 [cann-recipes-infer-pr-4-qwen3moe](https://gitcode.com/cann/cann-recipes-infer/merge_requests/4)
- diff + README（@50e41b5b8220）：缓存与"模型结构+部署方式"绑定、变更须手动删 `compile_cache/`。溯源下探 [cann-recipes-infer-pr-205-feat-support-qwen3-moe-sglang](https://gitcode.com/cann/cann-recipes-infer/merge_requests/205)
- diff 事实 + 维护者确认（@5b2f1202c508）：ACLGraph+cache_compile 需 `mode=reduce-overhead` + `ge_cache=False`；版本地板 CANN 8.3+/PTA 7.3.0（维护者答复、doc 未写）。溯源下探 [cann-recipes-infer-pr-258-feat-dsv3-2-support-aclgraph-cache-compile](https://gitcode.com/cann/cann-recipes-infer/merge_requests/258)
- diff 事实 + 作者说明：早期 acl_graph 下 cache_compile 未实现——init 硬 `assert not enable_aclgraph`；未完成卡点为 `clone_input` 性能 TODO。此为版本演进的前态，已被 CANN 8.3+/PTA 7.3.0 支持取代。溯源下探 [cann-recipes-infer-pr-236-fix-duplicate-creation-of-multi-stream-events-when-mtp-enable-skip-guard](https://gitcode.com/cann/cann-recipes-infer/merge_requests/236)
