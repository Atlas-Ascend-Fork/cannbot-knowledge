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
