---
type: API
title: Format（OpParamDef）
description: 定义算子参数数据格式。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpParamDef/Format.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# Format

## 功能说明
定义算子参数数据格式。
## 函数原型
## 参数说明
## 返回值说明
OpParamDef算子定义，OpParamDef请参考OpParamDef。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [OpDef FORMAT_NCHW 致 5D 报 161002](../../../../runbooks/compilation/opdef_format_nchw_5d_161002.md)（`exemplifies`）：“CANN 的 `ACL_FORMAT_NCHW` 仅对 4D 张量有效；5D 张量（`［N,D,C,H,W］`）没有 NCHW 这一物理格式，OpDef 强制 NCHW 会让 5D 输入在 `GetWorkspaceSize` 阶段被拒。”与“定义算子参数数据格式。”提供双方正文证据。Format API 给出 OpDef 参数格式定义入口，运行手册具体证明把 5D 输入定义为 NCHW 会在 GetWorkspaceSize 返回 161002，并给出保持 FORMAT_ND、由 shape 推断布局的边界。
- [UnknownShapeFormat](unknown_shape_format_deprecated.md)（`same_topic`）：该接口废弃，并将在后续版本移除，请不要使用该接口。无需针对动态/静态shape单独设置format，统一使用Format接口来设置即可。定义算子参数数据格式。废弃卡明确把 UnknownShapeFormat 的职责迁移到 Format，目标卡定义承接后的参数格式设置合同；替换后还能消除 deprecated 警告在严格编译选项下升级为错误的风险。
<!-- cannbot:related:end -->
