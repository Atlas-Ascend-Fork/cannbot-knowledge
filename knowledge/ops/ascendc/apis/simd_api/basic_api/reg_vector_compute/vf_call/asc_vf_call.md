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

- [RegBase VF __simd_vf__ 路线致 bisheng 编译崩溃](../../../../../runbooks/compilation/regbase_vf_simd_vf_bisheng_exit139_banned.md)（`exemplifies`）：“在用 ops-registry-invoke-glacier 工作流（ACLNN 算子仓开发路线）实现 `add` 算子（`out = self + alpha*other`，Broadcast 范式）时，按 DESIGN.md §3.5 的 RegBase 路线编写 kernel 头 `operators/add_package/op_kernel/arch35/add_kernel.h`：把逐元素加法 fusion 链封装成一个 VF 函数 `AddVF`，用 `__simd_vf__ inline` 标注，函数体内调用 `AscendC::Reg::Add` / `AscendC::Reg::Muls`（参数为 `AscendC::Reg::RegTensor<T>`），并由 Process 通过 `AscendC::asc_vf_call<AddVF<T>>(...)` 调用。目标芯片 `ascend950`，架构 `DAV_3510` / arch35，CANN 9.1.0。”记录按普通 `__simd_vf__` 函数调用 asc_vf_call 仍触发毕昇 139/70 的平台实测；“约束：- asc_vf_call启动SIMD VF子任务时，子任务函数不能是类的成员函数，推荐使用普通函数或类静态函数，且入口函数必须使用__simd_vf__修饰宏。”给出接口层的函数形态合同。两端一起表明该实现虽满足公开签名，仍需在指定 950/CANN 版本回退 LocalTensor 基础向量 API。
- [dim3 未声明：显式引入 SIMT 公共头](../../../../../runbooks/compilation/asc_vf_call_launch_config_requires_simt_header.md)（`exemplifies`）：在SIMD编程场景下使用。用于启动SIMD VF（Vector Function）子任务。；选择显式包含 `simt_api/common_functions.h`，因为它同时解决类型别名与带线程维度的 `asc_vf_call` 重载可见性，机制闭环比只把调用点改成 `cce::dim3` 更完整。API 说明启动职责，runbook 给出混合 SIMD/SIMT 带线程维度重载的头文件前置条件与可复现编译信号。
- [simd_vf 互调导致 helper 编译失败](../../../../../runbooks/compilation/simd_vf_helpers_use_simd_callee.md)（`exemplifies`）：在SIMD编程场景下使用。用于启动SIMD VF（Vector Function）子任务。；顶层函数继续保留 `__simd_vf__` 并由 `asc_vf_call` 进入；API 给出顶层 VF 启动，runbook 明确被启动入口与内部 `__simd_callee__` helper 的调用层级，能闭合编译器属性诊断。
- [分块 wrapper 与 VF callee 不可重复叠加 offset](../../../../../runbooks/precision/wrapper_and_vf_callee_must_not_double_apply_chunk_offset.md)（`exemplifies`）：在SIMD编程场景下使用。用于启动SIMD VF（Vector Function）子任务。；为每个 `asc_vf_call` 写出有效地址代数；调用前后的 offset 总和必须恰好出现一次。API 定义 VF 启动点，runbook 约束 wrapper 与 callee 的地址责任，可直接诊断多 chunk 从第二块开始错位。
<!-- cannbot:related:end -->
