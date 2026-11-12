---
type: Guide
title: SGLang NPU接口与采样测试的断言边界
description: 整理token ID、FIM、logprob、thinking、stop和Profiler等NPU回归，区分协议断言、数值比较与仅HTTP
  smoke。
tags:
- task.testing
- topic.model_serving
- topic.precision
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/api_related/test_npu_return_input_ids.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/api_related/test_npu_return_output_ids.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/backends/test_npu_sampling_backend.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/dllm/test_npu_llada2_mini_fdfo.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parameter/deepseek_coder.json
  role: constraint
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parameter/test_npu_fim_completion.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parameter/test_npu_log_level.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parameter/test_npu_original_logprobs.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/runtime_opts/test_npu_constrained_json_whitespace.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/interface/test_npu_api.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/interface/test_npu_api_abort_request.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/interface/test_npu_api_encode.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/interface/test_npu_enable_thinking.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/interface/test_npu_matched_stop.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/interface/test_npu_openai_server_ignore_eos.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/interface/test_npu_penalty.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/test/ascend/npu_eval_accuracy_kit.py
  role: constraint
created_at: '2026-11-08T12:28:23Z'
updated_at: '2026-11-09T04:35:32Z'
platforms:
- a3
---

# SGLang NPU接口与采样测试的断言边界

## 有明确输出语义的回归

这些是A3测试注册中的指定模型与请求，不是已运行结果或完整API支持表。

| 场景 | 模型/请求与断言 |
|---|---|
| 输入/输出token IDs | Llama3.2-1B、禁图；sglext prompt IDs与chat template一致；输出按choice嵌套，n=1/2、stream/nonstream用skip_special_tokens=True解码，再比较decoded.strip()与content.strip()相等（不检查特殊token或首尾空白差异） |
| FIM | DeepSeek-Coder1.3B，内置deepseek_coder模板或JSON模板；prompt/suffix、n=1/3，检查choices、id/created/object、prompt_tokens=两侧编码长度+2、输出tokens>0；不检查生成代码正确性 |
| Thinking | Qwen3-30B TP2禁图、qwen3 parser，开关thinking、stream/nonstream，检查reasoning/content字段的归属 |
| matched_stop | Llama3.1-8B，newline stop串、EOS128009、length5→matched_stop None；chat/completion两接口 |
| ignore_eos | Llama3.2-1B请求max200，比较输出长度与finish_reason=length；长度由content重分词，不能当逐token精确200断言 |
| JSON whitespace | Llama3.2-1B、xgrammar，限制连续空格/tab/newline/CR为1；schema要求name字符串/word regex、population整型、禁额外字段；generate/chat，max128/temp0 |

FIM JSON定义begin=`<｜fim▁begin｜>`、middle=`<｜fim▁hole｜>`、end=`<｜fim▁end｜>`、position=MIDDLE，不能套给其它tokenizer。

## 数值比较与采样检查

original-logprob测试Llama3.2-1B、禁图、seed1234、max-new1，HF float32 logits经logsoftmax与服务器top50和10个随机token比较，rtol0.2/atol0。环境变量`SGLANG_RETURN_ORIGINAL_LOGPROB`在True/False间区分原始与temperature0.5缩放结果；不证明全模型全序列logprob精度。

sampling backend用Qwen2.5-7B禁图/Radix，greedy重复5次、batch10一致；仅GITHUB_EVENT_NAME=pull_request且GITHUB_WORKFLOW_REF不含nightly-test-npu.yml时走PR smoke；其他分支（含PR触发的nightly）执行MMLU64题并断言score≥0.65。大型API用Llama3.2-1B检查health/model/metadata、hidden_states/logprob/rid/inputIDs batch与SSE；temperature2/5的不同输出只是随机性smoke，没有统计分布检验。

LLaDA2-mini FDFO用TP2、禁图/Radix、LowConfidence，128请求/输入3584/输出1024/C16/无限请求速率，断言mean与p99 TTFT及total throughput的对比方向。没有执行结果时不报告加速倍数。

## 只能支持较弱结论的用例

encode文件docstring仍写GME，但实际Qwen3-VL-4B TP2、is-embedding，只检查HTTP、rid与batch数量，不比较embedding数值。penalty用例只要求frequency/presence/min-new等组合HTTP200；`random.shuffle(args * 5)`丢弃了被打乱的副本，实际线程池对原14组合运行一次，不能写70次随机验证，也没断言惩罚的数值效果。

abort用例在生成1024 tokens的线程开始0.5秒后调用abort并打印响应，没有assert请求确已终止。start_profile三种调用（start_step15/num_steps5、手动start/stop、指定5steps）仅检查目录非空，不验证trace事件或profile性能。log-level用warning屏蔽HTTP访问日志，加log-level-http=info恢复日志并要求Paris补全，证明范围限于这条输出路径。Profiler采集方法见[服务剖析指南](../../optimization/sglang_ascend/sglang_ascend_doc_service_profiling.md)。

## Evidence

- [test/registered/npu/basic_function/api_related/test_npu_return_input_ids.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/api_related/test_npu_return_input_ids.py)（primary）
- [test/registered/npu/basic_function/api_related/test_npu_return_output_ids.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/api_related/test_npu_return_output_ids.py)（supporting）
- [test/registered/npu/basic_function/backends/test_npu_sampling_backend.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/backends/test_npu_sampling_backend.py)（supporting）
- [test/registered/npu/basic_function/dllm/test_npu_llada2_mini_fdfo.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/dllm/test_npu_llada2_mini_fdfo.py)（supporting）
- [test/registered/npu/basic_function/parameter/deepseek_coder.json](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parameter/deepseek_coder.json)（constraint）
- [test/registered/npu/basic_function/parameter/test_npu_fim_completion.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parameter/test_npu_fim_completion.py)（supporting）
- [test/registered/npu/basic_function/parameter/test_npu_log_level.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parameter/test_npu_log_level.py)（supporting）
- [test/registered/npu/basic_function/parameter/test_npu_original_logprobs.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/parameter/test_npu_original_logprobs.py)（supporting）
- [test/registered/npu/basic_function/runtime_opts/test_npu_constrained_json_whitespace.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/runtime_opts/test_npu_constrained_json_whitespace.py)（supporting）
- [test/registered/npu/interface/test_npu_api.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/interface/test_npu_api.py)（supporting）
- [test/registered/npu/interface/test_npu_api_abort_request.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/interface/test_npu_api_abort_request.py)（supporting）
- [test/registered/npu/interface/test_npu_api_encode.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/interface/test_npu_api_encode.py)（supporting）
- [test/registered/npu/interface/test_npu_enable_thinking.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/interface/test_npu_enable_thinking.py)（supporting）
- [test/registered/npu/interface/test_npu_matched_stop.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/interface/test_npu_matched_stop.py)（supporting）
- [test/registered/npu/interface/test_npu_openai_server_ignore_eos.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/interface/test_npu_openai_server_ignore_eos.py)（supporting）
- [test/registered/npu/interface/test_npu_penalty.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/interface/test_npu_penalty.py)（supporting）
