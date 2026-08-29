---
type: API
title: GetTPipePtr
description: 获取创建TPipe对象时设置的全局唯一TPipe指针，获取后可进行TPipe相关的操作如InitBuffer。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/GetTPipePtr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# GetTPipePtr

头文件路径为："basic_api/kernel_common.h"。

创建TPipe对象时，对象初始化会设置全局唯一的TPipe指针。本接口用于获取该指针，获取该指针后，可进行TPipe相关的操作。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [GetTPipePtr 错加 AscendC 命名空间导致编译失败](../../../../runbooks/compilation/gettpipeptr_is_global_function.md)（`exemplifies`）：“`GetTPipePtr` 的函数标识符声明在全局命名空间，只有返回类型是 `AscendC::TPipe*`，因此给函数名添加 `AscendC::` 会在该命名空间内查找一个不存在的成员。”给出编译失败的命名空间根因；“创建TPipe对象时，对象初始化会设置全局唯一的TPipe指针。”提供对应 API 的全局指针合同。
- [DequantBias A2/A3 ACLNN 算子知识](../../../../operators/aclnn/nn/quant/dequant_bias.md)（`related`）：“event_t eventMTE2V = static_cast<event_t>(GetTPipePtr()->FetchEventID(HardEvent::MTE2_V));”显示 DequantBias 通过全局 TPipe 指针取事件；“本接口用于获取该指针，获取该指针后，可进行TPipe相关的操作。”说明 GetTPipePtr 的返回用途。
<!-- cannbot:related:end -->
