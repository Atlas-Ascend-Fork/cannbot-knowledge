---
type: API
title: Store
description: 从RegTensor搬出至非32字节对齐的UB地址，支持搬出VL或指定count个数据。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/reg_data_store/Store.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Store

头文件路径为："basic_api/reg_compute/kernel_reg_compute_datacopy_intf.h"。

Reg矢量计算数据搬运接口，支持从RegTensor搬出至非32字节对齐的UB地址dstAddr。连续搬运时，用户需手动更新dstAddr地址。

该接口封装了StoreUnAlign和StoreUnAlignPost。

参数：T: 操作数数据类型。支持的数据类型请参考数据类型。；U: 源操作数的RegTensor类型，例如RegTensor\，由编译器自动推导，用户不需要填写。；dstAddr(输出): 目的操作数，UB起始地址，不需要32字节对齐。；srcReg(输入): 源操作数，类型为RegTensor。；count(输入): 搬运数据量。连续搬运时需手动更新地址：dstAddr = dstAddr + count。

支持数据类型：b8、b16、b32、b64。

约束：-   count不能大于一个RegTensor能存储的数据个数，即count <= 256B / sizeof(T)。
-   接口内部定义了一个UnalignRegForStore，该寄存器数量上限为4，超出后编译器将报错。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [LoadDist 错用 DIST_NORM_B32 导致编译失败](../../../../../runbooks/compilation/reg_load_and_store_use_distinct_dist_enums.md)（`exemplifies`）：LoadDist 错用 DIST_NORM_B32 导致编译失败 与《Store》的实质衔接是：该编译失败来自把 StoreDist::DIST_NORM_B32 套到 Reg LoadAlign；Reg load/LoadAlign 与 Store 总览直接展示 LoadDist 和 StoreDist 是两套枚举及正常 fp32 布局的配对。
- [Reg API int8 DIST_PACK_B32 交错零](../../../../../runbooks/precision/reg_api_int8_dist_pack_b32.md)（`exemplifies`）：《Reg API int8 DIST_PACK_B32 交错零》说明Ascend950 Reg API 用 StoreAlign<int8_t, DIST_PACK_B32> 配 float 粒度 UpdateMask 做 fp32→int8 量化时输出每隔一字节插零；用小 shape debug 脚本打印 y[0] 与参考逐元素对照即可判别。；《Store》说明从RegTensor搬出至非32字节对齐的UB地址，支持搬出VL或指定count个数据。。二者在DIST_PACK_B32的存储分布与float到int8 Cast、UpdateMask和StoreAlign/Pack位宽必须一致，否则产生隔字节零上存在可执行的直接衔接。
- [__ubuf__ 指针传普通形参导致编译失败](../../../../../runbooks/compilation/ubuf_pointer_preserves_address_space.md)（`exemplifies`）：__ubuf__ 指针传普通形参导致编译失败 与《Store》的实质衔接是：__ubuf__ 是指针类型的一部分，helper 形参、Load/Store、ReinterpretCast、地址空间转换与谓词必须保留相同 qualifier，不能隐式退化为普通 T*。
- [fp32 UB 非 VL 拷贝须用带掩码 Reg](../../../../../runbooks/precision/non_vl_fp32_ub_copy_needs_masked_reg_load_store.md)（`exemplifies`）：fp32 UB 非 VL 拷贝须用带掩码 Reg 与《Store》的实质衔接是：非 VL fp32 UB copy 的修复正文直接调用 UpdateMask、Reg Load/Store；所选 API 与 const/mask 故障卡约束同一尾块实现。
- [Reg矢量计算编程（C++ Tensor编程）](../../../../../guides/programming_guide/programming_model/ai_core_simd_programming/cpp_tensor_programming/reg_vector_computation.md)（`explains`）：Reg矢量计算编程（C++ Tensor编程） 与《Store》的实质衔接是：Reg C++ 编程仍遵循 asc_vf_call→__simd_vf__→Load/Compute/Store；C API 对照、性能/边界/merge/精度表和 helper 编译卡直接约束这一调用模型。
- [中级性能优化](../../../../../guides/operator_practice/typical_operator_cases/simd_operator_impl/gelu_reg_vector_operator/intermediate_optimization.md)（`explains`）：中级性能优化 与《Store》的实质衔接是：GELU 中级优化从入门版迁到 Reg/VF 融合并使用 Load/Store/PipeBarrier；所选故障卡直接约束这些调用和 GELU 数值实现。
- [中级性能优化](../../../../../guides/operator_practice/typical_operator_cases/simd_operator_impl/matmul_leakyrelu_fusion_operator/intermediate_optimization.md)（`explains`）：中级性能优化 与《Store》的实质衔接是：Matmul+LeakyRelu 中级优化的正文直接串联 LoadData/Mmad/LeakyRelu、Load/Store、PipeBarrier、SetFlag 和 UnitFlag；所选故障卡约束这条融合流水。
- [AscStore](../../../c_api/reg/reg_store/asc_store.md)（`related`）：AscStore 与《Store》的实质衔接是：AscStore 的 C++ 对应入口共享 GM 写回语义；B16 load-cast-store 与 RoPE store-mask 故障直接约束存储分布和有效 lane。
- [Load](../reg_data_load/load.md)（`related`）：《Load》处理“从UB非32字节对齐的源地址搬运数据至RegTensor，搬运量为VL（256B），内部封装了LoadUnAlignPre和LoadUnAlign接口。”。《Store》明确“从RegTensor搬出至非32字节对齐的UB地址，支持搬出VL或指定count个数据。”，可直接用于核对Reg LoadUnAlign 的 pre/load 地址推进、对齐搬运与相对 Store 合同。
- [AscStoreUnalign](../../../c_api/reg/reg_store/asc_storeunalign.md)（`same_topic`）：C++ Store 封装非对齐 Reg→UB 搬出，C API AscStoreUnalign 是同一机制的对应入口。
- [Reg矢量计算](../reg_vector_compute.md)（`same_topic`）：Reg矢量计算 与《Store》的实质衔接是：Reg 矢量计算必须在 VF 内完成 Load→寄存器计算→Store；C/C++ 编程指南和边界、精度、性能、MergeMode 表直接约束该执行模型。
- [StoreUnAlignContinuous](store_un_align_continuous.md)（`same_topic`）：Store 是连续非对齐搬出的便捷封装，底层语义对应 StoreUnAlign 连续接口。
- [reg数据搬出](../../../c_api/reg/reg_store/reg_store.md)（`same_topic`）：焦点处理Reg 数据搬出中对齐、非对齐与带 mask store 的选择；Store正文说明“从RegTensor搬出至非32字节对齐的UB地址，支持搬出VL或指定count个数据”。候选把总览中的 store 选择落到 Basic Reg 对应接口或真实非 VL/交错 mask 故障。
<!-- cannbot:related:end -->
