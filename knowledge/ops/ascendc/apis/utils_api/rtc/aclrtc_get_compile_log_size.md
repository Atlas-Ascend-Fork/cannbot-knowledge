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

- [aclrtcGetCompileLog](aclrtc_get_compile_log.md)（`related`）：调用前应先通过 aclrtcGetCompileLogSize 获取日志大小，并据此分配足够的内存空间。；典型用法：先调用本接口获取大小，再 malloc 对应大小的缓冲区，最后调用 aclrtcGetCompileLog 填充日志内容。。两端规定编译日志读取任务的先后顺序：先查询字节数并分配缓冲，再取得日志正文；容量查询和内容读取是不同接口动作。
<!-- cannbot:related:end -->
