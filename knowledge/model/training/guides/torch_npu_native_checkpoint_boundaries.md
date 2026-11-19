---
type: Guide
title: 原生激活重计算的版本、dtype与产品边界
description: 说明checkpoint_sequential的FP32支持表范围，避免推广到全部checkpoint或把未列950条目当绝对禁止。
tags:
- task.optimization
- topic.checkpointing
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-utils-checkpoint.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-utils-checkpoint.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-utils-checkpoint.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-utils-checkpoint.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-utils-checkpoint.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-utils-checkpoint.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-utils-checkpoint.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-utils-checkpoint.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-utils-checkpoint.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-utils-checkpoint.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-utils-checkpoint.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-utils-checkpoint.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-utils-checkpoint.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-utils-checkpoint.md
  role: constraint
created_at: '2026-11-09T07:31:16Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
- '950'
---

# 原生激活重计算的版本、dtype与产品边界

## 固定来源与版本边界

依据PyTorch仓主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的原生支持页。页面分别对应PyTorch 2.7.1、2.9.0、2.10.0、2.11.0、2.12.0、2.13.0、2.14.0，相关条目的限制文本已逐版本提取核对；这不是同一安装包同时兼容所有版本的证明，也不补出未列出的2.8行为。

产品页确认A2/A3训练系列及950DT的下列条目。仅以固定来源记录已声明范围与实现边界，未运行上游代码、训练或设备实验；来源文档的“已验证”不作为本卡新增 verified 事件。

## 不同重计算入口分开核对

七个版本支持页均对torch.utils.checkpoint.checkpoint_sequential写input仅FP32，不能只从普通checkpoint条目列“支持”就跳过sequential的专属限制。反过来，这个限制只属于列出的sequential条目，不能推广到所有checkpoint、框架自定义checkpoint或所有BF16训练重计算路径。

当前卡保存支持表的窄范围，没有同版本上游Python实现或NPU运行结果来消解更多dtype组合。超出支持表的组合应先建立正确性与版本证据，不能把目录里的FP32文字当作全部运行时实现必然抛错的证明。

## 产品和能力不能由名称外推

2.14支持表中checkpoint、get/set_device_states、CheckpointPolicy和set_checkpoint_debug_enabled列A2/A3及950DT；SelectiveCheckpointContext与create_selective_checkpoint_contexts条目只列A2/A3。上述是中文产品表；英文的显式排除和调试/恢复方法分歧在下节保留，不能因为CheckpointPolicy列950就推定整套selective接口均已纳入验证。

支持表列出的接口可用不代表当前模型所有随机状态、上下文、图后端、原地更新和参数分片组合均正确。每个入口按实际部署版本与计算路径核对，不将主线页面回推CANN9.0/PT2.8发布基线。

## 优化验收

对照关闭/启用重计算的相同输入、随机状态与精度，检查前向、梯度和多步loss，测峰值显存与步耗时。对sequential先按来源明确的FP32范围验收；其他组合单独验证，避免用一次前向通过代替反向一致性。

通用重计算策略与选择动机见[重计算概念](../concepts/techniques/recomputation.md)，其中框架或模型条件不自动成为上述原生接口的版本支持证明。

## 英文的显式排除与中文分歧

同提交七份英文页对SelectiveCheckpointContext和create_selective_checkpoint_contexts明确950DT不支持，而中文仅列A2/A3。更需区分set_checkpoint_debug_enabled：中文列三类产品，英文明确950不支持；set_device_states只在2.13/2.14收录，同样中文三类支持、英文950不支持。两者保持语言/版本范围，不用checkpoint或get_device_states的三产品表覆盖。

checkpoint、get_device_states、CheckpointPolicy及checkpoint_sequential的两侧表仍列三类产品，sequential的FP32限制不变。状态读取/恢复、调试和选择性策略不是一项能力，不由读状态接口支持推定恢复或任意随机/图组合已验证。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-utils-checkpoint.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-utils-checkpoint.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-utils-checkpoint.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-utils-checkpoint.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-utils-checkpoint.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-utils-checkpoint.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-utils-checkpoint.md)（primary）

- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-utils-checkpoint.md)（constraint）

- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-utils-checkpoint.md)（constraint）

- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-utils-checkpoint.md)（constraint）

- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-utils-checkpoint.md)（constraint）

- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-utils-checkpoint.md)（constraint）

- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-utils-checkpoint.md)（constraint）

- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-utils-checkpoint.md)（constraint）
