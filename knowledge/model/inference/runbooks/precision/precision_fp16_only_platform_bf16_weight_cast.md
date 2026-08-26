---
type: Runbook
title: FP16-only 平台 (310P) 部署 BF16 训练模型：权重 cast 精度回归与验收盲区
description: FP16-only 平台 (310P) 部署 BF16 训练模型：权重 cast 精度回归与验收盲区。把 BF16 训练/权重的大模型部署到只有 FP16 计算路径的推理硬件（Ascend 310P 一类）时，权重要从 BF16 转成 FP16。BF16 与 FP16 尾数/指数位不同，这个 cast 会引入输出层分布漂移、在生成过程中掺入结构性噪声。关键是它的影响高度任务相关——用错验收集会得出「已对齐」的假结论。
tags:
- task.debugging
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/128
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-07-06T00:00:00Z'
platforms:
- 310p
---

# FP16-only 平台 (310P) 部署 BF16 训练模型：权重 cast 精度回归与验收盲区

## 适用场景

把 BF16 训练/权重的大模型部署到只有 FP16 计算路径的推理硬件（[Ascend](../../concepts/platforms/atlas_a3.md) 310P 一类）时，权重要从 BF16 转成 FP16。BF16 与 FP16 尾数/指数位不同，这个 cast 会引入**输出层分布漂移**、在生成过程中掺入结构性噪声。关键是它的影响**高度任务相关**——用错验收集会得出「已对齐」的假结论。

## 失败签名：代码生成类精度坍塌、选择题类几乎不受影响

同一 310P FP16 部署，实测：

| 数据集 | Ours (FP16) | BaseLine |
| --- | --- | --- |
| HumanEval | 70.73% | 93.29% |
| MMLU | 84.82% | 85.09% |
| MGSM | 92.11% | 92.07% |
| DROP(3-shot) | 80.39% | 81.05% |

- **HumanEval（代码生成）掉 22.56 点**，而 MMLU/MGSM/DROP 几乎不动。
- 现象：生成过程偶发异常 token（如随机中文「吃点」等不符合语义的字符），直接破坏代码语法/逻辑→执行失败。
- 影响面差异化：强依赖「生成完整性/一致性」的任务（代码生成，需实际执行生成代码）受损严重；仅需「关键信息提取」的任务（选择题只需识别正确选项，掺入无关字符影响有限）几乎不受影响。

## 对运行时优化 agent 的含义

- **验收不能只看选择题类精度**：在 FP16-only 平台部署 BF16 模型时，评测必须覆盖「生成完整性」类任务（代码生成、长文本一致性），否则会因 MMLU/MGSM 对齐而误判整体对齐、漏掉代码生成的坍塌。
- **预期代价、提前定位**：把「BF16→FP16 权重 cast 引发输出层分布漂移」列为该类部署的已知风险，在 PyTorch CPU 侧对比实验中观察异常 token 分布可提前定位，而非上板后才发现。
- 本参考实现只把该问题作为**已知代价披露、未消除**——迁移到其它 BF16 模型 + FP16 平台时应预期同类风险，按生成完整性验收。

## 参考实现及其约束

- 参考实现：cann-recipes-infer 的 310P DeepSeek-V3 部署（`contrib/deepseek_v3_ascend310p`），全程 FP16 计算路径（反量化输出、MQA query/kv/output 均 `ACL_FLOAT16`），权重原为 BF16（FP8 dequant 得）、部署时转 FP16。
- 边界：精度数字为仓自报、无独立复测；因果归因（BF16→FP16 分布漂移引入结构性噪声）为仓自报分析、非维护者独立确认。结论限定到该 310P FP16 部署这一证据面，「FP16-only 平台部署 BF16 模型需按生成完整性验收」的判断可迁移到同类硬件/模型组合。
- 310P 这类非默认平台的整体部署选型（并行形态 / 模型变体 / 算子与 HCCL 适配）见 [ascend-deploy-parallel-variant-and-nondefault-platform](../../optimizations/experience/rules/ascend_deploy_parallel_variant_and_nondefault_platform.md)。

## 相关经验
- [Ascend 310P 不支持 Triton kernel：走 Triton 的算子须补纯](../runtime/ascend_310p_no_triton_kernel_eager_fallback.md)

## Evidence

- doc 披露 / 仓自报（@938a6c2c）：README §5.2 精度表与根因分析、异常 token 现象为仓 README 自报；FP16 计算路径（多个算子输出 `ACL_FLOAT16`）为 diff 事实；因果归因为仓自报分析、非独立验证。溯源下探 [cann-recipes-infer-pr-128-feat-support-deepseekv3-on-ascend310p-20](https://gitcode.com/cann/cann-recipes-infer/merge_requests/128)
