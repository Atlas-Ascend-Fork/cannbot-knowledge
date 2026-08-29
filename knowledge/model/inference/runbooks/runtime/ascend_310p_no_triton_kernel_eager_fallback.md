---
type: Runbook
title: Ascend 310P 不支持 Triton kernel：走 Triton 的算子须补纯 host/eager 等价路径
description: 在 **Ascend 310P（Atlas 300I 推理卡系列 / 300I Duo）** 上做 bringup / 跑推理时，凡是通用（跨平台）执行路径经由 **Triton kernel** 实现的算子，在 310P 上都不可用——310P 硬件不支持 Triton。这是 310P 的固有平台能力约束，不随某次修复消失，也不出现在支持 Triton 的 A3/A2 上。
tags:
- task.debugging
- topic.model_architecture
- topic.attention
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/7430
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/pull/8085
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-07-15T00:00:00Z'
platforms:
- 310p
---

# Ascend 310P 不支持 Triton kernel：走 Triton 的算子须补纯 host/eager 等价路径

## 适用场景

在 **Ascend 310P（Atlas 300I 推理卡系列 / 300I Duo）** 上做 bringup / 跑推理时，凡是通用（跨平台）执行路径经由 **Triton kernel** 实现的算子，在 310P 上都不可用——310P 硬件不支持 Triton。这是 310P 的固有平台能力约束，不随某次修复消失，也不出现在支持 Triton 的 [A3](../../concepts/platforms/atlas_a3.md)/A2 上。

一个通用后端（如 vLLM 昇腾后端 vllm-ascend）常把某些算子实现为 Triton kernel（gating 数学、KV cache 的 slot_mapping / block-table 索引计算等）。若 310P 的执行路径落回这些通用 Triton 路径，就会：算子跑不起来、或运行时崩溃。因此**在 310P 上，凡是通用路径经由 Triton 计算的地方，都需要为 310P 提供一份纯 host（eager PyTorch / NumPy）的等价实现来绕开 Triton**——这是可迁移的判断，下一个做 310P bringup、或把带线性注意力 / [gated-delta（GDN）](../../concepts/modules/gated_deltanet.md) 结构的模型部署到 300I Duo 的人同样会撞到。

该约束有两个具体信号：**(A)** GDN gating 这类 Triton 算子在 310P 上无可执行路径；**(B)** KV cache slot_mapping / block-table 计算走通用 Triton 路径在 310P 上运行时崩溃。二者根因同一（310P 无 Triton），修法同型（补 Triton-free 等价路径）。

### 信号 A：Triton kernel 算子在 310P 上无可执行路径（以 GDN gating 为例）

- **症状**：把带 [GDN / 线性注意力](../../concepts/kernels/recurrent_gated_delta_rule.md) 结构的模型部署到 310P（300I Duo），用到的 gating 算子（主线以 Triton kernel 实现）在 310P 上无法执行 → 用到该算子的模型起不来。
- **触发条件**：算子的通用实现是 Triton kernel（例：`fused_gdn_gating`，主线 `fused_gdn_gating_patch` 为 Triton 版），且目标硬件为 310P。
- **根因**：310P 不支持 Triton，Triton 版算子在 310P 上不可执行。
- **修法**：为该算子补一份语义对齐的 **eager PyTorch fallback**，310P 专属子树（如 `vllm_ascend/_310p/`）导出它。GDN gating fallback 的数学（`fused_gdn_gating_pytorch(A_log, a, b, dt_bias, beta=1.0, threshold=20.0)`）：

  ```
  x = a + dt_bias
  softplus(x) = (1/beta)*log1p(exp(beta*x))  若 beta*x <= threshold  否则退化为 x  # 带 threshold 的分段实现，避免 overflow
  g = -exp(A_log) * softplus(x)
  beta_output = sigmoid(b)
  # 末尾对 g / beta_output 各 unsqueeze(0) 补 sequence 维；g 形状 [1, batch, num_heads]，beta_output 同形
  ```

  该 fallback 的两点写法（fallback-vs-kernel 数值一致性纪律，非普适定律）：**(1)** 非线性 gating 数学（softplus / exp）先把输入 `.to(torch.float32)` 在 fp32 计算以保稳定；**(2)** `beta_output = torch.sigmoid(b_f).to(b.dtype)`——sigmoid 在 fp32 算完后 **cast 回输入 `b` 的 dtype**，否则输出 dtype 会与 Triton kernel 不一致、引下游问题。
- **correctness 验证**：写 parity UT，在**支持 Triton 的卡**上跑（310P 上无 Triton 版可比），同一份 fp16 随机输入（如 `num_tokens=37, num_heads=8`）分别过 Triton 版与 PyTorch fallback，`torch.testing.assert_close` 在 fp32 下 `rtol=atol=1e-2`、`equal_nan=True` 校验 `g` 与 `beta` 两路一致。

### 信号 B：KV cache slot_mapping / block-table 走通用 Triton 路径在 310P 上崩溃

- **症状**：在 310P 上跑 vLLM v1 推理，执行路径落到通用（基类）的 `NPUInputBatch` / `BlockTable.compute_slot_mapping`（其 slot_mapping 计算依赖 Triton kernel）时**运行时崩溃**。
- **触发条件**：310P worker 走通用 `vllm_ascend.worker.npu_input_batch.NPUInputBatch` / `vllm_ascend.worker.block_table.BlockTable` 的 Triton 版 `compute_slot_mapping`；CI 覆盖不全时（如 tracker 只盯 `model_runner_v1.py`、不盯 `worker/**`）该路径会被漏掉、错误地进入 Triton。涉及 DCP/PCP context-parallel 交织（`cp_kv_cache_interleave_size`）时也覆盖。
- **根因**：310P 不支持 Triton kernel，通用 slot_mapping/block_table 计算走 Triton → 崩溃。
- **修法**：不改通用路径，而是给 310P **派生一套 Triton-free 的等价实现**并把 model runner 切过去：
  - 新增 `_310p/block_table.py`（`BlockTable` 继承 `AscendBlockTable`、`MultiGroupBlockTable` 继承 `AscendMultiGroupBlockTable`），用**纯 NumPy 在 host 上重写 `compute_slot_mapping`**：
    - 非 CP 分支：`logical_block_idx = positions // block_size` → 取 `block_numbers` → `np.add(block_numbers*block_size, block_offsets, out=slot_mapping.np[:num_tokens])` → `copy_to_gpu(num_tokens)`。
    - CP 分支（`dcp_world_size * pcp_world_size > 1`）：按 `virtual_block_size = block_size * dcp_world_size * pcp_world_size` 算 virtual block/offset，`current_rank = dcp_world_size*pcp_rank + dcp_rank`，用 mask（`virtual_block_offsets // cp_kv_cache_interleave_size % (dcp*pcp) == current_rank`）把不属本 rank 的槽位写 `PAD_SLOT_ID`。
    - `_normalize_slot_mapping_inputs` 同时兼容 2 参（`req_indices, positions`）与 3 参（`num_reqs, query_start_loc, positions`）调用签名，输入统一 `_to_numpy(...).astype(int64)`。
  - 新增 `_310p/npu_input_batch.py`（`NPUInputBatch310` 继承通用 `NPUInputBatch`），构造时把 `self.block_table` 换成上面的 `_310p` `MultiGroupBlockTable`。
  - 改 `_310p/model_runner_310p.py`：import 从通用 `NPUInputBatch` 切到 `NPUInputBatch310`，并在 `NPUModelRunner310.__init__` 用它重建 `self.input_batch`（传 `block_sizes` / `kernel_block_sizes` / `cp_kv_cache_interleave_size` 等）。
- **correctness 验证**：310P 派生路径以行为 UT（`tests/ut/_310p/test_block_table_310p.py`，覆盖 2 参/3 参签名与 CP mask 输出 `[0,-1,...,1,-1,...]`）保正确性；此为崩溃修复，无性能数字。

## 修法的通用形态与边界

- **通用形态**：把 310P 专属实现放进 310P 子树（`_310p/`），对通用路径**派生 / override**而非改基类，让 310P 完全避开 Triton；有 Triton 版可对照时补 parity UT，无对照时补行为 UT（签名 / CP mask 输出）。
- **fallback 数值一致性**：eager fallback 与 Triton kernel 须逐路对齐——非线性数学在 fp32 算、输出 cast 回 kernel 的 dtype，否则 dtype 漂移引下游问题（见信号 A）。
- **边界**：范围限 **310P 无 Triton** 这一平台约束，不外推到「所有 Triton 算子 / 所有硬件」；A3/A2 支持 Triton、不适用本页。GDN gating / block_table 只是两个已知实例，判断本身覆盖「310P 上任何走 Triton 的算子」。CI 需把 310P tracker 覆盖到 `worker/**` 级别，否则新走 Triton 的路径会漏检、在 310P 上回归崩溃。

## 相关经验
- [Ascend 310P 不支持图模式：aclgraph capture 抛 ACL_MODE](ascend_310p_graph_mode_unsupported_enforce_eager.md)
- [昇腾多模态 M-RoPE 优先走 triton-ascend triton_mrope，de](../../optimizations/experience/rules/mrope_triton_ascend_vs_npu_mrope_decode.md)

- [昇腾融合算子按硬件条件门控回退到非融合等价路径](../../optimizations/experience/rules/fused_op_hardware_conditional_fallback.md)——同样是「算子路径按硬件能力门控 + 回退等价实现」的形态，但那里的抓手是 SoC 白名单 / matmul 轴上限，本页的抓手是 310P 无 Triton。
- [仅 fp16 平台需把 bf16 权重 cast](../precision/precision_fp16_only_platform_bf16_weight_cast.md)——同属「某昇腾平台缺某能力、须为其补专属路径」的 bringup 约束。

## Evidence

- **代码事实（信号 A）**：merge commit `13397e9cb75721f7365cfc4c22738320aac21d54`，`vllm_ascend/_310p/ops/fla/fused_gdn_gating.py` 新增 `fused_gdn_gating_pytorch` + `__init__.py` 导出 + parity UT `tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_fused_gdn_gating.py`；PR body「Add a PyTorch implementation of the GDN gating operator on 310P」/ docstring「fallback implementation for 310P without Triton support」/ RFC「Deploy Qwen3.5 series model on 300I Duo」三处印证 310P 无 Triton → 补 PyTorch fallback。`beta_output` cast-回-dtype 一致性由 review 提示、合并态已按此修。
- **代码事实（信号 B）**：merge commit `4aacaf888827da87fa3909cdddd8225a6959dd40`（2026-04-09 合入），`vllm_ascend/_310p/block_table.py`、`vllm_ascend/_310p/npu_input_batch.py` 为新增文件，`model_runner_310p.py` import 切换 + `input_batch` 重建；PR 描述明确「310P devices do not support Triton kernels ... the 310P execution path can incorrectly enter Triton kernels, causing runtime crashes on 310P」。CI tracker 从只盯 `model_runner_v1.py` 放宽到 `vllm_ascend/worker/**`。
- **归因边界**：根因「310P 不支持 Triton」由两处 PR 描述明确陈述；修法（补 Triton-free 等价路径）与根因自洽——被绕开的是 310P 本就不支持的 Triton，非某通用正确机制。fp32-稳定 / dtype-parity 两点为 fallback 写法事实，非平台定律。
- 溯源下探：[vllm-ascend-pr-7430-310p-fused-gdn-gating-ut](https://github.com/vllm-project/vllm-ascend/pull/7430)、[vllm-ascend-pr-8085-bugfix-310p-fix-triton-kernel-in-block-table-crash-that-caused-failures](https://github.com/vllm-project/vllm-ascend/pull/8085)

<!-- cannbot:related:start -->
## 相关

- [310P 上 dense/VL 模型 bringup：须显式规避的不可用算子路径 + KV cache/mask 的 NZ 布局约束](../../optimizations/experience/anti_patterns/ascend_310p_bringup_unusable_ops_and_nz_layout.md)（`related`）：一批在 A2/A3 上正常的算子路径与执行模式在 310P 上**不可用或未实现**；在 310P 上，凡是通用路径经由 Triton 计算的地方，都需要为 310P 提供一份纯 host（eager PyTorch / NumPy）的等价实现来绕开 Triton。候选卡把焦点卡的通用不可用算子检查落实为 Triton-free fallback 的实现与验证链。
- [Ascend 310P 不支持图模式：aclgraph capture 抛 ACL_MODEL_RI_CAPTURE_STATUS_ACTIVE INTERNAL ASSERT，须加 --enforce-eager](ascend_310p_graph_mode_unsupported_enforce_eager.md)（`related`）：这是与 ［310P 不支持 Triton kernel］(ascend_310p_no_triton_kernel_eager_fallback.md) 并列的另一条 310P 平台能力缺口：一个是无图模式（修法=关图模式跑 eager），一个是无 Triton（修法=补 Triton-free host 等价路径）。 该约束有两个具体信号：**(A)** GDN gating 这类 Triton 算子在 310P 上无可执行路径；**(B)** KV cache slot_mapping / block-table 计算走通用 Triton 路径在 310P 上运行时崩溃。 显式并列关系将 aclgraph capture 与 Triton 缺失的报错、根因和 fallback 分开，支撑 310P bringup 排查。
- [Triton-on-Ascend（昇腾 Triton 算子后端）](../../../training/concepts/frameworks/triton_on_ascend.md)（`related`）：“Triton-on-Ascend 让用 **Triton DSL**（`@triton.jit` + `tl.load/store` + `tl.dot` 的 SPMD 内核语法）写的融合算子直接跑在昇腾 NPU 上”；“在 **Ascend 310P（Atlas 300I 推理卡系列 / 300I Duo）** 上做 bringup / 跑推理时，凡是通用（跨平台）执行路径经由 **Triton kernel** 实现的算子，在 310P 上都不可用——310P 硬件不支持 Triton。”。后端能力卡与 310P 失败边界共同决定 Triton 算子的硬件可达性和 fallback 要求。
- [昇腾多模态 M-RoPE 优先走 triton-ascend triton_mrope，decode 吞吐优于原生 npu_mrope](../../optimizations/experience/rules/mrope_triton_ascend_vs_npu_mrope_decode.md)（`related`）：“- 依赖 `triton-ascend`（［Atlas A3］(../../../concepts/platforms/atlas_a3.md) / A2 支持 Triton；Ascend 310P 不支持 Triton，须自动回退）。”；“在 **Ascend 310P（Atlas 300I 推理卡系列 / 300I Duo）** 上做 bringup / 跑推理时，凡是通用（跨平台）执行路径经由 **Triton kernel** 实现的算子，在 310P 上都不可用——310P 硬件不支持 Triton。”。经验卡的 310P 自动回退条件由 runbook 的硬件能力边界直接解释。
<!-- cannbot:related:end -->
