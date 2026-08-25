---
type: API
title: VF调用
description: Reg矢量计算VF调用接口索引页，包含asc_vf_call。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/vf_call/vf_call.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# VF调用

提供 asc_vf_call 接口，用于在 SIMD 编程场景下启动 SIMD VF（Vector Function）子任务。通过模板参数 funcPtr 指定入口核函数，可变参数 Args 传递实参。

约束：子任务函数不能是类的成员函数，推荐使用普通函数或类静态函数，入口函数必须使用 __simd_vf__ 修饰；入参仅支持 Ascend C 内置数据类型及其指针、数组、结构体，指针必须指向 UB 内存。仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Ascend950 Reg 扫描按 256B 锁定 lane](../../../../../runbooks/precision/dav3510_vector_register_width_is_256_bytes.md)（`exemplifies`）：Ascend950 Reg 扫描按 256B 锁定 lane 与《VF调用》的实质衔接是：这些卡共同约束 256B RegTensor 的 lane 数、B16/B32 提升后的 mask 宽度以及 LoadAlign/VF 调用范围；所连错例均由按错误数据宽度计算 lane 或目标 VL 导致。
- [Reg 同 wrapper 回读 UB 引发尺寸相关漂移](../../../../../runbooks/precision/split_multi_pass_vf_at_ub_producer_consumer_boundaries.md)（`exemplifies`）：分阶段 VF 在同一 wrapper 回读 UB 会产生尺寸相关漂移，案例要求在 UB producer/consumer 边界拆分多次 asc_vf_call。
- [Reg 固定地址跨块累加需逐 VF PipeBarrier](../../../../../runbooks/precision/fixed_address_vf_accumulator_needs_per_call_barrier.md)（`exemplifies`）：固定地址跨 VF 累加卡说明每次 VF 调用之间需 PipeBarrier 才能保证上一轮 UB 写入对下一轮可见，补充了 asc_vf_call 跨调用的数据依赖约束。
- [RegBase VF __simd_vf__ 路线致 bisheng 编译崩溃](../../../../../runbooks/compilation/regbase_vf_simd_vf_bisheng_exit139_banned.md)（`exemplifies`）：RegBase VF 编译崩溃卡记录 bisheng 在 __simd_vf__ 路线的后端失败，是选择 asc_vf_call/Reg 路线时必须识别的构建边界。
- [RegTensor 跨 VF 内循环累加失效 — 状态改存 UB 槽](../../../../../runbooks/precision/regtensor_cross_chunk_state_should_persist_in_ub_slot.md)（`exemplifies`）：RegTensor 跨 VF 内循环状态不能仅保留在寄存器对象中，案例将状态改存 UB 槽以跨 asc_vf_call 持久化。
- [VF 归约落 UB 后 GetValue 读取陈旧标量](../../../../../runbooks/precision/vector_scalar_ub_handoff_requires_explicit_completion.md)（`exemplifies`）：VF 归约落 UB 后 GetValue 读取陈旧标量 与《VF调用》的实质衔接是：Reg Reduce 经 StoreAlign 落 UB 后，PIPE_V 不保证 Scalar GetValue 可见；相关跨 VF 累加、barrier、GetValue 陈旧和 SoftMax 卡共同支持把归约与 lane0 广播保留在同一 VF。
- [arch35 count Compare Select 异步VF 存读 RAW](../../../../../runbooks/precision/arch35_count_compare_select_vf_raw.md)（`exemplifies`）：Compare/Select 异步 VF 案例说明连续 asc_vf_call 的生产者写和消费者读之间若缺少完成屏障会出现 RAW 精度错误。
- [dim3 未声明：显式引入 SIMT 公共头](../../../../../runbooks/compilation/asc_vf_call_launch_config_requires_simt_header.md)（`exemplifies`）：dim3 未声明卡直接针对 asc_vf_call 的 launchConfig，要求显式包含 SIMT 公共头以解析 VF 启动维度类型。
- [simd_vf 互调导致 helper 编译失败](../../../../../runbooks/compilation/simd_vf_helpers_use_simd_callee.md)（`exemplifies`）：simd_vf 互调导致 helper 编译失败 与《VF调用》的实质衔接是：顶层 __simd_vf__ 只能调用 __simd_callee__ helper；asc_vf_call、执行限定符、kernel/VF 指南和相邻 VF 编译故障共同固定三层调用结构。
- [分块 wrapper 与 VF callee 不可重复叠加 offset](../../../../../runbooks/precision/wrapper_and_vf_callee_must_not_double_apply_chunk_offset.md)（`exemplifies`）：分块 wrapper 与 VF callee 双重应用 offset 会让每次 asc_vf_call 的数据窗口偏移两次；该卡给出调用层与 callee 层的偏移职责划分。
- [嵌套 VF 循环触发 bisheng stack smashing ICE](../../../../../runbooks/compilation/vf_bisheng_stack_smashing_ice.md)（`exemplifies`）：嵌套 VF 循环触发编译器 stack smashing，给出复杂循环结构在 __simd_vf__ 后端 lowering 中的失败信号。
- [Reg矢量计算编程（C++ Tensor编程）](../../../../../guides/programming_guide/programming_model/ai_core_simd_programming/cpp_tensor_programming/reg_vector_computation.md)（`explains`）：Reg矢量计算编程（C++ Tensor编程） 与《VF调用》的实质衔接是：Reg C++ 编程仍遵循 asc_vf_call→__simd_vf__→Load/Compute/Store；C API 对照、性能/边界/merge/精度表和 helper 编译卡直接约束这一调用模型。
- [SIMD&SIMT BuiltIn关键字](../../../../../guides/programming_guide/language_extension/simd_simt_hybrid_builtin_keywords.md)（`explains`）：SIMD&SIMT BuiltIn关键字 与《VF调用》的实质衔接是：混合 BuiltIn 关键字需结合执行/地址限定、kernel/VF、内置变量和混合编程故障使用。
- [VfFusionOptimization](../../../../../guides/operator_practice/simd_operator_optimization/vector_compute/vf_optimization/vf_fusion_optimization.md)（`explains`）：VF 融合优化指南说明何时把相邻 VF 合并以减少启动和 UB 往返，可直接用于评估多次 asc_vf_call 的调度开销与融合条件。
- [VfLoopOptimization](../../../../../guides/operator_practice/simd_operator_optimization/vector_compute/vf_optimization/vf_loop_optimization.md)（`explains`）：VF 循环优化指南讨论将循环组织到 VF 内的收益和边界，补足 asc_vf_call 调用粒度与循环应由 wrapper 还是 VF 承担的决策。
- [核函数与VF函数（SIMD与SIMT混合编程）](../../../../../guides/programming_guide/advanced_programming/advanced_ai_core_programming_model/simd_simt_hybrid_programming/kernel_and_vf_functions.md)（`explains`）：焦点处理混合 SIMD/SIMT 中 kernel、VF、callee 的限定符和启动边界；VF调用正文说明“Reg矢量计算VF调用接口索引页，包含asc_vf_call”。候选明确 kernel/VF/callee 的允许调用方向、地址空间和 launch API，或给出同机制编译失败。
- [asc_vf_call](asc_vf_call.md)（`same_topic`）：VF 调用总览说明通过 asc_vf_call 从 __aicore__ 包装器启动 __simd_vf__，asc_vf_call 卡提供实际 launch 配置与调用签名。
<!-- cannbot:related:end -->
