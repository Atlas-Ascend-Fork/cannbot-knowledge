---
type: API
title: LocalTensor简介
description: LocalTensor表达AI Core中Local Memory（内部存储）内的L1/L0A/L0B/L0C Buffer及Unified
  Buffer中的数据。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/LocalTensor/LocalTensor_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# LocalTensor简介

LocalTensor 表达 AI Core 中 Local Memory 内的数据，覆盖 L1/L0A/L0B/L0C Buffer 及 Unified Buffer。通过 TPosition 标识逻辑位置（A1/B1/C1/A2/B2/CO1/VECIN/VECOUT 等），同一物理内存可映射多个 TPosition。

核心方法：GetValue/SetValue 元素读写，GetShapeInfo/SetShapeInfo 形状管理，GetSize/GetLength 大小获取，GetPhyAddr 物理地址，ReinterpretCast 类型重解释，operator[]/operator() 下标访问，SetBufferLen/SetAddrWithOffset 地址管理，Print 调试打印，ToFile 数据导出。Pipe 编程框架下通过 TQue 分配，静态编程下通过构造函数指定 pos/addr/size。

<!-- cannbot:related:start -->
## 相关

- [特定 b16 load-cast-store 组合失真时在 LocalTensor 边界转换](../../../../../runbooks/precision/b16_reg_cast_layout_should_convert_at_localtensor_boundary.md)（`exemplifies`）：特定 b16 load-cast-store 组合失真时在 LocalTensor 边界转换 与《LocalTensor简介》的实质衔接是：故障链是 B16 LoadDist 解包后 Reg::Cast 写 UB 的 lane 布局失真；UNPACK 数值转换卡和 RegLayout 解释机制，LocalTensor/Load/Store 是出入边界，正确配方改用 Memory Cast 在 LocalTensor 边界转换。
- [GetPosition](get_position.md)（`related`）：《GetPosition》处理“获取LocalTensor所在的TPosition逻辑位置，支持TPosition为VECIN、VECOUT、VECCALC、A1、A2、B1、B2、CO1、CO2。”。《LocalTensor简介》明确提供“LocalTensor表达AI Core中Local Memory（内部存储）内的L1/L0A/L0B/L0C Buffer及Unified Buffer中的数据。”，其参数、调用或验证步骤直接接入GetPosition 所读取的 LocalTensor 位置、构造来源和 TPosition 故障定位。
- [GetUserTag](get_user_tag.md)（`related`）：《GetUserTag》处理“获取指定Tensor块的Tag信息，用户可以根据Tag信息对Tensor进行不同操作。”。《LocalTensor简介》提供“LocalTensor表达AI Core中Local Memory（内部存储）内的L1/L0A/L0B/L0C Buffer及Unified Buffer中的数据。”，其具体合同或探针直接接入GetUserTag 与 SetUserTag 及 LocalTensor 所有权的读写合同。
- [LocalTensor](local_tensor.md)（`same_topic`）：LocalTensor 索引页列出方法，intro 明确其对应 L1/L0A/L0B/L0C/UB 本地内存与 TPosition 语义，是理解对象存储契约的核心说明。
- [LocalTensor构造函数](local_tensor_constructor.md)（`same_topic`）：《LocalTensor构造函数》处理“LocalTensor构造函数。”。《LocalTensor简介》明确“LocalTensor表达AI Core中Local Memory（内部存储）内的L1/L0A/L0B/L0C Buffer及Unified Buffer中的数据。”，可直接用于核对LocalTensor 的默认/静态地址构造、LocalMemAllocator 构造路径及错误实参诊断。
<!-- cannbot:related:end -->
