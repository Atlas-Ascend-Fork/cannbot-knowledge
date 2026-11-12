---
type: Guide
title: SGLang NPU并行与缓存参数的解析次序和组合守卫
description: 说明平台默认后仍需按模型/CP/PD/HiCache验证组合，保留CP整除、DCP传输白名单、Host接收与布局自动转换不完整的边界。
tags:
- task.implementation
- topic.parallelism
- topic.model_serving
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/arg_groups/parallel_hook.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/arg_groups/pd_disaggregation_hook.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/arg_groups/hicache_hook.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/arg_groups/pipeline.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/layer_boundary/adapters/attention.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/arg_groups/choices.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/arg_groups/fields/device.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/arg_groups/fields/exec_.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/arg_groups/fields/lora.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/arg_groups/fields/mm.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/arg_groups/fields/schedule.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/arg_groups/fields/spec.py
  role: supporting
created_at: '2026-11-08T12:20:20Z'
updated_at: '2026-11-08T12:27:46Z'
platforms: []
---

# SGLang NPU并行与缓存参数的解析次序和组合守卫

平台默认不是最终可运行参数。解析管线继续经过模型、并行、内存、MoE、投机等hook；ascend_ops draft决议在speculative hook之后才能看到最终算法。需要保存最终resolved视图，不能只看用户输入和help默认值。

CP先经registry run_hook验证平台，允许受控OOT替换；attention CP>1要求TP可整除CP及attn_dp_size×CP，MoE DP>1还限制EP×MoEDP与TP且PP==1。attn_cp_size不等moe_dp_size时后者只能1。sharded padded CP KV与unified memory明确互斥；不是所有CP等价于文档某处的CP=TP。

模型条件独立生效：DeepSeekV3.2 prefill CP拒绝zigzag；MiMoV2/Flash只zigzag且多模态需language-only。PD decode DCP>1传输白名单含ascend，但这里只是入口许可，具体Ascend KV几何和P/D拓扑仍按传输实现校验；fake只用于不搬KV的合成benchmark。

decode_host_receive_threshold必须0..1，小于1不兼容HiSparse/role switch，要求Host pool retraction并拒绝cpu_tensor备份。HiCache存储npu_memcache不支持layer_first时，兼容resolver仅把direct换page_first_direct、kernel换page_first；kernel_ascend分支保留原布局，日志写switching也可能没有实际变更，须由调用方选正确Ascend布局。

逐项验证resolved参数、池组装、通信分组和目标请求，组合报错不能仅靠删除断言规避。调优时一次改变一个并行/缓存因素，保留可运行基线并复测精度与显存。

## 旧注释与实际PCP门控

当前validate_prefill_cp_platform仅在enable_prefill_cp且platform.is_musa时拒绝；函数docstring或旧测试停用注释不能推出NPU全局拒绝。NPU具体CP路线仍要通过模型、布局及后端守卫。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。

## Attention输入分散的真实条件

AttnTpContext允许NPU input-scattered，但要求已配置、q_lora_rank非None、MHC或非DSA、非Prefill TC_PIECEWISE、非EAGLE3。实际use还要求extend、非target_verify、有input_ids且非TBO。已预gather的AttentionInputs不会再次gather；不能把开启开关等同所有模式都减少通信。
