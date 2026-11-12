---
type: Guide
title: SGLang 昇腾 PD 传输、实例端口与角色配置
description: 融合两仓PD文档，区分MemFabric版本、Mooncake激活、物理设备映射和P/D分组。
tags:
- task.implementation
- task.optimization
- topic.model_serving
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/advanced_features/pd_disaggregation.mdx
  role: primary
- resource: https://github.com/sgl-project/sgl-docs/blob/c27f107bf92712760cff32fdd3c1cf08d2372b1a/docs/advanced_features/pd_disaggregation.mdx
  role: primary
created_at: '2026-11-08T12:09:58Z'
updated_at: '2026-11-08T12:09:58Z'
platforms: []
---

# SGLang 昇腾 PD 传输、实例端口与角色配置

## 传输后端与版本差异

ascend传输后端需要memfabric_hybrid和所有参与实例可达的ASCEND_MF_STORE_URL。旧通用页安装1.0.5，新通用页反而写1.0.0，而新NPU安装页是1.2.1配套组；不能按仓库新旧排序就当作库版本升级顺序，更不能混装后宣称兼容。

两通用页还保留ENABLE_ASCEND_TRANSFER_WITH_MOONCAKE=true及容器ASCEND_NPU_PHY_ID设置；新支持矩阵却称mooncake不支持NPU、必须显式ascend。需要核对所用Mooncake构建、集成版本和实际后端，不能把这几个互有冲突的声明融合成任意可用。来源只称NPU、没有逐产品证明，故draft空平台。

## 实例角色与拓扑

旧单机Llama示例P/D分别HTTP30000/30001、D base-device1、router8000。新单机MiMo示例将P/D各TP8分配至base0/base8，P禁用graph，D使用multi-layer EAGLE（3 steps/4 draft tokens）、low_latency和graph1/2/4/8/10/12/14/16；两者bootstrap8996、store24669、HTTP10000/10001、router9903。需要足够不同device，不能把标题“单机”理解为单NPU或同device任意复用。

新R1例子P TP16/attn-DP8、DeepEP normal、NEXTN1/1/2；D TP16/attn-DP16、low_latency、NEXTN3/1/4和独立graph覆盖。每组dist-init只组内分布式初始化，store承担P/D传输协调；不能把HTTP、bootstrap、HCCL初始化、store几个端口互换。路由器端口省略的示例需按实际router版本补核bootstrap配置。

P/D拆分减少prefill对decode干扰是设计目标，不保证所有负载受益；还增加KV传输和调度开销。两个worker需分别profiling，验收先查实际role、精度/权重、设备映射、可达性和同一请求的KV交付，再同负载比较TTFT/TPOT/吞吐。本次没有启动服务或执行设备测试。

## Evidence

- [sglang：docs/docs/advanced_features/pd_disaggregation.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/advanced_features/pd_disaggregation.mdx)（primary）
- [sgl_docs：docs/advanced_features/pd_disaggregation.mdx](https://github.com/sgl-project/sgl-docs/blob/c27f107bf92712760cff32fdd3c1cf08d2372b1a/docs/advanced_features/pd_disaggregation.mdx)（primary）
