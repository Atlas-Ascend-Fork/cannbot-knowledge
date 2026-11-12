---
type: Guide
title: SGLang Ascend GDN：卷积历史、chunk prefill与投机状态
description: 说明NPU Gated DeltaNet在decode/prefill/verify中的卷积run mode、门控dtype、分块状态写回和候选中间态。
tags:
- task.implementation
- topic.attention
- topic.speculative_decoding
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/ascend_gdn_backend.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/ascend_hybrid_linear_attn_backend.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/attention/linear/gdn_backend.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/attention/linear/kernels/gdn_triton.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/kernels/ops/attention/linear/gdn_replayssm_spec_decode.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/kernels/ops/attention/fla/layernorm_gated.py
  role: implementation
created_at: '2026-11-08T12:07:58Z'
updated_at: '2026-11-09T04:31:18Z'
platforms: []
aliases:
- AscendGDNAttnBackend
- GDN chunk64
---

# SGLang Ascend GDN：卷积历史、chunk prefill与投机状态

## 三阶段状态流

decode调用causal_conv1d run_mode1、activation1、pad_slot=-1，卷积权重转置后缓存；Q/K/V整理为[1,bs,heads,dim]，由kernel_dispatcher执行recurrent更新。每请求接受数和实际长度为1。draft_extend_v2跳过常规元数据重建，由对应draft流程提供。

普通prefill只从卷积池取最后kernel_size-1历史并contiguous，run_mode0后把更新后的历史写回。fused gate产生g/beta，Q/K先l2norm，再调native chunk_gated_delta_rule，chunk64、scale=Kdim^-0.5；返回最终状态按mamba slot scatter，跟踪前缀时从chunk中间h选择边界状态。不能把h的分块索引当请求slot。

## Target verify

verify卷积会处理完整draft宽并记录候选窗口；gating使用without_sigmoid变体，beta BF16而g FP32，native recurrent初始状态选择接受数1的既有slot，并把各候选步SSM写入intermediate buffer。graph使用预分配扩展mamba索引的说明仅适用于 topk<=1、非 ragged 的固定宽度 verify；topk>1 的 capture/replay 元数据不含 mamba_cache_indices_gdn，而 GDN verify 会直接读取并 view 该字段，不能据此认为树形 verify 已支持。该 Ascend hybrid 基类还明确拒绝 ragged verify。eager裁掉DP全局无效token后再补零输出。候选写入并不等于已经提交最终persistent状态。

接受结果由hybrid层执行中间SSM搬移和卷积rollback。拒绝后续token时，如果只改seq_len而没有恢复conv/state，下一轮会读到未接受token的历史；必须同时检查这两个状态族。

## 选择与验证

NPU注册要求hybrid GDN的full attention同样选ascend。共享Triton GDN dispatcher在NPU禁用packed decode，外部chunk内核不提供inplace_update=False，多item scoring该模式会抛错；不要把CUDA ReplaySSM融合verify直接迁移。

建议覆盖新请求/有历史、chunk64边界、不同请求长度、接受0/部分/全部候选与后续第二轮decode，比较SSM和conv双状态以及输出。native与融合路线可减少调用但有dtype/布局转换代价；本次仅阅读源码，没有状态或性能实测，具体芯片范围未确认。

输出门控norm包装在NPU替换为sgl_kernel_npu的layer_norm_fwd_npu：输入展平到二维、最后一维连续，weight/bias也contiguous，只接受swish。z可为原输入同shape或约定三维分组视图；norm_before_gate决定先norm还是先门控，不能在适配时交换。

## 配套知识

[分块GDN接口](../../../apis/sgl_kernel_npu/sgl_chunk_gated_delta_rule.md)。
