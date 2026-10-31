---
type: Concept
title: GLM-5.3-Flash 混合注意力与混合量化
description: 说明 950DT 适配的34层KDA与11层MLA/DSA、4流mHC、MoE及HiF8/MXFP8/MXFP4的分工和并行边界。
tags:
- task.design
- topic.model_architecture
- topic.attention
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5_3/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5_3/config/glm_5_3_flash_ep8.yaml
  role: example
created_at: '2026-10-29T12:19:41Z'
updated_at: '2026-10-29T12:19:41Z'
platforms:
- '950'
---

# GLM-5.3-Flash 混合注意力与混合量化

## 模型结构

当前 Recipes 适配 GLM-5.3-Flash 发布权重，约306B总参数，目标为 Ascend 950DT 上的 Hybrid HiF8–MXFP8–MXFP4 推理。

45层中34层使用 KDA 线性注意力，包含短卷积与门控 delta 递推；另外11层使用 MLA + DSA，吸收式 MLA 走 NoPE，压缩 k-pool 供 indexer 选择稀疏注意力候选。递推状态与 MLA/DSA 的缓存具有不同语义，不能按同一种 KV 张量管理。

mHC 在层间维护 `[T,4,D]` 的4条隐藏流，子层前使用经 Sinkhorn 归一化的组合矩阵折叠，子层后再展开。MoE 使用288个路由专家、top-8选择及1个共享专家；前 `first_k_dense_replace` 层为 dense MLP。

## 当前量化分工

| 计算或权重 | 当前部署精度 |
| --- | --- |
| DSA 投影、dense MLP | HiF8 W8A8 |
| 共享专家 | MXFP8 W8A8 |
| 路由专家 | MXFP4 W4A8 |
| KDA 权重、DSA kv_b_proj、indexer、mHC、norm、router gate、embed/lm_head | 保留 BF16/FP32 |

这是模型部件分工，不能概括为整个模型统一FP8或所有权重都转成HiF8。原始发布权重为FP8，需要使用当前模型转换脚本生成运行时格式并更新 `quantization_config`，输入与输出目录必须分开。

## 实现与适用边界

当前推理配置支持 eager 和 npugraph_ex，默认使用后者；暂不支持MTP。CP以及attention/dense/MoE/o_proj/shared TP均要求为1，MoE EP随world size派生。默认8卡配置不表示单卡或任意并行组合已通过验证。

共享专家可在decode侧流计算，与路由专家的dispatch/GMM/combine重叠；该开关不能代替对流间依赖、输出正确性和实际时延的验收。具体环境、转换与启动见[950DT部署](../../guides/models/glm_5_3_flash_950_deployment.md)。

## 相关入口

- [Kimi K3 的 KDA 与递推状态](kimi_k3.md)
- [mHC](../modules/mhc.md)
- [共享专家双流](../../optimizations/rules/moe_shared_expert_decode_dual_stream.md)
