---
type: API
title: Interleave
description: 对寄存器源操作数srcReg0和srcReg1中的元素进行交织，存入结果寄存器dstReg0和dstReg1中。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/data_reorder/Interleave.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Interleave

给定源操作数寄存器srcReg0和srcReg1，将srcReg0和srcReg1中的元素交织存入结果操作数dstReg0和dstReg1中。交织排列方式如下图所示，其中每个方格代表一个元素

头文件："basic_api/reg_compute/kernel_reg_compute_vec_interleave_intf.h"。

参数：T: 目的操作数和源操作数的数据类型。支持的数据类型请参考数据类型。；U: 源操作数和目的操作数的RegTensor类型，例如RegTensor，由编译器自动推导，用户不需要填写。；dstReg0<br>dstReg1(输出): 目的操作数。 类型为RegTensor。；srcReg0<br>srcReg1(输入): 源操作数。 类型为RegTensor。 源操作数的数据类型需要与目的操作数保持一致。

支持数据类型：bool、int8_t、uint8_t、int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float、int64_t、uint64_t。

约束：- srcReg0、srcReg1、dstReg0、dstReg1的数据类型需要保持一致。
- srcReg0和srcReg1可以为同一个RegTensor。
- dstReg0和dstReg1不能为同一个RegTensor。
- 允许源操作数和目的操作数为同一个RegTensor，例如Interleave(srcReg0, srcReg1, srcReg0, srcReg1)。
- 数据类型为b64时，仅支持RegTraitNumTwo。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [B16 交错 DINTLV 成对归零 — 转 fp32 后重排](../../../../../runbooks/precision/b16_interleave_compute_should_promote_to_b32_layout.md)（`exemplifies`）：该卡实测 B16 交织布局直接计算会成对归零，给出先升 B32 的边界。
- [DeInterleave 两路写反——按偶索引到 dst0 修正](../../../../../runbooks/precision/deinterleave_dst0_is_even_lane_output.md)（`exemplifies`）：该卡明确 DeInterleave dst0/dst1 对应偶/奇 lane，可验证交织顺序。
- [DeInterleave](de_interleave.md)（`related`）：Reg DeInterleave 把两个 RegTensor 拆为交错子流，Reg Interleave 用相同寄存器布局重新组合，是成对计算前后的直接布局链。
- [Interleave](../mask_reg_compute/interleave.md)（`related`）：MaskReg 版本操作掩码位布局，不等同于数值 RegTensor 交织。
- [Interleave](../../memory_vector_compute/data_rearrange/interleave.md)（`same_topic`）：Memory Tensor 版本完成同一交织任务，可按数据驻留选择。
<!-- cannbot:related:end -->
