---
type: Guide
title: Qwen3-Next 在当前上游的量化主模型与 NEXTN 配方
description: 把 v0.5.18 的 Qwen3-Next A3 混部与已有旧补丁的 CP 方案区分，保留图和 draft 权重条件。
tags:
- task.implementation
- task.optimization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/qwen3_next_80b_a3b_instruct.mdx
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/qwen3_next_80b_a3b_instruct.mdx
  role: constraint
created_at: '2026-11-08T11:58:59Z'
updated_at: '2026-11-08T11:58:59Z'
platforms:
- a3
---

# Qwen3-Next 在当前上游的量化主模型与 NEXTN 配方

## 版本与权重

本卡对应上游SGLang v0.5.18、CANN9.0 A3教程。W8A8主模型约84.90GB，容量起点TP2（1物理卡），NEXTN使用单独BF16权重目录并设draft unquant、mamba-ssm dtype BF16。容量起点不能覆盖任意并发与状态缓存。

这与已有[Qwen3-Next A3部署](../qwen3_next_atlas_a3_deployment.md)和[旧补丁的CP/TP实验](../../../optimizations/cases/qwen3_next_a3_prefill_cp_tp.md)具有不同版本和代码背景。不能把旧补丁中的MTP/graph或CP限制直接搬到本卡：当前配方明确同时列出NEXTN和decode graph。

## 三组配置

一物理卡方案TP2、max-running2、graph batch2、NEXTN3/1/4、禁用Radix，page128和FIA，chunk=-1；设置ZBCCL VMM/graph。两卡吞吐方案TP4/DP2、DP attention/DP LM head、DeepEP auto、max-running300、graph覆盖至150，静态比例0.75，并改用ZBAL环境。6K方案仍TP4/DP2，但max-running16、graph2/4/8、静态比例0.85，context81920。三者都关闭NPU multistream，不能从其他模型的开启建议推导这里也应开启。

来源保留ZBCCL与ZBAL两套名称，并有FORCE_DRAFT_MODEL_NON_QUANT和显式draft quant参数；需要核对实际版本加载日志，不假设任意名称均受支持。Hybrid GDN/attention状态、draft与KV/graph共同消耗HBM，应观察实际分配，不能只按权重大小填充max-total-tokens。

## 报告边界

来源报告：一卡3500/1500 TPOT20ms；两卡RANDOM3500/1500、并发300/请求300、seed1为50ms；两卡6144/1500、batch16为15.62ms。第一条benchmark与已读其他页面共用相同命令块，仍应以该页实际请求设置为准。缺独立重复、误差与完整warmup，本次未测；资源、长度和并发变化不能当单项加速比。

## Evidence

- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/qwen3_next_80b_a3b_instruct.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/qwen3_next_80b_a3b_instruct.mdx)（primary）
- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/qwen3_next_80b_a3b_instruct.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/qwen3_next_80b_a3b_instruct.mdx)（constraint）
