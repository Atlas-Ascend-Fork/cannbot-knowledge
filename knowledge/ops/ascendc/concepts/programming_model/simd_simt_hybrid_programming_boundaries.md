---
type: Concept
title: SIMD 与 SIMT 混合编程的边界与约束
description: 同一算子里 SIMD 与 SIMT 混合编程的机制与边界：按"规则逐元素 vs 不规则含分支"分工，一般入口用 __global__ __aicore__，vector 场景用 __global__ __vector__，VF 经 asc_vf_call 启动，并受调用层级派生、__gm__/__ubuf__ 地址空间、block_num/dyn_ub_size 启动配置、Thread Block/Warp 与 UB 容量五类约束。
tags:
- task.design
- task.implementation
- topic.programming_model.execution_model.simt
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/SIMD_SIMT_hybrid_programming_intro/programming_model.md
  role: primary
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/SIMD_SIMT_hybrid_programming_intro/extended_syntax/function_execution_space_qualifier.md
  role: primary
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/SIMD_SIMT_hybrid_programming_intro/extended_syntax/kernel_function_config.md
  role: primary
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/SIMD_SIMT_hybrid_programming_intro/extended_syntax/memory_space_qualifier.md
  role: supporting
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/SIMT_programming_intro/programming_model.md
  role: supporting
created_at: '2026-10-23T01:53:00Z'
updated_at: '2026-10-27T16:44:00Z'
platforms: []
---

# SIMD 与 SIMT 混合编程的边界与约束

## 定义

SIMD 与 SIMT 混合编程，指在**同一个算子**内按算子特征做精细化映射：规则的逐元素（elementwise）计算可交给 SIMD，不规则或包含分支的计算可交给 SIMT。其中 SIMT 部分以 VF（Vector Function）子任务的形式被启动，由算子入口协调其调度与调用。

它面向"一个算子内部既有连续规整计算、又有离散访问"时的映射：来源文档将 SIMD 与 SIMT 的组合描述为有利于利用率、能效、融合和数据复用；这些是适用方向，不是对每个算子的性能保证。

## 机制与结构

### 1. 分工边界从哪来

- SIMD 基于向量寄存器与指令，单指令处理多数据，规则的逐元素计算可获得高带宽和高算力利用率。
- SIMT 以线程为最小调度单元，每个线程有独立控制流与地址计算能力，简化复杂算子与不规则控制流的开发。
- 混合的收益来源是系统层面的：提高硬件利用率与能效，并更便于做算子融合与数据复用。

### 2. 入口形态

- vector 计算单元混合编程场景的 Device 侧入口形如 `__global__ __vector__ void kernel_name(__gm__ type* param1, __gm__ type* param2, ...)`，其中 `__vector__` 是**必需**修饰符，标识函数在 Device 侧 AIV 核上执行。
- 若只有在 AIV 核内执行的 SIMD 与 SIMT 混合编程场景，可使用 `__global__ __vector__` 标识只启动 AIV 核；一般算子入口为 `__global__ __aicore__`（算子入口，协调 VF 执行）。
- 入口入参：支持指针类型（需 `__gm__` 修饰）和 AscendC 内置数据类型；指针参数必须指向 Global Memory。

### 3. 调用层级派生（谁能调用谁）

混合编程涉及的函数类型构成严格层级，越界调用即突破边界：

| 层 | 函数类型 | 调用方式 |
| --- | --- | --- |
| 算子入口 | `__global__ __aicore__` / `__global__ __vector__` | Host 侧通过 `<<<...>>>` 调用 |
| Device 侧辅助函数 | `__aicore__` | 核函数或同级函数调用 |
| 并行计算任务 | `__simt_vf__`（线程级）、`__simd_vf__`（向量级） | 分别通过 SIMT / SIMD 提供的 `asc_vf_call` 调用 |
| VF 子函数 | `__simt_callee__`、`__simd_callee__` | 仅由对应 VF 内部调用 |
| 编译期辅助函数 | `__callee__` | Device 侧函数内部均可调用 |

派生约束：SIMT VF 内**只能**调用 `__simt_callee__` 或 `__callee__` 函数；`__simt_callee__` 内同样只能调用 `__simt_callee__` 或 `__callee__`。VF 的入参有独立限制——仅支持 AscendC 内置数据类型及其组成的指针、数组、结构体类型，且指针必须指向 GM 或 UB。

### 4. 启动边界

- 启动 VF：`asc_vf_call<funcPtr>(dim3 threadNums, Args&&...args)`，`threadNums` 指定线程块内线程数量，总数 `x * y * z` 必须不大于 2048，建议为 32 的倍数；调用 SIMT VF 时需**显式指定 Thread Block 的维度信息**。
- 启动算子：`kernel_name<<<block_num, dyn_ub_size, stream>>>(args...)`，`block_num` 为 uint32_t、取值 `[1, 65535]`；`dyn_ub_size` 不超过 `256KB - 8KB - 32KB - 静态内存`。
- 因为 `block_num` 是 uint32_t，混合编程下 `gridDim` 是一维的（`gridDim.x = block_num`，`y`、`z` 均为 1）。核数超过物理核数时头尾开销会增大，来源强烈建议启动的 AIV 核数小于物理核数。
- `__launch_bounds__(N)` 可在 SIMT VF 入口配置，未配置时默认 1024，取值范围 1 到 2048，且需不小于各维度线程数之积；它决定每个线程可用的寄存器个数。

### 5. 地址空间边界

- `__gm__` 表示分配于设备侧全局内存的对象，可声明为指向标量或用户自定义结构体的指针；混合编程的核函数指针参数必须使用它修饰。
- `__ubuf__` 表示 Unified Buffer 上的动、静态内存；静态内存大小在编译期确定，动态内存大小在核函数执行时确定。
- 动态内存有两条申请路径——`extern __ubuf__` 动态数组，或 LocalMemAllocator 的 Alloc 接口；两者都从静态内存结束位置之后开始分配，**同时使用可能导致地址空间重叠并引发未定义行为，只能选择其中一种**。

### 6. SIMT 侧保留的执行约束

混合后，SIMT 侧的约束不会消失：Thread Block 最大 2048 个线程，线程数建议取 32 的整数倍；Warp 固定 32 线程，同一 Warp 内线程相互独立、不能存在依赖关系；发生分支发散时硬件串行执行各分支，只有活跃线程被执行。UB 总大小 256KB，按静态内存、动态内存、预留空间（8KB）、Data Cache 划分，Data Cache 小于 32KB 会出现校验报错。

## 适用与不适用

**适用**：同一个算子内既包含 SIMD 擅长的连续规整计算（规则 elementwise），也包含 SIMT 擅长的离散访问或不规则分支；需要评估按特征映射对利用率、能效、融合或数据复用的影响。

**不适用或需谨慎**：

- 计算全程规则连续时，应先评估是否需要引入 SIMT 及其 VF 启动开销；本卡没有性能实验，不能断言混合编程一定无收益。
- 核数与线程规模受硬边界约束：线程块总数不超过 65535、Thread Block 不超过 2048 线程、VF 的 `threadNums` 总数不超过 2048，且核数超过物理核数会因头尾开销增大而劣化。
- 分支发散、同 Warp 无依赖、32 整数倍建议等 SIMT 侧约束在混合后仍然生效，不是"用 SIMD 段就能绕过"的。
- UB 的划分约束同时服务于两侧：SIMT 侧 Data Cache 有 32KB 下限，动态内存两条申请路径不能并用，容量需要在设计阶段一并核算。

## 与其他概念的边界

- 与"纯 SIMT 编程"的边界：混合编程多了一层由 `asc_vf_call` 启动的 VF 子任务，且入口形态受 `__vector__` / `__aicore__` 的选择约束。
- 与"纯 SIMD 编程"的边界：混合编程允许算子内同时存在两套执行模型，因此必须显式处理两侧的地址空间与容量约束。
- 本卡只覆盖 **SIMD 与 SIMT 两种执行模型之间的边界**；SIMD 内部再往下的编程模型选择不在本卡来源范围内，本卡不做推导。

## 与相邻卡的分工

- [SIMT vs SIMD 决策框架](../simt_vs_simd_decision.md)：回答"该用 SIMT 还是 SIMD"的决策框架、速查表与实测案例；本卡回答"决定混起来之后，机制上允许什么、不允许什么"，**不重复选型判断**。
- [CANN 9.0.1 SIMT 入口类型无法派生—改混合 VF](../../runbooks/compilation/mixed_simt_requires_vector_shell_and_simt_vf.md)：纯 SIMT 全局入口无法完成 kernel 类型派生时的处置配方；本卡为其提供"入口形态与调用层级派生"的机制解释。
- [混合 SIMT 启动边界用 GM_ADDR 承接地址空间](../../runbooks/compilation/mixed_simt_launch_boundary_uses_gm_addr.md)：host launch 实参经 `GM_ADDR` 穿过 `__global__` wrapper、再由 device 侧恢复具体 `__gm__` 指针的配方；本卡为其提供第 5 节地址空间边界的机制解释。
- [AscendC SIMT 与 RegBase 术语表](../../../../common/glossaries/ascendc_simt_and_regbase_terminology.md)：本卡用到的 `__simt_vf__`、`asc_vf_call`、`__gm__`、Grid/Warp 等术语的稳定定义与检索别名归它。
- [AscendC 存储层次与执行单元术语表](../../../../common/glossaries/ascendc_memory_and_execution_terminology.md)：UB 作为存储单元的通用定义与存储层次归属归它；本卡只保留第 6 节那一条与混合编程容量约束直接相关的 UB 划分事实。

## 失效边界

- 本卡所列混合编程与 SIMT 介绍页面说明了函数类型、启动和容量约束，但没有声明整张卡的产品支持范围。固定提交的架构指南将 SIMT 列在 Ascend950 相关能力中，也不能单独证明这些页面只适用于 950，或证明其他平台不适用。因此本卡保留为 `draft`、`platforms: []`；消费前须补核目标版本的产品支持声明与编译证据，不按产品名称外推。
- 上表与约束以来源文档为准；具体 API 清单、工程化接入步骤与验证方法不在本卡范围，实际能力以目标 CANN 版本的公开文档、公开头文件和编译验证为准。
- 容量类数值（65535、2048、256KB、8KB、32KB、寄存器个数表）来自来源文档的当前表述，随版本可能变化，落地前需回查目标版本文档。
