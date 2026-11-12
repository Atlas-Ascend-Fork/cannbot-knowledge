---
type: Guide
title: Qwen3.8-Max 在 A3 四节点的 W4A8 混部起点
description: 记录 daily build 的 TP64/DP4、DeepEP 和容量条件，不把内置 MTP 或教程命令当已测推测收益。
tags:
- task.implementation
- task.optimization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/qwen3_8_max.mdx
  role: primary
created_at: '2026-11-08T11:58:59Z'
updated_at: '2026-11-08T11:58:59Z'
platforms:
- a3
---

# Qwen3.8-Max 在 A3 四节点的 W4A8 混部起点

## 环境与容量

来源的Qwen3.8-Max即Qwen3.8-2.4T-A95B，hybrid GDN/attention MoE。文档使用当时main/daily build，镜像为CANN9.1 A3 B105验证构建，并未指定稳定SGLang版本。W4A8约1.33TB部署在4台A3、总64die；BF16 checkpoint约4.8TB，需要更多资源。不能仅按激活参数95B估算完整权重容量。

## 配置起点

四节点相同脚本按IP选rank，TP64/DP4、DP attention/LM head、DeepEP auto、ModelSlim、chunk8192、decode graph batch16、max-running64、静态比例0.8、禁用Radix。环境含一进程一visible device、overlap plan stream和ragged verify static、normal dispatch64轮×512。HCCL/Gloo必须指向跨节点业务网卡，而不是单机lo。

模型描述带MTP并不意味着这段服务脚本已开启推测解码：命令没有speculative-algorithm或draft参数，不能据此宣称NEXTN收益。页面暂无独立best-practice，调参尚未定型，也没有吞吐/延迟数值。验收需核对64rank组、精度加载、单请求功能和实际上下文行为，然后同负载测HBM、TTFT、TPOT与吞吐；本次没有执行源仓代码。

## Evidence

- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/qwen3_8_max.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/qwen3_8_max.mdx)（primary）
