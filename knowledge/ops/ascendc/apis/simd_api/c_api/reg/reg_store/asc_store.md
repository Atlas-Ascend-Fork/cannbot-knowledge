---
type: API
title: AscStore
description: 从矢量数据寄存器搬出数据到UB，不区分是否对齐，对齐场景推荐使用asc_storealign接口。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_store/asc_store.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscStore

reg计算数据搬运接口，适用于从矢量数据寄存器搬出到UB的场景，不区分是否对齐，在追求极致性能时，对齐场景推荐使用asc_storealign接口。
函数原型：void asc_store(__ubuf__  int8_t* dst, vector_int8_t src)
约束：count的取值范围为[1, VL/sizeof(dst)]，VL为矢量长度。超出该范围会导致未定义行为。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [Reg API int8 DIST_PACK_B32 交错零](../../../../../runbooks/precision/reg_api_int8_dist_pack_b32.md)（`exemplifies`）：《Reg API int8 DIST_PACK_B32 交错零》说明Ascend950 Reg API 用 StoreAlign<int8_t, DIST_PACK_B32> 配 float 粒度 UpdateMask 做 fp32→int8 量化时输出每隔一字节插零；用小 shape debug 脚本打印 y[0] 与参考逐元素对照即可判别。；《AscStore》说明从矢量数据寄存器搬出数据到UB，不区分是否对齐，对齐场景推荐使用asc_storealign接口。。二者在DIST_PACK_B32的存储分布与float到int8 Cast、UpdateMask和StoreAlign/Pack位宽必须一致，否则产生隔字节零上存在可执行的直接衔接。
- [RoPE DIST_INTLV_B16 store mask 致零值](../../../../../runbooks/precision/rope_dist_intlv_b16_store_mask.md)（`exemplifies`）：AscStore 与《RoPE DIST_INTLV_B16 store mask 致零值》的实质衔接是：AscStore 的 C++ 对应入口共享 GM 写回语义；B16 load-cast-store 与 RoPE store-mask 故障直接约束存储分布和有效 lane。
- [特定 b16 load-cast-store 组合失真时在 LocalTensor 边界转换](../../../../../runbooks/precision/b16_reg_cast_layout_should_convert_at_localtensor_boundary.md)（`exemplifies`）：AscStore 与《特定 b16 load-cast-store 组合失真时在 LocalTensor 边界转换》的实质衔接是：AscStore 的 C++ 对应入口共享 GM 写回语义；B16 load-cast-store 与 RoPE store-mask 故障直接约束存储分布和有效 lane。
- [AscStoreAlignPostupdate](asc_storealign_postupdate.md)（`related`）：AscStoreAlignPostupdate 与《AscStore》的实质衔接是：StoreAlignPostupdate 在对齐写回后推进地址，pack/first/non-post 变体、Load postupdate、reg 搬出和 AscUpdateAddrReg 拆解数据分布与地址更新。
- [Store](../../../basic_api/reg_vector_compute/reg_data_store/store.md)（`related`）：AscStore 与《Store》的实质衔接是：AscStore 的 C++ 对应入口共享 GM 写回语义；B16 load-cast-store 与 RoPE store-mask 故障直接约束存储分布和有效 lane。
- [AscStorealign](asc_storealign.md)（`same_topic`）：AscStorealign 与《AscStore》的实质衔接是：AscStorealign 在 VF 内把 Reg/MaskReg 对齐写回 UB；postupdate、unalign、C++ StoreAlign 变体和 LoadDist/StoreDist 故障直接约束地址推进、分布枚举与对齐。
- [AscStorealign1stPostupdate](asc_storealign_1st_postupdate.md)（`same_topic`）：AscStorealign1stPostupdate 与《AscStore》的实质衔接是：AscStorealign1stPostupdate 在仅写首元素后更新地址，非 postupdate/通用 Store 与 AscUpdateAddrReg 明确写回粒度和地址推进两部分契约。
- [AscStorealignPackPostupdate](asc_storealign_pack_postupdate.md)（`same_topic`）：AscStorealignPackPostupdate 与《AscStore》的实质衔接是：PackPostupdate 将低半位压缩写回后推进地址，非 postupdate/quarter/general Store、AscUpdateAddrReg 和 Pack/UnPack 接口拆解同一存储协议。
- [Reg矢量计算](../../../basic_api/reg_vector_compute/reg_vector_compute.md)（`same_topic`）：Reg矢量计算 与《AscStore》的实质衔接是：Reg 矢量计算必须在 VF 内完成 Load→寄存器计算→Store；C/C++ 编程指南和边界、精度、性能、MergeMode 表直接约束该执行模型。
<!-- cannbot:related:end -->
