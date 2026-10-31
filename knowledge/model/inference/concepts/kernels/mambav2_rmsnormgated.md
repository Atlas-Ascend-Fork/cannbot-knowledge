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
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/ops/gated_delta_net/rmsnormgated/torch_interface.cpp
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/ops/gated_delta_net/rmsnormgated/op_kernel/CustVec.h
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/patches/stage5/0001-feat-support-GDN-and-rmsnormgated-fusion-ops.patch
  role: implementation
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-29T15:24:38Z'
platforms:
- a3
---

# mambav2_rmsnormgated

## Summary

AscendC 实现的 Mamba v2 风格 RMSNorm + SiLU(z) + Mul 融合算子，Qwen3-Next [gated-deltanet](../modules/gated_deltanet.md) 输出段使用。BF16 输入输出（`x`, `z`, `w`），FP32 内部计算，单 AIV kernel 完成归一化、门控激活、权重缩放和逐元素相乘，消除三次独立 kernel launch 和两次中间 BF16 转存。

## Role In Pipeline

- 输入符号（不是通用形状承诺，限制见下文）：`x`（B,S,D，GDN attn 输出）、`z`（B,S,D，gate 分支）、`w`（RMSNorm 权重，尺寸为 `group_size = D/G`，即 norm.weight 的 per-head 维，`headdim = w.size(0)`，跨 G 组广播复用）、`G`（group 数）、`eps`。
- 输出：`out = (RMSNorm(x, w, G, eps)) * SiLU(z)`，shape 与 x 相同。
- 由 `torch.ops.npu_ops_transformer_ext.mambav2_rmsnormgated` 调用；Meta 函数 `mambav2_rmsnormgated_meta` 对输入做 `TORCH_CHECK(x.defined())` 校验后直接返回输入张量 `x`（用于形状/dtype 推断），并非分配新张量——真正分配输出的是 device 实现里的 `torch::empty(x.sizes(), x.options())`。
- 核心数可由环境变量 `RMSNORMGATED_BLOCK_DIMS` 指定（默认 1，建议默认）。

## 固定实现的输入限制

x/z/w 必须是连续、storage_offset=0 的 BF16 张量：torch_interface.cpp 使用 storage().data() 作为基址，kernel 只做连续线性寻址，不处理 stride 或非零视图偏移。

CustVec.h 每轮固定读写 2048 元素且没有尾块保护，D=1024 等不足一块的形状不能使用；权重只加载 2048/G 元素，不能据接口形式推定支持一般 D/G。D=2048 才与此权重加载长度直接一致；还需 G 整除 2048，group_size 及搬运/向量归约满足实现的块对齐要求。源码未给出完整可用 (D,G) 矩阵或通用尾块支持，本卡没有独立验证其他组合；新 shape 必须先补齐边界处理并对齐数值，不能只满足 D%G==0 就调用。

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
- 使能方式：环境变量 USE_CUSTOM_NORM_KERNEL="true" 只在非 Extend 路径分派到该算子；forward_mode.is_extend() 仍调用 self.norm，因此不将此融合收益外推到 Prefill/Extend。可选 `RMSNORMGATED_BLOCK_DIMS` 指定核数。
- 与 [recurrent-gated-delta-rule](recurrent_gated_delta_rule.md) 组合，实现 Decode GDN 路径的端到端融合；stage5 patch 中本算子仅由 qwen3_next.py 直接调用；ascend_backend.py 调用的是 recurrent_gated_delta_rule，应分别追踪。

## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/README.md)（primary）
- [torch_interface.cpp](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/ops/gated_delta_net/rmsnormgated/torch_interface.cpp)（supporting）
- [CustVec.h](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/ops/gated_delta_net/rmsnormgated/op_kernel/CustVec.h)（implementation）
- [0001-feat-support-GDN-and-rmsnormgated-fusion-ops.patch](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/patches/stage5/0001-feat-support-GDN-and-rmsnormgated-fusion-ops.patch)（implementation）

## Links

- [qwen3-next](../models/qwen3_next.md)
- [gated-deltanet](../modules/gated_deltanet.md)
- [recurrent-gated-delta-rule](recurrent_gated_delta_rule.md)
- [ascendc](../frameworks/ascendc.md)
- [atlas-a3](../platforms/atlas_a3.md)
- [mamba-ssm-train](../../../training/concepts/modules/mamba_ssm_train.md)（训练侧 Mamba2 SSM：mamba_mixer / SSD chunk 矩阵化 / SSM 上下文并行）
