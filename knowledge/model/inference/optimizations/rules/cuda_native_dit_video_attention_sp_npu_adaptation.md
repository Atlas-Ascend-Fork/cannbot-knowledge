---
type: Optimization
title: CUDA 原生 DiT/视频生成模型移植昇腾：注意力后端改路由 NPU + 绕过 SP 库 CUDA 硬检查
description: '注意力后端是 CUDA 专用的（flash_attn 或 xformers）——NPU 无这些包，import 即失败或运行即错。→ 把注意力改路由到 NPU 融合注意力（npu_fused_infer_attention_score 或 scaled_dot_product_attention）。 序列并行依赖库（xDiT/xfuser + yunchang）内置 CUDA 版本硬检查，初始化阶段强制校验 CUDA 环境，NPU 上直接判失败。→ 在检查点插入 try: import torch_npu 的 NPU 探测分支，跳过 CUDA 校验、保留 GPU 双路径。'
tags:
- task.optimization
- topic.attention
- topic.diffusion
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/29
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/34
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/356
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/353
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-20T12:49:18Z'
platforms:
- agnostic
---

# CUDA 原生 DiT/视频生成模型移植昇腾：注意力后端改路由 NPU + 绕过 SP 库 CUDA 硬检查

## 条件 → 优先尝试什么

把上游 GPU 原生的 [dit](../../concepts/modules/dit.md) / 视频生成模型（HunyuanVideo、SANA-Video 等）搬上昇腾 NPU 时，两类后端假设几乎必然会让它起不来，先按下面处置，不要指望上游代码开箱即用：

1. **注意力后端是 CUDA 专用的**（`flash_attn` 或 `xformers`）——NPU 无这些包，import 即失败或运行即错。→ 把注意力**改路由到 NPU 融合注意力**（[npu_fused_infer_attention_score](../../concepts/kernels/fused_infer_attention_score.md) 或 `scaled_dot_product_attention`）。
2. **序列并行依赖库（xDiT/xfuser + yunchang）内置 CUDA 版本硬检查**，初始化阶段强制校验 CUDA 环境，NPU 上直接判失败。→ 在检查点插入 `try: import torch_npu` 的 NPU 探测分支，**跳过 CUDA 校验、保留 GPU 双路径**。

命中这两点后，[ulysses](../../concepts/parallelism/ulysses.md)（AllToAll 换轴）+ [ring-attention](../../concepts/parallelism/ring_attention.md)（P2P 环形传 KV）序列并行才能在昇腾多卡跑长序列 DiT 推理。

## 做什么（两种落地形态）

### 形态 A：xDiT/xfuser + yunchang 序列并行库（HunyuanVideo）

侵入式改第三方库 + monkey-patch，源保留 GPU 兼容。

**A1. try-import torch_npu 绕过 CUDA 检查（三处，均保留 `except` 走原 CUDA 分支）**：

- `xfuser/envs.py` `PackagesEncChecker.initialize()`：`try: import torch_npu` 成功则 `has_flash_attn=False`；`except ImportError` 走原 `check_flash_attn()`。
- `xfuser/config/config.py`：`try: import torch_npu; from xfuser.envs import TORCH_VERSION, PACKAGES_CHECKER` / `except ImportError:` 走 `CUDA_VERSION` 分支。
- `yunchang/ring/ring_flashinfer_attn.py`：`try: import torch_npu` / `except ImportError: torch_cpp_ext._get_cuda_arch_flags()`。

GPU 上 `import torch_npu` 失败即回落 CUDA 路径——双路径共存、不破坏 GPU。

**A2. monkey_patch 把 `flash_attn_forward` 换成 NPU FIA 包装**：

```python
def npu_fia(q, k, v, dropout_p=0.0, softmax_scale=None, causal=False, ...):
    b, s, n, d = q.shape
    scale = 1.0 / math.sqrt(d)
    block_out, block_lse = torch_npu.npu_fused_infer_attention_score(
        q.transpose(1, 2), k.transpose(1, 2), v.transpose(1, 2),
        num_heads=n, input_layout="BNSD", scale=scale,
        softmax_lse_flag=True, pre_tokens=65535, next_tokens=65535)
    return block_out.transpose(1, 2), block_lse.squeeze(dim=-1)

attn_mod.flash_attn_forward = npu_fia
for mod in list(sys.modules.values()):     # 覆盖所有已 from...import flash_attn_forward 的模块级绑定
    if isinstance(mod, types.ModuleType) and hasattr(mod, 'flash_attn_forward'):
        if mod.flash_attn_forward is not npu_fia:
            mod.flash_attn_forward = npu_fia
```

要点：先替 `yunchang.kernels.attention.flash_attn_forward`，再遍历 `sys.modules` 把所有已解析的同名符号一并替换；`npu_fia` 返回 `(out, lse)` 是因为 Ring Attention 要用 lse 做 online-softmax 跨卡累加（ring 侧 `ring_flashinfer_attn_forward` 用 `RingComm.send_recv` P2P 传 KV，每步 `fn(...)` 得 `(block_out, block_lse)` 后 `update_out_and_lse`）。

**版本前置**：yunchang 需 `7a52abd669efb35e…` 之后、xfuser 需 `e559fe8f07c7cfdd…` 之后；`xfuser<=0.4.4` / `yunchang<=0.6.3.post1` 需按仓内 `appendix/` 手工打补丁。

### 形态 B：xformers 后端模型，靠环境开关切后端（SANA-Video）

上游用 xformers 实现 attention 的模型（观测实例 SANA-Video 2B 文生视频 DiT），不改建模代码，置环境变量即可绕开：

```bash
export DISABLE_XFORMERS=1   # 让 attention 跳过 xformers 分支，回落到 NPU 融合注意力算子
```

比形态 A 轻——不需侵入库、不 monkey-patch，靠模型内已有的 backend 开关切换。下一个把 xformers-based 模型迁昇腾的人，遇到 attention 后端不可用时先查是否需关 xformers。

## 反例 / 边界

- **块稀疏注意力当前只支持 Ulysses、不支持 Ring**：HunyuanVideo 开块稀疏（`--sparse-method` 为 `TopK` / `SVG`，即 `sparse_method != "no_sparse"`）时若再设 `ring_degree > 1`，`sample_video.py main()` 会直接 `raise ValueError("Sparse attention does not support ring_degree > 1 in the current runtime.")`。稀疏路径尚未适配 [ring-attention](../../concepts/parallelism/ring_attention.md)，正确做法是稀疏 + `ulysses_degree > 1` 组合做序列并行，不要配 `ring_degree > 1`。（同 PR 的 README 曾称"稀疏支持与 Ring 组合"，与代码守卫矛盾——以代码守卫为准，README 该表述失真。）稠密路径不受此限。参见 [blockwise-sparse-attention](../../concepts/modules/blockwise_sparse_attention.md)。
- 适用面限定"走 xDiT(xfuser)+yunchang 或 xformers 的 DiT/视频生成模型上昇腾"；不外推到其它 SP 框架。
- 施动者是 cann-recipes-infer 的昇腾适配（侵入改上游库 / 环境开关），非上游库自身能力。

## Rollback

- 形态 A：补丁是原地改拷贝出的第三方库目录，回退 = 删目录重装原库、不污染上游源码。
- 形态 B：`unset DISABLE_XFORMERS`（回 xformers，仅 GPU 环境有意义）。

## 相关经验

- 另见 [NPU 推理脚本 os._exit 快退残留 CANN TBE 孙进程的 shutdown 噪声（RouteServer.finalize 消除）](../../runbooks/runtime/os_exit_tbe_routeserver_shutdown_noise.md)。


## Evidence

- **代码事实**（HunyuanVideo，clone `cann/cann-recipes-infer@5d15b2598ffa`）：`hyvideo/monkey_patch.py` 的 `npu_fia` 与全局符号替换、`appendix/xfuser/envs.py`·`config.py` 的 try-import、`appendix/yunchang/ring/ring_flashinfer_attn.py` 的 P2P 循环、README 附录"侵入式修改外部依赖库"。
- **维护者确认**（HunyuanVideo）：try-import 双路径是"为了兼容 GPU"。
- **代码事实**（SANA-Video，clone `@d7174ec0ba19`）：`config/2b_480p_single.yaml` 的 `DISABLE_XFORMERS: "1"`（注释"route attention to NPU fused kernel"）+ `docs/design/mm_inference_design.md`。
- **代码事实**（稀疏 ⊥ Ring，clone `@a12b2affe2d0`）：`models/hunyuan-video/sample_video.py main()` 新增 `raise ValueError` 守卫（diff 事实）；README 表述与守卫矛盾，取代码为准。
- 溯源下探：
  - [cann-recipes-infer-issue-29-rfc-hunyuanvideo-model-inference-support](https://gitcode.com/cann/cann-recipes-infer/issues/29)
  - [cann-recipes-infer-pr-34-feat-add-hunyuanvideo-model](https://gitcode.com/cann/cann-recipes-infer/merge_requests/34)
  - [cann-recipes-infer-pr-353-feat-hunyuanvideo-support-ulysses-parallelism-with-block-wise-sparse-att](https://gitcode.com/cann/cann-recipes-infer/merge_requests/353)
  - [cann-recipes-infer-pr-356-refactor-unified-inference-script-for-multimodal-models](https://gitcode.com/cann/cann-recipes-infer/merge_requests/356)