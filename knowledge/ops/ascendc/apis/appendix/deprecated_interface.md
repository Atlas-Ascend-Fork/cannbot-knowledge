---
type: API
title: 废弃接口
description: 列出Ascend C中已废弃或后续版本将废弃的C API接口，并给出每个接口的推荐替代方案。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/deprecated_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 废弃接口

列出 Ascend C 中已废弃或后续版本将废弃的 C API 接口，并给出每个接口的推荐替代方案。涵盖数据搬运、原子操作、系统变量、Reg 数据搬运、Reg 矢量计算、同步控制与矢量计算等类别。
数据搬运类 asc_set_gm2ub_pad 建议改用 asc_set_copy_pad_val；高维切分搬运形式已废弃，改用 asc_load_l2_cache_mode 与 asc_store_l2_cache_mode 枚举配置 L2 Cache 策略。
原子操作类建议改用 asc_atomic_add、asc_set_atomic_add_int32、asc_set_atomic_max_int32、asc_set_atomic_min_int32 等显式类型版本。
Reg 数据搬运中 asc_loadalign 多模式重载已收窄为 NORM 模式，BRC、UNPACK、DOWN2X 等模式拆分到独立函数；asc_storealign 同样拆分为 NORM、PACK、INTLV 等独立函数。
同步控制类 asc_sync_vec 与矢量计算类 asc_abs_sync 已废弃，统一改用 asc_sync 执行全流水线同步。

<!-- cannbot:related:start -->
## 相关

- [AscSqueezeWithStatus](../simd_api/c_api/reg/compare_and_select/asc_squeeze_with_status_deprecated.md)（`related`）：AscSqueezeWithStatus：该废弃接口的功能是按mask压紧并记录有效长度；推荐替代AscSqueezeAndStoreunalign的Init/执行/Finalize链同时完成压紧和非对齐搬出，GetSqueezeStatus/基础Squeeze用于核对长度语义。 目标卡《废弃接口》补充：列出Ascend C中已废弃或后续版本将废弃的C API接口，并给出每个接口的推荐替代方案。
- [AscStoreAlign](../simd_api/c_api/reg/reg_store/asc_storealign_v1_deprecated.md)（`related`）：《AscStoreAlign》说明已废弃接口。从矢量数据寄存器或掩码寄存器连续对齐搬出到UB，支持NORM、FIRST、PACK、PACKV2、INTLV等多种搬出模式，不传入偏移，由用户自行更新目的地址。；《废弃接口》说明列出Ascend C中已废弃或后续版本将废弃的C API接口，并给出每个接口的推荐替代方案。。二者在废弃StoreAlign与现行StoreAlign、PostUpdate和原子配置的差异决定UB连续搬出地址及写语义上存在可执行的直接衔接。
- [AscStoreAlign](../simd_api/c_api/reg/reg_store/asc_storealign_v4_deprecated.md)（`related`）：《AscStoreAlign》说明已废弃接口。从矢量数据寄存器或掩码寄存器连续对齐搬出到UB，支持NORM、FIRST、PACK、PACKV2等多种搬出模式，通过int32_t传入偏移并由硬件自动Post Update目的地址。；《废弃接口》说明列出Ascend C中已废弃或后续版本将废弃的C API接口，并给出每个接口的推荐替代方案。。二者在废弃StoreAlign重载需迁移到现行或PostUpdate形式；连续、MaskReg、非连续搬出和原子配置决定地址推进与写语义上存在可执行的直接衔接。
- [C API](release_notes/cann_9_1_0.md)（`related`）：C API 与《废弃接口》的实质衔接是：9.1.0 C API 发布说明承接 9.0.0 的初始能力，并以总 Release Notes、废弃表和接口改名表说明新增入口及签名修复在既有代码中的迁移落点。
- [Gemm（废弃）](../simd_api/basic_api/cube_compute/mmad_compute/gemm_deprecated.md)（`related`）：Gemm（废弃）：Gemm 已废弃，附录确认废弃状态，正文明确把 Mmad 作为矩阵乘替代路径，因此两者形成可执行迁移关系。 目标卡《废弃接口》补充：列出Ascend C中已废弃或后续版本将废弃的C API接口，并给出每个接口的推荐替代方案。
- [Release Notes](release_notes/release_notes.md)（`related`）：“废弃接口”定义：列出Ascend C中已废弃或后续版本将废弃的C API接口，并给出每个接口的推荐替代方案。；“Release Notes”定义：汇总Ascend C API各CANN版本的发布说明，包含版本间接口变更和新特性介绍。。实质衔接：三者分别提供 C API 废弃清单、接口替换变更表和发布演进记录，可从旧接口定位推荐替代而不把清单与每个成员全连接。
- [asc_bfloat162e1m2x2 (废弃)](../simd_api/c_api/reg/data_type_convert/asc_bfloat162e1m2x2_deprecated.md)（`related`）：asc_bfloat162e1m2x2 (废弃) 与《废弃接口》的实质衔接是：该废弃转换与 E1M2/E2M1 逆转换、现行 BF16 转换及舍入/饱和规则共享明确的位宽压缩与迁移契约。
- [asc_clear_ar_spr](../simd_api/c_api/reg/system_variables_access/asc_clear_ar_spr_deprecated.md)（`related`）：“asc_clear_ar_spr”定义：该接口已废弃，请使用asc_squeeze_and_storeunalign_init替代。用于对AR特殊寄存器清零，配合asc_squeeze_with_status记录有效元素字节数。；“废弃接口”定义：列出Ascend C中已废弃或后续版本将废弃的C API接口，并给出每个接口的推荐替代方案。。实质衔接：废弃 clear AR SPR 的直接替代是 SqueezeAndStoreUnalignInit；旧 SqueezeWithStatus 解释 AR 有效字节计数的消费链，附录用于查替换。
- [asc_create_iter_reg (废弃)](../simd_api/c_api/reg/reg_data_types/asc_create_iter_reg_deprecated.md)（`related`）：废弃汇总提供替代建议和版本状态。
- [asc_get_ar_spr (废弃)](../simd_api/c_api/sys_var/asc_get_ar_spr_deprecated.md)（`related`）：asc_get_ar_spr (废弃) 与《废弃接口》的实质衔接是：asc_get_ar_spr 已明确由 AscGetSqueezeStatus 替代；clear AR、旧 SqueezeWithStatus/SqueezeV2 和废弃接口表解释该特殊寄存器状态的生产、清理与迁移。
- [asc_pack (废弃)](../simd_api/c_api/reg/data_compress/asc_pack_deprecated.md)（`related`）：废弃接口汇总提供 asc_pack 的版本状态和推荐替代项，是迁移判断的权威入口。
- [接口变更说明（附录）](interface_change_description.md)（`related`）：“废弃接口”定义：列出Ascend C中已废弃或后续版本将废弃的C API接口，并给出每个接口的推荐替代方案。；“接口变更说明（附录）”定义：为了优化API命名，使其更加清晰和易于理解，当前版本相比于CANN8.5.0及前序版本，部分API命名有变更，具体变更情况请参考以下表格：。实质衔接：三者分别提供 C API 废弃清单、接口替换变更表和发布演进记录，可从旧接口定位推荐替代而不把清单与每个成员全连接。
- [AscStoreAlign](../simd_api/c_api/reg/reg_store/asc_storealign_v3_deprecated.md)（`same_topic`）：AscStoreAlign 与《废弃接口》的实质衔接是：该 int32-offset AscStoreAlign 已废弃；当前 AscStorealign/StoreAlignContinuous 承接连续对齐搬出，Postupdate 版本自动推进地址，PACKV2 场景按正文应改用 PackQuarter，废弃表给出迁移边界。
- [Conv2D（废弃）](../simd_api/basic_api/cube_compute/mmad_compute/conv2_d_deprecated.md)（`same_topic`）：废弃接口说明列出Ascend C中已废弃或后续版本将废弃的C API接口，并给出每个接口的推荐替代方案。
- [废弃接口](../simd_api/c_api/deprecated_interface/deprecated_interface.md)（`same_topic`）：两张卡都是 C API 废弃清单：右卡列出 SIMD C API 的局部废弃项，左卡覆盖更完整的跨模块清单并给出推荐替代；迁移旧调用时可在同一废弃契约下补齐替代入口。
<!-- cannbot:related:end -->
