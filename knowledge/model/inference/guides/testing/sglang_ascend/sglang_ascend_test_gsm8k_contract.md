---
type: Guide
title: SGLang NPU精度测试的PR smoke、容差和重试口径
description: 区分NPUGSM8KMixin的单请求PR smoke与完整评测、0.99相对容差、默认最多3次尝试和EvalScope历史采样基线。
tags:
- task.testing
- topic.precision
- topic.model_serving
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/test/ascend/npu_eval_accuracy_kit.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/test/ascend/gsm8k_ascend_mixin.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/test/ascend/test_mmlu.py
  role: supporting
created_at: '2026-11-08T12:20:21Z'
updated_at: '2026-11-09T04:36:43Z'
platforms: []
---

# SGLang NPU精度测试的PR smoke、容差和重试口径

## 测试定义不是运行结果

NPUGSM8KMixin在GITHUB_EVENT_NAME=pull_request且workflow ref不含nightly-test-npu.yml时，只向/generate发送固定Paris问题、temperature0/max_new_tokens32，断言HTTP200与响应含Paris，然后返回。该PR成功不能宣称GSM8K数据集通过；nightly虽也可PR触发仍走完整评测。

完整模式优先gsm8k_score_threshold，NaN才用legacy gsm8k_accuracy_thres，乘0.99并缓存，避免重入重复放宽；这是相对1%而非减1个百分点。默认最多3次尝试，子类可限制。run_eval/sgl_eval委托父mixin，evalscope分支采用历史4-shot chat基线，默认temperature1、max_tokens7168、eval batch64、limit100000，保留最高accuracy达到阈值即停止。

旧GSM8KAscendMixin另一套默认200题、5-shot、max_tokens512、128线程，分别断言accuracy与output_throughput，且也在上述PR条件走smoke。它的历史env拼写及默认图禁用不能直接作为当前全局性能建议。

报告必须写明实际分支、样本数、prompt/grader、采样、阈值/放宽、尝试次数及全部得分，不能把best-of-retry当单次确定性结果；调整量化、图或MTP后应使用同一harness重评。[在线评测文档入口](/model/inference/guides/deployment/sglang_ascend/sglang_ascend_doc_accuracy_evaluation.md)提供操作背景。

本次仅静态读取测试实现，未发起请求、安装评测工具或运行数据集，未知芯片范围保持草稿。

## MMLU公共类的断言边界

TestMMLU默认128题、32线程，score严格大于accuracy_mmlu（缺省0）；latency与output_throughput只写summary，没有相应门槛断言。单一score检查不能扩成完整性能验收，具体模型还需检查子类配置。
