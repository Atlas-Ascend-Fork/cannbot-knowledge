---
type: Guide
title: Qwen3.5-397B 在 A3 的混合状态缓存与长输入配方
description: 记录 Qwen3.5 W4A8 MTP 的 GDN、NEXTN、DeepEP 与 extra_buffer 前缀复用配置及负载指标。
tags:
- task.implementation
- task.optimization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/qwen3_5_397b.mdx
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/qwen3_5_397b.mdx
  role: constraint
- resource: https://github.com/sgl-project/sgl-docs/blob/c27f107bf92712760cff32fdd3c1cf08d2372b1a/docs/hardware-platforms/ascend-npus/Qwen3.5.mdx
  role: primary
created_at: '2026-11-08T11:58:59Z'
updated_at: '2026-11-09T04:33:52Z'
platforms:
- a3
---

# Qwen3.5-397B 在 A3 的混合状态缓存与长输入配方

## 先决条件

教程以SGLang v0.5.16编写，容器示例为CANN9.1 B105验证构建，不能由“建议更新版本”推导任意版本兼容。目标W4A8-MTP权重约235.88GB，容量起点TP8/4物理卡；最佳实践均用A3 8物理卡/TP16。模型混合GDN、全attention与MoE并支持多模态；状态预算不等于纯attention KV预算。

## 配方中的共同契约

来源使用ModelSlim、GDN_ATTN_BACKEND_TRITON、FIA、NEXTN3/1/4、draft unquant、mamba-ssm BF16、DeepEP auto和multimodal/ascend_attn。长输入随机场景chunk=-1且禁用Radix，按16K/64K/128K选prefill admission、DP与max-total-tokens；不能把任意一个max-total值视作全部场景安全上限。

共享前缀场景保留Radix，并设置`mamba-radix-cache-strategy extra_buffer`。128K配方max-mamba-cache-size320、max-running64；64K配方640/128。这个容量应覆盖混合状态缓存，不能只增大请求数却保留不足状态槽。ZBAL graph/VMM、HCCL缓冲与分轮normal dispatch也需按具体输入长度选用；并非每个方案都配置相同通信资源。

## 上游报告的工作负载

以下均A3、8物理卡、W4A8 INT8、rate=inf。随机负载行使用RANDOM定长（random-range-ratio=1）并显式seed1；共享前缀两行使用generated-shared-prefix，分别为1组40/96请求、前缀117965/58982、后缀13107/6554、输出1024，命令均未显式设置seed。来源缺独立重复和误差，本次未测试。

| 输入/输出 | 并发/请求与warmup | 报告TPOT |
|---|---|---|
| 131072/1024 | 低延迟3/3、warmup2；吞吐配置10/10、warmup8 | 20ms；50ms |
| 16384/1024 | 40/40、warmup32；132/132、warmup8 | 20ms；50ms |
| 3500/1500 | 160/160、warmup64；432/432、warmup16 | 22.2ms；50ms |
| 65536/1024 | 6/6、warmup6；24/24、warmup8 | 20ms；50ms |
| 前缀117965+后缀13107/1024 | 1组40请求/并发40 | 50ms |
| 前缀58982+后缀6554/1024 | 1组96请求/并发96 | 50ms |

部分长输入命令额外设temperature0.6/top_p0.95，不能与不同采样条件直接比较。生成前缀比例90%不等同所有请求的真实缓存命中；需另查冷启动、驱逐与路由后的命中日志。128K低延迟行的并发3、请求3、warmup2由来源命令明确给出；完整命令可沿固定来源复核。


## 旧版 Qwen3.5 简例的差异

旧仓CANN8.5的qwen3.5专用A2/A3镜像页只称qwen35_w8a8可在一台A3（16×64GB）部署；TP16、chunk16384/max-prefill280000、graph-bs16、BF16计算和ascend_attn。没有指明397B、具体checkpoint大小或MTP开关，因此不能把旧页的泛称权重当作本卡当前W4A8-MTP同一产物，也不能外推其未展示的A2部署资源。

## Evidence

- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/qwen3_5_397b.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/qwen3_5_397b.mdx)（primary）
- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/qwen3_5_397b.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/qwen3_5_397b.mdx)（constraint）
- [sgl_docs：docs/hardware-platforms/ascend-npus/Qwen3.5.mdx](https://github.com/sgl-project/sgl-docs/blob/c27f107bf92712760cff32fdd3c1cf08d2372b1a/docs/hardware-platforms/ascend-npus/Qwen3.5.mdx)（primary）
