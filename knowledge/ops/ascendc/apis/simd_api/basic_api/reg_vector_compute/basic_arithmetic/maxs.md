---
type: API
title: Maxs
description: 根据mask对源操作数srcReg按元素与标量比较取较大值，将结果写入目的操作数dstReg。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/basic_arithmetic/Maxs.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Maxs

根据mask对源操作数srcReg按元素与标量比较取较大值，将结果写入目的操作数dstReg。

RegTensor寄存器是矢量计算基本单元，RegTensor位宽为VL（Vector Length），长度为256B。b64或complex32类型下，支持通过RegTrait模板参数扩展存储2VL用于复杂计算。

本接口组包含 MaskMergeMode, RegTensor, RegTensor, MaskReg。

本接口属于 Reg 矢量计算基础算术接口，操作 RegTensor 寄存器数据，直接在寄存器级别执行矢量运算。

支持的数据类型为 b8、b16、b32、b64。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：RegTensor寄存器数量上限为32。超出限制上限的寄存器数据会写入预留的8KUB内存中，可能会引起性能劣化。编译器会自动复用生命周期结束的寄存器和预留内存，若寄存器与预留内存均存在可用空间，将优先复用寄存器。；寄存器的生命周期限定于单个VF内部。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Exp 默认 INTRINSIC FTZ 致 subnormal 残留失配](../../../../../runbooks/precision/exp_intrinsic_ftz_subnormal.md)（`exemplifies`）：Maxs 与《Exp 默认 INTRINSIC FTZ 致 subnormal 残留失配》的实质衔接是：Reg Maxs 是 vector-scalar 下限 clamp，Mins/Max/其他层级 Maxs 对照操作数形态；Exp/FTZ/sigmoid 卡直接验证 clamp 阈值改变数值尾部。
- [Maxs 下限 clamp 阻止 exp 自然下溢残留](../../../../../runbooks/precision/maxs_clamp_exp.md)（`exemplifies`）：Maxs 与《Maxs 下限 clamp 阻止 exp 自然下溢残留》的实质衔接是：Reg Maxs 是 vector-scalar 下限 clamp，Mins/Max/其他层级 Maxs 对照操作数形态；Exp/FTZ/sigmoid 卡直接验证 clamp 阈值改变数值尾部。
- [arch35 sigmoid 大负 z 下 exp 溢出 inf 致 sig=0](../../../../../runbooks/precision/arch35_sigmoid_z_exp_inf_sig_0.md)（`exemplifies`）：Maxs 与《arch35 sigmoid 大负 z 下 exp 溢出 inf 致 sig=0》的实质衔接是：Reg Maxs 是 vector-scalar 下限 clamp，Mins/Max/其他层级 Maxs 对照操作数形态；Exp/FTZ/sigmoid 卡直接验证 clamp 阈值改变数值尾部。
- [exp 下界 clamp -50 破坏 sigmoid 大负数下溢](../../../../../runbooks/precision/exp_clamp_50_sigmoid.md)（`exemplifies`）：Maxs 与《exp 下界 clamp -50 破坏 sigmoid 大负数下溢》的实质衔接是：Reg Maxs 是 vector-scalar 下限 clamp，Mins/Max/其他层级 Maxs 对照操作数形态；Exp/FTZ/sigmoid 卡直接验证 clamp 阈值改变数值尾部。
- [Maxs（灵活标量位置）](../../memory_vector_compute/basic_arithmetic/maxs_flexible_scalar.md)（`related`）：Maxs 与《Maxs（灵活标量位置）》的实质衔接是：Reg Maxs 是 vector-scalar 下限 clamp，Mins/Max/其他层级 Maxs 对照操作数形态；Exp/FTZ/sigmoid 卡直接验证 clamp 阈值改变数值尾部。
- [Mins](mins.md)（`related`）：Mins 与 Maxs 都是 RegTensor 对标量的逐元素边界运算，可组合实现上下界截断。
- [Max](max.md)（`same_topic`）：Maxs 与《Max》的实质衔接是：Reg Maxs 是 vector-scalar 下限 clamp，Mins/Max/其他层级 Maxs 对照操作数形态；Exp/FTZ/sigmoid 卡直接验证 clamp 阈值改变数值尾部。
- [Maxs](../../memory_vector_compute/basic_arithmetic/maxs.md)（`same_topic`）：Maxs 与《Maxs》的实质衔接是：Maxs 是 tensor 与标量逐元素取大值；Reg/灵活标量入口保持同一契约，Mins/Relu/LeakyRelu 以及 exp clamp 案例说明它在分段和限幅公式中的实际组合。
<!-- cannbot:related:end -->
