---
type: Guide
title: vLLM Ascend E2E配置证据矩阵：模型、并行、任务与负载选择
description: 从固定测试配置选择模型与量化、TP/PP/PCP/DCP和精度/性能场景，区分模型家族名、实际checkpoint、模板参数及未执行的支持声明；保留多模态、ASR、奖励模型和小型fixture的证据边界。
tags:
- task.testing
- task.implementation
- topic.model_adaptation
- topic.parallelism
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/context_parallel/DeepSeek-V4.1-Flash-W8A8-DSpark-PCP.yaml
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/context_parallel/Kimi-K2.6-W4A8-PCP-DCP.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/context_parallel/Qwen3-30B-A3B-VWN-eagle3-PCP.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/context_parallel/glm-5.2-W4A8C8-DSpark-PCP.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/kv_pool/DSv4-Flash-Memcache-PD-layerwise.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/kv_pool/DeepSeek-V4-Flash-Memcache-PD-acc.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/kv_pool/GLM-5.2-W8A8C8-A3-Memcache-PD.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/kv_pool/Qwen3.5-397B-Memcache-perf.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/kv_pool/Qwen3.5-397B-no-Memcache-perf.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/pp/GLM-5.3-W8A8C8-A3-200k-PP-PD.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/DeepSeek/DS-V4-flash-w8a8-PD-prefix-weekly.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/DeepSeek/DeepSeek-R1-W8A8-EPLB.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/DeepSeek/DeepSeek-V4-Flash-W8A8-A3-Breakable.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/DeepSeek/DeepSeek-V4-Flash-W8A8-A3-MRV2.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/DeepSeek/DeepSeek-V4-Flash-W8A8-A3.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/DeepSeek/DeepSeek-V4-Flash-w8a8-bugtest-acc.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/DeepSeek/DeepSeek-V4-Flash-w8a8-sleep-wakeup.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/DeepSeek/DeepSeek-V4-Pro-w4a8-1M-PD.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/DeepSeek/DeepSeek-V4-Pro-w4a8-PD-no-prefix.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/DeepSeek/DeepSeek-V4-Pro-w4a8-prefix-cache-PD.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/DeepSeek/DeepSeek-V4-Pro-w4a8-prefix-cache-PD_weekly.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/DeepSeek/DeepSeek-V4-flash-w8a8-PD-no-prefix.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/DeepSeek/DeepSeek-V4-flash-w8a8-PD-prefix-MRV2.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/DeepSeek/DeepSeek-V4-flash-w8a8-PD-prefix.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/DeepSeek/DeepSeek-V4.1-Flash-w8a8-PD-MRV2.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/DeepSeek/DeepSeek-V4.1-Flash-w8a8-PD-prefix.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/DeepSeek/DeepSeek_V3.1T_MTP1_128K_1K_PD.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/DeepSeek/DeepSeek_V3.1T_MTP1_3_5K_1_5K_PD.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/DeepSeek/DeepSeek_V3.1T_MTP1_PD.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/DeepSeek/DeepSeek_V3.1T_MTP3_PD.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/DeepSeek/DeepSeek_V3.1T_layerwise_PD.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/DeepSeek/DeepSeek_V31_Terminus_w4a8_w8a8_A5.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/DeepSeek/DeepSeek_V31_Terminus_w4a8_w8a8_A5_weekly.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/DeepSeek/DeepSeek_V31_W4A4C8_A5.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/DeepSeek/DeepSeek_V31_W4A4C8_A5_weekly.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/DeepSeek/DeepSeek_V4_Flash_A5.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/DeepSeek/DeepSeek_V4_Flash_A5_weekly.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/DeepSeek/DeepSeek_V4_Flash_K15_dspark_A5.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/DeepSeek/acceptace_rate_deepseekv4-flash-w8a8-mtp.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM-5.1-W8A8-PrefillMC2.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM-5.1-W8A8C8-128k-1k-90-50-PD.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM-5.1-W8A8C8-3.5k-1.5k-0-20-PD.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM-5.1-W8A8C8-3.5k-1.5k-0-50-PD.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM-5.1-W8A8C8-64k-1k-90-50-PD.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM-5.1-W8A8C8-A3_128k_90_50.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM-5.1-W8A8C8-A3_198k_function.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM-5.1-W8A8C8-A3_3.5k_1.5k_0_20.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM-5.1-W8A8C8-A3_3.5k_1.5k_0_50.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM-5.1-W8A8C8-A3_64k_90_50.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM-5.1-w8a8c8-MTP-offload-test-perf.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM-5.2-W4A8-DSpark-A3-V2.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM-5.2-W4A8-DSpark-A3.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM-5.2-W4A8-MTP-A3-V2.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM-5.2-W4A8-MTP-A3.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM-5.2-W4A8C8-1M-PD-DCP.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM-5.2-W4A8C8-SFA-DCP.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM-5.2-W8A8C8-128k-1k-90-50-PD.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM-5.2-W8A8C8-3.5k-1.5k-0-20-PD.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM-5.2-W8A8C8-3.5k-1.5k-0-50-PD.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM-5.2-W8A8C8-64k-1k-90-50-PD.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM-5.2-W8A8C8-A3_128k-static-super-kernels.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM-5.2-W8A8C8-A3_128k_90_50.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM-5.2-W8A8C8-A3_198k_function.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM-5.2-W8A8C8-A3_3.5k_1.5k_0_20.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM-5.2-W8A8C8-A3_3.5k_1.5k_0_50.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM-5.2-W8A8C8-A3_64k_90_50.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM-5.3-Flash-W8A8-130k-PD.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM-5_1-W8A8_A3_weekly.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM5_1-W8A8-A2-dual-nodes.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM5_1-W8A8-A3-dual-nodes.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM5_1-W8A8-EP.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM5_1_W4A4_A5.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM5_1_W4A4_A5_weekly.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM5_2-W8A8-A3-dual-nodes.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM5_3-W8A8-A3-dual-nodes.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM_5_1_PD_in32k_bs16-0.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM_5_1_PD_in32k_bs20-90.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/GLM/GLM_5_1_PD_in64k_bs16-90.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Gemma/Gemma4-31B-Dense.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Gemma/Gemma4.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Gemma/Gemma4_26B_A4B_W4A4_A5.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Gemma/Gemma4_31B_W4A4_A5.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Hunyuan/Hy3-preview.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Kimi/Kimi-K2.5-W4A8-128k-1k-TPOT50.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Kimi/Kimi-K2.5-W4A8-16k-1k-TPOT50.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Kimi/Kimi-K2.6-W4A8-128k-1k-TPOT50-PD.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Kimi/Kimi-K2.6-W4A8-254k-1k-TPOT20-PD.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Kimi/Kimi-K2.6-W4A8-3.5k-1.5k-TPOT50-PD.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Kimi/Kimi-K2.6-W4A8-64k-1k-TPOT50-PD.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Kimi/Kimi-K2.6-w4a8-A3.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Kimi/Kimi-K2.6-w4a8-A3_weekly.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Kimi/Kimi-K2.7-W4A8-128k-1k-TPOT50-PD.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Kimi/Kimi-K2.7-W4A8-254k-1k-TPOT20-PD.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Kimi/Kimi-K2.7-W4A8-3.5k-1.5k-TPOT50-PD.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Kimi/Kimi-K2.7-W4A8-64k-1k-TPOT50-PD.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Kimi/Kimi-K2.7-w4a8-A3.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Kimi/Kimi-K2_5-W4A8-A2-dual-nodes.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Kimi/KimiK26_w4a4c8_A5.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Kimi/KimiK26_w4a4c8_A5_weekly.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Kimi/kimi-k2.6_max_model_len.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/MiniMax/MiniMax-M2.5-W8A8-A3.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/MiniMax/MiniMax-M2.5-w8a8-QuaRot-A3.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/MiniMax/MiniMax-M2.5-w8a8-QuaRot-step.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/MiniMax/MiniMax-M3-BF16-A3.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/MiniMax/MiniMax-M3-W8A8-A3-EAGLE3.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/MiniMax/MiniMax-PD-in32k-bs4-1.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/MiniMax/Minimax_M2.7_w8a8_A3.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/MiniMax/Minimax_m2.7_in128k_1k_prefix90_tpot50.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/MiniMax/Minimax_m2.7_in198_prefix99.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/MiniMax/Minimax_m2.7_in3_5_tpot20.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/MiniMax/Minimax_m2.7_in3_5_tpot50.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/MiniMax/Minimax_m2.7_in64k_1k_prefix90_tpot50.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Prefix-Cache-Qwen3-32B-Int8.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/QWEN3_235B_PD_3_5K_1_5k.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen-3.5-397B-A17B-W8A8-PD.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen2.5-VL-7B-Instruct-EPD.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3-14B-w8a8sc-310p.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3-235B-A22B-A2.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3-235B-A22B-W8A8_piecewise_fullgraph_A3.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3-30B-A3B-BF16-A2.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3-30B-A3B-W4A8-llm-compressor.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3-30B-A3B-W8A8-A2.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3-30B-A3B-W8A8-offload-test-acc.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3-30B-A3B-W8A8.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3-30B-QuaRot-eagle3.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3-32B-Int8-A2.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3-32B-Int8.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3-32B-QuaRot-eagle3.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3-32B-W8A8C8-A3.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3-32B-w8a8sc-310p.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3-32B.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3-8B-w8a8sc-310p.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3-Coder-30B-A3B-Instruct-test-acc.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3-VL-32B-Instruct-W8A8.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3.5-122B-A10B-W8A8-A2.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3.5-122B-A10B-W8A8-A3.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3.5-122B-A10B-W8A8-A3_weekly.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3.5-122B-A10B-w4a8-128k-1k-PD.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3.5-122B-A10B-w4a8-16k-1k-PD.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3.5-122B-A10B-w4a8-984k-1k-0-PD.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3.5-122B-A10B-w4a8-A3-accuracy.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3.5-122B-A10B-w4a8-A3.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3.5-27B-w8a8-A2.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3.5-27B-w8a8-A3.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3.5-27B-w8a8-A3_weekly.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3.5-2b-310p.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3.5-397B-A17B-W8A8-mtp-A3-perf_weekly.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3.5-397B-A17B-W8A8-mtp-A3.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3.5-397B-A17B-W8A8-mtp-A3_weekly.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3.5-397B-A17B-w4a8-mtp-A2.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3.5-397B-A17B-w8a8-3.5k-1.5k-0-50-single.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3.5-397B-A17B-w8a8-64k-1k-90-50-single.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3.5-397B-w4a8_128k-1k-90-50-PD.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3.5-397B-w4a8_3.5k-1.5k-0-50-PD.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3.5-397B-w4a8_64k-1k-90-50-PD.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3.5-397B-w4a8_986k-function-PD.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3.6-27B-W8A8-310P-300I-DUO.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3.6-35B-A3B-w4a8-A3.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3.6-35B-A3B-w8a8-310p-MTP.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3.6-35B-A3B-w8a8-A3-accuracy.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3.6-35B-W8A8-310P-300I-DUO.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3.6_35B_27B_A3_acceptance_rate.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3.8-27B-w8a8-A2.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3.8-27B-w8a8-A3.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3VL-8B-310p.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3_235b_w8a8_A5.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3_235b_w8a8_A5_weekly.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3_32b_w8a8_A5.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3_32b_w8a8_A5_weekly.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3_5_35B_A3B_FP8_A5.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3_5_35B_A3B_FP8_A5_weekly.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3_5_397B_A17B_w8a8_mxfp8_A5.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3_5_397B_A17B_w8a8_mxfp8_A5_weekly.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3_6_27B_W8A8_A5.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3_6_27B_W8A8_A5_weekly.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3_6_27b_A5.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/Qwen3_6_27b_A5_weekly.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/models/configs/Qwen/qwen_3_6_27b_w8a8_A3.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/models/configs/ERNIE-4.5-21B-A3B-PT.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/models/configs/Hunyuan-A13B-Instruct.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/models/configs/InternVL3_5-8B-hf.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/models/configs/Llama-3.2-3B-Instruct.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/models/configs/Minitron-8B-Base.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/models/configs/Mixtral-8x7B-Instruct-v0.1.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/models/configs/Molmo-7B-D-0924.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/models/configs/Qwen2-Audio-7B-Instruct.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/models/configs/Qwen2.5-Math-RM-72B.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/models/configs/Qwen3-30B-A3B-W8A8.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/models/configs/Qwen3-30B-A3B.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/models/configs/Qwen3-8B-W8A8.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/models/configs/Qwen3-ASR-1.7B.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/models/configs/Qwen3-Next-80B-A3B-Instruct.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/models/configs/Qwen3-Omni-30B-A3B-Instruct.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/models/configs/Qwen3-VL-30B-A3B-Instruct.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/models/configs/Qwen3-VL-8B-Instruct-W8A8.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/models/configs/Qwen3-VL-8B-Instruct.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/models/configs/gemma-3-4b-it.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/models/configs/internlm3-8b-instruct.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/glm53flash_assets/config.json
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/glm53flash_assets/quant.json
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/glm53flash_assets/tokenizer.json
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/glm53flash_assets/tokenizer_config.json
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_fake_weight/config.json
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/eplb/core/expert_map.json
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/E2E_TEST_CASE_GUIDE.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/models/configs/accuracy.txt
  role: supporting
created_at: '2026-11-03T04:50:49Z'
updated_at: '2026-11-04T02:56:11Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend E2E配置证据矩阵：模型、并行、任务与负载选择

## 先区分场景配置与模型评估配置

选择部署/负载场景时读第一张表；选择数据集、任务和指标时读第二张表。两表末列给出固定 ceac 来源的完整仓库相对路径，与 Frontmatter 同 revision 的 `sources` 对应。`Qwen3-30B-A3B-W8A8` 在两表各有一项，分别位于 `tests/e2e/cases/models/configs/Qwen/` 与 `tests/e2e/models/configs/`；相同标识不代表相同文件或判据。

先按模型与权重格式、目标任务和 Runner 选候选，随后打开该行完整源文件，展开角色/主机变量，核最终 argv、输入输出预算与实际拓扑。遇到重名 variant、未展开变量或缺失业务检查时，保持独立配置身份并回源核对，再决定是否适合作为验收起点。

## 配置是可选择的试验定义，不是通过记录

本卡解析固定ceac提交的204份YAML/JSON配置，蒸馏模型身份、并行维度和任务集合。前178份为场景配置，20份为模型评估配置，末6份为小型模型/分词器/专家映射fixture。参数来自配置字面值，不执行脚本、环境展开、模型、评估或NPU；环境变量、所有后端实现及配置声明的硬件组合并未因此验收。

新模型先选同架构、checkpoint量化和runner的近邻场景，再核最终命令、模型/数据身份、实际设备拓扑和收集/skip，参见[测试证据选择](vllm_ascend_test_evidence_selection.md)、[多节点编排](vllm_ascend_multi_node_test_contract.md)与[结果判定](../../runbooks/validations/vllm_ascend_benchmark_verdict_contract.md)。表中TP等列只摘选命令中的显式值；空白不表示1，不推导支持；${变量}表示仍待模板/rank展开。文件名中的A2/A3/A5/310P只是测试命名，不扩大本卡platforms。

## 从模型和功能组合选择场景

| 配置标识 | 实际模型/用例数 | 显式并行与量化摘选 | 配置中的业务检查类别  固定来源完整路径 |
| --- | --- | --- | ---  --- |
| DeepSeek-V4.1-Flash-W8A8-DSpark-PCP | DeepSeek-V4.1-Flash-w8a8 / 1 | TP=2; DP=2; PCP=4; quant=ascend | accuracy  `tests/e2e/cases/features/context_parallel/DeepSeek-V4.1-Flash-W8A8-DSpark-PCP.yaml` |
| Kimi-K2.6-W4A8-PCP-DCP | Kimi-K2.6-w4a8 / 1 | TP=4; DP=2; PCP=2; DCP=8; quant=ascend | accuracy  `tests/e2e/cases/features/context_parallel/Kimi-K2.6-W4A8-PCP-DCP.yaml` |
| Qwen3-30B-A3B-VWN-eagle3-PCP | Qwen3-30B-A3B / 1 | TP=2; DP=2; PCP=2 | accuracy  `tests/e2e/cases/features/context_parallel/Qwen3-30B-A3B-VWN-eagle3-PCP.yaml` |
| glm-5.2-W4A8C8-DSpark-PCP | GLM-5.2-w4a8c8 / 1 | TP=4; DP=2; PCP=2; quant=ascend | accuracy  `tests/e2e/cases/features/context_parallel/glm-5.2-W4A8C8-DSpark-PCP.yaml` |
| DSv4-Flash-Memcache-PD-layerwise | DeepSeek-V4-Flash-w8a8-mtp / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; PCP=${CP_SIZE}; quant=ascend | accuracy,performance  `tests/e2e/cases/features/kv_pool/DSv4-Flash-Memcache-PD-layerwise.yaml` |
| DeepSeek-V4-Flash-Memcache-PD-acc | DeepSeek-V4-Flash-w8a8-mtp / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; PCP=${CP_SIZE}; quant=ascend | accuracy  `tests/e2e/cases/features/kv_pool/DeepSeek-V4-Flash-Memcache-PD-acc.yaml` |
| GLM-5.2-W8A8C8-A3-Memcache-PD | GLM-5.2-w8a8c8 / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; PCP=${CP_SIZE}; quant=ascend; KV=int8 | accuracy,performance  `tests/e2e/cases/features/kv_pool/GLM-5.2-W8A8C8-A3-Memcache-PD.yaml` |
| Qwen3.5-397B-Memcache-perf | Qwen3.5-397B-A17B-w8a8-mtp / 1 | TP=16; DP=1; quant=ascend | performance  `tests/e2e/cases/features/kv_pool/Qwen3.5-397B-Memcache-perf.yaml` |
| Qwen3.5-397B-no-Memcache-perf | Qwen3.5-397B-A17B-w8a8-mtp / 1 | TP=16; DP=1; quant=ascend | performance  `tests/e2e/cases/features/kv_pool/Qwen3.5-397B-no-Memcache-perf.yaml` |
| GLM-5.3-W8A8C8-A3-200k-PP-PD | GLM-5.3-w8a8c8 / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; PP=${PP_SIZE}; quant=ascend; KV=int8 | accuracy,performance  `tests/e2e/cases/features/pp/GLM-5.3-W8A8C8-A3-200k-PP-PD.yaml` |
| DS-V4-flash-w8a8-PD-prefix-weekly | DeepSeek-V4-Flash-w8a8-mtp / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; PCP=${CP_SIZE}; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/DeepSeek/DS-V4-flash-w8a8-PD-prefix-weekly.yaml` |
| DeepSeek-R1-W8A8-EPLB | DeepSeek-R1-0528-W8A8 / 1 | TP=1,8; DP=2,32; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/DeepSeek/DeepSeek-R1-W8A8-EPLB.yaml` |
| DeepSeek-V4-Flash-W8A8-A3-Breakable | DeepSeek-V4-Flash-w8a8-mtp / 1 | TP=4; DP=4; quant=ascend | accuracy  `tests/e2e/cases/models/configs/DeepSeek/DeepSeek-V4-Flash-W8A8-A3-Breakable.yaml` |
| DeepSeek-V4-Flash-W8A8-A3-MRV2 | DeepSeek-V4-Flash-0731-w8a8 / 1 | TP=4; DP=4; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/DeepSeek/DeepSeek-V4-Flash-W8A8-A3-MRV2.yaml` |
| DeepSeek-V4-Flash-W8A8-A3 | DeepSeek-V4-Flash-w8a8-mtp / 1 | TP=4; DP=4; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/DeepSeek/DeepSeek-V4-Flash-W8A8-A3.yaml` |
| DeepSeek-V4-Flash-w8a8-bugtest-acc | DeepSeek-V4-Flash-0731-w8a8 / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; PCP=${CP_SIZE}; quant=ascend | accuracy  `tests/e2e/cases/models/configs/DeepSeek/DeepSeek-V4-Flash-w8a8-bugtest-acc.yaml` |
| DeepSeek-V4-Flash-w8a8-sleep-wakeup | DeepSeek-V4-Flash-w8a8-mtp / 1 | TP=4; DP=4; quant=ascend | accuracy,curl_cmd  `tests/e2e/cases/models/configs/DeepSeek/DeepSeek-V4-Flash-w8a8-sleep-wakeup.yaml` |
| DeepSeek-V4-Pro-w4a8-1M-PD | DeepSeek-V4-Pro-w4a8-mtp / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; quant=ascend | performance  `tests/e2e/cases/models/configs/DeepSeek/DeepSeek-V4-Pro-w4a8-1M-PD.yaml` |
| DeepSeek-V4-Pro-w4a8-PD-no-prefix | DeepSeek-V4-Pro-w4a8-mtp / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; PCP=${CP_SIZE}; quant=ascend | performance  `tests/e2e/cases/models/configs/DeepSeek/DeepSeek-V4-Pro-w4a8-PD-no-prefix.yaml` |
| DeepSeek-V4-Pro-w4a8-prefix-cache-PD | DeepSeek-V4-Pro-w4a8-mtp / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; PCP=${CP_SIZE}; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/DeepSeek/DeepSeek-V4-Pro-w4a8-prefix-cache-PD.yaml` |
| DeepSeek-V4-Pro-w4a8-prefix-cache-PD_weekly | DeepSeek-V4-Pro-w4a8-mtp / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; PCP=${CP_SIZE}; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/DeepSeek/DeepSeek-V4-Pro-w4a8-prefix-cache-PD_weekly.yaml` |
| DeepSeek-V4-flash-w8a8-PD-no-prefix | DeepSeek-V4-Flash-w8a8-mtp / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; PCP=${CP_SIZE}; quant=ascend | performance  `tests/e2e/cases/models/configs/DeepSeek/DeepSeek-V4-flash-w8a8-PD-no-prefix.yaml` |
| DeepSeek-V4-flash-w8a8-PD-prefix-MRV2 | DeepSeek-V4-Flash-0731-w8a8 / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; PCP=${CP_SIZE}; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/DeepSeek/DeepSeek-V4-flash-w8a8-PD-prefix-MRV2.yaml` |
| DeepSeek-V4-flash-w8a8-PD-prefix | DeepSeek-V4-Flash-w8a8-mtp / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; PCP=${CP_SIZE}; quant=ascend | accuracy  `tests/e2e/cases/models/configs/DeepSeek/DeepSeek-V4-flash-w8a8-PD-prefix.yaml` |
| DeepSeek-V4.1-Flash-w8a8-PD-MRV2 | DeepSeek-V4.1-Flash-w8a8 / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; PCP=${CP_SIZE}; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/DeepSeek/DeepSeek-V4.1-Flash-w8a8-PD-MRV2.yaml` |
| DeepSeek-V4.1-Flash-w8a8-PD-prefix | DeepSeek-V4.1-Flash-w8a8 / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/DeepSeek/DeepSeek-V4.1-Flash-w8a8-PD-prefix.yaml` |
| DeepSeek_V3.1T_MTP1_128K_1K_PD | DeepSeek-V3.1-Terminus-w8a8-mtp-QuaRot / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; quant=ascend | performance  `tests/e2e/cases/models/configs/DeepSeek/DeepSeek_V3.1T_MTP1_128K_1K_PD.yaml` |
| DeepSeek_V3.1T_MTP1_3_5K_1_5K_PD | DeepSeek-V3.1-Terminus-w8a8-mtp-QuaRot / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; quant=ascend | performance  `tests/e2e/cases/models/configs/DeepSeek/DeepSeek_V3.1T_MTP1_3_5K_1_5K_PD.yaml` |
| DeepSeek_V3.1T_MTP1_PD | DeepSeek-V3.1-Terminus-w8a8-mtp-QuaRot / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; quant=ascend | accuracy  `tests/e2e/cases/models/configs/DeepSeek/DeepSeek_V3.1T_MTP1_PD.yaml` |
| DeepSeek_V3.1T_MTP3_PD | DeepSeek-V3.1-Terminus-w8a8-mtp-QuaRot / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; quant=ascend | accuracy  `tests/e2e/cases/models/configs/DeepSeek/DeepSeek_V3.1T_MTP3_PD.yaml` |
| DeepSeek_V3.1T_layerwise_PD | DeepSeek-V3.1-Terminus-w8a8-mtp-QuaRot / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; quant=ascend | accuracy  `tests/e2e/cases/models/configs/DeepSeek/DeepSeek_V3.1T_layerwise_PD.yaml` |
| DeepSeek_V31_Terminus_w4a8_w8a8_A5 | DeepSeek-V3.1-w4a4c8-mxfp4 / 10 | quant=ascend | performance  `tests/e2e/cases/models/configs/DeepSeek/DeepSeek_V31_Terminus_w4a8_w8a8_A5.yaml` |
| DeepSeek_V31_Terminus_w4a8_w8a8_A5_weekly | DeepSeek-V3.1-w4a4c8-mxfp4 / 10 | quant=ascend | performance  `tests/e2e/cases/models/configs/DeepSeek/DeepSeek_V31_Terminus_w4a8_w8a8_A5_weekly.yaml` |
| DeepSeek_V31_W4A4C8_A5 | DeepSeek-V3.1-w4a4c8-mxfp4 / 1 | quant=ascend; KV=fp8 |   `tests/e2e/cases/models/configs/DeepSeek/DeepSeek_V31_W4A4C8_A5.yaml` |
| DeepSeek_V31_W4A4C8_A5_weekly | DeepSeek-V3.1-w4a4c8-mxfp4 / 1 | quant=ascend; KV=fp8 |   `tests/e2e/cases/models/configs/DeepSeek/DeepSeek_V31_W4A4C8_A5_weekly.yaml` |
| DeepSeek_V4_Flash_A5 | DeepSeek-V4-Flash / 6 | TP=1; DP=8; KV=fp8 | accuracy,performance  `tests/e2e/cases/models/configs/DeepSeek/DeepSeek_V4_Flash_A5.yaml` |
| DeepSeek_V4_Flash_A5_weekly | DeepSeek-V4-Flash / 6 | TP=1; DP=8; KV=fp8 | accuracy,performance  `tests/e2e/cases/models/configs/DeepSeek/DeepSeek_V4_Flash_A5_weekly.yaml` |
| DeepSeek_V4_Flash_K15_dspark_A5 | DeepSeek-V4-Flash-0731 / 2 | TP=1; DP=8; quant=ascend; KV=fp8 | performance  `tests/e2e/cases/models/configs/DeepSeek/DeepSeek_V4_Flash_K15_dspark_A5.yaml` |
| acceptace_rate_deepseekv4-flash-w8a8-mtp | DeepSeek-V4-Flash-w8a8-mtp / 2 | TP=8; DP=1 | performance  `tests/e2e/cases/models/configs/DeepSeek/acceptace_rate_deepseekv4-flash-w8a8-mtp.yaml` |
| GLM-5.1-W8A8-PrefillMC2 | GLM-5.1-w8a8 / 1 | TP=16; DP=1; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/GLM/GLM-5.1-W8A8-PrefillMC2.yaml` |
| GLM-5.1-W8A8C8-128k-1k-90-50-PD | GLM-5.1-w8a8c8 / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; PCP=${CP_SIZE}; quant=ascend; KV=int8 | accuracy,performance  `tests/e2e/cases/models/configs/GLM/GLM-5.1-W8A8C8-128k-1k-90-50-PD.yaml` |
| GLM-5.1-W8A8C8-3.5k-1.5k-0-20-PD | GLM-5.1-w8a8c8 / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; PCP=${CP_SIZE}; quant=ascend | performance  `tests/e2e/cases/models/configs/GLM/GLM-5.1-W8A8C8-3.5k-1.5k-0-20-PD.yaml` |
| GLM-5.1-W8A8C8-3.5k-1.5k-0-50-PD | GLM-5.1-w8a8c8 / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; PCP=${CP_SIZE}; quant=ascend | performance  `tests/e2e/cases/models/configs/GLM/GLM-5.1-W8A8C8-3.5k-1.5k-0-50-PD.yaml` |
| GLM-5.1-W8A8C8-64k-1k-90-50-PD | GLM-5.1-w8a8c8 / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; PCP=${CP_SIZE}; quant=ascend | performance  `tests/e2e/cases/models/configs/GLM/GLM-5.1-W8A8C8-64k-1k-90-50-PD.yaml` |
| GLM-5.1-W8A8C8-A3_128k_90_50 | GLM-5.1-w8a8c8 / 1 | TP=1; DP=8; PCP=4; quant=ascend; KV=int8 | performance  `tests/e2e/cases/models/configs/GLM/GLM-5.1-W8A8C8-A3_128k_90_50.yaml` |
| GLM-5.1-W8A8C8-A3_198k_function | GLM-5.1-w8a8c8 / 1 | TP=1; DP=8; PCP=4; quant=ascend; KV=int8 | accuracy,performance  `tests/e2e/cases/models/configs/GLM/GLM-5.1-W8A8C8-A3_198k_function.yaml` |
| GLM-5.1-W8A8C8-A3_3.5k_1.5k_0_20 | GLM-5.1-w8a8c8 / 1 | TP=1; DP=2; PCP=16; quant=ascend | performance  `tests/e2e/cases/models/configs/GLM/GLM-5.1-W8A8C8-A3_3.5k_1.5k_0_20.yaml` |
| GLM-5.1-W8A8C8-A3_3.5k_1.5k_0_50 | GLM-5.1-w8a8c8 / 1 | TP=1; DP=8; PCP=4; quant=ascend | performance  `tests/e2e/cases/models/configs/GLM/GLM-5.1-W8A8C8-A3_3.5k_1.5k_0_50.yaml` |
| GLM-5.1-W8A8C8-A3_64k_90_50 | GLM-5.1-w8a8c8 / 1 | TP=1; DP=8; PCP=4; quant=ascend | performance  `tests/e2e/cases/models/configs/GLM/GLM-5.1-W8A8C8-A3_64k_90_50.yaml` |
| GLM-5.1-w8a8c8-MTP-offload-test-perf | GLM-5.1-w8a8c8-MTP / 1 | TP=8; DP=2; quant=ascend | performance  `tests/e2e/cases/models/configs/GLM/GLM-5.1-w8a8c8-MTP-offload-test-perf.yaml` |
| GLM-5.2-W4A8-DSpark-A3-V2 | GLM-5.2-w4a8 / 1 | TP=8; DP=2; quant=ascend | spec_decode  `tests/e2e/cases/models/configs/GLM/GLM-5.2-W4A8-DSpark-A3-V2.yaml` |
| GLM-5.2-W4A8-DSpark-A3 | GLM-5.2-w4a8 / 1 | TP=8; DP=2; quant=ascend | spec_decode  `tests/e2e/cases/models/configs/GLM/GLM-5.2-W4A8-DSpark-A3.yaml` |
| GLM-5.2-W4A8-MTP-A3-V2 | GLM-5.2-w4a8 / 1 | TP=8; DP=2; quant=ascend | spec_decode  `tests/e2e/cases/models/configs/GLM/GLM-5.2-W4A8-MTP-A3-V2.yaml` |
| GLM-5.2-W4A8-MTP-A3 | GLM-5.2-w4a8 / 1 | TP=8; DP=2; quant=ascend | spec_decode  `tests/e2e/cases/models/configs/GLM/GLM-5.2-W4A8-MTP-A3.yaml` |
| GLM-5.2-W4A8C8-1M-PD-DCP | GLM-5.2-w4a8c8 / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; PP=1; PCP=${CP_SIZE}; DCP=8; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/GLM/GLM-5.2-W4A8C8-1M-PD-DCP.yaml` |
| GLM-5.2-W4A8C8-SFA-DCP | GLM-5.2-w4a8c8 / 1 | TP=1; DP=1; PP=1; PCP=16; DCP=16; quant=ascend | accuracy  `tests/e2e/cases/models/configs/GLM/GLM-5.2-W4A8C8-SFA-DCP.yaml` |
| GLM-5.2-W8A8C8-128k-1k-90-50-PD | GLM-5.2-w8a8c8 / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; PCP=${CP_SIZE}; quant=ascend; KV=int8 | accuracy,performance  `tests/e2e/cases/models/configs/GLM/GLM-5.2-W8A8C8-128k-1k-90-50-PD.yaml` |
| GLM-5.2-W8A8C8-3.5k-1.5k-0-20-PD | GLM-5.2-w8a8c8 / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; PCP=${CP_SIZE}; quant=ascend | performance  `tests/e2e/cases/models/configs/GLM/GLM-5.2-W8A8C8-3.5k-1.5k-0-20-PD.yaml` |
| GLM-5.2-W8A8C8-3.5k-1.5k-0-50-PD | GLM-5.2-w8a8c8 / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; PCP=${CP_SIZE}; quant=ascend | performance  `tests/e2e/cases/models/configs/GLM/GLM-5.2-W8A8C8-3.5k-1.5k-0-50-PD.yaml` |
| GLM-5.2-W8A8C8-64k-1k-90-50-PD | GLM-5.2-w8a8c8 / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; PCP=${CP_SIZE}; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/GLM/GLM-5.2-W8A8C8-64k-1k-90-50-PD.yaml` |
| GLM-5.2-W8A8C8-A3_128k-static-super-kernels | GLM-5.2-w8a8c8 / 1 | TP=4; DP=8; quant=ascend; KV=int8 | performance  `tests/e2e/cases/models/configs/GLM/GLM-5.2-W8A8C8-A3_128k-static-super-kernels.yaml` |
| GLM-5.2-W8A8C8-A3_128k_90_50 | GLM-5.2-w8a8c8 / 1 | TP=1; DP=8; PCP=4; quant=ascend | performance  `tests/e2e/cases/models/configs/GLM/GLM-5.2-W8A8C8-A3_128k_90_50.yaml` |
| GLM-5.2-W8A8C8-A3_198k_function | GLM-5.2-w8a8c8 / 1 | TP=1; DP=8; PCP=4; quant=ascend; KV=int8 | accuracy,performance  `tests/e2e/cases/models/configs/GLM/GLM-5.2-W8A8C8-A3_198k_function.yaml` |
| GLM-5.2-W8A8C8-A3_3.5k_1.5k_0_20 | GLM-5.2-w8a8c8 / 1 | TP=1; DP=2; PCP=16; quant=ascend | performance  `tests/e2e/cases/models/configs/GLM/GLM-5.2-W8A8C8-A3_3.5k_1.5k_0_20.yaml` |
| GLM-5.2-W8A8C8-A3_3.5k_1.5k_0_50 | GLM-5.2-w8a8c8 / 1 | TP=1; DP=8; PCP=4; quant=ascend | performance  `tests/e2e/cases/models/configs/GLM/GLM-5.2-W8A8C8-A3_3.5k_1.5k_0_50.yaml` |
| GLM-5.2-W8A8C8-A3_64k_90_50 | GLM-5.2-w8a8c8 / 1 | TP=1; DP=8; PCP=4; quant=ascend | performance  `tests/e2e/cases/models/configs/GLM/GLM-5.2-W8A8C8-A3_64k_90_50.yaml` |
| GLM-5.3-Flash-W8A8-130k-PD | GLM-5.3-Flash-w8a8 / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; PCP=${CP_SIZE}; quant=ascend; KV=int8 | accuracy,performance  `tests/e2e/cases/models/configs/GLM/GLM-5.3-Flash-W8A8-130k-PD.yaml` |
| GLM-5_1-W8A8_A3_weekly | GLM-5.1-w8a8 / 4 | TP=16; DP=1; quant=ascend | performance  `tests/e2e/cases/models/configs/GLM/GLM-5_1-W8A8_A3_weekly.yaml` |
| GLM5_1-W8A8-A2-dual-nodes | GLM-5.1-w8a8 / 1 | TP=8; DP=2; quant=ascend | performance  `tests/e2e/cases/models/configs/GLM/GLM5_1-W8A8-A2-dual-nodes.yaml` |
| GLM5_1-W8A8-A3-dual-nodes | GLM-5.1-w8a8 / 1 | TP=16; DP=2; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/GLM/GLM5_1-W8A8-A3-dual-nodes.yaml` |
| GLM5_1-W8A8-EP | GLM-5.1-w8a8 / 1 | TP=4,8; DP=4,8; quant=ascend | performance  `tests/e2e/cases/models/configs/GLM/GLM5_1-W8A8-EP.yaml` |
| GLM5_1_W4A4_A5 | GLM-5.1-w4a4c8-mxfp4 / 1 | TP=2; DP=1; PCP=4; quant=ascend; KV=fp8 |   `tests/e2e/cases/models/configs/GLM/GLM5_1_W4A4_A5.yaml` |
| GLM5_1_W4A4_A5_weekly | GLM-5.1-w4a4c8-mxfp4 / 1 | TP=1; DP=1; PCP=8; quant=ascend |   `tests/e2e/cases/models/configs/GLM/GLM5_1_W4A4_A5_weekly.yaml` |
| GLM5_2-W8A8-A3-dual-nodes | GLM-5.2-w8a8 / 1 | TP=16; DP=2; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/GLM/GLM5_2-W8A8-A3-dual-nodes.yaml` |
| GLM5_3-W8A8-A3-dual-nodes | GLM-5.3-w8a8c8 / 1 | TP=1; DP=8; PCP=4; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/GLM/GLM5_3-W8A8-A3-dual-nodes.yaml` |
| GLM_5_1_PD_in32k_bs16-0 | GLM-5.1-w8a8 / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; PCP=${CP_SIZE}; quant=ascend | performance  `tests/e2e/cases/models/configs/GLM/GLM_5_1_PD_in32k_bs16-0.yaml` |
| GLM_5_1_PD_in32k_bs20-90 | GLM-5.1-w8a8 / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; PCP=${CP_SIZE}; quant=ascend | performance  `tests/e2e/cases/models/configs/GLM/GLM_5_1_PD_in32k_bs20-90.yaml` |
| GLM_5_1_PD_in64k_bs16-90 | GLM-5.1-w8a8 / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; PCP=${CP_SIZE}; quant=ascend | performance  `tests/e2e/cases/models/configs/GLM/GLM_5_1_PD_in64k_bs16-90.yaml` |
| Gemma4-31B-Dense | gemma-4-31B-it / 1 | TP=4 | accuracy  `tests/e2e/cases/models/configs/Gemma/Gemma4-31B-Dense.yaml` |
| Gemma4 | gemma-4-26B-A4B-it / 1 | TP=4 | accuracy  `tests/e2e/cases/models/configs/Gemma/Gemma4.yaml` |
| Gemma4_26B_A4B_W4A4_A5 | gemma-4-26B-A4B-it-w4a4-mxfp4 / 1 | TP=4; quant=ascend | accuracy  `tests/e2e/cases/models/configs/Gemma/Gemma4_26B_A4B_W4A4_A5.yaml` |
| Gemma4_31B_W4A4_A5 | gemma-4-31B-it-w4a4-mxfp4 / 1 | TP=4; quant=ascend | accuracy  `tests/e2e/cases/models/configs/Gemma/Gemma4_31B_W4A4_A5.yaml` |
| Hy3-preview | Hy3-preview / 1 | TP=16 | accuracy  `tests/e2e/cases/models/configs/Hunyuan/Hy3-preview.yaml` |
| Kimi-K2.5-W4A8-128k-1k-TPOT50 | Kimi-K2.5-W4A8 / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/Kimi/Kimi-K2.5-W4A8-128k-1k-TPOT50.yaml` |
| Kimi-K2.5-W4A8-16k-1k-TPOT50 | Kimi-K2.5-W4A8 / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; quant=ascend | performance  `tests/e2e/cases/models/configs/Kimi/Kimi-K2.5-W4A8-16k-1k-TPOT50.yaml` |
| Kimi-K2.6-W4A8-128k-1k-TPOT50-PD | Kimi-K2.6-w4a8 / 1 | TP=${TP_SIZE}; DP=${DP_SIZE} | accuracy,performance  `tests/e2e/cases/models/configs/Kimi/Kimi-K2.6-W4A8-128k-1k-TPOT50-PD.yaml` |
| Kimi-K2.6-W4A8-254k-1k-TPOT20-PD | Kimi-K2.6-w4a8 / 1 | TP=16 | performance  `tests/e2e/cases/models/configs/Kimi/Kimi-K2.6-W4A8-254k-1k-TPOT20-PD.yaml` |
| Kimi-K2.6-W4A8-3.5k-1.5k-TPOT50-PD | Kimi-K2.6-w4a8 / 1 | TP=${TP_SIZE}; DP=${DP_SIZE} | performance  `tests/e2e/cases/models/configs/Kimi/Kimi-K2.6-W4A8-3.5k-1.5k-TPOT50-PD.yaml` |
| Kimi-K2.6-W4A8-64k-1k-TPOT50-PD | Kimi-K2.6-w4a8 / 1 | TP=${TP_SIZE}; DP=${DP_SIZE} | accuracy,performance  `tests/e2e/cases/models/configs/Kimi/Kimi-K2.6-W4A8-64k-1k-TPOT50-PD.yaml` |
| Kimi-K2.6-w4a8-A3 | Kimi-K2.6-w4a8 / 1 | TP=8; DP=2; quant=ascend | performance,spec_decode  `tests/e2e/cases/models/configs/Kimi/Kimi-K2.6-w4a8-A3.yaml` |
| Kimi-K2.6-w4a8-A3_weekly | Kimi-K2.6-w4a8 / 4 | TP=16,8; DP=1,2; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/Kimi/Kimi-K2.6-w4a8-A3_weekly.yaml` |
| Kimi-K2.7-W4A8-128k-1k-TPOT50-PD | Kimi-K2.7-Code-w4a8 / 1 | TP=${TP_SIZE}; DP=${DP_SIZE} | accuracy,performance  `tests/e2e/cases/models/configs/Kimi/Kimi-K2.7-W4A8-128k-1k-TPOT50-PD.yaml` |
| Kimi-K2.7-W4A8-254k-1k-TPOT20-PD | Kimi-K2.7-Code-w4a8 / 1 | TP=16 | performance  `tests/e2e/cases/models/configs/Kimi/Kimi-K2.7-W4A8-254k-1k-TPOT20-PD.yaml` |
| Kimi-K2.7-W4A8-3.5k-1.5k-TPOT50-PD | Kimi-K2.7-Code-w4a8 / 1 | TP=${TP_SIZE}; DP=${DP_SIZE} | performance  `tests/e2e/cases/models/configs/Kimi/Kimi-K2.7-W4A8-3.5k-1.5k-TPOT50-PD.yaml` |
| Kimi-K2.7-W4A8-64k-1k-TPOT50-PD | Kimi-K2.7-Code-w4a8 / 1 | TP=${TP_SIZE}; DP=${DP_SIZE} | performance  `tests/e2e/cases/models/configs/Kimi/Kimi-K2.7-W4A8-64k-1k-TPOT50-PD.yaml` |
| Kimi-K2.7-w4a8-A3 | Kimi-K2.7-Code-w4a8 / 5 | TP=16,8; DP=1,2; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/Kimi/Kimi-K2.7-w4a8-A3.yaml` |
| Kimi-K2_5-W4A8-A2-dual-nodes | Kimi-K2.5-W4A8 / 1 | TP=8; DP=2; quant=ascend | performance  `tests/e2e/cases/models/configs/Kimi/Kimi-K2_5-W4A8-A2-dual-nodes.yaml` |
| KimiK26_w4a4c8_A5 | Kimi-K2.6-w4a4c8-0605-dv3 / 6 | TP=4; DP=2; quant=ascend; KV=fp8 |   `tests/e2e/cases/models/configs/Kimi/KimiK26_w4a4c8_A5.yaml` |
| KimiK26_w4a4c8_A5_weekly | Kimi-K2.6-w4a4c8-0605-dv3 / 6 | TP=4; DP=2; quant=ascend; KV=fp8 |   `tests/e2e/cases/models/configs/Kimi/KimiK26_w4a4c8_A5_weekly.yaml` |
| kimi-k2.6_max_model_len | Kimi-K2.6-w4a8 / 3 | TP=16; DP=1; quant=ascend | performance  `tests/e2e/cases/models/configs/Kimi/kimi-k2.6_max_model_len.yaml` |
| MiniMax-M2.5-W8A8-A3 | MiniMax-M2.5-w8a8-QuaRot / 1 | TP=4; DP=4; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/MiniMax/MiniMax-M2.5-W8A8-A3.yaml` |
| MiniMax-M2.5-w8a8-QuaRot-A3 | MiniMax-M2.5-w8a8-QuaRot / 1 | TP=8; DP=1; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/MiniMax/MiniMax-M2.5-w8a8-QuaRot-A3.yaml` |
| MiniMax-M2.5-w8a8-QuaRot-step | MiniMax-M2.5-w8a8-QuaRot / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; quant=ascend | performance  `tests/e2e/cases/models/configs/MiniMax/MiniMax-M2.5-w8a8-QuaRot-step.yaml` |
| MiniMax-M3-BF16-A3 | MiniMax-M3 / 1 | TP=8; DP=2 | accuracy,performance  `tests/e2e/cases/models/configs/MiniMax/MiniMax-M3-BF16-A3.yaml` |
| MiniMax-M3-W8A8-A3-EAGLE3 | MiniMax-M3-w8a8-0626 / 1 | TP=4; DP=4; quant=ascend | accuracy,spec_decode  `tests/e2e/cases/models/configs/MiniMax/MiniMax-M3-W8A8-A3-EAGLE3.yaml` |
| MiniMax-PD-in32k-bs4-1 | MiniMax-M2.5-w8a8-QuaRot / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; quant=ascend | performance  `tests/e2e/cases/models/configs/MiniMax/MiniMax-PD-in32k-bs4-1.yaml` |
| Minimax_M2.7_w8a8_A3 | MiniMax-M2.7-w8a8-QuaRot / 4 | TP=8; DP=2; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/MiniMax/Minimax_M2.7_w8a8_A3.yaml` |
| Minimax_m2.7_in128k_1k_prefix90_tpot50 | MiniMax-M2.7-w8a8-QuaRot / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/MiniMax/Minimax_m2.7_in128k_1k_prefix90_tpot50.yaml` |
| Minimax_m2.7_in198_prefix99 | MiniMax-M2.7-w8a8-QuaRot / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; quant=ascend | performance  `tests/e2e/cases/models/configs/MiniMax/Minimax_m2.7_in198_prefix99.yaml` |
| Minimax_m2.7_in3_5_tpot20 | MiniMax-M2.7-w8a8-QuaRot / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; quant=ascend | performance  `tests/e2e/cases/models/configs/MiniMax/Minimax_m2.7_in3_5_tpot20.yaml` |
| Minimax_m2.7_in3_5_tpot50 | MiniMax-M2.7-w8a8-QuaRot / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; quant=ascend | performance  `tests/e2e/cases/models/configs/MiniMax/Minimax_m2.7_in3_5_tpot50.yaml` |
| Minimax_m2.7_in64k_1k_prefix90_tpot50 | MiniMax-M2.7-w8a8-QuaRot / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; quant=ascend | performance  `tests/e2e/cases/models/configs/MiniMax/Minimax_m2.7_in64k_1k_prefix90_tpot50.yaml` |
| Prefix-Cache-Qwen3-32B-Int8 | Qwen3-32B-W8A8-QuaRot / 1 | TP=4; quant=ascend | performance  `tests/e2e/cases/models/configs/Qwen/Prefix-Cache-Qwen3-32B-Int8.yaml` |
| QWEN3_235B_PD_3_5K_1_5k | Qwen3-235B-A22B-W8A8 / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/Qwen/QWEN3_235B_PD_3_5K_1_5k.yaml` |
| Qwen-3.5-397B-A17B-W8A8-PD | Qwen3.5-397B-A17B-w8a8-mtp / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; quant=ascend | accuracy  `tests/e2e/cases/models/configs/Qwen/Qwen-3.5-397B-A17B-W8A8-PD.yaml` |
| Qwen2.5-VL-7B-Instruct-EPD | Qwen2.5-VL-7B-Instruct / 1 |  | accuracy,performance  `tests/e2e/cases/models/configs/Qwen/Qwen2.5-VL-7B-Instruct-EPD.yaml` |
| Qwen3-14B-w8a8sc-310p | Qwen3-14B-w8a8sc-310-vllm-tp1 / 1 | TP=1; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/Qwen/Qwen3-14B-w8a8sc-310p.yaml` |
| Qwen3-235B-A22B-A2 | Qwen3-235B-A22B / 1 | TP=8; DP=2 | accuracy,performance  `tests/e2e/cases/models/configs/Qwen/Qwen3-235B-A22B-A2.yaml` |
| Qwen3-235B-A22B-W8A8_piecewise_fullgraph_A3 | Qwen3-235B-A22B-w8a8-QuaRot / 2 | TP=4; DP=4; quant=ascend | accuracy  `tests/e2e/cases/models/configs/Qwen/Qwen3-235B-A22B-W8A8_piecewise_fullgraph_A3.yaml` |
| Qwen3-30B-A3B-BF16-A2 | Qwen3-30B-A3B / 1 | TP=4 | performance  `tests/e2e/cases/models/configs/Qwen/Qwen3-30B-A3B-BF16-A2.yaml` |
| Qwen3-30B-A3B-W4A8-llm-compressor | Qwen3-30B-A3B-quantized.w4a8 / 1 | TP=2 | accuracy  `tests/e2e/cases/models/configs/Qwen/Qwen3-30B-A3B-W4A8-llm-compressor.yaml` |
| Qwen3-30B-A3B-W8A8-A2 | Qwen3-30B-A3B-w8a8 / 1 | TP=4 | performance  `tests/e2e/cases/models/configs/Qwen/Qwen3-30B-A3B-W8A8-A2.yaml` |
| Qwen3-30B-A3B-W8A8-offload-test-acc | Qwen3-30B-A3B-W8A8 / 1 | TP=4 | accuracy  `tests/e2e/cases/models/configs/Qwen/Qwen3-30B-A3B-W8A8-offload-test-acc.yaml` |
| Qwen3-30B-A3B-W8A8 | Qwen3-30B-A3B-W8A8 / 1 | TP=1 | performance  `tests/e2e/cases/models/configs/Qwen/Qwen3-30B-A3B-W8A8.yaml` |
| Qwen3-30B-QuaRot-eagle3 | Qwen3-30B-A3B-W8A8-QuaRot / 1 | TP=2 | performance  `tests/e2e/cases/models/configs/Qwen/Qwen3-30B-QuaRot-eagle3.yaml` |
| Qwen3-32B-Int8-A2 | Qwen3-32B-W8A8-QuaRot / 1 | TP=4; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/Qwen/Qwen3-32B-Int8-A2.yaml` |
| Qwen3-32B-Int8 | Qwen3-32B-W8A8-QuaRot / 2 | TP=4; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/Qwen/Qwen3-32B-Int8.yaml` |
| Qwen3-32B-QuaRot-eagle3 | Qwen3-32B-W8A8-QuaRot / 1 | TP=2 | performance  `tests/e2e/cases/models/configs/Qwen/Qwen3-32B-QuaRot-eagle3.yaml` |
| Qwen3-32B-W8A8C8-A3 | Qwen3-32B-w8a8c8 / 2 | TP=4; KV=int8 | accuracy  `tests/e2e/cases/models/configs/Qwen/Qwen3-32B-W8A8C8-A3.yaml` |
| Qwen3-32B-w8a8sc-310p | Qwen3-32B-w8a8sc-310-vllm-tp4 / 1 | TP=4; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/Qwen/Qwen3-32B-w8a8sc-310p.yaml` |
| Qwen3-32B | Qwen3-32B / 1 | TP=4 | accuracy,performance  `tests/e2e/cases/models/configs/Qwen/Qwen3-32B.yaml` |
| Qwen3-8B-w8a8sc-310p | Qwen3-8B-w8a8sc-310-vllm-tp1 / 1 | TP=1; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/Qwen/Qwen3-8B-w8a8sc-310p.yaml` |
| Qwen3-Coder-30B-A3B-Instruct-test-acc | Qwen3-Coder-30B-A3B-Instruct / 1 | TP=4; DP=1 | accuracy  `tests/e2e/cases/models/configs/Qwen/Qwen3-Coder-30B-A3B-Instruct-test-acc.yaml` |
| Qwen3-VL-32B-Instruct-W8A8 | Qwen3-VL-32B-Instruct-w8a8-QuaRot / 1 | TP=2; quant=ascend | accuracy  `tests/e2e/cases/models/configs/Qwen/Qwen3-VL-32B-Instruct-W8A8.yaml` |
| Qwen3.5-122B-A10B-W8A8-A2 | Qwen3.5-122B-A10B-w8a8-mtp / 1 | TP=8; DP=1; quant=ascend | performance  `tests/e2e/cases/models/configs/Qwen/Qwen3.5-122B-A10B-W8A8-A2.yaml` |
| Qwen3.5-122B-A10B-W8A8-A3 | Qwen3.5-122B-A10B-w8a8-mtp / 1 | TP=4; DP=1; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/Qwen/Qwen3.5-122B-A10B-W8A8-A3.yaml` |
| Qwen3.5-122B-A10B-W8A8-A3_weekly | Qwen3.5-122B-A10B-w8a8-mtp / 7 | TP=4; DP=1; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/Qwen/Qwen3.5-122B-A10B-W8A8-A3_weekly.yaml` |
| Qwen3.5-122B-A10B-w4a8-128k-1k-PD | Qwen3.5-122B-A10B-w4a8 / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; quant=ascend | performance  `tests/e2e/cases/models/configs/Qwen/Qwen3.5-122B-A10B-w4a8-128k-1k-PD.yaml` |
| Qwen3.5-122B-A10B-w4a8-16k-1k-PD | Qwen3.5-122B-A10B-w4a8 / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; quant=ascend | performance  `tests/e2e/cases/models/configs/Qwen/Qwen3.5-122B-A10B-w4a8-16k-1k-PD.yaml` |
| Qwen3.5-122B-A10B-w4a8-984k-1k-0-PD | Qwen3.5-122B-A10B-w4a8 / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; quant=ascend | performance  `tests/e2e/cases/models/configs/Qwen/Qwen3.5-122B-A10B-w4a8-984k-1k-0-PD.yaml` |
| Qwen3.5-122B-A10B-w4a8-A3-accuracy | Qwen3.5-122B-A10B-w4a8 / 1 | TP=16; DP=1; quant=ascend | accuracy  `tests/e2e/cases/models/configs/Qwen/Qwen3.5-122B-A10B-w4a8-A3-accuracy.yaml` |
| Qwen3.5-122B-A10B-w4a8-A3 | Qwen3.5-122B-A10B-w4a8 / 3 | TP=16; quant=ascend | performance  `tests/e2e/cases/models/configs/Qwen/Qwen3.5-122B-A10B-w4a8-A3.yaml` |
| Qwen3.5-27B-w8a8-A2 | Qwen3.5-27B-w8a8-mtp / 1 | TP=2; quant=ascend | performance  `tests/e2e/cases/models/configs/Qwen/Qwen3.5-27B-w8a8-A2.yaml` |
| Qwen3.5-27B-w8a8-A3 | Qwen3.5-27B-w8a8-mtp / 1 | TP=2; DP=1; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/Qwen/Qwen3.5-27B-w8a8-A3.yaml` |
| Qwen3.5-27B-w8a8-A3_weekly | Qwen3.5-27B-w8a8-mtp / 12 | TP=2; DP=1; quant=ascend | performance  `tests/e2e/cases/models/configs/Qwen/Qwen3.5-27B-w8a8-A3_weekly.yaml` |
| Qwen3.5-2b-310p | Qwen3.5-2B / 2 |  | accuracy,performance  `tests/e2e/cases/models/configs/Qwen/Qwen3.5-2b-310p.yaml` |
| Qwen3.5-397B-A17B-W8A8-mtp-A3-perf_weekly | Qwen3.5-397B-A17B-w8a8-mtp / 1 | TP=16; DP=1; quant=ascend | performance  `tests/e2e/cases/models/configs/Qwen/Qwen3.5-397B-A17B-W8A8-mtp-A3-perf_weekly.yaml` |
| Qwen3.5-397B-A17B-W8A8-mtp-A3 | Qwen3.5-397B-A17B-w8a8-mtp / 1 | TP=16; DP=1; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/Qwen/Qwen3.5-397B-A17B-W8A8-mtp-A3.yaml` |
| Qwen3.5-397B-A17B-W8A8-mtp-A3_weekly | Qwen3.5-397B-A17B-w8a8-mtp / 12 | TP=16; DP=1; quant=ascend | performance  `tests/e2e/cases/models/configs/Qwen/Qwen3.5-397B-A17B-W8A8-mtp-A3_weekly.yaml` |
| Qwen3.5-397B-A17B-w4a8-mtp-A2 | Qwen3.5-397B-A17B-w4a8-mtp / 1 | TP=8; DP=1; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/Qwen/Qwen3.5-397B-A17B-w4a8-mtp-A2.yaml` |
| Qwen3.5-397B-A17B-w8a8-3.5k-1.5k-0-50-single | Qwen3.5-397B-A17B-w8a8-mtp / 1 | TP=16; DP=1; quant=ascend | performance  `tests/e2e/cases/models/configs/Qwen/Qwen3.5-397B-A17B-w8a8-3.5k-1.5k-0-50-single.yaml` |
| Qwen3.5-397B-A17B-w8a8-64k-1k-90-50-single | Qwen3.5-397B-A17B-w8a8-mtp / 1 | TP=16; DP=1; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/Qwen/Qwen3.5-397B-A17B-w8a8-64k-1k-90-50-single.yaml` |
| Qwen3.5-397B-w4a8_128k-1k-90-50-PD | Qwen3.5-397B-A17B-w4a8-mtp / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/Qwen/Qwen3.5-397B-w4a8_128k-1k-90-50-PD.yaml` |
| Qwen3.5-397B-w4a8_3.5k-1.5k-0-50-PD | Qwen3.5-397B-A17B-w4a8-mtp / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; quant=ascend | performance  `tests/e2e/cases/models/configs/Qwen/Qwen3.5-397B-w4a8_3.5k-1.5k-0-50-PD.yaml` |
| Qwen3.5-397B-w4a8_64k-1k-90-50-PD | Qwen3.5-397B-A17B-w4a8-mtp / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; quant=ascend | performance  `tests/e2e/cases/models/configs/Qwen/Qwen3.5-397B-w4a8_64k-1k-90-50-PD.yaml` |
| Qwen3.5-397B-w4a8_986k-function-PD | Qwen3.5-397B-A17B-w4a8-mtp / 1 | TP=${TP_SIZE}; DP=${DP_SIZE}; quant=ascend | performance  `tests/e2e/cases/models/configs/Qwen/Qwen3.5-397B-w4a8_986k-function-PD.yaml` |
| Qwen3.6-27B-W8A8-310P-300I-DUO | Qwen3.6-27B-W8A8-310P / 1 | TP=2; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/Qwen/Qwen3.6-27B-W8A8-310P-300I-DUO.yaml` |
| Qwen3.6-35B-A3B-w4a8-A3 | Qwen3.6-35B-A3B-w4a8 / 3 | TP=2; DP=1; quant=ascend | performance  `tests/e2e/cases/models/configs/Qwen/Qwen3.6-35B-A3B-w4a8-A3.yaml` |
| Qwen3.6-35B-A3B-w8a8-310p-MTP | Qwen3.6-35B-A3B-w8a8 / 1 | TP=4 | accuracy,performance  `tests/e2e/cases/models/configs/Qwen/Qwen3.6-35B-A3B-w8a8-310p-MTP.yaml` |
| Qwen3.6-35B-A3B-w8a8-A3-accuracy | Qwen3.6-35B-A3B-w8a8 / 1 | TP=2; quant=ascend | accuracy  `tests/e2e/cases/models/configs/Qwen/Qwen3.6-35B-A3B-w8a8-A3-accuracy.yaml` |
| Qwen3.6-35B-W8A8-310P-300I-DUO | Qwen3.6-35B-A3B-w8a8 / 1 | TP=4 | performance  `tests/e2e/cases/models/configs/Qwen/Qwen3.6-35B-W8A8-310P-300I-DUO.yaml` |
| Qwen3.6_35B_27B_A3_acceptance_rate | Qwen3.6-35B-A3B-w8a8,Qwen3.6-27B / 2 | TP=2; DP=1 | performance  `tests/e2e/cases/models/configs/Qwen/Qwen3.6_35B_27B_A3_acceptance_rate.yaml` |
| Qwen3.8-27B-w8a8-A2 | Qwen3.8-27B-w8a8 / 1 | TP=2; DP=1; quant=ascend | performance  `tests/e2e/cases/models/configs/Qwen/Qwen3.8-27B-w8a8-A2.yaml` |
| Qwen3.8-27B-w8a8-A3 | Qwen3.8-27B-w8a8 / 1 | TP=2; DP=1; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/Qwen/Qwen3.8-27B-w8a8-A3.yaml` |
| Qwen3VL-8B-310p | Qwen3-VL-8B-Instruct-w8a8sc-310-vllm-tp1 / 2 | TP=1; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/Qwen/Qwen3VL-8B-310p.yaml` |
| Qwen3_235b_w8a8_A5 | Qwen3-235B-A22B-w8a8-mxfp8 / 1 | quant=ascend | accuracy  `tests/e2e/cases/models/configs/Qwen/Qwen3_235b_w8a8_A5.yaml` |
| Qwen3_235b_w8a8_A5_weekly | Qwen3-235B-A22B-w8a8-mxfp8 / 1 | quant=ascend | accuracy  `tests/e2e/cases/models/configs/Qwen/Qwen3_235b_w8a8_A5_weekly.yaml` |
| Qwen3_32b_w8a8_A5 | Qwen3-32B-w8a8-mxfp8 / 1 | quant=ascend | accuracy  `tests/e2e/cases/models/configs/Qwen/Qwen3_32b_w8a8_A5.yaml` |
| Qwen3_32b_w8a8_A5_weekly | Qwen3-32B-w8a8-mxfp8 / 1 | quant=ascend | accuracy  `tests/e2e/cases/models/configs/Qwen/Qwen3_32b_w8a8_A5_weekly.yaml` |
| Qwen3_5_35B_A3B_FP8_A5 | Qwen3.5-35B-A3B-FP8-dynamic / 1 | TP=2; DP=1 | accuracy  `tests/e2e/cases/models/configs/Qwen/Qwen3_5_35B_A3B_FP8_A5.yaml` |
| Qwen3_5_35B_A3B_FP8_A5_weekly | Qwen3.5-35B-A3B-FP8-dynamic / 1 | TP=2; DP=1 | accuracy  `tests/e2e/cases/models/configs/Qwen/Qwen3_5_35B_A3B_FP8_A5_weekly.yaml` |
| Qwen3_5_397B_A17B_w8a8_mxfp8_A5 | Qwen3.5-397B-A17B-w8a8-mxfp8 / 2 | TP=4; DP=1; PCP=2; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/Qwen/Qwen3_5_397B_A17B_w8a8_mxfp8_A5.yaml` |
| Qwen3_5_397B_A17B_w8a8_mxfp8_A5_weekly | Qwen3.5-397B-A17B-w8a8-mxfp8 / 2 | TP=4; DP=1; PCP=2; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/Qwen/Qwen3_5_397B_A17B_w8a8_mxfp8_A5_weekly.yaml` |
| Qwen3_6_27B_W8A8_A5 | Qwen3.6-27B-w8a8-mxfp8 / 6 | TP=4; DP=1; quant=ascend |   `tests/e2e/cases/models/configs/Qwen/Qwen3_6_27B_W8A8_A5.yaml` |
| Qwen3_6_27B_W8A8_A5_weekly | Qwen3.6-27B-w8a8-mxfp8 / 6 | TP=4; DP=1; quant=ascend |   `tests/e2e/cases/models/configs/Qwen/Qwen3_6_27B_W8A8_A5_weekly.yaml` |
| Qwen3_6_27b_A5 | Qwen3.6-27B / 1 | TP=4; DP=1 | performance  `tests/e2e/cases/models/configs/Qwen/Qwen3_6_27b_A5.yaml` |
| Qwen3_6_27b_A5_weekly | Qwen3.6-27B / 1 | TP=4; DP=1 | performance  `tests/e2e/cases/models/configs/Qwen/Qwen3_6_27b_A5_weekly.yaml` |
| qwen_3_6_27b_w8a8_A3 | Qwen3.6-27B-w8a8 / 5 | TP=2; DP=1; quant=ascend | accuracy,performance  `tests/e2e/cases/models/configs/Qwen/qwen_3_6_27b_w8a8_A3.yaml` |

## 模型评估是任务和指标，不是泛化的文本精度

| 模型配置 | 后端与显式TP | 任务及配置目标值 | fewshot / chat模板 / batch  固定来源完整路径 |
| --- | --- | --- | ---  --- |
| ERNIE-4.5-21B-A3B-PT | vllm,TP=1 | gsm8k:exact_match,flexible-extract=0.71 | 5 / True / auto  `tests/e2e/models/configs/ERNIE-4.5-21B-A3B-PT.yaml` |
| Hunyuan-A13B-Instruct | vllm,TP=4 | gsm8k:exact_match,strict-match=0.37,exact_match,flexible-extract=0.28 | 5 / False / auto  `tests/e2e/models/configs/Hunyuan-A13B-Instruct.yaml` |
| InternVL3_5-8B-hf | vllm-vlm,TP=1 | mmmu_val:acc,none=0.58 | 0 / False / auto  `tests/e2e/models/configs/InternVL3_5-8B-hf.yaml` |
| Llama-3.2-3B-Instruct | vllm,TP=1 | gsm8k:exact_match,strict-match=0.71,exact_match,flexible-extract=0.76 | 5 / True / auto  `tests/e2e/models/configs/Llama-3.2-3B-Instruct.yaml` |
| Minitron-8B-Base | vllm,TP=1 | gsm8k:exact_match,strict-match=0.5436,exact_match,flexible-extract=0.5451 | 未显式声明 / False / auto  `tests/e2e/models/configs/Minitron-8B-Base.yaml` |
| Mixtral-8x7B-Instruct-v0.1 | 未显式声明,TP=4 | ceval-valid:acc,none=0.45 | 5 / True / 32  `tests/e2e/models/configs/Mixtral-8x7B-Instruct-v0.1.yaml` |
| Molmo-7B-D-0924 | vllm-vlm,TP=1 | ceval-valid:acc,none=0.71 | 0 / False / auto  `tests/e2e/models/configs/Molmo-7B-D-0924.yaml` |
| Qwen2-Audio-7B-Instruct | vllm,TP=1 | gsm8k:exact_match,strict-match=0.44,exact_match,flexible-extract=0.45 | 5 / True / auto  `tests/e2e/models/configs/Qwen2-Audio-7B-Instruct.yaml` |
| Qwen2.5-Math-RM-72B | vllm-rm,TP=4 | gsm8k_correctness:accuracy=0.8 | 未显式声明 / 未显式声明 / 4  `tests/e2e/models/configs/Qwen2.5-Math-RM-72B.yaml` |
| Qwen3-30B-A3B-W8A8 | vllm,TP=2 | gsm8k:exact_match,strict-match=0.9,exact_match,flexible-extract=0.8 | 5 / False / auto  `tests/e2e/models/configs/Qwen3-30B-A3B-W8A8.yaml` |
| Qwen3-30B-A3B | vllm,TP=2 | gsm8k:exact_match,strict-match=0.89,exact_match,flexible-extract=0.85; ceval-valid:acc,none=0.84 | 5 / False / auto  `tests/e2e/models/configs/Qwen3-30B-A3B.yaml` |
| Qwen3-8B-W8A8 | vllm,TP=1 | gsm8k:exact_match,strict-match=0.8,exact_match,flexible-extract=0.82 | 5 / True / auto  `tests/e2e/models/configs/Qwen3-8B-W8A8.yaml` |
| Qwen3-ASR-1.7B | vllm-asr,TP=1 | librispeech_test_clean:wer=0.035 | 未显式声明 / 未显式声明 / 未显式声明  `tests/e2e/models/configs/Qwen3-ASR-1.7B.yaml` |
| Qwen3-Next-80B-A3B-Instruct | vllm,TP=4 | ceval-valid_accountant:acc,none=0.98 | 5 / True / 1  `tests/e2e/models/configs/Qwen3-Next-80B-A3B-Instruct.yaml` |
| Qwen3-Omni-30B-A3B-Instruct | vllm-vlm,TP=4 | mmmu_val:acc,none=0.6 | 0 / True / auto  `tests/e2e/models/configs/Qwen3-Omni-30B-A3B-Instruct.yaml` |
| Qwen3-VL-30B-A3B-Instruct | vllm-vlm,TP=2 | mmmu_val:acc,none=0.58 | 0 / True / auto  `tests/e2e/models/configs/Qwen3-VL-30B-A3B-Instruct.yaml` |
| Qwen3-VL-8B-Instruct-W8A8 | vllm-vlm,TP=1 | mmmu_val:acc,none=0.52 | 0 / True / 32  `tests/e2e/models/configs/Qwen3-VL-8B-Instruct-W8A8.yaml` |
| Qwen3-VL-8B-Instruct | vllm-vlm,TP=1 | mmmu_val:acc,none=0.55 | 0 / True / 32  `tests/e2e/models/configs/Qwen3-VL-8B-Instruct.yaml` |
| gemma-3-4b-it | vllm,TP=1 | gsm8k:exact_match,strict-match=0.59,exact_match,flexible-extract=0.59 | 5 / False / auto  `tests/e2e/models/configs/gemma-3-4b-it.yaml` |
| internlm3-8b-instruct | vllm,TP=1 | ceval-valid:acc,none=0.42 | 5 / False / auto  `tests/e2e/models/configs/internlm3-8b-instruct.yaml` |

ASR的WER、奖励模型的gsm8k_correctness、VLM的MMMU与文本模型的strict/flexible exact-match不是同一指标。hardware字段在这20份配置中是Atlas A2 Series的试验标记，不证明某checkpoint在所有A2卡、依赖栈或任务已通过；任务value是预设目标，实际比较方向及容差仍看评估入口和原始结果。

## 不能省略的配置差异

- DeepSeek_V31_Terminus_w4a8_w8a8_A5文件实际model指向w4a4c8-mxfp4，不能按文件名决定权重量化；模型路径、quantization和KV dtype各自记录。Qwen3-VL、Audio、Omni、ASR及奖励模型也不可只从家族名推统一输入/输出接口。
- PD的P/D模板常不同：P eager和D FULL_DECODE_ONLY、不同token预算或投机步数均有明确实例；不能只看首个命令。PCP/DCP、PP与EP是独立维度，节点×NPU也不是TP数。internal/external两种DP加载模式按实际字段和运行时选择。
- test_content可能缺省、null、空列表或含chat_completion、spec_decode_acceptance、benchmark_comparisons、image/messages；没有显式业务项不能宣称执行过该检查。case_type还存在accuracy、performance、spec_decode及curl_cmd，不能只按文件后缀推测试种类。
- performance warmup可用baseline=0、极少prompt或max_out_len=1；这类记录不是质量/吞吐达标。阈值0.95/0.97等和accuracy的差值阈值不混解释；请求速率、前缀比例、输入输出长度、并发和采样需同组核对，不能把文件名TPOT直接当实测时延。
- daily/weekly和同名variant保留独立配置身份，不能仅靠stem去重；原路径与全部字段仍通过sources定位。表只帮助选择场景，不替代源配置展开、CLI解析和后端门禁。

## 小型资产的用途边界

六份小型资产的完整来源路径为：

- `tests/e2e/pull_request/four_card/glm53flash_assets/config.json`。
- `tests/e2e/pull_request/four_card/glm53flash_assets/quant.json`。
- `tests/e2e/pull_request/four_card/glm53flash_assets/tokenizer.json`。
- `tests/e2e/pull_request/four_card/glm53flash_assets/tokenizer_config.json`。
- `tests/ut/_fake_weight/config.json`。
- `tests/ut/eplb/core/expert_map.json`。


glm53flash_assets的config/quant/tokenizer/tokenizer_config为构造和接口回归的固定输入，quant映射按层列出参数类别，WordLevel词表含少量图像/视频特殊token；tests/ut/_fake_weight/config.json用于小模型mock，expert_map.json用于EPLB层/专家映射。它们能限定测试输入身份，不能证明真实GLM checkpoint、processor、分片加载或EPLB通信已正确。Agent应把小型fixture与真实权重阶段分开留证。

没有运行这些配置、pytest、评估器或任何NPU；本卡不把用例登记、配置解析、源码固定或未来CI绿色当作模型适配/性能完成。


## 场景定义与调度相互独立

E2E_TEST_CASE_GUIDE将cases中的测试实现、workflow矩阵的资源拓扑与common框架分层；单节点test_cases每项生成一个参数，name非空并用于输出，不把name当不可变身份。pytest-driven用于需要fixture/自定义控制流的场景；YAML驱动用于可由共享runner表达的配置，扩展业务handler仍需相应断言和生命周期管理。KV pool先于服务启动、晚于全部服务/代理退出停止，服务命令中的kv-transfer-config原样透传，不能只配置pool就推模型已消费。

accuracy.txt只是显式评估配置文件列表，含文本、VL、Audio、ASR等；列出名称不等于相应文件存在、收集成功或任务达标。其名单与本卡204份配置范围不同，不能用一个列表的条目数替代真实矩阵和结果。
