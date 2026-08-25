---
type: API
title: And
description: 根据mask对两个RegTensor或MaskReg执行按位与操作，将结果写入目的操作数，支持ZEROING模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/logical_compute/And.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# And

头文件路径为："basic_api/reg_compute/kernel_reg_compute_vec_binary_intf.h"（对RegTensor操作）、"basic_api/reg_compute/kernel_reg_compute_maskreg_intf.h"（对MaskReg操作）。

本节介绍两种接口，分别用于对RegTensor和MaskReg进行操作
- 对RegTensor操作
  根据mask对输入数据srcReg0、srcReg1执行按位与（&）操作，将结果写入dstReg。

- 对MaskReg操作
  根据mask对两个输入MaskReg数据src0、src1执行按位与（&）操作，将结果写入dst。

参数：T: 操作数数据类型。；mode: MaskMergeMode枚举类型。选择MERGING模式或ZEROING模式。 • ZEROING模式下，mask未筛选的元素在dstReg中置零。 • MERGING模式当前不支持。；U: 目的操作数和源操作数的RegTensor类型，例如RegTensor ，由编译器自动推导，用户不需要填写。；dstReg(输出): 目的操作数。 类型为RegTensor。；srcReg0(输入): 源操作数。 类型为RegTensor。 两个源操作数的数据类型需要与目的操作数保持一致。；srcReg1(输入): 源操作数。 类型为RegTensor。 两个源操作数的数据类型需要与目的操作数保持一致。；mask(输入): 指示源操作数元素操作的有效性，详细说明请参考MaskReg文档。；dst: 目的操作数。

支持数据类型：bool、int8_t、uint8_t、int16_t、uint16_t、int32_t、uint32_t、int64_t、uint64_t。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Not](not.md)（`related`）：Not 可构造掩码反转并与 And 组合。
- [Or](or.md)（`related`）：And/Or 是位表达式的互补操作。
- [And](../../memory_vector_compute/logical_compute/and.md)（`same_topic`）：And说明根据mask对两个RegTensor或MaskReg执行按位与操作，将结果写入目的操作数，支持ZEROING模式。
- [Ands](../../memory_vector_compute/logical_compute/ands.md)（`same_topic`）：Ands：Ands在 isSetMask=false时依赖SetMaskCount/Norm/VectorMask并要求ResetMask；And的tensor与Reg版本帮助区分标量按位与和双tensor按位与。 目标卡《And》补充：根据mask对两个RegTensor或MaskReg执行按位与操作，将结果写入目的操作数，支持ZEROING模式。
- [AscAnd](../../../c_api/reg/logic_compute/asc_and.md)（`same_topic`）：C Reg API 是同一 And 的语言映射。
- [AscAnd](../../../c_api/vector_compute/asc_and.md)（`same_topic`）：AscAnd：C Vector AscAnd、C Reg AscAnd及两套基础And都是逐元素按位与，关系用于核对操作数容器、mask与数据类型约束。 目标卡《And》补充：根据mask对两个RegTensor或MaskReg执行按位与操作，将结果写入目的操作数，支持ZEROING模式。
<!-- cannbot:related:end -->
