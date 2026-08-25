---
type: API
title: ExtendCfgInfo
description: 用于扩展算子相关参数配置，提供更灵活的参数配置能力。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpAICoreConfig/ExtendCfgInfo.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---
# ExtendCfgInfo

## 功能说明
用于扩展算子相关参数配置，提供更灵活的参数配置能力。
## 函数原型
## 参数说明
参数说明
key：配置项，如"aclnnSupport.value"。
value：配置项key对应的取值，如"aclnnSupport.value"，可以填充"support_aclnn"或者"aclnn_only"。
ExtendCfgInfo支持的参数如下表：
ExtendCfgInfo支持配置的参数
aclnnSupport.value：- support_aclnn：此模式下，静态Shape场景中该算子通过模型下沉执行，动态Shape场景则在Host侧调用fallback函数下发算子。如果调用了EnableFallBack则默认采用该模式。- aclnn_only：此模式下，动静态Shape场景中该算子均以fallback形式下发。不建议用户使用该模式，后续版本待废弃。关于fallback下发算子的详细介绍请参考《图引擎开发指南》。
support_aclnn使用示例：
aclnn_only使用示例：
## 返回值说明
OpAICoreConfig算子定义，请参考OpAICoreConfig。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [EnableFallBack](../op_def/enable_fall_back.md)（`related`）：ExtendCfgInfo 的 aclnnSupport.value 明确以 EnableFallBack 为默认 support_aclnn 触发来源；前者细化静态/动态下发策略，后者生成并注册实际 fallback 函数。
- [ExtendCfgInfo](../op_host_cpu_def/extend_cfg_info.md)（`same_topic`）：ExtendCfgInfo：HostCPU ExtendCfgInfo与AICPU/AICore同名接口比较可确认配置落在哪类实现，OpHostCPUDef页定义其所属注册对象与其他属性组合。 目标卡《ExtendCfgInfo》补充：用于扩展算子相关参数配置，提供更灵活的参数配置能力。
<!-- cannbot:related:end -->
