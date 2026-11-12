---
type: Guide
title: SGLang 在 A3 部署 GLM-5.2 的精度与 3P1D 配方
description: 区分A3 W8A8容量、W4A8 3P1D性能案例与950待验证生成器分支，保留MTP权重和镜像差异。
tags:
- task.implementation
- task.optimization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/glm_5_2.mdx
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/glm_5_2.mdx
  role: constraint
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/cookbook/autoregressive/GLM/GLM-5.2.mdx
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/src/snippets/configs/zai-org/glm-5.2.jsx
  role: supporting
created_at: '2026-11-08T11:58:59Z'
updated_at: '2026-11-08T12:38:11Z'
platforms:
- a3
- '950'
---

# SGLang 在 A3 部署 GLM-5.2 的精度与 3P1D 配方

## 适用条件

来源的部署对象是 A3 上的 GLM-5.2。教程提供 CANN 9.1 `a3-B105` 验证构建镜像，说明当时没有对应稳定镜像；不是任意 SGLang/CANN 组合的兼容声明。BF16 权重约 1.51TB，教程链接的 W8A8 权重为 774.08GB，并明确标为不含 MTP；其容量起点是 TP16、16×64GB die，即一台 8 卡 A3 节点。

教程还给出双节点 TP32 和 PD 分离命令。命令中存在 NEXTN 与 unquant draft 设置，而链接的 W8A8 checkpoint 又标明无 MTP。必须核对实际权重、draft 来源和加载日志；不能依据命令中的开关断言该 checkpoint 自带可用 MTP。

## W4A8 的吞吐配置

最佳实践使用另一种 W4A8 INT8 精度与 32 张物理卡的 3P1D 部署，不能把其性能归给上述 W8A8 checkpoint。P 端是三个独立实例，使用 DeepEP normal 和 CP/PP 组合处理长输入；D 端使用 TP16、EP16、DP16、DP attention 与 DeepEP low_latency。P/D 的 graph、静态内存和通信缓冲应保持各自角色的成组配置。连接路由器时须同时提供每个 P 的 HTTP 地址和 bootstrap 端口以及 D 地址，并核对 `ASCEND_MF_STORE_URL` 和 HCCL/Gloo 网卡。

来源报告 16K+1K 的 TPOT 50ms，附带 RANDOM 命令为输入16000、输出1000、并发64、请求200。来源没有给出与 W8A8 或同资源混部的对照、重复次数和完整 warmup 条件；本次没有运行基准。验收先确认 checkpoint 的精度/MTP 状态和功能输出，再在一致请求负载下记录 TTFT、TPOT、吞吐与内存。

参见[GLM-5.1 的长上下文配置差异](sglang_ascend_doc_glm_5_1.md)和[安装版本组](../../deployment/sglang_ascend/sglang_ascend_doc_installation_version_sets.md)。

## Evidence

- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/glm_5_2.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/glm_5_2.mdx)（primary）
- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/glm_5_2.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/glm_5_2.mdx)（constraint）

## Cookbook生成器的独立证据边界

Cookbook要求在配套Ascend容器内运行生成的Python命令，不能照用该页GPU镜像。NPU cell均写verified=false/verificationStatus=in-progress；这是上游配置的状态说明，不是本卡新增verified事件。NPU PD使用专属resolveRecipe替换角色命令，GPU attention/spec overlay不应覆写其拓扑。生成器将P HTTP改为30000、D改为30100，router的P bootstrap8998须匹配；它们与教程中原始HTTP端口不是同一组命令。


A3 Cookbook镜像是v0.5.22-cann9.1.0-a3，与教程B105及最佳实践另一版本组分别保留。它自述W8A8约774GB、下一预测层tensor为BF16/F32而非INT8，所以draft unquant；这是Cookbook对包含MTP的本地权重前提，不能消除教程链接checkpoint“不含MTP”的矛盾。源权重、实际shard及加载日志仍需单独确认。

A3单节点TP16/static0.7/NEXTN3/1/4；双节点TP32/static0.8、disable-Radix。1P1D角色各一节点，P TP16/attention-DP4、DeepEP normal、禁图/NEXTN1/1/2；D TP16/DP16/EP16、low_latency、decode graph最大4/NEXTN3/1/4，共用P头24707 store。这是Cookbook的1P1D入口，不是上文W4A8 3P1D吞吐场景。

### 明确但仍待验证的950参考分支

此处950范围来自源码硬件项明确的“950PR/DT series”，不是由通用device=npu推导。Cookbook要求本地ModelSlim W8A8C8_MXFP8 checkpoint（含MTP）；没有规定950镜像tag，须准备匹配的CANN/TorchNPU/custom operators。混部两节点、TP16/DP1、static0.8、max-running8，FP8 E4M3 KV与BF16 draft KV，DeepEP auto、NEXTN4/1/5，chunk16384/max-prefill2048000，FIA/MLAPO及SPEC_V2/overlap配置成组保留。

PD每个角色各两节点，均TP16/DP4、DP attention、device_urma、store指向统一31001。P禁图、static0.82、DeepEP buffer2048；D static0.86、buffer400、decode graph16、NEXTN4/1/5，router改cache_aware。跨角色dist-init组和每节点网卡必须分别填对。该分支依参考脚本改编，未提供完整硬件精度或性能结果，不可把A3已报告数据归给950。

- [docs/cookbook/autoregressive/GLM/GLM-5.2.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/cookbook/autoregressive/GLM/GLM-5.2.mdx)（supporting）
- [docs/src/snippets/configs/zai-org/glm-5.2.jsx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/src/snippets/configs/zai-org/glm-5.2.jsx)（supporting）
