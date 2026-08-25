---
type: API
title: Load
description: 从UB非32字节对齐的源地址搬运数据至RegTensor，搬运量为VL（256B），内部封装了LoadUnAlignPre和LoadUnAlign接口。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/reg_data_load/Load.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Load

头文件路径为："basic_api/reg_compute/kernel_reg_compute_datacopy_intf.h"。

Reg矢量计算数据搬运接口，支持从UB非32字节对齐的源地址srcAddr搬运至RegTensor，搬运量为VL（256B）。连续搬运时，用户需手动更新srcAddr地址。

该接口封装了LoadUnAlignPre和LoadUnAlign。

参数：T: 操作数数据类型。支持的数据类型请参考数据类型。；U: 目的操作数的RegTensor类型，例如RegTensor\，由编译器自动推导，用户不需要手动填写。；dstReg(输出): 目的操作数，类型为RegTensor。；srcAddr(输入): 源操作数，UB起始地址，不需要32字节对齐。

支持数据类型：b8、b16、b32、b64。

约束：- dstReg不支持RegTraitNumTwo。
- 接口内部定义了一个UnalignRegForLoad，该寄存器数量上限为4，超出后编译器将报错。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [LoadDist 错用 DIST_NORM_B32 导致编译失败](../../../../../runbooks/compilation/reg_load_and_store_use_distinct_dist_enums.md)（`exemplifies`）：LoadDist 错用 DIST_NORM_B32 导致编译失败 与《Load》的实质衔接是：该编译失败来自把 StoreDist::DIST_NORM_B32 套到 Reg LoadAlign；Reg load/LoadAlign 与 Store 总览直接展示 LoadDist 和 StoreDist 是两套枚举及正常 fp32 布局的配对。
- [__ubuf__ 指针传普通形参导致编译失败](../../../../../runbooks/compilation/ubuf_pointer_preserves_address_space.md)（`exemplifies`）：__ubuf__ 指针传普通形参导致编译失败 与《Load》的实质衔接是：__ubuf__ 是指针类型的一部分，helper 形参、Load/Store、ReinterpretCast、地址空间转换与谓词必须保留相同 qualifier，不能隐式退化为普通 T*。
- [fp32 UB 非 VL 拷贝须用带掩码 Reg](../../../../../runbooks/precision/non_vl_fp32_ub_copy_needs_masked_reg_load_store.md)（`exemplifies`）：fp32 UB 非 VL 拷贝须用带掩码 Reg 与《Load》的实质衔接是：非 VL fp32 UB copy 的修复正文直接调用 UpdateMask、Reg Load/Store；所选 API 与 const/mask 故障卡约束同一尾块实现。
- [Reg矢量计算编程（C++ Tensor编程）](../../../../../guides/programming_guide/programming_model/ai_core_simd_programming/cpp_tensor_programming/reg_vector_computation.md)（`explains`）：Reg矢量计算编程（C++ Tensor编程） 与《Load》的实质衔接是：Reg C++ 编程仍遵循 asc_vf_call→__simd_vf__→Load/Compute/Store；C API 对照、性能/边界/merge/精度表和 helper 编译卡直接约束这一调用模型。
- [中级性能优化](../../../../../guides/operator_practice/typical_operator_cases/simd_operator_impl/gelu_reg_vector_operator/intermediate_optimization.md)（`explains`）：中级性能优化 与《Load》的实质衔接是：GELU 中级优化从入门版迁到 Reg/VF 融合并使用 Load/Store/PipeBarrier；所选故障卡直接约束这些调用和 GELU 数值实现。
- [中级性能优化](../../../../../guides/operator_practice/typical_operator_cases/simd_operator_impl/matmul_leakyrelu_fusion_operator/intermediate_optimization.md)（`explains`）：中级性能优化 与《Load》的实质衔接是：Matmul+LeakyRelu 中级优化的正文直接串联 LoadData/Mmad/LeakyRelu、Load/Store、PipeBarrier、SetFlag 和 UnitFlag；所选故障卡约束这条融合流水。
- [连续非对齐场景优化](../../../../../guides/operator_practice/simd_operator_optimization/vector_compute/vf_optimization/continuous_unaligned_optimization.md)（`explains`）：《Load》处理“从UB非32字节对齐的源地址搬运数据至RegTensor，搬运量为VL（256B），内部封装了LoadUnAlignPre和LoadUnAlign接口。”。《连续非对齐场景优化》明确“连续非对齐搬运场景的性能优化建议与接口介绍。”，可直接用于核对Reg LoadUnAlign 的 pre/load 地址推进、对齐搬运与相对 Store 合同。
- [Store](../reg_data_store/store.md)（`related`）：《Load》处理“从UB非32字节对齐的源地址搬运数据至RegTensor，搬运量为VL（256B），内部封装了LoadUnAlignPre和LoadUnAlign接口。”。《Store》明确“从RegTensor搬出至非32字节对齐的UB地址，支持搬出VL或指定count个数据。”，可直接用于核对Reg LoadUnAlign 的 pre/load 地址推进、对齐搬运与相对 Store 合同。
- [AscLoad](../../../c_api/reg/reg_load/asc_load.md)（`same_topic`）：《Load》处理“从UB非32字节对齐的源地址搬运数据至RegTensor，搬运量为VL（256B），内部封装了LoadUnAlignPre和LoadUnAlign接口。”。《AscLoad》明确“从UB非32字节对齐的源地址搬运VL大小的数据到矢量数据寄存器。”，可直接用于核对Reg LoadUnAlign 的 pre/load 地址推进、对齐搬运与相对 Store 合同。
- [AscLoadunalign](../../../c_api/reg/reg_load/asc_loadunalign.md)（`same_topic`）：《Load》处理“从UB非32字节对齐的源地址搬运数据至RegTensor，搬运量为VL（256B），内部封装了LoadUnAlignPre和LoadUnAlign接口。”。《AscLoadunalign》明确“从UB非32B对齐的起始地址连续搬入数据到矢量数据寄存器，需用户手动更新源地址。”，可直接用于核对Reg LoadUnAlign 的 pre/load 地址推进、对齐搬运与相对 Store 合同。
- [AscLoadunalignPre](../../../c_api/reg/reg_load/asc_loadunalign_pre.md)（`same_topic`）：《Load》处理“从UB非32字节对齐的源地址搬运数据至RegTensor，搬运量为VL（256B），内部封装了LoadUnAlignPre和LoadUnAlign接口。”。《AscLoadunalignPre》明确“用于非对齐数据搬入前的初始化，需配合asc_loadunalign或asc_loadunalign_postupdate使用。”，可直接用于核对Reg LoadUnAlign 的 pre/load 地址推进、对齐搬运与相对 Store 合同。
- [LoadUnAlign](load_un_align_continuous.md)（`same_topic`）：《Load》处理“从UB非32字节对齐的源地址搬运数据至RegTensor，搬运量为VL（256B），内部封装了LoadUnAlignPre和LoadUnAlign接口。”。《LoadUnAlign》明确“将数据从非32字节对齐的UB地址连续搬运至RegTensor，利用UnalignRegForLoad暂存跨对齐边界数据，需配合LoadUnAlignPre使用。移”，可直接用于核对Reg LoadUnAlign 的 pre/load 地址推进、对齐搬运与相对 Store 合同。
- [Reg矢量计算](../reg_vector_compute.md)（`same_topic`）：Reg矢量计算 与《Load》的实质衔接是：Reg 矢量计算必须在 VF 内完成 Load→寄存器计算→Store；C/C++ 编程指南和边界、精度、性能、MergeMode 表直接约束该执行模型。
<!-- cannbot:related:end -->
