---
type: Guide
title: TorchNPU DTensor AdamW out状态布局与对象复用
description: TorchNPU DTensor AdamW out状态布局与对象复用的固定双版本本地规则、重分布边界与验收条件。
tags:
- task.optimization
- topic.parallelism
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/tensor/_matrix_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/distributed/tensor/_matrix_ops.py
  role: implementation
created_at: '2026-11-11T06:44:03Z'
updated_at: '2026-11-11T06:44:03Z'
platforms: []
---

# TorchNPU DTensor AdamW out状态布局与对象复用

固定PyTorch仓主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`与发布快照`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的distributed/tensor/_matrix_ops.py。本文仅说明本地候选和派发实现，不据注册推导全部产品、dtype、shape或通信组合可用；未导入运行上游或设备实验。

## 以out状态作为grad布局锚点

npu_apply_adam_w的default与out均注册策略，但定制handler字典只给out入口。grad是第7位置参数；存在out时从第一个out子策略取首spec作为grad目标，否则取grad的首候选。第8位置max_grad_norm存在时跟随该grad placements，其他OpStrategy位置参数保持各自首spec。

输出spec仅从kwargs的out各子项取首spec组成tuple；没有out时本地策略构造的是空输出tuple，不由它推导default的全部运行返回已经被正确包装。主线读取TupleStrategy.children，发布读取childs，不能跨版本照抄内部字段。

## out返回原对象并更新spec

handler先unwrap并处理DTensor列表kwargs，再传播。参与mesh的rank按需重分布args、恢复位置参数树，直接调用torch_npu.npu_apply_adam_w与op_info.local_kwargs；主线的redistribute_local_args额外传use_val_from_redistribute_schema，发布没有第三参。它没有在这里单独对out列表做另一个kwargs重分布回调。

若schema是out variant，逐个取原kwargs['out']对象，原位写其_spec，再返回这些原DTensor；一个时返回该对象，多个时tuple。这里没有复制out状态或把返回对象换成新DTensor，因此不能仅靠对象相等证明底层状态布局与数据已经同步迁移。该out返回分支在非参与rank也会走，但不执行本地优化器更新。

非out分支尝试wrap(local_results, output_spec)；local_results只在参与rank分支赋值，所以函数若被别的调用者用于非参与rank的非out情况，存在未赋值路径；当前定制字典只安装out，不能把这个静态路径当成已证默认安装会触发的故障。

模块将这五项定制handler合入旧字典，同名项覆盖、其他保留：GMM default/List、AdamW out、all-gather-mm与mm-reduce-scatter。导入赋值没有本地回滚。验收保留状态对象身份、grad/max_grad_norm/out placements、优化器状态数值和通信，不由spec更新宣称无需数据重分布。
