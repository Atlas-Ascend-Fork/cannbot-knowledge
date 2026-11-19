---
type: Guide
title: Eager DVM归一化的统计、训练反向与输入准备
description: 聚合BatchNorm各入口的FP32准入、连续化、辅助输出、counts加权统计及原生归约与DVM反向组合。
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

# Eager DVM归一化的统计、训练反向与输入准备

固定OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`的Eager BatchNorm本地定义。平台和发布配套待核，保持draft、空平台，数值及分布式运行验收待执行。原生ACLNN BatchNorm准备另见[原生BatchNorm执行](../../../../training/guides/torch_npu_native_batch_norm_opapi_execution.md)。

## native_batch_norm与通道向量

BatchNormVectorCheck允许Optional无值，已给值必须是一维、numel等于channels且dtype为Float。native_batch_norm采用DVM的条件包括training=False、输入Float、rank为2到4，以及输入和已给Optional Tensor均为NPU。

输入和已给参数先contiguous，缺少running_mean/running_var时分别申请零/一向量，save_mean与save_invstd均申请零向量。随后先Flush，再以通道维1生成broadcast shape，使用running_var+eps求倒数平方根，构造中心化、缩放及可选weight/bias。返回输出和两份零辅助向量，动量参数在这条推理表达式中没有更新running统计。

## native_batch_norm_backward

反向要求O2、输入及grad_out为Float、输入rank为2到4并满足所列NPU条件。

| 分支 | 实际消费者 |
| --- | --- |
| train=True | 要求save_mean/save_invstd存在、channels非零并满足通道向量条件。先调用op_api::batch_norm_backward_reduce，need_input_reduce取输入/weight梯度mask的或，bias按自己的mask取归约返回值。 |
| train=False | 准备连续输入、梯度和参数，缺weight时用一、缺running mean/var时用零/一，Flush后在DVM中按非通道轴归约weight和bias梯度，按mask申请各输出。 |

训练分支对名为save_invstd的Tensor实际再次构造1/sqrt(value+eps)，将所得rstd用于grad_weight，并在需要grad_input时传给batch_norm_backward_elemt。采用时须核对调用方对该参数的真实定义及对应数值，变量名字与本地表达式都需要保存。

需要grad_input时还申请值为input.numel()/channels的Float count Tensor。batch_norm_backward_elemt本地要求weight存在，否则回到对应op_api；因此这条训练组合可能同时经过原生归约与DVM构图，各分支按实际mask和输入核验。

## stats与counts聚合

batch_norm_stats要求Float NPU输入，按除通道轴1之外各轴计算count，count非正时回退。连续化后通过sum(x/count)求均值，对中心化平方同样按count归约，再由variance+eps求invstd。两份输出申请采用invstd的shape，返回前Flush。

batch_norm_gather_stats_with_counts要求所列输入为NPU，input为Float，已给running统计通过InputCheck。输入、mean、invstd和counts先contiguous，再Flush。counts以[numel,1]逻辑shape输入，求global_counts，加权mean按mean除最后轴之外的轴归约。

局部表达式先计算std=1/invstd，再按std*std-eps还原variance，加上局部mean与global_mean差的平方，乘counts后归约。输出global variance使用global_counts作分母，更新running_var使用global_counts-1作分母；running_mean和running_var按momentum更新。本函数没有另行对这些分母建立完整正值限制，采用前核对counts和有效样本数。

## elemt消费者与资源准备

batch_norm_elemt将输入及参数contiguous并Flush，按通道维1广播传入mean/invstd，再构造归一化与可选weight/bias；eps在此进入Dump参数，计算直接消费提供的invstd。

batch_norm_backward_elemt将grad/input/mean/invstd/weight、两项sum及count准备为连续Tensor并Flush。count沿其全部轴归约，再构造由sum_dy、sum_dy_xmu和global_counts校正的输入梯度。两个elemt入口在本地按维1构造广播shape，调用者的rank、通道向量、dtype与实际外层检查需要一致。

本组local body包含连续化、辅助Tensor申请、原生归约、多个融合边界和运行统计写回。评估时分别记录这些阶段及output_mask、train、eps、momentum和counts，再比较精度与峰值资源。已有Storage与逻辑shape交互见[Eager复用边界](torch_npu_eager_dvm_metadata_alias_and_view_lifetime.md)。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_ops.cpp)（primary），读取范围 1–2372。
