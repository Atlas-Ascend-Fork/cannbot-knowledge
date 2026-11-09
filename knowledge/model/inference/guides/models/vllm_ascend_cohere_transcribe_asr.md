---
type: Guide
title: vLLM Ascend Cohere Transcribe：A2 ASR、长度预算与音频评测
description: 按 Conformer encoder-decoder 的 BF16 单卡基线接入音频，核对block size、max-model-len和processor依赖，以WER/CER与音频RTF验收。
  补充中文81条、两权重CV18/100样本口径和原生CPU音频处理/缓存边界。
tags:
- task.implementation
- topic.multimodal
- topic.model_adaptation
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Cohere-Transcribe.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/support_matrix/supported_models.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/support_matrix/supported_features.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Cohere-Transcribe.po
  role: supporting
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/transformers_utils/processors/cohere_asr.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/model_executor/models/cohere_asr.py
  role: constraint
created_at: '2026-10-29T09:52:40Z'
updated_at: '2026-10-30T11:21:27Z'
platforms:
- a2
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend Cohere Transcribe：A2 ASR、长度预算与音频评测

## 范围与证据差异

cohere_asr为2B Conformer encoder-decoder ASR，来源教程给A2 64GB单卡BF16基线、03-2026多语与07-2026Arabic微调两权重。总表列A2/A3实验，但详细测试与配方仅A2，本卡取较窄范围；950只是计划，不写支持。来源内部报告不是本仓实测。

## 接入与内存边界

匹配vLLM/Ascend镜像、librosa和模型自定义代码依赖，以TP1、dtype=bfloat16、eager、block-size=128先运行。源码说明block至少128，不按常规decoder的更小block假定。权重revision及processor固定，音频通过chat消息audio_url构造，响应model与served-model-name一致。

max_model_len自动取过大值会生成完整causal mask，内存随长度平方增长，初始化OOM先显式限制如4096并按实际音频需求逐步加大。不要把加大KV预算当成解决所有mask峰值的方法，也不以文本token长度代替音频时长。

## 验收与测量

功能覆盖短/长音频、代表性语言、静音/边界和并发，对齐转写参考。文本正规化一致后统计WER/CER；多语基座与Arabic微调需用相同样本再比较。来源100样本和10471样本指标不能混作同一评测集，vLLM0.23内部结果不能外推0.32基线。

性能同时记录总音频秒数、处理时间、RTF=处理时间/音频时长、RTFx及E2E延迟/吞吐，包含音频预处理和请求开销。文本随机负载不能作为ASR服务基准。source单卡配置不证明TP/图/PD组合，逐项取得证据再扩展。

## 停止与回退

识别率失败先查音频解码、processor、语言与权重版本；OOM回长度/并发基线；未知图或并行关闭后再比对。无可复核内部报告原始数据时仅标来源披露，不写verified。本次没有下载权重、运行音频或复测指标。


## 通用功能表不能替代具体模型边界

同提交通用表仍将Enc-dec列为Planned；模型表则将Cohere Transcribe列为A2/A3实验实现，BF16✅，W8A8/LoRA/投机/PD❌，TP及Piecewise/Fullgraph🟡。这两个层级不能合并成“所有编码器-解码器都可用”或“没有ASR实现”。本卡A2单卡基线也不证明多卡TP或图已经验收。


## 中文资料、权重与来源指标

Cohere-Transcribe.po 的81条有效译文均匹配当前英文；它们不是所有英文代码块/表格的独立中文副本。来源明确CohereLabs/cohere-transcribe-03-2026为14语言基座，CohereLabs/cohere-transcribe-arabic-07-2026为Arabic微调，两者权重与revision分别记录。基座列英语、法语、德语、意大利语、西班牙语、葡萄牙语、希腊语、荷兰语、波兰语、普通话、日语、韩语、越南语、阿拉伯语；下面的Arabic结果不当全部14语言的质量证明。

| 来源评测集/范围 | 03-2026 | Arabic 07-2026 | 解释 |
| --- | --- | --- | --- |
| 同一100条Common Voice Arabic | WER9.06%、CER2.96% | WER5.28%、CER1.27% | 来源称同事/内部报告；没有原始样本/归一化/完整环境，不当本仓结果。 |
| CV18 Arabic test 10,471条 | 未在此给出 | WER5.69%，另引官方5.82% | 不与100条子集混算，不据差值证明本次NPU优于官方实现。 |
| 同一100条、总音频440秒，vLLM0.23.0+Ascend | 时间47s、RTF0.107、RTFx9.4 | 时间44s、RTF0.100、RTFx10.0 | 已舍入来源数值；不移植为v0.32吞吐或SLO。 |

CV18细分是累计门槛：WER=0为2931/10471（28.0%）、WER<5%为6990（66.8%）、<10%为8116（77.5%）、<20%为9145（87.3%）。这些集合重叠，不能当互斥桶相加。来源“约6.5%更快”依RTF等舍入口径，不能把RTF下降百分比、时间下降与吞吐增幅当同一精确值，RTF/RTFx倒数也不要由已舍入表值强求精确相等。

镜像Up、pip show、Application startup complete及HTTP200/choices各自只是阶段信号；示例audio_url为占位地址，没有提供测试音频。离线标志要求已有本地权重/配置，不能下载缺件；各节点同名/root/.cache不证明共享文件系统或相同revision。本次未获取内部报告、音频或权重，没有测WER/RTF。

## 前处理与当前框架的交接

原生v0.32所读CohereASRProcessingInfo直接用hf_config.preprocessor建立CPU feature extractor，缓存processor对象，另配置MultiModalDataParser目标采样率。不要由trust-remote-code或同名类推断实际选的是远端processor；该标志仍可能承担模型配置/tokenizer等加载职责。实际音频媒体解码和重采样还要沿parser闭合。

CohereASRFeatureExtractor的单独调用没有使用sampling_rate参数做校验或重采样；输入shape、实际采样率与模型期望需在正确层对齐。默认dither在推理时仍可加噪，CohereASRMultiModalProcessor对此绕过处理缓存；不是KV/APC或编译缓存开关。关闭dither以换缓存会改变特征，先对齐语言/权重/WER再谈性能。

音频samples、Mel逻辑帧、pad后矩阵宽度、subsampling后的音频占位token及decoder输出不是同一单位。详见[音频处理契约](../../concepts/frameworks/vllm_ascend_cohere_audio_processor.md)。本卡仍只取A2详细配方，A2/A3实验矩阵、950计划及未验证TP/图状态不被CPU代码扩展。
