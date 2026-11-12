---
type: Guide
title: SGLang Ascend原生SDPA回退：GQA、SWA与交叉注意力
description: 说明逐请求PyTorch注意力参考路径的KV读取、SWA因果对齐和logit cap，及主机同步与吞吐代价。
tags:
- task.implementation
- topic.attention
- topic.precision
- topic.kv_cache
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/ascend_torch_native_backend.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/ascend_backend.py
  role: implementation
created_at: '2026-11-08T12:07:59Z'
updated_at: '2026-11-09T04:31:18Z'
platforms: []
aliases:
- run_sdpa_forward_extend
- run_sdpa_forward_decode
---

# SGLang Ascend原生SDPA回退：GQA、SWA与交叉注意力

## 何时采用

普通非 MLA extend 先按 use_fia/use_fa 等条件进入 FIA/FA 分支；只有避开这些分支后，qlens 快路要求 head_dim<=128、causal、encoder_lens=None、logit_cap=0 且未启用 use_native_sdpa，否则才选择原生 SDPA（含特定 Gemma2 精度开关）。decode 先处理图路径及其他专门分支；普通 eager 分支仅在 encoder_lens 非空或 logit_cap 非零时选择原生 SDPA，不检查 Gemma2 的 use_native_sdpa 标志。因此 cross attention/精度特例并非所有阶段和模式的无条件回退触发器。该类support_triton=False，按请求Python循环并读取长度标量，会产生主机同步；这是兼容/精度回退，不是融合attention吞吐路径。

GQA通过重复K/V head对齐Q，K/V转换到Q dtype；logit cap可按tanh方式实施。encoder长度和decoder长度分离，cross attention从encoder cache取KV，不能照搬自回归SWA裁剪Q的规则。

## SWA与缓存索引

SWA使用full req_to_token地址时，必须先应用full_to_swa_mapping，再索引实际SWA buffer。decode保留从end-(window+1)起的有效KV。extend窗口以chunk第一个query的prefix为锚；为对齐全局因果mask可增加冗余query后再提取真实query行，不能简单对每个chunk先裁KV再使用原mask。

## 检查与代价

先确认每请求prefix/extend/encoder长度，再核对full/SWA地址映射、head重复比例和qk/v维。建议比较短窗口、多token chunk、cross attention无新K/V、GQA和logit cap输出，作为融合路径的对照。逐请求循环、重复head和临时attention张量可明显增加延迟/内存，应在核实精度问题后选择是否保留回退。本次没有运行对照，未给出具体芯片支持范围。
