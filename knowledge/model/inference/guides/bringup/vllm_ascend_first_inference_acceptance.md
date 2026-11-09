---
type: Guide
title: vLLM Ascend 首次推理：硬件分支、离线断言与在线响应验收
description: 按A2、A3、310P（Atlas 300I DUO/200I Pro）和950DT的Qwen3-0.6B示例验收首请求，区分容器导入、模型列表、离线非空输出、在线choices文本及退出日志；保留ModelScope和进程身份边界。
  核对旧根 quick_start 孤儿译文的成功层次、ModelScope 权重身份与 DUO 图限制。
tags:
- task.testing
- task.implementation
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/getting_started/quick_start.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/getting_started/quick_start.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/getting_started/quick_start/ascend_image/atlas-a2.inc.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/getting_started/quick_start/ascend_image/atlas-a2.inc.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/getting_started/quick_start/ascend_image/atlas-a3.inc.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/getting_started/quick_start/ascend_image/atlas-a3.inc.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/getting_started/quick_start/ascend_image/atlas-200i-pro.inc.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/getting_started/quick_start/ascend_image/atlas-200i-pro.inc.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/getting_started/quick_start/ascend_image/atlas-300i-duo.inc.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/getting_started/quick_start/ascend_image/atlas-300i-duo.inc.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/getting_started/quick_start/ascend_image/atlas-950dt.inc.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/getting_started/quick_start/ascend_image/atlas-950dt.inc.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/getting_started/quick_start/online/qwen3-0.6b.inc.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/getting_started/quick_start/online/qwen3-0.6b.inc.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/getting_started/quick_start/online/qwen3-0.6b-310p.inc.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/getting_started/quick_start/online/qwen3-0.6b-310p.inc.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/getting_started/quick_start/offline/qwen3-0.6b.inc.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/getting_started/quick_start/offline/qwen3-0.6b.inc.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/getting_started/quick_start/offline/qwen3-0.6b-310p.inc.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/getting_started/quick_start/offline/qwen3-0.6b-310p.inc.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/getting_started/installation/cann_image/atlas-950dt.inc.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/quick_start.po
  role: supporting
created_at: '2026-10-30T03:52:08Z'
platforms:
- a2
- a3
- 310p
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-30T15:10:56Z'
---

# vLLM Ascend 首次推理：硬件分支、离线断言与在线响应验收


## 任务、来源与适用范围

固定Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2的Quick Start，以Qwen3-0.6B、准备好的Ascend主机和预构建容器为例。A2/A3/950DT使用标准示例，Atlas 300I DUO/200I Pro有独立配置；这是首次推理流程与来源报告的示例范围，不证明任意模型、所有950/310系列或功能组合已支持。环境/版本准备见[环境指南](../deployment/vllm_ascend_versioned_environment.md)，新架构/权重接入见[模型适配流程](vllm_ascend_new_model_onboarding.md)。

本卡在已准备的环境建立最小请求判据，不替代上述安装流程或完整新模型协议。quick_start.po的36条有效译文中31条msgid连续匹配当前英文，5条差异是模型链接、组件说明、ModelScope链接、导航措辞和产品称谓；不能把这些编辑差异当新增/撤销功能。其余9份PO共92条均匹配，总计128/123/5；无fuzzy也不证明页面已渲染。代码和部分采样/响应要求由英文include提供，必须一并阅读。

## 先确认所用容器与硬件分支

ascend_image/atlas-a2.inc.po、atlas-a3.inc.po、atlas-300i-duo.inc.po、atlas-200i-pro.inc.po及atlas-950dt.inc.po对应真实拉取/启动模板。Ascend镜像A2无硬件后缀，A3为-a3，300I DUO/200I Pro为-310p，950DT为-a5，openEuler再带-openeuler；模板版本须展开并记录实际镜像身份。下载加速只替换仓库前缀，完整tag按环境指南裁决。

A3模板要求两个设备节点，200I Pro需要额外设备/驱动库/配置且不同OS路径有差别，950DT使用host网络并挂hccn_tool；不能由同一镜像段推导相同挂载。尤其950DT的Ascend预构建模板与CANN基础模板并非同一命令，前者未列/dev/devmm_svm，后者列出；不由一份模板缺行推导系统无该设备或任意环境都应删除该映射。设备路径、shm和端口保留来源示例范围。

容器探针的torch/vllm/Ascend导入和torch.npu.is_available只关闭导入/可用性缺口。插件日志Platform plugin ascend is activated说明平台激活，不证明checkpoint加载、Worker首个forward或数值正确。接下来仍必须实际发送模型请求。

## 权重来源与最小配置

模型ID为Qwen/Qwen3-0.6B，实际使用前记录checkpoint、tokenizer与本地路径身份。若Hugging Face因超时/DNS等不可用，来源提供VLLM_USE_MODELSCOPE=True及modelscope>=1.18.1,<1.38的替代下载示例；这是固定文档约束，本批未验证外部下载器/仓库等价性或执行安装。已有本地模型时直接替换为本地目录，不需要为此设置下载源变量。

| 所读推理include/PO | 固定示例的参数 |
| --- | --- |
| offline/qwen3-0.6b.inc.po | LLM默认模型加载；两条prompt，temperature=0.0、max_tokens=32。 |
| online/qwen3-0.6b.inc.po | vllm serve标准模型，completions请求temperature=0、max_tokens=5。 |
| offline/qwen3-0.6b-310p.inc.po | dtype=float16、max_num_seqs=8，FULL_DECODE_ONLY，cudagraph_capture_sizes=[1,2,4,8]，ascend_compilation_config.enable_npugraph_ex=False；采样同标准离线示例。 |
| online/qwen3-0.6b-310p.inc.po | 使用与该硬件离线分支对应的dtype、最大序列数、受限抓图范围与禁用npugraph_ex配置；采样同标准在线请求。 |

这些数值是Qwen示例配置，不是新模型通用并发、输出长度或图配置最优值。310P分支不能漏掉enable_npugraph_ex=False，也不能把标准路径默认构造等同于两套配置没有差别；其它模型/图模式另核对实际支持与Runner。

## 离线与在线成功信号分别留证

| 阶段 | 来源要求与需要保留的实际证据 | 尚未证明 |
| --- | --- | --- |
| 离线generate | len(outputs)==len(prompts)，逐项output.outputs[0].text.strip()非空；保留实际prompt、输出、采样和错误阶段。 | 数量相同不自动验证输入身份、语义、参考logprobs、长上下文或任务准确率。 |
| 在线启动 | 进程启动、Application startup complete和监听日志；记录实际服务身份/base URL。 | 首请求已执行或真实权重正确。 |
| /v1/models | curl --fail取得服务目录，核对实际served model name。 | 模型forward可用，或目录中的模型等于指定checkpoint。 |
| /v1/completions | 真正发送指定模型和prompt，HTTP/JSON无错误，choices[0].text为非空生成文本。 | 仅curl返回、空completion或错误体都不能确认推理；非空文本仍只是smoke。 |

temperature=0与示例生成文本不构成所有设备逐字相同的保证，不把文档里的示例续写硬编码为正确性oracle。成功之后按[精度口径](vllm_ascend_accuracy_evaluation_contract.md)与所需模型功能继续验收，正确性通过再做[性能对照](../optimization/vllm_ascend_benchmark_workflow.md)。服务目录成功但首请求崩溃仍判运行失败，不能进入性能收益结论。可参考[假就绪排查](../../runbooks/runtime/vllm_ascend_first_request_false_ready.md)的证据分层，但该卡具体诊断来源限A2/A3，不将其中开关迁到310P/950DT当作已验证修法。

## 退出日志与进程身份

离线英文示例在输出完成之后列出Shutdown initiated、Shutdown complete、Engine core proc EngineCore died unexpectedly和swigvarlink DeprecationWarning，并说明这组退出消息不影响该次推理结果。这个判断有先后条件；不能对启动期、请求中或没有成功输出的同名错误统一忽略。记录输出、退出阶段和实际进程结果，出现新异常回到首个错误定位。

在线示例说明SIGINT/前台Ctrl+C优雅停止，并提醒pgrep -f "vllm serve"可能匹配其它服务。Agent应保留自己启动的服务/容器身份，确认目标后才停止；不能将宽泛匹配结果当作唯一PID。该来源的命令示例不是本次已启动/已停止服务的记录。

本批只读固定文档及译文，没有下载模型、拉镜像、安装依赖、导入上游、启动/停止服务、发送推理请求或执行NPU/Agent A/B。来源所称示例已验证与本次新增verified事件分开；这里没有新增真实验证事件。


## 旧 quick_start.po 的同名入口与成功层次

根目录 quick_start.po 的56条有效消息没有同路径英文 quick_start.md；当前入口是 getting_started/quick_start.md，不能与前述36条 canonical 译文合并计数或据此恢复网页。其 Qwen3-0.6B 单设备 smoke、ModelScope 替代来源、DUO float16 与禁用 enable_npugraph_ex 的线索与当前工作流融合，仍按固定权重、实际软件和硬件分支验收。

旧词句中的“平台检测成功”“服务启动成功”“调用后有结果”分别落实为插件选择、API ready、模型目录和实际非空生成输出四层。输出完成后的已知退出消息有时序前提；只有平台日志或 /v1/models 成功时出现 EngineCore 异常，仍应保留错误并判首请求未完成，不能套用退出FAQ忽略。ModelScope 与 Hugging Face 的同名路径也不自动保证 tokenizer、revision 和分片一致。

DUO 的 enable_npugraph_ex=false 不表示所有图均不支持；本卡当前 FULL_DECODE_ONLY 与有限 capture sizes 是 Qwen3-0.6B 专属例，不移植为 Qwen 27B 的 TP/MTP 图配置。200I 额外挂载、950DT 镜像/设备入口及各OS路径沿环境指南逐项核对。结束服务按实际所属 PID/容器停止，旧宽泛进程匹配不作为 Agent 的默认清理动作。

本次融合的是资料判据，没有实际下载、导入框架、运行推理或停止进程；smoke 不能替代新模型适配、任务精度与性能优化实验。
