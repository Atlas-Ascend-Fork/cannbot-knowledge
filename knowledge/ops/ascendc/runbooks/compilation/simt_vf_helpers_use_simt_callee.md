---
type: "Runbook"
title: "SIMT helper 误标 __simt_vf__ 导致编译失败"
description: "SIMT VF 入口调用的辅助函数也标成 __simt_vf__ 时，CANN 编译器拒绝调用；辅助函数须改用 __simt_callee__。"
tags: ["task.debugging", "topic.programming_model.execution_model.simt", "topic.implementation.api_layer.simt_api"]
status: stable
sources: []
created_at: "2026-08-14T03:13:06Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# SIMT helper 误标 __simt_vf__ 导致编译失败

## 现象

在 Ascend950 的 direct-launch Ascend C 工程中实现 `.asc` 核函数时，顶层 `__simt_vf__` 扫描入口需要调用一个用于 dtype 分支判断的函数模板。代码完整写入后，通过 CANN 9.0.1 的 CMake/make 构建入口编译，四种 dtype 的模板实例都在调用处失败，核心报错为：

```text
error: no matching function for call to 'is_nan_t'
note: candidate function not viable: simt_vf function can only call simt_callee function
9 errors generated.
```

当时代码并非缺少模板实参或函数声明；辅助函数与启动入口一样标成了 `__simt_vf__`。

## 适用场景

- 工程形态：Ascend C direct-launch 单文件 `.asc` 工程，CMake 编译并由 Host 侧启动 Kernel。
- API 路径：`asc_vf_call` 启动 `__simt_vf__` 入口，入口内部再调用设备辅助函数。
- 验证过的平台与版本：Ascend950PR_957b（平台注册值 `950`），CANN 9.0.1。
- 适用粒度：`platform_wide`；约束来自 SIMT VF 的设备调用约定，不依赖具体算子语义。
- 路线优先级：`recommended_fastpath`；被 `asc_vf_call` 启动的函数保留 `__simt_vf__`，被它调用的辅助函数标成 `__simt_callee__`。
- 不适用场景：Host 普通函数、`__aicore__` Kernel 壳函数，以及没有发生函数调用的内联表达式；其他 CANN 版本未验证。

## 根因

CANN SIMT 编译器把 `__simt_vf__` 识别为 VF 启动入口，而 VF 调用图中的普通设备辅助函数必须声明为 `__simt_callee__`，因此把被调用的 helper 也标成 `__simt_vf__` 会形成非法调用边。

## 解决配方

保留被 `asc_vf_call` 直接启动的顶层函数为 `__simt_vf__`，只把它调用的辅助函数改为 `__simt_callee__`；不要改函数模板参数、返回值或业务函数体。

### before

revision：轨迹内完整 `file_write` 源码快照（失败构建前）
path：`operators/<op>/<op>.asc`
symbol：`is_nan_t<T>`
line span：48–67
支撑结论：被调用 helper 使用 `__simt_vf__` 时触发 SIMT 调用约定编译错误。

```cpp
template <typename T>
__simt_vf__ inline bool is_nan_t(T x)
{
    if constexpr (std::is_same_v<T, int32_t>) {
        return false; // int32 has no NaN
    } else if constexpr (std::is_same_v<T, half>) {
        uint16_t bits;
        __builtin_memcpy(&bits, &x, sizeof(T));
        return ((bits & 0x7C00u) == 0x7C00u) && ((bits & 0x03FFu) != 0u);
    } else if constexpr (std::is_same_v<T, bfloat16_t>) {
        uint16_t bits;
        __builtin_memcpy(&bits, &x, sizeof(T));
        return ((bits & 0x7F80u) == 0x7F80u) && ((bits & 0x007Fu) != 0u);
    } else { // float (fp32)
        uint32_t bits;
        __builtin_memcpy(&bits, &x, sizeof(T));
        return ((bits & 0x7F800000u) == 0x7F800000u) && ((bits & 0x007FFFFFu) != 0u);
    }
}
```

### after

revision：轨迹内 `edit` 后源码快照（成功重建前）
path：`operators/<op>/<op>.asc`
symbol：`is_nan_t<T>`
line span：48–67
支撑结论：仅把 helper 属性改为 `__simt_callee__` 即恢复合法调用，函数体保持原样。

```cpp
template <typename T>
__simt_callee__ inline bool is_nan_t(T x)
{
    if constexpr (std::is_same_v<T, int32_t>) {
        return false; // int32 has no NaN
    } else if constexpr (std::is_same_v<T, half>) {
        uint16_t bits;
        __builtin_memcpy(&bits, &x, sizeof(T));
        return ((bits & 0x7C00u) == 0x7C00u) && ((bits & 0x03FFu) != 0u);
    } else if constexpr (std::is_same_v<T, bfloat16_t>) {
        uint16_t bits;
        __builtin_memcpy(&bits, &x, sizeof(T));
        return ((bits & 0x7F80u) == 0x7F80u) && ((bits & 0x007Fu) != 0u);
    } else { // float (fp32)
        uint32_t bits;
        __builtin_memcpy(&bits, &x, sizeof(T));
        return ((bits & 0x7F800000u) == 0x7F800000u) && ((bits & 0x007FFFFFu) != 0u);
    }
}
```

## 设计决策

选择把 `__simt_vf__` 限定为由 `asc_vf_call` 启动的入口，把复用逻辑声明为 `__simt_callee__`，因为这与编译器明确给出的调用约定一致，且不复制 helper 业务逻辑。轨迹没有尝试把函数体复制进每个调用点，也没有通过删掉 helper 调用规避问题。当前方案属于 `recommended_fastpath`。

## 系统信息

- Toolchain：CANN 9.0.1 的 ASC 编译链。
- 目标：Ascend950PR_957b / dav-3510。
- 工程入口：CMake/make 构建单个 `.asc` 翻译单元。
- 相关文件：`operators/<op>/<op>.asc`。

## 预防

- 代码审查时区分“由 `asc_vf_call` 启动的 VF 入口”和“入口调用的设备 helper”，不要仅因两者都在 SIMT 侧执行就使用相同属性。
- 搜索每个 `__simt_vf__` 函数体里的自定义函数调用，逐个确认被调用符号带 `__simt_callee__`。
- 在增加 dtype 模板实例后立即编译全部分支；该错误会在每个实例化点重复出现，首条 `simt_callee` note 已足够定位根因。

## 验证信号

本知识来自一次 Ascend950 direct-launch Kernel 开发中的真实编译失败与单行属性修复；修复后继续完成动态库链接、真机 pytest 和干净重建复验。

- 修复前构建输出包含 `simt_vf function can only call simt_callee function`、`9 errors generated`，目标未生成（来源平台：950；证据等级：tool_observed）。
- 修复后构建输出为 `Linking ASC shared library` 与 `Built target`（来源平台：950；证据等级：tool_observed）。
- 修复后的真机测试集 42/42 通过，随后干净重建后的同一测试集再次 42/42 通过（来源平台：950；证据等级：tool_observed）。

## 失效边界

- 结论只覆盖 CANN 9.0.1 的 SIMT VF 调用约定；后续编译器版本是否放宽或改名未验证。
- A2、A3 未验证，不能从本次 Ascend950 结果直接推断其可用属性组合。
- 本配方只修复调用约定，不证明 helper 函数体的数值语义正确；数值正确性仍须独立测试。

## 坏实践

把所有 SIMT 侧函数统一标成 `__simt_vf__` 会混淆“启动入口”和“可调用设备函数”；即使符号可见、模板实例化正常，编译器仍会拒绝 VF 到 VF 的普通函数调用。

## 误诊

错误在多个 dtype 实例化点重复出现，容易被误判为模板重载或 NaN 位模式实现问题；编译器 note 已明确指出候选不可调用的原因是函数属性，不应先改模板参数或函数体。

<!-- cannbot:related:start -->
## 相关

- [函数执行空间限定符](../../apis/simt_api/simd_simt_hybrid_programming_intro/extended_syntax/function_execution_space_qualifier.md)（`exemplifies`）：限定符文档明确 __simt_vf__ 是启动入口、__simt_callee__ 是可被调用 helper，为编译错误提供规范依据。
- [CANN 9.0.1 SIMT 入口类型无法派生—改混合 VF](mixed_simt_requires_vector_shell_and_simt_vf.md)（`related`）：合法 helper 属性之外，混合工程还需由 Vector shell 启动 __simt_vf__，二者共同形成完整调用层级。
- [SIMD&SIMT BuiltIn关键字](../../guides/programming_guide/language_extension/simd_simt_hybrid_builtin_keywords.md)（`related`）：SIMD&SIMT BuiltIn关键字 与《SIMT helper 误标 __simt_vf__ 导致编译失败》的实质衔接是：混合 BuiltIn 关键字需结合执行/地址限定、kernel/VF、内置变量和混合编程故障使用。
- [SIMT API 未进入 AscendC 命名空间导致编译失败](simt_api_is_in_ascendc_simt_namespace.md)（`related`）：helper 改为 __simt_callee__ 解决调用属性，API 仍需从 AscendC::Simt 命名空间解析，二者是独立编译条件。
- [SIMT VF 栈数组动态索引致输出全零](../precision/simt_vf.md)（`related`）：SIMT VF 栈数组动态索引致输出全零：本卡暴露 __simt_vf__ 内局部数组动态索引的编译器语义缺口；官方执行空间限定符界定 VF/callee契约，helper限定符和Block元数据卡给出同一执行域内已验证的代码生成禁区。 目标卡《SIMT helper 误标 __simt_vf__ 导致编译失败》补充：SIMT VF 入口调用的辅助函数也标成 __simt_vf__ 时，CANN 编译器拒绝调用；辅助函数须改用 __simt_callee__。
- [SIMT 内读块号致 Bisheng 崩溃—移到核入口](simt_move_block_metadata_to_vector_shell.md)（`related`）：SIMT 内读块号致 Bisheng 崩溃—移到核入口 与《SIMT helper 误标 __simt_vf__ 导致编译失败》的实质衔接是：块级 GetBlockIdx/GetBlockNum 必须在 __aicore__ caller 读取并把标量区间传给 __simt_vf__；C/C++ 查询卡给出正确入口，SIMT helper/纯 SIMT 参数与混合入口卡共同限定 caller/callee 作用域。
- [dim3 未声明：显式引入 SIMT 公共头](asc_vf_call_launch_config_requires_simt_header.md)（`related`）：《dim3 未声明：显式引入 SIMT 公共头》处理“混合 SIMD/SIMT 核函数调用 asc_vf_call 时，显式包含 common_functions.h 以暴露 dim3 别名和正确重载。”。《SIMT helper 误标 __simt_vf__ 导致编译失败》明确“SIMT VF 入口调用的辅助函数也标成 __simt_vf__ 时，CANN 编译器拒绝调用；辅助函数须改用 __simt_callee__。”，可直接用于核对dim3 类型可见性、SIMT 公共头、__vector__ 入口与混合 VF 启动边界。
- [带主元 Thomas 求解器 SIMT 直访 GM kernel](gtsv2_partial_pivoting_thomas_simt_direct_gm_kernel.md)（`related`）：Gtsv2 实现把 Gtsv2ProcessOneRhs/Gtsv2Fabsf 标为 __simt_callee__ 并由 __simt_vf__ 入口调用；该实测卡验证这正是编译器要求的调用约定。
- [核函数与VF函数（SIMD与SIMT混合编程）](../../guides/programming_guide/advanced_programming/advanced_ai_core_programming_model/simd_simt_hybrid_programming/kernel_and_vf_functions.md)（`related`）：焦点处理混合 SIMD/SIMT 中 kernel、VF、callee 的限定符和启动边界；SIMT helper 误标 __simt_vf__ 导致编译失败正文说明“SIMT VF 入口调用的辅助函数也标成 __simt_vf__ 时，CANN 编译器拒绝调用；辅助函数须改用 __simt_callee__”。候选明确 kernel/VF/callee 的允许调用方向、地址空间和 launch API，或给出同机制编译失败。
- [核函数调用未标__aicore__的纯算术辅助函数](aicore_helper_requires_device_qualifier.md)（`related`）：普通 __aicore__ Kernel helper 也需要设备限定符，和 SIMT callee 规则共同说明 helper 必须匹配调用空间。
- [simd_vf 互调导致 helper 编译失败](simd_vf_helpers_use_simd_callee.md)（`same_topic`）：simd_vf 互调导致 helper 编译失败 与《SIMT helper 误标 __simt_vf__ 导致编译失败》的实质衔接是：顶层 __simd_vf__ 只能调用 __simd_callee__ helper；asc_vf_call、执行限定符、kernel/VF 指南和相邻 VF 编译故障共同固定三层调用结构。
<!-- cannbot:related:end -->
