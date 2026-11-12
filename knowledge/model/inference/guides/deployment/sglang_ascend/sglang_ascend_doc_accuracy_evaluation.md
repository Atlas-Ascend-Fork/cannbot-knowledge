---
type: Guide
title: SGLang Ascend 精度验收：sgl-eval与EvalScope的在线文本/多模态流程
description: 以A3示例区分GSM8K/MMLU的sgl-eval入口和其他数据集的EvalScope调用，明确服务路由、模型ID、TLS/代理故障与验收产物。
tags:
- task.testing
- topic.precision
- topic.multimodal
- topic.model_serving
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/evaluation/accuracy_evaluation.mdx
  role: primary
created_at: '2026-11-08T11:50:28Z'
updated_at: '2026-11-08T11:50:28Z'
platforms:
- a3
---

# SGLang Ascend 精度验收：sgl-eval与EvalScope的在线文本/多模态流程

## 评测入口与前提

来源以A3容器、Qwen2.5-7B与Qwen2.5-VL-7B为例；安装正确设备镜像并启动ascend后端服务后，再开展在线质量验收。部署成功和单次Paris问答不替代数据集精度。多模态还需--mm-attention-backend ascend_attn以及匹配的图片输入路径。

当前页面虽然标题强调EvalScope，实际GSM8K/MMLU已切换到sgl-eval，由其负责数据、chat prompt和grader；其他示例保留EvalScope。不能把旧few_shot_gsm8k、sgl-eval和EvalScope得分不加条件直接比较。

| 场景 | 来源入口 | 必要核对 |
| --- | --- | --- |
| GSM8K、MMLU | sgl-eval run，对接/v1 | 用/v1/models报告的模型名，记录样本数与max tokens |
| CEval、MATH-500、HumanEval | evalscope eval，openai_api | api-url含正确/v1，api key和dataset匹配 |
| MMBench、MMMU、HallusionBench | 同上多模态数据集 | 图片可达、chat模板和多模态后端实际生效 |

sgl-eval输出metrics.json与逐样本预测；应保存模型/量化、tokenizer/chat模板、数据集版本、采样/思考模式、样本数、grader与输出，才能复核精度差异。来源示例的10题只是小样本演示，不是模型最终精度基线。

## 故障与诊断边界

连接失败先查服务就绪、端口和/v1后缀；PD请求走router。重试超时可能是HTTP代理拦截本地请求，先区分网络路由与模型计算。TLS链问题应配置可信CA bundle或离线准备数据；来源中的关闭证书验证被明确限定为临时隔离诊断，不能当作生产运行要求。

## 验收与回退

在同一工作负载比较BF16/目标量化或基线/优化配置，逐样本定位失败，不仅看聚合分数。变更runtime、投机、模型权重和精度后需重评，回退到原镜像/权重/模板以隔离原因。本次未安装评测工具、下载数据、运行服务或评测；来源工具步骤不是已经测得的模型得分。

## Evidence

- [sglang：docs/docs/hardware-platforms/ascend-npus/evaluation/accuracy_evaluation.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/evaluation/accuracy_evaluation.mdx)（primary）
