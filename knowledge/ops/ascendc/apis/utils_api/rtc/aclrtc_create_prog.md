---
type: API
title: aclrtcCreateProg
description: 通过给定的参数，创建编译程序的实例。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/RTC/aclrtcCreateProg.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# aclrtcCreateProg

通过给定参数创建编译程序实例。函数签名为 aclError aclrtcCreateProg(aclrtcProg* prog, const char* src, const char* name, int numHeaders, const char** headers, const char** includeNames)。
参数 prog 为输出，返回运行时编译程序句柄；src 为 Ascend C Device 侧源代码字符串；name 为程序名称，默认值为 default_program。
numHeaders 指定头文件数量（无需头文件时设为 0）；headers 为头文件源代码数组；includeNames 为头文件名称数组，需与源代码中 include 指令一致。
返回值为 aclError（int 类型），详细错误码参考 RTC 错误码文档。
支持 Ascend 950PR/950DT、Atlas A2 与 Atlas A3 系列产品。
