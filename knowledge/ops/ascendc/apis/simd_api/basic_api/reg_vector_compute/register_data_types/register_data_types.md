---
type: API
title: 寄存器数据类型
description: Reg矢量计算API操作的基础寄存器数据类型介绍如下：
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/register_data_types/register_data_types.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 寄存器数据类型

Reg矢量计算API操作的基础寄存器数据类型介绍如下：

-   **RegTensor**
矢量数据寄存器，Reg矢量计算基本存储单元，用于矢量计算。RegTensor的位宽是VL（VectorLength），长度为256B，可存储VL/sizeof(T)个数据（T表示数据类型）。b64或complex32类型下，支持扩展存储2VL用于复杂计算。

-   **MaskReg**
掩码寄存器，用于矢量计算中选择参与计算的元素。MaskReg的位宽是VL/8，长度为32B。

-   **UnalignRegForLoad & UnalignRegForStore**
非对齐寄存器，作为缓冲区，用来优化UB和RegTensor之间的连续非对齐地址访问的开销。

-   **AddrReg**
地址寄存器，用于存储地址偏移量的寄存器。AddrReg通过调用CreateAddrReg接口根据每层循环所设置的stride进行地址偏移自增。

<!-- cannbot:related:start -->
## 相关

- [Ascend950 Reg 扫描按 256B 锁定 lane](../../../../../runbooks/precision/dav3510_vector_register_width_is_256_bytes.md)（`exemplifies`）：Ascend950 Reg 扫描按 256B 锁定 lane 与《寄存器数据类型》的实质衔接是：这些卡共同约束 256B RegTensor 的 lane 数、B16/B32 提升后的 mask 宽度以及 LoadAlign/VF 调用范围；所连错例均由按错误数据宽度计算 lane 或目标 VL 导致。
- [MaskReg](mask_reg.md)（`same_topic`）：MaskReg 与《寄存器数据类型》的实质衔接是：MaskReg 定义有效 lane，直接被 Load/Store、MaskGen 与 MaskReg 计算消费；C 创建/更新接口、merge mode、复用指南和两个编译故障明确其构造约束。
- [RegTensor](reg_tensor.md)（`same_topic`）：RegTensor 与《寄存器数据类型》的实质衔接是：RegTensor 是 256B VL 的 VF 内基本单元；MaskReg/AddrReg/非对齐状态、内置类型和跨 VF/错误类型案例直接限定 lane、寿命和模板参数。
- [UnalignRegForLoadAndUnalignRegForStore](unalign_reg_for_load_unalign_reg_for_store.md)（`same_topic`）：UnalignRegForLoadAndUnalignRegForStore 与《寄存器数据类型》的实质衔接是：非对齐寄存器是 LoadUnAlign Pre→Load 与 Store→Post 协议的临时状态，所选 C/C++ 接口、连续优化和 Init/Postupdate 共同闭合搬入搬出流程。
<!-- cannbot:related:end -->
