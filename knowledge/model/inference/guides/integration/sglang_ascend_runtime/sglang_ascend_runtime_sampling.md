---
type: Guide
title: SGLang Ascend采样的融合TopK守卫与确定性路径
description: 说明Ascend从温度缩放logits采样、TopK1到1024融合资格、排序回退、min-p、logprob及种子采样编译禁用边界。
tags:
- task.implementation
- topic.model_serving
- topic.performance.analysis
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/sampler.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/sampling/sampling_batch_info.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/sampling/penaltylib/repetition_penalty.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/managers/scheduler.py
  role: supporting
created_at: '2026-11-08T12:07:26Z'
updated_at: '2026-11-09T04:33:25Z'
platforms: []
aliases:
- npu_top_k_top_p_eligible
- top_k_top_p_min_p_sampling_from_logits_ascend
---

# SGLang Ascend采样的融合TopK守卫与确定性路径

Sampler 先处理 is_all_greedy：全部请求 top_k<=1 时直接 argmax，logprob 取未温度缩放 logits 的 log_softmax，不进入 Ascend 的融合/seed 采样流程。只有非全贪心 batch 才按 sampling_backend==ascend 选择以下路径；TopK=1 在混合 batch 中仍可随该路径处理。_forward_ascend_backend先原地除temperature，再从logits采样；需要返回logprob且未要求原始logprob时另算log_softmax。无过滤的simple case仍执行softmax+multinomial，不保证所有请求都用融合算子。

只有torch_npu存在npu_top_k_top_p且Host侧npu_top_k_top_p_eligible为真才调用融合TopK/TopP；其TopK合法范围为1..1024，资格在Host缓存避免逐token设备标量同步。融合后 softmax；但固定快照的 need_min_p_sampling 分支将 max(dim=-1) 返回的 values/indices 组合直接乘 min_ps，未取 values，存在类型运算失败的静态缺陷，不能视为已实现正常 min-p 过滤（本次未运行故障复现）。排序回退则通过 probs_sort[:,0] 取得最大概率计算 min-p 阈值。无该缺陷触发时，有seed用float64 log概率的multinomial_with_seed，否则torch.multinomial。

回退先softmax并降序sort，TOP_K_ALL改成词表宽度，按rank与累积概率减当前值实现top-k/top-p遮罩，再min-p，最后将抽样排序索引映回token。不能把融合资格失败当不支持采样，也不能以默认排序回退声称与所有硬件版本逐位一致。

带seed路径使用seed与position哈希的Gumbel方案，float64降低数值不稳定；其torch.compile在NPU显式disable，repetition scaling helper也禁用compile。确定性需要同时检查各rank logits、种子、position及kernel；TP token同步默认可省，但grammar始终请求同步，world_size1不创建多余collective。

验收覆盖TopK=1/1024/超范围/ALL、top-p边界、min-p、seed、过滤后支持集、logprob和TP一致性；测量CPU准备、排序、融合task与整体TPOT。本文未把源码可达性当成统计分布或模型精度验收。

## 请求能力边界

Host资格要求batch每条请求top_k均在1..1024；合并batch用逻辑AND保守保留资格。Scheduler对ascend sampling_backend的return_sampling_mask明确拒绝，因为这一路从logits采样且不构造可返回的完整支持集；存在TopK融合算子不能推出支持该API。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
