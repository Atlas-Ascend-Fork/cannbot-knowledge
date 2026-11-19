---
type: Guide
title: Eager DVM的Foreach规模门控与SwiGLU View输入
description: 核对Foreach列表规模、dtype与共享Storage回退，区分scalar-list例外，并解释SwiGLU双半区Load及FP32计算。
tags:
- task.optimization
- topic.graph_execution
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_ops.cpp
  role: primary
created_at: '2026-11-11T03:41:44Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Eager DVM的Foreach规模门控与SwiGLU View输入

固定OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`的Eager Foreach helpers、包装与SwiGLU入口。产品与配套待核，保持draft、空平台。默认阈值及环境解析见[原生门控](torch_npu_eager_dvm_native_flags_and_dump_consumers.md)。本次静态读取源码，运行和性能验收待执行。

## 列表规模与别名

ForeachWorthFusing在列表长度不超过foreach_max_tensors时返回True，超过时要求每个self Tensor的numel都至少为foreach_min_numel。默认值分别为8和65536。该准入表达式描述实现策略，实际收益仍取决于工作负载。

AddStorageAliases按StorageImpl指针去重，忽略未定义Tensor和空StorageImpl指针。可写foreach遇到同Storage立即Flush并转入对应op_api，包含同一Tensor重复出现及同Storage兄弟view。这里检查共享Storage，并未计算切片是否真正交叠。

## 各helper的实际条件

| 本地消费者 | 共同门控之外的准备 |
| --- | --- |
| ForeachBinaryScalar，单scalar | 先规模门控，逐Tensor采用默认InputCheck，再将Long/Double scalar转float，别名检查后PrepareWritableOutput并逐项生成输出。 |
| ForeachBinaryScalar，scalar list | 同样规模门控，另要求scalar数等于Tensor数，逐项预先解析所有scalar后再修改图。 |
| ForeachAddc，单scalar | 规模门控、三列表长度一致、输入仅Half/Float且同dtype，另两Tensor可广播进对应input，三列表整体检查Storage别名。 |
| ForeachAddc，scalar list | 要求三个Tensor列表与scalar列表长度一致并执行同类dtype/broadcast/别名检查，本重载没有调用ForeachWorthFusing。 |

Addc生成input+scalar*(tensor1 op tensor2)，op分别取Mul或Div。helper会先准备写目标以及两个读取列表。所有所读原地foreach包装在成功建图后显式Flush。

_foreach_sqrt函数式包装采用规模与浮点连续准入，PrepareFusionInput后为每项申请新结果，返回前没有额外显式Flush。_foreach_sqrt_另检查Storage别名、准备写目标并在结束时Flush。列表准入失败时整次调用走对应op_api路径。

## SwiGLU的两个半区

npu_swiglu要求O2和默认InputCheck，dim按rank规范化后需要有效，所选维size必须为偶数。先PrepareFusionInput，再将该维尺寸减半，沿原strides为两半建立ViewInput。第二半地址偏移是half*dim_stride*element_size，base Tensor由ViewInput保存以维持Storage存活。

Half输入的两个对象在handler中显式转为FP32，再计算x0/(1+exp(-x0))*x1；BF16入口行为还受ViewInput自身的SoC转换条件影响。最后按原输入options、原dtype和减半后的shape申请输出，返回前没有额外显式Flush。

记录列表长度、每项numel、实际Storage身份、scalar形式及SwiGLU的dim/shape/stride。将别名回退、规模策略、双半区访问和真实kernel提交分别观察，并先检查数值与输出别名再评估收益。View的登记与后续原地写保护见[Tensor复用](torch_npu_eager_dvm_metadata_alias_and_view_lifetime.md)。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_ops.cpp)（primary），读取范围 1–2372。
