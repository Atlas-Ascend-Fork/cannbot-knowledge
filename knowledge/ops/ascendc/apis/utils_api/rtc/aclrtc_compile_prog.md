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

- [编译与执行RTC](../../../guides/programming_guide/compilation_and_execution/operator_compilation/rtc_runtime_compilation.md)（`explains`）：“aclrtcCompileProg：编译给定的程序，支持用户自定义编译选项”定位 RTC 编译步骤，“options 为编译选项数组（默认添加 -std=c++17）”明确选项参数及默认行为。
- [aclrtcCreateProg](aclrtc_create_prog.md)（`related`）：“通过给定参数创建编译程序实例。函数签名为 aclError aclrtcCreateProg(aclrtcProg* prog, const char* src, const char* name, int numHeaders, const char** headers, const char** includeNames)。”生产 RTC 程序句柄；“参数 prog 为运行时编译程序句柄，numOptions 为编译选项数量，options 为编译选项数组（默认添加 -std=c++17）。”说明 CompileProg 消费该句柄，形成创建后编译的生命周期链。
- [aclrtcAddNameExpr](aclrtc_add_name_expr.md)（`same_topic`）：该接口需要在aclrtcCompileProg编译接口前使用。编译接口，编译指定的程序。函数签名为 aclError aclrtcCompileProg(aclrtcProg prog, int numOptions, const char** options)。名称表达式卡规定注册时序，编译卡给出消耗同一 `aclrtcProg` 句柄的编译入口；模板 `__global__` 函数若需 lowered name，必须先注册表达式再执行编译。
<!-- cannbot:related:end -->
