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

- [LoadAlign](../reg_data_load/load_align_mask_reg.md)（`related`）：“使用AddrReg寄存器存储偏移量场景：在每次迭代中，需要先调用CreateAddrReg手动设定地址偏移量，再调用搬运指令。”规定 MaskReg LoadAlign 的 AddrReg 重载每轮必须先设偏移；“AddrReg应该通过CreateAddrReg API初始化，然后在循环中使用AddrReg存储地址偏移量。AddrReg在每层循环中根据所设置的stride进行自增。”给出 CreateAddrReg 初始化和按 stride 自增的寄存器语义。二者共同决定多维循环中的实际 UB 地址。
<!-- cannbot:related:end -->
