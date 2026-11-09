---
type: Guide
title: vLLM Ascend MXFP8 CEIL scale 与非交错 SwiGLU-OAI 接入
description: 核对3164 MiniMax M3 MXFP8的MAX_EXPONENT/CEIL枚举、硬件能力门禁、连续gate|up与swiglu_mode=2、量化scale布局；区分源码选择和实机验收。
aliases:
- DynamicMXQuantScaleAlg CEIL
- SWIGLUOAI_UNINTERLEAVE swiglu_mode=2
tags:
- task.implementation
- topic.model_adaptation
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/quantization/methods/w8a8/w8a8_mxfp8.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/quantization/utils.py
  role: implementation
created_at: '2026-11-03T06:28:46Z'
updated_at: '2026-11-03T06:28:46Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend MXFP8 CEIL scale 与非交错 SwiGLU-OAI 接入

固定增量 `ceac1a2→3164adc8fe75892fbf7f99f524bb72fddf1e6efd`，完整 unified diff 与上下文已读；不把增量阅读标为目标整文件FULL，没有执行上游、NPU、真实collective或性能验证。

`DynamicMXQuantScaleAlg` 为IntEnum：MAX_EXPONENT=0，CEIL=1。get_dynamic_mx_quant_scale_alg先看硬件DYNAMIC_MX_QUANT_SCALE_ALG_ONE，不具备则0；具备时再由forward/config中MiniMaxM3 architecture或model_type决定CEIL。CEIL先将amax映射目标FP8范围再向上取E8M0指数，与直接最大指数算法不同，不能凭MXFP8名字混用。

W8A8_MXFP8 MoE初始化缓存这项选择，在super已有融合激活之外，仅CEIL与SWIGLUOAI_UNINTERLEAVE组合声明额外支持。GMM1先产连续BF16 `[gate|up]`，再调用 `npu_swiglu_mx_quant`，activate_left=True、swiglu_mode=2，clamp_limit/glu_alpha/glu_bias来自MLP输入，最后归一化scale。mode1解释交替gate/up，会改变数学；此分支也不是将所有模型切到clipped activation。apply_act_quant同样复用初始化算法，forward metadata与scheme初始化须一致。

来源注释称该A5 MiniMax CEIL路径经验证，不是本次运行。适配应先检查真实activation和scale算法、gate/up排列、输出dtype、clamp参数，再比非融合参考与输出scale；图重放/模型reload后还需核对缓存配置是否仍匹配。旧[950 scale打包规则](../../optimizations/rules/950_mxfp8_moe_activation_scale_packed_layout.md)的历史证据与本版本的算法选择分开使用。
