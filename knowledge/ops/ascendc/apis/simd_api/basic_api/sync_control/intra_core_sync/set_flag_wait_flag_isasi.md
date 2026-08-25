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

<!-- cannbot:related:start -->
## 相关

- [CrossCore 反压 flag 方向错致通算流水死锁](../../../../../runbooks/compilation/crosscore_flag.md)（`exemplifies`）：CrossCore 反压 flag 方向错致通算流水死锁 与《SetFlag/WaitFlag》的实质衔接是：该死锁来自 CrossCoreSet/Wait 的 t↔t-buffer 循环依赖；同 MC2 流水、subBlock、UDMA/ReduceScatter 及核间 flag 材料共同支撑依赖图和去反压验证。
- [GetTPipePtr 错加 AscendC 命名空间导致编译失败](../../../../../runbooks/compilation/gettpipeptr_is_global_function.md)（`exemplifies`）：GetTPipePtr 错加 AscendC 命名空间导致编译失败 与《SetFlag/WaitFlag》的实质衔接是：GetTPipePtr 是返回 AscendC::TPipe* 的全局函数；全局符号前缀案例和 FetchEventID/SetFlag/WaitFlag API共同说明只应去掉函数名上的 AscendC::。
- [arch35 Select 异步SIMT同步失效致分支错选](../../../../../runbooks/precision/arch35_select_simt.md)（`exemplifies`）：arch35 Select 异步SIMT同步失效致分支错选 与《SetFlag/WaitFlag》的实质衔接是：该卡定位 arch35 VSEL_CMPMASK_SPR 在异步 VF/同步原语缺失下读取陈旧 mask；RAW、跨调用/超64复用、Compare/Select 和同步 API 是可执行区分机制。
- [arch35 count Compare Select 异步VF 存读 RAW](../../../../../runbooks/precision/arch35_count_compare_select_vf_raw.md)（`exemplifies`）：arch35 count Compare Select 异步VF 存读 RAW 与《SetFlag/WaitFlag》的实质衔接是：该故障是 count Compare 将 packed mask 异步写 UB、随后 Select 重新 Load 的 VEC_STORE→VEC_LOAD RAW；GetValue 探针、LocalMemBar/pipe 同步边界和准确 Compare/Select 接口共同支持确诊与修复。
- [探针末尾 MTE2_S/MTE3_S 同步不可由 stream sync 替代](../../../../../runbooks/compilation/mte2_s_mte3_s_stream_sync.md)（`exemplifies`）：The API contract explains why a matched MTE2_S/MTE3_S SetFlag/WaitFlag pair waits for source-pipeline reads/writes before allowing the scalar-side exit path to continue.
- [逐 rank 通信路径的 MTE2 主导诊断](../../../../../runbooks/performance/rank_flag_mte2.md)（`exemplifies`）：《逐 rank 通信路径的 MTE2 主导诊断》处理“ReduceScatter 远程读采用逐 rank DataCopy 与同步时，msprof 显示 aiv_mte2_time 主导 T_comm；三段注释法可排除 vec/reduce，但现有证据未单独验证 flag 是带宽缺口的唯一原因。”。《SetFlag/WaitFlag》明确“核内多流水间同步指令，SetFlag在源流水前序指令完成后设置硬件标志位，WaitFlag在目的流水等待标志位并清除，标注为ISASI类别，不保证跨硬件版本兼容。”，可直接用于核对ReduceScatter 逐 rank 搬运的 MTE2 计时、HBM 解释、同步必要性与成对 profile。
- [TPipe和TQue编程范式](../../../../../guides/programming_guide/programming_model/ai_core_simd_programming/tpipe_tque_programming/tpipe_tque_paradigm.md)（`explains`）：《TPipe和TQue编程范式》说明上一章阐述了TPipe‑TQue编程模型的底层设计原理：基于经典C/C++队列管道（Queue Pipeline）思想，将算子任务拆分为多级流水Stage，依靠TQue队列解决写后读数据依赖、依靠AllocTensor/FreeTensor解决读后写内存复用冲突，通过底层同步指令实现多单元异步并行的时序安全。；《SetFlag/WaitFlag》说明核内多流水间同步指令，SetFlag在源流水前序指令完成后设置硬件标志位，WaitFlag在目的流水等待标志位并清除，标注为ISASI类别，不保证跨硬件版本兼容。。二者在TPipe/TQue范式用InitBuffer和Alloc/EnQue/DeQue/FreeTensor表达内存所有权与Stage同步，相关FAQ和故障直接验证生命周期约束上存在可执行的直接衔接。
- [CrossCoreSetFlag](../inter_core_sync/cross_core_set_flag_isasi.md)（`related`）：CrossCore 作用于不同核，不能替代核内流水 event。
- [DataSyncBarrier](data_sync_barrier_isasi.md)（`related`）：明确 producer/consumer pipeline 时 flag/wait 可替代全局数据屏障，减少无关流水等待。
- [PipeBarrier](pipe_barrier_isasi.md)（`related`）：跨不同 producer/consumer 流水宜用配对 event，而非同流水 barrier。
- [关键特性说明](key_features.md)（`related`）：明确 producer/consumer 流水时 flag/wait 建立定向依赖。
- [SetFlag/WaitFlag](set_flag_wait_flag.md)（`same_topic`）：非 ISASI/封装版本提供同一核内 event 配对语义。
<!-- cannbot:related:end -->
