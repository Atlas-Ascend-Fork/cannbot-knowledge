---
type: API
title: aclrtcGetLoweredName
description: 获取已经注册的__global__函数的mangling name。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/RTC/aclrtcGetLoweredName.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# aclrtcGetLoweredName

## 功能说明
获取已经注册的__global__函数的mangling name。
## 函数原型
## 参数说明
接口参数说明
## 返回值说明
aclError为int类型变量，详细说明请参考RTC错误码。
## 约束说明
使用前必须先通过aclrtcAddNameExpr注册原始名称，且两次传入的nameExpression字符串必须完全相同。

<!-- cannbot:related:start -->
## 相关

- [__global__ 核函数 extern C 失效致符号未定义](../../../runbooks/compilation/global_vector_stub_ignores_extern_c_mangled_name.md)（`exemplifies`）：《aclrtcGetLoweredName》处理“获取已经注册的__global__函数的mangling name。”。《__global__ 核函数 extern C 失效致符号未定义》明确“ASC 编译器对 __global__ __vector__ 核函数忽略 extern "C"，host 侧 stub 以 C++ mangled 名链接；torch 侧 extern "C" 声明找不到符号，加载 .so 报 undefined symbol。用 nm -D 判别后改 C++ linkage 修复。”，可直接用于核对RTC name expression 到 lowered symbol 的 create/compile/query/destroy 生命周期。
- [编译与执行RTC](../../../guides/programming_guide/compilation_and_execution/operator_compilation/rtc_runtime_compilation.md)（`explains`）：《aclrtcGetLoweredName》处理“获取已经注册的__global__函数的mangling name。”。《编译与执行RTC》明确“RTC是Ascend C运行时编译库，通过aclrtc接口，在程序运行时，将中间代码动态编译成目标机器码，提升程序运行性能。”，可直接用于核对RTC name expression 到 lowered symbol 的 create/compile/query/destroy 生命周期。
- [RTC简介（RTC运行时编译）](rtc_intro.md)（`related`）：《aclrtcGetLoweredName》处理“获取已经注册的__global__函数的mangling name。”。《RTC简介（RTC运行时编译）》明确“RTC是Ascend C运行时编译库，通过aclrtc接口，在程序运行时，将中间代码动态编译成目标机器码，提升程序运行性能。开发指导请参考RTC。”，可直接用于核对RTC name expression 到 lowered symbol 的 create/compile/query/destroy 生命周期。
- [aclrtcCreateProg](aclrtc_create_prog.md)（`related`）：《aclrtcCreateProg》处理“通过给定的参数，创建编译程序的实例。”。《aclrtcGetLoweredName》明确提供“获取已经注册的__global__函数的mangling name。”，其参数、调用或验证步骤直接接入RTC Kernel 创建、编译、函数获取、launch 和销毁生命周期。
- [aclrtcAddNameExpr](aclrtc_add_name_expr.md)（`same_topic`）：《aclrtcGetLoweredName》处理“获取已经注册的__global__函数的mangling name。”。《aclrtcAddNameExpr》明确“注册指定的名称表达式，该表达式代表了一个__global__函数。 主要用于__global__函数为模板函数的场景，调用本接口后，可以通过aclrtcGetLoweredName接口获取函数的mangling name，在launch阶段调用对应的模板__global__函数。”，可直接用于核对RTC name expression 到 lowered symbol 的 create/compile/query/destroy 生命周期。
- [aclrtcCompileProg](aclrtc_compile_prog.md)（`same_topic`）：《aclrtcGetLoweredName》处理“获取已经注册的__global__函数的mangling name。”。《aclrtcCompileProg》明确“编译接口，编译指定的程序。”，可直接用于核对RTC name expression 到 lowered symbol 的 create/compile/query/destroy 生命周期。
- [aclrtcDestroyProg](aclrtc_destroy_prog.md)（`same_topic`）：《aclrtcGetLoweredName》处理“获取已经注册的__global__函数的mangling name。”。《aclrtcDestroyProg》明确“销毁运行时编译程序的实例。”，可直接用于核对RTC name expression 到 lowered symbol 的 create/compile/query/destroy 生命周期。
<!-- cannbot:related:end -->
