---
type: API
title: DynamicCompileStaticFlag
description: 用于标识该算子实现是否支持入图时的静态Shape编译。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpAICoreConfig/DynamicCompileStaticFlag.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# DynamicCompileStaticFlag

## 功能说明
用于标识该算子实现是否支持入图时的静态Shape编译。
## 函数原型
## 参数说明
## 返回值说明
OpAICoreConfig类，请参考OpAICoreConfig。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [arch35 小 per-channel 输出读旧值判别与规避](../../../../runbooks/compilation/arch35_per_channel.md)（`exemplifies`）：《arch35 小 per-channel 输出读旧值判别与规避》处理“arch35 上 DCCI 缓存不一致使 DataCopyPad 对小 per-channel [C] 输出不可靠、TQue GetValue(MTE2→scalar) 读到旧值；判别方法为先 V-launder(Duplicate 0.0f+Add) 到 TBuf 再 GetValue，并用 GlobalTensor::SetValue 直写 GM per-channel 结果。”。《DynamicCompileStaticFlag》提供“用于标识该算子实现是否支持入图时的静态Shape编译。”，其具体合同或探针直接接入arch35 小 per-channel 的 DCCI/Scalar 旧值机制、V-launder 与 SetValue 验证。
- [DynamicShapeSupportFlag](dynamic_shape_support_flag.md)（`same_topic`）：两张卡分别声明静态形状动态编译和动态形状支持能力，是 OpAICoreConfig 上同一 shape/compile 能力决策的互补标志。
<!-- cannbot:related:end -->
