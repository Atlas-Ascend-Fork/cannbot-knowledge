---
type: Guide
title: 算子工程编译时出现文件名过长报错
description: 工程化算子开发场景，在进行算子工程编译时，提示以下报错信息中的一种：
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/appendix/faq/filename_too_long_error.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 算子工程编译时出现文件名过长报错

## 现象描述
工程化算子开发场景，在进行算子工程编译时，提示以下报错信息中的一种：
-   file name is too long (cannot be split); not dumped
-   file name is too long (max 256); not dumped
## 问题根因
在构建过程中，由于文件名或路径长度超出系统限制，使用tar命令打包算子工程生成的文件时发生了错误。
## 定位步骤
出现此类报错，需要根据提示的报错信息（通常包含超长的文件名或者路径），减少对应的文件名长度或路径长度。
下面列出了常见错误的解决方案：
-   文件名过长报错
-   位于算子工程op_kernel目录下的kernel侧代码和位于op_host目录下的host侧代码等文件，文件名是根据创建算子工程时传入的算子OpType自动生成的。如果因为此类文件名过长报错，应减少OpType的长度。
-   使用Comment接口设置算子分组名称后，会对应生成同名的供GE调用的原型定义代码文件。如果因为此类文件导致文件名过长报错，应减少算子分组名称的长度。
-   文件路径过长报错
完成工程编译相关配置时，如果在CMakePresets.json文件中配置vendor_name，编译时会在vendor目录下生成以vendor_name为名称的路径。如果因为此类文件路径过长报错，应减少配置的vendor_name长度。

<!-- cannbot:related:start -->
## 相关

- [Comment](../../../../apis/utils_api/prototype_register_management/op_def/comment.md)（`explains`）：FAQ 指出 Comment 设置的算子分组名会生成同名原型文件；OpDef::Comment 是该分组和注释配置入口。
- [命名转换规则对照表（附录）](../../advanced_programming/aclnn_operator_development/appendix/naming_conversion_table.md)（`same_topic`）：FAQ 指出过长 OpType 会生成过长 host/kernel 文件名；命名转换表明确构建期如何从 OpType 派生文件名，可在改名前预估最终长度。
<!-- cannbot:related:end -->
