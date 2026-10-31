---
type: Concept
title: MHC 训练（融合 Pre/Post 与 Triton Head）
description: 当前 MindSpeed-LLM MHC 的分阶段后端、融合算子布局、四路与迭代数约束、细粒度重计算及流水线边界。
tags:
- task.implementation
- topic.model_architecture
- topic.compilation
status: stable
sources:
- resource: cann-recipes-raw/mindspeed-llm/72b0cca64535371e0bbf178087b88448c392970b/mindspeed_llm/tasks/models/transformer/deepseek4/mhc.py
  role: primary
- resource: cann-recipes-raw/mindspeed-llm/72b0cca64535371e0bbf178087b88448c392970b/mindspeed_llm/ops/npu_mhc.py
  role: implementation
- resource: cann-recipes-raw/mindspeed-llm/72b0cca64535371e0bbf178087b88448c392970b/mindspeed_llm/features_manager/transformer/mhc_feature.py
  role: implementation
- resource: cann-recipes-raw/mindspeed-llm/72b0cca64535371e0bbf178087b88448c392970b/mindspeed_llm/ops/triton/mhc_pre_only.py
  role: implementation
- resource: cann-recipes-raw/mindspeed-llm/72b0cca64535371e0bbf178087b88448c392970b/examples/mcore/deepseek4_flash/pretrain_deepseek4_flash_4k_A3_ptd.sh
  role: implementation
created_at: '2026-06-30T00:00:00Z'
updated_at: '2026-10-29T13:33:23Z'
platforms:
- a3
---

# MHC 训练：融合 Pre/Post 与 Triton Head

## Summary

当前 MindSpeed-LLM DeepSeek4 MHC 将普通残差扩为多路，以 pre 权重收敛到子层输入，再将子层输出按 post 扩展，并与 comb 混合后的多路 residual 相加。当前实现位于 deepseek4/mhc.py：Pre/Post 由 --use-fused-mhc 选择 cann_ops_transformer，出口 Head 由 --use-triton-mhc 选择 Triton。旧 mhc/ 目录内完整 Triton Sinkhorn/BMM 的启动和文件引用已移除。

## 三类映射

hc_mult=4 时投影 mixes 的末维为 (2+hc_mult)×hc_mult=24，分为 pre/post/comb 的 4/4/16；Head 只有 4。pre=sigmoid(mixes_pre×scale+base)+eps，post=2×sigmoid(mixes_post×scale+base)，comb 是 4×4 的 Sinkhorn 归一混合矩阵。

当前 PyTorch 参考先对 comb 做 row-softmax 加 eps、列归一，再循环行/列归一。有限迭代与 eps 影响数值，不可用理想双随机矩阵等式代替实测。

## 当前配置与约束

--enable-mhc 开启结构；hc_mult 默认 4，hc_sinkhorn_iters 默认 20，hc_eps 默认 1e-6。启用融合 Pre/Post 时显式限制 hc_mult=4 且迭代次数=20。模型还要求 MLA、FlashAttention；CP 算法只接受 ulysses_cp_algo、kvallgather_cp_algo、deepseek_v4_cp_algo。

当前 DeepSeek4-Flash A3 样例同时开启 use-fused-mhc 与 use-triton-mhc，分别控制不同阶段，旧 use-triton-sinkhorn 已无该注册项。

## 融合 Pre/Post 的布局

模型使用 [S,B,HC,D]，融合 op 使用 [B,S,HC,D]。mhc_pre_sinkhorn_ascend 显式 permute/contiguous，调用 cann_ops_transformer.ops.mhc_pre_sinkhorn，取 h_in/h_post/h_res 后转换回模型轴顺序。

mhc_post_ascend 将当前子层输出、residual、post、comb 分别转换为 batch-first，调用 ops.mhc_post，再变回模型布局，并 make_viewless_tensor 保留 autograd，避免流水线释放激活时遇到 view。仅 reshape 不能代替 B/S 换轴。

算子包仅在启用融合功能时惰性导入，缺失时明确报 ImportError。融合 op 的反向由配套算子包负责，本页不再把已删除 Triton 全量 Sinkhorn kernel 当作当前 Pre/Post 的反向实现。

## Triton Head 与参数精度

Head 无需 post/comb；use_triton_mhc 时调用 MHCPreOnlyTriton，否则使用 PyTorch RMS 归一、线性投影、sigmoid 和四路加权和。模型对 hc_fn.weight、hc_base、hc_scale 保持 fp32；输出恢复输入 dtype。当前 Triton Head 与融合 Pre/Post 是混合使用，而不是所有阶段都由一个 Triton 开关控制。

## 重计算与流水线

mhc_recompute 使用 CheckpointWithoutOutput 管理融合 Pre/Post。Pre 需处于训练、启用融合、非 MTP；Post 还限于 attention 子层。fb-overlap 且未 recompute_csa_attention 时，Post 重计算输入会 clone 暂态 attention 输出，避免 hook 前被释放。旧 drop storage 的 MHCRecomputeInfo 使用方式不能继续套用。

MHCFeature 还调整 PP 激活形状，并在 VPP 配置下选择 MHC 的 interleaved schedule。验证应覆盖融合/参考前后向、所需 CP/PP、重计算及输出布局；本次只做静态复核。

## Evidence

- [mhc.py](../../../../../cann-recipes-raw/mindspeed-llm/72b0cca64535371e0bbf178087b88448c392970b/mindspeed_llm/tasks/models/transformer/deepseek4/mhc.py)（primary）
- [npu_mhc.py](../../../../../cann-recipes-raw/mindspeed-llm/72b0cca64535371e0bbf178087b88448c392970b/mindspeed_llm/ops/npu_mhc.py)（implementation）
- [mhc_feature.py](../../../../../cann-recipes-raw/mindspeed-llm/72b0cca64535371e0bbf178087b88448c392970b/mindspeed_llm/features_manager/transformer/mhc_feature.py)（implementation）
- [mhc_pre_only.py](../../../../../cann-recipes-raw/mindspeed-llm/72b0cca64535371e0bbf178087b88448c392970b/mindspeed_llm/ops/triton/mhc_pre_only.py)（implementation）
- [pretrain_deepseek4_flash_4k_A3_ptd.sh](../../../../../cann-recipes-raw/mindspeed-llm/72b0cca64535371e0bbf178087b88448c392970b/examples/mcore/deepseek4_flash/pretrain_deepseek4_flash_4k_A3_ptd.sh)（implementation）

## Links

- [推理 MHC 结构](../../../inference/concepts/modules/mhc.md)
- [推理 HcPre/HcPost](../../../inference/concepts/kernels/mhc_hcpre_hcpost.md)
- [Triton 后端](../frameworks/triton_on_ascend.md)
