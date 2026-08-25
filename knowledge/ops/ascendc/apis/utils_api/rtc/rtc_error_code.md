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

<!-- cannbot:related:start -->
## 相关

- [调用算子时出现无法打开config.ini的报错](../../../guides/programming_guide/appendix/faq/config_ini_open_error.md)（`explains`）：调用算子时出现无法打开config.ini的报错 与《RTC错误码（RTC运行时编译）》的实质衔接是：config.ini 打开失败要沿文件名、权限、架构配置和构建/调试工具链排查；所保留卡均提供具体检查或恢复动作。
- [aclrtcCompileProg](aclrtc_compile_prog.md)（`related`）：aclrtcCompileProg 返回 ACL_ERROR_RTC_INVALID_OPTION、COMPILATION 等错误码，错误码卡提供从返回值到编译阶段根因的映射。
- [aclrtcCreateProg](aclrtc_create_prog.md)（`related`）：《aclrtcCreateProg》处理“通过给定的参数，创建编译程序的实例。”。《RTC错误码（RTC运行时编译）》明确提供“汇总 aclrtc 运行时编译接口返回的 aclError 错误码及其含义。”，其参数、调用或验证步骤直接接入RTC Kernel 创建、编译、函数获取、launch 和销毁生命周期。
- [aclrtcGetCompileLog](aclrtc_get_compile_log.md)（`related`）：遇到 RTC 编译错误码后可按同一 prog 句柄读取日志内容，进一步定位 176003 等编译失败。
<!-- cannbot:related:end -->
