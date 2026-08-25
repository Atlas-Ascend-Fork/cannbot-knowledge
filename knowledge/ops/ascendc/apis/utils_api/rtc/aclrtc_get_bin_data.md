---
type: API
title: aclrtcGetBinData
description: 获取编译后的二进制数据。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/RTC/aclrtcGetBinData.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# aclrtcGetBinData

获取编译后的 Device 侧二进制数据。函数签名为 aclError aclrtcGetBinData(aclrtcProg prog, char* binData)。
参数 prog 为输入，指定运行时编译程序句柄；binData 为输出，保存编译得到的二进制数据。
调用前应先通过 aclrtcGetBinDataSize 获取二进制数据大小，并据此分配足够的内存空间。
返回值为 aclError（int 类型），详细错误码参考 RTC 错误码文档。
支持 Ascend 950PR/950DT、Atlas A2 与 Atlas A3 系列产品。

<!-- cannbot:related:start -->
## 相关

- [编译与执行RTC](../../../guides/programming_guide/compilation_and_execution/operator_compilation/rtc_runtime_compilation.md)（`explains`）：指南随后取出 Device 二进制并交给 Runtime 加载；接口卡明确调用前必须先按查询大小分配空间。
- [RTC简介（RTC运行时编译）](rtc_intro.md)（`related`）：编译后必须先查询大小并由 aclrtcGetBinData 取出 Device 二进制，才能交给 runtime load；它连接 RTC 编译与执行阶段。
- [aclrtcCompileProg](aclrtc_compile_prog.md)（`related`）：只有 aclrtcCompileProg 成功编译 prog 句柄后才存在可由 GetBinData/Size 读取的 Device 二进制。
- [aclrtcCreateProg](aclrtc_create_prog.md)（`same_topic`）：《aclrtcCreateProg》处理“通过给定的参数，创建编译程序的实例。”。《aclrtcGetBinData》明确提供“获取编译后的二进制数据。”，其参数、调用或验证步骤直接接入RTC Kernel 创建、编译、函数获取、launch 和销毁生命周期。
- [aclrtcGetBinDataSize](aclrtc_get_bin_data_size.md)（`same_topic`）：《aclrtcGetBinDataSize》处理“获取编译的二进制数据大小。用于在aclrtcGetBinData获取二进制数据时分配对应大小的内存空间。”。《aclrtcGetBinData》提供“获取编译后的二进制数据。”，其具体合同或探针直接接入RTC 二进制大小查询、数据读取和 create/compile/destroy 生命周期。
<!-- cannbot:related:end -->
