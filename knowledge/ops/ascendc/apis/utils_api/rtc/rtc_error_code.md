---
type: API
title: RTC错误码（RTC运行时编译）
description: 汇总 aclrtc 运行时编译接口返回的 aclError 错误码及其含义。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/RTC/RTC_error_code.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# RTC错误码

aclrtc接口返回的aclError错误码定义。主要错误码：ACL_SUCCESS(0)执行成功；ACL_ERROR_RTC_INVALID_PROG(176000)无效的aclrtcProg句柄；ACL_ERROR_RTC_INVALID_INPUT(176001)入参错误；ACL_ERROR_RTC_INVALID_OPTION(176002)编译选项错误；ACL_ERROR_RTC_COMPILATION(176003)编译报错；ACL_ERROR_RTC_LINKING(176004)链接报错；ACL_ERROR_RTC_PROG_CREATION_FAILURE(276000)创建Prog失败；ACL_ERROR_RTC_OUT_OF_MEMORY(276001)内存不足；ACL_ERROR_RTC_FAILURE(576000)RTC内部错误。开发者应根据错误码值定位RTC编译和执行问题。
