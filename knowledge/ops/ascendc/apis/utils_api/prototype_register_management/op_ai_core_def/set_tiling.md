---
type: API
title: SetTiling（OpAICoreDef）
description: 注册Tiling函数。Tiling函数的原型是固定的，接受一个TilingContext作为输入，在此context上可以获取到输入、输出的Shape指针等内容。注册的Tiling函数由框架调用，调用时会传入TilingContext参数。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpAICoreDef/SetTiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# SetTiling

## 功能说明
注册Tiling函数。Tiling函数的原型是固定的，接受一个TilingContext作为输入，在此context上可以获取到输入、输出的Shape指针等内容。注册的Tiling函数由框架调用，调用时会传入TilingContext参数。
## 函数原型
## 参数说明
## 返回值说明
OpAICoreDef算子定义，OpAICoreDef请参考OpAICoreDef。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [561002：TilingParse 未生效，CompileInfo 为空](../../../../runbooks/compilation/561002_tilingparse_compileinfo.md)（`exemplifies`）：SetTiling（OpAICoreDef） 与《561002：TilingParse 未生效，CompileInfo 为空》的实质衔接是：SetTiling 作用于 OpAICoreDef 的 tiling 对象，TilingParse 空与 ValueDepend 轴错误是 host tiling 注册阶段的直接失败模式。
- [ValueDepend(REQUIRED) 让 axes 走 host 端](../../../../runbooks/compilation/opdef_value_depend_required_for_axes_host_read.md)（`exemplifies`）：SetTiling（OpAICoreDef） 与《ValueDepend(REQUIRED) 让 axes 走 host 端》的实质衔接是：SetTiling 作用于 OpAICoreDef 的 tiling 对象，TilingParse 空与 ValueDepend 轴错误是 host tiling 注册阶段的直接失败模式。
- [AICore（OpDef）](../op_def/ai_core.md)（`related`）：SetTiling 把 Host tiling 回调挂到 AICore 配置，是 AICore 描述中的核心后续动作。
- [OpAICoreDef](op_ai_core_def.md)（`same_topic`）：OpAICoreDef 与《SetTiling（OpAICoreDef）》的实质衔接是：OpAICoreDef 通过 SetTiling 与 AddConfig 绑定 tiling 和 OpAICoreConfig；注册宏及缺 AddConfig 故障验证这条 SOC 选择契约。
<!-- cannbot:related:end -->
