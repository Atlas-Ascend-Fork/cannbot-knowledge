---
type: API
title: AddrReg
description: 用于Reg矢量计算管理地址偏移量的专用寄存器，支持1至4层循环轴索引与步长绑定，逐层累加地址偏移。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/register_data_types/AddrReg.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AddrReg

头文件引用路径为 "basic_api/reg_compute/kernel_reg_compute_addrreg_intf.h"。

AddrReg是用于Reg矢量计算接口管理地址偏移量的专用寄存器。在循环外定义后，在循环内调用模板函数CreateAddrReg接口赋值并绑定每层循环轴索引（index）与步长（stride），能够在多维循环中逐层累加地址偏移。CreateAddrReg接口支持绑定1-4层for循环，返回的地址偏移由index*stride的决定，在循环中，index每次递增1，AddrReg的偏移量就自动增加对应的stride，具体的偏移量满足如下伪代码所示
AddrReg应该通过CreateAddrReg API初始化，然后在循环中使用AddrReg存储地址偏移量。AddrReg在每层循环中根据所设置的stride进行自增。

参数：T: 模板参数，支持的数据类型为b8、b16、b32、b64。；index0: 计算偏移量时作为最外层循环轴。；index1: 计算偏移量时作为第二层循环轴。；index2: 计算偏移量时作为第三层循环轴。；index3: 计算偏移量时作为第四层循环轴。；stride0: 每次循环，最外层循环轴对应的地址偏移量，单位为element。；stride1: 每次循环，第二层循环轴对应的地址偏移量，单位为element。；stride2: 每次循环，第三层循环轴对应的地址偏移量，单位为element。

约束：- AddrReg 为地址偏移量寄存器，仅支持部分搬运指令使用，请根据Reg数据搬运接口函数原型选择，除了通过AddrReg设置地址偏移，支持用户自行累加地址或通过PostUpdate模式进行地址自增，完整特性见连续对齐搬入关键特性。通过AddrReg地址偏移进行搬运时，需要满足对应搬运指令的地址对齐约束。
- AddrReg 数量上限为8。
- 由于硬件循环(HardwareLoop)限制，AddrReg最多支持4层循环轴。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [指令双发优化](../../../../../guides/operator_practice/simd_operator_optimization/vector_compute/vf_optimization/dual_issue_optimization.md)（`explains`）：指令双发优化 与《AddrReg》的实质衔接是：双发优化依赖 VF 融合、循环/掩码复用、原子与地址寄存器编排；这些卡分别提供发射冲突定位和可执行改写。
- [LoadAlign](../reg_data_load/load_align_mask_reg.md)（`related`）：选择 AddrReg 重载时必须先创建并配置多维地址偏移，LoadAlign 再按该偏移访问 UB；AddrReg 是该寻址模式的前置对象。
- [asc_create_iter_reg (废弃)](../../../c_api/reg/reg_data_types/asc_create_iter_reg_deprecated.md)（`related`）：废弃的 CreateIterReg 说明初始化式迭代寄存器已由 AscUpdateAddrReg 取代，有助于迁移旧 AddrReg 循环代码。
- [AscUpdateAddrReg](../../../c_api/reg/reg_data_types/asc_update_addr_reg.md)（`same_topic`）：AddrReg 类型是 UpdateAddrReg 更新的核心对象。
- [RegTensor](reg_tensor.md)（`same_topic`）：RegTensor 与《AddrReg》的实质衔接是：RegTensor 是 256B VL 的 VF 内基本单元；MaskReg/AddrReg/非对齐状态、内置类型和跨 VF/错误类型案例直接限定 lane、寿命和模板参数。
- [UnalignRegForLoadAndUnalignRegForStore](unalign_reg_for_load_unalign_reg_for_store.md)（`same_topic`）：UnalignRegForLoadAndUnalignRegForStore 与《AddrReg》的实质衔接是：非对齐寄存器是 LoadUnAlign Pre→Load 与 Store→Post 协议的临时状态，所选 C/C++ 接口、连续优化和 Init/Postupdate 共同闭合搬入搬出流程。
<!-- cannbot:related:end -->
