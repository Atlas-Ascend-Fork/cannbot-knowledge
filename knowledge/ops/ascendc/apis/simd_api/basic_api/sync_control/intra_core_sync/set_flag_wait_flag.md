---
type: API
title: SetFlag/WaitFlag
description: 同一核内不同流水线之间的同步指令，SetFlag设置硬件标志位，WaitFlag等待并清除标志位，用于具有数据依赖的不同流水指令间同步。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/SetFlag-WaitFlag.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetFlag/WaitFlag

头文件路径为："basic_api/kernel_operator_block_sync_intf.h"。

同一核内不同流水线之间的同步指令，具有数据依赖的不同流水指令之间需要插入此同步。

- SetFlag：当前序指令的所有读写操作都完成之后，当前指令开始执行，并将硬件中的对应标志位设置为1。
- WaitFlag：当执行到该指令时，如果发现对应标志位为0，该队列的后续指令将一直被阻塞；如果发现对应标志位为1，则将对应标志位设置为0，同时后续指令开始执行。

参数：id(输入): 事件ID，由用户自己指定，推荐通过AllocEventID或者FetchEventID来获取。定义如下： using TEventID = int8_t;。

约束：SetFlag/WaitFlag必须成对出现。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [CrossCore 反压 flag 方向错致通算流水死锁](../../../../../runbooks/compilation/crosscore_flag.md)（`exemplifies`）：CrossCore 反压 flag 方向错致通算流水死锁 与《SetFlag/WaitFlag》的实质衔接是：该死锁来自 CrossCoreSet/Wait 的 t↔t-buffer 循环依赖；同 MC2 流水、subBlock、UDMA/ReduceScatter 及核间 flag 材料共同支撑依赖图和去反压验证。
- [GetTPipePtr 错加 AscendC 命名空间导致编译失败](../../../../../runbooks/compilation/gettpipeptr_is_global_function.md)（`exemplifies`）：GetTPipePtr 错加 AscendC 命名空间导致编译失败 与《SetFlag/WaitFlag》的实质衔接是：GetTPipePtr 是返回 AscendC::TPipe* 的全局函数；全局符号前缀案例和 FetchEventID/SetFlag/WaitFlag API共同说明只应去掉函数名上的 AscendC::。
- [arch35 Select 异步SIMT同步失效致分支错选](../../../../../runbooks/precision/arch35_select_simt.md)（`exemplifies`）：arch35 Select 异步SIMT同步失效致分支错选 与《SetFlag/WaitFlag》的实质衔接是：该卡定位 arch35 VSEL_CMPMASK_SPR 在异步 VF/同步原语缺失下读取陈旧 mask；RAW、跨调用/超64复用、Compare/Select 和同步 API 是可执行区分机制。
- [arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染](../../../../../runbooks/precision/arch35_vsel_cmpmask_spr_mask.md)（`exemplifies`）：arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染 与《SetFlag/WaitFlag》的实质衔接是：该卡锁定标量/小 count 的 packed mask 仅写少量字节而 Select 载入 stale padding；跨调用、超64、RAW、Compare/Select、GetValue 与同步材料提供可执行区分。
- [arch35 count Compare Select 异步VF 存读 RAW](../../../../../runbooks/precision/arch35_count_compare_select_vf_raw.md)（`exemplifies`）：arch35 count Compare Select 异步VF 存读 RAW 与《SetFlag/WaitFlag》的实质衔接是：该故障是 count Compare 将 packed mask 异步写 UB、随后 Select 重新 Load 的 VEC_STORE→VEC_LOAD RAW；GetValue 探针、LocalMemBar/pipe 同步边界和准确 Compare/Select 接口共同支持确诊与修复。
- [逐 rank 通信路径的 MTE2 主导诊断](../../../../../runbooks/performance/rank_flag_mte2.md)（`exemplifies`）：《逐 rank 通信路径的 MTE2 主导诊断》处理“ReduceScatter 远程读采用逐 rank DataCopy 与同步时，msprof 显示 aiv_mte2_time 主导 T_comm；三段注释法可排除 vec/reduce，但现有证据未单独验证 flag 是带宽缺口的唯一原因。”。《SetFlag/WaitFlag》明确“同一核内不同流水线之间的同步指令，SetFlag设置硬件标志位，WaitFlag等待并清除标志位，用于具有数据依赖的不同流水指令间同步。”，可直接用于核对ReduceScatter 逐 rank 搬运的 MTE2 计时、HBM 解释、同步必要性与成对 profile。
- [中级性能优化](../../../../../guides/operator_practice/typical_operator_cases/simd_operator_impl/matmul_leakyrelu_fusion_operator/intermediate_optimization.md)（`explains`）：中级性能优化 与《SetFlag/WaitFlag》的实质衔接是：Matmul+LeakyRelu 中级优化的正文直接串联 LoadData/Mmad/LeakyRelu、Load/Store、PipeBarrier、SetFlag 和 UnitFlag；所选故障卡约束这条融合流水。
- [AllocEventID](../../resource_management/t_pipe/alloc_event_id.md)（`related`）：SetFlag/WaitFlag 需要有效 TEventID；当事件需持有或同管线重复使用时应由 AllocEventID 分配并在生命周期末释放。
- [FetchEventID](../../resource_management/t_pipe/fetch_event_id.md)（`related`）：FetchEventID 取得的 TEventID 作为 SetFlag/WaitFlag 的同步标识，后者是该临时 ID 的直接消费者。
- [LocalMemBar](../../reg_vector_compute/sync_control/local_mem_bar.md)（`related`）：LocalMemBar 与《SetFlag/WaitFlag》的实质衔接是：LocalMemBar 只解决本地内存可见性，AscMemBar/核内同步材料给出作用域；RAW 故障与 arch35 编译卡分别验证缺 barrier 和错误执行域的后果。
- [PipeBarrier](pipe_barrier_isasi.md)（`related`）：SetFlag/WaitFlag 面向不同 pipeline 的事件同步；同一 pipeline 的顺序依赖应选择 PipeBarrier，二者构成同步机制的实质选型边界。
- [SetFlag/WaitFlag](set_flag_wait_flag_isasi.md)（`same_topic`）：非 ISASI/封装版本提供同一核内 event 配对语义。
<!-- cannbot:related:end -->
