---
type: Guide
title: vLLM Ascend Qwen2.5 历史适配证据：7B 文本、Omni 与 Thinker 入口
description: 对照孤儿 Qwen2.5 7B 与 Omni 旧教程、vLLM v0.32.0 Thinker 注册及输入模态，保留 BF16 32GB、GSM8K、textVQA、TP、媒体路径和旧版本边界；当前昇腾硬件组合待验证。 区分Qwen2.5在CANN Executor与vLLM Ascend插件中的不同执行器证据，不相互恢复支持声明。
tags:
- task.design
- topic.model_adaptation
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen2.5-Omni.po
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen2.5-7B.po
  role: supporting
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/model_executor/models/registry.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/docs/models/supported_models.md
  role: constraint
created_at: '2026-10-30T14:23:18Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-30T14:23:18Z'
aliases:
- Qwen2.5 CANN Executor 与插件的不同执行器
---

# vLLM Ascend Qwen2.5 历史适配证据：7B 文本、Omni 与 Thinker 入口

## 范围与当前未知项

Qwen2.5-7B.po与Qwen2.5-Omni.po共112条业务译文完整读取，均没有同名当前英文页。它们提供历史模型身份与验收线索，不构成当前发布版本的完整部署命令。本卡保持draft/空平台：旧硬件、原生注册和家族介绍分别计证据，未确认当前Ascend各SKU/Runner/量化/图/PD组合。

同名英文缺失不等于停止维护声明；不能套用Qwen2.5-Math-RM-72B的v0.30停止维护结论。当前[支持裁决](vllm_ascend_model_support_resolution.md)对旧扩展Qwen2.5行采取未列出/待验证，也不把缺行解释为明确不支持。CANN Executor的[Qwen Dense](../../concepts/models/qwen_dense.md)有另一执行器、依赖与模型键，不为本插件恢复支持。

## 文本 Qwen2.5-7B-Instruct

旧Qwen2.5-7B.po以Qwen/Qwen2.5-7B-Instruct BF16为例，称从vllm-ascend v0.9.0开始支持，单节点单张Atlas910B4 32GB；另有A2/A3安装页签。支持起点不是所有后来版本保证，页签也不扩大模型已测硬件。简介128K上下文和最多8K输出是模型层声明，不证明这张32GB卡在任何并发/图/缓存条件下能服务该长度。

PO提到额外算子、镜像、deploy.sh与权重目录，但未保留完整代码和环境锁；不从标题恢复安装脚本或当前算子ABI。旧“建议单节点”“PD暂不支持”只按旧教程解释，不作当前框架永久结论。功能例的Beijing文本响应只关闭基本请求阶段，不能证明长上下文、结构化输出或数学质量。

旧精度词条按顺序给GSM8K、accuracy、gen及75.00，结果目录benchmark/outputs/default/；这是来源样例，非本仓成绩，缺数据集/工具/提示/采样和完整版本，不作当前精度门槛。PO的latency/serve/throughput分别指单batch延迟、在线吞吐、离线吞吐，没有可补写的性能数字，不能相互比较为加速。

## Qwen2.5-Omni：3B 与 7B 的历史资料

Qwen2.5-Omni.po标题为7B，同时列Qwen/Qwen2.5-Omni-3B与7B BF16，示例默认7B，旧支持起点v0.11.0rc0。两种checkpoint不因同族名称共享内存、processor或性能数据。旧多NPU段给TP候选1/2/4并称7B无需强制TP，PD也写暂不支持；这些未闭合当前硬件、版本和服务模式。

旧家族简介列文本、图像、音频、视频输入以及自然语音流式响应；实际后端应拆成encoder/processor、Thinker文本生成、Talker/音频生成与流式API分别验收，不能借家族介绍为所选vLLM类添加全部输出路径。旧vllm[audio]依赖建议只涉及软件资源入口，安装成功不证明每种媒体、音频编码器/解码器或流式结果正确。

旧LOCAL_MEDIA_PATH与--allowed-local-media-path用于本地媒体目录线索；不能仅凭模板变量就断言原生vLLM读取某环境键。按目标CLI、服务端实际目录、媒体类型/数量与读取权限核对，有需求才配置本地媒体路径；本次没有访问媒体、请求服务或修改目录权限。旧gpu-memory-utilization不要盲调的提醒也不替代权重、KV、encoder、临时张量和图预算。

### 旧 textVQA 与模态质量

旧PO将vllm-ascend 0.11.0rc0、Qwen2.5-Omni-7B、textVQA、accuracy、gen_base64及A2/A3、83.47/84.04列成扁平词条。按来源顺序可读为A2 83.47、A3 84.04，但缺原始英文表与完整评测栈，本卡保留其历史来源归属，不作为本仓复现或跨硬件精度差的证明。它是视觉问答线索，不证明音频识别WER/CER、语音生成质量、视频理解、工具调用或所有混合输入。

服务启动日志与客户端响应分别留证；音频/视频/图文各用真实目标请求检查processor与结果，再进入任务质量和性能。旧性能段只给基准入口，没有实测TTFT/TPOT/RTF、吞吐或峰值内存，不能从textVQA数字推性能。

## 原生 vLLM v0.32.0 当前入口的有限证据

固定Native 5df63a7203cdb9328d824a27b682e77c7b9928be的registry选段，将Qwen2_5OmniModel与Qwen2_5OmniForConditionalGeneration两个精确键映射到qwen2_5_omni_thinker:Qwen2_5OmniThinkerForConditionalGeneration。HF architecture键、Python实现类和模型展示名分开，不把表格展示类名自动拼成另一个registry键；本次未完整检查所有fallback/动态注册路径，也不宣称某未列字符串全局必失败。

所读Native supported_models.md选段把该Thinker列在Text Generation，例3B/7B，Inputs为T + I(E+) + V(E+) + A(+)。T/I/V/A分别为文本/图像/视频/音频，+表示允许组合，单模态上标+表示可有多项，E表示可输入预计算embedding；这些是原生文档声明，实际数量、shape、格式与processor仍按目标路径。表中LoRA、PP的✅也不恢复Ascend各硬件支持。

Inputs表并不是语音输出能力表；Thinker映射、音频输入依赖和“全模态”名字不能共同拼成Talker/语音流式输出已接入。这里未读完整qwen2_5_omni_thinker实现、音频输出API或Ascend全部消费者，原生注册与文档也不证明这两套固定版本二进制/模型路径已经配对运行。

## 给适配与性能 Agent 的任务输入

先固定完整checkpoint/config、任务输入输出、Native/Ascend/CANN/TorchNPU和硬件，再选择复现历史栈或当前重新适配。沿[新模型适配](../bringup/vllm_ascend_new_model_onboarding.md)确认实际类、权重与prefix；文本、图像、音频、视频和目标输出分别建立最小eager/真实权重基线，再逐项加图、量化、并行和缓存。

保留原始媒体与预处理、token展开、首请求及变长/并发、任务精度和同口径SLO。基准阶段区分文本TTFT/TPOT、视频帧/音频时长、端到端处理和内存，不能将curl文本例、家族参数或旧单卡数字当验收。遇到未核验的输出任务或硬件组合，保持未知并形成具体适配项；本批未下载权重/工具/数据集、运行模型/服务/基准、修改系统或完成NPU/Agent实验。
