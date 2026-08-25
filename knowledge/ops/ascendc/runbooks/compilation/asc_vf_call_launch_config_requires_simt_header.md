---
type: "Runbook"
title: "dim3 未声明：显式引入 SIMT 公共头"
description: "混合 SIMD/SIMT 核函数调用 asc_vf_call 时，显式包含 common_functions.h 以暴露 dim3 别名和正确重载。"
tags: ["task.debugging", "topic.implementation.api_layer.simt_api", "topic.compilation"]
status: stable
sources: []
created_at: "2026-08-14T03:13:06Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# dim3 未声明：显式引入 SIMT 公共头

## 现象

在 Ascend950 Flash 直调工程中编译一个“外层 `__global__ __aicore__ __vector__` 核函数调用 `asc_vf_call<__simt_vf__>`”的混合实现时，`gather.asc` 已经包含 `kernel_operator.h`，但在 `dim3(threadNum)` 处停止编译。远程 CANN 9.0.1 编译器原样报告：

```text
gather.asc:102:9: error: use of undeclared identifier 'dim3'; did you mean 'cce::dim3'?
        dim3(threadNum),
        ^
__clang_cce_simt.h:29:40: note: 'cce::dim3' declared here
typedef __device_builtin__ struct dim3 dim3;
```

当时代码已经有完整的 SIMT VF 与外层 block kernel，失败不是模板参数、gather 地址计算或 host schema 引起，而是调用点所需类型与重载没有进入当前翻译单元的可见范围。

## 适用场景

- 工程形态：Flash kernel 直调工程；Torch 扩展 host 与 Ascend C kernel 同一 `.asc` 翻译单元。
- API 路径：`__global__ __aicore__ __vector__` 外层核函数 → `asc_vf_call<__simt_vf__>(dim3, args...)`。
- 验证过的平台与版本：Ascend950PR_957c（平台注册值 `950`），CANN 9.0.1，`NpuArch=dav-3510`。
- 适用粒度：`operator_family`；适用于需要从 Vector 外层启动 SIMT VF 的混合编程算子，不依赖 gather 数学语义。
- 路线优先级：`safety_fallback`。这是 fallback，性能不是最优，追求性能请用另一路线（见 ## 相关）。
- 明确不适用 / 未验证场景：纯 SIMT 独立样例、无需 `asc_vf_call` 的核函数，以及 CANN 9.0.1 之外版本均未验证。

## 根因

CANN 9.0.1 混合 ASC 翻译单元仅含 kernel_operator.h 时，global dim3 alias 与 launch-config asc_vf_call overload 不可见；调用前须包含 SDK SIMT 公共/聚合头。cce::dim3 提示与 __vector__ qualifier 不是等价修复。

## 解决配方

先显式包含声明别名与重载的公共头，再使用三维聚合初始化调用带线程维度的 `asc_vf_call`。不要仅凭 `kernel_operator.h` 已被包含就假设 `dim3` 全局别名可见。

### before

revision: pre-fix trace write（Git revision 未在轨迹中记录）
path: `operators/gather/gather.asc`
symbol: `gather_kernel<X_T, IDX_T>`
line span: 96–105

```cpp
template <typename X_T, typename IDX_T>
__global__ __aicore__ __vector__ void gather_kernel(
    GM_ADDR x, GM_ADDR index, GM_ADDR y, GM_ADDR params,
    int64_t outputTotal, int32_t ndim, int32_t dim, uint32_t threadNum)
{
    asc_vf_call<gather_simt<X_T, IDX_T>>(
        dim3(threadNum),
        (__gm__ const X_T*)x, (__gm__ const IDX_T*)index, (__gm__ X_T*)y,
        (__gm__ const int64_t*)params, outputTotal, ndim, dim);
}
```

pre-fix include region（revision: pre-fix trace write；path: `operators/gather/gather.asc`；symbol: translation-unit includes；line span: 31–38）：

```cpp
#include <tuple>
#include <algorithm>
#include <vector>
#include <cstring>
#include <torch/extension.h>
#include "torch_npu/csrc/core/npu/NPUStream.h"
#include "kernel_operator.h"
#include "platform/platform_ascendc.h"
```

### after

revision: `76b4eab`（轨迹记录的短 Git revision）
path: `operators/gather/gather.asc`
symbol: `gather_kernel<X_T, IDX_T>`
line span: 111–119

```cpp
template <typename X_T, typename IDX_T>
__global__ __aicore__ __vector__ void gather_kernel(
    GM_ADDR x, GM_ADDR index, GM_ADDR y, GM_ADDR params,
    int64_t outputTotal, int32_t ndim, int32_t dim, uint32_t threadNum)
{
    asc_vf_call<gather_simt<X_T, IDX_T>>(
        dim3{threadNum, 1, 1},
        (__gm__ const X_T*)x, (__gm__ const IDX_T*)index, (__gm__ X_T*)y,
        (__gm__ const int64_t*)params, outputTotal, ndim, dim);
}
```

fixed include（revision: `76b4eab`, path: `operators/gather/gather.asc`, line 46, symbol: translation-unit include）：

```cpp
#include "simt_api/common_functions.h"   // dim3 alias + asc_vf_call(dim3, ...) -> cce::async_invoke
```

## 设计决策

1. 选择显式包含 `simt_api/common_functions.h`，因为它同时解决类型别名与带线程维度的 `asc_vf_call` 重载可见性，机制闭环比只把调用点改成 `cce::dim3` 更完整。
2. 轨迹中曾尝试改成纯 SIMT 并增加 `--enable-simt`，但该路线随后触发 `kernel_tpipe.h` 缺失的新编译错误，因此被放弃。
3. 当前方案属于 `safety_fallback`：它保证混合 SIMT 路线正确编译和执行，但轨迹中的任务级评测显示其性能明显低于优化基线。

## 系统信息

- toolchain：CANN 9.0.1，BiSheng/ASC，`dav-3510`。
- 目标平台：Ascend950PR_957c。
- 相关文件：`operators/gather/gather.asc`、`CMakeLists.txt`；诊断时读取 CANN 安装中的 `simt_api/common_functions.h` 与 `__clang_cce_simt.h`。
- 代码提交：轨迹只给出实现提交短哈希 `76b4eab`，未给出完整 40 位 revision 或固定 blob URL。

## 性能影响

最终混合 SIMT fallback 在同一任务、同一 950 平台上相对评测基线平均约 `0.02x`（来源平台: 950；证据等级: tool_observed）。这是成对的任务内路线代价，不是可迁移的通用性能预期。

## 预防

- 写 `asc_vf_call<vf>(dim3{...}, ...)` 前，确认翻译单元显式包含 `simt_api/common_functions.h`。
- 同时核对可见的 `asc_vf_call` 是否真有 `dim3` 首参重载，不要只确认函数名存在。
- 对 `cce::async_invoke` 的调用契约按“线程维度写 launch info，VF 只接收余下 `Args...`”理解，避免给 VF 错加 `dim3` 业务形参。
- 修复后至少同时验证编译链接、真机测试与完整任务评测，不能把仅消失的语法错误当成功闭环。

## 验证信号

来源说明：这条知识来自一次 Ascend950 Flash gather 直调工程的首次远程编译、CANN 头文件核对和修复后全链路验证。

- 首次远程构建稳定报告 `use of undeclared identifier 'dim3'`，并提示唯一可见声明是 `cce::dim3`（来源平台: 950；证据等级: tool_observed）。
- 远程读取 CANN 9.0.1 `simt_api/common_functions.h`，观察到 `using dim3 = cce::dim3` 与 `asc_vf_call(dim3 threadNums, Args&&...)` 的完整定义（来源平台: 950；证据等级: tool_observed）。
- 最终远程构建完成 `Linking ASC shared library libop_gather.so` 与 `Built target op_gather`（来源平台: 950；证据等级: tool_observed）。
- 修复后真机 pytest 为 50/50 通过，完整 cann-bench 为 20/20 通过且精度误差为零（来源平台: 950；证据等级: tool_observed）。

- 独立复现 R1：工具报告 [100%] Built target op_gather。该信号仅归属于本来源列出的精确编辑。（950，tool_observed）。
- 独立复现 R2：工具报告 [100%] Built target op_cummin。该信号仅归属于本来源列出的精确编辑。（950，tool_observed）。

## 失效边界

- 本结论验证于 CANN 9.0.1；其他 CANN 版本可能调整 include 聚合关系，未验证，推断可迁移。
- 纯 SIMT 独立工程的入口、编译选项和可用头文件与混合工程不同，不应直接套用。
- 该修复只解决声明与重载可见性，不证明 SIMT fallback 是性能最优路线。

## 坏实践

- 为绕过一个未限定类型名错误，直接把整个 Flash 翻译单元切成 `--enable-simt`；这会改变编译模型，并可能把局部头文件问题扩大为工具链头文件不可用。
- 只把 `dim3` 改成 `cce::dim3`，却不核对带 `dim3` 首参的 `asc_vf_call` 重载是否可见；类型名通过后仍可能匹配错误调用路径。

## 误诊

最初把报错理解成“应该改用纯 SIMT kernel 入口”，但工具输出只证明 `dim3` 未声明；远程头文件证据表明缺失的是公共头暴露的别名和重载，而不是 gather 算法必须切换执行模型。

<!-- cannbot:related:start -->
## 相关

- [VF调用](../../apis/simd_api/basic_api/reg_vector_compute/vf_call/vf_call.md)（`exemplifies`）：dim3 未声明卡直接针对 asc_vf_call 的 launchConfig，要求显式包含 SIMT 公共头以解析 VF 启动维度类型。
- [asc_vf_call](../../apis/simd_api/basic_api/reg_vector_compute/vf_call/asc_vf_call.md)（`exemplifies`）：《dim3 未声明：显式引入 SIMT 公共头》处理“混合 SIMD/SIMT 核函数调用 asc_vf_call 时，显式包含 common_functions.h 以暴露 dim3 别名和正确重载。”。《asc_vf_call》明确“在SIMD编程场景下使用。用于启动SIMD VF（Vector Function）子任务。”，可直接用于核对dim3 类型可见性、SIMT 公共头、__vector__ 入口与混合 VF 启动边界。
- [内置数据类型](../../apis/simt_api/simd_simt_hybrid_programming_intro/extended_syntax/builtin_data_types.md)（`exemplifies`）：《dim3 未声明：显式引入 SIMT 公共头》处理“混合 SIMD/SIMT 核函数调用 asc_vf_call 时，显式包含 common_functions.h 以暴露 dim3 别名和正确重载。”。《内置数据类型》明确“SIMD与SIMT混合编程提供了一系列适用于Device侧的数据类型，包括标量、短向量和dim3结构体。”，可直接用于核对dim3 类型可见性、SIMT 公共头、__vector__ 入口与混合 VF 启动边界。
- [扩展语法内置变量](../../apis/simt_api/simd_simt_hybrid_programming_intro/extended_syntax/builtin_variables.md)（`exemplifies`）：扩展语法内置变量 与《dim3 未声明：显式引入 SIMT 公共头》的实质衔接是：dim3 内置变量依赖扩展语法、核函数配置和公共头暴露；SIMT/mixed-SIMT 指南及 dim3 编译故障给出实际声明与使用链。
- [核函数配置](../../apis/simt_api/simd_simt_hybrid_programming_intro/extended_syntax/kernel_function_config.md)（`exemplifies`）：《dim3 未声明：显式引入 SIMT 公共头》处理“混合 SIMD/SIMT 核函数调用 asc_vf_call 时，显式包含 common_functions.h 以暴露 dim3 别名和正确重载。”。《核函数配置》明确“核函数是SIMD与SIMT混合编程的Device侧入口函数，负责协调整个算子的执行流程，包括VF的调度和调用。vector计算单元的混合编程场景下，函数定义语法为：”，可直接用于核对dim3 类型可见性、SIMT 公共头、__vector__ 入口与混合 VF 启动边界。
- [核函数配置](../../apis/simt_api/simt_programming_intro/extended_syntax/kernel_function_config.md)（`exemplifies`）：《核函数配置》的任务是“核函数是SIMT编程的Device侧入口函数，负责协调整个算子的执行流程。函数定义语法为：”。《dim3 未声明：显式引入 SIMT 公共头》具体提供“混合 SIMD/SIMT 核函数调用 asc_vf_call 时，显式包含 common_functions.h 以暴露 dim3 别名和正确重载。”，它直接用于SIMT Kernel 入口的执行/内存限定符、内置变量和 launch 头文件。
- [CANN 9.0.1 SIMT 入口类型无法派生—改混合 VF](mixed_simt_requires_vector_shell_and_simt_vf.md)（`related`）：《dim3 未声明：显式引入 SIMT 公共头》处理“混合 SIMD/SIMT 核函数调用 asc_vf_call 时，显式包含 common_functions.h 以暴露 dim3 别名和正确重载。”。《CANN 9.0.1 SIMT 入口类型无法派生—改混合 VF》明确“CANN 9.0.1 的混合 ASC 动态库中，纯 SIMT 全局入口无法稳定完成 kernel 类型派生；改用 Vector 入口承载 SIMT VF 和三参数 launch。”，可直接用于核对dim3 类型可见性、SIMT 公共头、__vector__ 入口与混合 VF 启动边界。
- [Gather算子快速入门](../../guides/getting_started/quick_start/simt_programming/gather_op_quick_start.md)（`related`）：Gather算子快速入门 与《dim3 未声明：显式引入 SIMT 公共头》的实质衔接是：Gather 快速入门覆盖 SIMT kernel、host launch 和构建；所连 Gather API、维度/步长/地址空间错例和 SIMT 入口约束都直接作用于该示例的实现或验证。
- [SIMT BuiltIn关键字](../../guides/programming_guide/language_extension/simt_builtin_keywords.md)（`related`）：《dim3 未声明：显式引入 SIMT 公共头》处理“混合 SIMD/SIMT 核函数调用 asc_vf_call 时，显式包含 common_functions.h 以暴露 dim3 别名和正确重载。”。《SIMT BuiltIn关键字》明确“函数执行空间限定符（Function Execution Space Qualifier）指示函数是在Host侧执行还是在Device侧执行，以及能被调用的空间范围。”，可直接用于核对dim3 类型可见性、SIMT 公共头、__vector__ 入口与混合 VF 启动边界。
- [SIMT helper 误标 __simt_vf__ 导致编译失败](simt_vf_helpers_use_simt_callee.md)（`related`）：《dim3 未声明：显式引入 SIMT 公共头》处理“混合 SIMD/SIMT 核函数调用 asc_vf_call 时，显式包含 common_functions.h 以暴露 dim3 别名和正确重载。”。《SIMT helper 误标 __simt_vf__ 导致编译失败》明确“SIMT VF 入口调用的辅助函数也标成 __simt_vf__ 时，CANN 编译器拒绝调用；辅助函数须改用 __simt_callee__。”，可直接用于核对dim3 类型可见性、SIMT 公共头、__vector__ 入口与混合 VF 启动边界。
- [SIMT 核类型推导失败 — 补 __vector__](direct_launch_kernel_requires_vector_qualifier.md)（`related`）：《dim3 未声明：显式引入 SIMT 公共头》处理“混合 SIMD/SIMT 核函数调用 asc_vf_call 时，显式包含 common_functions.h 以暴露 dim3 别名和正确重载。”。《SIMT 核类型推导失败 — 补 __vector__》明确“SIMT VF 启动 shell 只标 __aicore__ 时 ld.lld 无法推导模板核函数类型；补 __vector__ 后恢复链接。”，可直接用于核对dim3 类型可见性、SIMT 公共头、__vector__ 入口与混合 VF 启动边界。
- [torch_npu 只保留一族 ACL 头文件](torch_npu_uses_single_acl_header_family.md)（`related`）：该卡说明 asc_vf_call 的 launch config 还需 SIMT 专用声明，补充“只用一套根头”后仍需按设备接口显式包含的边界。
- [混合 SIMT 启动边界用 GM_ADDR 承接地址空间](mixed_simt_launch_boundary_uses_gm_addr.md)（`related`）：《dim3 未声明：显式引入 SIMT 公共头》处理“混合 SIMD/SIMT 核函数调用 asc_vf_call 时，显式包含 common_functions.h 以暴露 dim3 别名和正确重载。”。《混合 SIMT 启动边界用 GM_ADDR 承接地址空间》明确“混合 SIMT 的 host launch 实参先以 GM_ADDR 穿过 __global__ wrapper，再在 device 侧恢复具体 __gm__ 指针，避免地址空间类型转换失败。”，可直接用于核对dim3 类型可见性、SIMT 公共头、__vector__ 入口与混合 VF 启动边界。
- [空 Ascend C kernel 骨架需显式标注 Vector 执行类型](empty_kernel_requires_explicit_vector_type.md)（`related`）：《dim3 未声明：显式引入 SIMT 公共头》处理“混合 SIMD/SIMT 核函数调用 asc_vf_call 时，显式包含 common_functions.h 以暴露 dim3 别名和正确重载。”。《空 Ascend C kernel 骨架需显式标注 Vector 执行类型》明确“纯占位 kernel 没有设备指令可供 Bisheng 自动推导任务类型时，显式添加 __vector__ 可关闭链接期 auto derivate failed。”，可直接用于核对dim3 类型可见性、SIMT 公共头、__vector__ 入口与混合 VF 启动边界。
- [纯 SIMT kernel 形参 __gm__ 导致编译失败](pure_simt_parameters_do_not_use_gm_qualifier.md)（`related`）：《dim3 未声明：显式引入 SIMT 公共头》处理“混合 SIMD/SIMT 核函数调用 asc_vf_call 时，显式包含 common_functions.h 以暴露 dim3 别名和正确重载。”。《纯 SIMT kernel 形参 __gm__ 导致编译失败》明确“CANN 9.0.1 的纯 SIMT 编译模式会把 __gm__ 展开为 device attribute；kernel 形参应使用普通类型化指针。”，可直接用于核对dim3 类型可见性、SIMT 公共头、__vector__ 入口与混合 VF 启动边界。
- [编程示例（SIMD与SIMT混合编程）](../../guides/programming_guide/advanced_programming/advanced_ai_core_programming_model/simd_simt_hybrid_programming/programming_examples.md)（`related`）：《dim3 未声明：显式引入 SIMT 公共头》处理“混合 SIMD/SIMT 核函数调用 asc_vf_call 时，显式包含 common_functions.h 以暴露 dim3 别名和正确重载。”。《编程示例（SIMD与SIMT混合编程）》明确“本节以gather & adds混合编程样例为例，展示SIMD与SIMT混合编程的关键语法。”，可直接用于核对dim3 类型可见性、SIMT 公共头、__vector__ 入口与混合 VF 启动边界。
<!-- cannbot:related:end -->
