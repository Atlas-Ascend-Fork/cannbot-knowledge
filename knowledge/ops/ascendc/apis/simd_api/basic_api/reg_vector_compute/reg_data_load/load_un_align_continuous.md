---
type: API
title: LoadUnAlign
description: 将数据从非32字节对齐的UB地址连续搬运至RegTensor，利用UnalignRegForLoad暂存跨对齐边界数据，需配合LoadUnAlignPre使用。移
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/reg_data_load/LoadUnAlign_continuous.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# LoadUnAlign

头文件路径为："basic_api/reg_compute/kernel_reg_compute_datacopy_intf.h"。

为提升对不规则内存地址的处理能力，Reg矢量计算支持在数据搬运过程中对非32字节对齐的地址进行访问，降低非对齐访问带来的性能开销。LoadUnAlign能够实现数据从非对齐的Unified Buffer（UB）连续搬运至RegTensor，利用非对齐寄存器UnalignRegForLoad作为临时缓存区，暂存跨对齐边界的数据，从而实现高效的连续非对齐数据传输。

非对齐搬运有三类接口：普通搬运接口、PostUpdate扩展搬运接口、使用AddrReg寄存器存储偏移量接口。

RegTensor的模板参数regTrait支持RegTraitNumOne及RegTraitNumTwo。
非对齐搬入原理

参数：T: 源操作数的数据类型。支持的数据类型请参考数据类型。；postMode: 用于控制是否使能UB地址会自动更新功能（post update），PostLiteral类型。具体参数说明请参考PostLiteral。；U: 目的操作数的RegTensor类型。例如RegTensor\，由编译器自动推导，用户不需要手动填写。；dstReg(输出): 目的操作数，类型为RegTensor。；ureg(输入/输出): 非对齐寄存器，UnalignRegForLoad类型，用于存储非32字节的数据，寄存器大小为32字节。；srcAddr(输入/输出): 源操作数，UB起始地址，不需要32字节对齐。；postUpdateStride(输入): 地址更新步长，uint32_t类型，单位：元素个数。根据postMode的取值有两种情况： &bull; POST_MODE_NORMAL：不支持。 &b。

支持数据类型：b8、b16、b32、b64。

约束：- LoadUnAlignPre与LoadUnAlign接口需要组合使用。
- PostUpdate扩展搬运接口只支持POST_MODE_UPDATE模式。
- 当RegTensor模板参数RegTrait为RegTraitNumOne和RegTraitNumTwo时，支持情况

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [ACLNN 561000 非连续张量需 AutoContiguous](../../../../../runbooks/compilation/aclnn_561000_autocontiguous.md)（`exemplifies`）：ACLNN 561000 非连续张量需 AutoContiguous 与《LoadUnAlign》的实质衔接是：561000 来自 OpParamDef 未声明连续性策略；AutoContiguous/IgnoreContiguous、Input/OpDef 和非连续 Load/Store/Slice/Transpose 卡共同决定转换还是保留 strides。
- [连续非对齐场景优化](../../../../../guides/operator_practice/simd_operator_optimization/vector_compute/vf_optimization/continuous_unaligned_optimization.md)（`explains`）：连续非对齐场景优化 的核心契约是“连续非对齐搬运场景的性能优化建议与接口介绍”；LoadUnAlign 补充“将数据从非32字节对齐的UB地址连续搬运至RegTensor，利用UnalignRegForLoad暂存跨对齐边界数据，需配合LoadUnAlignPre使用。移”。
- [AscLoadunalignPre](../../../c_api/reg/reg_load/asc_loadunalign_pre.md)（`related`）：AscLoadunalignPre 与《LoadUnAlign》的实质衔接是：AscLoadunalignPre 需与 unalign/postupdate 形态及 UnalignReg 状态配套；基础 API 和优化指南给出相同非对齐搬入约束。
- [PostLiteral](../aux_data_types/post_literal.md)（`related`）：LoadUnAlign 不支持 NORMAL，必须使用 PostLiteral::POST_MODE_UPDATE 自动推进 UB 地址。
- [Reg数据搬入](reg_data_load.md)（`related`）：集合页按起点非 32B 对齐选择 LoadUnAlign，并区别于连续对齐 LoadAlign。
- [StoreUnAlignContinuous](../reg_data_store/store_un_align_continuous.md)（`related`）：LoadUnAlign 是非对齐连续 Store 的读侧对偶，二者组合可处理 UB 非对齐的寄存器往返。
- [AscLoadunalign](../../../c_api/reg/reg_load/asc_loadunalign.md)（`same_topic`）：两者都是连续非对齐 Reg 搬入，分别为 C++ RegTensor 与 C API 形式，且共享预处理状态的使用约束。
- [Load](load.md)（`same_topic`）：《Load》处理“从UB非32字节对齐的源地址搬运数据至RegTensor，搬运量为VL（256B），内部封装了LoadUnAlignPre和LoadUnAlign接口。”。《LoadUnAlign》明确“将数据从非32字节对齐的UB地址连续搬运至RegTensor，利用UnalignRegForLoad暂存跨对齐边界数据，需配合LoadUnAlignPre使用。移”，可直接用于核对Reg LoadUnAlign 的 pre/load 地址推进、对齐搬运与相对 Store 合同。
- [StoreUnAlignMaskReg](../reg_data_store/store_un_align_mask_reg.md)（`same_topic`）：StoreUnAlignMaskReg 与《LoadUnAlign》的实质衔接是：非对齐 MaskReg Store 依赖 MaskGen/MaskReg 与 UnalignReg 配置，和非对齐 Load 是往返协议；squeeze 初始化卡给出真实配置错误后果。
- [UnalignRegForLoadAndUnalignRegForStore](../register_data_types/unalign_reg_for_load_unalign_reg_for_store.md)（`same_topic`）：UnalignRegForLoadAndUnalignRegForStore 与《LoadUnAlign》的实质衔接是：非对齐寄存器是 LoadUnAlign Pre→Load 与 Store→Post 协议的临时状态，所选 C/C++ 接口、连续优化和 Init/Postupdate 共同闭合搬入搬出流程。
<!-- cannbot:related:end -->
