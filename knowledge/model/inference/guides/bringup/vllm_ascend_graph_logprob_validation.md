---
type: Guide
title: vLLM Ascend 图后端精度验收：3-token logprob 与 Xlite 测试边界
description: 按 compare_logprobs、_COMPILATION_KEYS 和 prefill/decode 判据核对 eager 基线、top-20单向cross-lookup、容差及输出数量；区分Xlite单卡数值检查、双卡非空smoke与UT占位。
tags:
- task.testing
- task.debugging
- topic.precision
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/utils.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_xlite.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/test_xlite.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/xlite/test_xlite.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/conftest.py
  role: implementation
created_at: '2026-10-29T23:35:28Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T23:35:28Z'
---

# vLLM Ascend 图后端精度验收：3-token logprob 与 Xlite 测试边界


## 任务与证据范围

用于新模型启用图后端/Xlite后的短序列差分验收，或测试返回成功但不清楚比较了什么。固定Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2`，参考vLLM v0.32.0。这里只静态蒸馏tests/e2e/pull_request/utils.py的logprob helper、Xlite调用点及conftest所述片段；没有执行测试、导入模型或取得真机结果。整项硬件/模型范围未知，保持draft/空平台。

## compare_logprobs如何构造两侧

helper先从runner_kwargs删去_COMPILATION_KEYS={compilation_config,additional_config,cudagraph_capture_sizes}，再给baseline设置enforce_eager=True。随后依次构造baseline Runner和原runner_kwargs的候选Runner；两侧都直接调用runner.model.generate。

删除的是整个additional_config，Xlite用例在里面同时设置weight_nz_mode=2和xlite_graph_config，因此比较不能仅由函数名推导为只改Xlite一项。应保存两侧的有效配置，核对NZ、并行、量化、图与其他扩展；默认值可能使部分字段实际相同，也可能不同，须以目标环境为准。原生enforce_eager与Xlite是否仍启用的区别见[运行接线](../integration/vllm_ascend_xlite_runner_dispatch.md)。

所读VllmRunner默认dtype=auto、TP=1、quantization=None，将参数传入LLM；标记BF16不是该调用点显式设置dtype。普通Runner拒绝data_parallel_size>1，另有DPVllmRunner；其已读构造片段默认dtype也为auto，不能把marker当实际NPU/dtype证明。helper使用普通Runner，不自动变成DP数值对照。

## 三个token的实际判据

_LOGPROB_SAMPLING_PARAMS设置max_tokens=3、temperature=0、top_p=1、top_k=0和logprobs=_DECODE_TOPK=20。这里max_tokens=3是生成预算，helper还逐对assert两侧实际token_ids长度均为3；提前EOS等条件需要按真实运行解释。

| 位置/条件 | 固定代码检查 | 不能外推 |
| --- | --- | --- |
| token 0，prefill产生 | _check_prefill_token要求选中token ID相同，且该token的绝对logprob差<=atol | 不等于比较全词表分布或完整任务质量 |
| token 1/2，ID相同 | _check_decode_token比较同一选中token的绝对logprob差<=decode_atol | 只覆盖这两个短decode位置 |
| token 1/2，ID不同 | baseline选中ID必须出现在候选top-20，比较baseline给它的logprob与候选给同一ID的logprob | 代码没有反向再检查候选ID是否在baseline top-20，不能按注释“vice versa”声称对称验证 |

atol缺省0.0689，decode_atol未传时为2*atol，即0.1378；它们是这份helper的绝对logprob容差，不是百分比、任务accuracy阈值或新硬件统一标准。语义/数值要求应先约定并独立留证，不能为候选通过而回写已冻结接受标准。

两个模型各自贪心生成，decode ID分歧后各自prefix可能不同；该检查不是强制同prefix的teacher-forcing比较，也不证明完整分布距离很小。微小argmax差异、实际累计误差和下游任务影响仍需目标用例。

## 外层输出完整性与测试成功含义

helper用zip(baseline_outputs,compiled_outputs)逐对检查，然后每对取outputs[0]。没有在这段helper里显式assert两侧外层数量都等于prompts数量；少的一侧可截断zip，双方为空时无逐对比较。这是静态判据边界，不是本次已复现LLM返回缺项。消费结果时先独立核对请求ID/输入输出数量、次序和完成状态，再解释逐token检查。

三token和非空logprobs通过，只说明所检查请求/位置满足这些条件；不替代长上下文、多轮KV、DP空batch/预算、投机拒绝、不同shape、全模型层与媒体输入。任务数据集精度另按[评测合同](vllm_ascend_accuracy_evaluation_contract.md)，性能另按[基准指南](../optimization/vllm_ascend_benchmark_workflow.md)。

## Xlite已定义用例的强度

| 源码用例 | 声明配置与实际断言 | 覆盖边界 |
| --- | --- | --- |
| one_card/test_xlite.py | Qwen/Qwen3-0.6B，A2/BF16 marker，max_model_len=1024、block_size=128、weight_nz_mode=2；decode-only/full分别调用compare_logprobs和4条PROMPTS_SHORT | 定义了上述短数值对照；未显式指定dtype或所有Runner组合，也不是本环境已通过 |
| two_card/test_xlite.py | Qwen/Qwen3-30B-A3B，A3/BF16 marker，TPDP_SIZES=(2,1)/(1,2)、EP=true、HCCL_BUFFSIZE=1024、长度2048、block128；两种模式generate_greedy(...,3)后assert all(output[1] for output in outputs) | 没有baseline/logprob相等断言；all本身也没有另验外层outputs非空/等长，不能称双卡精度或性能达标 |
| tests/ut/xlite/test_xlite.py | test_xlite_placeholder函数体只有pass | 没有语义或数值断言，不提供adapter、KV、DP或ABI验证 |

单/双卡路径都列full_mode=False/True，但marker、测试存在或CI成功不能证明实际这一步进入Xlite、全部请求未fallback、V1/V2均执行或其他模型可用。记录实际Worker/Runner、每rank token预算/选路、外部xlite版本、原始输出与错误；测试定义与真实运行事件分别存证。

普通VllmRunner的_finalize_generate_outputs把prompt与sample.text拼接，generate_greedy再取该字符串；所以双卡TP路线即使completion为空，非空原prompt也能使output[1]为真。双卡用例把3作为max_tokens预算，没有像单卡helper那样assert实际生成3个token。这个结论限已读普通Runner路线，不据此推导未读完整DP序列化实现，也不是本次已观察到空completion。

## Agent使用顺序与停止条件

先固定模型/权重、软件/硬件、两侧有效配置与接受标准；核对请求完整性，再做短prefill/decode定位。随后增加实际需要的长度、缓存、并行/媒体/投机边界及任务精度，最后比较正确配置的性能。数量不齐、logprobs缺失、容差失败、marker与实际设备/dtype不同或选路未知时，继续归因并保留结果，不把它们归并成已验证支持。

本文没有启动LLM、pytest、进程组或服务，也没有调用NPU、下载权重/工具或生成精度/性能报告；所读fixture构造/退出片段不替代完整DP进程、资源清理或Device实现分析。
