---
type: API
title: AscUpdateMask
description: 根据元素个数生成mask并自动扣减当前向量处理单元元素数，支持b8、b16、b32位宽模式
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_data_types/asc_update_mask.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscUpdateMask

根据元素个数value生成mask，并自动将value减去当前向量处理单元的元素个数。支持b8、b16、b32三种位宽模式，由于VL=256B，各模式的向量处理单元元素个数为： 图1  asc_update_mask更新流程
函数原型：vector_bool asc_update_mask_b8(uint32_t& value)
返回值：vector_bool，掩码寄存器。
约束：掩码寄存器的数量上限为8，超过上限的掩码寄存器会写入预留的8K UB内存中，可能引起性能劣化。编译器会自动复用生命周期结束的寄存器和预留内存，若两者均可用，优先复用寄存器。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [Reg API int8 DIST_PACK_B32 交错零](../../../../../runbooks/precision/reg_api_int8_dist_pack_b32.md)（`exemplifies`）：《Reg API int8 DIST_PACK_B32 交错零》说明Ascend950 Reg API 用 StoreAlign<int8_t, DIST_PACK_B32> 配 float 粒度 UpdateMask 做 fp32→int8 量化时输出每隔一字节插零；用小 shape debug 脚本打印 y[0] 与参考逐元素对照即可判别。；《AscUpdateMask》说明根据元素个数生成mask并自动扣减当前向量处理单元元素数，支持b8、b16、b32位宽模式。二者在DIST_PACK_B32的存储分布与float到int8 Cast、UpdateMask和StoreAlign/Pack位宽必须一致，否则产生隔字节零上存在可执行的直接衔接。
- [Reg 尾块 masked Add 清零跨块累加器](../../../../../runbooks/precision/reg_tail_mask_zeroing_clears_cross_chunk_accumulator.md)（`exemplifies`）：Reg 尾块 masked Add 清零跨块累加器 与《AscUpdateMask》的实质衔接是：尾块 Mul 用 tail mask 把无效临时 lane 置零，但跨块 Add 必须用 full mask；MaskMergeMode 定义 ZEROING/MERGING，Add/Mul 是实际指令，UpdateMask、Reduce 与跨块状态卡验证该修复不会清空历史 accumulator。
- [UpdateMask 引用参数拒绝 const — 改用可修改左值](../../../../../runbooks/compilation/updatemask_requires_mutable_uint32_lvalue.md)（`exemplifies`）：AscUpdateMask 的 uint32_t 引用参数必须是可修改左值；该构建卡给出 const 实参被拒的编译证据和正确声明方式。
- [fp32 UB 非 VL 拷贝须用带掩码 Reg](../../../../../runbooks/precision/non_vl_fp32_ub_copy_needs_masked_reg_load_store.md)（`exemplifies`）：fp32 UB 非 VL 拷贝须用带掩码 Reg 与《AscUpdateMask》的实质衔接是：非 VL fp32 UB copy 的修复正文直接调用 UpdateMask、Reg Load/Store；所选 API 与 const/mask 故障卡约束同一尾块实现。
- [如何使用掩码操作API](../../../../../guides/programming_guide/library_api/basic_api/quick_reference/how_to_use_mask_api.md)（`explains`）：如何使用掩码操作API 与《AscUpdateMask》的实质衔接是：掩码指南直接覆盖 Move/Create/UpdateMask、Normal/Counter 设置和 Reset；两张故障卡约束模板类型与可修改参数。
- [AscUpdateAddrReg](asc_update_addr_reg.md)（`related`）：地址推进和有效 lane mask 往往需在同一循环同步更新。
- [MaskReg](../../../basic_api/reg_vector_compute/register_data_types/mask_reg.md)（`related`）：MaskReg 与《AscUpdateMask》的实质衔接是：MaskReg 定义有效 lane，直接被 Load/Store、MaskGen 与 MaskReg 计算消费；C 创建/更新接口、merge mode、复用指南和两个编译故障明确其构造约束。
- [AscCreateMask](asc_create_mask.md)（`same_topic`）：AscCreateMask 与《AscUpdateMask》的实质衔接是：AscCreateMask 根据数据位宽和 pat_mode 生成 MaskReg，随后由 UpdateMask/GetMaskSpr、Load/Store 和 MergeMode 消费；两个编译错例限定模板类型与可写引用。
<!-- cannbot:related:end -->
