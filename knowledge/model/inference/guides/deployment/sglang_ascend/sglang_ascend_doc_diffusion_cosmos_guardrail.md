---
type: Guide
title: SGLang Diffusion Cosmos3昇腾启动：Guardrail权重加载边界
description: 记录可选Guardrail依赖、NPU UnpicklingError来源处理和模型启动与质量验证的区别。
tags:
- task.implementation
- topic.diffusion
- topic.multimodal
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/cookbook/diffusion/Cosmos/Cosmos3.mdx
  role: primary
created_at: '2026-11-08T12:33:46Z'
updated_at: '2026-11-08T12:33:46Z'
platforms: []
---

# SGLang Diffusion Cosmos3昇腾启动：Guardrail权重加载边界

## 触发与处理

Cosmos3的cosmos-guardrail是可选依赖，会下载受控NVIDIA guardrail权重，未安装时记录跳过；来源同时提供SGLANG_DISABLE_COSMOS3_GUARDRAILS=1供本地实验关闭。guardrail是否启用应单独记录，模型正常生成不代表该检查已运行。

来源指出Ascend启动可能在Cosmos-1.0-Guardrail加载阶段遇到_pickle.UnpicklingError，给出把cosmos_utils.py中的weights_only=True改为False的处理。这个改动扩大torch反序列化接受对象的范围，只应结合已确认来源的权重评估，不能以通用sed命令对所有第三方checkpoint批量取消限制。本次没有修改环境或执行该命令。

先确认错误发生在guardrail而非DiT权重，检查依赖与具体文件/权重版本，再在受控实验中验证加载、启用状态和请求结果。绕过guardrail和修复模型推理是不同操作，benchmark需保持相同设置；来源没有提供该问题在全部型号/版本的复现矩阵，保持draft与未知平台。
