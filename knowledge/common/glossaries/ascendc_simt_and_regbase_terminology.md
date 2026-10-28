---
type: Glossary
title: AscendC SIMT 与 RegBase 术语表
description: AscendC SIMT 与 SIMD/SIMT 混合编程术语的定义与检索别名：SIMT、SIMD、混合编程、RegBase、Grid/Thread Block/Warp/Thread、分支发散、__simt_vf__/__simd_vf__/__simt_callee__、asc_vf_call、__gm__/__ubuf__、UB 四区、__NPU_ARCH__ 等；Membase 的细节与选型归相邻卡。
tags:
- task.lookup
- topic.terminology
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/SIMT_programming_intro/programming_model.md
  role: primary
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/SIMD_SIMT_hybrid_programming_intro/programming_model.md
  role: primary
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/SIMD_SIMT_hybrid_programming_intro/extended_syntax/function_execution_space_qualifier.md
  role: primary
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/SIMD_SIMT_hybrid_programming_intro/extended_syntax/kernel_function_config.md
  role: primary
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/SIMD_SIMT_hybrid_programming_intro/extended_syntax/builtin_variables.md
  role: supporting
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/SIMT_programming_intro/extended_syntax/memory_space_qualifier.md
  role: supporting
- resource: https://gitcode.com/cann/asc-devkit/blob/e680c34c09ba6919b3cebd2b7ec027f4ff6f0f22/.agent/skills/asc-npu-arch/references/npu-arch-guide.md
  role: supporting
created_at: '2026-10-23T01:52:00Z'
updated_at: '2026-10-27T16:44:00Z'
---

# AscendC SIMT 与 RegBase 术语表

本卡登记 AscendC SIMT 与 SIMD/混合编程相关术语的**稳定定义**与**检索别名**（同一概念在文档与代码里的多种写法），用于统一检索入口、消除同义写法造成的歧义。术语的选型判据、调用层级与实现步骤不在本卡，见文末"与相邻卡的分工"。

## 适用范围

- 术语取自 SIMT 编程介绍、SIMD 与 SIMT 混合编程介绍两套公开文档，以及 NPU 架构代际说明。
- 两个来源对同一术语的表述不一致时，本卡并列给出，不擅自取舍。
- 本卡只回答"这个词指什么、还有哪些写法"，不回答"该怎么选、该怎么写代码"。

## 一、并行与编程模型

| 术语 | 稳定定义 | 检索别名 / 近义写法 |
| --- | --- | --- |
| SIMT | 线程级并行编程模型：以线程为最小调度单元，每个线程拥有独立的控制流与地址计算能力，适合控制流复杂、访存模式不规则的算子场景；提供原子操作和线程间内存屏障，支撑多线程对同一片内存的安全并发访问。 | SIMT 编程、SIMT 编程模型、线程级并行 |
| SIMD | 基于向量寄存器与指令的数据并行方式，即单指令处理多数据，用于提升每周期的吞吐量；规则的逐元素（elementwise）计算可获得高带宽和高算力利用率。 | SIMD 编程、向量化、单指令处理多数据 |
| SIMD 与 SIMT 混合编程 | 在同一算子里按算子特征做精细化映射：规则连续的逐元素计算可交给 SIMD，不规则或含分支的计算可交给 SIMT，从而在同一算子中组合两种执行模型。是否有收益取决于目标算子和配置。 | 混合编程、SIMD/SIMT 混合、混合 VF |
| RegBase | 来源术语表将其定义为基于寄存器的架构：中间结果可暂存在寄存器中；架构指南将直接操作寄存器的编程能力列为 Ascend950（DAV_3510）相关能力之一，并将 `ascend950pr_9599` 标为"当前 regbase / SIMT 主入口"。这不是排除其他平台的支持声明。 | Regbase、Regbase 编程、寄存器编程 |

## 二、线程层次、调度与内置变量

| 术语 | 稳定定义 | 检索别名 / 近义写法 |
| --- | --- | --- |
| Grid（线程块网格） | 线程层次结构的最顶层，由多个 Thread Block 组成；维度配置由用户设置的启动 AIV 核数决定，核函数执行期间不可更改；所有线程块尺寸与维度相同，相互独立、按任意顺序执行；线程块总数不超过 65535。 | grid、网格、线程块网格、blocks_per_grid |
| Thread Block（线程块） | Grid 的组成单元，最大 2048 个线程；同一线程块内的线程可访问共享内存（UB）并借助同步机制协作；线程数建议取 32 的整数倍，否则最后一个 Warp 会含空闲线程通道。 | block、线程块、threads_per_block |
| Warp（线程束） | SIMT 架构中基本的调度和执行单位，固定包含 32 个线程；同一 Warp 内的所有线程执行同一条指令，且彼此独立、不能存在依赖关系。 | warp、线程束、warpSize |
| Thread（线程） | 线程层次结构中的最小单元，每个线程独立完成计算任务，拥有独立的寄存器和栈空间。 | thread、线程 |
| 分支发散（Warp Divergence） | Warp 内的线程通过条件分支进入不同执行路径的现象。发生分支发散时硬件串行执行每个分支路径，只有进入当前分支的活跃线程被执行、其余线程被屏蔽，Warp 执行效率随之下降。 | 分支发散、发散、divergence |
| dim3 | 内置结构体类型，由 3 个无符号整数 `x`、`y`、`z` 组成，三维总数为 `x * y * z`；可用 `dim3(x)`、`dim3(x, y)`、`dim3(x, y, z)` 构造一维/二维/三维结构。 | dim3 结构体、dim3 类型 |
| gridDim / blockDim / blockIdx / threadIdx | 仅 Device 侧可用的 dim3 类型内置变量：`gridDim` 为整个计算任务在各维度上的线程块数量；`blockDim` 为线程块中三个维度的线程数；`blockIdx` 为当前线程块在网格中的位置坐标；`threadIdx` 为当前线程在线程块内部的索引。 | 内置索引变量、线程索引、thread index |
| warpSize | `const int32_t` 类型内置变量，表示一个线程束（Warp）中的线程数量，当前为固定值 32。 | warp 大小、线程束大小 |

索引约定（检索常用）：一维时 `idx = blockIdx.x * blockDim.x + threadIdx.x`；二维时 `x_index = blockIdx.x * blockDim.x + threadIdx.x`、`y_index = blockIdx.y * blockDim.y + threadIdx.y`。`threadIdx.x` 范围为 `[0, blockDim.x)`；`blockIdx.x` 范围为 `0` 到 `gridDim.x - 1`，`blockIdx.y`、`blockIdx.z` 目前只能返回 0。

## 三、函数类型与调用

| 术语 | 稳定定义 | 检索别名 / 近义写法 |
| --- | --- | --- |
| `__global__` | 函数执行空间限定符，修饰核函数入口，只能被 Host 侧函数调用；返回类型必须为 `void`，不能是 class、struct 或 union 的成员函数，不支持递归调用，且调用是异步的。 | global 函数、核函数限定符 |
| `__vector__` | vector 计算单元混合编程场景中的必需修饰符，标识函数在 Device 侧 AIV 核上执行；该场景下入口写作 `__global__ __vector__`。 | vector 修饰符、AIV 入口标识 |
| `__aicore__` | 函数执行空间限定符，修饰的函数只能在 Device 侧执行，只能被 `__global__` 函数或其他 `__aicore__` 函数调用；在混合编程中对应"Device 侧辅助函数"。 | aicore 函数、Device 侧函数 |
| `__simt_vf__` | 标记 SIMT VF（线程级并行计算任务）入口函数，函数无返回值；使用 `asc_vf_call` 调用以启动 VF 子任务，函数内可使用 SIMT 内置变量；入参仅支持 AscendC 内置数据类型及其组成的指针、数组、结构体，且指针必须指向 GM 或 UB；VF 内只能调用 `__simt_callee__` 或 `__callee__` 函数。 | SIMT VF、VF 入口函数、simt_vf |
| `__simt_callee__` | SIMT VF 函数内部调用的辅助函数，函数内部可使用 SIMT 内置变量；入参仅支持 AscendC 内置数据类型及对应的指针类型，返回值也只能是内置数据类型及对应的指针类型；函数内只能调用 `__simt_callee__` 或 `__callee__`。 | simt callee、VF 子函数 |
| `__simd_vf__` | 标记向量级并行计算任务，通过 SIMD 提供的 `asc_vf_call` 接口调用。 | SIMD VF、simd_vf |
| `__simd_callee__` | SIMD VF 的子函数，在 SIMD VF 内部调用。 | simd callee |
| `__callee__` | 编译期执行的 Device 侧辅助函数，Device 侧函数内部均可调用。 | callee 函数 |
| `asc_vf_call` | 启动 VF 子任务的接口：混合编程中用 `asc_vf_call<funcPtr>(dim3 threadNums, Args&&...args)` 启动 SIMT VF，`threadNums` 指定线程块内线程数量，总数 `x * y * z` 必须不大于 2048 且建议为 32 的倍数；SIMD 侧另提供 `asc_vf_call` 用于启动 `__simd_vf__`。调用 SIMT VF 时需显式指定 Thread Block 的维度信息。 | VF 调用、启动 VF、vf call |
| `<<<...>>>` 内核调用符 | Host 侧启动核函数的语法。SIMT 形式为 `<<<blocks_per_grid, threads_per_block, dyn_ubuf_size, stream>>>`（4 个参数）；混合编程形式为 `kernel_name<<<block_num, dyn_ub_size, stream>>>(args...)`，其中 `block_num` 为 uint32_t、取值 `[1, 65535]`，`dyn_ub_size` 不超过 `256KB - 8KB - 32KB - 静态内存`。混合编程下 `block_num` 是 uint32_t，因此 `gridDim` 是一维的。 | 内核调用符、kernel launch、执行配置 |
| `__launch_bounds__(N)` | 在核函数（SIMT）或 SIMT VF 入口函数（混合编程）上可选配置的标记宏，用于编译期指定启动的最大线程数；未配置时默认 1024，`N` 取值范围 1 到 2048 且需不小于各维度线程数之积。最大线程数决定每个线程可用的寄存器个数：1025~2048 对应 16，513~1024 对应 32，257~512 对应 64，1~256 对应 127。 | launch bounds、启动边界、最大线程数配置 |

## 四、地址空间与 UB 内存

| 术语 | 稳定定义 | 检索别名 / 近义写法 |
| --- | --- | --- |
| `__gm__` | 混合编程地址空间限定符，表示分配于设备侧全局内存（Global Memory）的对象，可声明为指向标量或用户自定义结构体的指针；混合编程的核函数指针参数必须使用它修饰。 | gm 限定符、全局内存限定符 |
| `__ubuf__` | 地址空间限定符，表示 Unified Buffer 上的动、静态内存；静态内存大小在编译期确定。固定来源对动态内存的确定时机分别写作“核函数启动时”和“核函数执行时”，本卡保留该差异，不将两种表述合并成单一规则。 | ubuf 限定符、UB 地址空间 |
| UB（Unified Buffer） | 本卡只登记它在**混合编程语境**下的一面：同一线程块内所有线程均可访问的共享内存，位于每个 AIV 内部，总大小 256KB。UB 作为存储层次单元的通用定义归 [AscendC 存储层次与执行单元术语表](ascendc_memory_and_execution_terminology.md)。 | Unified Buffer、统一缓冲区、共享内存 |
| 静态内存 | UB 中从起始地址分配、大小在编译期确定且不可动态修改的一段内存，通过数组分配，例如 `__ubuf__ half staticBuf[1024];`。 | static 内存、编译期内存 |
| 动态内存 | UB 中位于静态内存之后、大小在核函数启动时配置的一段内存，通过 `<<<>>>` 的 `dyn_ubuf_size` / `dyn_ub_size` 指定；混合编程中可用 `extern __ubuf__` 数组或 LocalMemAllocator 的 Alloc 接口申请，两者地址空间可能重叠，只能选择其中一种。 | dynamic 内存、动态共享内存 |
| 预留空间 | UB 中系统预留的固定 8KB 空间。 | reserved 空间、系统预留 |
| Data Cache | SIMT 专有的 UB 区域：`DataCache = min(UB 总大小(256KB) - 静态内存 - 动态内存 - 预留空间(8KB), 128KB)`，剩余空间超过 128KB 时固定为 128KB；若小于 32KB 会出现校验报错。 | 数据缓存、DCache |

## 五、架构标识（只保留锁定 RegBase / SIMT 归属所需的最小集）

| 术语 | 稳定定义 | 检索别名 / 近义写法 |
| --- | --- | --- |
| `__NPU_ARCH__` | Device 侧编译宏，四位数值，用于在编译期区分架构能力的条件编译。 | NPU 架构宏、架构条件编译宏 |
| 3510 / ascend950pr_9599 | `3510` 是 Ascend950 的 `__NPU_ARCH__` 取值（对应 `ASCEND950`、Ascend950DT/PR）；`ascend950pr_9599` 是其统一芯片调用名，备注为"当前 regbase / SIMT 主入口"。 | arch35、950PR、950DT |

架构指南将 RegBase 与 SIMT 列在 Ascend950 相关能力中，因此本卡只登记上面两个标识，不从该条目推断跨平台支持或独占性。架构代号别名（A2/A3/A5）、`SocVersion`、`NpuArch` 与完整统一调用名映射归 [AscendC 芯片别名与 NpuArch 映射表](../platforms/concepts/ascendc_chip_alias_and_npu_arch_map.md)，本卡不重复定义。

## 术语边界：本卡不定义的词

- **Membase**（近义写法 `MemBase`、memory-based）：登记归档的通用术语表确有 Membase 的简要定义，但本卡不展开其支持范围、调用层级与选型判据；这些细节由 [Membase vs Regbase 选型卡](../../ops/ascendc/optimizations/ol_196_membase_vs_regbase_simd_vf_selection.md) 及目标版本 API 文档负责。
- **Reg 矢量计算 / MicroAPI** 等具体 API 名称不在本卡范围：本卡只登记 `RegBase` 这一能力术语本身的定义（见第一节），不展开其 API 体系。

## 与相邻卡的分工

- [SIMT vs SIMD 决策框架](../../ops/ascendc/concepts/simt_vs_simd_decision.md)：按算子特征决定"用 SIMT 还是 SIMD"的决策框架与实测案例；本卡只提供该决策所需术语的**定义与别名**，不做选型判断。
- [AscendC 存储层次与执行单元术语表](ascendc_memory_and_execution_terminology.md)：GM/L1/L0A/L0B/L0C/UB 等**存储单元**与 Cube/Vector/Scalar、AIC/AIV 等**执行单元**的术语归它；本卡只保留混合编程语境所需的 UB 内部划分与地址空间限定符，不重复存储层次定义。
- [AscendC 芯片别名与 NpuArch 映射表](../platforms/concepts/ascendc_chip_alias_and_npu_arch_map.md)：统一调用名、`SocVersion`、`__NPU_ARCH__` 与产品别名的完整映射归它；本卡只登记锁定 RegBase/SIMT 归属所需的最小架构标识。
- [Membase vs Regbase 选型 + Reg vector `__simd_vf__` 编程入口](../../ops/ascendc/optimizations/ol_196_membase_vs_regbase_simd_vf_selection.md)：归档术语表有 Membase 的简要定义；两种模型的详细定义、调用层级与选型判据归该卡，本卡不展开细节。
- [A5/arch35 SIMD 计算链默认走 REGBASE 的实测边界](../../ops/ascendc/optimizations/ol_245_simd_chains_regbase_vs_membase.md)：RegBase 的收益条件与实测数据；本卡不承载性能结论。
- [arch35 RegBase VF 逐元素算子完整实现模式](../../ops/ascendc/runbooks/compilation/arch35_regbase_vf_elementwise_pattern.md)：RegBase VF 的实现骨架与工程步骤；本卡不写操作步骤。

## 失效边界

- 本卡是**术语登记**，不是规范：定义的最终依据始终是目标 CANN 版本的公开文档与公开头文件，术语表只用于检索与消歧。
- 两个来源表述不一致处（如 `__ubuf__` 动态内存的确定时机），本卡并列保留，不代替目标版本文档下结论。
- 本卡词条以所列 SIMT、混合编程介绍及固定提交架构指南为主；通用术语表虽定义 Membase，本卡只作职责导航，不据此推导其平台支持或实现模式。
