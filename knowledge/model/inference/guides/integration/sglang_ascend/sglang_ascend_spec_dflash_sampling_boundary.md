---
type: Guide
title: SGLang Ascend DFlash采样边界：可用kernel与worker语义分离
description: 说明NPU为何显式禁用DFlash非greedy验证，及top-k/top-p归一化的native探测、回退和显存成本。
tags:
- task.implementation
- topic.speculative_decoding
- topic.precision
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/speculative/dflash_utils.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/kernels/ops/sampling/renorm.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/kernels/ops/speculative/verify_sampling.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/speculative/dflash_worker_v2.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/cookbook/autoregressive/Qwen/Qwen3.8-27B.mdx
  role: supporting
created_at: '2026-11-08T12:08:07Z'
updated_at: '2026-11-08T12:38:11Z'
platforms: []
aliases:
- is_dflash_sampling_verify_available
- DFLASH non-greedy NPU
---

# SGLang Ascend DFlash采样边界：可用kernel与worker语义分离

## 直接能力守卫

`_DFLASH_SAMPLING_VERIFY_AVAILABLE`要求tree_speculative_sampling_target_only存在且not is_npu()。因此即使NPU sample包提供相同原语，DFlash非greedy计算函数仍报unavailable；worker常规路径会记录warning并采用greedy argmax，不能保留用户请求的temperature/top-k/top-p采样分布。无损greedy应使用对应greedy请求配置，不能声称回退维持一般采样语义。

## 概率归一化不是验证能力

归一化先尝试导入的top_k/top_p helper；缺失时可探测torch_npu.npu_top_k_top_p。native helper要求输入是NPU tensor且接口存在，把概率log后过滤再softmax；top_k若不在[1,1024]时回退。通用top-k用最大请求k取topk、按每请求k mask再归一化，可能读取max().item()；top-p回退纯Torch排序归一化。不能因为这一步有NPU实现而取消DFlash验证守卫。

## 输出、内存与验证

支持设备上的非greedy verify要求candidate为[bs,width]，logits为[bs*width,vocab]且同device、bs/width正；随机矩阵与最终采样uniform尺寸也严格匹配。每step全词表target/draft概率可借graph pool临时空间，但accept buffer必须先于borrow scope创建并跨scope有效。NPU本版本不进入该非greedy验证路线。

logit调整、mask和每请求采样参数应在目标概率构造时正确传播；request.return_hidden_states与overlap等另有请求guard。验收应区分“归一化输出正确”“验证kernel可导入”“worker实际启用”“最终分布保真”四层，逐层记录结果。本次仅静态核对，没有执行概率统计、峰值显存或非greedy验证测试。

## Qwen3.8-27B DFlash2的上游A3比较协议

Cookbook把NPU无损verify明确限于greedy：temperature0/top_k1；非greedy警告后draft proposal和target verify均回退greedy，不保留请求分布。该页引用的Ascend比较是A3 BF16 target、TP2/ascend attention/SSM BF16/extra_buffer，baseline与DFlash2都disable-Radix以排除prefix warmup；DFlash2另加DFLASH、incoai/Qwen3.8-27B-DFlash2和draft tokens8。

质量协议为0-shot GSM8K、max-new2048、128例、并发1/2/4/8/16；它不是该页CUDA的1319题多cell sweep，亦未在这段给出可摄取的NPU分数或加速比。本次没有复测该PR。引用协议不能将本卡未知具体芯片的实现守卫扩大成所有芯片已测能力。

- [docs/cookbook/autoregressive/Qwen/Qwen3.8-27B.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/cookbook/autoregressive/Qwen/Qwen3.8-27B.mdx)（supporting）
