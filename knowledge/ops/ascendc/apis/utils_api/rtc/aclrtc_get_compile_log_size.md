---
type: API
title: aclrtcGetCompileLogSize
description: 获取编译日志的大小。用于在aclrtcGetCompileLog获取日志内容时分配对应大小的内存空间。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/RTC/aclrtcGetCompileLogSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# aclrtcGetCompileLogSize

获取编译日志大小，用于在调用 aclrtcGetCompileLog 前分配对应大小的内存空间。
函数签名为 aclError aclrtcGetCompileLogSize(aclrtcProg prog, size_t* logSizeRet)。
参数 prog 为输入，指定运行时编译程序句柄；logSizeRet 为输出，返回编译日志长度。
返回值为 aclError（int 类型），详细错误码参考 RTC 错误码文档。
典型用法：先调用本接口获取大小，再 malloc 对应大小的缓冲区，最后调用 aclrtcGetCompileLog 填充日志内容。
支持 Ascend 950PR/950DT、Atlas A2 与 Atlas A3 系列产品。

<!-- cannbot:related:start -->
## 相关

- [编译与执行RTC](../../../guides/programming_guide/compilation_and_execution/operator_compilation/rtc_runtime_compilation.md)（`explains`）：RTC 指南给出 create/compile/log/bin/launch 生命周期，能把孤立的日志大小 API 放入错误处理和资源释放流程。
- [高级编程交叉编译](../../../guides/programming_guide/advanced_programming/aclnn_operator_development/compilation_and_deployment/cross_compilation.md)（`explains`）：高级编程交叉编译 与《aclrtcGetCompileLogSize》的实质衔接是：交叉编译需先生成本机 tiling 库再构建目标包；基本编译、CMake、runtime、compiler/RTC/compile-log 接口共同支撑配置和诊断。
- [aclrtcCompileProg](aclrtc_compile_prog.md)（`related`）：aclrtcCompileProg 产生编译结果和诊断，日志大小查询只能在该编译工作流中用于读取错误/警告信息。
- [aclrtcCreateProg](aclrtc_create_prog.md)（`related`）：《aclrtcCreateProg》处理“通过给定的参数，创建编译程序的实例。”。《aclrtcGetCompileLogSize》明确提供“获取编译日志的大小。用于在aclrtcGetCompileLog获取日志内容时分配对应大小的内存空间。”，其参数、调用或验证步骤直接接入RTC Kernel 创建、编译、函数获取、launch 和销毁生命周期。
- [aclrtcGetCompileLog](aclrtc_get_compile_log.md)（`same_topic`）：aclrtcGetCompileLogSize 先返回日志长度供分配缓冲，aclrtcGetCompileLog 随后把同一 prog 的日志写入该缓冲；二者是固定两步读取协议。
<!-- cannbot:related:end -->
