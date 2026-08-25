---
type: API
title: aclrtcDestroyProg
description: 销毁运行时编译程序的实例。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/RTC/aclrtcDestroyProg.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# aclrtcDestroyProg

销毁运行时编译程序实例，释放资源。函数签名为 aclError aclrtcDestroyProg(aclrtcProg* prog)。
参数 prog 为输入，指定待销毁的运行时编译程序句柄。
返回值为 aclError（int 类型），详细错误码参考 RTC 错误码文档。
调用后不应再使用已销毁的 prog 句柄。
支持 Ascend 950PR/950DT、Atlas A2 与 Atlas A3 系列产品。

<!-- cannbot:related:start -->
## 相关

- [编译与执行RTC](../../../guides/programming_guide/compilation_and_execution/operator_compilation/rtc_runtime_compilation.md)（`explains`）：RTC 指南把 DestroyProg 放在创建、可选名称注册、编译、取二进制、加载执行之后，说明正确销毁时机和完整生命周期。
- [aclrtcCompileProg](aclrtc_compile_prog.md)（`related`）：《aclrtcDestroyProg》明确“销毁运行时编译程序的实例。”；它与《aclrtcCompileProg》的“编译接口，编译指定的程序。”在实际调用参数、数据流或结果校验上直接衔接。
- [aclrtcCreateProg](aclrtc_create_prog.md)（`same_topic`）：《aclrtcCreateProg》处理“通过给定的参数，创建编译程序的实例。”。《aclrtcDestroyProg》明确提供“销毁运行时编译程序的实例。”，其参数、调用或验证步骤直接接入RTC Kernel 创建、编译、函数获取、launch 和销毁生命周期。
- [aclrtcGetBinDataSize](aclrtc_get_bin_data_size.md)（`same_topic`）：《aclrtcGetBinDataSize》处理“获取编译的二进制数据大小。用于在aclrtcGetBinData获取二进制数据时分配对应大小的内存空间。”。《aclrtcDestroyProg》提供“销毁运行时编译程序的实例。”，其具体合同或探针直接接入RTC 二进制大小查询、数据读取和 create/compile/destroy 生命周期。
- [aclrtcGetLoweredName](aclrtc_get_lowered_name.md)（`same_topic`）：《aclrtcGetLoweredName》处理“获取已经注册的__global__函数的mangling name。”。《aclrtcDestroyProg》明确“销毁运行时编译程序的实例。”，可直接用于核对RTC name expression 到 lowered symbol 的 create/compile/query/destroy 生命周期。
<!-- cannbot:related:end -->
