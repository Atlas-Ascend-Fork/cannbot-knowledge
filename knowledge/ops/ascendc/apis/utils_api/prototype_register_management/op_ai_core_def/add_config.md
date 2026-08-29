---
type: API
title: AddConfig（OpAICoreDef）
description: 注册算子支持的AI处理器型号以及OpAICoreConfig信息。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpAICoreDef/AddConfig.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# AddConfig

## 功能说明
注册算子支持的AI处理器型号以及OpAICoreConfig信息。
## 函数原型
## 参数说明
## 返回值说明
无
## 约束说明
不传入aicore_config参数时，对OpAICoreConfig结构中的部分参数会配置成默认值，具体的参数和默认值如下表所示：
不传入aicore_config参数时，OpAICoreConfig默认配置

<!-- cannbot:related:start -->
## 相关

- [def.cpp 缺 AddConfig 致 SOC_NOT_SUPPORT](../../../../runbooks/compilation/def_cpp_addconfig_soc_not_support.md)（`exemplifies`）：op_host `<op>_def.cpp` 的 `this->AICore().AddConfig("<soc>", <aicore_config>)` 注册块。；注册算子支持的AI处理器型号以及OpAICoreConfig信息。；候选是修复 SOC_NOT_SUPPORT 所需补齐的直接注册接口。
<!-- cannbot:related:end -->
