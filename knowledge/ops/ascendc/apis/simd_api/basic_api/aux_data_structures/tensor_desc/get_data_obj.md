---
type: API
title: GetDataObj
description: 将数据指针置于GlobalTensor中并返回该GlobalTensor。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.development_mode.tensor_programming
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/TensorDesc/GetDataObj.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- a2
- a3
- 310p
source_headers:
- include/basic_api/kernel_operator_list_tensor_intf.h
---

# GetDataObj<a name="ZH-CN_TOPIC_0000002340348465"></a>

## 功能说明<a name="zh-cn_topic_0000002078447573_zh-cn_topic_0000001576806829_zh-cn_topic_0000001339187720_section36583473819"></a>

将数据指针置于GlobalTensor中并返回该GlobalTensor。

## 函数原型<a name="zh-cn_topic_0000002078447573_zh-cn_topic_0000001576806829_zh-cn_topic_0000001339187720_section13230182415108"></a>

```cpp
GlobalTensor<T> GetDataObj()
```

## 参数说明<a name="zh-cn_topic_0000002078447573_zh-cn_topic_0000001576806829_zh-cn_topic_0000001339187720_section75395119104"></a>

无

## 返回值说明<a name="zh-cn_topic_0000002078447573_zh-cn_topic_0000001576806829_zh-cn_topic_0000001339187720_section25791320141317"></a>

返回设置了数据指针的GlobalTensor。

## 约束说明<a name="zh-cn_topic_0000002078447573_zh-cn_topic_0000001576806829_zh-cn_topic_0000001339187720_section19165124931511"></a>

无



<!-- cannbot:related:start -->
## 相关

- [GetDataPtr](get_data_ptr.md)（`related`）：获取储存Tensor数据地址。；将数据指针置于 GlobalTensor 中并返回该 GlobalTensor。；两接口都在 TensorDesc 与底层 Tensor 数据之间建立访问入口；前者返回原始地址，后者把相同数据指针封装成后续搬运或计算可消费的 GlobalTensor。
<!-- cannbot:related:end -->
