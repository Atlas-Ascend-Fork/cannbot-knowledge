---
type: Optimization
title: 310P 上 dense/VL 模型 bringup：须显式规避的不可用算子路径 + KV cache/mask 的 NZ 布局约束
description: Ascend 310P 上部署 Qwen2.5/3 与 Qwen2.5-VL 时，应绕开当前不支持的 MLA、稀疏注意力、MLAPO、batch_matmul_transpose、ATB 预热、KV cache transfer 和共享 KV tensor 路径，并强制 eager 模式。310P attention 仅注册非 MLA、非 sparse 后端，相关 AscendC 算子还会在构建期剔除。可用路径要求 fp16 张量采用 ACL_FORMAT_FRACTAL_NZ，尾维按 16 对齐；KV cache 重排为 16-packing，prefill 与 chunked-prefill 的 mask 也须补齐后转 NZ。forward 仅覆盖 DecodeOnly、PrefillNoCache 和 ChunkedPrefill。以上限制只针对当前 310P 实现，不应外推到 A2/A3。
tags:
- task.debugging
- topic.attention
- topic.kv_cache
- topic.precision
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/5776
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- 310p
---

# 310P 上 dense/VL 模型 bringup：须显式规避的不可用算子路径 + KV cache/mask 的 NZ 布局约束

## 适用场景

你在 **Ascend 310P** 上做 LLM/VL 模型 bringup（判定：`SOC_VERSION=="ascend310p3"`，`is_310p()` 为真），目标是让 dense LLM（如 Qwen2.5/3）或多模态 VL（如 Qwen2.5-VL）在推理框架上先完成正常启动与推理。相较 A2/A3，310P 是能力更受限的推理卡：一批在 A2/A3 上正常的算子路径与执行模式在 310P 上**不可用或未实现**，且 attention 对张量布局有硬性的分形 NZ 约束。若不预先按边界逐项核对与规避，会选到不可构建的定制算子、未实现的 attention 后端、或布局不匹配的 KV/mask，导致构建失败、后端 fallback 到不存在的 key、或算子布局报错。

## 不要做什么（310P 专属边界）

1. **不要依赖 MLA / sparse-flash-attention 的 attention 路径**：310P 当前只注册非-MLA、非-sparse 的 attention 后端（`(use_mla=False, use_sparse=False)`）。任何 attention key 都会 fallback 到这个唯一后端；MLA/SFA 的 310P 后端仅留 TODO 注释、未实现。→ 在 310P 上做模型选型时，走 MLA 或稀疏 attention 的模型当前无法在此路径上正常推理。

2. **不要期望 MLAPO 与 batch-matmul-transpose 定制算子可用**：构建期在 `SOC_VERSION=="ascend310p3"` 时从 AscendC 定制算子集里 `REMOVE_ITEM` 掉 `mla_preprocess_kernel.cpp`（MLAPO）与 `batch_matmul_transpose_kernel.cpp`（构建日志会打印 `310P hardware detected: disabling MLAPO operators` / `excluding batch_matmul_transpose operators`）。→ 这两类定制算子在 310P 根本不构建，运行期不可调用。

3. **不要触发 atb 预热里的 `torch_npu._npu_matmul_add_fp32`**：310P 直接跳过 atb 算子预热（日志 `Skip warm-up atb ops for 310P device`），因为该 atb 算子在 310P 不支持。→ 依赖此 atb 融合的路径在 310P 无效。

4. **不要走图模式 / 期望非-eager 执行**：310P 强制 `set_compile_mode(jit_compile=False)`（eager），worker 类固定为专用 310P worker，不进 xlite/图路径。→ 依赖图捕获、图内融合、图态优化的策略在 310P 上不生效（可另见 [atlas-a3](../../../concepts/platforms/atlas_a3.md) 对比 SoC 能力差）。

5. **不要用 KV cache transfer，也不要多层共享同一 KV tensor**：310P KV cache 初始化在 `kv_transfer_config is not None` 时直接 `raise ValueError("KV cache transfer is not supported for 310P.")`；并 `assert len(kv_cache_tensor.shared_by)==1`（禁止多层共享同一 KV tensor）。→ PD 分离/KV 池化/跨实例 KV 传输、以及跨层 KV 共享（longcat_flash 式）在 310P 上都不可用。

6. **不要在 encoder/prefill 类 attention 上用 `torch_npu._npu_flash_attention_unpad`**：该算子在 310P 有精度问题。多模态视觉 encoder（Qwen2.5-VL）的非因果 attention 因此不走 unpad 算子，改为按 `cu_seqlens` 逐段调用 `torch_npu.npu_prompt_flash_attention`（`input_layout="BSND"`），每段 q/k/v 形状 `[1, S, H, D]`（head_size 按需 pad 到 `MAX_PAD_SIZE` 并补齐到 16 的倍数）。→ 在 310P 上做 encoder/prefill 类 attention，选用 `_npu_flash_attention_unpad` 会撞到精度问题。

## 必须做什么：attention 的 NZ 布局改造

310P 的 attention 算子要求输入张量为**分形 NZ 布局**（`torch_npu.npu_format_cast(..., ACL_FORMAT_FRACTAL_NZ)`）且尾维**按 16 元素对齐**，否则布局不匹配。这是 310P 硬件层的张量布局约束、跨模型复用，不是某模型专属。dtype 走 fp16（310P attention 用 fp16 additive causal mask，上三角填 `float("-inf")`）。

1. **KV cache 形状 16-packing**：把 KV cache shape 重排为
   ```python
   # Align to a multiple of 16, as required by the 310P device
   return (2, num_blocks, (num_kv_heads * head_size) // 16, block_size, 16)
   ```

2. **KV cache 张量 NZ-cast**：`self._acl_format = ACL_FORMAT_FRACTAL_NZ`；每层
   ```python
   k_tensor = torch.zeros(...); k_cache = torch_npu.npu_format_cast(k_tensor, self._acl_format)
   ```

3. **prefill mask 16-对齐 + NZ-cast**（`PrefillNoCache` 路径）：`query/key/value/output` 先过 `aligned_16(t)`；mask 切到 `aligned_len = ((max_len+15)//16)*16`，转 fp16，`nd_to_nz_2d(mask2d)` 后 `npu_format_cast(mask_nz, ACL_FORMAT_FRACTAL_NZ)`；多 batch 时 `mask_nz.repeat(bsz,1,1,1)`。

4. **splitfuse/chunked-prefill mask NZ-cast**（`ChunkedPrefill` 路径）：
   ```python
   mask = torch_npu.npu_format_cast(nd_to_nz_spec(rows).contiguous(), ACL_FORMAT_FRACTAL_NZ)
   ```

5. **状态覆盖有限**：310P attention `forward_impl` 只支持 `DecodeOnly`（paged attention，见 [fused-infer-attention-score](../../../concepts/kernels/fused_infer_attention_score.md) 的 paged 语义）、`PrefillNoCache`（`_npu_flash_attention` fallback）、`ChunkedPrefill`（`_npu_paged_attention_splitfuse`），其余状态 `raise NotImplementedError`。

> ⚠️ 与静态 weight NZ 不同：这里约束的是 **KV cache 与 attention mask 张量**的运行期 NZ 布局，不是权重。

## 适用边界

- 均为「310P 当前」的规避/未实现，不外推到其它 SoC：**MLA / SFA / 图模式在 A2/A3 正常**，只在 310P 缺失。NZ 布局与 16 对齐是 310P attention 算子的真实硬件约束，跨模型复用。
- 覆盖面：310P 上 dense LLM（Qwen2.5/3）与 VL（Qwen2.5-VL）的**非-MLA、非-sparse** attention 后端；MLA/SFA 后端在 310P 尚未实现，本页不描述其行为。
- 概念对照：MLA 见 [mla](../../../concepts/modules/mla.md)；sparse-flash-attention 见 [sparse-flash-attention](../../../concepts/modules/sparse_flash_attention.md)——它们是 310P 当前**不可用**的路径，选型时须避开。

## Evidence

- vllm-ascend 为 310P 新增 Qwen2.5/3 dense 与 Qwen2.5-VL 支持（merge sha `1ffca8673fa460174b891a194560e4fd05eb651d`，"Only dense models work with eager mode now"）。
- 不可用算子/后端/执行边界：`CMakeLists.txt` 的 `REMOVE_ITEM` 排除项与打印、`platform.py get_attn_backend_cls` 的独立 `backend_map_310`、`_310p/worker_310p.py` 的 `_warm_up_atb` 跳过 + `set_compile_mode(jit_compile=False)`、`_310p/modelrunner_310p.py` 的 KV transfer/`shared_by` 的 raise/assert 与 `bind_kv_cache(..., 1)`（310P 不跑 longcat_flash 模式）。
- NZ 布局约束：`_310p/attention/attention_v1.py` 的 `get_kv_cache_shape` 16-packing + 显式注释、`_acl_format = ACL_FORMAT_FRACTAL_NZ`、prefill/splitfuse 两条路径的 `nd_to_nz_*` + `npu_format_cast(..., ACL_FORMAT_FRACTAL_NZ)`、`aligned_16`；`attention_mask.py` fp16 additive mask。
- encoder attention 精度边界：`_310p/ops/mm_encoder_attention.py`（`AscendMMEncoderAttention310`）未使用 `_npu_flash_attention_unpad`，改为按 `cu_seqlens` 逐段 `npu_prompt_flash_attention`（BSND）。
- 溯源 claim（可下探）：
  - [310p-bringup-边界-不可用-mlapo-batch-matmul-transpose-定制算子-mla-sf](https://github.com/vllm-project/vllm-ascend/pull/5776)
  - [310p-上-attention-的-kv-cache-与-mask-张量须为-nz-格式-acl-format-fra](https://github.com/vllm-project/vllm-ascend/pull/5776)
  - [310p-上-torch-npu-npu-flash-attention-unpad-有精度问题-多模态-encoder](https://github.com/vllm-project/vllm-ascend/pull/5776)

<!-- cannbot:related:start -->
## 相关

- [Ascend 310P 不支持 Triton kernel：走 Triton 的算子须补纯 host/eager 等价路径](../../../runbooks/runtime/ascend_310p_no_triton_kernel_eager_fallback.md)（`related`）：一批在 A2/A3 上正常的算子路径与执行模式在 310P 上**不可用或未实现**；在 310P 上，凡是通用路径经由 Triton 计算的地方，都需要为 310P 提供一份纯 host（eager PyTorch / NumPy）的等价实现来绕开 Triton。Triton-free fallback 是排查 310P 不可用算子后的一条实现与验证路径。
- [Ascend 310P 不支持图模式：aclgraph capture 抛 ACL_MODEL_RI_CAPTURE_STATUS_ACTIVE INTERNAL ASSERT，须加 --enforce-eager](../../../runbooks/runtime/ascend_310p_graph_mode_unsupported_enforce_eager.md)（`related`）：一批在 A2/A3 上正常的算子路径与执行模式在 310P 上**不可用或未实现**；在 310P 上部署时默认预期图模式不可用。前者要求 310P bringup 先排除不可用执行模式，后者把其中 aclgraph 路径收敛为必须使用 eager 的可执行处置。
<!-- cannbot:related:end -->
