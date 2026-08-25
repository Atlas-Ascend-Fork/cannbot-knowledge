---
type: API
title: IBSet
description: 核间存在全局内存数据依赖时插入同步语句，被等待核通过写全局内存通知等待核，与IBWait成对使用实现核间同步。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/inter_core_sync/IBSet.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# IBSet

头文件路径为："basic_api/kernel_operator_block_sync_intf.h"。

当不同核之间操作同一块全局内存且可能存在读后写、写后读以及写后写等数据依赖问题时，通过调用该函数来插入同步语句来避免上述数据依赖时可能出现的数据读写错误问题。

调用IBSet设置某一个核的标志位，与IBWait成对使用，表示核之间的同步等待指令：被等待核中调用IBSet，通过将值1写入全局内存中某块地址来通知等待核；而等待核中调用IBWait，持续读取全局内存中相应地址块的值，直到其值变为1，从而实现核间同步。

参数：isAIVOnly: 控制是否为AIVOnly模式，默认为true。；gmWorkspace(输入): 外部存储核状态的公共缓存，类型为GlobalTensor。GlobalTensor数据结构的定义请参考GlobalTensor。；ubWorkspace(输入): 存储当前核状态的公共缓存。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。；blockIdx(输入): 表示等待核的idx号，取值范围：[0,核数-1]。；eventID(输入): 用来控制当前核的set、wait事件。

约束：- gmWorkspace申请的空间最少要求为：核数*32Bytes*eventID_max+blockIdx_max*32Bytes+32Bytes（eventID_max和blockIdx_max分别指eventID、blockIdx的最大值）。需要注意的是，如果是AIVOnly模式，核数=GetBlockNum()；如果是MIX模式，核数=GetBlockNum()*2。
- ubWorkspace申请的空间最少要求为：32Bytes。
- 使用该接口进行多核控制时，算子调用时指定的逻辑AI Core核数numBlocks必须保证不大于实际运行该算子的AI处理器核数，否则框架进行多轮调度时会插入异常同步，导致Kernel“卡死”现象。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [IBWait](ib_wait.md)（`same_topic`）：IBSet说明核间存在全局内存数据依赖时插入同步语句，被等待核通过写全局内存通知等待核，与IBWait成对使用实现核间同步。
<!-- cannbot:related:end -->
