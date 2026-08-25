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

<!-- cannbot:related:start -->
## 相关

- [编译与执行RTC](../../../guides/programming_guide/compilation_and_execution/operator_compilation/rtc_runtime_compilation.md)（`explains`）：《aclrtcCreateProg》处理“通过给定的参数，创建编译程序的实例。”。《编译与执行RTC》明确提供“RTC是Ascend C运行时编译库，通过aclrtc接口，在程序运行时，将中间代码动态编译成目标机器码，提升程序运行性能。”，其参数、调用或验证步骤直接接入RTC Kernel 创建、编译、函数获取、launch 和销毁生命周期。
- [RTC简介（RTC运行时编译）](rtc_intro.md)（`related`）：《aclrtcCreateProg》处理“通过给定的参数，创建编译程序的实例。”。《RTC简介（RTC运行时编译）》明确提供“RTC是Ascend C运行时编译库，通过aclrtc接口，在程序运行时，将中间代码动态编译成目标机器码，提升程序运行性能。开发指导请参考RTC。”，其参数、调用或验证步骤直接接入RTC Kernel 创建、编译、函数获取、launch 和销毁生命周期。
- [RTC错误码（RTC运行时编译）](rtc_error_code.md)（`related`）：《aclrtcCreateProg》处理“通过给定的参数，创建编译程序的实例。”。《RTC错误码（RTC运行时编译）》明确提供“汇总 aclrtc 运行时编译接口返回的 aclError 错误码及其含义。”，其参数、调用或验证步骤直接接入RTC Kernel 创建、编译、函数获取、launch 和销毁生命周期。
- [aclrtcAddNameExpr](aclrtc_add_name_expr.md)（`related`）：《aclrtcCreateProg》处理“通过给定的参数，创建编译程序的实例。”。《aclrtcAddNameExpr》明确提供“注册指定的名称表达式，该表达式代表了一个__global__函数。 主要用于__global__函数为模板函数的场景，调用本接口后，可以通过aclrtcGetLoweredName接口获取函数的mangling name，在launch阶段调用对应的模板__global__函数。”，其参数、调用或验证步骤直接接入RTC Kernel 创建、编译、函数获取、launch 和销毁生命周期。
- [aclrtcGetBinDataSize](aclrtc_get_bin_data_size.md)（`related`）：《aclrtcCreateProg》处理“通过给定的参数，创建编译程序的实例。”。《aclrtcGetBinDataSize》明确提供“获取编译的二进制数据大小。用于在aclrtcGetBinData获取二进制数据时分配对应大小的内存空间。”，其参数、调用或验证步骤直接接入RTC Kernel 创建、编译、函数获取、launch 和销毁生命周期。
- [aclrtcGetCompileLog](aclrtc_get_compile_log.md)（`related`）：《aclrtcCreateProg》处理“通过给定的参数，创建编译程序的实例。”。《aclrtcGetCompileLog》明确提供“获取编译日志的内容，以字符串形式保存。”，其参数、调用或验证步骤直接接入RTC Kernel 创建、编译、函数获取、launch 和销毁生命周期。
- [aclrtcGetCompileLogSize](aclrtc_get_compile_log_size.md)（`related`）：《aclrtcCreateProg》处理“通过给定的参数，创建编译程序的实例。”。《aclrtcGetCompileLogSize》明确提供“获取编译日志的大小。用于在aclrtcGetCompileLog获取日志内容时分配对应大小的内存空间。”，其参数、调用或验证步骤直接接入RTC Kernel 创建、编译、函数获取、launch 和销毁生命周期。
- [aclrtcGetLoweredName](aclrtc_get_lowered_name.md)（`related`）：《aclrtcCreateProg》处理“通过给定的参数，创建编译程序的实例。”。《aclrtcGetLoweredName》明确提供“获取已经注册的__global__函数的mangling name。”，其参数、调用或验证步骤直接接入RTC Kernel 创建、编译、函数获取、launch 和销毁生命周期。
- [aclrtcCompileProg](aclrtc_compile_prog.md)（`same_topic`）：《aclrtcCreateProg》处理“通过给定的参数，创建编译程序的实例。”。《aclrtcCompileProg》明确提供“编译接口，编译指定的程序。”，其参数、调用或验证步骤直接接入RTC Kernel 创建、编译、函数获取、launch 和销毁生命周期。
- [aclrtcDestroyProg](aclrtc_destroy_prog.md)（`same_topic`）：《aclrtcCreateProg》处理“通过给定的参数，创建编译程序的实例。”。《aclrtcDestroyProg》明确提供“销毁运行时编译程序的实例。”，其参数、调用或验证步骤直接接入RTC Kernel 创建、编译、函数获取、launch 和销毁生命周期。
- [aclrtcGetBinData](aclrtc_get_bin_data.md)（`same_topic`）：《aclrtcCreateProg》处理“通过给定的参数，创建编译程序的实例。”。《aclrtcGetBinData》明确提供“获取编译后的二进制数据。”，其参数、调用或验证步骤直接接入RTC Kernel 创建、编译、函数获取、launch 和销毁生命周期。
<!-- cannbot:related:end -->
