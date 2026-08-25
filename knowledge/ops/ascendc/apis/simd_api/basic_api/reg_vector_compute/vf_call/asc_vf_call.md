---
type: API
title: asc_vf_call
description: 在SIMD编程场景下使用。用于启动SIMD VF（Vector Function）子任务。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/vf_call/asc_vf_call.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# asc_vf_call

在SIMD编程场景下使用。用于启动SIMD VF（Vector Function）子任务。

参数：funcPtr: 用于指定SIMD入口核函数。；Args: 定义可变参数，用于传递实参到SIMD入口核函数。；args(输入): 可变参数，用于传递实参到SIMD入口核函数。

约束：-   asc_vf_call启动SIMD VF子任务时，子任务函数不能是类的成员函数，推荐使用普通函数或类静态函数，且入口函数必须使用__simd_vf__修饰宏。
-   asc_vf_call启动SIMD VF子任务时，入参仅支持Ascend C的内置数据类型（half、int32_t、uint32_t、float等）及其组成的指针、数组、结构体类型，且指针类型必须指向UB内存。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Ascend950 Reg 扫描按 256B 锁定 lane](../../../../../runbooks/precision/dav3510_vector_register_width_is_256_bytes.md)（`exemplifies`）：Ascend950 Reg 扫描按 256B 锁定 lane 与《asc_vf_call》的实质衔接是：这些卡共同约束 256B RegTensor 的 lane 数、B16/B32 提升后的 mask 宽度以及 LoadAlign/VF 调用范围；所连错例均由按错误数据宽度计算 lane 或目标 VL 导致。
- [Reg 固定地址跨块累加需逐 VF PipeBarrier](../../../../../runbooks/precision/fixed_address_vf_accumulator_needs_per_call_barrier.md)（`exemplifies`）：运行卡展示连续 asc_vf_call 对固定 UB 累加槽执行读改写时需要逐调用提交/同步，补足跨 VF 调用的数据依赖约束。
- [RegBase VF __simd_vf__ 路线致 bisheng 编译崩溃](../../../../../runbooks/compilation/regbase_vf_simd_vf_bisheng_exit139_banned.md)（`exemplifies`）：RegBase VF __simd_vf__ 路线致 bisheng 编译崩溃 与《asc_vf_call》的实质衔接是：该卡定位 __simd_vf__ 加 Reg 调用导致 BiSheng 139/70；所选编译故障复现相邻 VF 崩溃机制，asc_vf_call、执行限定符和 Reg 编程材料解释受禁路线的真实契约。
- [VF 归约落 UB 后 GetValue 读取陈旧标量](../../../../../runbooks/precision/vector_scalar_ub_handoff_requires_explicit_completion.md)（`exemplifies`）：VF 归约落 UB 后 GetValue 读取陈旧标量 与《asc_vf_call》的实质衔接是：Reg Reduce 经 StoreAlign 落 UB 后，PIPE_V 不保证 Scalar GetValue 可见；相关跨 VF 累加、barrier、GetValue 陈旧和 SoftMax 卡共同支持把归约与 lane0 广播保留在同一 VF。
- [dim3 未声明：显式引入 SIMT 公共头](../../../../../runbooks/compilation/asc_vf_call_launch_config_requires_simt_header.md)（`exemplifies`）：《dim3 未声明：显式引入 SIMT 公共头》处理“混合 SIMD/SIMT 核函数调用 asc_vf_call 时，显式包含 common_functions.h 以暴露 dim3 别名和正确重载。”。《asc_vf_call》明确“在SIMD编程场景下使用。用于启动SIMD VF（Vector Function）子任务。”，可直接用于核对dim3 类型可见性、SIMT 公共头、__vector__ 入口与混合 VF 启动边界。
- [simd_vf 互调导致 helper 编译失败](../../../../../runbooks/compilation/simd_vf_helpers_use_simd_callee.md)（`exemplifies`）：simd_vf 互调导致 helper 编译失败 与《asc_vf_call》的实质衔接是：顶层 __simd_vf__ 只能调用 __simd_callee__ helper；asc_vf_call、执行限定符、kernel/VF 指南和相邻 VF 编译故障共同固定三层调用结构。
- [分块 wrapper 与 VF callee 不可重复叠加 offset](../../../../../runbooks/precision/wrapper_and_vf_callee_must_not_double_apply_chunk_offset.md)（`exemplifies`）：运行卡证明 wrapper 已偏移 UB 指针时 VF callee 不能再次叠加 chunk offset，明确 asc_vf_call 参数地址的责任边界。
- [双 VF 融合输出非预期 先排 CopyOut slot 勿用 PRINTF](../../../../../runbooks/precision/vf_fusion_output_unexpected_check_copyout_slot_not_printf.md)（`exemplifies`）：Runbook围绕 asc_vf_call 启动 __simd_vf__ 的实际融合排障，API 卡确认入口必须是非成员/静态函数、使用 __simd_vf__ 且指针指向 UB。
- [Reg矢量计算编程（C++ Tensor编程）](../../../../../guides/programming_guide/programming_model/ai_core_simd_programming/cpp_tensor_programming/reg_vector_computation.md)（`explains`）：Reg矢量计算编程（C++ Tensor编程） 与《asc_vf_call》的实质衔接是：Reg C++ 编程仍遵循 asc_vf_call→__simd_vf__→Load/Compute/Store；C API 对照、性能/边界/merge/精度表和 helper 编译卡直接约束这一调用模型。
- [SIMD&SIMT BuiltIn关键字](../../../../../guides/programming_guide/language_extension/simd_simt_hybrid_builtin_keywords.md)（`explains`）：SIMD&SIMT BuiltIn关键字 与《asc_vf_call》的实质衔接是：混合 BuiltIn 关键字需结合执行/地址限定、kernel/VF、内置变量和混合编程故障使用。
- [核函数与VF函数（SIMD与SIMT混合编程）](../../../../../guides/programming_guide/advanced_programming/advanced_ai_core_programming_model/simd_simt_hybrid_programming/kernel_and_vf_functions.md)（`explains`）：焦点处理混合 SIMD/SIMT 中 kernel、VF、callee 的限定符和启动边界；asc_vf_call正文说明“在SIMD编程场景下使用。用于启动SIMD VF（Vector Function）子任务”。候选明确 kernel/VF/callee 的允许调用方向、地址空间和 launch API，或给出同机制编译失败。
- [Reg矢量计算概述](../overview.md)（`related`）：《asc_vf_call》给出“在SIMD编程场景下使用。用于启动SIMD VF（Vector Function）子任务。”；该约束/探针可直接复现、解释或前置验证《Reg矢量计算概述》中的“Reg矢量计算API概述，直接操作Vector计算寄存器实现数据搬运与计算，较Memory矢量计算API提供更大开发自由度。”。
- [VF调用](vf_call.md)（`same_topic`）：VF 调用总览说明通过 asc_vf_call 从 __aicore__ 包装器启动 __simd_vf__，asc_vf_call 卡提供实际 launch 配置与调用签名。
<!-- cannbot:related:end -->
