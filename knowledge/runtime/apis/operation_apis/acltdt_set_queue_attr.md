---
type: API
title: acltdtSetQueueAttr
description: "向队列属性配置对象写入指定类型的属性值，供创建队列使用；len 须匹配整数或指针类型大小。"
tags:
- task.lookup
- topic.implementation
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/25-03_Operation_APIs.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_tdt_queue.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/acl_tdt_queue/queue.cpp
  role: implementation
source_headers:
- include/external/acl/acl_tdt_queue.h
created_at: '2026-09-15T00:00:00Z'
updated_at: "2026-10-30T08:26:15Z"
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---

# acltdtSetQueueAttr

## 功能说明

设置队列属性值。

## 函数原型

```c
aclError acltdtSetQueueAttr(acltdtQueueAttr *attr, acltdtQueueAttrType type, size_t len, const void *param)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | :---: | --- |
| attr | 输入&输出 | 队列属性配置信息的指针。<br>需提前调用[acltdtCreateQueueAttr](acltdt_create_queue_attr.md)接口创建acltdtQueueAttr类型的数据。 |
| type | 输入 | 属性类型。类型定义请参见acltdtQueueAttrType。 |
| len | 输入 | 属性值的字节数。<br><br>  - type取值的枚举名以_UINT64结尾时，此处配置为8；<br>  - type取值的枚举名以_UINT32结尾时，此处配置为4；<br>  - type取值的枚举名以_PTR结尾时，若操作系统是32位，则此处配置为4；若操作系统是64位，则配置为8。 |
| param | 输入 | 指向属性值的指针。 |

## 返回值说明

返回0表示成功，返回其他值表示失败，请参见aclError。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/tdt_queue/0_simple_queue/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/tdt_queue/0_simple_queue/main.cpp#L42)
- [`2_advanced_features/tdt_queue/1_queue_route/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/tdt_queue/1_queue_route/main.cpp#L49)
