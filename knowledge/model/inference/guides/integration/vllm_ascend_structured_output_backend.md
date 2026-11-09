---
type: Guide
title: vLLM Ascend 结构化输出接入：单backend、校验与grammar生命周期
description: 沿 StructuredOutputsParams、_validate_structured_outputs 与 StructuredOutputManager
  核对 auto回退、单引擎backend锁存、Outlines终止与xgrammar空白补丁，区分版本注释、实际校验和模型门禁。
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_structured_output.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/structured_output.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/structured_output.po
  role: supporting
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/sampling_params.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/config/structured_outputs.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/structured_output/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/structured_output/backend_xgrammar.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/structured_output/backend_outlines.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/requirements.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/requirements-nightly.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/requirements-dev.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/platform/test_patch_structured_output.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/images/structured_output_1.png
  role: supporting
created_at: '2026-10-29T21:54:22Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-11-03T01:29:41Z'
---

# vLLM Ascend 结构化输出接入：单backend、校验与grammar生命周期


## 任务与固定范围

新模型需JSON/regex/choice/grammar输出，auto请求先成功后报already using，或格式已结束仍报FSM错误。固定Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 与原生vLLM v0.32.0 `5df63a7203cdb9328d824a27b682e77c7b9928be`；只生产Ascend所需上游依赖，不据指南“用法相同”推导所有backend/模型/设备组合可用。整项硬件范围未明确，保持draft/空平台。

这是Host校验、选择与生命周期知识，未导入上游、安装backend库、启动服务/线程池或执行模型。Device mask与真实schema兼容性不由本卡完成。

## 先校验请求与模型

StructuredOutputsParams的json、regex、choice、grammar、json_object、structural_tag必须恰好选一种；whitespace等是附加选项。原生_validate_structured_outputs在配置和参数都存在时执行：拒绝diffusion模型、缺tokenizer、空choice、空白grammar/JSON字符串、过深JSON、json_object=False、含NUL的regex和空白structural_tag。空regex及只含空白的regex没有被当作同一种错误；它们可以是合法匹配模式。JSON nesting及各backend完整校验器内部未在本卡穷尽。

_backend是内部路由状态，不能让Agent通过私有请求字段强制选库。复用曾由auto解析的params与任意手写_backend不同，原生用_backend_was_auto标识；更改server backend、复用参数对象和序列化应核对实际版本。

固定StructuredOutputsConfig允许auto/xgrammar/guidance/outlines/lm-format-enforcer；disable_any_whitespace只允许显式xgrammar/guidance，disable_additional_properties只允许guidance。字段存在不证明每个backend支持相同schema、regex方言或tokenizer。

## auto回退不是每请求可混用backend

原生auto优先尝试xgrammar；部分Lark+Tekken Mistral场景直接guidance。xgrammar的VLLMValidationError才进入所读回退分支；按非Tekken Mistral/不支持的JSON特性等选outlines或guidance，后者还检查tokenizer能力。显式backend不走相同auto回退。具体特性全集以对应库和原生校验器为准，不把这里的路由分支当完整支持表。

Ascend补丁分两层拒绝mixed backend：

| 层 | 当前实现动作 | 边界 |
| --- | --- | --- |
| SamplingParams校验 | 先调用原始校验，再用inspect.signature.bind_partial定位structured_outputs_config；在配置对象上锁存解析出的字符串backend | 原始校验抛错时不走锁存；同一配置后续解析不同字符串时抛VLLMValidationError |
| StructuredOutputManager.grammar_init | 从request读内部backend；若未锁存，尝试按现有backend类及MRO类名推断，再比较；原始初始化返回且backend非None才记状态 | 非结构化请求透传；类名子串识别不是通用插件注册，不能保证任意自定义backend被识别 |

属性名为_vllm_ascend_structured_output_backend。报错包含V1 structured outputs only supports one backend per engine及already using；V1在这里指engine契约，不等同于强制MRv1。混用不同约束类型不一定混用backend，但两个schema在auto下解析成不同backend会触发这个约束。显式统一server backend并校验所有schema，或由上层分流到独立engine；不能靠重复重试、改私有_backend或移除合法业务约束宣布适配完成。

配置锁存与manager锁存不是同一个对象，也没有在所读补丁里建立跨进程/并发事务。前端校验成功、backend对象存在、grammar编译成功与请求已可调度是不同状态。

## 编译Future、请求reasoner与退役

原生manager默认用线程池编译grammar；external_launcher关闭异步编译，注释指出各TP scheduler状态转移不同步会破坏确定性。同步编译异常也被装入Future；_create_grammar记录并重新抛错，由后续请求状态消费者处理，而不是本函数保证HTTP状态码或整个engine自愈。

reasoner类由manager持有，实例在structured request上按其chat-template kwargs懒创建。enable_in_reasoning和reasoning-end边界决定何时喂grammar/施加mask，不能把普通content JSON检查直接用于整个reasoning文本。

clear_backend会等待/取消相关executor任务，再destroy backend并置None；所读代码没有清除Ascend锁存属性，也不重建已shutdown线程池。它不是热切换backend的完整公共流程；不能仅调用clear_backend后继续把原engine当全新实例。

## Outlines终止与xgrammar空白补丁

Ascend对OutlinesGrammar.accept_tokens在guide.is_finished()时直接返回True，意图避免终态额外EOS/stop token被拒。该短路不调用原accept，也不自行推进num_processed_tokens或_is_terminated。固定原生v0.32已具有EOS截断、终态检查与_is_terminated逻辑；补丁注释的旧问题不能替代两个固定实现组合的实际验证。需要覆盖终态、EOS、rollback、后续mask及请求最终结束，不由返回True单独认定完整终止。

Ascend对GrammarCompiler.compile_json_schema强制kwargs[separators]=None，保留其他传入参数；可选xgrammar导入失败时不安装这层覆写。原生compile_grammar在disable_any_whitespace时本来传any_whitespace=False与(',',':')，因此补丁改变其中separators，不是简单地忽略整个空白配置。不要承诺输出必无空白，另按业务规范验收。

补丁注释提到0.2.7/0.2.8和待0.2.9，但代码没有按版本判断；固定requirements仅写xgrammar>=0.1.30，nightly/dev也没有固定实际安装版本。记录真实wheel版本、调用签名与补丁加载证据，不把注释当环境探测，也不据它自动删除补丁。两个终态/空白补丁有original属性guard；前两层校验/manager覆写没有同样完整的reload防重包裹流程，不能声称任意重复加载幂等。

## 验收入口与中文资料

按[格式与接口验收](../../runbooks/validations/vllm_ascend_structured_output_acceptance.md)分别验证请求门禁、编译失败、单backend、终态/空白和业务语义；按[mask行与投机接线](vllm_ascend_grammar_mask_contract.md)核对实际Runner路径。UT使用FakeBackend/monkeypatch定义mixed、同backend、首次失败不锁存及子类推断等断言，本次未执行；没有覆盖全部真实backend/多进程竞态。

structured_output.po的8条有效非空译文已和英文全文对照，0obsolete/fuzzy，msgid均匹配。它们解释模板/schema和沿用vLLM接口，没有单独提供所有模型/硬件、单引擎混库或语义正确性保证。线上中文HTML映射仍未证明。

## Schema图是机制示意，不是backend ABI

固定结构化输出图将语言模型token分布与Schema定义的约束路径汇入Constrained Sampling，再产生Structured Output；图中Logit Bias表达的是约束作用点，不表示每个backend都暴露同名参数、支持同一schema或只需改一张偏置。

实际接入仍按本卡请求校验、grammar编译/状态、单backend与reasoning边界，以及独立mask行和投机接线合同。图没有给出任意模型tokenizer兼容、业务语义正确或真机执行结果，本次也未运行其示例。
