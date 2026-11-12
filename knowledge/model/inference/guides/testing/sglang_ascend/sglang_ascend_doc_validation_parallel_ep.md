---
type: Guide
title: SGLang NPU并行、DeepEP与EPLB测试配方
description: 归纳DP负载均衡、DeepEP auto/低时延、专家记录及offload测试，保留随机抽样和仅smoke的断言范围。
tags:
- task.testing
- topic.model_serving
- topic.precision
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/dp_attn/test_npu_dp_attention.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/offloading/test_npu_offload_modes.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parallel_strategy/data_parallelism/test_npu_load_balance_method.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parallel_strategy/data_parallelism/test_npu_load_balance_method_pd_disaggregation.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parallel_strategy/expert_parallelism/test_npu_deepep_auto_deepseek_v3_2_w8a8.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parallel_strategy/expert_parallelism/test_npu_deepep_auto_qwen3_480b.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parallel_strategy/expert_parallelism/test_npu_deepep_auto_qwen3_next.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parallel_strategy/expert_parallelism/test_npu_deepep_low_latency_deepseek_v3_2_w8a8.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parallel_strategy/expert_parallelism/test_npu_deepep_low_latency_qwen3_480b.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parallel_strategy/expert_parallelism/test_npu_deepep_low_latency_qwen3_next.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parallel_strategy/expert_parallelism/test_npu_eplb_min_rebalancing_utilization_threshold.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parallel_strategy/expert_parallelism/test_npu_expert_distribution_recorder_mode.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parallel_strategy/expert_parallelism/test_npu_moe_dense_tp_size.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parallel_strategy/expert_parallelism/test_npu_moe_runner_backend.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/test/ascend/test_mmlu.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/test/ascend/npu_eval_accuracy_kit.py
  role: constraint
created_at: '2026-11-08T12:28:23Z'
updated_at: '2026-11-09T04:35:32Z'
platforms:
- a3
---

# SGLang NPU并行、DeepEP与EPLB测试配方

## DP与PD负载分配

本卡来源为A3注册测试定义，未执行。下文“普通PR smoke”统一指GITHUB_EVENT_NAME=pull_request且GITHUB_WORKFLOW_REF不含nightly-test-npu.yml；其他情况（包括PR触发的nightly）走完整评测分支，采用[精度测试契约](sglang_ascend_test_gsm8k_contract.md)的定义。混部DeepSeek-R1 W8A8 TP16/attention-DP2、禁图，四种DP load-balance mode在CI随机选一个；完整评测分支 GSM8K200题/5shot/max512/parallel128目标0.95，普通PR仅smoke，并检查server_info mode。不能说一次CI覆盖所有四种模式。

PD Qwen3-30B P/D TP2、attention-DP2，P五种×D五种共25组合，CI随机抽3组；完整评测分支 GSM8K目标0.93，普通PR仅smoke。auto的预期解析为P follow_bootstrap_room、D round_robin，不代表随机抽到每种调度策略。

DP-attention测试还包含Qwen3-32B TP4/DP2禁图的GSM8K0.6与JSON/EBNF/regex mixin；Moonlight TP2/DP2 mixed chunk256的GSM8K1319题目标0.83、最多2次，以及max-total4500/max-running128的retraction压力；Kimi-VL TP2/DP2仅验证图像usage>0。后两者不自动形成吞吐或视觉质量结论。

## DeepEP两种模式矩阵

| 模型 | GSM8K目标；MMLU声明值与生效断言 | 配置差异 |
|---|---|---|
| DeepSeek-V3.2 W8A8 TP16 | GSM8K0.95；MMLU声明0.85，auto实际score>0.85，LL实际score>0 | auto max-prefill40960；LL128，LL dispatch128、buffer2048 |
| Qwen3-Coder-480B W8A8 TP16/attention-DP4 | GSM8K0.91（200题/8shot）；MMLU8题声明0.61，auto/LL实际均score>0 | auto chunk28672；LL chunk1024 |
| Qwen3-Next TP8 | GSM8K0.90（200题/5shot）；MMLU8题声明0.56，auto/LL实际均score>0 | LL chunk1024、round tokens3000/round10、dispatch160、buffer2048 |

QwenNext源docstring写W8A8，但实际模型常量是INSTRUCT；本卡不据标题补写权重精度。源注释还写mixed LL不推荐，这只是该版本配方的建议。TestMMLU只消费accuracy_mmlu：DeepSeek auto设置该字段，其他上述类使用未被消费的accuracy_mmlu_threshold，故实际回落默认门槛0。声明值不能作为共同验收标准。质量测试也不是auto比LL的性能对照，不能由目标相同推出时延相同。

## EPLB与专家记录

Qwen3-30B W8A8 TP8、DeepEP normal、禁图、redundant16，EPLB iterations50/recorder buffer50/layers chunk1分别试阈值0.05与0.95，期待skip/rebalance-end日志及完整评测分支 GSM8K≥0.86。普通PR smoke会提前return，日志断言也被跳过，不能说普通PR smoke验证了重平衡门槛。

recorder测试Qwen30 TP2/EP2、normal：stat/stat_approx配EPLB，per_pass/per_token不配；仅检查start→生成→stop→dump端点与至少一个`.pt`文件，不核验专家直方图内容。将真实分布和[perfect EPLB合成分布](../../../optimizations/rules/perfect_eplb_profiling_upper_bound.md)区分，合成均匀路由不能用于质量。

DeepSeek-Coder-Lite的moe-dense-tp-size1场景TP2/EP2/EPLB normal要求完整评测分支 GSM8K>0.79；auto/triton runner对照则只检查HTTP200/Paris。offload cpu和sharded_gpu场景同模型、DP2、group4/num1/prefetch1、禁图，也只做HTTP200/Paris smoke，没有驻留字节或吞吐收益测量。

## Evidence

- [test/registered/npu/basic_function/dp_attn/test_npu_dp_attention.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/dp_attn/test_npu_dp_attention.py)（primary）
- [test/registered/npu/basic_function/offloading/test_npu_offload_modes.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/offloading/test_npu_offload_modes.py)（supporting）
- [test/registered/npu/basic_function/parallel_strategy/data_parallelism/test_npu_load_balance_method.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parallel_strategy/data_parallelism/test_npu_load_balance_method.py)（supporting）
- [test/registered/npu/basic_function/parallel_strategy/data_parallelism/test_npu_load_balance_method_pd_disaggregation.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parallel_strategy/data_parallelism/test_npu_load_balance_method_pd_disaggregation.py)（supporting）
- [test/registered/npu/basic_function/parallel_strategy/expert_parallelism/test_npu_deepep_auto_deepseek_v3_2_w8a8.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parallel_strategy/expert_parallelism/test_npu_deepep_auto_deepseek_v3_2_w8a8.py)（supporting）
- [test/registered/npu/basic_function/parallel_strategy/expert_parallelism/test_npu_deepep_auto_qwen3_480b.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parallel_strategy/expert_parallelism/test_npu_deepep_auto_qwen3_480b.py)（supporting）
- [test/registered/npu/basic_function/parallel_strategy/expert_parallelism/test_npu_deepep_auto_qwen3_next.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parallel_strategy/expert_parallelism/test_npu_deepep_auto_qwen3_next.py)（supporting）
- [test/registered/npu/basic_function/parallel_strategy/expert_parallelism/test_npu_deepep_low_latency_deepseek_v3_2_w8a8.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parallel_strategy/expert_parallelism/test_npu_deepep_low_latency_deepseek_v3_2_w8a8.py)（supporting）
- [test/registered/npu/basic_function/parallel_strategy/expert_parallelism/test_npu_deepep_low_latency_qwen3_480b.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parallel_strategy/expert_parallelism/test_npu_deepep_low_latency_qwen3_480b.py)（supporting）
- [test/registered/npu/basic_function/parallel_strategy/expert_parallelism/test_npu_deepep_low_latency_qwen3_next.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parallel_strategy/expert_parallelism/test_npu_deepep_low_latency_qwen3_next.py)（supporting）
- [test/registered/npu/basic_function/parallel_strategy/expert_parallelism/test_npu_eplb_min_rebalancing_utilization_threshold.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parallel_strategy/expert_parallelism/test_npu_eplb_min_rebalancing_utilization_threshold.py)（supporting）
- [test/registered/npu/basic_function/parallel_strategy/expert_parallelism/test_npu_expert_distribution_recorder_mode.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parallel_strategy/expert_parallelism/test_npu_expert_distribution_recorder_mode.py)（supporting）
- [test/registered/npu/basic_function/parallel_strategy/expert_parallelism/test_npu_moe_dense_tp_size.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parallel_strategy/expert_parallelism/test_npu_moe_dense_tp_size.py)（supporting）
- [test/registered/npu/basic_function/parallel_strategy/expert_parallelism/test_npu_moe_runner_backend.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parallel_strategy/expert_parallelism/test_npu_moe_runner_backend.py)（supporting）
