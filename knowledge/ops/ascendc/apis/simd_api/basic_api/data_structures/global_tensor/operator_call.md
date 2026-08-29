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

- [GetValue](get_value.md)（`related`）：返回值为指定索引位置的 PrimType 类型引用，用于左值相当于 SetValue，用于右值相当于 GetValue。；获取GlobalTensor的相应偏移位置的值。。GlobalTensor operator() 卡明确右值语境等价于 GetValue，GetValue 卡给出按偏移读取的语义，二者连接运算符重载与显式读取接口。
- [SetValue](set_value.md)（`related`）：返回值为指定索引位置的 PrimType 类型引用，用于左值相当于 SetValue，用于右值相当于 GetValue。；设置 GlobalTensor 指定偏移位置的元素值。操作先写入 DCache，需配合 DataCacheCleanAndInvalid 确保数据一致性。。GlobalTensor operator() 卡明确左值语境等价于 SetValue，SetValue 卡说明指定偏移写入及 DCache 一致性要求，二者连接运算符重载与显式写接口。
<!-- cannbot:related:end -->
