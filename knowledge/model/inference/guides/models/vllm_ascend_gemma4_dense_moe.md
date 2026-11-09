---
type: Guide
title: vLLM Ascend Gemma4：Dense/MoE、多模态与 950 MXFP4 分支
description: 按31B Dense和26B-A4B MoE区分并行与量化，先验证BF16多模态基线，再评估图和950的ModelSlim MXFP4，保留实验维护状态。
  补充中文教程核对、完整checkpoint身份、API/离线配置差异与GPQA文本和图像分层验收。 明确 Gemma4 的 API alias 与本地权重路径、32768
  上下文的 KV cache 预算，并区分 batch 激活内存和 HBM 余量。
tags:
- task.implementation
- topic.model_adaptation
- topic.multimodal
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Gemma4.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/support_matrix/supported_models.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Gemma4.po
  role: supporting
created_at: '2026-10-29T09:52:40Z'
updated_at: '2026-10-30T17:05:24Z'
platforms:
- a2
- a3
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend Gemma4：Dense/MoE、多模态与 950 MXFP4 分支

## 范围与维护状态

教程覆盖A2/A3/950的31B-it Dense与26B-A4B-it MoE；总支持表仍标Experimental，不能因教程用supported词就宣布生产认证。机制可参考既有Gemma4概念卡，当前指南只描述vLLM Ascend部署与验收契约。

## 权重、并行与图选择

先固定BF16权重revision，用eager与能容纳的TP拓扑核对加载、文本和图像，再比较FULL_DECODE_ONLY/PIECEWISE。MoE才可选EP；Dense权重即使相同family也不能启EP。max-model-len是单请求输入+输出上限，不按模型名盲设最大上下文。

950的Eco-Tech31B/26B-A4B MXFP4 checkpoint带quant_model_description.json，来源要求quantization=ascend；BF16例子省略量化。示例TP4DP2用8NPU，不是每平台固定最优，也不能把MXFP4支持外推A2/A3。packed shard和省略v_proj例外遵守[量化映射指南](../integration/vllm_ascend_modelslim_scheme_adaptation.md)。

## 验收与优化顺序

分别核对实际model class、Dense/MoE层和量化scheme，按权重generation_config匹配max_tokens/temperature/stop。HTTP200与choices只作smoke，真实质量用固定文本/多模态评测；图与量化分别对照原精度基线。

先图，再按真实上下文调KV、并发与token budget，记录运行峰值余量；EP/TP拓扑作为独立变量比较，不能把位宽节省直接当端到端加速。失败关闭新增量化/图或回eager原权重，不绕过硬校验。本次未运行Gemma4或GPQA评测。


## 中文教程与权重身份：先锁定实际运行对象

本节对照固定 ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2 的 Gemma4.md 全文与中文 Gemma4.po 103 条业务译文；msgid 全部可在该英文中定位，但这不证明发布站点 HTML 与该快照一致。教程中的 latest main 指写作分支，A5 镜像使用版本模板；应按[环境版本指南](../deployment/vllm_ascend_versioned_environment.md)锁定实际组合，不将模板或 pip show 输出当端到端兼容证明。支持矩阵仍为 Experimental，原平台范围 A2/A3/950 不扩展到 310P。

| 完整 checkpoint 名称 | 本教程身份 | 配方边界 |
| --- | --- | --- |
| google/gemma-4-31B-it | BF16、31B Dense | 先按可用设备和内存选择 TP，不加量化参数 |
| google/gemma-4-26B-A4B-it | BF16、总参约26B/激活约4B的 MoE | 按部署计划选择 TP/EP，不能仅以激活参数估算所需内存 |
| Eco-Tech/gemma-4-31B-it-w4a4-mxfp4 | 950 MXFP4 Dense | quant_model_description.json 与 quantization ascend 一起核对；Dense 不启 EP |
| Eco-Tech/gemma-4-26B-A4B-it-w4a4-mxfp4 | 950 MXFP4 MoE | 同样需要量化元数据和参数；示例另启 EP |

950 量化表给出一个 96GB×8 的 950DT 节点，命令为可见设备0–7、TP4DP2、max-model-len=32768、FULL_DECODE_ONLY；这是八 NPU 配方，不能当所有950型号、所有上下文的最优或最低配置。BF16 基线为四可见设备、TP4、32768，先 enforce-eager，再比较图；MXFP4 flag 不把 BF16 权重在线转换成目标 checkpoint。安装示例对950DT选择匹配版本的 A5 image，其他平台按各自安装入口核对设备映射和权重挂载；设备列表与包版本检查只是环境前置条件。

## 文本、图像、离线与精度验收分开

在线 API 的 served-model-name 为 gemma4，Completion 与 Chat 请求都用这个服务别名；离线 LLM 则用实际本地权重目录。MODEL_PATH 及 /root/.cache/path/to/gemma4 是占位符，必须在调用方、容器挂载、离线和评测配置中分别核对，不能用 checkpoint 下载名或不存在的目录代替服务别名。

功能示例的 max_tokens=128、temperature=0 只用于文本与图像请求。图像 Chat 在 content 中同时给 image_url 和 text，教程用 tiger.jpeg URL；HTTP200、choices 文本与图像描述是分层 smoke 预期，没有证明视频、音频、所有图像尺寸或视觉质量。需要实际保留输入媒体、processor/chat template、生成输出和结束原因；不把文本基线通过当多模态验收完成。

离线示例是本地路径、TP4、FULL_DECODE_ONLY 的文本 generate，没有在线950 MXFP4配方的DP2、量化参数和MoE EP。两者不能直接互作同配置性能对照；选量化权重时先完整核对其加载契约，不能直接套用省略相关参数的离线示例。教程未给出离线多模态负载或离线性能结果。

精度示例为在线 gpqa_diamond，lm_eval 选 local-completions，model=gemma4、base_url 指向 /v1/completions，并设 tokenized_requests=False、trust_remote_code=True。它是文本任务入口，没有本教程实测分数，也不替代图像精度。max_tokens、temperature、stop 等须对齐该权重 generation_config.json；不要将 smoke 的128/0强行当精度评测参数。AISBench 与 vLLM benchmark 在该教程主要给入口链接，不能据此补造吞吐、TTFT、精度阈值或跨硬件排名。

## 优化顺序与另一套实现的边界

按相同权重与真实请求负载比较：eager 正确性→FULL_DECODE_ONLY/PIECEWISE图→所需上下文与KV容量→max-num-batched-tokens及激活内存→max-num-seqs与排队→gpu-memory-utilization及HBM余量→MoE并行策略。长上下文OOM先核对并发和KV；增大token budget也会增激活开销。教程场景表的4/8NPU都是参考，不推断图或量化必然带来端到端加速。指标口径配合[性能基准指南](../optimization/vllm_ascend_benchmark_workflow.md)，实际模型和NPU测量尚未执行。

仓库中的[Gemma4 文本 Decoder 部署](gemma4_26b_a4b_deployment.md)主来源为另一套固定 cann-recipes-infer 实现，覆盖 Language MoE Decoder 与EP8等配置；它的backend、cache布局、精度限制及A2/A3性能观测不自动适用于这里的 vLLM 多模态或950 MXFP4路径。新模型 Agent 应先识别实现仓库、版本、模型变体与媒体路径，再复用配置和排障结论。


### Gemma4 服务身份与容量验收

为 Gemma4 同时记录 API alias（本教程为 gemma4）和实际本地权重路径：一个是请求路由的服务别名，一个是加载对象的位置，二者分别与请求 model、served-model-name、挂载和离线 LLM 参数核对。没有完成这层身份检查，不能把错误归因到模型算子。

32768 是上述 Gemma4 配方的单请求输入加输出上限，仍需按真实 token 与并发核对 KV cache 预算。batch 的激活内存与 KV cache 都会占用 HBM；增大 token budget、并发或上下文时分别记录峰值与余量。只看到 HBM 尚有空闲或一条请求成功，不足以证明目标混合负载可持续运行。以上是教程调优条件的归纳，没有新增模型执行或测量结果。
