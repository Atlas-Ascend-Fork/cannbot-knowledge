---
type: Guide
title: SGLang Ascend投机参数：Eagle、MTP、DSpark与DFlash启动约束
description: 对齐算法别名、draft宽度和并行守卫，区分NPU允许的路线、CUDA专属block verification和V4模型额外限制。
tags:
- task.implementation
- topic.speculative_decoding
- topic.parallelism
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/arg_groups/speculative_hook.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/arg_groups/deepseek_v4_hook.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/speculative/spec_utils.py
  role: implementation
created_at: '2026-11-08T12:08:02Z'
updated_at: '2026-11-09T04:32:54Z'
platforms: []
aliases:
- NEXTN EAGLE NPU
- DSpark gamma
- DFLASH block size
---

# SGLang Ascend投机参数：Eagle、MTP、DSpark与DFlash启动约束

## 算法与静态宽度

NEXTN归一为EAGLE；部分Gemma4配置可转FROZEN_KV_MTP，不能仅凭用户原字符串判断worker。Eagle默认最大running requests为48，某些模型用target自身checkpoint的nextn权重；是否保留mixed chunk由算法能力控制。

DFlash允许cuda/npu/xpu设备，要求PP=1且显式draft模型；num_steps与topk归一为1，以匹配共享buffer计数。block size必须正数，显式num_draft_tokens需与其一致，未显式时从配置或默认16推导；draft window不能小于block宽度。

DSpark允许NPU，num_steps/topk同样固定1。gamma为生成draft数量，verify宽度=gamma+1（含root），显式num_draft_tokens冲突时报错，verify宽至少2。draft checkpoint必须可解析为bundled draft、对应子目录或显式路径，不能把普通target当可用draft。默认running为48；graph对齐verify仅对compact ragged调度生效，static模式没有该效果。

## 并行、采样与平台守卫

DSpark的DP attention要求DP LM head，DP与CP>1仍拒绝。NPU豁免一些GPU MoE/静态ragged限制，不能由此推导所有DP/TP/CP组合都通过；PP>1只允许PD prefill等源码明确路线。V4配置另只允许EAGLE或DSPARK，Eagle topk=1；zigzag CP要求NPU。V4.1 的 validate_deepseek_v41_features 更严格：仅允许不启用投机或使用 DSPARK，且 PP 必须为1，包括 PD prefill，不能沿用通用 PP 例外。V4.1的encoder bounded replay及某些candidate/Engram能力有CUDA/AMD guard，不自动属于NPU。

block verification虽然接受Eagle/DFlash/DSpark等算法名，设备guard要求cuda（包含ROCm的torch设备语义），NPU明确拒绝。经典rejection flag只允许EAGLE/EAGLE3/NEXTN且topk1线性链；deterministic rejection另限CUDA兼容，阈值需满足对应规则。启用经典 rejection sampling 时，多层 EAGLE 同样要求线性 topk1；该守卫位于 speculative_use_rejection_sampling 分支内，不能外推为所有未启用此模式的多层 MTP 启动限制。

## 使用与验证

启动前记录“解析后的”算法、draft path、gamma/verify宽、steps、topk和并行域，再检查模型专属hook。文档中的通用支持项与当前代码guard可能不同，应保留各版本说明，不能删掉guard以套配方。建议对支持配置和应拒绝配置分别验收启动，再测prefill→draft→verify→接受后decode；本次未启动模型。平台字段不由设备类型泛化。

共享spec_utils对后续step的TopK选择在NPU关闭torch.compile；这保留普通PyTorch计算路径，不等于关闭全部模型图。
