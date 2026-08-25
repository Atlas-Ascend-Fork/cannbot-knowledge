---
type: API
title: ExtendCfgInfo
description: 为AICPU自定义算子额外添加一组键值对形式的扩展配置。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpAICPUDef/ExtendCfgInfo.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# ExtendCfgInfo

## 功能说明
为AICPU自定义算子额外添加一组键值对形式的扩展配置。
## 函数原型
## 参数说明
## 返回值说明
OpAICPUDef算子定义，OpAICPUDef请参考OpAICPUDef。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [AICPU launcher 缺 OP_ATTR_NAMES 编译错](../../../../runbooks/compilation/aicpu_launcher_op_attr_names.md)（`exemplifies`）：ExtendCfgInfo 与《AICPU launcher 缺 OP_ATTR_NAMES 编译错》的实质衔接是：ExtendCfgInfo 属于 OpAICPUDef 的扩展键值配置，AICPU 编译材料与 launcher 属性缺失故障说明该配置进入生成和加载阶段的位置。
- [AI CPU算子编译](../../../../guides/programming_guide/compilation_and_execution/operator_compilation/ai_cpu_operator_compilation.md)（`explains`）：ExtendCfgInfo 与《AI CPU算子编译》的实质衔接是：ExtendCfgInfo 属于 OpAICPUDef 的扩展键值配置，AICPU 编译材料与 launcher 属性缺失故障说明该配置进入生成和加载阶段的位置。
- [ExtendCfgInfo](../op_host_cpu_def/extend_cfg_info.md)（`same_topic`）：ExtendCfgInfo：HostCPU ExtendCfgInfo与AICPU/AICore同名接口比较可确认配置落在哪类实现，OpHostCPUDef页定义其所属注册对象与其他属性组合。 目标卡《ExtendCfgInfo》补充：为AICPU自定义算子额外添加一组键值对形式的扩展配置。
- [OpAICPUDef](op_aicpu_def.md)（`same_topic`）：ExtendCfgInfo 与《OpAICPUDef》的实质衔接是：ExtendCfgInfo 属于 OpAICPUDef 的扩展键值配置，AICPU 编译材料与 launcher 属性缺失故障说明该配置进入生成和加载阶段的位置。
<!-- cannbot:related:end -->
