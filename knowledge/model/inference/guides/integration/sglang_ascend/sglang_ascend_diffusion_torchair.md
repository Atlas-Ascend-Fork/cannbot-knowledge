---
type: Guide
title: SGLang Diffusion NPU编译：torchair、区域编译与VAE调用缓存
description: 说明NPU编译参数、CacheDiT条件延期、区域匹配和按对象身份缓存ActiveTarget callable。
tags:
- task.implementation
- topic.diffusion
- topic.graph_execution
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/utils/torch_compile.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/pipelines_core/stages/denoising.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/pipelines_core/stages/decoding.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/pipelines_core/stages/model_specific_stages/cosmos3.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/layers/vocab_parallel_embedding.py
  role: implementation
created_at: '2026-11-08T12:26:56Z'
updated_at: '2026-11-09T04:32:54Z'
platforms: []
---

# SGLang Diffusion NPU编译：torchair、区域编译与VAE调用缓存

## 编译入口

out-of-tree compiler backend/options优先；内置NPU通过get_compiler_backend选择torchair并使用fullgraph=False、dynamic=False，不套用CUDA的max-autotune mode和Inductor专用选项。compute/communication overlap的相关Inductor调优只对相应backend生效，不能据公共配置推导NPU获得同样融合。

DiT初始化时尝试编译；仅在服务默认请求 CacheDiT 且尚未启用时延期，待缓存设置后编译。服务默认关闭而后续请求单独开启缓存时，没有先装缓存再调用 module.compile 的统一保证，实际追踪与缓存效果须验证；已编译对象不重复编译。通用 regional compile 按匹配条件对匹配子模块原地调用 submodule.compile，必须至少命中一个否则ValueError，模块id注册避免重复处理。NPU的denoising使用其backend参数，Cosmos3同样保持静态shape而非CUDA参数；Cosmos3 专用路径则把 torch.compile 的返回值写回 gen_layers[i]，与通用原地编译方式不同。

## VAE与对象生命周期

VAE decoding用ActiveTargetCompiledCallable只保留当前目标对象id及compiled callable；切换实际目标时需重建，不能把一个模型的编译结果复用于另一个对象。权重/offload切换与callable缓存是不同生命周期，必须验证重新加载和多组件交替行为。

先eager确认输出，再记录首次编译耗时、重用命中、regional匹配数与稳态延迟；覆盖输入shape变化、级联DiT和VAE切换。失败恢复eager，不能把fullgraph=False理解为全部输入动态适配。本次未调用torch.compile或上游模型，平台未按芯片声明。

## 补充调用与验证边界

词表并行get_masked_input_and_mask的torch.compile在NPU显式disable=True，保留普通Tensor的原始/新增词表区间掩码、offset换算及无效项屏蔽；这不等于关闭全部DiT/VAE编译。不可把该helper上的dynamic=True解释成NPU已启用动态编译。
