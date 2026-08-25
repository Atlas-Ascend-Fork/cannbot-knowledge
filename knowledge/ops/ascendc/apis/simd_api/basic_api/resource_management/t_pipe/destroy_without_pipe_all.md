---
type: API
title: DestroyWithoutPipeAll
description: 释放TPipe资源，用于重复申请释放TPipe。内部未设置PIPE_ALL同步，需开发者自行保证同步流水正确。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TPipe/DestroyWithoutPipeAll.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# DestroyWithoutPipeAll

头文件路径为："basic_api/kernel_tpipe.h"。

释放资源。

约束：用于重复申请释放TPipe，创建TPipe对象后，可调用DestroyWithoutPipeAll手动释放资源。

该接口内部未设置PIPE_ALL同步，需要开发者自行保证同步流水正确。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [TPipe-TQue编程原理介绍](../../../../../guides/programming_guide/programming_model/ai_core_simd_programming/tpipe_tque_programming/tpipe_tque_principles.md)（`explains`）：DestroyWithoutPipeAll 与《TPipe-TQue编程原理介绍》的实质衔接是：DestroyWithoutPipeAll 释放 TPipe 但不插入 PIPE_ALL，调用前需自行完成事件/流水同步；Destroy、EventID 释放和 TPipe 范式给出完整销毁顺序。
- [TPipe和TQue编程范式](../../../../../guides/programming_guide/programming_model/ai_core_simd_programming/tpipe_tque_programming/tpipe_tque_paradigm.md)（`explains`）：DestroyWithoutPipeAll 与《TPipe和TQue编程范式》的实质衔接是：DestroyWithoutPipeAll 释放 TPipe 但不插入 PIPE_ALL，调用前需自行完成事件/流水同步；Destroy、EventID 释放和 TPipe 范式给出完整销毁顺序。
- [避免TPipe在对象内创建和初始化](../../../../../guides/operator_practice/simd_operator_optimization/overhead_optimization/avoid_tpipe_init_in_object.md)（`explains`）：DestroyWithoutPipeAll 与《避免TPipe在对象内创建和初始化》的实质衔接是：DestroyWithoutPipeAll 释放 TPipe 但不插入 PIPE_ALL，调用前需自行完成事件/流水同步；Destroy、EventID 释放和 TPipe 范式给出完整销毁顺序。
- [Reset](../t_buf_pool/reset.md)（`related`）：Reset 与《DestroyWithoutPipeAll》的实质衔接是：Reset 结束当前 TBufPool 事件但保留 pool/buffer，必须放在 InitBufPool/Init 与 Destroy 之间；自定义池说明给出切换资源池的生命周期。
- [TPipe](t_pipe_constructor.md)（`related`）：《DestroyWithoutPipeAll》明确“释放TPipe资源，用于重复申请释放TPipe。内部未设置PIPE_ALL同步，需开发者自行保证同步流水正确。”；它与《TPipe》的“构造用来管理内存和同步的TPipe对象。”在实际调用参数、数据流或结果校验上直接衔接。
- [AllocEventID](alloc_event_id.md)（`same_topic`）：DestroyWithoutPipeAll 与《AllocEventID》的实质衔接是：DestroyWithoutPipeAll 释放 TPipe 但不插入 PIPE_ALL，调用前需自行完成事件/流水同步；Destroy、EventID 释放和 TPipe 范式给出完整销毁顺序。
- [Destroy](destroy.md)（`same_topic`）：DestroyWithoutPipeAll 与《Destroy》的实质衔接是：DestroyWithoutPipeAll 释放 TPipe 但不插入 PIPE_ALL，调用前需自行完成事件/流水同步；Destroy、EventID 释放和 TPipe 范式给出完整销毁顺序。
- [FetchEventID](fetch_event_id.md)（`same_topic`）：DestroyWithoutPipeAll 与《FetchEventID》的实质衔接是：DestroyWithoutPipeAll 释放 TPipe 但不插入 PIPE_ALL，调用前需自行完成事件/流水同步；Destroy、EventID 释放和 TPipe 范式给出完整销毁顺序。
- [FreeAllEvent](../t_que_bind/free_all_event.md)（`same_topic`）：《FreeAllEvent》处理“释放TQueBind队列中申请的所有同步事件，便于在Buffer数量超过同步事件限制时重新申请队列。”。《DestroyWithoutPipeAll》明确“释放TPipe资源，用于重复申请释放TPipe。内部未设置PIPE_ALL同步，需开发者自行保证同步流水正确。”，可直接用于核对FreeAllEvent 对 TQueBind 事件和 Alloc/Fetch/Release event ID 生命周期的回收合同。
- [GetTPipePtr](../get_t_pipe_ptr.md)（`same_topic`）：DestroyWithoutPipeAll 与《GetTPipePtr》的实质衔接是：DestroyWithoutPipeAll 释放 TPipe 但不插入 PIPE_ALL，调用前需自行完成事件/流水同步；Destroy、EventID 释放和 TPipe 范式给出完整销毁顺序。
- [ReleaseEventID](release_event_id.md)（`same_topic`）：DestroyWithoutPipeAll 与《ReleaseEventID》的实质衔接是：DestroyWithoutPipeAll 释放 TPipe 但不插入 PIPE_ALL，调用前需自行完成事件/流水同步；Destroy、EventID 释放和 TPipe 范式给出完整销毁顺序。
- [TBufPool简介](../t_buf_pool/t_buf_pool_intro.md)（`same_topic`）：TBufPool简介 与《DestroyWithoutPipeAll》的实质衔接是：TBufPool 在 TPipe 下手工复用 UB/L1，必须依次 InitBufPool、分配/取址、Reset 或 Destroy；所连容量和 TPipe 初始化案例直接约束资源预算与生命周期。
- [TPipe](t_pipe.md)（`same_topic`）：DestroyWithoutPipeAll 与《TPipe》的实质衔接是：DestroyWithoutPipeAll 释放 TPipe 但不插入 PIPE_ALL，调用前需自行完成事件/流水同步；Destroy、EventID 释放和 TPipe 范式给出完整销毁顺序。
- [TPipe简介](t_pipe_intro.md)（`same_topic`）：DestroyWithoutPipeAll 与《TPipe简介》的实质衔接是：DestroyWithoutPipeAll 释放 TPipe 但不插入 PIPE_ALL，调用前需自行完成事件/流水同步；Destroy、EventID 释放和 TPipe 范式给出完整销毁顺序。
<!-- cannbot:related:end -->
