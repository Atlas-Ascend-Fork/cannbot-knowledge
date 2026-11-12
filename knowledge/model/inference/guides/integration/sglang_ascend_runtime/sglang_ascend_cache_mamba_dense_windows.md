---
type: Guide
title: SGLang NPU Mamba状态布局与投机卷积窗口预算
description: 说明NPU禁用CUDA envelope与重叠窗口去重、KDA窗口轴交换、dense draft中间态的字节开销和清拷贝融合守卫。
tags:
- task.implementation
- topic.memory
- topic.speculative_decoding
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/mem_cache/memory_pool.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/memory_pool_npu.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/arg_groups/mamba_hook.py
  role: supporting
created_at: '2026-11-08T12:20:19Z'
updated_at: '2026-11-08T12:27:46Z'
platforms: []
---

# SGLang NPU Mamba状态布局与投机卷积窗口预算

Mamba池的CUDA envelope_layout明确assert排除NPU，不能把统一byte envelope的省显存模式不加条件套用NPU。普通conv分配后经_init_npu_conv_state转换为后端所需布局；temporal_state独立分配，实际dtype与shape由cache_params决定。

conv_window_dedup_enabled要求非NPU、非CPU、非KDA且线性draft链topk<=1。CUDA连续draft窗口可用重叠as_strided共享列，把D×(K-1)变成D+K-2；NPU保留逐draft dense窗口，因为后端kernel要求连续step，KDA还会转置，重叠view可能污染写入。

dense intermediate conv形状为[num_mamba_layers,spec_state_size+1,draft_tokens,conv_dim0,conv_dim1]，KDA在NPU交换原conv的两轴。字节预算为这些维度乘conv_dtype.itemsize，不能用GPU去重公式。SSM中间态另按[layer,slot,draft,HV,V,K]和ssm dtype计，ReplaySSM开关存在也不证明其各平台消费路径已支持。

_conv_fuse_ok显式排除NPU，CUDA bf16连续conv才走clear/copy融合；其余走逐Tensor逻辑，不能以Tensor.is_cuda别名绕过。状态恢复精度还需按[混合线性注意力精度线索](/model/inference/runbooks/precision/precision_mamba_gdn_linear_attention.md)核对所用版本，不把历史缓解参数视为本提交根治。

验收比较draft数、slot数和层数增长时的HBM开销，覆盖KDA/普通GDN、图padding、树verify与状态清除/恢复；KV主池预算之外需保留这些状态与临时staging。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
