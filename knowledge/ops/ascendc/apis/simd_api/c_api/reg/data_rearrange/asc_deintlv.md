---
type: API
title: AscDeintlv
description: 将src0和src1中的元素解交织存入dst0和dst1，提供矢量数据解交织和掩码解交织两种模式，仅在AIV上生效。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_rearrange/asc_deintlv.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscDeintlv

将src0和src1中的元素解交织存入dst0和dst1中，本接口提供矢量数据解交织和掩码解交织两种功能模式
- 矢量数据解交织：对两个源矢量数据寄存器中的有效元素逐对解交织。src0的偶数索引元素写入dst0前半部分，奇数索引元素写入dst1前半部分。src1的偶数索引元素写入dst0后半部分，奇数索引元素写入dst1后半部分。
- 掩码解交织：对两个源掩码寄存器中的比特位按指定位宽解交织。src0的偶数索引位写入dst0前半部分，奇数索引位写入dst1前半部分。src1的偶数索引位写入dst0后半部分，奇数索引位写入dst1后半部分。

以int8_t数据类型为例，asc_deintlv的实现流程如图1所示
本接口为Reg矢量计算接口，仅在AIV上生效。

参数：dst0(输出): 目的矢量数据寄存器，写入解交织后的偶数索引元素集合。dtype须与dst1、src0、src1一致。；dst1(输出): 目的矢量数据寄存器，写入解交织后的奇数索引元素集合。dtype须与dst0、src0、src1一致。；src0(输入): 源矢量数据寄存器，参与解交织的操作数。dtype须与dst0一致。其偶数索引元素写入dst0前半部分，奇数索引元素写入dst1前半部分。；src1(输入): 源矢量数据寄存器，参与解交织的操作数。dtype须与dst0一致。其偶数索引元素写入dst0后半部分，奇数索引元素写入dst1后半部分。；dst0(输出): 目的掩码寄存器，写入解交织后的偶数索引位集合。；dst1(输出): 目的掩码寄存器，写入解交织后的奇数索引位集合。；src0(输入): 源掩码寄存器，参与解交织的操作数。其偶数索引位写入dst0前半部分，奇数索引位写入d。

支持数据类型：half。

约束：- 本接口仅在AIV上生效，非AIV调用直接返回。
- 本接口在Vector Function（__simd_vf__标记的函数）内调用。
- src0、src1、dst0、dst1的数据类型需要保持一致。
- src0和src1可以为同一个矢量数据寄存器或掩码寄存器。
- dst0与dst1必须为不同的矢量数据寄存器或掩码寄存器，若两者引用同一寄存器将导致两个输出互相覆盖，结果未定义。
- 允许源操作数和目的操作数为同一个矢量数据寄存器，例如asc_deintlv(src0, src1, src0, src1)。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [DeInterleave 两路写反——按偶索引到 dst0 修正](../../../../../runbooks/precision/deinterleave_dst0_is_even_lane_output.md)（`exemplifies`）：该精度卡验证 DeInterleave 的 dst0 必须接收偶索引 lane、dst1 接收奇索引 lane，直接补充 AscDeintlv 输出顺序的可执行 oracle。
- [AscIntlv](asc_intlv.md)（`related`）：AscDeintlv 将交织数据拆成两路，AscIntlv 执行逆向合并；二者可组成数据重排的往返验证链。
- [AscLoadalignDeintlvPostupdate](../reg_load/asc_loadalign_deintlv_postupdate.md)（`related`）：《AscLoadalignDeintlvPostupdate》的任务是“从UB读取连续2×VL长度数据并在Load过程中完成解交织，分别写入两个目的矢量寄存器，调用后自动更新源地址。”。《AscDeintlv》具体提供“将src0和src1中的元素解交织存入dst0和dst1，提供矢量数据解交织和掩码解交织两种模式，仅在AIV上生效。”，它直接用于解交织 Load 的地址 post-update、DeInterleave 结果顺序和等价入口。
- [DeInterleave](../../../basic_api/memory_vector_compute/data_rearrange/de_interleave.md)（`related`）：DeInterleave：DeInterleave 的双输出偶/奇 lane 契约可由另一编程接口和逆操作 Interleave 对照，dst0 偶 lane runbook直接验证最易写反的输出约定，b16卡限定重排位宽风险。 目标卡《AscDeintlv》补充：将src0和src1中的元素解交织存入dst0和dst1，提供矢量数据解交织和掩码解交织两种模式，仅在AIV上生效。
- [AscStorealignIntlv](../reg_store/asc_storealign_intlv.md)（`same_topic`）：AscStorealignIntlv 与《AscDeintlv》的实质衔接是：AscStorealignIntlv 忽略 mask，将两路 Reg lane 交错写 UB；普通 StoreAlign、C++ Store 和 DeIntlv 反向操作及 B16 交错故障直接核对偶奇 lane。
<!-- cannbot:related:end -->
