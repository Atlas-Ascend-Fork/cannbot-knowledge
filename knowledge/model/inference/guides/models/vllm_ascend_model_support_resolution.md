---
type: Guide
title: vLLM Ascend 模型支持裁决：维护状态、平台、单项功能与版本冲突
description: 按固定支持表及中文译文裁决模型/硬件/单项能力，识别Hy3-preview停止维护、旧扩展模型缺行与长度差异，区分缺行、空白和明确不支持。
tags:
- task.design
- topic.model_adaptation
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/support_matrix/supported_models.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/DeepSeek-V4.1-Flash.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/platform.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/support_matrix/supported_features.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/support_matrix/supported_models.po
  role: supporting
created_at: '2026-10-29T09:52:40Z'
updated_at: '2026-10-30T04:45:44Z'
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
---

# vLLM Ascend 模型支持裁决：维护状态、平台、单项功能与版本冲突

## 范围与裁决产物

本卡固定Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，适用于A2/A3/310P/950的选型和缺口判断。用户希望服务所有硬件/模型是知识覆盖目标，不表示该插件当前对所有组合提供支持。输出“版本+模型revision+architecture+硬件+量化+Runner+拓扑+功能组合+证据等级”，缺项保留未知。

## 五种状态不能压成布尔值

Supported、Experimental、Unverified、Unmaintained、Unsupported分别表示来源维护状态。来源称supported/verified属于上游报告，不是本仓运行结果。表中空白不等同明确不支持，也不能当成功能全开；反之❌、硬校验和专门功能限制必须保留。

先查模型硬件行，再查每项功能，再查精确教程与实现。比如310P Qwen3-Dense/30B的W8A8和FP16路径不能套A2的BF16；SigLIP2是pooling不是生成；950原生混合MX权重也不能当作A2的同一量化方法。

## 遇到冲突时怎样继续

同一提交支持表与教程也可能不一致：DeepSeek-V4.1-Flash表对PD标❌，教程仍有示例且明确不建议生产；不能因此宣布PD已稳定。教程A2/A3使用MRv1，而平台代码对950有MRv2要求，需按平台和版本分别核对，不能扩成“全平台只能V1/只能V2”。

执行时遵守实际startup硬校验和更具体的模型/功能条件，同时保留冲突证据与待验证项；代码可构造仅证明有实现路径，不自动推翻维护状态。没有真实验证的组合只作为适配候选，不能把强制Runner或删除assert视为支持完成。

## 维护状态与历史适配

停止维护不等于数学架构无法运行，也不应把既有CANN Executor/SGLang或旧Ascend知识一并deprecated。若任务确需旧模型，选择相应历史版本、冻结其完整依赖/文档，再独立验收；若坚持最新框架，则作为新适配任务。详见[历史模型入口规则](vllm_ascend_retired_model_version_boundary.md)。

## 验证与停止条件

按[新模型接入](../bringup/vllm_ascend_new_model_onboarding.md)先最小eager/原始精度，再加载、单请求、混batch、图、并行和性能，各阶段保存输入/有效配置/结果。支持表、测试定义和来源benchmark分别计证据，未运行不写verified。冲突未消除、精度失败或关键功能无证据时停止生产可用结论，回已验证组合。本次为静态来源裁决。


## 按任务核对模型与硬件行

以下按固定支持表归并仍维护的45个“模型×任务×平台”行，包含38个支持行、7个实验行；不是45个独立模型。相同声明才合并。每行只在列出的硬件有效，页签标题不能替代行内硬件：Kimi-K3及Qwen3.8-Flash-Next的A2/A3页签行实际仅列A3，950页签多行只列950DT，不能扩为950PR。

“明确支持”是上游单元格✅的声明，不表示本仓运行过，也不证明所有单项可同时开启。BF16、W8A8是该列的来源标注，不代表全部Linear/MoE/KV格式；Dense行的EP✅不构成存在routed experts的架构证据。Chunked=Chunked Prefill，APC=Automatic Prefix Cache；Piecewise/Fullgraph为表中ACLGraph列，具体运行模式还需核对专门指南。未列出的功能在该行为空白，保持未知；“未声明”不等于❌。长度保留来源单位与数值，是该行的声明而非所有显存/并发预算的保证。任务分区按来源章节归档，不改写真实任务：如ASR、Reward Model仍应按模型教程选择API与验收指标。

| 模型 | 来源任务分区 / 硬件 | 上游维护状态 | 明确支持的单项 | 其他显式状态 | 长度与备注 |
| --- | --- | --- | --- | --- | --- |
| DeepSeek V4-Flash / DeepSeek V4-Pro | 文本生成 / 950DT | 支持 | W8A8、Chunked、APC、投机、异步调度、PP、EP、DP、PD、Fullgraph | 未声明 | 长度标注：1M；原生混合MXFP8/MXFP4权重 |
| GLM-5.1 | 文本生成 / 950DT | 支持 | BF16、W8A8、Chunked、APC、投机、异步调度、TP、EP、DP、PD、Fullgraph | 未声明 | 长度标注：200k |
| GLM-5.2 | 文本生成 / 950DT | 支持 | W8A8、APC、投机、异步调度、TP、PP、EP、DP、PD、Fullgraph | 未验证：BF16、Chunked、Piecewise | 长度标注：🟡；W8A8C8 MXFP8或W4A4C8 MXFP4 |
| GLM-5.3 | 文本生成 / 950DT | 支持 | W8A8、APC、投机、异步调度、TP、PP、EP、DP、PD、Fullgraph | 未验证：BF16、Chunked、Piecewise | 长度标注：1M；W8A8C8 MXFP8或W4A4C8 MXFP4 |
| DeepSeek V4-Flash / DeepSeek V4-Pro | 文本生成 / A2/A3 | 支持 | BF16、W8A8、Chunked、APC、投机、异步调度、TP、EP、DP、PD、Fullgraph | 未声明 | 长度标注：1M |
| Qwen3-Dense | 文本生成 / A2/A3 | 支持 | BF16、W8A8、Chunked、APC、异步调度、TP、DP、Piecewise、Fullgraph | 未声明 | 长度标注：128k |
| Qwen3-30B-A3B | 文本生成 / A2/A3 | 支持 | BF16、W8A8、Chunked、APC、投机、异步调度、TP、EP、DP、Piecewise、Fullgraph | 未声明 | 未声明 |
| GLM-5.1 | 文本生成 / A2/A3 | 支持 | BF16、W8A8、Chunked、APC、投机、异步调度、TP、PP、EP、DP、PD、Piecewise、Fullgraph | 未声明 | 长度标注：200k |
| GLM-5.2 | 文本生成 / A2/A3 | 支持 | BF16、W8A8、Chunked、APC、投机、异步调度、TP、PP、EP、DP、PD、Piecewise、Fullgraph | 未声明 | 长度标注：200k；W8A8C8 |
| GLM-5.3 | 文本生成 / A2/A3 | 支持 | BF16、W8A8、Chunked、APC、投机、异步调度、TP、PP、EP、DP、PD、Piecewise、Fullgraph | 未声明 | 长度标注：135k (A2) / 1M (A3)；W8A8C8 |
| Gemma4 | 文本生成 / A2/A3/950PR&950DT | 实验 | BF16、Chunked、APC、异步调度、TP、DP、Piecewise、Fullgraph | 未声明 | 未声明 |
| Hy4-preview (Experimental) | 文本生成 / A3 | 实验 | 未声明 | 未声明 | 未声明 |
| Qwen3-Dense | 文本生成 / 310P（Atlas 300I DUO） | 支持 | W8A8、Chunked、APC、异步调度、TP、Piecewise、Fullgraph | 不支持：BF16、LoRA、PD；未验证：投机 | 长度标注：20k |
| Qwen3-30B-A3B | 文本生成 / 310P（Atlas 300I DUO） | 支持 | W8A8、Chunked、APC、异步调度、TP、Piecewise、Fullgraph | 不支持：BF16、LoRA、PD；未验证：投机 | 长度标注：16k |
| SigLIP2 | Pooling / 310P（Atlas 300I DUO） | 支持 | 未声明 | 实验：W8A8 | FP16；文本/图像embedding |
| GLM-5.3-Flash | 多模态生成 / 950DT | 支持 | BF16、W8A8、Chunked、APC、投机、异步调度、TP、PP、EP、DP、PD、Piecewise、Fullgraph | 未声明 | 长度标注：133120；文本/图像/视频 |
| Qwen3.5-397B-A17B | 多模态生成 / 950DT | 支持 | BF16、W8A8、Chunked、APC、投机、异步调度、TP、EP、DP、PD、Piecewise、Fullgraph | 未声明 | 长度标注：1010000；文本/图像/视频 |
| Qwen3.6-27B | 多模态生成 / 950DT | 支持 | BF16、W8A8、Chunked、APC、投机、异步调度、TP、EP、DP、PD、Piecewise、Fullgraph | 未声明 | 长度标注：262144 |
| Qwen3.6-35B-A3B | 多模态生成 / 950DT | 支持 | BF16、W8A8、Chunked、APC、投机、异步调度、TP、EP、DP、Piecewise、Fullgraph | 不支持：PD | 长度标注：135168 |
| Kimi-K3 | 多模态生成 / 950DT | 支持 | APC、投机、TP、EP、DP、PD、Fullgraph | 未声明 | 长度标注：131072；W4A8；DSpark；FULL_DECODE_ONLY；KV Cache Pool |
| MiniMax-M3 | 多模态生成 / 950DT | 支持 | Chunked、APC、投机、异步调度、TP、PP、EP、DP、PD、Fullgraph | 未验证：Piecewise | 长度标注：1M；MXFP8；文本/图像/视频 |
| Step-5-Preview | 多模态生成 / 950DT | 实验 | W8A8、Chunked、APC、投机、异步调度、TP、PP、EP、DP、Fullgraph | 未声明 | 长度标注：1M；实验性 |
| MiniMax-M3.1-Flash | 多模态生成 / 950DT | 实验 | W8A8、Chunked、APC、投机、异步调度、TP、PP、EP、DP、PD、Fullgraph | 未验证：Piecewise | 长度标注：1M；实验性 |
| GLM-5.3-Flash | 多模态生成 / A2/A3 | 支持 | BF16、W8A8、Chunked、APC、投机、异步调度、TP、PP、EP、DP、PD、Piecewise、Fullgraph | 未声明 | 长度标注：200k (A2) / 1M (A3)；文本/图像/视频 |
| Qwen3-VL | 多模态生成 / A2/A3 | 支持 | TP、Piecewise、Fullgraph | 未声明 | 未声明 |
| Qwen3-VL-30B-A3B | 多模态生成 / A2/A3 | 支持 | BF16、W8A8、Chunked、APC、异步调度、TP、EP、DP、PD、Piecewise、Fullgraph | 未声明 | 长度标注：262144 |
| DeepSeek-V4.1-Flash | 多模态生成 / A2/A3 | 支持 | W8A8、APC、投机、TP、EP、DP、Fullgraph | 不支持：LoRA、PP、PD、Piecewise；未验证：BF16、Chunked、异步调度 | 长度标注：1048576；W8A8；A3两节点或A2四节点混部 |
| Qwen3.5-397B-A17B | 多模态生成 / A2/A3 | 支持 | BF16、W8A8、Chunked、APC、投机、异步调度、TP、EP、DP、PD、Piecewise、Fullgraph | 未声明 | 长度标注：1010000；文本/图像/视频 |
| Qwen3.5-27B / Qwen3.6-27B | 多模态生成 / A2/A3 | 支持 | BF16、W8A8、Chunked、APC、投机、异步调度、TP、EP、DP、PD、Piecewise、Fullgraph | 未声明 | 长度标注：262144 |
| Qwen3.6-35B-A3B | 多模态生成 / A2/A3 | 支持 | BF16、W8A8、Chunked、APC、投机、异步调度、TP、EP、DP、Piecewise、Fullgraph | 不支持：PD | 长度标注：135168 |
| Qwen3.8-Flash-Next | 多模态生成 / A3 | 实验 | BF16、W8A8、Chunked、APC、投机、异步调度、TP、EP、DP、PD、Piecewise、Fullgraph | 未声明 | 长度标注：262144 |
| Kimi-K2.6 | 多模态生成 / A2/A3 | 支持 | Chunked、APC、投机、异步调度、TP、EP、DP、PD、Piecewise、Fullgraph | 未声明 | 长度标注：262144 |
| Kimi-K3 | 多模态生成 / A3 | 支持 | APC、投机、TP、EP、DP、PD、Fullgraph | 未声明 | 长度标注：131072；W4A8；DSpark；FULL_DECODE_ONLY；KV Cache Pool |
| MiniMax-M3 | 多模态生成 / A2/A3 | 支持 | BF16、W8A8、Chunked、APC、投机、异步调度、TP、PP、EP、DP、PD、Fullgraph | 未验证：Piecewise | 长度标注：1M；文本/图像/视频；ViT DP |
| MiniMax-M3.1-Flash | 多模态生成 / A2/A3 | 实验 | W8A8、Chunked、APC、投机、异步调度、TP、PP、EP、DP、PD、Fullgraph | 未验证：Piecewise | 长度标注：1M；实验性 |
| Cohere Transcribe | 多模态生成 / A2/A3 | 实验 | BF16 | 不支持：W8A8、LoRA、投机、PD；未验证：TP、Piecewise、Fullgraph | 2B Conformer编码器-解码器ASR；14种语言，03-2026及arabic-07-2026权重 |
| Qwen3-VL | 多模态生成 / 310P（Atlas 300I DUO） | 支持 | W8A8、Chunked、APC、异步调度、TP、Piecewise、Fullgraph | 不支持：BF16、LoRA、PD；未验证：投机 | 长度标注：16k |
| Qwen3.5-Dense / Qwen3.5-35B-A3B / Qwen3.5-27B / Qwen3.6-27B / Qwen3.6-35B-A3B / Qwen3.8-27B | 多模态生成 / 310P（Atlas 300I DUO） | 支持 | W8A8、Chunked、APC、投机、异步调度、TP、Piecewise、Fullgraph | 不支持：BF16、LoRA、PD | 长度标注：256k |

## 容易生成错误配置的边界

- Qwen3.6-35B-A3B在A2/A3与950DT行的PD均为❌；不能借397B的PD示例推导35B支持。310P的PD也为❌。
- GLM-5.2/5.3在950DT行的BF16、Chunked、Piecewise均为🟡；GLM-5.2的最大长度也是🟡。A2/A3行的肯定状态不能覆盖950行。GLM-5.3的A2 135k与A3 1M分开规划。
- DeepSeek-V4.1-Flash的A2/A3行对LoRA、PP、PD、Piecewise明确为❌，对BF16、Chunked、异步调度为🟡。PP指南的模型接口表或教程候选不能改写这些状态；实际950路径需继续按专属教程/校验核对，不能把A2/A3表扩到950。
- 310P各Qwen生成行的BF16、LoRA、PD为❌；FP16候选从具体教程取证，不能从“BF16不支持”反推任意其他dtype都支持。Qwen3/Qwen3-VL的投机为🟡，Qwen3.5/3.6/3.8 Hybrid行的投机为✅，不能按品牌统一。
- Cohere Transcribe为实验ASR；W8A8、LoRA、投机、PD明确不支持，TP与两类图为未验证。通用功能表的Enc-dec Planned与这个具体模型的实验实现并存，不能由一者宣称所有编码器-解码器均支持或均无实现。
- SigLIP2为310P的FP16文本/图像pooling，模型✅但W8A8🔵；模型维护状态与量化成熟度必须分开。
- 未列出的模型仍需独立验证；例如有[Qwen3.8大MoE教程](vllm_ascend_qwen38_large_moe.md)不代表本支持表已经列出该组合。

按对应[模型指南索引](index.md)取得权重、Runner、cache及拓扑的具体条件，再用[功能组合裁决](../integration/vllm_ascend_feature_combination_resolution.md)核对叠加。停止维护的33行（含畸形Pooling行）保留在[历史模型边界](vllm_ascend_retired_model_version_boundary.md)，其单项✅不恢复维护承诺。


## 中文supported_models.po与当前模型矩阵

固定supported_models.po的68条有效业务译文已对照同提交完整英文，37条msgid连续匹配、31条未匹配，0 fuzzy/obsolete/空翻译。它不是完整英文表的逐行翻译清单：部分当前行仍来自英文，旧扩展条目也可滞留PO。匹配只说明源字符串对应，不证明网站已正确生成、具体组合或本仓NPU结果；页首issue1608仅是来源给出的最新信息链接，本批未读取其当前内容。

| 旧PO中的行/数值 | 当前英文对应状态与裁决 |
| --- | --- |
| GLM-5.1的A2/A3行🔵，Kimi-K2.6的A2/A3行🔵 | 当前均为✅；950DT的GLM-5.1行原本已是✅，不能说所有硬件行都经历相同变化。单项列/真实模型配置仍逐项核对。 |
| Qwen3.5-397B-A17B、Qwen3.5-27B / Qwen3.6-27B的A2/A3行🔵 | 当前为✅；397B的说明增加文本/图像/视频，不据此把所有输入、processor或任务质量当已测。 |
| Qwen3.6-35B-A3B的A2/A3行🔵，投机🔵，长度262144 | 当前该行模型与投机均为✅，长度标注135168；PD仍❌。不从支持状态推进推导PD也解禁，不把旧262144继续用于该行容量声明；实际checkpoint/显存与并发仍另验。 |
| Qwen2.5-Math-RM-72B文本和Pooling行🔵 | 当前为🔴；旧vllm-rm、TP4/max_model_len4096及gsm8k_correctness accuracy=0.80属于来源历史线索，不恢复当前维护，也不代表本次达到该准确率。详见[历史模型边界](vllm_ascend_retired_model_version_boundary.md)。 |
| 950DT的Qwen3.5-397B-A17B行仍✅但msgid不匹配 | 当前备注/格式增加媒体说明；不把每个未匹配项都解释为维护状态改变。 |
| Expert Parallel表头、950DT/950PR页签及旧图例bullets | 当前有Expert Parallelism和图例详细表等结构/文字变化；以行内硬件及单项列为准，不从页签排序或表头名称推演新增能力。 |

旧PO中的Extended Compatible Models分区已不在当前英文。Ernie4.5、Ernie4.5-Moe、Phi-3-Vision/Phi-3.5-Vision、Llama2/3/3.1/3.2、单列Llama3.2、Qwen2.5的🔵，以及DeepSeek V2.5、Mllama、MiniMax-Text、Ultravox的🟡，都不作为当前表的支持承诺；当前缺行保留“未列出/待独立验证”，不改写成❌或🔴。

InternVL2.0/2.5/3.0、InternVideo2.5/Mono-InternVL旧PO行有❌并链接issue2064，当前英文没有该旧行；本批未读取该Issue，不由旧条目给所有当前版本作全局不支持结论。Qwen2.5-based的FP16 classification旧扩展行也不作为当前Pooling接口。模型名相近、原生registry存在或旧模型有经验都只提供适配候选，仍沿[模型接入](../bringup/vllm_ascend_new_model_onboarding.md)验证实际任务/权重/状态。

旧Hy3-preview行的内容/格式已变，但当前仍🔴，不能只因msgid不匹配把它转回实验。当前Qwen/GLM等完整维护行与历史33行仍按前文分开读取；缺行与停止维护是不同证据，不把旧CANN Executor/SGLang或历史昇腾知识随之删除。

处理中文资料时保留原msgid/msgstr与当前英文对应行，先区分编辑变化、状态推进、状态退役、功能/长度变化和整段移除，再按代码guard/具体教程裁决。缺少当前英文段落时，不靠旧PO自动补回官方页面或生成可执行部署模板。本次只读固定矩阵/译文与既有卡，没有执行模型、外部Issue、网站构建或NPU验证，也没有新增verified。
