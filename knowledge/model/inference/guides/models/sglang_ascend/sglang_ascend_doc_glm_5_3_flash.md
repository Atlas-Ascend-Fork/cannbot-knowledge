---
type: Guide
title: GLM-5.3-Flash 在 A3 与 950 的分平台精度和 PD 配方
description: 保留 A3 W8A8 与 950 W8A8_MXFP8 的页大小、推测参数、并行和传输协议差异。
tags:
- task.implementation
- task.optimization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/glm_5_3_flash.mdx
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/cookbook/autoregressive/GLM/GLM-5.3-Flash.mdx
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/src/snippets/configs/zai-org/glm-5.3-flash.jsx
  role: supporting
created_at: '2026-11-08T11:58:59Z'
updated_at: '2026-11-08T12:38:11Z'
platforms:
- a3
- '950'
---

# GLM-5.3-Flash 在 A3 与 950 的分平台精度和 PD 配方

## 权重和运行环境

该页将 A3 的 W8A8（332.97GB）和 950PR/DT 的 W8A8_MXFP8（338.12GB）分开。checkpoint 应含配置、tokenizer、量化权重、`quant_model_description.json` 以及 NEXTN 所需 MTP。A3 示例使用 CANN9.1 专用 GLM5.3-Flash 镜像，950 镜像仍是用户占位符，且950 PD 要求镜像支持 DP attention。不能把两种量化或镜像互换。

## 混部与 PD 的平台差异

| 条件 | A3 | 950PR/DT |
|---|---|---|
| 单节点混部 | 8物理卡/16die，TP16，page128，graph batch16 | 8device，TP8，无DP attention，page64，graph1/8/64 |
| NEXTN | steps3/topk1/draft4 | steps4/topk1/draft5，draft KV BF16 |
| PD P | TP4/PP4/DP4，DeepEP normal | TP8/PP1/DP2，DP attention |
| PD D | TP16/PP1/DP16，DeepEP low_latency，graph1/2 | TP8/PP1/DP2，DP attention |
| KV 传输 | ascend 后端与 MemFabric store | ascend 后端，明确 `device_urma` |

每个 PD 配方使用同平台的两台节点。A3 P 的长序列 normal 参数为128轮×1024 token；D 的每rank dispatch上限16，队列及buffer参数与P不同。950运行还加载custom_transformer库；不要把旧FAQ中笼统“FP8不支持”套到这组明确的950 MXFP8配方。

## 验收与测量边界

worker HTTP8810/8811、P bootstrap8998、router8000、store各有用途。路由示例禁用重试并显式增加启动和请求超时，目的是保留该场景的连接设置，不是通用生产默认。混部验证发8810，PD验证发router8000。

页面给出约128K输入/1K输出的共享前缀负载建议，但没有提供完成的性能数值、对照与重复次数。本次仅摄取文档。先核对实际加载精度、MTP和DP支持，再记录生成正确性与同负载性能，不能由参数行推导加速收益。

## Evidence

- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/glm_5_3_flash.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/glm_5_3_flash.mdx)（primary）

## Cookbook生成器的独立证据边界

Cookbook要求在配套Ascend容器内运行生成的Python命令，不能照用该页GPU镜像。NPU cell均写verified=false/verificationStatus=in-progress；这是上游配置的状态说明，不是本卡新增verified事件。NPU PD使用专属resolveRecipe替换角色命令，GPU attention/spec overlay不应覆写其拓扑。生成器将P HTTP改为30000、D改为30100，router的P bootstrap8998须匹配；它们与教程中原始HTTP端口不是同一组命令。


生成器同样只为NPU发布Python入口，A3使用专用cann9.1.0-a3-glm5.3-flash镜像，950使用用户自备兼容镜像；内部残留A3 Docker字符串不能作为950镜像承诺。A3权重W8A8、950 W8A8_MXFP8，cell的page128/64与NEXTN3/1/4或4/1/5分别对应上表，不能借GPU默认FP8/TRT-LLM、通用mamba-ratio或FA4 DFlash命令覆写它们。

950混部cell显式ASCEND_LAUNCH_BLOCKING=1、profiling=0；这是源配置现状，尚无性能验证，不能把它当普通异步吞吐测量的推荐开关。A3/950 PD专属resolveRecipe输出P30000/D30100，router带startup3600/request7200秒与disable-retries；950仍用device_urma、store24670，A3用P头24707。源页面GPU部分的“仅Mooncake/PD不可投机”等限制有其GB300预览上下文，不能覆盖这组NPU专属Ascend-transfer/NEXTN脚本。

- [docs/cookbook/autoregressive/GLM/GLM-5.3-Flash.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/cookbook/autoregressive/GLM/GLM-5.3-Flash.mdx)（supporting）
- [docs/src/snippets/configs/zai-org/glm-5.3-flash.jsx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/src/snippets/configs/zai-org/glm-5.3-flash.jsx)（supporting）
