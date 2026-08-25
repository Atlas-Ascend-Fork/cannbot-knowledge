---
type: API
title: operator
description: 获取某个索引位置的元素的引用。 与LocalTensor的operator\(\)类似。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/GlobalTensor/operator_call.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# operator

获取 GlobalTensor 某个索引位置元素的引用，与 LocalTensor 的 operator() 类似。
函数签名为 __aicore__ inline PrimType& operator()(const uint64_t offset) const，参数 offset 为 GlobalTensor 的下标索引。
返回值为指定索引位置的 PrimType 类型引用，用于左值相当于 SetValue，用于右值相当于 GetValue。
PrimType 通过 PrimT<T> 从基础数据类型或 TensorTrait 中萃取基础数据类型。
支持 Ascend 950PR/950DT、Atlas A2 与 Atlas A3 系列产品，Atlas 200I/500 A2 推理产品、Atlas 推理系列产品与 Atlas 训练系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [GM SetValue 写回后 GetValue 读到旧值](../../../../../runbooks/precision/gm_setvalue_getvalue_reads_stale_within_kernel.md)（`exemplifies`）：The runbook demonstrates that a GM scalar write followed by a scalar read in one kernel can observe stale data, constraining operator()/SetValue/GetValue use.
- [GetValue](get_value.md)（`same_topic`）：GetValue is the explicit rvalue operation equivalent to using GlobalTensor::operator() on the right-hand side.
<!-- cannbot:related:end -->
