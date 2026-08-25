---
type: API
title: AscSqueezeWithStatus
description: 已废弃接口，请使用asc_squeeze_and_storeunalign。将src中被mask选择的有效元素依次复制到dst并连续排列，会将有效数据大小保存至AR寄存器供搬出时使用。
tags: [task.lookup, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/compare_and_select/asc_squeeze_with_status_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscSqueezeWithStatus

该接口已废弃，请使用asc_squeeze_and_storeunalign实现筛选并连续搬出有效元素的功能。

将src中被mask选择的有效元素依次复制到dst，有效元素在dst上连续排列。dst中剩余位置元素置为0。

本接口会将有效数据大小保存至AR寄存器，搬出时配合asc_storeunalign_postupdate接口使用该值作为存储偏移量。AR寄存器中的数值可以通过asc_get_squeeze_status接口获取。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：bfloat16_t、float、fp8_e4m3fn_t、fp8_e5m2_t、fp8_e8m0_t、half、hifloat8_t、int16_t、int32_t、int8_t、uint16_t、uint32_t、uint8_t。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [asc_clear_ar_spr](../system_variables_access/asc_clear_ar_spr_deprecated.md)（`related`）：“asc_clear_ar_spr”定义：该接口已废弃，请使用asc_squeeze_and_storeunalign_init替代。用于对AR特殊寄存器清零，配合asc_squeeze_with_status记录有效元素字节数。；“AscSqueezeWithStatus”定义：已废弃接口，请使用asc_squeeze_and_storeunalign。将src中被mask选择的有效元素依次复制到dst并连续排列，会将有效数据大小保存至AR寄存器供搬出时使用。。实质衔接：废弃 clear AR SPR 的直接替代是 SqueezeAndStoreUnalignInit；旧 SqueezeWithStatus 解释 AR 有效字节计数的消费链，附录用于查替换。
- [废弃接口](../../../../appendix/deprecated_interface.md)（`related`）：AscSqueezeWithStatus：该废弃接口的功能是按mask压紧并记录有效长度；推荐替代AscSqueezeAndStoreunalign的Init/执行/Finalize链同时完成压紧和非对齐搬出，GetSqueezeStatus/基础Squeeze用于核对长度语义。 目标卡《废弃接口》补充：列出Ascend C中已废弃或后续版本将废弃的C API接口，并给出每个接口的推荐替代方案。
- [AscGetSqueezeStatus](../../sys_var/asc_get_squeeze_status.md)（`same_topic`）：《AscGetSqueezeStatus》说明读取squeeze操作后保存的有效数据长度值。；《AscSqueezeWithStatus》说明已废弃接口，请使用asc_squeeze_and_storeunalign。将src中被mask选择的有效元素依次复制到dst并连续排列，会将有效数据大小保存至AR寄存器供搬出时使用。。二者在Squeeze有效长度由带status的压缩/搬出操作写入，再由AscGetSqueezeStatus读取；普通Squeeze并不等价上存在可执行的直接衔接。
- [AscSqueeze](asc_squeeze.md)（`same_topic`）：AscSqueezeWithStatus：该废弃接口的功能是按mask压紧并记录有效长度；推荐替代AscSqueezeAndStoreunalign的Init/执行/Finalize链同时完成压紧和非对齐搬出，GetSqueezeStatus/基础Squeeze用于核对长度语义。 目标卡《AscSqueeze》补充：将src中被mask选择的有效元素依次复制到dst中，有效元素在dst中从低到高连续排列，剩余位置元素置为0。本接口不会将有效数据大小保存至AR寄存器。
- [AscSqueeze](../../vector_compute/asc_squeeze.md)（`same_topic`）：AscSqueezeWithStatus说明已废弃接口，请使用asc_squeeze_and_storeunalign。将src中被mask选择的有效元素依次复制到dst并连续排列，会将有效数据大小保存至AR寄存器供搬出时使用。
- [AscSqueezeAndStoreunalign](../reg_store/asc_squeeze_and_storeunalign.md)（`same_topic`）：AscSqueezeWithStatus：该废弃接口的功能是按mask压紧并记录有效长度；推荐替代AscSqueezeAndStoreunalign的Init/执行/Finalize链同时完成压紧和非对齐搬出，GetSqueezeStatus/基础Squeeze用于核对长度语义。 目标卡《AscSqueezeAndStoreunalign》补充：从矢量数据寄存器中筛选有效元素后按非32B对齐地址连续搬出到UB，通过AR寄存器累加偏移实现自动地址管理。
- [AscSqueezeAndStoreunalignFinalize](../reg_store/asc_squeeze_and_storeunalign_finalize.md)（`same_topic`）：AscSqueezeWithStatus：该废弃接口的功能是按mask压紧并记录有效长度；推荐替代AscSqueezeAndStoreunalign的Init/执行/Finalize链同时完成压紧和非对齐搬出，GetSqueezeStatus/基础Squeeze用于核对长度语义。 目标卡《AscSqueezeAndStoreunalignFinalize》补充：配合asc_squeeze_and_storeunalign接口，将暂存于非对齐寄存器的尾块数据搬出到UB，完成非对齐搬出收尾。
- [AscSqueezeAndStoreunalignInit](../system_variables_access/asc_squeeze_and_storeunalign_init.md)（`same_topic`）：AscSqueezeWithStatus：该废弃接口的功能是按mask压紧并记录有效长度；推荐替代AscSqueezeAndStoreunalign的Init/执行/Finalize链同时完成压紧和非对齐搬出，GetSqueezeStatus/基础Squeeze用于核对长度语义。 目标卡《AscSqueezeAndStoreunalignInit》补充：对AR特殊寄存器清零，用于配合asc_squeeze_and_storeunalign进行地址自动偏移，首次调用前需初始化。
- [AscSqueezeV2](asc_squeeze_deprecated.md)（`same_topic`）：AscSqueezeWithStatus：该废弃接口的功能是按mask压紧并记录有效长度；推荐替代AscSqueezeAndStoreunalign的Init/执行/Finalize链同时完成压紧和非对齐搬出，GetSqueezeStatus/基础Squeeze用于核对长度语义。 目标卡《AscSqueezeV2》补充：已废弃接口，请使用asc_squeeze_and_storeunalign。将src中被mask选择的有效元素依次复制到dst并连续排列，搭配asc_storeunalign_postupdate可将有效数据大小保存至AR寄存器。
- [Squeeze](../../../basic_api/reg_vector_compute/compare_and_select/squeeze.md)（`same_topic`）：Squeeze：Squeeze 按 mask 压紧有效 lane，并通过 AR 字节数驱动非对齐 Store；C API、废弃替代链和 StoreUnAlign 正好覆盖同一压紧/搬出契约。 目标卡《AscSqueezeWithStatus》补充：已废弃接口，请使用asc_squeeze_and_storeunalign。将src中被mask选择的有效元素依次复制到dst并连续排列，会将有效数据大小保存至AR寄存器供搬出时使用。
- [asc_get_ar_spr (废弃)](../../sys_var/asc_get_ar_spr_deprecated.md)（`same_topic`）：asc_get_ar_spr (废弃) 与《AscSqueezeWithStatus》的实质衔接是：asc_get_ar_spr 已明确由 AscGetSqueezeStatus 替代；clear AR、旧 SqueezeWithStatus/SqueezeV2 和废弃接口表解释该特殊寄存器状态的生产、清理与迁移。
<!-- cannbot:related:end -->
