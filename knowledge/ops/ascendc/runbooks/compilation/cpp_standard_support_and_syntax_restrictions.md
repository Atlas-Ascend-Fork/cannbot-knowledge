---
type: "Runbook"
title: "Ascend C Device 侧 C++ 标准级别与语法限制判定"
description: "核对 Ascend C Host/Device 编译标准：Device 默认 C++17，可选 C++11/14/20；区分纯 SIMT 与 SIMD/SIMT 混合编程的运行时递归边界，并检查核函数 POD 入参、SIMT VF 地址空间与结构体限制。附编译选项、诊断步骤和静默栈地址错误的验证边界。"
tags:
- "task.implementation"
- "task.migration"
- "topic.compilation"
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/technical_appendix/cpp_standard_support/overview.md
  role: primary
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/technical_appendix/cpp_standard_support/cpp_language_restrictions/general_restrictions.md
  role: primary
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/technical_appendix/cpp_standard_support/cpp_language_feature/lambda_expressions.md
  role: supporting
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/compilation_and_execution/operator_compilation/ai_core_operator_compilation.md
  role: constraint
created_at: '2026-10-23T02:00:00Z'
updated_at: '2026-10-23T08:55:34Z'
platforms:
- agnostic
---

# Ascend C Device 侧 C++ 标准级别与语法限制判定

## 适用场景

出现下列任一情形时，先用本卡定性，再动代码：

- 把 Host 侧或普通 C++ 代码搬进 kernel，用到虚函数、STL 容器、`tuple`、动态申请内存、`typeid`、文件 IO；
- 编译报错涉及参数地址空间或结构体参数，或者 VF 内携带 MainScalar 栈地址却未报错；
- 设计核函数（Kernel）入参列表、`__simt_vf__` 函数签名，或写 SIMD 与 SIMT 混合编程的结构体定义；
- 想确认实际 C++ 标准，以及为什么切换到 C++11/14/20 后语法或 API 无法使用。

## 支持级别：先分清 Host 侧与 Device 侧

- **Host 侧**：与 clang15 一致，支持完整的 C/C++ 标准。
- **Device 侧**：固定来源文档的默认标准是 **C++17**，可指定 **C++11、C++14、C++20**；bisheng 命令行用 `-std=c++<version>` 或 `--std=c++<version>`，CMake 用 `CMAKE_ASC_STANDARD`（默认 17，设置低于 17 会告警）。无论使用哪种构建方式，都应核对实际编译命令；指定低于 C++17 的标准时，部分 API 内部实现可能不可用，部分高版本语法仍可能以 clang 扩展告警通过，需要严格约束时使用 `-Werror`。
- 两条轴必须分开判：**标准级别与编译诊断**用于核对语法，**Device 运行时能力与编程模式**用于核对特性是否可用。标准级别够（例如按 C++17 编译）不代表该特性在 Device 侧可用。
- 平台口径：本卡来源全部按 C++ 标准级别与编译器行为给结论，正文未把结论绑定到任何芯片型号，因此本卡标 `agnostic`；若问题实际来自某个芯片/架构的后端能力缺口，本卡不适用（见文末"相邻卡分工"）。
- Host 侧的"完整标准"是编译能力口径，不等于每条构建链都开到了最新标准：具体编译单元以什么语言标准编译，要按构建配置核对（op_host 侧已有"链上标准低于宿主机 g++"的实例，见文末相邻卡）。

## Device 侧不可用/被限制的语言特性

| 类别 | 限制（Device 侧） |
|---|---|
| 类与继承 | 不支持虚函数；不支持虚继承 |
| 控制流 | 运行时递归仅纯 SIMT 编程场景可用；SIMD 与 SIMT 混合编程等其他场景不支持 |
| 动态内存 | 不支持动态 `malloc`、`free`、`new`、`delete` |
| 标准库 | 不支持 STL；不支持标准库下的 `tuple` 及算法类运算（相关库函数调用需要标记 `aicore`） |
| RTTI | 不支持运行时 `typeid` |
| IO | 不支持文件系统 IO |
| Lambda | 纯 SIMT 的核函数局部 lambda 无需附加函数属性；混合编程场景按定义位置标记 `__aicore__`、`__simd_callee__`、`__simt_callee__` 或 `__callee__` |

混合编程场景的 SIMT VF 内 lambda 属性标注形态（属性写在参数列表之后；纯 SIMT 核函数局部 lambda 无需此标记）：

```cpp
auto affine = [scale, bias](float v) __simt_callee__ { return v * scale + bias; };
```

诊断用法：虚函数/虚继承、动态申请、STL、运行时 `typeid` 或文件系统 IO 命中禁用项；运行时递归先区分纯 SIMT 与混合编程，再对照目标编译命令验证。编译期 `constexpr` 递归与运行时递归也须分开判。

## 核函数（Kernel）参数列表限制

核函数参数列表**仅支持**以下三类：

1. 基础数据类型，如 `int32_t`、`float`；
2. 基础数据类型组成的结构体：支持嵌套结构体形式，但必须是 **POD**（Plain Old Data）；
3. 基础数据类型的指针，如 `int32_t*`、`float*`——这些指针实际指向 Global Memory。

判定：核函数入参须落在上述三类；非 POD 类对象、引用、多态类型不能仅凭名字归入“POD 结构体”。POD 约束取决于类型性质而非使用 `struct` 还是 `class` 关键字，不能把所有自定义类对象一概排除；仍须核对实际定义并以目标编译结果验证。

## SIMT VF 函数（`__simt_vf__`）限制

- 标量按值传入；引用形参不支持，指针形参必须指向 GM 或 UB 并带地址空间限定符，不能用普通标量指针形参。
- 不允许把栈数组作为参数传入；指针形参必须显式使用 `__gm__` 或 `__ubuf__` 地址空间限定符。违反时编译期报错，来源给出的报错文本为 `error: cannot initialize a parameter of type '__gm__ int *' with an lvalue of type 'int[5]'`。规避写法：把数据放到 Global Memory 或 UB，用带限定符的指针传参。
- VF 内不得访问 MainScalar 栈空间：即使把栈地址通过 UB 中的整数/多级指针间接传入并编译通过，VF 内解引用仍是运行时未定义行为，可能静默读写错误内存。
- 不允许使用结构体作为参数。
- `__simt_vf__` 入口本身不能通过函数指针调用，须以编译期确定的模板实参经 `asc_vf_call()` 调用；VF 内 `__simt_callee__` 辅助函数可通过带 `__simt_callee__` 标记的函数指针间接调用，普通函数指针类型不匹配。
- 函数的 inline 行为由编译器决定：额外添加的 `always_inline` 或 `noinline` 会被忽略。

## SIMD 与 SIMT 混合编程的结构体限制

- 使用位于 Global Memory 或 Unified Buffer（UB）中的结构体/类**拷贝构造**新对象时，需要开发者手动实现拷贝构造函数，编译器不会隐式生成；两个地址空间要分别重载，例如 `__callee__ TestS(const __gm__ TestS& other)` 与 `__callee__ TestS(const __ubuf__ TestS& other)`，调用点按数据所在空间选中对应重载。
- 异构编译场景中 Host 与 Device 可共用结构体定义，但 Host 侧无法识别 `__callee__`、`__gm__` 等 Device 侧关键字，因而无法据此实现函数重载。需要定义多个地址空间重载函数时，用编译预定义宏 `__NPU_ARCH__` 把相关 Device 代码隔离，避免函数定义冲突。
- 不支持直接向 Global Memory 或 UB 地址空间写入结构体；来源对该形态仅标注"不支持，编译报错"，未给出报错文本。

## 判定步骤（按序执行）

1. **分侧**：先确认代码属于 Device 侧（kernel）还是 Host 侧（tiling/框架）。Host 侧按完整 C/C++ 标准处理；Device 侧继续往下。
2. **过特性清单**：比对禁用项；运行时递归核对编程模式，lambda 核对定义位置与函数属性，不将条件限制误判为通用禁用。
3. **查核函数入参**：把参数列表逐项归入"基础类型 / POD 结构体 / 基础类型指针"三类，任一项落不进就调整入参形态（例如把类成员拆成 POD 字段、把引用改成值或指针）。
4. **查 `__simt_vf__`**：标量按值、无引用或栈数组实参、指针带 `__gm__`/`__ubuf__`、无结构体参数；入口经 `asc_vf_call()` 调用，辅助 callee 函数指针须带匹配标记。追溯间接传入的地址是否指向 MainScalar 栈，不能用编译通过排除这类运行时错误；`always_inline`/`noinline` 不控制内联。
5. **查混合编程结构体**：拷贝构造是否手写、是否按地址空间重载、Device 代码是否用 `__NPU_ARCH__` 隔离、是否存在"向 GM/UB 写结构体"的语句。
6. **编译与运行验证**：检查实际标准与目标编程模式下的编译诊断；编译成功只证明部分语法检查通过，不能排除 VF 读写 MainScalar 栈地址的静默未定义行为，需排查地址来源并用目标环境验证数据。

## 验证方式

- 核对 bisheng `-std` / `--std` 或 CMake `CMAKE_ASC_STANDARD` 与实际编译命令；需要严格拒绝高版本语法扩展时加 `-Werror`，低于 C++17 还要检查所用 API 是否依赖 C++17。
- 对文档声明会编译报错的禁用项检查编译诊断；对 MainScalar 栈地址经 UB 带入 VF 的情况直接检查地址来源及数据结果，不能以无编译错误为通过证据。此处没有执行硬件或编译实验。
- 混合编程结构体：检查 Global Memory 与 UB 两个地址空间的拷贝构造函数是否都已实现——来源示例中两条读路径分别调用不同的重载，两条路径都要覆盖。

## 失效边界

- **清单之外不等于可用**：来源给的是禁用项与受限项，没有"允许清单"；未被禁止的特性仍以实际编译结果为准，本卡不做"一定可用"的背书。
- **报错文本覆盖不全**：来源对多种限制给出不同诊断示例；不要将任何一条错误串视为所有编译模式的固定文本，静默未定义行为尤其不能靠报错判断。
- **不覆盖全部构建链**：来源给出 bisheng `-std` / `--std` 与 AI Core CMake 的 `CMAKE_ASC_STANDARD`；其他工程须核对实际传给编译器的选项。
- **不覆盖具体后端缺口**：来源按标准级别与编译器行为给结论，不针对某一芯片/架构；具体芯片上的后端能力缺口属于另一类问题。

## 相邻卡分工

- [bf16_scalar_to_fp32_bit_extension](./bf16_scalar_to_fp32_bit_extension.md)：具体后端缺口的实测实例（bf16 标量强转、标量有序比较报错与位级规避）。本卡给语言/标准级的限制清单，该卡给"某条限制在特定后端上的具体形态"。
- [pipebarrier_pipe_s_is_not_supported](./pipebarrier_pipe_s_is_not_supported.md)：模板参数取值域导致的编译失败实例。本卡管语言特性与函数签名，该卡管"某模板参数不在目标编译器允许范围"。
- [casttrait_nttp_uses_reference_in_cxx17](./casttrait_nttp_uses_reference_in_cxx17.md)：同一写法在不同标准级别下的可用性差异（按值 NTTP 需 C++20，C++17 需改用 const 引用 NTTP），是"标准级别决定语法能否被接受"的落地证据。
- [op_host_fwk_modules_rejects_cxx20](./op_host_fwk_modules_rejects_cxx20.md)：Host 侧某个具体构建链以低于宿主机 g++ 的标准编译（`auto` lambda 形参、结构化绑定失败），用于核对"该编译单元实际用的语言标准"。
- [device_cpp_and_scalar_vector_interfaces](../../guides/environments/device_cpp_and_scalar_vector_interfaces.md)：设备 C++ 子集与函数可调用性的边界（按编译目标、函数标注、头文件与数值合同判断某个 std 风格/设备函数能否调用）。本卡给"官方禁用清单 + 判定步骤"，该卡给"未被本卡禁止时如何逐个核对实现与类型约束"。
- [duplicate_dtype_support_arch22_arch35](./duplicate_dtype_support_arch22_arch35.md)：按架构分档的 API/指令支持差异，不属于 C++ 标准限制范畴。
- [deprecated_interface_detection_and_replacement](./deprecated_interface_detection_and_replacement.md)：接口废弃与替换流程（编译期告警/文档清单驱动），与本卡的语言级限制互补。
