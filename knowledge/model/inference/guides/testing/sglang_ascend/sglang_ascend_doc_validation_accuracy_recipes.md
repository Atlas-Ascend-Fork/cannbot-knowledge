---
type: Guide
title: SGLang NPU任务精度回归的模型与采样配方
description: 汇总GPQA、AIME、GSM8K及MMMU注册配置，标出PR数据集切换、禁用测试、CP注释与文件名不等于真实负载的差异。
tags:
- task.testing
- topic.model_serving
- topic.precision
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/deepseek_v3_2/test_npu_deepseek_v3_2_8p_aime25.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/deepseek_v4_flash/test_npu_deepseek_v4_flash_0731_w8a8_1p1d_16p_gpqa.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/deepseek_v4_flash/test_npu_deepseek_v4_flash_fp8_4p_gpqa_a5.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/deepseek_v4_flash/test_npu_deepseek_v4_flash_w8a8_8p_gpqa.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/deepseek_v4_pro/test_npu_deepseek_v4_pro_0813_w4a8_1p1d_32p_gpqa.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/glm4_6v_flash/test_npu_glm4_6v_flash_1p_mmmu.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/glm4_7_flash/test_npu_glm4_7_flash_1p_aime25.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/glm4_7_flash/test_npu_glm4_7_flash_1p_gsm8k.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/glm5_1/test_npu_glm5_1_w4a8_1p1d_32p_in64k_out1k_50ms_aime26.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/glm5_2/test_npu_glm_5_2_w8a8_16p_gpqa.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/glm5_2/test_npu_glm_5_2_w8a8_2p2d_32p_dcp_gpqa.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/glm5_2/test_npu_glm_5_2_w8a8_2p2d_32p_pcp_gpqa.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/glm5_top64_pruned/test_npu_glm5_top64_pruned_bf16_8p_gsm8k.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/kimi_k2_6/test_npu_kimi_k2_6_w4a8_16p_in64k_out1k_100ms_aime25.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/kimi_k3/test_npu_kimi_k3_w4a8_32p_gpqa.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/minimax_m2_5/test_npu_minimax_m2_5_w8a8_4p_in64k_out1k_prefix90_50ms_gpqa.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/minimax_m2_5/test_npu_minimax_m2_5_w8a8_8p_in3k5_out1k5_50ms_gpqa.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/moonshotai_moonlight_16b_a3b/test_npu_moonlight_16b_a3b_bf16_1p_gsm8k.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/qwen3-8b/test_npu_qwen3_8b_w8a8_1p_in3k5_out1k5_50ms_gpqa.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/qwen3-8b/test_npu_qwen3_8b_w8a8_1p_in6k_out1k5_bs16_gpqa.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/qwen3_30b_a3b/test_npu_qwen3_30b_w8a8_1p_in3k5_out1k5_50ms_aime25.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/qwen3_32b/test_npu_qwen3_32b_bf16_8p_gpqa.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/qwen3_32b/test_npu_qwen3_32b_w8a8_2p_in3k5_out1k5_50ms_gpqa.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/qwen3_32b/test_npu_qwen3_32b_w8a8_2p_in3k5_out1k5_50ms_gpqa_a2.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/qwen3_5_9b/test_npu_qwen3_5_9b_bf16_1p_gsm8k.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/qwen3_6_27b/test_npu_qwen3_6_27b_1p_gpqa.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/qwen3_6_27b/test_npu_qwen3_6_27b_w8a8_1p_in3k5_out1k5_50ms_gpqa.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/qwen3_6_35b_a3b/test_npu_qwen3_6_35b_a3b_1p_aime26.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/qwen3_6_35b_a3b/test_npu_qwen3_6_35b_a3b_1p_in64k_out1k_prefix90_50ms_aime26.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/qwen3_next_80b_a3b_instruct/test_npu_qwen3_next_80b_w8a8_2p_in6k_out1k5_bs16_aime25.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/qwen3_omni_30b_a3b_thinking/test_npu_qwen3_omni_30b_a3b_thinking_1p_mmmu.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/qwen3_vl_30b_a3b/test_npu_qwen3_vl_30b_a3b_bf16_2p_gsm8k.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/qwen3_vl_30b_a3b_thinking/test_npu_qwen3_vl_30b_a3b_thinking_1p_mmmu.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/qwen3_vl_8b/test_npu_qwen3_vl_8b_bf16_2p_gsm8k.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/qwen3_vl_8b_thinking/test_npu_qwen3_vl_8b_thinking_1p_mmmu.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/test/ascend/e2e/test_npu_accuracy_utils.py
  role: implementation
created_at: '2026-11-08T12:28:23Z'
updated_at: '2026-11-09T04:35:53Z'
platforms:
- a2
- a3
- '950'
---

# SGLang NPU任务精度回归的模型与采样配方

## 任务与证据的解释

固定源码定义了阈值和调用参数，本次没有启动模型或得到分数。下表为声明的quality目标；其中 few_shot_num（0/5-shot）和 seed（1/42）仅为测试类属性，当前 run_evalscope_with_retry 未将它们传给 run_evalscope，后者亦不接收/写入这些参数，不能视为 EvalScope 已生效的条件。比较实现使用的容差、重试和AISBench配置见[精度阈值契约](sglang_ascend_test_accuracy_thresholds.md)。A3/A2/950是逐文件注册或明确说明的测试目标，不是所有条目的通用支持矩阵。与部署指南复用模型名时仍须保留本卡checkpoint、TP/DP/CP与采样差异。

| 模型配方 | 实际任务与目标 | 主要参数/区别 |
|---|---|---|
| DeepSeek-V3.2 W8A8 TP16 | **GSM8K 0.936** | 文件名AIME25但datasets实际gsm8k；ModelSlim、禁图 |
| DSV4-Flash 0731 W8A8 PD | GPQA 0.874 | P TP8/PP2/DP8、CP interleave；D TP16/DP16 low_latency、DSPARK6，draft ModelSlim、KV BF16；batch128、max125000、temp1、top_p1、reasoning high |
| DSV4-Flash W8A8混部 | 仅非nightly PR为GSM8K 0.93/limit300；其他（含PR触发nightly）GPQA 0.874/limit100000 | TP16/DP16、DSPARK7/block6；batch128、stream、seed类属性1（未传EvalScope）、timeout6000 |
| DSV4-Flash FP8 | GPQA 0.874 | TP4，nightly A5及明确950上下文；DSPARK6/block5，draft FP8，KV auto；batch128/max125000/reasoning max |
| DSV4-Pro 0813 W4A8 PD | GPQA 0.85 | P两节点TP16/PP2/DP8；D两节点TP32/DP4、DSPARK6；batch64；测试标记disabled |
| GLM4.7-Flash BF16 TP2 | AIME25 0.7667（0shot类属性，未传）；GSM8K 0.956（5shot类属性，未传） | 两者max65536/temp1/batch64 |
| GLM4.6V-Flash BF16 TP2 | MMMU 0.711 | batch16/max65536/temp1；禁用理由写performance，但此类为精度测试 |
| GLM5.1 W4A8 PD | AIME26 0.953 | P TP4/PP8/CP4，D TP32/DP32；batch64/max65536/temp1；disabled PCP注释仅此测试，不能推广NPU全局PCP禁用 |
| GLM5.2 W8A8 混部/PD | GPQA 0.912 | 混部两节点TP32/DP8、NEXTN3/1/4 unquant；PD分别DCP4或PCP8方案，SDMA、HiCache80；max131072/temp1/top_p0.95/batch32；均disabled |
| GLM5 top64 pruned BF16 | GSM8K 0.48 | TP16，limit100、max2048/temp0.01/batch16 |
| Kimi-K2.6 W4A8 | AIME25 0.961 | 两节点TP32/DP32，EAGLE3 unquant3/1/4，max65536/temp1/batch64；disabled |
| Kimi-K3 W4A8 | GPQA 0.935 | 四节点TP64/DP4、DSpark block7 unquant、HiCache2 write_through；max131072/temp1/top_p0.95/reasoning max、batch32、seed类属性42（未传EvalScope）、timeout10000 |
| MiniMax-M2.5 W8A8 | GPQA 0.852 | TP8长前缀和TP16/DP16吞吐两配置；EAGLE3及外部custom包、fuseEP2 |
| Moonlight-16B-A3B BF16 | GSM8K 0.837 | TP2，5shot类属性（未传）、max7168/temp1/batch64 |

GLM5.2 PD两种方案共享GPQA后处理：删除think之前内容，并强调答案格式；PD max_retries1。其P配置均TP8/PP4/DP8或CP8；DCP方案D为TP32/DP8/DCP4/EP32，PCP方案D没有DCP。不能将两个方案拼成同一个启动命令。

DSV4-Flash W8A8混部的缩减条件同时要求 GITHUB_EVENT_NAME=pull_request 且 GITHUB_WORKFLOW_REF 不含 nightly-test-npu.yml；其他运行均使用 GPQA，不能只按 PR 事件判断。

## Qwen质量配置

| 权重/配置 | 实际目标 | 采样及并行条件 |
|---|---|---|
| Qwen3-8B W8A8 | GPQA 0.4444 | TP1 EAGLE3 3/1/4，max40000/batch64；另一TP2 4/1/5，max32768/batch16 |
| Qwen3-30B W8A8 | AIME25 0.613 | TP2 EAGLE3 3/1/4，max32768/temp1/batch16 |
| Qwen3-32B | GPQA 0.4949 | BF16 TP16/EAGLE3 4/1/5，W8A8 TP4/3/1/4；max40000/temp1/batch64；W8配置另有A2专门注册 |
| Qwen3.5-9B BF16 | GSM8K 0.835 | TP2、limit100、5shot类属性（未传）、max8192/temp0.6/batch64 |
| Qwen3.6-27B BF16 / W8A8 | GPQA 0.878 | TP2，max81920/temp0/enable_thinking=true；BF16 Mamba120/batch64，W8 Mamba74/batch16；max_retries2 |
| Qwen3.6-35B-A3B BF16 | AIME26 0.927 | TP2、temp0/repetition1.08，max_retries2；普通版batch4/max131072，64K-prefix版batch64/max65536 |
| Qwen3-Next W8A8 | AIME25 0.695 | TP4/DP2、NEXTN3/1/4 unquant；max65536/temp0.7/top_p0.8/top_k20/thinkingfalse；max_concurrency16 |
| Qwen3-Omni-30B Thinking | MMMU 0.576 | TP2；继承Qwen30 ModelSlim配置再移除spec/parser参数；disabled |
| Qwen3-VL-30B BF16 | GSM8K 0.9538 | TP4、5shot类属性（未传）、max40000/temp0/thinkingfalse |
| Qwen3-VL-30B Thinking | MMMU 0.7167 | TP2、0shot类属性（未传）、max65536/batch64 |
| Qwen3-VL-8B BF16 | GSM8K 0.9553 | TP4、5shot类属性（未传）、max32768/temp1/top_p1/top_k40/presence2/thinkingfalse |
| Qwen3-VL-8B Thinking | PR MMMU 0.64/limit5；其他0.7011/limit100000 | TP2、max65536/batch64 |

Qwen3.6-27B W8A8先用最多3次256-token请求检查accept_length推导的`(acc_length-1)/(draft_tokens-1) >= 0.2`，再做昂贵GPQA。这是草稿健康门槛，不是报告20%加速。

## 缓存与性能伴随检查

DSV4-Flash 0731和Pro声明host-cache hit门槛0，harness要求严格>0且缺少host指标会失败，即要求非零Host命中；这不能证明高命中率或性能改善。Kimi-K3的64K共享前缀门槛10%，同样要求严格>10%，3组各32请求、并发32、输出1024、warmup16。DSV4-Flash FP8还定义8K/1K、C160/N160、warmup32、最多3次的accept_rate0.5检查，没有在该类设置TPOT/throughput目标。相同模型的数值准确率、cache命中与吞吐应分别报告。

## Evidence

- [test/registered/npu/accuracy/deepseek_v3_2/test_npu_deepseek_v3_2_8p_aime25.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/deepseek_v3_2/test_npu_deepseek_v3_2_8p_aime25.py)（primary）
- [test/registered/npu/accuracy/deepseek_v4_flash/test_npu_deepseek_v4_flash_0731_w8a8_1p1d_16p_gpqa.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/deepseek_v4_flash/test_npu_deepseek_v4_flash_0731_w8a8_1p1d_16p_gpqa.py)（supporting）
- [test/registered/npu/accuracy/deepseek_v4_flash/test_npu_deepseek_v4_flash_fp8_4p_gpqa_a5.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/deepseek_v4_flash/test_npu_deepseek_v4_flash_fp8_4p_gpqa_a5.py)（supporting）
- [test/registered/npu/accuracy/deepseek_v4_flash/test_npu_deepseek_v4_flash_w8a8_8p_gpqa.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/deepseek_v4_flash/test_npu_deepseek_v4_flash_w8a8_8p_gpqa.py)（supporting）
- [test/registered/npu/accuracy/deepseek_v4_pro/test_npu_deepseek_v4_pro_0813_w4a8_1p1d_32p_gpqa.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/deepseek_v4_pro/test_npu_deepseek_v4_pro_0813_w4a8_1p1d_32p_gpqa.py)（supporting）
- [test/registered/npu/accuracy/glm4_6v_flash/test_npu_glm4_6v_flash_1p_mmmu.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/glm4_6v_flash/test_npu_glm4_6v_flash_1p_mmmu.py)（supporting）
- [test/registered/npu/accuracy/glm4_7_flash/test_npu_glm4_7_flash_1p_aime25.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/glm4_7_flash/test_npu_glm4_7_flash_1p_aime25.py)（supporting）
- [test/registered/npu/accuracy/glm4_7_flash/test_npu_glm4_7_flash_1p_gsm8k.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/glm4_7_flash/test_npu_glm4_7_flash_1p_gsm8k.py)（supporting）
- [test/registered/npu/accuracy/glm5_1/test_npu_glm5_1_w4a8_1p1d_32p_in64k_out1k_50ms_aime26.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/glm5_1/test_npu_glm5_1_w4a8_1p1d_32p_in64k_out1k_50ms_aime26.py)（supporting）
- [test/registered/npu/accuracy/glm5_2/test_npu_glm_5_2_w8a8_16p_gpqa.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/glm5_2/test_npu_glm_5_2_w8a8_16p_gpqa.py)（supporting）
- [test/registered/npu/accuracy/glm5_2/test_npu_glm_5_2_w8a8_2p2d_32p_dcp_gpqa.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/glm5_2/test_npu_glm_5_2_w8a8_2p2d_32p_dcp_gpqa.py)（supporting）
- [test/registered/npu/accuracy/glm5_2/test_npu_glm_5_2_w8a8_2p2d_32p_pcp_gpqa.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/glm5_2/test_npu_glm_5_2_w8a8_2p2d_32p_pcp_gpqa.py)（supporting）
- [test/registered/npu/accuracy/glm5_top64_pruned/test_npu_glm5_top64_pruned_bf16_8p_gsm8k.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/glm5_top64_pruned/test_npu_glm5_top64_pruned_bf16_8p_gsm8k.py)（supporting）
- [test/registered/npu/accuracy/kimi_k2_6/test_npu_kimi_k2_6_w4a8_16p_in64k_out1k_100ms_aime25.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/kimi_k2_6/test_npu_kimi_k2_6_w4a8_16p_in64k_out1k_100ms_aime25.py)（supporting）
- [test/registered/npu/accuracy/kimi_k3/test_npu_kimi_k3_w4a8_32p_gpqa.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/kimi_k3/test_npu_kimi_k3_w4a8_32p_gpqa.py)（supporting）
- [test/registered/npu/accuracy/minimax_m2_5/test_npu_minimax_m2_5_w8a8_4p_in64k_out1k_prefix90_50ms_gpqa.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/minimax_m2_5/test_npu_minimax_m2_5_w8a8_4p_in64k_out1k_prefix90_50ms_gpqa.py)（supporting）
- [test/registered/npu/accuracy/minimax_m2_5/test_npu_minimax_m2_5_w8a8_8p_in3k5_out1k5_50ms_gpqa.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/minimax_m2_5/test_npu_minimax_m2_5_w8a8_8p_in3k5_out1k5_50ms_gpqa.py)（supporting）
- [test/registered/npu/accuracy/moonshotai_moonlight_16b_a3b/test_npu_moonlight_16b_a3b_bf16_1p_gsm8k.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/moonshotai_moonlight_16b_a3b/test_npu_moonlight_16b_a3b_bf16_1p_gsm8k.py)（supporting）
- [test/registered/npu/accuracy/qwen3-8b/test_npu_qwen3_8b_w8a8_1p_in3k5_out1k5_50ms_gpqa.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/qwen3-8b/test_npu_qwen3_8b_w8a8_1p_in3k5_out1k5_50ms_gpqa.py)（supporting）
- [test/registered/npu/accuracy/qwen3-8b/test_npu_qwen3_8b_w8a8_1p_in6k_out1k5_bs16_gpqa.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/qwen3-8b/test_npu_qwen3_8b_w8a8_1p_in6k_out1k5_bs16_gpqa.py)（supporting）
- [test/registered/npu/accuracy/qwen3_30b_a3b/test_npu_qwen3_30b_w8a8_1p_in3k5_out1k5_50ms_aime25.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/qwen3_30b_a3b/test_npu_qwen3_30b_w8a8_1p_in3k5_out1k5_50ms_aime25.py)（supporting）
- [test/registered/npu/accuracy/qwen3_32b/test_npu_qwen3_32b_bf16_8p_gpqa.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/qwen3_32b/test_npu_qwen3_32b_bf16_8p_gpqa.py)（supporting）
- [test/registered/npu/accuracy/qwen3_32b/test_npu_qwen3_32b_w8a8_2p_in3k5_out1k5_50ms_gpqa.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/qwen3_32b/test_npu_qwen3_32b_w8a8_2p_in3k5_out1k5_50ms_gpqa.py)（supporting）
- [test/registered/npu/accuracy/qwen3_32b/test_npu_qwen3_32b_w8a8_2p_in3k5_out1k5_50ms_gpqa_a2.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/qwen3_32b/test_npu_qwen3_32b_w8a8_2p_in3k5_out1k5_50ms_gpqa_a2.py)（supporting）
- [test/registered/npu/accuracy/qwen3_5_9b/test_npu_qwen3_5_9b_bf16_1p_gsm8k.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/qwen3_5_9b/test_npu_qwen3_5_9b_bf16_1p_gsm8k.py)（supporting）
- [test/registered/npu/accuracy/qwen3_6_27b/test_npu_qwen3_6_27b_1p_gpqa.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/qwen3_6_27b/test_npu_qwen3_6_27b_1p_gpqa.py)（supporting）
- [test/registered/npu/accuracy/qwen3_6_27b/test_npu_qwen3_6_27b_w8a8_1p_in3k5_out1k5_50ms_gpqa.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/qwen3_6_27b/test_npu_qwen3_6_27b_w8a8_1p_in3k5_out1k5_50ms_gpqa.py)（supporting）
- [test/registered/npu/accuracy/qwen3_6_35b_a3b/test_npu_qwen3_6_35b_a3b_1p_aime26.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/qwen3_6_35b_a3b/test_npu_qwen3_6_35b_a3b_1p_aime26.py)（supporting）
- [test/registered/npu/accuracy/qwen3_6_35b_a3b/test_npu_qwen3_6_35b_a3b_1p_in64k_out1k_prefix90_50ms_aime26.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/qwen3_6_35b_a3b/test_npu_qwen3_6_35b_a3b_1p_in64k_out1k_prefix90_50ms_aime26.py)（supporting）
- [test/registered/npu/accuracy/qwen3_next_80b_a3b_instruct/test_npu_qwen3_next_80b_w8a8_2p_in6k_out1k5_bs16_aime25.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/qwen3_next_80b_a3b_instruct/test_npu_qwen3_next_80b_w8a8_2p_in6k_out1k5_bs16_aime25.py)（supporting）
- [test/registered/npu/accuracy/qwen3_omni_30b_a3b_thinking/test_npu_qwen3_omni_30b_a3b_thinking_1p_mmmu.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/qwen3_omni_30b_a3b_thinking/test_npu_qwen3_omni_30b_a3b_thinking_1p_mmmu.py)（supporting）
- [test/registered/npu/accuracy/qwen3_vl_30b_a3b/test_npu_qwen3_vl_30b_a3b_bf16_2p_gsm8k.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/qwen3_vl_30b_a3b/test_npu_qwen3_vl_30b_a3b_bf16_2p_gsm8k.py)（supporting）
- [test/registered/npu/accuracy/qwen3_vl_30b_a3b_thinking/test_npu_qwen3_vl_30b_a3b_thinking_1p_mmmu.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/qwen3_vl_30b_a3b_thinking/test_npu_qwen3_vl_30b_a3b_thinking_1p_mmmu.py)（supporting）
- [test/registered/npu/accuracy/qwen3_vl_8b/test_npu_qwen3_vl_8b_bf16_2p_gsm8k.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/qwen3_vl_8b/test_npu_qwen3_vl_8b_bf16_2p_gsm8k.py)（supporting）
- [test/registered/npu/accuracy/qwen3_vl_8b_thinking/test_npu_qwen3_vl_8b_thinking_1p_mmmu.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/accuracy/qwen3_vl_8b_thinking/test_npu_qwen3_vl_8b_thinking_1p_mmmu.py)（supporting）
