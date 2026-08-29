---
type: Concept
title: mambav2_rmsnormgated
description: AscendC 实现的 Mamba v2 风格 RMSNorm + SiLU(z) + Mul 融合算子，Qwen3-Next gated-deltanet 输出段使用。BF16 输入输出（`x`, `z`, `w`），FP32 内部计算，单 AIV kernel 完成归一化、门控激活、权重缩放和逐元素相乘，消除三次独立 kernel launch 和两次中间 BF16 转存。
tags:
- task.implementation
- topic.model_architecture
- topic.attention
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/qwen3-next/ops/gated_delta_net/rmsnormgated/torch_interface.cpp
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-06-27T00:00:00Z'
platforms:
- a3
---

# mambav2_rmsnormgated

## Summary

AscendC 实现的 Mamba v2 风格 RMSNorm + SiLU(z) + Mul 融合算子，Qwen3-Next [gated-deltanet](../modules/gated_deltanet.md) 输出段使用。BF16 输入输出（`x`, `z`, `w`），FP32 内部计算，单 AIV kernel 完成归一化、门控激活、权重缩放和逐元素相乘，消除三次独立 kernel launch 和两次中间 BF16 转存。

## Role In Pipeline

- 输入：`x`（B,S,D，GDN attn 输出）、`z`（B,S,D，gate 分支）、`w`（RMSNorm 权重，尺寸为 `group_size = D/G`，即 norm.weight 的 per-head 维，`headdim = w.size(0)`，跨 G 组广播复用）、`G`（group 数）、`eps`。
- 输出：`out = (RMSNorm(x, w, G, eps)) * SiLU(z)`，shape 与 x 相同。
- 由 `torch.ops.npu_ops_transformer_ext.mambav2_rmsnormgated` 调用；Meta 函数 `mambav2_rmsnormgated_meta` 对输入做 `TORCH_CHECK(x.defined())` 校验后直接返回输入张量 `x`（用于形状/dtype 推断），并非分配新张量——真正分配输出的是 device 实现里的 `torch::empty(x.sizes(), x.options())`。
- 核心数可由环境变量 `RMSNORMGATED_BLOCK_DIMS` 指定（默认 1，建议默认）。

## Performance Signals

- 分组归一：`group_size = D/G`，`BASED = 2048`，`BASEG = BASED/group_size`；每核 `loopnum = ceil_div(B·S, BlockNum·2)` 行。
- 双缓冲 MTE2↔V↔MTE3 事件流水：`DEvent<PIPE_MTE2, PIPE_V> in_ready`、`DEvent<PIPE_V, PIPE_MTE3> out_ready` 等 4 个事件组成 ping-pong；下次迭代的 x/z MTE2 预取与当前迭代的 V 计算并行。
- 内部缓冲全部 FP32（`fp32_xbuf`、`fp32_normbuf`、`fp32_zbuf`、`fp32_wbuf`、`fp32_squarebuf`、`fp32_silubuf`），BF16 只在 GM ↔ UB 边界存在；Cast 使用 `RoundMode::CAST_NONE`（input）/ `CAST_RINT`（output）。
- 权重 `w` 只在首次迭代加载，整核复用；`w_mul_params` 设置 `src1RepStride=0` 做权重广播，`dstRepStride=src0RepStride=16` 按 BLK 对齐乘。
- SiLU(z) 序列：`z → -z → exp → +1 → 1/(…) → · z`，全部 FP32，dispatch 到 `fp32_silubuf`。

## Optimization Notes

- 融合收益：原 SGLang 路径为 `RMSNorm` → `SiLU` → `Mul` 三个独立算子，产生两次 BF16 中间结果往返 GM。融合后仅一次 GM→UB + 一次 UB→GM；BF16/FP32 Cast 仅在 edge 发生。
- Grouped RMSNorm：按 `group_size` 分组做 ReduceSum(x²) → /n → +eps → sqrt → 倒数 → Brcb 广播；两次 `Brcb` 将 rstd 扩展成与 x 对齐的 per-element scale 向量，再逐组 Mul。
- Cube handler 保留占位（空 `Init/Compute` + dummy `mad`），当前只激活 AIV；为未来 Cube 版本预留结构（例如将 grouped MatMul 融入）。
- 使能方式：环境变量 `USE_CUSTOM_NORM_KERNEL="true"`；可选 `RMSNORMGATED_BLOCK_DIMS` 指定核数。
- 与 [recurrent-gated-delta-rule](recurrent_gated_delta_rule.md) 组合，实现 Decode GDN 路径的端到端融合；在 stage5 patch 中被 `ascend_backend.py` 和 `qwen3_next.py` 直接调用。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/qwen3-next/ops/gated_delta_net/rmsnormgated/torch_interface.cpp`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/qwen3-next/ops/gated_delta_net/rmsnormgated/torch_interface.cpp)、`op_kernel/CustVec.h`；`models/qwen3-next/patches/stage5/0001-feat-support-GDN-and-rmsnormgated-fusion-ops.patch`；README "新增特性使能" 表。

## Links

- [qwen3-next](../models/qwen3_next.md)
- [gated-deltanet](../modules/gated_deltanet.md)
- [recurrent-gated-delta-rule](recurrent_gated_delta_rule.md)
- [ascendc](../frameworks/ascendc.md)
- [atlas-a3](../platforms/atlas_a3.md)
- [mamba-ssm-train](../../../training/concepts/modules/mamba_ssm_train.md)（训练侧 Mamba2 SSM：mamba_mixer / SSD chunk 矩阵化 / SSM 上下文并行）

<!-- cannbot:related:start -->
## 相关

- [Gated DeltaNet (GDN)](../modules/gated_deltanet.md)（`related`）：“AscendC 实现的 Mamba v2 风格 RMSNorm + SiLU(z) + Mul 融合算子，Qwen3-Next ［gated-deltanet］(../modules/gated_deltanet.md) 输出段使用。BF16 输入输出（`x`, `z`, `w`），FP32 内部计算，单 AIV kernel 完成归一化、门控激活、权重缩放和逐元素相乘，消除三次独立 kernel launch 和两次中间 BF16 转存。”与“**输出 Norm 变体**：Qwen3-Next 用 AscendC `mambav2_rmsnormgated` 融合算子；Qwen3.5-MoE 用 `Qwen3_5MoeRMSNormGated`（`torch_npu.npu_rms_norm` + 门控相乘）。”分别给出双端正文事实；模块卡明确把该融合算子指定为 Qwen3-Next GDN 输出 Norm 路径，算子卡给出 RMSNorm、SiLU 与 Mul 的实现合同，二者连接模块阶段与具体 kernel。
<!-- cannbot:related:end -->
