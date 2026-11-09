---
type: Runbook
title: vLLM Ascend 双向Attention异常：causal标记与default mask分开核对
description: 在Pooling/encoder新模型适配中排查非因果Attention仍被上三角mask遮挡，区分标准FIA、310P显式mask与具体dtype表示。
tags:
- task.debugging
- topic.attention
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/attention_mask.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_attention_mask.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/attention/attention_mask.py
  role: implementation
created_at: '2026-10-29T11:32:34Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T11:41:26Z'
---

# vLLM Ascend 双向Attention异常：causal标记与default mask分开核对


## 触发与范围

新Pooling/双向模型中早期token无法看后续token、embedding偏离参考，shape和推理流程却无明显错误时，检查causal与mask是否一致。本卡依据固定ceac1a2b的标准AttentionMaskBuilder；来源未声明整项接口产品范围，保持draft，不将310P差异推导为其他平台不支持。本次无现场复现。

## 标记为非causal仍可能错误遮挡

标准get_attention_mask(causal=False,...)返回None。FIA即便sparse_mode=0，也会将传入mask作为defaultMask应用；因此不能只关闭causal开关、却继续把上三角mask传入双向Attention。另查实际后端有没有自行添加mask，不能仅看模型config。

310P builder使用其算子要求的显式non-masking mask，是独立接口；None和全可见mask是否等价需按当前算子核对，不能跨backend照搬。

## 因果路径与dtype

标准causal pooling使用按长度缓存的bool上三角mask；普通splitfuse路径使用2048×2048的int8上三角。_generate_attn_mask在FP16时以-inf标遮挡，其他dtype使用1。不同表示不是可任意互换的数值张量，核对实际consumer期待的dtype/语义与缓存复用，不把一次to(dtype)视为所有mask协议的转换证明。

## 探针与验收

保存attn_type、causal、所选backend、实际mask形态/dtype/值以及sparse_mode；用未来token内容改变后早期token是否响应的受控输入，与可信双向参考对照。分别覆盖causal、noncausal、pooling、不同长度和相邻请求，排除padding及request边界错误。

修复构造/消费两侧的一致性；不要简单去掉所有模型的mask，因果模型仍必须禁止看未来。源UT断言FP16上三角-inf及缓存形状，未覆盖所有非causal/310P/图组合，也未由本次执行。数值通过后再测优化，失败回到已验证backend与mask协议。


## 310P例外的具体构造

310P实现仅在pooling分支依据causal选择；非pooling入口仍返回因果mask。pooling的noncausal mask是model dtype的全零矩阵，经nd_to_nz_2d和FRACTAL_NZ格式转换，不是标准FIA的None。是否支持压缩mask还同时检查_npu_flash_attention_v3与_npu_paged_attention_splitfuse_v2；不能只看其中一个符号。其docstring仍写pooling会抛NotImplementedError，与当前实际分支不符，应以这次固定实现为准，且仍需实际模型验收。
