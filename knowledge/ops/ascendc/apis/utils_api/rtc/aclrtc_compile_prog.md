---
type: API
title: aclrtcCompileProg
description: 编译接口，编译指定的程序。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/RTC/aclrtcCompileProg.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# aclrtcCompileProg

编译接口，编译指定的程序。函数签名为 aclError aclrtcCompileProg(aclrtcProg prog, int numOptions, const char** options)。
参数 prog 为运行时编译程序句柄，numOptions 为编译选项数量，options 为编译选项数组（默认添加 -std=c++17）。
支持的编译选项可参考毕昇编译器用户指南，如 --npu-arch 用于指定目标硬件架构。
返回值为 aclError（int 类型），详细错误码参考 RTC 错误码文档。
支持 Ascend 950PR/950DT、Atlas A2 与 Atlas A3 系列产品，Atlas 200I/500 A2 推理产品、Atlas 推理系列产品与 Atlas 训练系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [编译与执行RTC](../../../guides/programming_guide/compilation_and_execution/operator_compilation/rtc_runtime_compilation.md)（`explains`）：指南的核心编译步骤调用 aclrtcCompileProg，并举出 --npu-arch 等选项；接口卡给出 options 数组与句柄契约。
- [高级编程交叉编译](../../../guides/programming_guide/advanced_programming/aclnn_operator_development/compilation_and_deployment/cross_compilation.md)（`explains`）：高级编程交叉编译 与《aclrtcCompileProg》的实质衔接是：交叉编译需先生成本机 tiling 库再构建目标包；基本编译、CMake、runtime、compiler/RTC/compile-log 接口共同支撑配置和诊断。
- [RTC简介（RTC运行时编译）](rtc_intro.md)（`related`）：aclrtcCompileProg 消费已创建的 aclrtcProg，并用 --npu-arch 等选项产生目标机器码，是 RTC intro 所述运行时编译的核心执行步骤。
- [RTC错误码（RTC运行时编译）](rtc_error_code.md)（`related`）：aclrtcCompileProg 返回 ACL_ERROR_RTC_INVALID_OPTION、COMPILATION 等错误码，错误码卡提供从返回值到编译阶段根因的映射。
- [aclrtcAddNameExpr](aclrtc_add_name_expr.md)（`related`）：aclrtcAddNameExpr 必须在 aclrtcCompileProg 前调用，编译完成后才能为已注册模板 kernel 解析 lowered name。
- [aclrtcDestroyProg](aclrtc_destroy_prog.md)（`related`）：《aclrtcDestroyProg》明确“销毁运行时编译程序的实例。”；它与《aclrtcCompileProg》的“编译接口，编译指定的程序。”在实际调用参数、数据流或结果校验上直接衔接。
- [aclrtcGetBinData](aclrtc_get_bin_data.md)（`related`）：只有 aclrtcCompileProg 成功编译 prog 句柄后才存在可由 GetBinData/Size 读取的 Device 二进制。
- [aclrtcGetCompileLog](aclrtc_get_compile_log.md)（`related`）：《aclrtcGetCompileLog》明确“获取编译日志的内容，以字符串形式保存。”；它与《aclrtcCompileProg》的“编译接口，编译指定的程序。”在实际调用参数、数据流或结果校验上直接衔接。
- [aclrtcGetCompileLogSize](aclrtc_get_compile_log_size.md)（`related`）：aclrtcCompileProg 产生编译结果和诊断，日志大小查询只能在该编译工作流中用于读取错误/警告信息。
- [aclrtcCreateProg](aclrtc_create_prog.md)（`same_topic`）：《aclrtcCreateProg》处理“通过给定的参数，创建编译程序的实例。”。《aclrtcCompileProg》明确提供“编译接口，编译指定的程序。”，其参数、调用或验证步骤直接接入RTC Kernel 创建、编译、函数获取、launch 和销毁生命周期。
- [aclrtcGetBinDataSize](aclrtc_get_bin_data_size.md)（`same_topic`）：《aclrtcGetBinDataSize》处理“获取编译的二进制数据大小。用于在aclrtcGetBinData获取二进制数据时分配对应大小的内存空间。”。《aclrtcCompileProg》提供“编译接口，编译指定的程序。”，其具体合同或探针直接接入RTC 二进制大小查询、数据读取和 create/compile/destroy 生命周期。
- [aclrtcGetLoweredName](aclrtc_get_lowered_name.md)（`same_topic`）：《aclrtcGetLoweredName》处理“获取已经注册的__global__函数的mangling name。”。《aclrtcCompileProg》明确“编译接口，编译指定的程序。”，可直接用于核对RTC name expression 到 lowered symbol 的 create/compile/query/destroy 生命周期。
<!-- cannbot:related:end -->
