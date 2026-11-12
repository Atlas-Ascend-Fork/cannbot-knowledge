---
type: Guide
title: SGLang NPU推测解码回归与950原生block-FP8用例
description: 保留EAGLE3多卡、token map、dummy draft和950 NEXTN FP8草稿测试定义，区分草稿参数、实际启用和质量断言。
tags:
- task.testing
- topic.model_serving
- topic.precision
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/accuracy/models/test_npu_qwen36_block_fp8_gsm8k.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/speculative_inference/test_npu_basic_sanity_eagle3.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/speculative_inference/test_npu_eagle3.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/speculative_inference/test_npu_speculative_attention_mode.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/speculative_inference/test_npu_speculative_moe_a2a_backend.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/speculative_inference/test_npu_speculative_multi_npu.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/speculative_inference/test_npu_speculative_token_map.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/test/ascend/npu_eval_accuracy_kit.py
  role: constraint
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/test/ascend/gsm8k_ascend_mixin.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/test/simple_eval_mixed_prefix_gsm8k.py
  role: implementation
created_at: '2026-11-08T12:28:23Z'
updated_at: '2026-11-09T04:36:43Z'
platforms:
- a3
- '950'
---

# SGLang NPU推测解码回归与950原生block-FP8用例

## EAGLE与EAGLE3覆盖

本卡收集A3注册及明确950DT用例，没有执行。参数steps/topk/draft是分别的值，不等同接受长度或加速。相关算法实现由专门机制卡说明，这里只保存回归负载与断言。Basic EAGLE3、独立质量、MoE A2A、token map等表中数据集与质量目标适用于完整评测分支；当GITHUB_EVENT_NAME=pull_request且GITHUB_WORKFLOW_REF不含nightly-test-npu.yml时只执行Paris单请求smoke，不能据此宣称质量目标通过。PR触发的nightly仍走完整评测。

| 用例 | 配置 | 实际检查 |
|---|---|---|
| Basic EAGLE3 sanity | Qwen3-8B FP16，steps1/topk1/draft2，graph最大4、static0.7 | API/decode/scheduler stress mixin及GSM8K目标0.74；类有num_questions1400，实际mixin契约另核对 |
| EAGLE3独立质量 | Qwen3-8B BF16，4/1/5 unquant，禁图 | GSM8K配置num_questions上限1319；默认1319条数据先取5条demonstrations，实际1314条计分，目标0.81 |
| attention-mode/multicard | Qwen3-32B W8A8 TP4，decode 4/1/5 unquant | 完整评测GSM8K≥0.83，普通PR按上述条件仅smoke；docstring提prefill/decode但实际方法只有decode |
| MoE A2A | DeepSeek-R1 W8A8 TP16，target/draft fuseEP1 | GSM8K目标0.95；common args只有草稿步数类参数，无明确speculative-algorithm，不能只凭测试名声称已启用算法 |
| dummy draft | Qwen3-32B TP4，draft load-format dummy/revision main | server_info与Paris补全，不能作真实草稿质量基准 |
| token map | Qwen3-32B TP4 EAGLE3传不存在路径；Llama8B TP4 EAGLE传有效map | EAGLE3路径被忽略的质量目标0.83；EAGLE有效map目标0.75。其TP4设置不能用来消除文档TP1限制，需看当前实现 |

## 950DT Qwen3.6原生block-FP8

独立文件明确Ascend950DT，注册nightly-a5：Qwen3.6 block-FP8 checkpoint，TP2、NEXTN3/1/4，**draft quantization=fp8**。环境变量`SGLANG_NPU_ARCH35_REQUANT_BLOCK_FP8`默认0，区分原生block-FP8与重定量化MXFP8路径；模型/dataset均允许本地环境覆盖。

此配置与文档若只列draft unquant的配方不同，保留为版本内专用测试事实，不能合成“所有950 NEXTN草稿均支持FP8”。评测旧run_eval入口：1319个dataset条目中的前5作demonstrations，后1314计分，16线程、max4096/temp0、disable_thinking，assert accuracy≥0.90。没有运行结果时既不声称达到0.90，也不宣称FP8与MXFP8哪条更快。

比较草稿质量和性能须固定target/draft checkpoint、量化、graph、采样与接受率统计；服务器启动和非空输出属于更弱证据。

## Evidence

- [test/registered/accuracy/models/test_npu_qwen36_block_fp8_gsm8k.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/accuracy/models/test_npu_qwen36_block_fp8_gsm8k.py)（primary）
- [test/registered/npu/basic_function/speculative_inference/test_npu_basic_sanity_eagle3.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/speculative_inference/test_npu_basic_sanity_eagle3.py)（supporting）
- [test/registered/npu/basic_function/speculative_inference/test_npu_eagle3.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/speculative_inference/test_npu_eagle3.py)（supporting）
- [test/registered/npu/basic_function/speculative_inference/test_npu_speculative_attention_mode.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/speculative_inference/test_npu_speculative_attention_mode.py)（supporting）
- [test/registered/npu/basic_function/speculative_inference/test_npu_speculative_moe_a2a_backend.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/speculative_inference/test_npu_speculative_moe_a2a_backend.py)（supporting）
- [test/registered/npu/basic_function/speculative_inference/test_npu_speculative_multi_npu.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/speculative_inference/test_npu_speculative_multi_npu.py)（supporting）
- [test/registered/npu/basic_function/speculative_inference/test_npu_speculative_token_map.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/speculative_inference/test_npu_speculative_token_map.py)（supporting）
