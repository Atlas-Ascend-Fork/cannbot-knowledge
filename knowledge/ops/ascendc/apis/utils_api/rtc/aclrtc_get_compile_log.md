---
type: API
title: aclrtcGetCompileLog
description: 获取编译日志的内容，以字符串形式保存。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/RTC/aclrtcGetCompileLog.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# aclrtcGetCompileLog

获取编译日志内容，以字符串形式保存。函数签名为 aclError aclrtcGetCompileLog(aclrtcProg prog, char* log)。
参数 prog 为输入，指定运行时编译程序句柄；log 为输出，保存编译日志字符串。
调用前应先通过 aclrtcGetCompileLogSize 获取日志大小，并据此分配足够的内存空间。
返回值为 aclError（int 类型），详细错误码参考 RTC 错误码文档。
支持 Ascend 950PR/950DT、Atlas A2 与 Atlas A3 系列产品。

<!-- cannbot:related:start -->
## 相关

- [高级编程交叉编译](../../../guides/programming_guide/advanced_programming/aclnn_operator_development/compilation_and_deployment/cross_compilation.md)（`explains`）：高级编程交叉编译 与《aclrtcGetCompileLog》的实质衔接是：交叉编译需先生成本机 tiling 库再构建目标包；基本编译、CMake、runtime、compiler/RTC/compile-log 接口共同支撑配置和诊断。
- [RTC错误码（RTC运行时编译）](rtc_error_code.md)（`related`）：遇到 RTC 编译错误码后可按同一 prog 句柄读取日志内容，进一步定位 176003 等编译失败。
- [aclrtcCompileProg](aclrtc_compile_prog.md)（`related`）：《aclrtcGetCompileLog》明确“获取编译日志的内容，以字符串形式保存。”；它与《aclrtcCompileProg》的“编译接口，编译指定的程序。”在实际调用参数、数据流或结果校验上直接衔接。
- [aclrtcCreateProg](aclrtc_create_prog.md)（`related`）：《aclrtcCreateProg》处理“通过给定的参数，创建编译程序的实例。”。《aclrtcGetCompileLog》明确提供“获取编译日志的内容，以字符串形式保存。”，其参数、调用或验证步骤直接接入RTC Kernel 创建、编译、函数获取、launch 和销毁生命周期。
- [aclrtcGetCompileLogSize](aclrtc_get_compile_log_size.md)（`same_topic`）：aclrtcGetCompileLogSize 先返回日志长度供分配缓冲，aclrtcGetCompileLog 随后把同一 prog 的日志写入该缓冲；二者是固定两步读取协议。
<!-- cannbot:related:end -->
