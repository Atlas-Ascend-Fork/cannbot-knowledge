---
type: Guide
title: SGLang昇腾手工大模型量化与草稿预取测试配方
description: 保留DeepSeek MLA C8、GLM草稿预取、Kimi K3双机及MiMo DFLASH/多层EAGLE手工测试的精确配置和证据边界。
tags:
- task.testing
- topic.model_serving
- topic.precision
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/llm_models/test_npu_deepseek_v3_modelslim_mla_fp8.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/llm_models/test_npu_glm_5_1_w4a8_draft_prefetch.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/llm_models/test_npu_kimi_k3_modelslim_mla_fp8.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/llm_models/test_npu_mimo_v2_5_pro_fp4_dflash.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/llm_models/test_npu_mimo_v2_5_w8a8.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/llm_models/test_npu_mimo_v2_flash.py
  role: supporting
created_at: '2026-11-08T12:28:23Z'
updated_at: '2026-11-09T04:35:53Z'
platforms: []
---

# SGLang昇腾手工大模型量化与草稿预取测试配方

## 手工文件的覆盖边界

本卡描述手工测试配方，不提供已运行结果。只有源注释明确8张A5/双机A5的条目可以带该硬件上下文，其余没有产品证据，整卡保持draft空平台。GSM8K子类阈值按[共同契约](sglang_ascend_test_gsm8k_contract.md)解释；Kimi使用独立GPQA流程。

| 配方 | 模型、并行与图/缓存 | 量化及推测设置 | 声明目标 |
|---|---|---|---:|
| DeepSeek-V3 MLA FP8 | ModelSlim Terminus W4A4C8 MXFP；8 A5、TP8/DP1/EP1，max-running16，graph最大16，page128，chunk1024，static0.85 | KV fp8_e4m3，FIA/NZ/MLA PO；none A2A，无MTP、无DeepEP | GSM8K 0.95 |
| GLM5.1 W4A8 draft prefetch | TP16/attention-DP4，CPU seq lens关、pin memory开 | DeepEP auto，NEXTN steps4/topk1/draft5、draft unquant | GSM8K 0.80 |
| MiMo-V2.5-Pro FP4 DFLASH | TP8/attention-DP2，static0.87 | DeepEP auto，DFLASH，draft子目录，draft8 | GSM8K 0.90 |
| MiMo-V2.5 W8A8 | TP8/attention-DP2 | 多层EAGLE，steps3/topk1/draft4，draft unquant | GSM8K 0.90 |
| MiMo-V2-Flash | TP16 | 多层EAGLE，steps3/topk1/draft4 | GSM8K 0.90 |

GLM环境中原文变量拼作`SGLANG_ENBLE_TORCH_COMILE`，本卡只保留这个字符串的存在，不将其当作有效编译开关。DFLASH和多层EAGLE是分别配置的路径，不能因模型家族相近互换。产品部署背景可参见[MiMo DFLASH指南](../../models/sglang_ascend/sglang_ascend_doc_mimo_v2_5_pro_dflash.md)。

## Kimi-K3 C8双机流程

源文件明确两主机各8 A5，总TP16，nnodes2，attention使用ascend，A2A none、KV FP8、page128、max-running4，graph批次1/2/4，计算BF16；没有配置DSpark。只有模型路径可用 KIMI_K3_MODELSLIM_MODEL_PATH 环境变量覆盖；dataset 的 local_path 固定为 ./gpqa_diamond，须从包含该目录的位置运行。评测GPQA diamond目标0.935，batch4，max_tokens131072、temperature1、top_p0.95、reasoning_effort=max，并在重试中挑最佳score再assert_metrics。它是长推理质量验收定义，不是稳定重复测量，更不是开启C8的性能对照实验。

比较此配方和W4A8/DSpark注册测试前，必须同时固定权重、KV dtype、节点数、draft算法与采样条件；不能只比较“都是Kimi K3”。

## Evidence

- [test/manual/ascend/llm_models/test_npu_deepseek_v3_modelslim_mla_fp8.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/llm_models/test_npu_deepseek_v3_modelslim_mla_fp8.py)（primary）
- [test/manual/ascend/llm_models/test_npu_glm_5_1_w4a8_draft_prefetch.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/llm_models/test_npu_glm_5_1_w4a8_draft_prefetch.py)（supporting）
- [test/manual/ascend/llm_models/test_npu_kimi_k3_modelslim_mla_fp8.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/llm_models/test_npu_kimi_k3_modelslim_mla_fp8.py)（supporting）
- [test/manual/ascend/llm_models/test_npu_mimo_v2_5_pro_fp4_dflash.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/llm_models/test_npu_mimo_v2_5_pro_fp4_dflash.py)（supporting）
- [test/manual/ascend/llm_models/test_npu_mimo_v2_5_w8a8.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/llm_models/test_npu_mimo_v2_5_w8a8.py)（supporting）
- [test/manual/ascend/llm_models/test_npu_mimo_v2_flash.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/llm_models/test_npu_mimo_v2_flash.py)（supporting）
