---
type: Guide
title: Qwen3-235B 在 A3 的混部、256K 与 PCP 文档边界
description: 区分 Qwen3-235B BF16/W8A8 的测量负载及同版本文档对 CP=TP 和 CP 整除 TP 的冲突。
tags:
- task.implementation
- task.optimization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/qwen3_235b_a22b.mdx
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/qwen3_235b_a22b.mdx
  role: constraint
created_at: '2026-11-08T11:58:59Z'
updated_at: '2026-11-09T04:33:25Z'
platforms:
- a3
---

# Qwen3-235B 在 A3 的混部、256K 与 PCP 文档边界

## 环境与容量

教程限定SGLang v0.5.18、CANN9.0 A3镜像。BF16约470.21GB，对应容量起点TP16/8物理卡；W8A8约236.80GB，起点TP8/4物理卡。最佳实践的两个方案都用8卡，分别使用BF16和ModelSlim W8A8以及独立EAGLE3 draft；不能由权重容量推导相同并发能力。

## 三种不同目标

低延迟BF16混部为TP16、max-running1、graph batch1、EAGLE3 steps4/topk1/draft5、DP LM head和禁用Radix。W8A8吞吐混部为TP16/DP16、DP attention、ascend_fuseep、static EP dispatch、EAGLE3 3/1/4、chunk94208、max-running432，graph覆盖到27；所有数值是此checkpoint及请求负载下的配方。

256K无CP的PD来源配方基于 W8A8，P/D 分处两个 A3 节点；不能直接外推至 BF16 或单节点。在P用TP16、chunk=-1、max-running1、DeepEP normal，D用TP16/low_latency并禁用graph和overlap。P bootstrap8995、D HTTP8232、router6689；与常用默认端口不同，且skip-server-warmup不是已验证长序列性能的证明。

PCP教程同样基于 W8A8，P/D 分处两个 A3 节点，不能直接外推至 BF16 或单节点；另给TP16/CP2、moe-dp-size2、zigzag、P max-running1，要求CP整除TP、PD分离和FIA；明确非FIA CP路径未实现，D不加CP开关。**同commit的参数调优页却写attn-cp-size必须等于tp-size。** 两份文档的约束发生冲突，不能把此PCP示例当当前全局契约；应按实际版本实现与模型分支核对后再运行。这里保留来源差异，不用其中一页推翻另一页。

## 指标与验收

来源报告BF16、RANDOM11000/1500、并发1/请求1、seed1的TPOT8ms；W8A8、3500/1500、并发432/请求1728、seed1为50.1ms。精度、长度、并发和配置均不同，不能用其比值量化量化收益。来源没有提供重复和误差，本次未测。验收应先确认精度、draft和FIA/CP分支，再按同工作负载测TTFT、TPOT、吞吐和HBM。

已有[Qwen3 MoE部署总览](../qwen3_moe_deployment.md)及[当前参数调优页](../../optimization/sglang_ascend/sglang_ascend_doc_parameter_tuning.md)提供相关入口；本卡专门保留这组上游SGLang配方与冲突。

## Evidence

- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/qwen3_235b_a22b.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/qwen3_235b_a22b.mdx)（primary）
- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/qwen3_235b_a22b.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/qwen3_235b_a22b.mdx)（constraint）
