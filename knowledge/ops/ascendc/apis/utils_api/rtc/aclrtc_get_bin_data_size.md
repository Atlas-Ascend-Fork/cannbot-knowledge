---
type: API
title: aclrtcGetBinDataSize
description: 获取编译的二进制数据大小。用于在aclrtcGetBinData获取二进制数据时分配对应大小的内存空间。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/RTC/aclrtcGetBinDataSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# aclrtcGetBinDataSize

获取编译后的 Device 侧二进制数据大小，用于在调用 aclrtcGetBinData 前分配对应大小的内存空间。
函数签名为 aclError aclrtcGetBinDataSize(aclrtcProg prog, size_t* binDataSizeRet)。
参数 prog 为输入，指定运行时编译程序句柄；binDataSizeRet 为输出，返回二进制数据大小。
返回值为 aclError（int 类型），详细错误码参考 RTC 错误码文档。
典型用法：先调用本接口获取大小，再 malloc 对应大小的缓冲区，最后调用 aclrtcGetBinData 填充数据。
支持 Ascend 950PR/950DT、Atlas A2 与 Atlas A3 系列产品。

<!-- cannbot:related:start -->
## 相关

- [编译与执行RTC](../../../guides/programming_guide/compilation_and_execution/operator_compilation/rtc_runtime_compilation.md)（`explains`）：《aclrtcGetBinDataSize》处理“获取编译的二进制数据大小。用于在aclrtcGetBinData获取二进制数据时分配对应大小的内存空间。”。《编译与执行RTC》提供“RTC是Ascend C运行时编译库，通过aclrtc接口，在程序运行时，将中间代码动态编译成目标机器码，提升程序运行性能。”，其具体合同或探针直接接入RTC 二进制大小查询、数据读取和 create/compile/destroy 生命周期。
- [aclrtcCreateProg](aclrtc_create_prog.md)（`related`）：《aclrtcCreateProg》处理“通过给定的参数，创建编译程序的实例。”。《aclrtcGetBinDataSize》明确提供“获取编译的二进制数据大小。用于在aclrtcGetBinData获取二进制数据时分配对应大小的内存空间。”，其参数、调用或验证步骤直接接入RTC Kernel 创建、编译、函数获取、launch 和销毁生命周期。
- [aclrtcCompileProg](aclrtc_compile_prog.md)（`same_topic`）：《aclrtcGetBinDataSize》处理“获取编译的二进制数据大小。用于在aclrtcGetBinData获取二进制数据时分配对应大小的内存空间。”。《aclrtcCompileProg》提供“编译接口，编译指定的程序。”，其具体合同或探针直接接入RTC 二进制大小查询、数据读取和 create/compile/destroy 生命周期。
- [aclrtcDestroyProg](aclrtc_destroy_prog.md)（`same_topic`）：《aclrtcGetBinDataSize》处理“获取编译的二进制数据大小。用于在aclrtcGetBinData获取二进制数据时分配对应大小的内存空间。”。《aclrtcDestroyProg》提供“销毁运行时编译程序的实例。”，其具体合同或探针直接接入RTC 二进制大小查询、数据读取和 create/compile/destroy 生命周期。
- [aclrtcGetBinData](aclrtc_get_bin_data.md)（`same_topic`）：《aclrtcGetBinDataSize》处理“获取编译的二进制数据大小。用于在aclrtcGetBinData获取二进制数据时分配对应大小的内存空间。”。《aclrtcGetBinData》提供“获取编译后的二进制数据。”，其具体合同或探针直接接入RTC 二进制大小查询、数据读取和 create/compile/destroy 生命周期。
<!-- cannbot:related:end -->
