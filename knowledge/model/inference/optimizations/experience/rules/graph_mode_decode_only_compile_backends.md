---
type: Optimization
title: NPU LLM 图模式启用骨架：decode-only 编译 + ge_graph / acl_graph / npugraph_ex 后端编译入口与配置约束
description: NPU LLM 图模式启用骨架：decode-only 编译 + ge_graph / acl_graph / npugraph_ex 后端编译入口与配置约束。要给一个 NPU 上的 LLM 推理开 图模式（压掉逐算子下发的 host 调度开销）时，先照这套骨架搭编译路径，再谈模型侧的图适配。它回答三件事：编哪个阶段、用哪个图后端、每个后端的编译入口和硬性配置约束是什么。
tags:
- task.optimization
- topic.graph_execution
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/328
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/294
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/204
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/326
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/304
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# NPU LLM 图模式启用骨架：decode-only 编译 + ge_graph / acl_graph / npugraph_ex 后端编译入口与配置约束

## 适用场景

要给一个 NPU 上的 LLM 推理开 [图模式](../../../concepts/techniques/npu_graph_mode.md)（压掉逐算子下发的 host 调度开销）时，先照这套骨架搭编译路径，再谈模型侧的图适配。它回答三件事：**编哪个阶段、用哪个图后端、每个后端的编译入口和硬性配置约束是什么**。

## 阶段划分：只编 decode，prefill 恒 eager

LLM 推理必须严格区分两阶段再决定入图：

| 阶段 | 是否入图 | 原因 |
|------|---------|------|
| Prefill | 禁用（eager） | 输入序列长动态变化、首 token 逻辑复杂、shape 不固定，不适合图捕获 |
| Decode | 推荐 | 输入长度固定（通常为 1）、shape 稳定，适合图捕获、收益大 |

实现上把 prefill / decode 的 forward 拆成不同方法，**只对 decode 方法** `torch.compile(...)`，prefill 保持 eager。前置条件：decode 侧须为静态 shape——KV cache 预分配为连续张量、batch 定形填充、前向用就地写（`scatter_update_` 等）更新 KV。连续 KV + 定形 batch 是图捕获的前提。

**warm-up 触发一次编译**：预热阶段跑一次 prefill（eager）+ 一次 decode（dummy 输入，shape 取 `batch_size_per_dp_rank × input_max_len`）；decode 步在图模式下触发首次编译，正式请求复用编译结果，避免首个真实请求承担编译开销。warm-up dummy 输入须与正式输入同签名（见 [graph-mode-stable-input-signature-recompile](../../../runbooks/performance/graph_mode_stable_input_signature_recompile.md)）。

## 后端选择与编译入口（三条互斥路径）

NPU 图模式用 GE 图（Ascend IR），经 `torchair.get_npu_backend()` 启用；`aot_eager` / `inductor` / `cudagraphs` 等 CUDA 生态后端在 NPU 上**不可用**。带 TP/EP 并行时须先 `torchair.patch_for_hcom()` 让集合通信入图。三种执行模式 `exe_mode ∈ {eager, ge_graph, acl_graph/npugraph_ex}` 编译入口不同：

```python
import torchair as tng
tng.patch_for_hcom()                       # 有并行时令集合通信入图
compiler_config = tng.CompilerConfig()
compiler_config.experimental_config.frozen_parameter = True
compiler_config.experimental_config.tiling_schedule_optimize = True
compiler_config.experimental_config.topology_sorting_strategy = "StableRDFS"
```

- **ge_graph（GE 图）**：`dynamic=False`；落盘缓存走 `tng.inference.cache_compile(..., ge_cache=True)`（见 [torchair-cache-compile-persisted-graph](torchair_cache_compile_persisted_graph.md)）。静态图优化更充分。
- **acl_graph / npugraph_ex（torch.compile + ACLGraph 捕获）**：
  ```python
  compiler_config.mode = "reduce-overhead"                       # ACLGraph 必需
  if torch.__version__ < "2.5.0":
      compiler_config.debug.aclgraph.disable_reinplace_inplaceable_ops_pass = True
  if hasattr(compiler_config.debug.aclgraph, "clone_input"):
      compiler_config.debug.aclgraph.clone_input = False          # clone_input=True 有性能问题（非精度）
  if enable_static_kernel:
      compiler_config.experimental_config.aclgraph._aclnn_static_shape_kernel = True
  torch._dynamo.config.inline_inbuilt_nn_modules = False
  npu_backend = tng.get_npu_backend(compiler_config=compiler_config)
  cached_decode = torch.compile(cache_model, dynamic=False, fullgraph=True, backend=npu_backend)
  ```
- **编译范围只覆盖 decode**：`if "graph" in exe_mode and not is_prefill: logits = model_compiled(**inputs)` else 走 eager 的 `model(**inputs)`。

`acl_graph` 是旧名，executor 侧后续统一为 `npugraph_ex`；用旧名会撞 `exe_mode` 枚举 ValueError。

## npugraph_ex / acl_graph 的硬配置约束

启用 torch.compile+ACLGraph 图捕获路径时几处配置必须满足，否则报错或行为异常：

- **`enable_static_kernel` 只能配 `npugraph_ex`**：`enable_static_kernel and exe_mode != "npugraph_ex"` → `raise ValueError("enable_static_kernel only supports exe_mode='npugraph_ex'")`；static kernel 加速仅这条路径支持。
- **`TASK_QUEUE_ENABLE` 只能取 0 或 1**：图捕获路径下框架强制 `os.environ["TASK_QUEUE_ENABLE"]="1"`；**别手动置 2**——`2` 是 eager 下优化 host 侧性能的默认值，与图捕获不兼容（取 2 会越界）。eager / 非图模式才用 `2`。
- **decode 的 `actual_seq_lengths_q/kv` 须转 python list**（`.detach().cpu().numpy().tolist()`）供图执行；这与 eager 单算子对该参数的类型要求耦合，详见 [fia-actual-seq-lengths-kv-backend-type](../../../runbooks/runtime/fia_actual_seq_lengths_kv_backend_type.md)。

**rollback**：`exe_mode=eager`（不走图编译，`TASK_QUEUE_ENABLE=2`）。图适配本身的图中断消除、多流同步分别见 [graph-break-elimination-host-sync-unsupported-ops](../../../guides/experience/interventions/graph_break_elimination_host_sync_unsupported_ops.md)、[graph-mode-multi-stream-cross-stream-sync-api](../../../guides/experience/interventions/graph_mode_multi_stream_cross_stream_sync_api.md)。

## 参考实现及其约束

参考实现在 cann-recipes-infer 的 executor（`executor/core/engine`、`executor/core/model_worker`）与 DeepSeek-V3.2-Exp / Pangu-7B / R1 建模：executor 用统一 `compile_model_forward` 编 `model.forward`，按 `exe_mode` 分叉 CompilerConfig；`clone_input=False` 是临时规避（待 torch_npu 后续版本移除），`_aclnn_static_shape_kernel` 仅在 `enable_static_kernel` 时开。这些开关名/默认值是该 recipe/框架的落地约定，`TASK_QUEUE_ENABLE`、`static_kernel` 约束不外推为整个昇腾栈通用律；decode-only + GE 后端 + warm-up 触发编译是可迁移的图模式启用范式。

## Evidence

- diff 事实（@73ed847）：graph-mode-adaptation skill 明述「NPU 图模式用 GE 后端 / decode-only / prefill eager / aot_eager·inductor·cudagraphs 不可用」。溯源下探 [cann-recipes-infer-pr-328-feat-add-agent-optimization-skills-and-evaluation-reports](https://gitcode.com/cann/cann-recipes-infer/merge_requests/328)
- diff 事实（@029272b28d4a）：executor 只对 decode 编译、warm-up 跑一次 decode 触发编译、acl_graph/ge_graph 的 CompilerConfig 分支（reduce-overhead / dynamic / ge_cache / torch<2.5.0 补丁）。溯源下探 [cann-recipes-infer-pr-294-refactor-introducing-a-new-execution-mechanism-for-recipes-infer-and-tes](https://gitcode.com/cann/cann-recipes-infer/merge_requests/294)
- diff 事实 + 维护者确认（@f8bb1545）：acl_graph 走 `torch.compile`+`reduce-overhead` 与 ge_graph 的 cache_compile 分叉；`clone_input=False` 为性能（非精度）临时规避、需 `hasattr` 版本门控。溯源下探 [cann-recipes-infer-pr-204-feat-dsv3-2-support-acl-graph](https://gitcode.com/cann/cann-recipes-infer/merge_requests/204)
- diff 事实（@b7a110bd6812）：`_validate` 的 `enable_static_kernel↔npugraph_ex` 门控、`TASK_QUEUE_ENABLE` 联动、seq_lengths 转 list。溯源下探 [cann-recipes-infer-pr-326-refactor-mtp-refactor-and-r1-adaptation-framework](https://gitcode.com/cann/cann-recipes-infer/merge_requests/326)
- diff 事实（@dc0404e17de0）：aclgraph 下强制 `TASK_QUEUE_ENABLE=1`、eager=2（「aclgraph only supports 0 or 1」为代码注释级依据）。溯源下探 [cann-recipes-infer-pr-304-feat-pangu-7b-model-inference-support-on-cann](https://gitcode.com/cann/cann-recipes-infer/merge_requests/304)