---
type: Guide
title: Eager DVM矩阵乘与Sum的布局和提交条件
description: 解释矩阵布局识别、连续化与addmm epilogue，记录Sum的FP32准入、维度处理和out准备边界。
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

# Eager DVM矩阵乘与Sum的布局和提交条件

本卡静态审阅OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`的Eager MatMulAdapter、matmul/mm/bmm/addmm与Sum入口，平台和完整配套待核，保持draft、空平台。输入缓存和分配生命周期沿用[Eager DVM复用](torch_npu_eager_dvm_metadata_alias_and_view_lifetime.md)。

## 矩阵输入准备

矩阵乘四个包装均要求O2。MatMulAdapter要求两个主输入为NPU基础格式、dtype一致且为Half或BFloat16、rank在2到4。存在bias时还要求基础格式、连续且dtype为主输入类型或Float。

连续矩阵直接使用。非连续输入先尝试末两维转置识别，要求倒数第二维stride为1、末维stride等于倒数第二维size，外部batch步幅为连续乘积；识别成功时翻转trans标记并交换相应逻辑尺寸。其余通过检查的布局调用contiguous准备。局部尺寸上界只比较当前x_shape.back与y_shape.back不超过UINT16_MAX-UINT8_MAX，即65280，其他轴及具体DVM矩阵合法性仍沿后续消费者核验。

MatMul在上述准备后先LazyFusionFlush，取得新kernel，再用enable_cast=False及显式shape输入，传入转置标志。输出按主输入options和dtype申请。包装只在helper返回未定义Tensor时走对应op_api回退，成功后记录Dump并返回。

## addmm的bias与后处理

alpha和beta经GetScalarValue接受Long/Double并转float。self作为bias交MatMulAdapter检查。只有self为一维且alpha、beta都为1时，MatMul直接接收bias对象。

其余分支先计算矩阵乘，将Half/BFloat16计算对象转FP32，再处理alpha缩放。beta为0时跳过读取self，非零时读取并按计算类型转换，必要时乘beta后相加。输出申请使用self.options，因此self与矩阵主输入的dtype和输出准备需分别核对。

## Sum

三个Sum入口均要求O2、浮点输入且选择的out_type为Float。未指定dtype时out_type取self.dtype，因此Half/BFloat16输入需要准确的dtype选择才能通过这项门控。输入建图后显式Cast为FP32，再Reduce Sum，并在返回前LazyFusionFlush。

无dim重载归约全部维度，keepdim为False。带dim的重载将负轴加rank，dim为空或未给时展开全部轴，keepdim原样交DVM。所读循环没有另外建立重复轴和所有越界轴的校验，采用时保留实际分派与下层检查。

sum_out只对out调用OutputCheck，写入前PrepareWritableOutput，再按所读axis逻辑建图并登记到调用方out。它没有在本函数另行按归约shape申请新out，局部准入也没有完整的目标shape/dtype对照。应核对实际外层元数据准备、输出地址和最终dtype。

## 优化测量

把转置识别、contiguous准备、矩阵乘和后处理分别计成本。记录O2门控、输入rank/stride/内部格式、alpha/beta、self与矩阵dtype、归约轴和显式提交次数。先验证结果、别名及资源寿命，再比较稳态表现。本次只有源码证据，运行验收待执行。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_ops.cpp)（primary），读取范围 1–2372。
