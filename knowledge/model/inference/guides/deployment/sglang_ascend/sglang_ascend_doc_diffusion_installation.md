---
type: Guide
title: SGLang Diffusion昇腾安装入口：同包引擎与版本证据
description: 对齐新旧文档中的diffusion extra、NPU安装分流和A2/A3总声明，避免把NVIDIA容器当NPU环境。
tags:
- task.implementation
- topic.diffusion
- topic.multimodal
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/sglang-diffusion/installation.mdx
  role: primary
- resource: https://github.com/sgl-project/sgl-docs/blob/c27f107bf92712760cff32fdd3c1cf08d2372b1a/docs/sglang-diffusion/installation.mdx
  role: primary
- resource: https://github.com/sgl-project/sgl-docs/blob/c27f107bf92712760cff32fdd3c1cf08d2372b1a/sglang-diffusion/intro.mdx
  role: supporting
created_at: '2026-11-08T12:33:42Z'
updated_at: '2026-11-08T12:37:01Z'
platforms: []
---

# SGLang Diffusion昇腾安装入口：同包引擎与版本证据

## 适用场景

SGLang Diffusion和LLM引擎位于同一sglang Python包，sglang generate执行离线任务，sglang serve提供服务；[diffusion]只是可选依赖集合。新sglang/docs与旧sgl-docs安装页均把NPU环境导向Ascend专门安装说明，并以FLUX.1示例检查生成入口。页面的NVIDIA Docker、CUDA轮子与--gpus all命令不适用于昇腾运行时。

旧sgl-docs intro明确框架整体支持A2/A3，并列模型家族；这不证明所有模型、稀疏attention或量化精度均在两平台可运行。更新文档与实现时应逐特性核对，尤其950 MX量化不能由这条总体声明推出A2/A3可用。

## 准备和验收

先完成版本匹配的Ascend驱动/CANN/TorchNPU与kernel安装，再在同一环境安装或加载sglang的diffusion依赖，准备完整权重和输出目录。固定实际包版本/commit、容器digest、可见NPU及模型配置；源码页中的main/latest是示例，本卡来源版本已固定，不代表那些滚动标识现在的内容。

先按模型的最小合法配置生成一张图，记录加载日志、实际设备和输出，再启用HTTP并验证请求/输出路径。只有命令存在不算精度/性能验收。本次未安装软件、下载权重或运行模型；平台未对全部流程逐一证明，保持draft。

## 配套知识

[昇腾安装版本组](sglang_ascend_doc_installation_version_sets.md)；[Diffusion平台分派](../../integration/sglang_ascend/sglang_ascend_diffusion_platform.md)。
