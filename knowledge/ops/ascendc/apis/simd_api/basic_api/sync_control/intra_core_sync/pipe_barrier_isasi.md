---
type: API
title: PipeBarrier
description: 完成同一流水线内的同步控制，保证前序指令中所有数据的读写工作全部完成后，后序指令才能执行。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/PipeBarrier_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# PipeBarrier

头文件路径为："basic_api/kernel_operator_block_sync_intf.h"。

如下图1所示，完成同一流水线内的同步控制，用于在同一流水线内部约束执行顺序。其作用是，保证前序指令中所有数据的读写工作全部完成，后序指令才能执行。

参数：pipe: 模板参数，表示阻塞的流水类别。 支持的流水参考硬件流水类型，其中不支持PIPE_S。 如果不关注流水类别，希望阻塞所有流水，可以传入PIPE_ALL。

约束：- Scalar流水之间的同步由硬件自动保证，PipeBarrier接口不支持PIPE_S单流水的同步。

- PipeBarrier()会等待所有流水线中所有先前提交的接口完成，这会对性能产生影响。若仅阻塞单条流水线即可解决问题，应避免随意调用PipeBarrier()。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [BF16 gamma Cast 分阶段编排导致随机 NaN](../../../../../runbooks/precision/bf16_gamma_cast_must_share_ordered_compute_stage.md)（`exemplifies`）：本卡在相关 MTE2 搬入后和两次 Vector Cast 后建立管线屏障。
- [DataCopyPad 后未先同步 Cast 导致低精度 NaN](../../../../../runbooks/precision/mte2_barrier_must_precede_vector_cast.md)（`exemplifies`）：Runbook 证明 PipeBarrier 放在 Cast 之后不能倒退补齐依赖，必须位于 MTE2 producer 与 Vector consumer 之间。
- [Duplicate 掩码向量化未修复 triu 大 shape 失败](../../../../../runbooks/performance/duplicate_triu_shape.md)（`exemplifies`）：《PipeBarrier》明确“完成同一流水线内的同步控制，保证前序指令中所有数据的读写工作全部完成后，后序指令才能执行。”；它与《Duplicate 掩码向量化未修复 triu 大 shape 失败》的“triu 大 shape Case9 失败初判为标量 SetValue 掩码瓶颈，改 Duplicate 0 填充向量化后仍失败；后续 timing 定位实为 per-tile event flag 耗尽的正确性问题（非超时），Duplicate 向量化路线 banned。”在实际调用参数、数据流或结果校验上直接衔接。
- [PipeBarrier 的 PIPE_V 是全局枚举](../../../../../runbooks/compilation/pipebarrier_pipe_v_uses_global_enum.md)（`exemplifies`）：《PipeBarrier 的 PIPE_V 是全局枚举》处理“在 CANN 9.0.1/9.2 classic Ascend C 中把 PIPE_V 写成 AscendC 命名空间成员会编译失败，改用全局枚举后构建通过；已在 A3 与 Ascend950 两个平台闭环。”。《PipeBarrier》提供“完成同一流水线内的同步控制，保证前序指令中所有数据的读写工作全部完成后，后序指令才能执行。”，其具体合同或探针直接接入PipeBarrier 模板与 PIPE_* 全局枚举的符号解析及同类编译诊断。
- [PipeBarrier<PIPE_S> 编译失败 — 只保留目标架构支持的管线](../../../../../runbooks/compilation/pipebarrier_pipe_s_is_not_supported.md)（`exemplifies`）：接口契约列出 PipeBarrier 支持的流水同步语义，可据此确认 PIPE_S 不是有效模板参数，并选择实际生产者/消费者流水。
- [Reg 固定地址跨块累加需逐 VF PipeBarrier](../../../../../runbooks/precision/fixed_address_vf_accumulator_needs_per_call_barrier.md)（`exemplifies`）：focal 的修复在每次 asc_vf_call 后使用 PipeBarrier<PIPE_V>，API 卡提供该 Vector pipeline 顺序原语的调用契约。
- [VF 归约落 UB 后 GetValue 读取陈旧标量](../../../../../runbooks/precision/vector_scalar_ub_handoff_requires_explicit_completion.md)（`exemplifies`）：VF 归约落 UB 后 GetValue 读取陈旧标量 与《PipeBarrier》的实质衔接是：Reg Reduce 经 StoreAlign 落 UB 后，PIPE_V 不保证 Scalar GetValue 可见；相关跨 VF 累加、barrier、GetValue 陈旧和 SoftMax 卡共同支持把归约与 lane0 广播保留在同一 VF。
- [arch35 Select 异步SIMT同步失效致分支错选](../../../../../runbooks/precision/arch35_select_simt.md)（`exemplifies`）：arch35 Select 异步SIMT同步失效致分支错选 与《PipeBarrier》的实质衔接是：该卡定位 arch35 VSEL_CMPMASK_SPR 在异步 VF/同步原语缺失下读取陈旧 mask；RAW、跨调用/超64复用、Compare/Select 和同步 API 是可执行区分机制。
- [arch35 count Compare Select 异步VF 存读 RAW](../../../../../runbooks/precision/arch35_count_compare_select_vf_raw.md)（`exemplifies`）：arch35 count Compare Select 异步VF 存读 RAW 与《PipeBarrier》的实质衔接是：该故障是 count Compare 将 packed mask 异步写 UB、随后 Select 重新 Load 的 VEC_STORE→VEC_LOAD RAW；GetValue 探针、LocalMemBar/pipe 同步边界和准确 Compare/Select 接口共同支持确诊与修复。
- [bisheng 不接受 device 侧 sqrtf—改用向量 Sqrt](../../../../../runbooks/compilation/device_sqrt_uses_vector_api.md)（`exemplifies`）：“bisheng 不接受 device 侧 sqrtf—改用向量 Sqrt”定义：device kernel 中直接调用 sqrtf 导致 bisheng 编译失败；改为 32B 对齐的向量 Sqrt 链并显式同步。；“PipeBarrier”定义：完成同一流水线内的同步控制，保证前序指令中所有数据的读写工作全部完成后，后序指令才能执行。。实质衔接：device sqrtf 编译失败时改用对齐 LocalTensor 的 Vector Sqrt；数值 runbook给出该替换在 Rsqrt 精度修复中的实例，PipeBarrier闭合向量结果消费。
- [标量 S pipe 误用 TQue 导致输出全常数](../../../../../runbooks/precision/scalar_s_pipe_requires_explicit_mte_dependencies.md)（`exemplifies`）：该卡证明 V-pipe barrier 不会自动覆盖 S 与 MTE 的依赖。
- [模板内 float→float Cast 使 fp32 分支全错](../../../../../runbooks/precision/templated_float_input_must_bypass_same_type_cast.md)（`exemplifies`）：模板内 float→float Cast 使 fp32 分支全错 与《PipeBarrier》的实质衔接是：float 到 float 不应进入窄化 Cast，应该保持原值或 Copy；同步、BF16 分阶段、native 类型、VL、舍入与 RmsNorm 案例分别说明真正需要 Cast 时的类型、时序和验证契约。
- [重复目标随机写丢失 — 在 UB 内按序合并后 DMA 写回](../../../../../runbooks/precision/repeated_overwrite_updates_need_ordered_ub_merge.md)（`exemplifies`）：该卡用 PipeBarrier 排空 UB 更新和写回，展示正确放置。
- [中级性能优化](../../../../../guides/operator_practice/typical_operator_cases/simd_operator_impl/gelu_reg_vector_operator/intermediate_optimization.md)（`explains`）：中级性能优化 与《PipeBarrier》的实质衔接是：GELU 中级优化从入门版迁到 Reg/VF 融合并使用 Load/Store/PipeBarrier；所选故障卡直接约束这些调用和 GELU 数值实现。
- [中级性能优化](../../../../../guides/operator_practice/typical_operator_cases/simd_operator_impl/matmul_leakyrelu_fusion_operator/intermediate_optimization.md)（`explains`）：中级性能优化 与《PipeBarrier》的实质衔接是：Matmul+LeakyRelu 中级优化的正文直接串联 LoadData/Mmad/LeakyRelu、Load/Store、PipeBarrier、SetFlag 和 UnitFlag；所选故障卡约束这条融合流水。
- [AscSyncPipe](../../../c_api/sync/asc_sync_pipe.md)（`related`）：PipeBarrier 是 C++ 基础 API 的同流水同步对应，同样不支持 PIPE_S 并建议只阻塞必要管线。
- [DataCopy](../../memory_vector_compute/data_move/data_copy_gm_and_ub_continuous.md)（`related`）：多个 DataCopy 目的地址重叠时需要对应 MTE2 或 MTE3 PipeBarrier 串行化，避免前后搬运覆盖竞态。
- [DataSyncBarrier](data_sync_barrier_isasi.md)（`related`）：PipeBarrier 只同步指定流水，而 DataSyncBarrier 建立更广的数据可见性；依赖范围决定选型。
- [GetSystemCycle](../../tool_interface/system_resources_and_variables/get_system_cycle_isasi.md)（`related`）：GetSystemCycle 正文要求测量 Vector/MTE 等异步流水前先做对应同步，否则时间戳只反映 Scalar 发射而非工作完成；PipeBarrier 提供这一前置完成性约束。
- [SetFlag/WaitFlag](set_flag_wait_flag.md)（`related`）：SetFlag/WaitFlag 面向不同 pipeline 的事件同步；同一 pipeline 的顺序依赖应选择 PipeBarrier，二者构成同步机制的实质选型边界。
- [SetFlag/WaitFlag](set_flag_wait_flag_isasi.md)（`related`）：跨不同 producer/consumer 流水宜用配对 event，而非同流水 barrier。
- [关键特性说明](key_features.md)（`related`）：同流水排空使用 PipeBarrier，不应误用跨流水 event。
- [AscSyncDataBarrier](../../../c_api/sync/asc_sync_data_barrier.md)（`same_topic`）：《AscSyncDataBarrier》处理“阻塞后续指令执行，直到所有之前的内存访问指令执行结束，用于解决Scalar的内存依赖。”。《PipeBarrier》提供“完成同一流水线内的同步控制，保证前序指令中所有数据的读写工作全部完成后，后序指令才能执行。”，其具体合同或探针直接接入Scalar 内存依赖的 data barrier、pipe barrier 选择和同步位置验证。
- [核内同步能力概述](intra_core_sync_overview.md)（`same_topic`）：概览解释 barrier、event、mutex 的作用域。
<!-- cannbot:related:end -->
