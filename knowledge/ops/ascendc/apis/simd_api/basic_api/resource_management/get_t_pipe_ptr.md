---
type: API
title: GetTPipePtr
description: 获取创建TPipe对象时设置的全局唯一TPipe指针，获取后可进行TPipe相关的操作如InitBuffer。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/GetTPipePtr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# GetTPipePtr

头文件路径为："basic_api/kernel_common.h"。

创建TPipe对象时，对象初始化会设置全局唯一的TPipe指针。本接口用于获取该指针，获取该指针后，可进行TPipe相关的操作。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [GetTPipePtr 错加 AscendC 命名空间导致编译失败](../../../../runbooks/compilation/gettpipeptr_is_global_function.md)（`exemplifies`）：GetTPipePtr：GetTPipePtr 返回当前 TPipe，全局命名空间 runbook直接修复其调用错误；TPipe与资源管理页解释返回对象及其生命周期。 目标卡《GetTPipePtr 错加 AscendC 命名空间导致编译失败》补充：Ascend C 事件 ID 初始化时，GetTPipePtr 是返回 AscendC::TPipe 指针的全局函数；误写为 AscendC::GetTPipePtr 会触发成员查找失败。
- [InitSpmBuffer](t_pipe/init_spm_buffer.md)（`related`）：InitSpmBuffer 与《GetTPipePtr》的实质衔接是：InitSpmBuffer 创建 GM 上的 SPM 溢出区，Read/WriteSpmBuffer 与 TPipe 生命周期共同构成初始化、访问和销毁链。
- [TPipe](t_pipe/t_pipe.md)（`related`）：GetTPipePtr：GetTPipePtr 返回当前 TPipe，全局命名空间 runbook直接修复其调用错误；TPipe与资源管理页解释返回对象及其生命周期。 目标卡《TPipe》补充：TPipe接口索引页，包含简介、构造函数、Init/Destroy、InitBuffer、事件ID管理及SpmBuffer读写等。
- [TPipe简介](t_pipe/t_pipe_intro.md)（`related`）：GetTPipePtr：GetTPipePtr 返回当前 TPipe，全局命名空间 runbook直接修复其调用错误；TPipe与资源管理页解释返回对象及其生命周期。 目标卡《TPipe简介》补充：TPipe用于统一管理Device端内存等资源，一个Kernel函数必须且只能初始化一个TPipe对象。其主要功能包括：
- [资源管理](resource_management.md)（`related`）：GetTPipePtr：GetTPipePtr 返回当前 TPipe，全局命名空间 runbook直接修复其调用错误；TPipe与资源管理页解释返回对象及其生命周期。 目标卡《资源管理》补充：资源管理API总览，涵盖TPipe、TBuf、TBufPool、TQue、TQueBind、TSCM、LocalMemAllocator及workspace等。
- [DestroyWithoutPipeAll](t_pipe/destroy_without_pipe_all.md)（`same_topic`）：DestroyWithoutPipeAll 与《GetTPipePtr》的实质衔接是：DestroyWithoutPipeAll 释放 TPipe 但不插入 PIPE_ALL，调用前需自行完成事件/流水同步；Destroy、EventID 释放和 TPipe 范式给出完整销毁顺序。
<!-- cannbot:related:end -->
