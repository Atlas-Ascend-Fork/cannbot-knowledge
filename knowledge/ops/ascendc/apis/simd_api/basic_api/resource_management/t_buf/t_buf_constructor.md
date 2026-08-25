---
type: API
title: TBufConstructor
description: 创建TBuf对象时，初始化数据成员。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TBuf/TBuf_constructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# TBufConstructor

头文件路径为："basic_api/kernel_tpipe.h"。

创建TBuf对象时，初始化数据成员。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [Get](get.md)（`related`）：构造并分配 TBuf 后通过 Get 取得 LocalTensor；构造是该访问链的前置步骤。
- [InitBuffer](../t_buf_pool/init_buffer.md)（`related`）：TBuf 构造本身不分配容量，需由 InitBuffer 指定块大小后 Get 才可安全使用。
- [GetWithOffset](get_with_offset.md)（`same_topic`）：GetWithOffset 与《TBufConstructor》的实质衔接是：GetWithOffset 在 TBuf::Get 基础上增加 offset；TBuf 初始化长度、32B 对齐和重叠地址案例共同决定 size*sizeof(T)+offset 的合法范围。
- [TBuf简介](t_buf_intro.md)（`same_topic`）：TBuf简介 与《TBufConstructor》的实质衔接是：TBuf 的构造、InitBuffer、Get/GetWithOffset 共同定义 UB 临时缓冲的分配与类型化取用；所连案例分别验证参数签名、地址独立性、容量预算和 helper 传参约束。
<!-- cannbot:related:end -->
