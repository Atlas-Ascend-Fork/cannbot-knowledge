---
type: Guide
title: 把 decode 逻辑塞进图前消除 graph break：host 同步 / host 构造张量 / 图后端不支持算子的图安全改写
description: 把 decode 逻辑塞进图前消除 graph break：host 同步 / host 构造张量 / 图后端不支持算子的图安全改写。要把一段 decode 逻辑整图编译进 GE 图 / aclgraph（npu-graph-mode），但它含 host 依赖或图后端不支持的算子，捕获失败 / 断图 / 走 CPU fallback。上图前先按下面几类逐条排查、把图中断（graph break）改成图安全等价——这是把 decode 从 eager 迁到图模式的核心适配工作。是否值得为某模块付这份适配见 graph-mode-enable-decision-profiling。
tags:
- task.debugging
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/403
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/204
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/284
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/408
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/462
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/348
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 把 decode 逻辑塞进图前消除 graph break：host 同步 / host 构造张量 / 图后端不支持算子的图安全改写

## 适用场景

要把一段 decode 逻辑整图编译进 GE 图 / aclgraph（[npu-graph-mode](../../../concepts/techniques/npu_graph_mode.md)），但它含 host 依赖或图后端不支持的算子，捕获失败 / 断图 / 走 CPU fallback。上图前先按下面几类逐条排查、把图中断（graph break）改成图安全等价——这是把 decode 从 eager 迁到图模式的核心适配工作。是否值得为某模块付这份适配见 [graph-mode-enable-decision-profiling](../../../optimizations/experience/rules/graph_mode_enable_decision_profiling.md)。

## 类别 1：forward 内 host-device 同步/host 依赖打断图（总原则）

**不要在推理模型的 `forward` 里放 device→host 同步**（`.cpu()`、`.tolist()`、`.item()`、`.nonzero()` 等）：prefill（eager 流水）会**断流**（打断算子下发流水）、图模式 decode 会**断图**（引入 host 依赖、切断整图捕获）。

修法：
- **挪出 forward**：把 host 侧取数/序列长度扩展等挪到模块外，每次 forward 只算一次、shape 为编译期常量。
- **收敛到不入图的 eager 分支**：确需 host 依赖的数据依赖逻辑（如 MoE all_to_all 按 token 计数切分）只保留在 eager / prefill 路径；图模式 decode 路径不得有任何 `.cpu()`。

## 类别 2：host 侧 Python list 构造张量 → 设备侧等价算子

捕获区内**不能用 host Python 数据构造 tensor**（`torch.tensor([...]).npu()`：先在 host 建 list 再拷到 device），会引入 host 依赖无法固化进静态图。若某张量的值只依赖形状/步长等编译期已知量，用设备侧构造算子表达同一数值：
```python
# 断捕获：host list → device
torch.tensor([q_len + i * q_len for i in range(bsz)], dtype=torch.int32).npu()
# 可捕获：纯设备侧等价构造
torch.arange(q_len, q_len * (bsz + 1), q_len, dtype=torch.int32, device=dev)
```

## 类别 3：逐 batch Python 循环 + `.item()` → 全向量化

decode/并行解码里"对每个 batch 起 Python 循环、内含 `torch.sum(...).item()` / 逐 batch argmax·scatter"这类 `.item()` 同步与动态形状写会强制 host-device 同步、打断 graph capture。改成**全向量化、graph-friendly** 的更新：一次处理整批 `[B, blk]`，"force-at-least-one"这类条件写用**单点稀疏写 + 门控成 no-op**（`new_ids[rows, idx2]=val2`）替代 `[B,blk]` one-hot `scatter_`，回写用原地 `input_ids.copy_(new_ids)` 保 storage。落库也批量化（一次 `extend` + 一次 `check_finished` 替代逐 token 循环）。

## 类别 4：图后端不支持的算子 → 定形展开/图安全替换

把逻辑塞进整图前，先核其中是否含图后端未支持的算子；命中就用等价的**定形展开算子**替换，或把该逻辑留在 eager 阶段（由 `is_prefill` 分派）：

| 算子/结构 | 症状 | 图安全替换 |
|---|---|---|
| `aten.cummax` / `aten.amax`（前缀 max） | GE 后端不支持 → 无法捕获 | 按静态 seq 长度展开成一串 `torch.maximum`（unrolled max-chain），需定形；`cummax` 只留 eager(prefill) |
| `npu_geglu`（GEGLU 融合） | ge_graph 无 torchair converter；npugraph_ex 下 torch.compile meta 签名不匹配 | decode 图路径手动 `gate,up=chunk(2); npu_fast_gelu(gate)*up`（tanh 近似、图安全）；prefill(eager) 仍用融合 `npu_geglu` |
| `F.gelu` / `aten::gelu` | aclgraph 捕获下回退 CPU（拖慢/断图） | `npu_fast_gelu`（matches gelu approximate='tanh'，避免 aclgraph CPU fallback） |
| `tensor[bool_mask]=0` 布尔掩码赋值 | GE 不支持 | 乘法掩码 `x * mask.to(dtype)` |
| 有状态属性重绑 `self.ctx = ...` | 属性重绑 + `.item()`/`.nonzero()` 循环断图 | `register_buffer(persistent=False)` + forward 内 `self.ctx.copy_(...)` 原地写 |
| PA cache 读 `self.cache_*` | GE 图数据流依赖断流 | 用 cache 算子（`npu_kv_rmsnorm_rope_cache`）的**返回值**而非读 `self.cache_*` |

注：图不支持某算子常带**版本锁定**语义（"该 CANN/GE 版本尚不支持 cummax"）——迁到新版前须复核是否已支持。`npu_geglu` 手动路径与 eager 融合路径**非比特一致**（BF16 舍入 + AllReduce 加法顺序累积，输出语义连贯但文本不完全一致）；且早期把 `use_fused_geglu` 全局设 False 会致 prefill 首 token 偏移——应按 `is_prefill` 动态选（prefill 保留融合、decode 走手动）。

## 配套：静态化以支持整图

整图编译还需把图编译期须静态的张量 `_mark_static`（如 absorb/prolog 权重、`block_table`），但**原地更新的 cache 本身不 mark_static**；`actual_seq_lengths_kv` 值每步变会触发重编译，改用接受 Tensor 的 `tng.ops.npu_fused_infer_attention_score` + `dynamic=False`（类型契约见 [fia-actual-seq-lengths-kv-backend-type](../../../runbooks/runtime/fia_actual_seq_lengths_kv_backend_type.md)）。输入签名稳定见 [graph-mode-stable-input-signature-recompile](../../../runbooks/performance/graph_mode_stable_input_signature_recompile.md)；host 侧入参预算复用见 [decode-host-scalar-precompute-passthrough](../../../optimizations/experience/rules/decode_host_scalar_precompute_passthrough.md)；用 `@torch._dynamo.disable` 把不该入图的构建隔离出图见 [cache-compile-fail-dynamic-build-in-compile-region](../../../runbooks/compilation/cache_compile_fail_dynamic_build_in_compile_region.md)。

## 参考实现及其约束

综合参考实现在 LongCat-Flash-Lite decode 整图编译（`NgramEmbedding` register_buffer、`_shift_right_ignore_eos` 的 cummax→展开 max、boolean-mask→乘法掩码、PA cache 用算子返回值）——报告自报 GE 整图使 A2 decode 92→18.5 ms（−79.9%，仓自报无独立复测）；hy3-preview 的 forward host 同步移除、DeepSeek-V3.2-Exp 的 host-list→arange、LLaDA2.x-sglang DLLM 向量化、Gemma-4 GEGLU 手动路径。模型专属的算子名/分派点是参考实现细节；"上图前消除 host 同步 / host 构造 / 图不支持算子，图路径与 eager 按 is_prefill 分派"是跨模型可迁移的图适配范式。

## Evidence

- 维护者确认 + diff 佐证（@f7e80e5fbd73）：forward 内 `.cpu().tolist()` prefill 断流/decode 断图，图 decode 路径无 host 同步；仓自报 decode 293→~28.4 ms/t。溯源下探 [cann-recipes-infer-pr-403-feat-adapt-and-optimize-hy3-preview-inference-via-deepseek-v4-pro-recipe](https://gitcode.com/cann/cann-recipes-infer/merge_requests/403)
- diff 事实（@f8bb1545）：aclgraph 捕获区 host list 构造改 `torch.arange(...)`。溯源下探 [cann-recipes-infer-pr-204-feat-dsv3-2-support-acl-graph](https://gitcode.com/cann/cann-recipes-infer/merge_requests/204)
- diff 事实（@8cd85a87af03）：DLLM 去掩码更新向量化消除 `.item()` 同步以入图（单点稀疏写、`input_ids.copy_`）。溯源下探 [cann-recipes-infer-pr-284-feat-llada2-x-sglang-ascend](https://gitcode.com/cann/cann-recipes-infer/merge_requests/284)
- diff 事实 + 作者报告（@8721be444490）：图模式 `npu_geglu` 不可用、`aten::gelu` aclgraph 回退 CPU，decode 手动 `npu_fast_gelu(gate)*up`、prefill 保留融合；手动路径与 eager 非比特一致。溯源下探 [cann-recipes-infer-pr-408-feat-add-gemma-4-model-optimized-by-agent-skills](https://gitcode.com/cann/cann-recipes-infer/merge_requests/408)
- diff 事实（@895615c）：GE 后端无 `cummax`，图路径用固定形状展开 `torch.maximum` 链，`cummax` 留 eager(prefill)；注释"GE graph backend has no cummax"，版本锁定。溯源下探 [cann-recipes-infer-pr-462-refactor-longcat-flash-lite-tnd-pa-npugraph-ex-mc2-ep-decode](https://gitcode.com/cann/cann-recipes-infer/merge_requests/462)
- diff 事实 + 仓自报数值（@8fd8db72）：decode 整图消除图中断清单（乘法掩码/register_buffer/cummax 展开/actual_seq_lengths Tensor/PA cache 返回值/mark_static）；92→18.5 ms 为 optimization_report 仓自报。溯源下探 [cann-recipes-infer-pr-348-feat-add-longcat-flash-lite-model-optimized-by-agent-skills](https://gitcode.com/cann/cann-recipes-infer/merge_requests/348)

<!-- cannbot:related:start -->
## 相关

- [FIA 的 actual_seq_lengths_kv 类型随后端不同：torch.ops.npu/npugraph_ex 要 host list、torchair/ge_graph 要 Tensor](../../../runbooks/runtime/fia_actual_seq_lengths_kv_backend_type.md)（`related`）：`actual_seq_lengths_kv` 值每步变会触发重编译，改用接受 Tensor 的 `tng.ops.npu_fused_infer_attention_score` + `dynamic=False`；经 `torch.ops.npu`（eager 及 npugraph_ex 的 `torch.compile`/dynamo 路径）时，dynamo 按 `SymInt［］` schema 校验该入参——**传 Tensor 会失败**，必须传 host Python list。。指南的 Tensor+dynamic=False 改写适用于 tng.ops 的 ge_graph 路径，运行手册补上 torch.ops.npu/npugraph_ex 必须使用 host list 的相反类型契约，防止跨后端误套。
- [NPU LLM 图模式启用骨架：decode-only 编译 + ge_graph / acl_graph / npugraph_ex 后端编译入口与配置约束](../../../optimizations/experience/rules/graph_mode_decode_only_compile_backends.md)（`related`）：要把一段 decode 逻辑整图编译进 GE 图 / aclgraph（［npu-graph-mode］(../../../concepts/techniques/npu_graph_mode.md)），但它含 host 依赖或图后端不支持的算子，捕获失败 / 断图 / 走 CPU fallback。；要给一个 NPU 上的 LLM 推理开 ［图模式］(../../../concepts/techniques/npu_graph_mode.md)（压掉逐算子下发的 host 调度开销）时，先照这套骨架搭编译路径，再谈模型侧的图适配。。后端规则先确定 decode-only 编译入口与 ge_graph/npugraph_ex 路线，本指南随后消除模型代码里的捕获中断，二者是同一入图任务的先后步骤。
- [NPU 图模式（ge_graph / npugraph_ex）](../../../concepts/techniques/npu_graph_mode.md)（`related`）：要把一段 decode 逻辑整图编译进 GE 图 / aclgraph（［npu-graph-mode］(../../../concepts/techniques/npu_graph_mode.md)），但它含 host 依赖或图后端不支持的算子，捕获失败 / 断图 / 走 CPU fallback。；图模式通过 `torch.compile` 把前向逻辑捕获成图、交给 NPU 后端编译执行，**减少 Host 下发开销，允许后端在更大范围做融合、内存复用、调度优化**，显著降低 decode 时延。。指南针对概念页的 NPU 图捕获目标，给出 host 同步、host 构造和后端算子支持造成 graph break 时的可执行改写。
- [cache_compile / 图缓存失败：动态构建（KV cache 初始化 / row_idx 生成）落在编译区——挪出或 @dynamo.disable 隔离](../../../runbooks/compilation/cache_compile_fail_dynamic_build_in_compile_region.md)（`related`）：用 `@torch._dynamo.disable` 把不该入图的构建隔离出图见 ［cache-compile-fail-dynamic-build-in-compile-region］(../../../runbooks/compilation/cache_compile_fail_dynamic_build_in_compile_region.md)。；被编译的 decode 路径里若含"惰性初始化 / 首轮才建 / 每步换新对象"的动态构建，会与"缓存同一张已编译图"冲突：。指南给出 @torch._dynamo.disable 的图外隔离手段，运行手册说明 KV cache 与 row_idx 动态构建如何破坏 cache_compile 以及应上提生命周期。
- [消除 decode/生成热路径每步重复的 host 侧算子入参准备（scale / seq-length / 量化 scale：预算一次 + 透传/缓存复用）](../../../optimizations/experience/rules/decode_host_scalar_precompute_passthrough.md)（`related`）：host 侧入参预算复用见 ［decode-host-scalar-precompute-passthrough］(../../../optimizations/experience/rules/decode_host_scalar_precompute_passthrough.md)；通用症结：**每前向重复做、但在稳态内容不变的 host 侧算子入参准备**（标量 scale、seq-length 小张量、量化 scale）是可去除的固定开销——它落在 host、每层/每步触发，造成下发中断与 H2D 强同步。。图安全指南要求移除 forward 的 host 依赖，规则页把稳态不变的 scale、seq-length 和量化 scale 上提并透传，给出该要求的性能化实现。
<!-- cannbot:related:end -->
