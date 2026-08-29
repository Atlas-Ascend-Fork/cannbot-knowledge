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

- [aclrtcGetCompileLogSize](aclrtc_get_compile_log_size.md)（`related`）：调用前应先通过 aclrtcGetCompileLogSize 获取日志大小，并据此分配足够的内存空间。；典型用法：先调用本接口获取大小，再 malloc 对应大小的缓冲区，最后调用 aclrtcGetCompileLog 填充日志内容。。两端规定编译日志读取任务的先后顺序：先查询字节数并分配缓冲，再取得日志正文；容量查询和内容读取是不同接口动作。
<!-- cannbot:related:end -->
