---
type: Guide
title: SGLang Ascend 后端注册与拒绝条件：混合状态、K-pool和图变体
description: 区分NPU实际注册的Ascend、V4、GDN和KDA后端，保留短卷积侧状态缺口及K-pool和GPU图变体不可直接迁移的边界。
tags:
- task.implementation
- topic.attention
- topic.kv_cache
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/attention/attention_registry.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/attention/dsa/dsa_indexer_kpool.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/attention/graph_variants.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/attention/mamba/mamba.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/utils/device.py
  role: implementation
created_at: '2026-11-08T12:07:53Z'
updated_at: '2026-11-09T04:32:54Z'
platforms: []
aliases:
- IndexerKPool
- ShortConvAttnBackend
- NPU attention registry
---

# SGLang Ascend 后端注册与拒绝条件：混合状态、K-pool和图变体

## 选择后端时先核对可达实现

`ascend`注册到 `AscendAttnBackend`；`dsv4`在NPU注册到 `DeepseekV4AscendAttnBackend`。若为HIP/NPU而请求 `cutedsl_h16` V4 prefill，初始化直接报错，因为该实现要求CUDA SM90。注册名称可以跨平台相同，实现类及限制仍由平台分支决定。

混合GDN模型在NPU替换为Ascend GDN与hybrid类，prefill和decode都必须选择ascend。Kimi线性模型替换为 `AscendKDAAttnBackend` 和专用KDA hybrid类，不能照搬默认FlashInfer前缀；GLM5-next的共享KDA分支是另一条注册路径，应单独核对。draft worker假设MTP/NEXTN使用full attention，并把full层列表设为[0]。

## 明确未实现的路线

短卷积混合ZAYA1 CCA、LFM2/LFM2-MoE等需要 `conv_state_metadata()` sidecar；Ascend hybrid/mamba类没有该方法，注册阶段提前抛NotImplementedError。不能以NPU有causal_conv1d原语推断整模型状态管理可用。

`IndexerKPool`存在NPU的custom_ops导入，但没有专门 `forward_npu`；其计算末尾明确只接收CUDA/ROCm，否则报错。K-pool的分页MQA、压缩写和breakable graph流程不能因独立sgl-kernel-npu库中存在同名原语而视为本版本模型路线已接通。

`graph_variants.py`只为HIP DSA建立dense/sparse图变体，且排除K-pool；V4.1候选图要求 `model_runner.device=="cuda"`，并在 HIP 分支检查 gfx95 家族支持、非 HIP 分支检查 CUDA 计算能力主版本 >=10；HIP 在 PyTorch 中也使用 cuda 设备名。NPU 不满足该设备条件。NPU的NPUGraph实现不自动获得这些GPU图变体。gfx950是AMD架构标识，不能与Ascend 950混用。

## 适配与验证

排查启动失败时，记录解析后的prefill/decode后端、模型hybrid配置和draft身份，再按注册类检查是否具备需要的状态方法。新增原语接入必须同时闭合元数据、状态池、投机接受后提交与图重放，而不能只补import。建议用startup guard、首个prefill、连续decode和verify后续轮次分别验收；本次仅核对源码，没有执行服务测试。芯片范围未按各路线证明，保持draft和空平台。
