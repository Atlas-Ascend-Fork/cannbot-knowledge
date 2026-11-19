---
type: Guide
title: TorchNPU DTensor分组Matmul列表策略与kwargs
description: TorchNPU DTensor分组Matmul列表策略与kwargs的固定双版本本地规则、重分布边界与验收条件。
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

# TorchNPU DTensor分组Matmul列表策略与kwargs

固定PyTorch仓主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`与发布快照`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的distributed/tensor/_matrix_ops.py。本文仅说明本地候选和派发实现，不据注册推导全部产品、dtype、shape或通信组合可用；未导入运行上游或设备实验。

## 列表数量、量化参数与bias限制

default和List两个overload分别注册RuntimeSchemaInfo，needs_pytree=True；静态kwargs名单包括bias及scale/offset/antiquant/per_token和activation相关列表，只有default名单含group_list。策略从x、weight、bias列表计数；split_item为0/1时按weight数量给多输出，其余为单输出。到达读取bias的len操作前没有将显式None独立规范化为空列表，不能把注解Optional当作本函数已经处理全部缺省表示。

先给全部复制。如果scale、offset、antiquant_scale、antiquant_offset、per_token_scale或三项activation参数在schema中是非空TupleStrategy，就提前展开并返回复制方案；这个局部判断不是识别所有可能Python容器的完整量化开关。无bias时可加入一边复制、一边Partial并输出Partial，避免把bias重复加到归约结果；存在bias则不加这些Partial候选。

在没有提前返回而到达后续group_type检查时，group_type非None且大于0抛NotImplementedError；不把这条局部分支改写成所有输入都会先校验group_type。

## 三类矩阵列表布局

多x/多weight/多输出分支按第一份x的rank统一为各pair套规则：x非末维分片则输出同维、weight和bias复制；weight列维Shard(1)时输出沿x末维，bias沿0；无bias才能将x末维与weight第0维收缩分片成Partial。源码假设每组shape与列表数量对应，没有在本函数逐pair验证全部等形等长。

单x/单weight/单输出分支假设x二维、weight三维：无bias时x与weight沿1分片得到Partial；列方案是x复制、weight沿2分片、输出沿1、bias沿1。其余weight数量大于1的分支给无bias收缩分片或列分片，列方案weight及输出沿1、bias沿0，x复制。group_list张量始终复制。

展开时input_index=y_num，单输出还把output_specs包成列表以符合算子Tensor[]返回；不是把单输出改成普通Tensor合同。

## kwargs推导与版本内部差异

_handle_tensor_list_in_kwargs只处理Python list且所有元素均DTensor的kwargs，取_spec组成tuple便于缓存，_local_tensor组成list；空列表因all为空成立也会进入。主线末尾重算schema比较键，发布没有该调用；不递归任意列表/tuple混合结构。

目标kwargs根据第一个输出spec：group_list复制，bias只在输出placement是输出末维Shard时改成Shard(0)，其它张量列表复制。单x/三维weight分支的候选bias沿1，但这个通用kwargs推导仍用0，不能把策略候选与消费推导默认写成在所有分支严格一致；需针对该分支实际验收。列表识别只检查首个元素的spec类型，不构成所有项完整Schema验证。

发布用TupleStrategy.childs，主线用children；发布缺schema_info时补needs_pytree，并在handler传播前把op_info.schema.return_type_tensor替换为恒True函数，以处理旧版列表输出Meta。主线没有这两个局部补丁，不能跨版本混用私有字段。

handler先unwrap并处理kwargs列表，再propagate；参与mesh的rank分别重分布args和kwargs后调用op，非参与rank用公共空结果helper，最后wrap。未执行这些步骤，列表支持、Partial归约和性能仍需按真实模型验证，公共行为见[重分布与注册](torch_npu_dtensor_redistribution_and_registration.md)。
