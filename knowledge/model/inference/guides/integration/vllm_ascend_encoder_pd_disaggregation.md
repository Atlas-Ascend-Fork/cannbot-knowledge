---
type: Guide
title: vLLM Ascend EPD：编码缓存与 P/D 传输的分离接入
description: 结合EPD中文与原图区分Encoder/Prefill传输的EP和专家并行，分别核对EC/KV缓存、进程/设备共置及1E1PD/1E1P1D参考路径。
tags:
- task.implementation
- topic.multimodal
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/epd_disaggregation.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/epd_disaggregation.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/images/epd_disaggregation.jpg
  role: supporting
created_at: '2026-10-29T09:45:39Z'
updated_at: '2026-10-30T07:18:05Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend EPD：编码缓存与 P/D 传输的分离接入

## 范围与证据边界

draft：来源给出 disaggregated_encoder 的 ExampleConnector 参考和1E1PD/1E1P1D脚本，没有独立硬件/模型支持矩阵。它说明架构与接入路径，不承诺所有多模态模型或服务拓扑可用。

## 两类缓存和角色

Encoder 实例产出视觉/多模态 embedding；ECConnector 的 scheduler 查存在并计划load，worker把embedding加载给语言模型。P/D之间另传Attention KV。EC命中与KV命中、embedding字节与KV layout、两条connector配置不能混作一个开关。

EPD proxy对纯文本与多模态分路，并按实例负载调度。先定义请求/输入identity、encoder输出与placeholder token位置的对应，保持processor/模型版本一致；这些是适配验收要求，不能从示例推导跨版本embedding可复用。

## 接入与验收

先构建共置多模态基线，再试1E1PD，验证图片/音频输入、embedding shape/dtype、插入位置及输出；再拆为1E1P1D，沿各自PD connector验收。来源MooncakeLayerwise流程为D端触发remote prefill、P逐层推KV，不能假设等同其他V1/V2 connector协议。跨进程缓存的 mm-processor-cache 配置按目标版本检查，来源措辞不足以替代实验。

分别测encode、EC传输、Prefill、KV传输、Decode及总体TTFT，避免把encoder缓存收益归给PD。故障覆盖EC缺失、输入不匹配和P/D传输失败；关闭拆分回共置基线。CPU或API请求成功不证明目标NPU/模型支持，本次未运行示例。


## 中文EPD与原图中的两条传输链

epd_disaggregation.po的32条译文对应当前英文；epd_disaggregation.jpg按原始分辨率阅读。图中多模态请求经Proxy到Encode实例，纯文本旁路Encoder进入Prefill；E有MM Cache/Encoder Weights，P有MM Cache/KV Cache/LLM Weights，D有KV Cache/LLM Weights。E→P的EP Connector在此表示编码到预填充传输，不是Expert Parallelism；P→D的PD Connector另传KV。图示不能替代EC/PD两套实际connector的key、payload、布局与完成事件验证。

底部六种摆放包括三设备分离E/P/D、E与P独立实例同设备后接D、E与D同设备后接P、E+P与D、E与P+D，以及E/P/D全在一设备。它区分进程、实例、阶段与设备共置；图里的NPU编号和实例叠层不是固定设备需求、产品支持矩阵或六种方案已跑过的证明。当前可用参考入口仍是ExampleConnector的1E1PD和1E1P1D，不能从总览图声称任意部署可运行。

页面将encoder轻量、encode/prefill计算密集而decode带宽密集作为设计动机，不是任意视觉/音频/视频模型的瓶颈测量。通过实例独立扩缩、共享EC和纯文本旁路获得收益的条件，需要测编码耗时、embedding传输、排队和总体TTFT/ITL；least-loaded/优先队列的概述不是严格公平或故障重试保证。

当前限制仍写“Disable --mm-processor-cache-gb 0”，英文/中文均未消除措辞歧义，不能直接改写成某个已验证跨进程缓存设置。按实际processor cache与EC配置留有效值、命中/错失和输出，先保证共置基线正确。外部Google设计文档、所有示例/代理/EC实现和真实NPU本批未重新读取或运行，图示阅读不当完整执行链证明。
