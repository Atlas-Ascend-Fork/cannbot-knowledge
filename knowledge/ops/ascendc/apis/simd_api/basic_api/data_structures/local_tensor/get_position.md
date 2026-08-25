---
type: API
title: GetPosition
description: 获取LocalTensor所在的TPosition逻辑位置，支持TPosition为VECIN、VECOUT、VECCALC、A1、A2、B1、B2、CO1、CO2。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/LocalTensor/GetPosition.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetPosition

获取 LocalTensor 所在的 TPosition 逻辑位置。函数签名为 __aicore__ inline int32_t GetPosition() const，无入参。
返回值为 TPosition 枚举，支持 VECIN、VECOUT、VECCALC、A1、A2、B1、B2、CO1、CO2 等逻辑位置。
用于在运行时查询 Tensor 所处的缓冲区位置，从而选择不同的处理逻辑。
支持 Ascend 950PR/950DT、Atlas A2、Atlas A3、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品 AI Core 与 Vector Core 以及 Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [L1/L0 tensor 须用 TPosition 构造非 SetAddr](../../../../../runbooks/compilation/l1_l0_tensor_tposition_setaddr.md)（`exemplifies`）：《GetPosition》处理“获取LocalTensor所在的TPosition逻辑位置，支持TPosition为VECIN、VECOUT、VECCALC、A1、A2、B1、B2、CO1、CO2。”。《L1/L0 tensor 须用 TPosition 构造非 SetAddr》明确提供“CANN 9.2.0 arch35 上 TBuf 无 SetAddr、LocalTensor<T>(addr) 触 tPos trait 错；L1/L0A/L0B/L0C 须用 LocalTensor<T>(TPosition, addr, size) 构造。”，其参数、调用或验证步骤直接接入GetPosition 所读取的 LocalTensor 位置、构造来源和 TPosition 故障定位。
- [TQue 位置参数须用 AscendC::TPosition 枚举](../../../../../runbooks/compilation/tque_ascendc_tposition.md)（`exemplifies`）：《GetPosition》处理“获取LocalTensor所在的TPosition逻辑位置，支持TPosition为VECIN、VECOUT、VECCALC、A1、A2、B1、B2、CO1、CO2。”。《TQue 位置参数须用 AscendC::TPosition 枚举》明确提供“dav-3510/CANN 9.1.0 上用 ASCEND_TPOSITION_VECIN/VECOUT 宏声明 TQue 模板位置参数，编译报 use of undeclared identifier；判别后改用 AscendC::TPosition::VECIN/VECOUT 作用域枚举可消除该组错误。”，其参数、调用或验证步骤直接接入GetPosition 所读取的 LocalTensor 位置、构造来源和 TPosition 故障定位。
- [LocalTensor](local_tensor.md)（`related`）：《GetPosition》处理“获取LocalTensor所在的TPosition逻辑位置，支持TPosition为VECIN、VECOUT、VECCALC、A1、A2、B1、B2、CO1、CO2。”。《LocalTensor》明确提供“LocalTensor 数据结构接口集，提供 UB 侧局部张量管理能力，含构造函数、SetValue、GetValue、GetSize 等。”，其参数、调用或验证步骤直接接入GetPosition 所读取的 LocalTensor 位置、构造来源和 TPosition 故障定位。
- [LocalTensor构造函数](local_tensor_constructor.md)（`related`）：《GetPosition》处理“获取LocalTensor所在的TPosition逻辑位置，支持TPosition为VECIN、VECOUT、VECCALC、A1、A2、B1、B2、CO1、CO2。”。《LocalTensor构造函数》明确提供“LocalTensor构造函数。”，其参数、调用或验证步骤直接接入GetPosition 所读取的 LocalTensor 位置、构造来源和 TPosition 故障定位。
- [LocalTensor简介](local_tensor_intro.md)（`related`）：《GetPosition》处理“获取LocalTensor所在的TPosition逻辑位置，支持TPosition为VECIN、VECOUT、VECCALC、A1、A2、B1、B2、CO1、CO2。”。《LocalTensor简介》明确提供“LocalTensor表达AI Core中Local Memory（内部存储）内的L1/L0A/L0B/L0C Buffer及Unified Buffer中的数据。”，其参数、调用或验证步骤直接接入GetPosition 所读取的 LocalTensor 位置、构造来源和 TPosition 故障定位。
- [TPosition](../../aux_data_structures/t_position.md)（`related`）：《GetPosition》处理“获取LocalTensor所在的TPosition逻辑位置，支持TPosition为VECIN、VECOUT、VECCALC、A1、A2、B1、B2、CO1、CO2。”。《TPosition》明确提供“Ascend C管理不同层级物理内存的抽象逻辑位置，代替片上物理存储概念，包括矢量编程和矩阵编程所需的各类存储位置。”，其参数、调用或验证步骤直接接入GetPosition 所读取的 LocalTensor 位置、构造来源和 TPosition 故障定位。
<!-- cannbot:related:end -->
