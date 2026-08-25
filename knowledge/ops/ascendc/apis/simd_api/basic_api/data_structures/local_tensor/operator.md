---
type: API
title: OperatorSubscript
description: 获取距原LocalTensor起始地址偏移量为offset的新LocalTensor，offset不能超过原有LocalTensor的size大小。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/LocalTensor/operator.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# OperatorSubscript

获取距原 LocalTensor 起始地址偏移量为 offset 的新 LocalTensor，offset 不能超过原 LocalTensor 的 size 大小。
通过 operator 下标操作符获取偏移 Tensor，参数 offset 为 uint32_t 类型偏移量，单位为元素，返回值为偏移后的新 LocalTensor，共享原 Tensor 的存储空间。
常用于对 LocalTensor 进行分段操作，例如 inputLocal 偏移 16 个元素后返回的新 Tensor 可供 Add 等计算接口使用。
支持 Ascend 950PR/950DT、Atlas A2、Atlas A3、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品 AI Core 与 Vector Core 以及 Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [Vector Sub 源 UB 非 32B 对齐触发错误 340](../../../../../runbooks/compilation/vector_sub_ub_32b_340.md)（`exemplifies`）：Vector Sub 源 UB 非 32B 对齐触发错误 340 与《OperatorSubscript》的实质衔接是：Vector Sub 的每个 UB 源必须 32B 对齐，LocalTensor 非零 operator[] 偏移会破坏对齐；Sub API、GetWithOffset/TBuf 和相邻未对齐故障卡直接支持定位及对齐搬入修法。
- [SetBufferLen](set_buffer_len.md)（`related`）：operator[] 创建 LocalTensor 子视图后，正文建议立即 SetBufferLen，使编译器掌握子视图物理缓冲长度。
- [SetAddrWithOffset](set_addr_with_offset.md)（`same_topic`）：SetAddrWithOffset 与《OperatorSubscript》的实质衔接是：SetAddrWithOffset 与子视图/偏移接口共享元素偏移契约，所选故障卡直接说明错误基址叠加、L1/L0 限制及 DataCopy 偏移修复。
- [operator](operator_call.md)（`same_topic`）：LocalTensor::operator[] 按元素偏移得到共享存储的子张量，operator() 提供另一种切片/地址视图入口；二者共同决定子视图的偏移与共享存储语义。
<!-- cannbot:related:end -->
