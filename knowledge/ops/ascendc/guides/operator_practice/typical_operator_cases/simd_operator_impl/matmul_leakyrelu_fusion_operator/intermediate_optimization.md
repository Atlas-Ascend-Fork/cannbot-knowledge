---
type: Guide
title: 中级性能优化
description: 本节在入门功能落地的基础上，介绍Matmul融合算子的中级性能优化方法。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/typical_operator_cases/simd_operator_impl/matmul_leakyrelu_fusion_operator/intermediate_optimization.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# 中级性能优化

本节在入门功能落地的基础上，介绍Matmul融合算子的中级性能优化方法。
> 说明：入门功能落地以Matmul+LeakyRelu融合算子作为讲解样例，而中级和高阶极限打磨以Matmul+Gelu融合算子作为讲解样例。为更好展示VF融合的性能优化手段，本章节以Matmul+Gelu融合算子作为讲解样例。GELU相比LeakyRelu计算逻辑更复杂，能更充分地体现各类优化手段的效果。
## 优化手段总览
编号：优化手段：说明：定位
1：L1/L0双缓冲Ping-Pong布局：Cube核内MTE2搬运和MTE1/Mmad计算并行：流水线骨架
2：大包搬运：增大搬运粒度，减少搬运次数：流水线骨架
3：细粒度流水同步：SetFlag/WaitFlag替代PipeBarrier实现更细粒度同步：流水线骨架
4：LoadData3D替代LoadData2D：减少MTE1指令队列占用：指令队列优化
5：多核并行切分：按M/N方向切分到多核并行计算：并行策略
6：常量Tiling：Tiling参数编译期确定，减少运行时Scalar计算开销：编译期优化
7：UnitFlag优化：Mmad与Fixpipe细粒度流水重叠：MMAD-FIXPIPE流水重叠
## CV融合：Scenario 1 — CV融合-GM中转
中级性能优化采用CV融合-GM中转方式（A2/A3/Ascend 950PR均支持）。AIC侧通过Fixpipe将L0C计算结果写入GM，AIV侧从GM读取数据到UB后进行GELU计算，再将结果写回GM。
数据流路径：
### Matmul优化手段
Case：优化手段：说明
Case 1：单核Tiling优化：优化base块参数，降低访存计算比
Case 2：多核切分 2x12：引入多核并行计算，均衡负载分配
Case 3：多核切分 4x6：优化多核切分策略，地址512B对齐
Case 4：多核使用MDL模板：启用L1多块缓存，大包搬运
### Gelu优化手段
Case：优化手段：说明
Case 1：RegBase API + VF融合：寄存器级计算减少中间Load/Store，利用双发特性提升IPC
### 性能数据
以Ascend 950PR芯片数据为例：
- 单独Gelu任务耗时348.868μs，单独Matmul任务耗时2601.311μs
- Scenario 1融合后总耗时2606.91μs，与Matmul单独执行时间基本一致
这表明采用CV融合方式编写时，AIV的Vector计算时间基本被AIC的Cube计算时间完全覆盖，实现了高效的流水并行。
详细内容请参见Matmul+Gelu中级性能优化。

<!-- cannbot:related:start -->
## 相关

- [LeakyRelu](../../../../../apis/simd_api/basic_api/memory_vector_compute/basic_arithmetic/leaky_relu.md)（`explains`）：中级性能优化 与《LeakyRelu》的实质衔接是：Matmul+LeakyRelu 中级优化的正文直接串联 LoadData/Mmad/LeakyRelu、Load/Store、PipeBarrier、SetFlag 和 UnitFlag；所选故障卡约束这条融合流水。
- [LeakyRelu](../../../../../apis/simd_api/basic_api/reg_vector_compute/basic_arithmetic/leaky_relu.md)（`explains`）：LeakyRelu 与《中级性能优化》的实质衔接是：Reg LeakyRelu 与 Memory/C Reg/C Vector 入口实现同一负半轴 slope 计算，Matmul-LeakyRelu 案例给出该接口在融合算子中的真实落点。
- [Load](../../../../../apis/simd_api/basic_api/reg_vector_compute/reg_data_load/load.md)（`explains`）：中级性能优化 与《Load》的实质衔接是：Matmul+LeakyRelu 中级优化的正文直接串联 LoadData/Mmad/LeakyRelu、Load/Store、PipeBarrier、SetFlag 和 UnitFlag；所选故障卡约束这条融合流水。
- [LoadData](../../../../../apis/simd_api/basic_api/cube_compute/cube_compute_load/load_data_2_d.md)（`explains`）：中级性能优化 与《LoadData》的实质衔接是：Matmul+LeakyRelu 中级优化的正文直接串联 LoadData/Mmad/LeakyRelu、Load/Store、PipeBarrier、SetFlag 和 UnitFlag；所选故障卡约束这条融合流水。
- [Mmad](../../../../../apis/simd_api/basic_api/cube_compute/mmad_compute/mmad.md)（`explains`）：中级性能优化 与《Mmad》的实质衔接是：Matmul+LeakyRelu 中级优化的正文直接串联 LoadData/Mmad/LeakyRelu、Load/Store、PipeBarrier、SetFlag 和 UnitFlag；所选故障卡约束这条融合流水。
- [PipeBarrier](../../../../../apis/simd_api/basic_api/sync_control/intra_core_sync/pipe_barrier_isasi.md)（`explains`）：中级性能优化 与《PipeBarrier》的实质衔接是：Matmul+LeakyRelu 中级优化的正文直接串联 LoadData/Mmad/LeakyRelu、Load/Store、PipeBarrier、SetFlag 和 UnitFlag；所选故障卡约束这条融合流水。
- [SetFlag/WaitFlag](../../../../../apis/simd_api/basic_api/sync_control/intra_core_sync/set_flag_wait_flag.md)（`explains`）：中级性能优化 与《SetFlag/WaitFlag》的实质衔接是：Matmul+LeakyRelu 中级优化的正文直接串联 LoadData/Mmad/LeakyRelu、Load/Store、PipeBarrier、SetFlag 和 UnitFlag；所选故障卡约束这条融合流水。
- [Store](../../../../../apis/simd_api/basic_api/reg_vector_compute/reg_data_store/store.md)（`explains`）：中级性能优化 与《Store》的实质衔接是：Matmul+LeakyRelu 中级优化的正文直接串联 LoadData/Mmad/LeakyRelu、Load/Store、PipeBarrier、SetFlag 和 UnitFlag；所选故障卡约束这条融合流水。
- [AIC和AIV独立运行机制](../../../simd_operator_impl/matrix_advanced_api/feature_scenarios/aic_aiv_independent_execution.md)（`related`）：中级性能优化 与《AIC和AIV独立运行机制》的实质衔接是：Matmul+LeakyRelu 中级优化的正文直接串联 LoadData/Mmad/LeakyRelu、Load/Store、PipeBarrier、SetFlag 和 UnitFlag；所选故障卡约束这条融合流水。
- [Matmul高阶API开启UnitFlag](../../../best_practices/matmul_tuning_cases/matmul_unit_flag.md)（`related`）：中级性能优化 与《Matmul高阶API开启UnitFlag》的实质衔接是：Matmul+LeakyRelu 中级优化的正文直接串联 LoadData/Mmad/LeakyRelu、Load/Store、PipeBarrier、SetFlag 和 UnitFlag；所选故障卡约束这条融合流水。
- [PipeBarrier 的 PIPE_V 是全局枚举](../../../../../runbooks/compilation/pipebarrier_pipe_v_uses_global_enum.md)（`related`）：中级性能优化 与《PipeBarrier 的 PIPE_V 是全局枚举》的实质衔接是：Matmul+LeakyRelu 中级优化的正文直接串联 LoadData/Mmad/LeakyRelu、Load/Store、PipeBarrier、SetFlag 和 UnitFlag；所选故障卡约束这条融合流水。
- [PipeBarrier<PIPE_S> 编译失败 — 只保留目标架构支持的管线](../../../../../runbooks/compilation/pipebarrier_pipe_s_is_not_supported.md)（`related`）：中级性能优化 与《PipeBarrier<PIPE_S> 编译失败 — 只保留目标架构支持的管线》的实质衔接是：Matmul+LeakyRelu 中级优化的正文直接串联 LoadData/Mmad/LeakyRelu、Load/Store、PipeBarrier、SetFlag 和 UnitFlag；所选故障卡约束这条融合流水。
- [Reg 固定地址跨块累加需逐 VF PipeBarrier](../../../../../runbooks/precision/fixed_address_vf_accumulator_needs_per_call_barrier.md)（`related`）：中级性能优化 与《Reg 固定地址跨块累加需逐 VF PipeBarrier》的实质衔接是：Matmul+LeakyRelu 中级优化的正文直接串联 LoadData/Mmad/LeakyRelu、Load/Store、PipeBarrier、SetFlag 和 UnitFlag；所选故障卡约束这条融合流水。
- [融合算子编程基础知识](../../../simd_operator_impl/fusion_operator_programming/cv_fusion/basics.md)（`related`）：中级性能优化 与《融合算子编程基础知识》的实质衔接是：Matmul+LeakyRelu 中级优化的正文直接串联 LoadData/Mmad/LeakyRelu、Load/Store、PipeBarrier、SetFlag 和 UnitFlag；所选故障卡约束这条融合流水。
- [入门功能落地](getting_started.md)（`same_topic`）：中级性能优化 与《入门功能落地》的实质衔接是：Matmul+LeakyRelu 中级优化的正文直接串联 LoadData/Mmad/LeakyRelu、Load/Store、PipeBarrier、SetFlag 和 UnitFlag；所选故障卡约束这条融合流水。
- [高阶极限打磨](extreme_optimization.md)（`same_topic`）：中级性能优化 与《高阶极限打磨》的实质衔接是：Matmul+LeakyRelu 中级优化的正文直接串联 LoadData/Mmad/LeakyRelu、Load/Store、PipeBarrier、SetFlag 和 UnitFlag；所选故障卡约束这条融合流水。
<!-- cannbot:related:end -->
