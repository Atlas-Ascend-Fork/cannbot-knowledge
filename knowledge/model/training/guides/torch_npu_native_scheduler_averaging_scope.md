---
type: Guide
title: 原生学习率调度与参数平均：方法类型和产品边界
description: 区分lr与参数dtype，保留MultiplicativeLR状态保存的950DT排除及SWA/EMA中文清单范围。
tags:
- task.optimization
- topic.optimizer
- topic.checkpointing
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-optim.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-optim.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-optim.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-optim.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-optim.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-optim.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-optim.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-optim.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-optim.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-optim.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-optim.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-optim.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-optim.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-optim.md
  role: constraint
created_at: '2026-11-09T13:25:17Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
- '950'
---

# 原生学习率调度与参数平均：方法类型和产品边界

## 固定版本与范围

依据TorchNPU主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的PyTorch2.7.1、2.9至2.14中英文原生支持页。来源仅给所列产品和接口的支持/约束信息；未收录不等于已证实不支持，缺少的参数与组合不补造。按A2/A3训练系列和950DT分别消费，不扩展950PR，不回推26.0/PyTorch2.8发布组合，也不证明主线与其他框架配套。本卡仅静态审阅，未执行上游、训练、进程启动或设备实验。

## 调度类与方法不能合并为一张dtype表

LambdaLR、MultiplicativeLR、StepLR、MultiStepLR、ConstantLR、LinearLR、ExponentialLR、PolynomialLR、CosineAnnealingLR、ChainedScheduler、SequentialLR、ReduceLROnPlateau、CyclicLR、OneCycleLR和CosineAnnealingWarmRestarts类列三类产品。LRScheduler基类及get_last_lr/get_lr/load_state_dict/state_dict/step只在中文七页列三类产品，不由英文缺项认定基类不可用。

| 调度器 | 限定lr类型的方法 | 来源类型 |
| --- | --- | --- |
| MultiplicativeLR | get_last_lr、load_state_dict、state_dict | FP32 |
| StepLR、MultiStepLR | get_last_lr、load_state_dict、state_dict | FP16/FP32 |
| ConstantLR | get_last_lr、load_state_dict、state_dict | FP32 |

这些是lr字段的局部限制，不是把模型参数、梯度或优化器状态统一转换为该dtype的指令；也不能据其余get_lr没有同一句限制便断言支持任意Tensor学习率。MultiplicativeLR.state_dict明确950DT不支持，类和其他方法的支持不能补齐完整保存/恢复流程。

其余列出的get_last_lr、get_lr、load_state_dict、state_dict按各类实际子项列三类产品；并非每类都列齐这些方法。中文额外列ChainedScheduler.step、SequentialLR.recursive_undo/step、ReduceLROnPlateau.load_state_dict/step和CyclicLR.scale_fn等；英文没有全部重复，不能将收录差异当作同名方法运行结果。CosineAnnealingWarmRestarts.step两侧均列三类产品。

## SWA与EMA只使用来源明确的信息

七份中文页对swa_utils.AveragedModel及forward、SWALR、get_ema_multi_avg_fn和update_bn列三类产品，英文页未收录这一章。SWALR.load_state_dict仅在中文2.10..2.14收录，2.7.1/2.9未列；这不证明旧包实际无该方法。

清单没有平均更新公式、decay/default、buffer同步、BatchNorm数据重跑、分片参数、优化器/调度器恢复顺序及图模式的完整合同，不凭函数名生成一套已验证的SWA/EMA训练方案。forward产品表也不能覆盖未列出的update_parameters和任意分布式组合。

## 优化与恢复验收

固定实际版本、每个参数组的学习率表示和调用序列，对照逐步学习率轨迹、状态恢复后下一步行为、平均参数和模型输出，再测调度/平均的端到端开销。清单不承诺收敛、训练吞吐或模型质量收益，本卡没有运行训练。

- [原生优化器的foreach/fused与方法级dtype](torch_npu_native_optimizer_modes.md)
- [分布式状态检查点的独立边界](torch_npu_native_distributed_checkpoint_scope.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-optim.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-optim.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-optim.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-optim.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-optim.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-optim.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-optim.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-optim.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-optim.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-optim.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-optim.md)（constraint）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-optim.md)（primary）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-optim.md)（constraint）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-optim.md)（constraint）
