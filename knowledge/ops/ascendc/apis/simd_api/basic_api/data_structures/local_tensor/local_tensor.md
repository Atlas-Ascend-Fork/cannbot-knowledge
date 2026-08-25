---
type: API
title: LocalTensor
description: LocalTensor 数据结构接口集，提供 UB 侧局部张量管理能力，含构造函数、SetValue、GetValue、GetSize 等。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/LocalTensor/LocalTensor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# LocalTensor

LocalTensor 用于管理 UB（Unified Buffer）侧的局部张量，是矢量计算的主要数据载体。提供 SetValue/GetValue/operator[]/operator() 元素读写，SetSize/GetSize/SetShapeInfo/GetShapeInfo 形状管理，GetPhyAddr/GetPosition/GetLength 地址与位置查询，ReinterpretCast 类型重解释。ToFile/Print 用于调试输出，SetUserTag 用于设置调试标签。

<!-- cannbot:related:start -->
## 相关

- [DataCopyPad 无匹配重载 LocalTensor 实参不一致](../../../../../runbooks/compilation/datacopypad_localtensor.md)（`exemplifies`）：该构建故障证明 LocalTensor<T> 的模板元素类型是强契约，float 与 int8_t 不能在 DataCopyPad/helper 重载间隐式转换；可用于定位 LocalTensor 类型不匹配。
- [Gather 双加 LocalTensor 基址导致交错旋转乱码](../../../../../runbooks/precision/localtensor_gather_base_address_not_double_counted.md)（`exemplifies`）：LocalTensor 已封装源基址时 Gather 的 srcBaseAddr 只能传相对字节偏移；该卡证明重复传物理基址会二次加址，补充了 LocalTensor 与 Gather 的地址契约。
- [LocalTensor SetValue 参数颠倒导致索引错乱](../../../../../runbooks/precision/localtensor_setvalue_uses_offset_then_value.md)（`exemplifies`）：该故障卡验证 SetValue 参数顺序是 offset 后 value，颠倒会直接破坏 Reg Gather 索引表；补充了 LocalTensor 标量写接口的可执行诊断。
- [TBuf 不能直接传给 LocalTensor 形参](../../../../../runbooks/compilation/tbuf_gets_typed_localtensor_before_helper_call.md)（`exemplifies`）：LocalTensor 接口定义 helper 实际消费的带类型、可寻址张量视图，解释编译器为何拒绝把 TBuf 管理对象直接绑定到该形参。
- [GetPosition](get_position.md)（`related`）：《GetPosition》处理“获取LocalTensor所在的TPosition逻辑位置，支持TPosition为VECIN、VECOUT、VECCALC、A1、A2、B1、B2、CO1、CO2。”。《LocalTensor》明确提供“LocalTensor 数据结构接口集，提供 UB 侧局部张量管理能力，含构造函数、SetValue、GetValue、GetSize 等。”，其参数、调用或验证步骤直接接入GetPosition 所读取的 LocalTensor 位置、构造来源和 TPosition 故障定位。
- [LocalTensor简介](local_tensor_intro.md)（`same_topic`）：LocalTensor 索引页列出方法，intro 明确其对应 L1/L0A/L0B/L0C/UB 本地内存与 TPosition 语义，是理解对象存储契约的核心说明。
<!-- cannbot:related:end -->
