---
type: Guide
title: GLM-5.3 在 A3 与950的未验证参考部署拓扑
description: 融合A3单节点改编、四节点PD及950 MXFP8参考分支，保留未独立硬件验证、MTP与MemFabric边界。
tags:
- task.implementation
- task.optimization
- topic.model_serving
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/glm_5_3.mdx
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/cookbook/autoregressive/GLM/GLM-5.3.mdx
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/src/snippets/configs/zai-org/glm-5.3.jsx
  role: supporting
created_at: '2026-11-08T11:58:59Z'
updated_at: '2026-11-08T12:38:11Z'
platforms:
- a3
- '950'
---

# GLM-5.3 在 A3 与950的未验证参考部署拓扑

## 证据强度与环境

该教程明确说明配置没有经过独立硬件验证；单节点配置由 GLM-5.2 改编。因此本卡保持 draft，脚本不是已测性能或所有平台的支持声明。GLM-5.3 使用 DSA/MTP；它与单独发布的 GLM-5.3-Flash 不同，不能共享 checkpoint 或直接套用 attention 假设。

来源 BF16 权重约 1.51TB；脚本使用本地 ModelSlim W8A8 转换产物，大小和 MTP 可用性依转换结果而定。启用 NEXTN 前须确认 MTP 权重。教程要求 CANN9.1、匹配的 SGLang/TorchNPU/ATB/custom operators，PD 另需 MemFabric；基础 CANN 容器本身不代表已装好这些组件。页面虽有 A2 容器标签，实际多节点拓扑明确为 A3，不能据此证明 A2 完整运行。

## 角色与端口

双节点混部是 TP32/DP16、DeepEP auto、graph decode batch2、NEXTN steps3/topk1/draft4，HTTP 6688；单节点参考端口8000。混部可选环境开关在原脚本中注释，不应全部默认为开启。

四节点 PD 将两台 A3 分给 P、两台分给 D。P 为 TP8/PP4/CP8 interleave/DP1，层划分18,20,24,16，DeepEP normal、禁用图；D 为 TP32/DP32/EP32、DP attention、DeepEP low_latency、graph batch1/2/3、NEXTN3/1/4。P 的 speculative 配置为1/1/2。P/D 使用独立 dist-init 组；MemFabric store 指向 P rank0。脚本通过所有本机 IP 匹配角色，避免假设 `hostname -I` 的第一项就是业务网卡。

客户端经 router6688，请求不可误发到 bootstrap8998。180000 的 context/max-prefill 是示例配置，不是模型最大上下文能力。排障逐项关闭可选 overlap/multistream，并记录 HBM、TTFT、TPOT、请求长度与并发；来源没有可用于推导加速比的基准结果。

## Evidence

- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/glm_5_3.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/glm_5_3.mdx)（primary）

## Cookbook生成器的独立证据边界

Cookbook要求在配套Ascend容器内运行生成的Python命令，不能照用该页GPU镜像。NPU cell均写verified=false/verificationStatus=in-progress；这是上游配置的状态说明，不是本卡新增verified事件。NPU PD使用专属resolveRecipe替换角色命令，GPU attention/spec overlay不应覆写其拓扑。生成器将P HTTP改为30000、D改为30100，router的P bootstrap8998须匹配；它们与教程中原始HTTP端口不是同一组命令。


A3 Cookbook使用cann9.1.0-a3-B080，要求SGLang source checkout、TorchNPU、ATB和custom operators匹配，不能把基础镜像当已装好模型栈。单节点cell再次明确“adapted from GLM-5.2; not yet verified on GLM-5.3 hardware”，保留draft。单节点TP16/static0.75、chunk4096/max-prefill8192、max-running32、NEXTN3/1/4；双节点和四节点PD按上文角色配置，不因UI选项可见而自动验证。

### 明确但仍待验证的950参考分支

此处950范围来自源码硬件项明确的“950PR/DT series”，不是由通用device=npu推导。Cookbook要求本地ModelSlim W8A8C8_MXFP8 checkpoint（含MTP）；没有规定950镜像tag，须准备匹配的CANN/TorchNPU/custom operators。混部两节点、TP16/DP1、static0.8、max-running8，FP8 E4M3 KV与BF16 draft KV，DeepEP auto、NEXTN4/1/5，chunk16384/max-prefill2048000，FIA/MLAPO及SPEC_V2/overlap配置成组保留。

PD每个角色各两节点，均TP16/DP4、DP attention、device_urma、store指向统一31001。P禁图、static0.82、DeepEP buffer2048；D static0.86、buffer400、decode graph16、NEXTN4/1/5，router改cache_aware。跨角色dist-init组和每节点网卡必须分别填对。该分支依参考脚本改编，未提供完整硬件精度或性能结果，不可把A3已报告数据归给950。

- [docs/cookbook/autoregressive/GLM/GLM-5.3.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/cookbook/autoregressive/GLM/GLM-5.3.mdx)（supporting）
- [docs/src/snippets/configs/zai-org/glm-5.3.jsx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/src/snippets/configs/zai-org/glm-5.3.jsx)（supporting）
