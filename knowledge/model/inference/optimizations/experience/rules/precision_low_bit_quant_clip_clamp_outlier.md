---
type: Optimization
title: 低比特 (W4A8) 权重/激活量化用 clip/clamp 抑制离群值保精度
description: 把权重从 8bit 降到 4bit（W4A8）时精度掉得比 W8A8 明显——根因是 4bit 值域窄、更易被离群值主导：少数大值撑大量化 scale、压垮多数值的有效位宽。想到「W4A8 直接量化不无损、要先处理离群值」时，clip/clamp（收窄量化幅值）是第一手段。它作用在两个位置：权重侧（量化前削波）和 MoE 专家中间激活侧（两段 GMM 之间 requant 前削波）。W8A8 通常可不 clip（见 precision-quant-convert-model-config-pitfalls）；离群值也可用 Hadamard 正交旋转摊平（attention q/k，见 precision-lightning-indexer-low-bit-quant）。
tags:
- task.optimization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/464
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/13
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/12
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/410
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 低比特 (W4A8) 权重/激活量化用 clip/clamp 抑制离群值保精度

## 适用场景

把权重从 8bit 降到 4bit（[W4A8](../../../concepts/quantization/w4a8c8.md)）时精度掉得比 W8A8 明显——根因是 4bit 值域窄、更易被**离群值**主导：少数大值撑大量化 scale、压垮多数值的有效位宽。想到「W4A8 直接量化不无损、要先处理离群值」时，clip/clamp（收窄量化幅值）是第一手段。它作用在两个位置：**权重侧**（量化前削波）和 **MoE 专家中间激活侧**（两段 GMM 之间 requant 前削波）。W8A8 通常可不 clip（见 [precision-quant-convert-model-config-pitfalls](precision_quant_convert_model_config_pitfalls.md)）；离群值也可用 Hadamard 正交旋转摊平（attention q/k，见 [precision-lightning-indexer-low-bit-quant](precision_lightning_indexer_low_bit_quant.md)）。

## 手段 1：权重侧削波幅值——逐通道 MSE 网格搜索 + 外部学习 clip 因子

不用裸 abs_max 定 scale（对离群值敏感），改用逐通道最小化量化重构 MSE 的网格搜索选削波幅值（INT4 专用）：

```python
end_ratio = 1.3; start_ratio = 0.7; step = 0.01
qmax = 2 ** (4 - 1) - 1                       # =7，对称 int4 值域 [-7,7]
for i in range(max_size):
    max_candidates = (start_ratio + i * step) * max_val
    qx = x.clamp(-max_candidates, max_candidates).mul(1.0/(max_candidates/qmax)).round().mul(max_candidates/qmax)
    current_loss = (x - qx).pow(2).sum(dim=1, keepdim=True)   # 逐通道 MSE
    # 取 loss 最小的 max_candidates → scales = tmp_val / qmax
```

并支持外部**逐层 clip 因子**（离线学习得到、随权重加载）做非对称削波：对 `tensor.min/max` 分别乘 `clip_factor[0]`/`clip_factor[1]` 后 `clamp`，比旧的「对称标量乘 abs_max」更贴合分布。学习算法本体（如何学 Clamp）不在部署仓内、只加载其产物——下游复用此路径须拿到对应的已学 clip 系数。该削波在 `bits==4` 分支之前，对 INT8 与 INT4 路径都生效。

## 手段 2：MoE 专家中间激活侧——clip-before-dynamic_quant 融合算子

MoE 专家 FFN 的中间量（第一段 grouped-matmul 输出经 swiglu 后）要再动态量化喂第二段 GMM，直接 requant 会损失精度。用带 clip 的融合算子把「swiglu + clip + 动态量化」并成一步、**clip 在 dynamic_quant 之前**：

```python
# W4A8：npu_swiglu_clip_quant(mm1_mm3, expert_tokens, alpha, activate_left=True, quant_mode=1, clamp_mode=1)
#   alpha = 每专家一个 float 裁剪因子（torch.ones(num_experts) 初始化）
# 对照 W8A8：npu_dequant_swiglu_quant（dequant+swiglu+quant，无 clip、无 per-expert alpha）
```

W4A8-int4 变体用 `npu_dequant_swiglu_clamp_quant` 一步做 dequant+swiglu+clip+动态 requant，clamp 可选——仅当模型侧传入 `swiglu_limit` 时才装 `swiglu_mode=1, clamp_limit=swiglu_limit` 参数：

```python
if swiglu_limit:
    swiglu_limit_args = {"swiglu_mode": 1, "clamp_limit": swiglu_limit, "glu_alpha": 1, "glu_bias": 0}
intermediate_h, pertoken_scale = torch_npu.npu_dequant_swiglu_clamp_quant(
    mm1_mm3, quant_scale=self.experts.smooth_scale_2, group_index=expert_tokens,
    activate_left=True, quant_mode=1, **swiglu_limit_args)
```

W4A8 与 W8A8 的差异关键点 = **clip-before-dynamic_quant + per-expert alpha**。

## 效果（据实层级）

- 权重侧 MSE 搜索 / 外部 clip 因子、激活侧 clip：源码注释均声明 clip 用于「提升量化精度」（enhance quantization accuracy），但**幅度未给独立 before→after 数字**——手段有据、幅度未验，不写「误差越小」类单调律。
- 配上学习 Clamp 后，DeepSeek-V3.2-Exp W4A8C8 实测与 BF16 近乎无损、且在 GPQA/DROP/MGSM 上不低于 W8A8C8（doc 披露、仓自报，精度表见 [benchmark-deepseek-v32-quant-accuracy](../benchmark_observations/benchmark_deepseek_v32_quant_accuracy.md)）。

## 参考实现及其约束

- 手段 1 权重 MSE 搜索 / 外部 clip 参考实现：cann-recipes-infer 的 [DeepSeek-V4](../../../concepts/models/deepseek_v4.md) `convert_model.py`（`per_channel_searching` / `int_weight_quant` / `load_clip_params`）。
- 手段 1 学习 Clamp + 手段 2 MoE GMM clip 参考实现：cann-recipes-infer 的 DeepSeek-V3.2-Exp（compressed-tensors W4A8 MoE GMM）与 DeepSeek-V4（`experts_w4a8int4`）。
- 边界：`[0.7,1.3]`/step 0.01、qmax=7、`activate_left=True`/`quant_mode=1` 等是这些参考实现的调用约定；「低比特量化用 clip/clamp 抑制离群值、激活侧 clip 放在 requant 之前」的判断可迁移到同结构、同量化方案（W4A8 权重 + MoE GMM）的其它模型，不外推为通用量化定律。

## Evidence

- diff 事实（@dce3a777）：`per_channel_searching` MSE 网格、`int_weight_quant` 非对称 clip 分支、`load_clip_params`。溯源下探 [cann-recipes-infer-pr-464-add-w4a8-int-for-deepseekv4-pro](https://gitcode.com/cann/cann-recipes-infer/merge_requests/464)
- diff 事实 + doc 披露（@8c6c58b36bac）：clip 系数加载 + `activation_use_clip`、「基于学习的 Clamp」段落 + 精度表。溯源下探 [cann-recipes-infer-pr-13-feat-add-deepseek-v3-2-exp-w4a8c8-quantization-support](https://gitcode.com/cann/cann-recipes-infer/merge_requests/13)
- diff 事实 + 源码注释（@47228911d04d）：W4A8 `npu_swiglu_clip_quant` + per-expert alpha 对照 W8A8 `npu_dequant_swiglu_quant`；「提升精度」为注释意图、无量化收益。溯源下探 [cann-recipes-infer-pr-12-feat-support-moe-gmm-w4a8](https://gitcode.com/cann/cann-recipes-infer/merge_requests/12)
- diff 事实 + 源码注释（@6857a2062f66）：`experts_w4a8int4` 的 `npu_dequant_swiglu_clamp_quant` + `swiglu_limit` 门控 clamp。溯源下探 [cann-recipes-infer-pr-410-feat-w4a8int4](https://gitcode.com/cann/cann-recipes-infer/merge_requests/410)

<!-- cannbot:related:start -->
## 相关

- [DSA/MLA+MoE 量化转换 (convert_model.py) 的选择性层布局·clip 开关·MTP 分片导出陷阱](precision_quant_convert_model_config_pitfalls.md)（`related`）：W8A8 通常可不 clip（见 ［precision-quant-convert-model-config-pitfalls］(precision_quant_convert_model_config_pitfalls.md)）；离群值也可用 Hadamard 正交旋转摊平（attention q/k，见 ［precision-lightning-indexer-low-bit-quant］(precision_lightning_indexer_low_bit_quant.md)）。；clip 关闭走标准 per-channel 对称 abs-max int8 量化；clip 开启则从 `quant_param_path` 载入学到的 clip 因子收窄量化范围（`if c8 and clip: assert quant_param_path is not None`）。。离群值卡说明 W4A8 的 clip 机制，转换卡给出 W8A8 的开关与参数包行为，联合用于选择转换配置。
<!-- cannbot:related:end -->
