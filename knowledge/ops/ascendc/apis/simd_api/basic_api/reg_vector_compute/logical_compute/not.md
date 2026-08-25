---
type: API
title: Not
description: 根据mask对RegTensor或MaskReg执行按位取反操作，将结果写入目的操作数，支持ZEROING模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/logical_compute/Not.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# Not

头文件路径为："basic_api/reg_compute/kernel_reg_compute_vec_unary_intf.h"（对RegTensor操作）、"basic_api/reg_compute/kernel_reg_compute_maskreg_intf.h"（对MaskReg操作）。

本节介绍两种接口，分别用于对RegTensor和MaskReg进行操作
- 对RegTensor操作
  根据mask对输入数据srcReg执行按位取反操作，将结果写入dstReg。

- 对MaskReg操作
    根据mask对输入数据src执行按位取反操作，将结果写入dst。

参数：T: 操作数数据类型。；mode: MaskMergeMode枚举类型。选择MERGING模式或ZEROING模式。 • ZEROING模式下，mask未筛选的元素在dstReg中置零。 • MERGING模式当前不支持。；U: 目的操作数和源操作数的RegTensor类型，例如RegTensor ，由编译器自动推导，用户不需要填写。；dstReg(输出): 目的操作数。 类型为RegTensor。；srcReg(输入): 源操作数。 类型为RegTensor。 源操作数的数据类型需要与目的操作数保持一致。；mask(输入): 源操作数元素操作的有效指示，详细说明请参考MaskReg。；dst: 目的操作数。；src: 源操作数。

支持数据类型：int8_t、uint8_t、int16_t、uint16_t、half、int32_t、uint32_t、float、int64_t、uint64_t。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [And](and.md)（`related`）：Not 可构造掩码反转并与 And 组合。
- [Not](../../memory_vector_compute/logical_compute/not.md)（`same_topic`）：Memory Not 与 Reg Not 都执行逐位取反；前者使用 LocalTensor，后者使用 RegTensor/MaskReg 且要求 ZEROING，便于按执行模型选择实现。
<!-- cannbot:related:end -->
