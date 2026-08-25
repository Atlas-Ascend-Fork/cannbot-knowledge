---
type: API
title: AscGetPhyStackBase
description: 获取物理堆栈基地址。
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sys_var/asc_get_phy_stack_base.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscGetPhyStackBase

获取物理堆栈基地址。
函数原型：int64_t asc_get_phy_stack_base()
返回值：物理堆栈基地址。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [GetPhyAddr const __gm__ 返回不可去 const](../../../../runbooks/compilation/getphyaddr_const_gm_const.md)（`exemplifies`）：AscGetPhyStackBase 与《GetPhyAddr const __gm__ 返回不可去 const》的实质衔接是：物理栈基地址与 Global/LocalTensor GetPhyAddr、物理 buffer 地址共同用于物理寻址；const GetPhyAddr 故障直接约束返回地址可变性。
- [GetPhyAddr](../../basic_api/data_structures/global_tensor/get_phy_addr.md)（`related`）：AscGetPhyStackBase 与《GetPhyAddr》的实质衔接是：物理栈基地址与 Global/LocalTensor GetPhyAddr、物理 buffer 地址共同用于物理寻址；const GetPhyAddr 故障直接约束返回地址可变性。
- [GetPhyAddr](../../basic_api/data_structures/local_tensor/get_phy_addr.md)（`related`）：AscGetPhyStackBase 与《GetPhyAddr》的实质衔接是：物理栈基地址与 Global/LocalTensor GetPhyAddr、物理 buffer 地址共同用于物理寻址；const GetPhyAddr 故障直接约束返回地址可变性。
- [AscGetPhyBufAddr](asc_get_phy_buf_addr.md)（`same_topic`）：AscGetPhyStackBase 与《AscGetPhyBufAddr》的实质衔接是：物理栈基地址与 Global/LocalTensor GetPhyAddr、物理 buffer 地址共同用于物理寻址；const GetPhyAddr 故障直接约束返回地址可变性。
<!-- cannbot:related:end -->
