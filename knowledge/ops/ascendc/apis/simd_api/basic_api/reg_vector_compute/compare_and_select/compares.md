---
type: API
title: Compares
description: 逐元素比较RegTensor中每个元素与标量的大小关系，结果为真则MaskReg对应比特位置1。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/compare_and_select/Compares.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# Compares

头文件路径为："basic_api/reg_compute/kernel_reg_compute_vec_cmpsel_intf.h"。

该接口用于逐元素比较源操作数中每个元素与一个标量的大小关系，根据模板参数指定的比较模式（LT/GT/GE/EQ/NE/LE）判断结果是否为真，若为真则输出MaskReg对应比特位置1，否则置0。

参数：T: 矢量源操作数数据类型。；mode: 比较模式。支持如下取值： • LT：小于 • GT：大于 • GE：大于或等于 • EQ：等于 • NE：不等于 • LE：小于或等于；U: 矢量源操作数的RegTensor类型，由编译器自动推导，用户不需要填写。；S: 标量操作数数据类型。；dst(输出): MaskReg类型，目的操作数。；srcReg(输入): 源操作数。 类型为RegTensor。；scalarValue(输入): 源操作数。 类型为标量。；mask(输入): 源操作数元素操作的有效指示，详细说明请参考MaskReg。

约束：通过mask参数控制的未选中元素在目的操作数中被置零。

仅 Ascend 950PR/Ascend 950DT 支持。
