---
type: API
title: TBuf
description: TBuf接口索引页，包含简介、构造函数、Get与GetWithOffset。
tags: [task.lookup, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TBuf/TBuf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# TBuf

TBuf 接口集合，用于管理 AscendC 片上 Buffer。通过构造函数创建实例，配合 TPipe::InitBuffer 分配内存；Get 获取指定类型的 LocalTensor；GetWithOffset 获取带偏移的 LocalTensor，支持从一个 TBuf 中切分多段使用。TBuf 不含 Queue 语义，适用于无需队列管理的纯 buffer 场景。

<!-- cannbot:related:start -->
## 相关

- [InitOutput GM 专用，UB 清零用 Duplicate](../../../../../runbooks/compilation/initoutput_gm_ub_duplicate.md)（`exemplifies`）：InitOutput GM 专用，UB 清零用 Duplicate 与《TBuf》的实质衔接是：InitOutput 只接受 GM GlobalTensor，而 UB LocalTensor 要用 Duplicate；相关 API、类型错误、TBuf 取 LocalTensor 和清零覆盖故障直接验证该边界。
- [SIMT __ubuf__ 静态数组 UB 占用不随分支释放](../../../../../runbooks/compilation/simt_ubuf_ub.md)（`exemplifies`）：《SIMT __ubuf__ 静态数组 UB 占用不随分支释放》说明SIMT kernel 的 __ubuf__ 静态数组是编译期分配、生命周期绑所在函数栈的 UB 资源，运行时分支只控制是否解引用、不控制是否占用；把“需要该数组”与“不需要该数组”两条路径塞进同一函数，会令不解引用的路径也白白占住 UB。给出按解引用关系拆函数的判别方法。；《TBuf》说明TBuf接口索引页，包含简介、构造函数、Get与GetWithOffset。。二者在SIMT静态__ubuf__数组按函数栈常驻，地址空间限定、UB预算及TBuf管理方案直接决定如何拆函数或改为受管内存上存在可执行的直接衔接。
- [TBuf的使用](../../../../../guides/operator_practice/simd_operator_impl/vector_programming/tbuf_usage.md)（`explains`）：TBuf API 定义 Get 获得 LocalTensor 和缓冲生命周期，正是指南样例管理 Cast/Add 中间结果的底层契约。
- [TBuf简介](t_buf_intro.md)（`same_topic`）：TBuf简介 与《TBuf》的实质衔接是：TBuf 的构造、InitBuffer、Get/GetWithOffset 共同定义 UB 临时缓冲的分配与类型化取用；所连案例分别验证参数签名、地址独立性、容量预算和 helper 传参约束。
<!-- cannbot:related:end -->
