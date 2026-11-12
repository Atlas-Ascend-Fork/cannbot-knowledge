---
type: Guide
title: SGLang NPU模型性能回归的声明负载和基线
description: 保存DeepSeek、Kimi和Qwen性能测试的TP/DP、长前缀、多模态shape、并发和目标字段，明确这些不是实测收益。
tags:
- task.testing
- topic.model_serving
- topic.precision
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/deepseek_v4_flash/expert-layout-ais-replicas16.json
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/deepseek_v4_flash/test_npu_deepseek_v4_flash_w8a8_1p1d_16p_in128k_out1k_prefix90_20ms.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/deepseek_v4_flash/test_npu_deepseek_v4_flash_w8a8_8p_in8k_out1k_50ms.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/deepseek_v4_pro/test_npu_deepseek_v4_pro_w4a8_16p_in128k_out1k_prefix90_20ms.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/glm5_1/test_npu_glm5_1_w4a8_1p1d_32p_in64k_out1k_50ms.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/kimi_k3/test_npu_kimi_k3_w4a8_32p_mix_in128k_out1_prefill.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/kimi_k3/test_npu_kimi_k3_w4a8_32p_mix_in128k_out1k_decode_prefix.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/qwen3_5_397b/test_npu_qwen3_5_397b_w4a8_8p_in3k5_out1k5_50ms.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/qwen3_6_27b/test_npu_qwen3_6_27b_1p_in1024x1024_30_out1024_50ms.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/qwen3_6_27b/test_npu_qwen3_6_27b_1p_in1080p_30_out256_50ms.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/qwen3_6_27b/test_npu_qwen3_6_27b_2p_in64k_out1k_prefix90_50ms.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/qwen3_6_27b/test_npu_qwen3_6_27b_w8a8_1p_in3k5_out1k5_50ms.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/qwen3_6_27b/test_npu_qwen3_6_27b_w8a8_1p_in64k_out1k_50ms.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/qwen3_6_27b/test_npu_qwen3_6_27b_w8a8_2p_in128k_out1k_50ms.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/qwen3_6_27b/test_npu_qwen3_6_27b_w8a8_2p_in16k_out1k_50ms.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/qwen3_6_35b_a3b/test_npu_qwen3_6_35b_a3b_1p_in128k_out1k_50ms.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/qwen3_6_35b_a3b/test_npu_qwen3_6_35b_a3b_1p_in128k_out1k_prefix90_50ms.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/qwen3_6_35b_a3b/test_npu_qwen3_6_35b_a3b_1p_in3k5_out1k5_50ms.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/qwen3_6_35b_a3b/test_npu_qwen3_6_35b_a3b_1p_in64k_out1k_50ms.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/qwen3_6_35b_a3b/test_npu_qwen3_6_35b_a3b_1p_in64k_out1k_prefix90_50ms.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/arg_groups/fields/memory.py
  role: constraint
created_at: '2026-11-08T12:28:23Z'
updated_at: '2026-11-09T04:36:38Z'
platforms:
- a3
---

# SGLang NPU模型性能回归的声明负载和基线

## 基线字段的证据强度

以下均来自固定源码的类属性与启动配方，本次没有运行，不是benchmark observation。A3 suite只是计划目标，部分用例disabled或suite空；文件名的1p/2p/8p不能覆盖实际TP参数。指标字段的单位、接受率、hitrate、重试及断言方向按[性能契约](sglang_ascend_test_performance_contract.md)，负载生成按[GSP/随机数据契约](sglang_ascend_test_workload_generation.md)。表中C=客户端最大并发、N=请求数，长度为测试输入/输出token参数，GSP为generated-shared-prefix；prefix90/1是生成器复用参数，不是已观测命中率。

| 配方 | 实际并行/主要设置 | 负载、warmup、请求速率 | 声明指标字段 |
|---|---|---|---|
| DSV4-Flash0731 W8A8 PD | P TP16/DP4 CP zigzag、redundant16；D TP16/DP16 LL、DSPARK6/block5、KV BF16、SWA ratio0.05 | GSM8K型AISBench，131072/1024，C54/N90、repeat0.9、rate3、dp16 | TPOT20，output throughput964.864，TTFT7000 |
| DSV4-Flash W8A8混部 | TP16/DP16 DSPARK7/block6 | random8000/1000、C160/N160、warmup32、rate∞；max_attempts3 | TPOT50、throughput3100、accept_rate0.5 |
| DSV4-Pro W4A8 | 两节点TP32/DP8、DSPARK6/block5，suite空 | GSP131072/1024、prefix0.9、C8/N32、warmup16、seed42、rate∞ | TPOT20、throughput128 |
| GLM5.1 W4A8 PD | P TP4/PP8/CP4，D TP32/DP32/NEXTN3/1/4；disabled | random65536/1024、C32/N64、seed1 | TPOT50、throughput160；docstring写3.5K/1.5K与实际参数不符 |
| Kimi-K3 W4A8 prefill | 四节点TP16/PP4/DP2、层分配24/24/24/21，禁overlap/decode graph，无DSpark；disabled | AISBench131072/1、C1/N1、rate0 | TTFT20000；输出1不比较普通TPOT |
| Kimi-K3 W4A8 decode | 四节点TP64/DP4、DSpark block7 unquant；disabled | AISBench131072/1024、prefix1、C12/N12、rate3、dp4 | TPOT30；prefix1不等于实测100%命中 |
| Qwen3.5-397B W4A8 | **TP16/DP8**，NEXTN3/1/4 unquant、DeepEP auto、ZBAL graph，static0.8，max-total280000 | random3500/1500、C432/N432、warmup16、seed1、rate∞ | TPOT50、throughput5415 |

DSV4-Flash PD配套expert-layout JSON有43个不同层映射，每层272个physical位置，覆盖0..255共256个logical experts，即每层16个额外physical副本；副本分布随层变化，同一logical expert可能出现多次（全文件最高6次），不能理解成固定16个专家各复制一次。它是指定工作负载的静态映射输入，不证明负载已平衡或质量正确。P另有index-cache frequency2、early-send/optimistic；不能把此映射直接用于其它层数/EP配置。

## Qwen3.6的长度、前缀和图批次配方

以下均TP按启动参数，不按文件名推断，TPOT字段均50。未显式warmup处保留harness默认，不补造重复次数或统计置信区间。

| 模型/输入模式 | TP与缓存/图配置 | input/output、C/N、其它控制 | output throughput字段 |
|---|---|---|---:|
| 27B BF16图像1024² | TP2、Mamba60、static0.74，mm-DP-encoder；graph decode2..60 | 单图1024×1024，文本30/output1024，C60/N240、seed1 | 800.8 |
| 27B BF16图像1080p | TP2、max-running38/Mamba38，graph1..38、prefill delay5500ms/pass300 | 单图1920×1080，文本30/output256，C42/N152、warmup38、seed1 | 226 |
| 27B BF16长前缀 | TP2、Mamba160、static0.82，graph1/2/5/10/15/17/19/20 | GSP64000/1000、prefix0.9、C20/N20、warmup1、seed1、rate∞ | 225 |
| 27B W8A8短输入 | TP2、Mamba74，NEXTN3/1/4 | random3500/1500、C54/N216、seed1 | 786.69 |
| 27B W8A8 64K | TP2、Mamba16/max-running6、static0.6、graph1/2/4/5/6 | random64000/1000、C6/N12 | 57.85 |
| 27B W8A8 128K | **TP4**、Mamba7、static0.63，不配置speculative-algorithm/steps/draft数量 | random128000/1000、C4/N16、seed1 | 41.39 |
| 27B W8A8 16K | **TP4**、max-running37，NEXTN4/1/5，graph密集覆盖1..37子集 | random16000/1000、C37/N37、warmup4、seed1 | 426.1 |
| 35B-A3B BF16 128K | TP2、Mamba3/max-running3、static0.9、graph1/2/3、max-total420000 | random128000/1000、C3/N3、seed1 | 60.57 |
| 35B-A3B BF16 128K prefix | TP2、Mamba85/max-running103、static0.85、chunk16384，graph2..103子集 | GSP128000/1000、prefix0.9、C103/N412、seed1、rate∞ | 308.2 |
| 35B-A3B BF16短输入 | TP2、Mamba122/max-running122，max-total659840/max-prefill43400/prefill-max-requests12 | random3500/1500、C122/N122、seed1 | 2031.71 |
| 35B-A3B BF16 64K | TP2、Mamba20/max-running10、static0.65、max-total600000 | random64000/1000、C10/N40、seed1 | 141.72 |
| 35B-A3B BF16 64K prefix | TP2、Mamba Radix前缀缓存extra_buffer、DEEPEP_HCCL_BUFFSIZE300 | GSP65536/1024、prefix0.9、C40/N40、seed1、rate∞ | 660 |

35B-A3B BF16 64K prefix 配方没有启用 hierarchical cache（默认False），其吞吐字段不能归因于 HiCache 主机分层缓存。图像case使用sglang-oai-chat/MM_CUSTOM_GEN，视觉shape和文本长度必须一起报告。1024²用例显式profiling=1/prefill，1080p用例profiling=0，存在测量条件差异，不能只看throughput字段得出图像大小的因果影响。35B两个类写aisbench_dataset_type而其它常用dataset_type，是否消费取决于当前harness；本卡不自行宣称覆盖效果。

复测需记录服务版本、权重、设备、客户端tokenizer、warmup、有效请求、实际采样/EOS、重复次数、分位数和日志。上述类属性缺少重复测量、误差及完整硬件软件记录，禁止转换成“某优化提升X%”。

## Evidence

- [test/registered/npu/performance/deepseek_v4_flash/expert-layout-ais-replicas16.json](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/deepseek_v4_flash/expert-layout-ais-replicas16.json)（primary）
- [test/registered/npu/performance/deepseek_v4_flash/test_npu_deepseek_v4_flash_w8a8_1p1d_16p_in128k_out1k_prefix90_20ms.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/deepseek_v4_flash/test_npu_deepseek_v4_flash_w8a8_1p1d_16p_in128k_out1k_prefix90_20ms.py)（supporting）
- [test/registered/npu/performance/deepseek_v4_flash/test_npu_deepseek_v4_flash_w8a8_8p_in8k_out1k_50ms.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/deepseek_v4_flash/test_npu_deepseek_v4_flash_w8a8_8p_in8k_out1k_50ms.py)（supporting）
- [test/registered/npu/performance/deepseek_v4_pro/test_npu_deepseek_v4_pro_w4a8_16p_in128k_out1k_prefix90_20ms.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/deepseek_v4_pro/test_npu_deepseek_v4_pro_w4a8_16p_in128k_out1k_prefix90_20ms.py)（supporting）
- [test/registered/npu/performance/glm5_1/test_npu_glm5_1_w4a8_1p1d_32p_in64k_out1k_50ms.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/glm5_1/test_npu_glm5_1_w4a8_1p1d_32p_in64k_out1k_50ms.py)（supporting）
- [test/registered/npu/performance/kimi_k3/test_npu_kimi_k3_w4a8_32p_mix_in128k_out1_prefill.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/kimi_k3/test_npu_kimi_k3_w4a8_32p_mix_in128k_out1_prefill.py)（supporting）
- [test/registered/npu/performance/kimi_k3/test_npu_kimi_k3_w4a8_32p_mix_in128k_out1k_decode_prefix.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/kimi_k3/test_npu_kimi_k3_w4a8_32p_mix_in128k_out1k_decode_prefix.py)（supporting）
- [test/registered/npu/performance/qwen3_5_397b/test_npu_qwen3_5_397b_w4a8_8p_in3k5_out1k5_50ms.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/qwen3_5_397b/test_npu_qwen3_5_397b_w4a8_8p_in3k5_out1k5_50ms.py)（supporting）
- [test/registered/npu/performance/qwen3_6_27b/test_npu_qwen3_6_27b_1p_in1024x1024_30_out1024_50ms.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/qwen3_6_27b/test_npu_qwen3_6_27b_1p_in1024x1024_30_out1024_50ms.py)（supporting）
- [test/registered/npu/performance/qwen3_6_27b/test_npu_qwen3_6_27b_1p_in1080p_30_out256_50ms.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/qwen3_6_27b/test_npu_qwen3_6_27b_1p_in1080p_30_out256_50ms.py)（supporting）
- [test/registered/npu/performance/qwen3_6_27b/test_npu_qwen3_6_27b_2p_in64k_out1k_prefix90_50ms.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/qwen3_6_27b/test_npu_qwen3_6_27b_2p_in64k_out1k_prefix90_50ms.py)（supporting）
- [test/registered/npu/performance/qwen3_6_27b/test_npu_qwen3_6_27b_w8a8_1p_in3k5_out1k5_50ms.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/qwen3_6_27b/test_npu_qwen3_6_27b_w8a8_1p_in3k5_out1k5_50ms.py)（supporting）
- [test/registered/npu/performance/qwen3_6_27b/test_npu_qwen3_6_27b_w8a8_1p_in64k_out1k_50ms.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/qwen3_6_27b/test_npu_qwen3_6_27b_w8a8_1p_in64k_out1k_50ms.py)（supporting）
- [test/registered/npu/performance/qwen3_6_27b/test_npu_qwen3_6_27b_w8a8_2p_in128k_out1k_50ms.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/qwen3_6_27b/test_npu_qwen3_6_27b_w8a8_2p_in128k_out1k_50ms.py)（supporting）
- [test/registered/npu/performance/qwen3_6_27b/test_npu_qwen3_6_27b_w8a8_2p_in16k_out1k_50ms.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/qwen3_6_27b/test_npu_qwen3_6_27b_w8a8_2p_in16k_out1k_50ms.py)（supporting）
- [test/registered/npu/performance/qwen3_6_35b_a3b/test_npu_qwen3_6_35b_a3b_1p_in128k_out1k_50ms.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/qwen3_6_35b_a3b/test_npu_qwen3_6_35b_a3b_1p_in128k_out1k_50ms.py)（supporting）
- [test/registered/npu/performance/qwen3_6_35b_a3b/test_npu_qwen3_6_35b_a3b_1p_in128k_out1k_prefix90_50ms.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/qwen3_6_35b_a3b/test_npu_qwen3_6_35b_a3b_1p_in128k_out1k_prefix90_50ms.py)（supporting）
- [test/registered/npu/performance/qwen3_6_35b_a3b/test_npu_qwen3_6_35b_a3b_1p_in3k5_out1k5_50ms.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/qwen3_6_35b_a3b/test_npu_qwen3_6_35b_a3b_1p_in3k5_out1k5_50ms.py)（supporting）
- [test/registered/npu/performance/qwen3_6_35b_a3b/test_npu_qwen3_6_35b_a3b_1p_in64k_out1k_50ms.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/qwen3_6_35b_a3b/test_npu_qwen3_6_35b_a3b_1p_in64k_out1k_50ms.py)（supporting）
- [test/registered/npu/performance/qwen3_6_35b_a3b/test_npu_qwen3_6_35b_a3b_1p_in64k_out1k_prefix90_50ms.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/performance/qwen3_6_35b_a3b/test_npu_qwen3_6_35b_a3b_1p_in64k_out1k_prefix90_50ms.py)（supporting）
