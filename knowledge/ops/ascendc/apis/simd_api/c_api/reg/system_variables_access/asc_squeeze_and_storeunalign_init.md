---
type: API
title: AscSqueezeAndStoreunalignInit
description: 对AR特殊寄存器清零，用于配合asc_squeeze_and_storeunalign进行地址自动偏移，首次调用前需初始化。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/system_variables_access/asc_squeeze_and_storeunalign_init.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscSqueezeAndStoreunalignInit

对AR特殊寄存器进行清零操作。AR寄存器用于配合asc_squeeze_and_storeunalign及asc_squeeze_and_storeunalign_finalize使用：当调用asc_squeeze_and_storeunalign后，有效元素的总字节数会被存入AR寄存器用于asc_squeeze_and_storeunalign接口内自动地址偏移。在首次调用asc_squeeze_and_storeunalign之前，需调用本接口将AR寄存器清零。
函数原型：void asc_squeeze_and_storeunalign_init()
约束：在首次调用asc_squeeze_and_storeunalign之前，需调用本接口将AR寄存器清零。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscGetSqueezeStatus](../../sys_var/asc_get_squeeze_status.md)（`related`）：《AscGetSqueezeStatus》说明读取squeeze操作后保存的有效数据长度值。；《AscSqueezeAndStoreunalignInit》说明对AR特殊寄存器清零，用于配合asc_squeeze_and_storeunalign进行地址自动偏移，首次调用前需初始化。。二者在Squeeze有效长度由带status的压缩/搬出操作写入，再由AscGetSqueezeStatus读取；普通Squeeze并不等价上存在可执行的直接衔接。
- [AscSqueezeAndStoreunalignFinalize](../reg_store/asc_squeeze_and_storeunalign_finalize.md)（`related`）：Init 在首次 squeeze-store 前清零 AR 偏移，和 Finalize 分别闭合该状态机的开始与结束。
- [Squeeze](../../../basic_api/reg_vector_compute/compare_and_select/squeeze.md)（`related`）：Squeeze：Squeeze 按 mask 压紧有效 lane，并通过 AR 字节数驱动非对齐 Store；C API、废弃替代链和 StoreUnAlign 正好覆盖同一压紧/搬出契约。 目标卡《AscSqueezeAndStoreunalignInit》补充：对AR特殊寄存器清零，用于配合asc_squeeze_and_storeunalign进行地址自动偏移，首次调用前需初始化。
- [StoreUnAlignMaskReg](../../../basic_api/reg_vector_compute/reg_data_store/store_un_align_mask_reg.md)（`related`）：StoreUnAlignMaskReg 与《AscSqueezeAndStoreunalignInit》的实质衔接是：非对齐 MaskReg Store 依赖 MaskGen/MaskReg 与 UnalignReg 配置，和非对齐 Load 是往返协议；squeeze 初始化卡给出真实配置错误后果。
- [UnalignRegForLoadAndUnalignRegForStore](../../../basic_api/reg_vector_compute/register_data_types/unalign_reg_for_load_unalign_reg_for_store.md)（`related`）：UnalignRegForLoadAndUnalignRegForStore 与《AscSqueezeAndStoreunalignInit》的实质衔接是：非对齐寄存器是 LoadUnAlign Pre→Load 与 Store→Post 协议的临时状态，所选 C/C++ 接口、连续优化和 Init/Postupdate 共同闭合搬入搬出流程。
- [asc_clear_ar_spr](asc_clear_ar_spr_deprecated.md)（`related`）：“asc_clear_ar_spr”定义：该接口已废弃，请使用asc_squeeze_and_storeunalign_init替代。用于对AR特殊寄存器清零，配合asc_squeeze_with_status记录有效元素字节数。；“AscSqueezeAndStoreunalignInit”定义：对AR特殊寄存器清零，用于配合asc_squeeze_and_storeunalign进行地址自动偏移，首次调用前需初始化。。实质衔接：废弃 clear AR SPR 的直接替代是 SqueezeAndStoreUnalignInit；旧 SqueezeWithStatus 解释 AR 有效字节计数的消费链，附录用于查替换。
- [AscSqueeze](../../vector_compute/asc_squeeze.md)（`same_topic`）：AscSqueezeAndStoreunalignInit说明对AR特殊寄存器清零，用于配合asc_squeeze_and_storeunalign进行地址自动偏移，首次调用前需初始化。
- [AscSqueezeAndStoreunalign](../reg_store/asc_squeeze_and_storeunalign.md)（`same_topic`）：AscSqueezeAndStoreunalign 与《AscSqueezeAndStoreunalignInit》的实质衔接是：AscSqueezeAndStoreunalign 必须先 Init 清 AR、可多次压紧并自动推进地址、最后 Finalize；旧 SqueezeWithStatus/GetSqueezeStatus 路径解释迁移前的长度状态。
- [AscSqueezeV2](../compare_and_select/asc_squeeze_deprecated.md)（`same_topic`）：AscSqueezeAndStoreunalignInit说明对AR特殊寄存器清零，用于配合asc_squeeze_and_storeunalign进行地址自动偏移，首次调用前需初始化。
- [AscSqueezeWithStatus](../compare_and_select/asc_squeeze_with_status_deprecated.md)（`same_topic`）：AscSqueezeWithStatus：该废弃接口的功能是按mask压紧并记录有效长度；推荐替代AscSqueezeAndStoreunalign的Init/执行/Finalize链同时完成压紧和非对齐搬出，GetSqueezeStatus/基础Squeeze用于核对长度语义。 目标卡《AscSqueezeAndStoreunalignInit》补充：对AR特殊寄存器清零，用于配合asc_squeeze_and_storeunalign进行地址自动偏移，首次调用前需初始化。
- [asc_storeunalign_post_postupdate](../reg_store/asc_storeunalign_post_postupdate.md)（`same_topic`）：焦点处理非对齐 Reg store 的 post-update 与尾块收尾；AscSqueezeAndStoreunalignInit正文界定“对AR特殊寄存器清零，用于配合asc_squeeze_and_storeunalign进行地址自动偏移，首次调用前需初始化”。候选明确 base store、post/postupdate、squeeze 替代及 finalize/init 的同一地址推进生命周期。
<!-- cannbot:related:end -->
