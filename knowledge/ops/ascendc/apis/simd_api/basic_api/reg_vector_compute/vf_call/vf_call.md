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

- [Reg 固定地址跨块累加需逐 VF PipeBarrier](../../../../../runbooks/precision/fixed_address_vf_accumulator_needs_per_call_barrier.md)（`exemplifies`）：提供 asc_vf_call 接口，用于在 SIMD 编程场景下启动 SIMD VF（Vector Function）子任务。通过模板参数 funcPtr 指定入口核函数，可变参数 Args 传递实参。；- API 路径：`asc_vf_call` 调用 `__simd_vf__`，VF 内通过固定 `accAddr` 做 `LoadAlign→计算→StoreAlign` 的跨 chunk 累加；。API提供逐次 VF 调用及 UB 指针参数合同，Runbook利用调用边界在固定 UB 累加器的多 chunk 调用间插入 PipeBarrier。
- [dim3 未声明：显式引入 SIMT 公共头](../../../../../runbooks/compilation/asc_vf_call_launch_config_requires_simt_header.md)（`exemplifies`）：提供 asc_vf_call 接口，用于在 SIMD 编程场景下启动 SIMD VF（Vector Function）子任务。通过模板参数 funcPtr 指定入口核函数，可变参数 Args 传递实参。；先显式包含声明别名与重载的公共头，再使用三维聚合初始化调用带线程维度的 `asc_vf_call`。不要仅凭 `kernel_operator.h` 已被包含就假设 `dim3` 全局别名可见。。API定义 VF 启动入口及 __simd_vf__、UB 指针限制，Runbook闭合带 dim3 启动配置时所需的 SIMT 公共头和重载可见性。
- [simd_vf 互调导致 helper 编译失败](../../../../../runbooks/compilation/simd_vf_helpers_use_simd_callee.md)（`exemplifies`）：提供 asc_vf_call 接口，用于在 SIMD 编程场景下启动 SIMD VF（Vector Function）子任务。通过模板参数 funcPtr 指定入口核函数，可变参数 Args 传递实参。；`__simd_vf__` 是由 `asc_vf_call` 进入的顶层 VF 函数属性，被另一个 `__simd_vf__` 直接调用不满足编译器调用约束；可复用的 VF 内部 helper 必须声明为 `__simd_callee__`。。API要求 asc_vf_call 入口使用 __simd_vf__，Runbook进一步区分顶层 __simd_vf__ 与内部 __simd_callee__ 的调用层级。
- [分块 wrapper 与 VF callee 不可重复叠加 offset](../../../../../runbooks/precision/wrapper_and_vf_callee_must_not_double_apply_chunk_offset.md)（`exemplifies`）：提供 asc_vf_call 接口，用于在 SIMD 编程场景下启动 SIMD VF（Vector Function）子任务。通过模板参数 funcPtr 指定入口核函数，可变参数 Args 传递实参。；- API 路径：`LocalTensor::GetPhyAddr` → chunk pointer arithmetic → `asc_vf_call` → `LoadAlign`/`StoreAlign`。。API定义 asc_vf_call 的入口与实参传递，Runbook说明 wrapper 传已偏移 UB 指针时 callee 不得再次叠加同一 offset。
<!-- cannbot:related:end -->
