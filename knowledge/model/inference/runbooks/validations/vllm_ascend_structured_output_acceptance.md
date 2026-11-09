---
type: Runbook
title: vLLM Ascend 结构化输出验收：schema、流式拼接与错误后恢复
description: 按 assert_structured_output、EMPLOYEE_SCHEMA 与接口fixture检验JSON Schema、regex、choice、grammar，核对32请求8线程、流式最终文本和400/422后续请求；区分测试定义与实际质量。
tags:
- task.testing
- task.debugging
- topic.model_adaptation
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/structured_output/test_openai_api.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/structured_output/cases.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/structured_output/api.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/structured_output/assertions.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/structured_output/conftest.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/structured_output/test_offline_api.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/structured_output/README.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/structured_output.md
  role: supporting
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/docs/features/structured_outputs.md
  role: supporting
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/sampling_params.py
  role: constraint
created_at: '2026-10-29T21:54:22Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T22:12:19Z'
---

# vLLM Ascend 结构化输出验收：schema、流式拼接与错误后恢复


## 触发、范围与原始观测

服务HTTP200/非空但JSON不完整、schema不符、流式分片解析失败、错误请求后后续生成异常，或换模型/量化/投机后格式回归。固定Ascend ceac与原生v0.32指南/接口；当前只有测试定义和源级验收合同，没有实际服务观测、模型运行或故障复现，整项硬件范围未知，保持draft/空平台。

格式合法、业务答案正确、吞吐/时延达标分别保留判据。案例名、pytest定义或温度0不提供执行成功、确定性或性能证据。

## 先核对接口和有效环境

离线用SamplingParams(structured_outputs=StructuredOutputsParams(...))；在线JSON案例用response_format.type=json_schema及json_schema.name/schema，regex/choice/grammar案例通过extra_body.structured_outputs。原始HTTP invalid案例把structured_outputs写在payload顶层；客户端extra_body是SDK封装层，不应再给服务JSON套一层extra_body。

固定原生指南声明旧guided_json/guided_regex/guided_choice/guided_grammar等在v0.12移除，使用structured_outputs；guided_decoding_backend从请求移除，由engine配置选择backend。该版本说明不是对任意旧服务的迁移实测，也不要求把SDK历史beta例子的版本当当前安装版本。

仓内fixture指定vllm-ascend/Qwen3-32B-W4A4、TP2、mp、quantization=ascend、max_model_len40960、max_num_seqs64、gpu_memory_utilization0.9、capture_sizes[64]、FlashComm1且fuse_norm_quant=False；在线另有DP1和max_num_batched_tokens16384、served name qwen3。它们是一组样例条件，不推广为所有模型的推荐值。

fixture的SERVER_ENV写有VLLM_USE_V1=1；这条声明不能证明安装版本实际消费了该变量，也不能证明MRv1正在执行。Engine与Runner均按实际版本的配置解析/选择日志及[mask接线](../../guides/integration/vllm_ascend_grammar_mask_contract.md)核对。真实checkpoint/tokenizer、版本、backend、Runner与硬件未确认时，不先归因为NPU数值错误。

## 按约束类型建立独立探针

| 类型 | 固定案例与断言 | 通过后仍不证明 |
| --- | --- | --- |
| JSON Schema | 非空→json.loads→jsonschema.validate；EMPLOYEE_SCHEMA要求name/age/department/skills、额外字段禁止及相应范围 | 不是只parse成功；合法员工记录不证明内容真实或业务问答准确 |
| regex | regex.fullmatch匹配完整IPv4文本 | 不把部分match当完整输出；测试regex库语义不等于所有backend方言 |
| choice | 完整text必须属于red/green/blue | 不预先strip/改大小写后掩盖额外文本 |
| grammar | 当前yes/no案例用allowed_outputs精确成员检查 | 这是该有限语言oracle，不是任意EBNF的通用解释器 |

离线每种case两条同prompt都验收，另循环切换四种constraint检查状态泄漏。切换constraint类型不等于切换backend；auto若解析到不同backend，按[单引擎约束](../../guides/integration/vllm_ascend_structured_output_backend.md)诊断，不能把该测试名当支持混库的证据。

## 流式、并发和错误后恢复

流式helper按顺序只拼delta.content，忽略空choices/空content，finally关闭响应，然后对最终整串执行同一oracle。单个分片不必是完整JSON；不要逐chunk json.loads后把合法拆分误判为模型失败。reasoning字段、工具调用、断连/取消、stop/finish_reason与尾部完整性需另验，本测试helper并未覆盖全部。

并发定义为32个请求、8个ThreadPoolExecutor workers，循环四种约束和plain请求；对每个返回按自己的case验证，plain仅要求非空白。32是总任务数，不是保证同时32个在途；定义没有给出时延/SLO或跨node证据，也没有证明所有backend并发可混用。

错误恢复探针分别发送非法JSON schema和互斥约束冲突，通过原始HTTP后立即发合法JSON请求并验证，再断言原错误状态属于400/422。它证明的是设计的前后请求判据；本次未执行，错误body、engine状态和所有故障类型未被覆盖。不能只看某次400就认定后续请求健康，也不能把500/超时自动归为某个算子。

## 失败归因与验收产物

依次核对请求序列化与版本→tokenizer/模型门禁→实际backend和grammar编译→请求FSM/终态与空白补丁→mask行和投机拒绝→最终文本oracle。格式通过后再做业务语义、真实精度与性能对照，避免改parser/strip/filter后掩盖原始输出。

记录原请求、最终原始text及流分片、schema/regex/grammar revision、每请求ID和有效backend、模型/软件/硬件与Runner、错误响应、后续合法请求、finish原因、样本数/失败数与独立性能结果。缺少这些记录时只保留待验证结论。更广模型验收沿[精度合同](../../guides/bringup/vllm_ascend_accuracy_evaluation_contract.md)，本卡未启动server/客户端、下载权重或运行pytest/NPU。
