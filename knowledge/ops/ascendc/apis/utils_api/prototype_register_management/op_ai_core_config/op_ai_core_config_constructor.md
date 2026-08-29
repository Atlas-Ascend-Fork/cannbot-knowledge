---
type: API
title: OpAICoreConfig构造函数
description: OpAICoreConfig构造函数。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpAICoreConfig/OpAICoreConfig_constructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---
# OpAICoreConfig构造函数

## 功能说明
OpAICoreConfig构造函数。
## 函数原型
## 参数说明
soc：输入：AI处理器型号。
aicore_config：输入：已构造完成的OpAICoreConfig，用于拷贝构造OpAICoreConfig。
## 返回值说明
无
## 约束说明
传入soc入参的构造函数会对OpAICoreConfig结构中的部分参数进行初始化，具体的参数和初始化值如下表所示：
无入参的默认构造函数不会初始化上述参数。
拷贝构造函数会复制被拷贝对象中已配置的输入、输出和配置项信息。
