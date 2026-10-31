---
type: Optimization
title: 自定义算子框架决定可用图后端：PyPTO 仅 GE 入图（无 eager/aclgraph）、tilelang 仅 aclgraph
description: 自定义算子框架决定可用图后端：PyPTO 仅 GE 入图（无 eager/aclgraph）、tilelang 仅 aclgraph。给一个用自定义算子框架（PyPTO / tilelang）写的模型/算子链路规划图模式时——先看该框架的算子注册形态支持哪条图路径，再选后端，别默认"图模式=随便挑 ge_graph/aclgraph/eager"。算子的注册形态（有没有 eager kernel、有没有 GE converter）直接决定它只能被哪种图捕获。
tags:
- task.optimization
- topic.graph_execution
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/83
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/133
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T15:32:47Z'
platforms:
- agnostic
---

# 自定义算子框架决定可用图后端：PyPTO 仅 GE 入图（无 eager/aclgraph）、tilelang 仅 aclgraph

## 适用场景

给一个用自定义算子框架（[PyPTO](../../concepts/frameworks/pypto.md) / [tilelang](../../concepts/frameworks/tilelang.md)）写的模型/算子链路规划图模式时——**先看该框架的算子注册形态支持哪条图路径，再选后端**，别默认"图模式=随便挑 ge_graph/aclgraph/eager"。算子的注册形态（有没有 eager kernel、有没有 GE converter）直接决定它只能被哪种图捕获。

## PyPTO 融合算子：只支持 GE 入图，不支持 acl graph、不支持 eager

- **结论**：cann-recipes-infer 的 PyPTO 算子（`torch.ops.custom_pypto.*`，如 `npu_lightning_indexer_prolog_pto` / `npu_lightning_indexer_pto` / `npu_sparse_attention_pto`）**只提供 GE 入图路径（TorchAir GE 图）**，不支持 acl graph、也不支持 eager/aclnn 直调。要给用这些算子的链路（如 [DSA](../../concepts/modules/dsa.md) / DeepSeek Indexer Attention）开图模式，只能走 TorchAir GE 图。
- **机制（决定为何）**：算子只注册了 **Meta 实现**（`TORCH_LIBRARY_IMPL(custom_pypto, Meta)`，做 tracing/shape 推导）+ **TorchAir GE converter**（`register_fx_node_ge_converter` + `torchair.ge.custom_op`，成图落地），**全仓无 NPU/PrivateUse1 eager kernel**。Meta+converter 但无 eager kernel ⇒ 算子无法在 eager 流上单独执行 ⇒ 只能进 TorchAir GE 图。acl graph（ACL runtime 抓图，类 CUDA graph）需要算子先在 eager 流上执行才能被捕获，PyPTO 算子没有 eager kernel，故不支持 acl graph（此机制推断与维护者结论一致）。
- **不要做**：规划 acl graph 抓图这些算子、或 eager/aclnn 直调它们——会因缺 eager 落地而不可行。PyPTO 的 DSA 落地手段另见 [pypto-dsa-fused-attention-decompose-quant](pypto_dsa_fused_attention_decompose_quant.md)。

## tilelang-ascend 算子：走 aclgraph 进图，短期无 GE 图规划

- **结论**：要让 tilelang(`@tilelang.jit`)自定义算子被图执行捕获（减少逐 kernel 下发调度开销），走 **aclgraph**（`torch.npu.NPUGraph` capture/replay）路径；**GE 图接入维护者称短期无规划**（roadmap，可变）。已有可运行的 tilelang + aclgraph 参考实现（RMS Norm → RoPE）。
- **参考三步法**（capture/replay）：
  ```python
  g = torch.npu.NPUGraph()
  with torch.npu.graph(g):          # 只记录、不立即执行
      q = tilelang_rms_norm(q, eps); q = tilelang_apply_rope(q, sin, cos)
  g.replay()                        # 提交整图执行；可多次 replay
  ```
  算子用 `@tilelang.jit(out_idx=[-1], pass_configs=pass_configs)` 定义，kernel 内 `with T.Kernel(m_num, is_npu=True)`；`pass_configs` 四项：`TL_ASCEND_AUTO_SYNC`（共享 buffer 读写自动插同步）、`TL_ASCEND_MEMORY_PLANNING`（昇腾内存规划）、`TL_ASCEND_AUTO_CV_SYNC`（Cube/Vector 核间同步）、`TL_ASCEND_AUTO_CV_COMBINE`（合并跨核通信）。
- **验证 aclgraph 是否生效**：Host 编译 info 日志搜 `capture model`（0=未开 / 1=已开），配 `ASCEND_HOST_LOG_FILE_NUM` / `ASCEND_PROCESS_LOG_PATH` / `ASCEND_GLOBAL_LOG_LEVEL=1`；correctness 用 `torch.testing.assert_close(rtol=1e-2, atol=1e-2)`。
- **内存注意**：tilelang 下发到 device 的 kernel 常驻 device 内存、随进程结束才释放（维护者口头确认）——做 memory 规划/排查 tilelang 算子内存占用时留意。tilelang 的框架/版本分支坑见 [tilelang-op-framework-version-branch-skew](../../runbooks/compilation/tilelang_op_framework_version_branch_skew.md)。

## 对照

| 自定义算子框架 | GE 图 | aclgraph | eager | 记住 |
|---|---|---|---|---|
| PyPTO（`custom_pypto`） | ✅ 唯一 | ✗ | ✗ | 只能 TorchAir GE 图 |
| tilelang-ascend | ✗（短期无规划） | ✅ | — | 走 `torch.npu.NPUGraph` |

## 参考实现及其约束

参考实现：PyPTO 的 `ops/pypto/torch_ops_extension/custom_pypto`（Meta impl + GE converter、无 eager kernel）+ DeepSeek-V3.2-Exp indexer 调用；tilelang-ascend `examples/aclgraph/rms_rope_aclgraph.py` + README。tilelang「短期无 GE 图规划」是维护者 roadmap 陈述（可变，迁移前复核）；结论范围限本仓 `custom_pypto` 命名空间与 tilelang-ascend 该分支，未外推为"所有 PyPTO/tilelang 处处如此"；"看算子注册形态定可用图后端"是可迁移判断。图后端启用骨架见 [graph-mode-decode-only-compile-backends](../../guides/optimization/graph_mode_decode_only_compile_backends.md)。

## 相关经验
- [自定义算子接图模式的 lowering 正确性：converter 按 GE IR 原型对齐](../../runbooks/precision/custom_op_graph_lowering_converter_meta_correctness.md)

- 另见 [图模式下 KV cache 就地更新与 MLA-prolog 入参适配：静态预分配 / 就地写 cache 算子 / inplace 看护 / 空 kr_cache](graph_mode_kvcache_inplace_mla_prolog_adaptation.md)。


## Evidence

- [远程来源](https://gitcode.com/cann/cann-recipes-infer/issues/83)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/issues/133)（evidence）
