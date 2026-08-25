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
