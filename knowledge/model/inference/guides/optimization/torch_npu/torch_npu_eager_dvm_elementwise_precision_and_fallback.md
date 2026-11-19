---
type: Guide
title: Eager DVM逐元素融合的类型、精度与回退条件
description: 聚合Cast、算术、比较和激活的实际准入、公共类型及FP32计算，核对原地提交与GELU近似参数消费者。
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

# Eager DVM逐元素融合的类型、精度与回退条件

## 固定实现

本卡覆盖OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`中Eager lazy-fusion逐元素入口。本次全文静态读取本地ops实现，产品、发布配套、数值与性能验收待核，保持draft、空平台。开关条件见[Eager DVM原生门控](torch_npu_eager_dvm_native_flags_and_dump_consumers.md)，图内复用与提交见[Tensor别名](torch_npu_eager_dvm_metadata_alias_and_view_lifetime.md)和[工作区生命周期](torch_npu_eager_dvm_flush_workspace_and_allocation_reentry.md)。

## 共同准入和逐入口回退

各入口用函数内static保存IsEnabled(op, required)结果，门控或helper拒绝后调用相应op_api入口。InputCheck同时检查NPU、dtype与连续性。请求allow_non_contig时，还依赖O2等级和IsViewLoadable条件。NpuCheck的Optional重载允许无值，已存在的Tensor仍需NPU。OutputCheck要求NPU且连续。DumpOp建立RECORD_FUNCTION记录；只有kernel的ShouldDump为真时，才调用kernel Dump保存算子与参数。

| 局部类型集合 | 成员及消费者 |
| --- | --- |
| IsFloat16_32 | Half、Float，foreach addc族使用 |
| IsFloatType | Half、Float、BFloat16，sqrt/exp/reciprocal、div/pow、比较及多数激活使用 |
| IsFloatIntType | 上述浮点加Int，abs/neg、add/sub/mul、min/max及relu使用 |
| IsSupportType | 再加Bool，DVM dtype_cast的源和目标均按此检查 |

DVM _npu_dtype_cast直接构造Cast节点并按目标dtype申请输出。所读入口对同dtype也沿该建图申请路径，原生ACL/OpAPI分配行为另见[Cast后端与存储](torch_npu_dtype_cast_backend_allocation_and_aliases.md)。

## 算术和比较

BinaryTensor对CPU零维other转取item后使用标量helper，其他Tensor需通过两个InputCheck。不同输入dtype时按result_type构造公共类型，BF16公共类型在该分支使用FP32。BinaryScalar接受Long/Double标量并转float，add/sub还按Half/BF16结果类型将标量先舍入；mul/div沿所读float标量。

Add和Sub另外接收alpha。Add的整数other、整数alpha先做整数乘法，混合Long/Double分支以double相乘后交标量helper。Sub的Double alpha会把计算类型提升为FP32。原地二元入口先检查other能广播进self，self尺寸保持为写目标尺寸，随后PrepareWritableOutput与读取准备，再生成节点。

add/sub/mul/div/pow的原地包装、exp_、tanh_、relu_与leaky_relu_在登记输出后显式LazyFusionFlush。函数式入口通常保留待融合图。eq/ne/gt/ge/lt/le使用浮点准入并申请Bool结果，maximum/minimum采用浮点加Int准入。这些是所读分支的准入范围。

FloorDivide先构造Div再Floor。标量分支只接受Long/Double并转换float；Tensor混合dtype按公共类型转换。floor_divide_out额外要求OutputCheck，CPU scalar other走原生回退。该out入口的本地门控没有where_out那组显式shape/dtype匹配条件，实际外层分派需结合准确入口核验。

where要求condition为连续NPU Bool，另外两个输入采用浮点准入。函数式分支允许通过ViewLoad条件的非连续数据输入。where_out的数据输入采用默认连续准入，并明确计算三输入broadcast后的shape，要求out尺寸和result_type一致，登记后提交。

## 激活的计算表达式

sigmoid和silu前反向显式Cast为FP32后构造其表达式，再按输入或梯度dtype申请输出。sigmoid反向采用dy*y*(1-y)，silu反向使用sigmoid与x*sigmoid组合。tanh前向把FP32输入截到[-8.8,8.8]，构造(exp(2x)-1)/(exp(2x)+1)；反向使用dy*(1-y*y)，要求两输入dtype一致。

gelu_out只在approximate等于tanh、out与self的shape/dtype匹配且OutputCheck成立时采用DVM，构造含0.044715和1.5957691216057308的FP32表达式。gelu_backward的所读准入只检查输入类型和dtype一致，approximate参与回退调用及Dump，DVM建图分支本身始终构造含tanh近似的表达式。采用不同approximate值时，应针对这条真实分支比较前反向数值。

relu用max(x,0)，LeakyRelu用max(x,0)+slope*min(x,0)，slope经标量helper转换。slope为0时只使用正半轴对象。out登记最终会按目标dtype转换，实际计算类型与返回Tensor类型需分别记录。

## 验证记录

记录实际分派、每op门控、dtype/stride、CPU scalar与alpha、out和原地别名、approximate以及提交边界。分别检查数值和准备成本，再评价融合收益。源码注释中的对齐目标属于实现动机，本次设备比较与性能测量待执行。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_ops.cpp)（primary），读取范围 1–2372。
