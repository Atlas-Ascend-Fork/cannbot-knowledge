---
type: Guide
title: 950 Inductor 调优成本：CostModel 筛选与动态形状分组
description: 说明候选预筛选失败回退、保留比例和分组 benchmark 的范围，避免把预测结果当作实测最优。
tags:
- task.implementation
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/INDUCTOR_ASCEND_ENABLE_COSTMODEL.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/INDUCTOR_ASCEND_COSTMODEL_RATIO.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/INDUCTOR_ASCEND_SYMBOLIC_GROUP_AUTOTUNE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/INDUCTOR_ASCEND_SYMBOLIC_GROUP_TEMPLATES.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/INDUCTOR_ASCEND_COSTMODEL_RATIO.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/INDUCTOR_ASCEND_ENABLE_COSTMODEL.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/INDUCTOR_ASCEND_SYMBOLIC_GROUP_AUTOTUNE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/INDUCTOR_ASCEND_SYMBOLIC_GROUP_TEMPLATES.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/config.py
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/costmodel/INDUCTOR_ASCEND_ENABLE_COSTMODEL.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/costmodel/INDUCTOR_ASCEND_COSTMODEL_RATIO.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/dynamicshape/INDUCTOR_ASCEND_SYMBOLIC_GROUP_AUTOTUNE.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/dynamicshape/INDUCTOR_ASCEND_SYMBOLIC_GROUP_TEMPLATES.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/costmodel/overview.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/dynamicshape/symbolic.md
  role: primary
created_at: '2026-11-09T06:01:51Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- '950'
---

# 950 Inductor 调优成本：CostModel 筛选与动态形状分组

## 固定版本与证据

依据 PyTorch/TorchNPU 固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的环境变量文档，按所列产品和选项限制使用，不推导发布组合具备全部功能。只读来源审阅，未运行上游代码或设备实验。

## CostModel 只做预筛选

INDUCTOR_ASCEND_ENABLE_COSTMODEL 默认关闭，1/true/yes 开启，0/false/no 关闭。Triton 有多个候选 config 时，生成 TTIR 并用已安装的 Triton-Ascend CostModel 预测耗时、重排与筛选；候选≤1 不调用。后端不可用、返回异常或无有效预测时跳过筛选，保留原候选集合。

INDUCTOR_ASCEND_COSTMODEL_RATIO 默认 0.25，范围 (0,1]；非法范围回到 0.25，1 不筛选。比例越低通常减少预编译和 profiling，但可能错失实际最优；筛选出的 config 都编译失败时，用先前被筛掉的候选兜底。预测不替代后续编译和实测结果。

## 动态 shape 分组是另一层复用

INDUCTOR_ASCEND_SYMBOLIC_GROUP_AUTOTUNE 默认 0，1/true/yes 开启，按动态轴 shape 特征分桶，用代表 shape 调优后为同桶运行输入选 config。只影响 Triton 的 pointwise、reduction、persistent_reduction 模板，静态 shape 不受影响。

INDUCTOR_ASCEND_SYMBOLIC_GROUP_TEMPLATES 默认这三类，逗号分隔；只在分组开关开启时生效，未知项忽略。计划不支持，或 benchmark 显存超过相应预算时，回退普通 autotune；文档提到 MAX_BENCHMARK_MEMORY_RATIO 控制预算，但本页未给默认值；同提交源码的补充见后文，不把它当作所有历史版本默认。两项是灰度功能，不保证所有动态 shape 都共享同一个最优配置。

分别比较冷编译时间、候选数量、回退日志和业务 shape 的稳态时延；分组代表值或 CostModel 预测最快不能替代目标输入的实测。


## 核验

保存解释器、包版本、设备、完整配置及首次生效时机，在新进程中做单项对照。检查数值与实际路径，再分别比较首次启动、稳态时间和资源开销；调试配置关闭后复测。

## 分组预算与解析层的补充

中英文分组两页明确列Ascend950PR及950DT；此前引用的CostModel独立环境页只列950DT；内部概述的PR/DT范围另见后文，不从分组开关自动扩大其他能力。同提交config.py给INDUCTOR_ASCEND_SYMBOLIC_GROUP_MAX_BENCHMARK_MEMORY_RATIO默认0.25，复用浮点解析器，合法有限数按(0,1]处理；转换失败、≤0或>1会告警回默认。

该解析器本身没有isfinite检查，不能仅凭范围比较就认定NaN已被拒绝，更不能从配置层推定下游如何处理它。CostModel开关的源码布尔解析还接受on/y并忽略前后空白，文档只承诺其列出的取值；不将额外解析容忍度当跨版本公共合同。预算、代表shape、后端可用性和真实编译结果仍分别核对。

## 内部CostModel概述与单动态轴条件

内部概述面向950PR/DT及PyTorch2.13，独立环境详情只列950DT；保留这处来源范围粒度，不能继续概括全部CostModel来源只列DT，也不把PR概述扩大为每个版本和模式均已验证。

该流程按config生成TTIR，从运行标量及grid构造Arg Bindings（需要时含num_programs_x），逐项调用Triton-Ascend costmodel_bench，过滤预测为无穷大的项，再排序、保留和记录兜底。它只在候选>1且比例处于(0,1)时预筛选，比例1不筛选。标量解析失败可使候选无有效预测；缓存键含TTIR与传入参数，模型/配置或参数变化不能假定仍命中。

Symbolic长说明把当前grouped autotune进一步限定为**一个动态shape轴**，从numel提取动态维/归约乘积特征，bucketize得到group_id、复用代表shape的best launcher，并按策略材料化R0BLOCK_SUB等运行block；访问签名不一致、无法构造代表或显存超预算均回普通流程。文档还称支持AOT/CppWrapper分组调度和Kernel落盘，这不覆盖MegaCache明确排除CppWrapper产物的另一层制品打包。具体形状复用与分档见[动态形状指南](torch_npu_inductor_dynamic_shape_choices.md)。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/INDUCTOR_ASCEND_ENABLE_COSTMODEL.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/INDUCTOR_ASCEND_COSTMODEL_RATIO.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/INDUCTOR_ASCEND_SYMBOLIC_GROUP_AUTOTUNE.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/INDUCTOR_ASCEND_SYMBOLIC_GROUP_TEMPLATES.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/INDUCTOR_ASCEND_COSTMODEL_RATIO.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/INDUCTOR_ASCEND_ENABLE_COSTMODEL.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/INDUCTOR_ASCEND_SYMBOLIC_GROUP_AUTOTUNE.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/INDUCTOR_ASCEND_SYMBOLIC_GROUP_TEMPLATES.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/config.py)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/costmodel/INDUCTOR_ASCEND_ENABLE_COSTMODEL.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/costmodel/INDUCTOR_ASCEND_COSTMODEL_RATIO.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/dynamicshape/INDUCTOR_ASCEND_SYMBOLIC_GROUP_AUTOTUNE.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/dynamicshape/INDUCTOR_ASCEND_SYMBOLIC_GROUP_TEMPLATES.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/costmodel/overview.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/dynamicshape/symbolic.md)（primary）
