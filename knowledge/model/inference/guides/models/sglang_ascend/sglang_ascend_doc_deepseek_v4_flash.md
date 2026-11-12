---
type: Guide
title: SGLang Ascend DeepSeek-V4-Flash：dsv4后端、分页与分角色投机
description: 限定A3教程/最佳实践与950待验证Flash Official cell的dsv4、page128、精度及分角色投机差异，不从variant列表推导Pro支持。
tags:
- task.implementation
- task.optimization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/deepseek_v4_flash.mdx
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/deepseek_v4_flash.mdx
  role: constraint
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/src/snippets/configs/deepseek-ai/deepseek-v4.jsx
  role: supporting
created_at: '2026-11-08T11:50:28Z'
updated_at: '2026-11-08T12:38:11Z'
platforms:
- a3
- '950'
---

# SGLang Ascend DeepSeek-V4-Flash：dsv4后端、分页与分角色投机

## 平台和版本

本任务指南覆盖A3上的DeepSeek-V4-Flash，284B总参数/13B激活，混合CSA/HCA、MoE和MTP；架构全貌见[DeepSeek-V4](/model/inference/concepts/models/deepseek_v4.md)。模型声明1M上下文不等于本页8K性能配方已覆盖1M。教程自述基于v0.5.16并建议后续版本，实际镜像示例已改用cann9.1.0-a3-B105，二者并非同一个锁定二进制版本，部署时须记录真实镜像及组件。

ModelSlim W8A8-MTP权重约300GB，教程给A3物理4卡/8die/TP8最小混部实例；最佳实践则另用物理8卡TP16混部或16卡1P1D。不能把最小资源、最佳吞吐和模型最大上下文同时视为一组测量条件。

## 关键部署约束

主模型选择--attention-backend dsv4、--page-size 128、--kv-cache-dtype bfloat16，不用普通ascend替换整个V4后端。来源还加载customize/custom_transformer vendor环境，关闭若干CUDA/TileLang专用优化分支，不能仅保留一条model-path命令就认为完成适配。

- TP8最小实例使用DP attention8、DeepEP auto、DP LM Head，prefill-max-requests160、chunked-prefill-size131072、max-prefill-tokens80000；ZBAL有独立bootstrap、local memory与图内存设置。
- 1P1D配方在P用TP16/DP16、DeepEP normal、关图、静态dispatch，mem-fraction0.68、prefill-max-requests6，额外开启WAR barrier相关配置；D用TP16/DP16、DeepEP auto、显式decode图档位至48、EAGLE(steps2,topk1,draft3)，mem-fraction0.75、最大896请求。
- TP16混部配方改为DSPARK，单独提供draft model路径和ascend draft attention，draft tokens7、block size6，静态ragged verify；同时用DEEPEP_HYBRID_DEPLOYMENT=1隔离Normal/LL窗口。它与分离配方EAGLE不是可随意互换的命令末尾选项。

来源同时出现FORCE_DRAFT_MODEL_NON_QUANT和draft-model-quantization参数；这只能记录为完整配方的两个设置，不能据此断言最终draft权重或每个算子的精度，须按实际加载日志与实现核对。ZBAL显存、HCCL缓冲、graph batch及投机候选容量都增加资源占用。

## 传输与上游观测

PD使用ascend transfer与一致MemFabric store，router须匹配P的bootstrap。P/D设备与网络接口必须按角色分别配置，示例中的lo只适用于其相应单机上下文，不能照搬跨节点。

来源RANDOM输入8000/输出1000：W8A8 1P1D共16物理卡，prompts2400、并发800、warmup16、请求率inf、seed1，自报TPOT50ms；W8A8混部8物理卡，prompts160、并发160、warmup0、请求率inf、seed1，也标50ms。两组资源、投机算法和并发均不同，没有独立相同条件基线，不能据数字相等推导效率或通用收益；重复次数、方差和独立复测未知。

## 验证、失效和回退

先检验dsv4稀疏/压缩KV元数据、分页、不同请求长度和最终文本精度，再分别验收EAGLE与DSPARK接受率、图档位、P/D缓存传输和ZBAL内存。改变page size、模型权重或投机算法后需要重新验证，不只扩大max-running-requests。性能异常先回到同镜像、非投机或已知通信基线再逐项消融。本次未运行服务、量化、基准、上游代码或设备测试。

## Evidence

- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/deepseek_v4_flash.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/deepseek_v4_flash.mdx)（primary）
- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/deepseek_v4_flash.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/deepseek_v4_flash.mdx)（constraint）

## Cookbook cell只覆盖Flash Official，不覆盖所有variant

配置顶部虽然列Flash/Flash Official/Vision/Pro/Pro Official，实际NPU只有Flash Official单节点Balanced两cell，均in-progress且待release build复跑、镜像/provenance/gating仍有TODO。不能从variant/hardware列表拼出NPU Pro支持。

A3 cell为ModelSlim W8A8、page128/KV BF16、DP16/DP attention、DeepEP auto、static0.7/max-running160、chunk131072/max-prefill65536、DSPARK draft tokens6/block5、draft ModelSlim/attention ascend、graph1/2/4/8/10；cell未显式写TP，不能只从DP猜完整生成命令。它与上文draft7/block6混部最佳实践是不同配方。

950PR/DT cell明确TP4/DP4、page128、KV auto、static0.72/max-running64、chunk与max-prefill均65536、禁Radix、DSPARK6/block5、draft quantization fp8/attention ascend，graph1/2/4/8/10/16。环境同时写FORCE_DRAFT_MODEL_NON_QUANT=1、DSV4_FP4_EXPERTS=True并关闭多种fused/TileLang优化；最终draft精度仍需按实际加载实现核对，不能单靠变量或FP8标签下结论。FlashInfer/Marlin选项对NPU禁用，不应把CUDA kernel路线混入这些cell。

- [docs/src/snippets/configs/deepseek-ai/deepseek-v4.jsx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/src/snippets/configs/deepseek-ai/deepseek-v4.jsx)（supporting）
