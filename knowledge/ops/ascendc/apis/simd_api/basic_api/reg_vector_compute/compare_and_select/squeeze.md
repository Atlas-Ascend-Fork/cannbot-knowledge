---
type: API
title: Squeeze
description: 将srcReg中被mask选择的有效元素依次复制到dstReg中连续排列，剩余位置置0。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/compare_and_select/Squeeze.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# Squeeze

头文件路径为："basic_api/reg_compute/kernel_reg_compute_gather_mask_intf.h"。

将传入的srcReg中被mask选择的有效元素依次复制到dstReg中，有效元素在dstReg中从低到高连续排列，剩余位置元素置为0，如图1所示。

特别地，当模板参数store取值为GatherMaskMode::STORE_REG时，Squeeze会将有效元素的总字节数存入AR特殊寄存器。此时配合使用连续非对齐搬出的场景3接口（无需显式传入偏移量），StoreUnAlign会自动从AR寄存器读取有效字节数作为地址偏移，参考调用示例。

参数：T: 目的操作数和源操作数的数据类型。；store: GatherMaskMode选择是否将有效元素的总字节数存入AR寄存器，AR寄存器描述参考表 模板参数说明。 • NO_STORE_REG，有效元素的总字节数不存入AR寄存器； • STORE_REG，有效元素的总字节数存入AR寄存器。；U: 目的操作数和源操作数的RegTensor类型，例如RegTensor ，由编译器自动推导，用户不需要填写。；dstReg(输出): 目的操作数。 类型为RegTensor。；srcReg(输入): 源操作数。 类型为RegTensor。；mask(输入): mask用于控制每次迭代内参与计算的元素。

支持数据类型：int8_t、uint8_t、int16_t、uint16_t、half、int32_t、uint32_t、float。

约束：- 当模板参数store取值为GatherMaskMode::STORE_REG时，由于硬件约束，StoreUnAlign指令和Squeeze指令必须交替使用，例如
- 当store取值为GatherMaskMode::NO_STORE_REG时，不涉及AR寄存器，Squeeze和StoreUnAlign不强制交替。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscGetSqueezeStatus](../../../c_api/sys_var/asc_get_squeeze_status.md)（`related`）：《AscGetSqueezeStatus》说明读取squeeze操作后保存的有效数据长度值。；《Squeeze》说明将srcReg中被mask选择的有效元素依次复制到dstReg中连续排列，剩余位置置0。。二者在Squeeze有效长度由带status的压缩/搬出操作写入，再由AscGetSqueezeStatus读取；普通Squeeze并不等价上存在可执行的直接衔接。
- [AscSqueezeAndStoreunalignInit](../../../c_api/reg/system_variables_access/asc_squeeze_and_storeunalign_init.md)（`related`）：Squeeze：Squeeze 按 mask 压紧有效 lane，并通过 AR 字节数驱动非对齐 Store；C API、废弃替代链和 StoreUnAlign 正好覆盖同一压紧/搬出契约。 目标卡《AscSqueezeAndStoreunalignInit》补充：对AR特殊寄存器清零，用于配合asc_squeeze_and_storeunalign进行地址自动偏移，首次调用前需初始化。
- [SelectFlexibleScalar](../../memory_vector_compute/compare_and_select/select_flexible_scalar.md)（`related`）：Squeeze：Squeeze 按 mask 压紧有效 lane，并通过 AR 字节数驱动非对齐 Store；C API、废弃替代链和 StoreUnAlign 正好覆盖同一压紧/搬出契约。 目标卡《SelectFlexibleScalar》补充：提供灵活标量位置的Select接口，支持标量在前和标量在后两种场景，标量可配置为LocalTensor单点元素。
- [StoreUnAlignContinuous](../reg_data_store/store_un_align_continuous.md)（`related`）：Squeeze：Squeeze 按 mask 压紧有效 lane，并通过 AR 字节数驱动非对齐 Store；C API、废弃替代链和 StoreUnAlign 正好覆盖同一压紧/搬出契约。 目标卡《StoreUnAlignContinuous》补充：将数据从RegTensor连续搬运至非对齐Unified Buffer，利用非对齐寄存器暂存跨边界数据。
- [AscSqueeze](../../../c_api/reg/compare_and_select/asc_squeeze.md)（`same_topic`）：Squeeze：Squeeze 按 mask 压紧有效 lane，并通过 AR 字节数驱动非对齐 Store；C API、废弃替代链和 StoreUnAlign 正好覆盖同一压紧/搬出契约。 目标卡《AscSqueeze》补充：将src中被mask选择的有效元素依次复制到dst中，有效元素在dst中从低到高连续排列，剩余位置元素置为0。本接口不会将有效数据大小保存至AR寄存器。
- [AscSqueezeV2](../../../c_api/reg/compare_and_select/asc_squeeze_deprecated.md)（`same_topic`）：Squeeze：Squeeze 按 mask 压紧有效 lane，并通过 AR 字节数驱动非对齐 Store；C API、废弃替代链和 StoreUnAlign 正好覆盖同一压紧/搬出契约。 目标卡《AscSqueezeV2》补充：已废弃接口，请使用asc_squeeze_and_storeunalign。将src中被mask选择的有效元素依次复制到dst并连续排列，搭配asc_storeunalign_postupdate可将有效数据大小保存至AR寄存器。
- [AscSqueezeWithStatus](../../../c_api/reg/compare_and_select/asc_squeeze_with_status_deprecated.md)（`same_topic`）：Squeeze：Squeeze 按 mask 压紧有效 lane，并通过 AR 字节数驱动非对齐 Store；C API、废弃替代链和 StoreUnAlign 正好覆盖同一压紧/搬出契约。 目标卡《AscSqueezeWithStatus》补充：已废弃接口，请使用asc_squeeze_and_storeunalign。将src中被mask选择的有效元素依次复制到dst并连续排列，会将有效数据大小保存至AR寄存器供搬出时使用。
- [Squeeze](../../data_structure_tensor_api/layout_structure/squeeze.md)（`same_topic`）：Squeeze：Squeeze 按 mask 压紧有效 lane，并通过 AR 字节数驱动非对齐 Store；C API、废弃替代链和 StoreUnAlign 正好覆盖同一压紧/搬出契约。 目标卡《Squeeze》补充：删除Layout的Shape中大小为1的指定维度并同步删除Stride中的对应维度，支持Tensor输入。
- [系统变量访问](../system_variable_access/system_variable_access.md)（`same_topic`）：系统变量访问 与《Squeeze》的实质衔接是：本页的实际能力是 ClearSpr 清零 AR 特殊寄存器；GetSpr 读取同一 AR，而 Reg Squeeze 会把有效元素字节数写入 AR，因此它们形成明确的生产、读取和复位契约。
<!-- cannbot:related:end -->
