---
type: Guide
title: SGLang NPU语言模型回归配方与GSM8K目标矩阵
description: 汇总A2/A3注册及Gemma4手工语言测试的并行、量化和质量目标，保留CP停用注释及继承参数边界。
tags:
- task.testing
- topic.model_serving
- topic.precision
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/llm_models/test_npu_gemma_4_26b_a4b_it_llm.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/llm_models/test_npu_gemma_4_31b_llm.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/llm_models/test_npu_gemma_4_e2b_llm.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/llm_models/test_npu_gemma_4_e4b_llm.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_ascend_minimax_m2.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_ascend_trinity_mini.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_afm_4_5b.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_deepseek_v3_2_exp_w8a8.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_gemma_3_4b_it_llm.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_ling_lite.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_llama4_scount_17b_16e.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_mimo_7b_rl.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_phi_4_multimodal_llm.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_qwen3_0_6b.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_qwen3_1_7b_gptq_int8.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_qwen3_235b_a22b_w8a8.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_qwen3_30b.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_qwen3_30b_attn_cp.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_qwen3_30b_fuseep.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_qwen3_30b_w4a4.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_qwen3_32b.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_qwen3_8b_communications_quantization.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_qwen3_coder_480b_a35b.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_qwq_32b_w8a8.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/test_ascend_deepseek_mtp.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/test_ascend_w8a8_quantization.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/test_mindspore_models.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/test/ascend/gsm8k_ascend_mixin.py
  role: implementation
created_at: '2026-11-08T12:28:23Z'
updated_at: '2026-11-09T04:36:38Z'
platforms:
- a2
- a3
---

# SGLang NPU语言模型回归配方与GSM8K目标矩阵

## 使用这些目标的前提

这些是固定提交中的测试定义，没有运行记录。注册suite说明计划运行的平台：大多数nightly/full A3，Qwen1.7B GPTQ INT8、Qwen30B W4A4另注册A2；不能据此认定所有模型在两平台均通过。以下accuracy是子类声明的目标，实际数据量、PR smoke替换和容差按[共同GSM8K契约](sglang_ascend_test_gsm8k_contract.md)。未覆写参数的模型继承基类，不补写想象的TP或图设置。

| 模型/权重形式 | GSM8K目标 | 测试覆写的关键条件 |
|---|---:|---|
| MiniMax-M2 BF16 | 0.90 | TP8，禁图、Radix和overlap |
| Trinity-Mini | 0.85 | TP2，禁图、Radix和overlap，context4096，专用chat template |
| AFM-4.5B Base | 0.375 | 继承默认启动参数 |
| DeepSeek-V3.2-Exp W8A8 | 0.50 | TP16、ModelSlim，禁图与Radix |
| Gemma3-4B-IT | 0.70 | 禁图、Radix，chunk=-1 |
| Ling-Lite | 0.75 | TP2，禁图 |
| Llama4-Scout-17B-16E | 0.90 | TP4、Llama4模板，context8192，禁图与Radix |
| MiMo-7B-RL / Phi4-multimodal语言模式 | 0.75 / 0.80 | 继承默认参数；这里不是视觉精度验证 |
| Qwen3-0.6B | 0.38 | chunk256，禁图 |
| Qwen3-1.7B GPTQ INT8 | 0.65 | quantization=gptq；A2注册 |
| Qwen3-235B-A22B W8A8 | 0.955 | TP8、ModelSlim，禁图 |
| Qwen3-30B | 0.90 | TP2，禁图，static0.7，max-running32 |
| Qwen3-30B attention CP | 0.92 | TP4、MoE-DP2、CP2、FIA，100题/5shot；子类声明gsm8k_parallel=32但当前入口未消费，解除skip后的完整评测固定128线程；该测试已disabled |
| Qwen3-30B W8A8 FuseEP | 0.90 | TP4、fuseEP2、graph最大128；A3注册 |
| Qwen3-30B W4A4 LAOS | 0.85 | TP2；A2注册 |
| Qwen3-32B | 0.86 | TP4，禁图 |
| Qwen3-8B通信量化 | 0.85 | TP2，enable-quant-communications，不强制禁图 |
| Qwen3-Coder-480B-A35B W8A8 QuaRot | 0.94 | TP16、ModelSlim，禁图 |
| QwQ-32B W8A8 | 0.59 | TP2、ModelSlim，禁图 |

CP服务器的 max-running-requests=32 与客户端评测线程数不同，GSM8KAscendMixin.test_gsm8k 实际传 num_threads=128。CP测试的disabled注释声称HIP/NPU/MUSA PCP deprecated，只能说明该用例停用及注释。当前平台验证实现的NPU边界不能由注释推导；尤其不能将本条改写成“NPU全局禁止PCP”。

## Gemma4手工回归

手工Gemma4语言模式统一禁图、static0.7：26B-A4B-IT目标0.35/TP2，31B目标0.70/TP2，E2B目标0.05/TP1，E4B目标0.60/TP1。这些文件没有明确芯片产品注册，不把A3 suite范围借给它们。对应视觉模式有不同MMMU目标，见[视觉配方](sglang_ascend_doc_validation_vlm_matrix.md)。目标很低的smoke门槛不能解释为模型完整能力或已测准确率。

## 其它手工回归与性能字段

DeepSeek-R1-0528 W8A8手工MTP使用TP16/attention-DP2、NEXTN1/topk1/draft2、chunk32768、static0.8、disable-Radix，MLAPO及overlap-plan-stream开；GSM8K1319题/5shot/max512/parallel128目标0.95。矩阵latency1000和output_throughput6没有被assert。

Qwen2.5-0.5B W8A8手工测试禁图，GSM8K200题/5shot/max512/parallel128要求accuracy≥0.25且输出吞吐≥1000；另单请求名义256tokens/墙钟计吞吐，仅CI要求≥25，但未核对实际输出token数。两种吞吐口径不能相互替代。

MindSpore Qwen3-8B显式device=npu/model-impl=mindspore、TP1/DP1/static0.8，GSM8K200题/5shot/max512/parallel128要求accuracy>0.78。这三份手工文件都没有产品型号注册，不能借A3 suite宣称已在A3验证。

复现时记录checkpoint、继承后的实际启动参数、dataset、PR/nightly分支与分数；模型列表和阈值都不是实测收益。

## Evidence

- [test/manual/ascend/llm_models/test_npu_gemma_4_26b_a4b_it_llm.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/llm_models/test_npu_gemma_4_26b_a4b_it_llm.py)（primary）
- [test/manual/ascend/llm_models/test_npu_gemma_4_31b_llm.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/llm_models/test_npu_gemma_4_31b_llm.py)（supporting）
- [test/manual/ascend/llm_models/test_npu_gemma_4_e2b_llm.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/llm_models/test_npu_gemma_4_e2b_llm.py)（supporting）
- [test/manual/ascend/llm_models/test_npu_gemma_4_e4b_llm.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/llm_models/test_npu_gemma_4_e4b_llm.py)（supporting）
- [test/registered/npu/llm_models/test_ascend_minimax_m2.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_ascend_minimax_m2.py)（supporting）
- [test/registered/npu/llm_models/test_ascend_trinity_mini.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_ascend_trinity_mini.py)（supporting）
- [test/registered/npu/llm_models/test_npu_afm_4_5b.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_afm_4_5b.py)（supporting）
- [test/registered/npu/llm_models/test_npu_deepseek_v3_2_exp_w8a8.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_deepseek_v3_2_exp_w8a8.py)（supporting）
- [test/registered/npu/llm_models/test_npu_gemma_3_4b_it_llm.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_gemma_3_4b_it_llm.py)（supporting）
- [test/registered/npu/llm_models/test_npu_ling_lite.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_ling_lite.py)（supporting）
- [test/registered/npu/llm_models/test_npu_llama4_scount_17b_16e.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_llama4_scount_17b_16e.py)（supporting）
- [test/registered/npu/llm_models/test_npu_mimo_7b_rl.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_mimo_7b_rl.py)（supporting）
- [test/registered/npu/llm_models/test_npu_phi_4_multimodal_llm.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_phi_4_multimodal_llm.py)（supporting）
- [test/registered/npu/llm_models/test_npu_qwen3_0_6b.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_qwen3_0_6b.py)（supporting）
- [test/registered/npu/llm_models/test_npu_qwen3_1_7b_gptq_int8.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_qwen3_1_7b_gptq_int8.py)（supporting）
- [test/registered/npu/llm_models/test_npu_qwen3_235b_a22b_w8a8.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_qwen3_235b_a22b_w8a8.py)（supporting）
- [test/registered/npu/llm_models/test_npu_qwen3_30b.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_qwen3_30b.py)（supporting）
- [test/registered/npu/llm_models/test_npu_qwen3_30b_attn_cp.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_qwen3_30b_attn_cp.py)（supporting）
- [test/registered/npu/llm_models/test_npu_qwen3_30b_fuseep.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_qwen3_30b_fuseep.py)（supporting）
- [test/registered/npu/llm_models/test_npu_qwen3_30b_w4a4.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_qwen3_30b_w4a4.py)（supporting）
- [test/registered/npu/llm_models/test_npu_qwen3_32b.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_qwen3_32b.py)（supporting）
- [test/registered/npu/llm_models/test_npu_qwen3_8b_communications_quantization.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_qwen3_8b_communications_quantization.py)（supporting）
- [test/registered/npu/llm_models/test_npu_qwen3_coder_480b_a35b.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_qwen3_coder_480b_a35b.py)（supporting）
- [test/registered/npu/llm_models/test_npu_qwq_32b_w8a8.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/llm_models/test_npu_qwq_32b_w8a8.py)（supporting）
- [test/manual/ascend/test_ascend_deepseek_mtp.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/test_ascend_deepseek_mtp.py)（supporting）
- [test/manual/ascend/test_ascend_w8a8_quantization.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/test_ascend_w8a8_quantization.py)（supporting）
- [test/manual/ascend/test_mindspore_models.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/test_mindspore_models.py)（supporting）
