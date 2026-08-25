---
type: API
title: SetFlag/WaitFlag
description: 核内多流水间同步指令，SetFlag在源流水前序指令完成后设置硬件标志位，WaitFlag在目的流水等待标志位并清除，标注为ISASI类别，不保证跨硬件版本兼容。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/SetFlag_WaitFlag_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetFlag/WaitFlag

头文件路径为："basic_api/kernel_operator_block_sync_intf.h"。

如图1所示，SetFlag/WaitFlag接口用于核内多流水间的同步
- SetFlag：当源流水的前序指令的所有读写操作都完成之后，当前指令开始执行，并将硬件中的对应标志位设置为1。SetFlag只是设置硬件中的对应标志位，并不会阻塞源流水中的下一个指令。
- WaitFlag：当目的流水执行到该指令时，如果发现硬件中对应标志位为0，目的流水的后续指令将一直被阻塞；如果发现硬件中对应标志位为1，则将硬件中对应标志位设置为0，同时目的流水的后续指令开始执行。

参数：event(输入): 模板参数。同步事件，数据类型为HardEvent。同一核内的不同流水之间，在存在数据访问依赖时，需要根据数据访问的先后顺序，插入对应的同步事件。HardEvent用来表示对应的同步事件。 HardEvent命名规则为 ，其中源流水的指令先执行、目标流水中的指令后执行。例如MTE2_V，代表PIPE_MTE2为源流水，PIPE_V为目标流水，标识从PIPE_MTE2到PIPE_V的同步，PIPE_V等待PIPE_MTE2。 流水类型的取值及含义请参考硬件流水类型。由于硬件架构版本代际间的差异，不同硬件架构上的事件存在差异。HardEvent的取值范围请参考核内同步分类小节中表2和表3。；eventID(输入): 事件ID。数据类型为int32_t类型。eventID的取值范围与产品型号有关，具体请参考约束说明。

约束：- SetFlag只是设置硬件标志位，不会阻塞源流水中的下一个指令。

- SetFlag和WaitFlag必须成对使用，且SetFlag和WaitFlag的参数必须完全一致（包括模板参数event和输入参数eventID）。如果不匹配，会引发timeout问题。例如，SetFlag(1)和WaitFlag(1)并不匹配，因为其模板参数event不同。

- 在采用TPipe-TQue框架编程范式时，eventID需要通过AllocEventID或者FetchEventID来获取。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。
