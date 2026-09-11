---
type: API
title: SetFlag/WaitFlag
description: 同一核内不同流水线之间的同步指令，SetFlag设置硬件标志位，WaitFlag等待并清除标志位，用于具有数据依赖的不同流水指令间同步。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.implementation.synchronization
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/SetFlag-WaitFlag.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
- '910'
source_headers:
- include/basic_api/kernel_operator_block_sync_intf.h
---

# SetFlag/WaitFlag<a name="ZH-CN_TOPIC_0000001944599897"></a>

## 功能说明<a name="section618mcpsimp"></a>

头文件路径为：`"basic_api/kernel_operator_block_sync_intf.h"`。

同一核内不同流水线之间的同步指令，具有数据依赖的不同流水指令之间需要插入此同步。

- SetFlag：当前序指令的所有读写操作都完成之后，当前指令开始执行，并将硬件中的对应标志位设置为1。
- WaitFlag：当执行到该指令时，如果发现对应标志位为0，该队列的后续指令将一直被阻塞；如果发现对应标志位为1，则将对应标志位设置为0，同时后续指令开始执行。

> [!NOTE]说明
> 此接口与[SetFlag/WaitFlag(ISASI)](set_flag_wait_flag_isasi.md)接口也能实现相同的功能。二者的区别在于，TQueSync类接口可以保证跨硬件版本兼容，而[SetFlag/WaitFlag(ISASI)](set_flag_wait_flag_isasi.md)中的接口标注为ISASI类别，不能保证跨硬件版本兼容。

## 函数原型<a name="section620mcpsimp"></a>

```cpp
__aicore__ inline void SetFlag(TEventID id)
__aicore__ inline void WaitFlag(TEventID id)
```

## 参数说明<a name="section622mcpsimp"></a>

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| id | 输入 | 事件ID，由用户自己指定，推荐通过[AllocEventID](../../resource_management/t_pipe/alloc_event_id.md)或者[FetchEventID](../../resource_management/t_pipe/fetch_event_id.md)来获取。定义如下：<br>`using TEventID = int8_t;`<br>不同产品对id的取值范围说明请参见[id取值范围说明](#id取值范围说明)。 |

### id取值范围说明


- Ascend 950PR/Ascend 950DT，取值范围是0-7。


- Atlas A3 训练系列产品/Atlas A3 推理系列产品，取值范围是0-7。


- Atlas A2 训练系列产品/Atlas A2 推理系列产品，取值范围是0-7。


- Atlas 200I/500 A2 推理产品，取值范围是0-7。


- Atlas 推理系列产品AI Core，取值范围是0-7。


- Atlas 训练系列产品，取值范围是0-3。


## 返回值说明<a name="section640mcpsimp"></a>

无

## 约束说明<a name="section633mcpsimp"></a>

SetFlag/WaitFlag必须成对出现。

## 调用示例<a name="section837496171220"></a>

如DataCopy需要等待SetValue执行完成后才能执行，需要插入PIPE\_S到PIPE\_MTE3的同步。

```cpp
AscendC::GlobalTensor<half> dstGlobal;
AscendC::LocalTensor<half> dstLocal;
dstLocal.SetValue(0, 0);
AscendC::TQueSync<PIPE_S, PIPE_MTE3> sync;
sync.SetFlag(0);
sync.WaitFlag(0);
AscendC::DataCopy(dstGlobal, dstLocal, dataSize);
```
