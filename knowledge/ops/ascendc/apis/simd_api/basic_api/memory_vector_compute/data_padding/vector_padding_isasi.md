---
type: API
title: VectorPadding
description: 根据填充模式和方向对源操作数按datablock进行填充操作，支持邻近数填充和对称填充等模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_padding/VectorPadding_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# VectorPadding

根据填充模式和方向对源操作数按datablock进行填充操作，支持邻近数填充和对称填充等模式。

根据padMode（pad模式）与padSide（pad方向）对源操作数按照datablock进行填充操作。 假设源操作数的一个datablock有16个数，datablock[0:15]=a\~p： - padSide==false：从datablock的左边开始填充，即datablock的起始值方向(a->p) - padSide==true：从datablock的右边开始填充，即datablock的结束值方向(p->a) - padMode==0：用邻近数作为填充值，例：aaa|abc(padSide=false)、nop|ppp(padSide=true) - padMode==1：用邻近datablock值对称填充，例：cba|abc(padSide=false)、nop|pon(padSide=true) - padMode==2：用邻近datablock值填充，偏移一个数，做对称填充，例： - padSide=false：xcb|abc，xcb被填充，填充过程描述：a被丢弃，对称填充，x处填充0 - padSide=true：nop|onx，onx被填充，填充过程描述：p被丢弃，对称填充，x处填充0

本接口属于 UB 矢量计算数据填充接口。

约束：操作数地址对齐要求请参见通用地址对齐约束。；mask仅控制目的操作数中的哪些元素要写入，源操作数的读取与mask无关。；count表示写入目的操作数中的元素总数，源操作数的读取与count无关。
