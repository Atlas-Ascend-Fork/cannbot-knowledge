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

- [LocalTensor SetValue 参数颠倒导致索引错乱](../../../../../runbooks/precision/localtensor_setvalue_uses_offset_then_value.md)（`exemplifies`）：`LocalTensor::SetValue` 的真实契约是 `SetValue(offset, value)`，而出错代码按 `SetValue(value, offset)` 调用。；设置 LocalTensor 指定索引的元素值。仅在 TPosition 为 VECIN/VECCALC/VECOUT 时支持。参数 offset 为索引偏移，value 为设置的值。支持 950/a2/a3。。故障卡中的参数顺序错误由 SetValue API 的 offset 索引优先、value 值次之合同直接解释。
- [arch35 GetValue/SetValue 标量bypass禁用](../../../../../runbooks/compilation/arch35_getvalue_setvalue_bypass.md)（`exemplifies`）：设置 LocalTensor 指定索引的元素值。仅在 TPosition 为 VECIN/VECCALC/VECOUT 时支持。参数 offset 为索引偏移，value 为设置的值。支持 950/a2/a3。；在 Ascend950PR（arch35 / RegBase、CANN cann-9.0.0-beta.2）上开发 `softplus_v2_grad` 算子。为绕过 `Select(VSEL_CMPMASK_SPR)` 在标量场景（count==1）的 mask 污染问题，尝试对标量输入用 `LocalTensor::GetValue` / `SetValue` 做标量计算 bypass：当 count==1 时用 GetValue 从 LocalTensor 取标量值、用标量数学函数计算、用 SetValue 写回，绕开 Compare+Select 路径。；API 卡给出合法位置和参数，runbook 说明在 arch35 向量流把它当标量 bypass 会让测试失败数暴涨。
<!-- cannbot:related:end -->
