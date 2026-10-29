---
type: Guide
title: LLM Decode 图编译指南：来源实现的 GE 与 ACLGraph 入口及验收
description: 按来源实现组织 Decode 图编译、预热和回退，列出 GE、ACLGraph/npugraph_ex 的配置差异；入图取舍引用图模式决策，不将 Prefill eager 或历史后端限制泛化为 NPU 平台禁令。
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
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/executor/utils/graph_utils.py
  role: implementation
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/executor/core/engine/execution_engine.py
  role: implementation
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/executor/core/model_worker/model_worker.py
  role: implementation
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-23T09:41:54Z'
platforms:
- agnostic
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - decode
---

# LLM Decode 图编译指南：来源实现的 GE 与 ACLGraph 入口及验收

## 适用场景

按下列来源中的实现，为 NPU 上的 LLM 推理开 [图模式](../../concepts/techniques/npu_graph_mode.md)（压掉逐算子下发的 host 调度开销）时，先照这套骨架搭编译路径，再谈模型侧的图适配。它回答三件事：**编哪个阶段、用哪个图后端、每个后端的编译入口和硬性配置约束是什么**。

## 先确认入图取舍，再按来源实现分阶段

先读 [图模式决策](../../optimizations/rules/graph_mode_enable_decision_profiling.md)，确认 host 下发开销、shape/控制流、正确性与收益。本指南的来源路径将 Prefill 留在 eager、只编译 Decode；这是所记录实现的范围，不是 Prefill 不可入图的结论。

本路径把 prefill / decode 的 forward 分开，仅对 decode 方法编译。预分配 KV 缓冲、稳定 batch 与输入签名，并核对就地更新行为；具体内存布局和动态能力应按所选后端、算子与版本核对，不能把“连续 KV + 定形 batch”写成所有图后端的共同硬约束。

**warm-up 触发一次编译**：预热阶段跑一次 prefill（eager）+ 一次 decode（dummy 输入：无 MTP 时 shape 为 `batch_size_per_dp_rank × 1`，MTP 时序列长度为 `next_n + 1`；`input_max_len` 是 Prefill 长度）；decode 步在图模式下触发首次编译，正式请求复用编译结果，避免首个真实请求承担编译开销。warm-up dummy 输入须与正式输入同签名（见 [graph-mode-stable-input-signature-recompile](../../runbooks/performance/graph_mode_stable_input_signature_recompile.md)）。

## 来源实现的后端选择与编译入口

以下先记录历史 GE/ACLGraph 的 `torchair.get_npu_backend()` 路径，再单列固定 `2f82d10` 的 npugraph_ex 入口，二者不能只替换后端名称。PR328 的历史 Skill 限制不能作为所有 NPU 后端的能力结论；其他路径可参考 [inductor/autofuse 局部编译规则](../../optimizations/rules/inductor_autofuse_partial_compile_scope.md)，并核对其软件版本与编译范围。带 TP/EP 并行时须先 `torchair.patch_for_hcom()` 让集合通信入图。三种执行模式 `exe_mode ∈ {eager, ge_graph, acl_graph/npugraph_ex}` 编译入口不同：

```python
import torchair as tng
tng.patch_for_hcom()                       # 有并行时令集合通信入图
compiler_config = tng.CompilerConfig()
compiler_config.experimental_config.frozen_parameter = True
compiler_config.experimental_config.tiling_schedule_optimize = True
compiler_config.experimental_config.topology_sorting_strategy = "StableRDFS"
```

- **ge_graph（GE 图）**：`dynamic=False`；落盘缓存走 `tng.inference.cache_compile(..., ge_cache=True)`（见 [torchair-cache-compile-persisted-graph](../../optimizations/rules/torchair_cache_compile_persisted_graph.md)）。静态图优化更充分。
- **历史 acl_graph（PR294/204 的 CompilerConfig 入口）**：
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

固定 `2f82d10467e6fe8dae81c97a2cdac78d733a6703` 的 `executor/utils/graph_utils.py` 使用独立 npugraph_ex 后端，不能照搬上面的历史 CompilerConfig：

```python
compile_options = {"frozen_parameter": True,
                   "static_kernel_compile": enable_static_kernel}
cached_decode = torch.compile(
    cache_model, backend="npugraph_ex", dynamic=True, fullgraph=True,
    options=compile_options,
)
```

该版本落盘缓存走 `torch.npu.npugraph_ex.inference.cache_compile`，同样传 `dynamic=True` 与 options。执行模式枚举使用 `npugraph_ex`；旧 acl_graph 名称与旧编译接口须按版本一起核对。

## 来源实现中的 npugraph_ex / acl_graph 配置约束

启用 torch.compile+ACLGraph 图捕获路径时几处配置必须满足，否则报错或行为异常：

- **`enable_static_kernel` 只能配 `npugraph_ex`**：`enable_static_kernel and exe_mode != "npugraph_ex"` → `raise ValueError("enable_static_kernel only supports exe_mode='npugraph_ex'")`；static kernel 加速仅这条路径支持。
- **`TASK_QUEUE_ENABLE` 只能取 0 或 1**：图捕获路径下框架强制 `os.environ["TASK_QUEUE_ENABLE"]="1"`；**别手动置 2**——`2` 是 eager 下优化 host 侧性能的默认值，与图捕获不兼容（取 2 会越界）。eager / 非图模式才用 `2`。
- **该 npugraph_ex decode 路径的 `actual_seq_lengths_q/kv` 转 python list**（`.detach().cpu().numpy().tolist()`）供图执行；GE 与 eager 的类型按各自接口核对，不能由该分支推导 eager 也必须用 list，详见 [fia-actual-seq-lengths-kv-backend-type](../../runbooks/runtime/fia_actual_seq_lengths_kv_backend_type.md)。

**rollback**：`exe_mode=eager`（不走图编译，`TASK_QUEUE_ENABLE=2`）。图适配本身的图中断消除、多流同步分别见 [graph-break-elimination-host-sync-unsupported-ops](../integration/graph_break_elimination_host_sync_unsupported_ops.md)、[graph-mode-multi-stream-cross-stream-sync-api](../../optimizations/rules/graph_mode_multi_stream_cross_stream_sync_api.md)。

## 验收与停止条件

先保存 eager 的输出和预热后时延，再在同一输入、权重、batch 与并行配置下比较图模式。记录首次编译耗时和稳态时延；检查重复请求是否重编译、输出是否满足该模型的精度标准。输出不对齐、输入签名仍不稳定或没有净收益时，回到 eager，按关联 Runbook 定位后再重试。

## 参考实现及其约束

历史 executor 在 `compile_model_forward` 内使用 CompilerConfig；固定 `2f82d10` 已将 npugraph_ex 拆为 backend/options 分支。`clone_input=False`、旧 `_aclnn_static_shape_kernel` 等配置只按其历史来源解释，不与新 `static_kernel_compile` 拼成一套参数。后端、版本和阶段分别验收，不能外推为整个昇腾栈的共同配置。

## Evidence

- 历史来源（@73ed847）：graph-mode-adaptation Skill 采用 GE 后端、decode-only、prefill eager。本指南保留其流程范围，撤下该来源对所有 NPU 后端不可用的泛化表述。溯源下探 [cann-recipes-infer-pr-328-feat-add-agent-optimization-skills-and-evaluation-reports](https://gitcode.com/cann/cann-recipes-infer/merge_requests/328)
- diff 事实（@029272b28d4a）：executor 只对 decode 编译、warm-up 跑一次 decode 触发编译、acl_graph/ge_graph 的 CompilerConfig 分支（reduce-overhead / dynamic / ge_cache / torch<2.5.0 补丁）。溯源下探 [cann-recipes-infer-pr-294-refactor-introducing-a-new-execution-mechanism-for-recipes-infer-and-tes](https://gitcode.com/cann/cann-recipes-infer/merge_requests/294)
- diff 事实 + 维护者确认（@f8bb1545）：acl_graph 走 `torch.compile`+`reduce-overhead` 与 ge_graph 的 cache_compile 分叉；`clone_input=False` 为性能（非精度）临时规避、需 `hasattr` 版本门控。溯源下探 [cann-recipes-infer-pr-204-feat-dsv3-2-support-acl-graph](https://gitcode.com/cann/cann-recipes-infer/merge_requests/204)
- diff 事实（@b7a110bd6812）：`_validate` 的 `enable_static_kernel↔npugraph_ex` 门控、`TASK_QUEUE_ENABLE` 联动、seq_lengths 转 list。溯源下探 [cann-recipes-infer-pr-326-refactor-mtp-refactor-and-r1-adaptation-framework](https://gitcode.com/cann/cann-recipes-infer/merge_requests/326)
- diff 事实（@dc0404e17de0）：aclgraph 下强制 `TASK_QUEUE_ENABLE=1`、eager=2（「aclgraph only supports 0 or 1」为代码注释级依据）。溯源下探 [cann-recipes-infer-pr-304-feat-pangu-7b-model-inference-support-on-cann](https://gitcode.com/cann/cann-recipes-infer/merge_requests/304)

## Executor 路由与输入适配参考

以下来源为 `2f82d10467e6fe8dae81c97a2cdac78d733a6703` 的图模式文档；路径和接口按该提交解释，不作为其他后端或版本的强制配置。

### 使能链路

```
1. 配置层：executor/core/config/inference_config.py
 model_config.exe_mode ∈ {eager, ge_graph, npugraph_ex}

2. 预热层：executor/core/engine/execution_engine.py::warm_up
 先跑一次 prefill（eager） → 再跑一次 decode（触发图编译）

3. 编译层：executor/core/model_worker/model_worker.py::compile_model
 → executor/utils/graph_utils.py::compile_model_forward

4. 执行层：ModelWorker.inference
 if not is_prefill and exe_mode in ["ge_graph", "npugraph_ex"]:
 return self.model_compiled(**model_inputs)
 else:
 return self.model(**model_inputs)

5. 元数据层：executor/utils/forward_metadata.py::ForwardMetaData
 is_prefill / kv_len / actual_seq_lengths_q / actual_seq_lengths_kv / attention_mask
 由框架构造后作为显式输入传入模型
```

## 固定来源实现的适配条件

仅仅开 `exe_mode` 不够，该参考实现要求：

1. **eager 下稳定运行** —— 图模式不会修复 eager 下本来就存在的错误。
2. **prefill 与 decode 明确区分** —— 推荐 `prefill` 保持 eager、`decode` 使用图模式；用 `forward_metadata.is_prefill` 或独立的 `prefill/decode` 方法区分路径。
3. **动态信息显式输入** —— `kv_len`、`position_ids`、`actual_seq_lengths_q/kv`、`is_prefill` 由框架构造传入，而非模型内部临时生成 Python 标量或隐式推导。
4. **KV Cache 与常驻 buffer 预分配 + 原地更新**：

 ```python
 # 错误：decode 场景下 KV 的 shape/地址变化 → dynamo guard 失败 + 重编译
 key = torch.cat([past_key, new_key], dim=1)

 # 推荐：原地更新
 torch_npu.scatter_update_(k_cache, kv_len, key_states, -2)
 torch_npu.scatter_update_(v_cache, kv_len, value_states, -2)
 ```

5. **避免典型 Graph Break 写法**：
 - `tensor.item`
 - 基于 Tensor 值的 Python `if/while`
 - 在 forward 内部临时创建影响 shape 的控制分支
 - 根据 Python `list/tuple` 长度变化切换图内控制流

## FIA 融合算子适配建议

| 模式 | 常见 FIA 接口 | `actual_seq_lengths` | 说明 |
|------|--------------|----------------------|------|
| `ge_graph` | `torchair.ops` | Tensor | 只适合 GE 图模式 |
| `npugraph_ex` | `torch_npu` | `list[int]`（推理常见） | 当前 FIA 接口主打推理；算子支持变化时再调整 |

参考 `models/qwen3_moe/models/modeling_qwen3_moe.py`：decode 且 `enable_gegraph` 时切到 `torchair.ops`；ExecutionEngine 在 `npugraph_ex` decode 模式下把 `actual_seq_lengths_*` 转成 `list`。
