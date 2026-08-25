---
type: Guide
title: 附录
description: aclnn算子开发附录，包含命名转换规则、cmake函数参考与外部样例链接。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/aclnn_operator_development/appendix/appendix.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# 附录

aclnn算子开发附录，提供三部分参考内容。命名转换规则对照表：aclnn接口命名与Ascend C底层命名之间的映射关系，帮助开发者理解接口层次和命名规范，便于在aclnn接口与底层Ascend C接口之间进行对照查找。cmake函数参考：算子工程构建相关的CMake函数说明，包括编译选项配置、链接库设置、目标平台选择等，支撑算子工程的自动化构建。外部样例链接汇总：官方提供的算子开发示例代码链接，涵盖常见算子类型的完整实现参考。

<!-- cannbot:related:start -->
## 相关

- [CMake函数参考（附录）](cmake_function_reference.md)（`related`）：CMake 参考给出算子工程编译、链接和目标平台配置函数，是附录所承诺的构建查询入口。
- [命名转换规则对照表（附录）](naming_conversion_table.md)（`related`）：命名表具体展开 aclnn 接口名、OpType、文件名和 Kernel 入口之间的转换规则。
- [外部样例链接汇总（附录）](external_sample_links.md)（`related`）：外部样例汇总提供各开发步骤对应的完整代码落点，用于从规则查阅转入可运行示例。
<!-- cannbot:related:end -->
