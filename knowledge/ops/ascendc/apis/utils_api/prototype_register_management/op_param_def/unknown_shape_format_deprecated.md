---
type: API
title: UnknownShapeFormat
description: 已废弃接口，设置未知Shape情况下的Format默认值，请统一使用Format接口替代。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpParamDef/UnknownShapeFormat_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# UnknownShapeFormat（废弃）

## 功能说明
> [!CAUTION]注意
>-   该接口废弃，并将在后续版本移除，请不要使用该接口。无需针对动态/静态shape单独设置format，统一使用Format接口来设置即可。
>-   如果开发者使用了该接口，并开启-Werror -Wall编译选项开启所有警告当做错误处理，会有编译报错。此时可以通过添加-Wno-deprecated编译选项来消除，但是存在后续接口在版本中移除后编译报错的风险，建议不要使用该接口，统一使用Format接口来设置。
>    编译选项加在自定义算子工程目录下op_host/CMakeLists.txt中的cust_optiling、cust_opproto编译target上，样例如下：
>
未知Shape情况下的Format的默认值。
## 函数原型
## 参数说明
## 返回值说明
OpDef算子定义，OpDef请参考OpDef。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [Format（OpParamDef）](format.md)（`same_topic`）：该接口废弃，并将在后续版本移除，请不要使用该接口。无需针对动态/静态shape单独设置format，统一使用Format接口来设置即可。定义算子参数数据格式。废弃卡明确把 UnknownShapeFormat 的职责迁移到 Format，目标卡定义承接后的参数格式设置合同；替换后还能消除 deprecated 警告在严格编译选项下升级为错误的风险。
<!-- cannbot:related:end -->
