---
type: API
title: SetValue
description: 设置LocalTensor中的某个值。 该接口仅在LocalTensor的TPosition为VECIN/VECCALC/VECOUT时支持。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/LocalTensor/SetValue.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetValue

设置 LocalTensor 指定索引的元素值。仅在 TPosition 为 VECIN/VECCALC/VECOUT 时支持。参数 offset 为索引偏移，value 为设置的值。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [Ascend950 DMA 32B 块最小传输粒度](../../../../../runbooks/compilation/ascend950_dma_32b_minimum_block_granularity.md)（`exemplifies`）：SetValue 与 GetValue 配合建立单元素写入基线，可区分 32B DMA 组织错误与算术错误。
- [LocalTensor SetValue 参数颠倒导致索引错乱](../../../../../runbooks/precision/localtensor_setvalue_uses_offset_then_value.md)（`exemplifies`）：Runbook 的编译错误来自把 SetValue 参数写成 value, offset；API 卡明确签名语义为 offset 在前、value 在后。
- [arch35 GetValue/SetValue 标量bypass禁用](../../../../../runbooks/compilation/arch35_getvalue_setvalue_bypass.md)（`exemplifies`）：Runbook 的 scalar bypass 用 SetValue 写回标量再进入向量计算；API 卡给出 offset/value 基本契约，但不承诺与前后向量流水自动同步。
- [GetValue](get_value.md)（`same_topic`）：SetValue 写入 LocalTensor 单元素，GetValue 读取单元素，构成同一 LocalTensor 标量访问契约的读写对。
- [operator](operator_call.md)（`same_topic`）：operator 与《SetValue》的实质衔接是：LocalTensor operator 生成子视图，必须与地址/size/shape 属性和 Get/SetValue、offset 故障共同理解。
<!-- cannbot:related:end -->
