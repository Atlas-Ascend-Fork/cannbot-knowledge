---
type: "Runbook"
title: "GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型"
description: "GET_TILING_DATA_WITH_STRUCT 宏内部对 tiling_struct 做 # 字符串化拼进 section 名，传入带 <> 的模板类型（如 MaskedFillTilingData<RANK>）会触发 C++ 解析错；用 if constexpr 或 trait 绕开 <> 又会破坏节级 tiling 注册，报 do not registe tiling struct。"
tags: ["task.debugging", "topic.implementation.tiling"]
status: stable
sources: []
created_at: "2026-08-18T05:30:41Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
aliases: ["section_name", "stringification", "template_type", "if_constexpr", "trait_alias", "do_not_registe_tiling_struct"]
---

# GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型

## 现象

为修复 tiling 容量不匹配，把 kernel stub 的 `GET_TILING_DATA_WITH_STRUCT` 从小 `MaskFillTilingData` 改成真实 `MaskedFillTilingData<RANK>`（host 侧下发的结构体）。构建 Ascend950 kernel 时报 C++ 解析错，出错行即 `GET_TILING_DATA_WITH_STRUCT(MaskedFillTilingData<RANK>, tilingData, tiling);`。后续用 `if constexpr` 分支或 trait（`typename MaskFillTilingDataTrait<RANK>::Type`）绕开 `<>`，C++ 解析过了，但转报 `MaskFill do not registe tiling struct!!!`，节级 tiling 注册丢失、`.o` 产物缺失。

## 适用场景

- 工程形态：Kernel 直调（ops-registry-invoke-glacier），`op_kernel/mask_fill_apt.cpp` 入口的 tiling 结构体注册。
- API 路径：`GET_TILING_DATA_WITH_STRUCT` / `REGISTER_TILINGDATA_SIZE`（宏内部 `#` 字符串化 tiling_struct 拼 section 名）；`asc_opc` / opbuild 节级 tiling 注册扫描 `.ascendc_tiling` section。
- 验证过的平台与 CANN 版本：Ascend950，CANN 9.1.0。
- 适用粒度：`operator_family`——任何 kernel 侧 tiling 结构体是 C++ 模板类型（带 `<>`）的 AscendC 算子。
- 路线优先级：`recommended_fastpath`——file-scope 非 template `using` 别名 + `template<>` 显式特化是首选正解（每个 RANK 的注册在各自函数体里独立展开，`__COUNTER__` 符号在翻译单元内全局唯一可见）。
- 不适用或未验证场景：tiling 结构体是非模板普通类（无 `<>`）时宏可直传，本坑不触发；a2 / a3 未在本 trace 上板验证（推断可迁移，宏与节级注册机制是 kernel 侧通用，与 NPU arch 无关），标注「未验证，推断可迁移」。

## 判别方法

触发：构建含 `GET_TILING_DATA_WITH_STRUCT(<模板类型>, ...)` 调用的 AscendC kernel（目标 950，CANN 9.1.0），构建日志含 `error: expected '(' for function-style cast or type construction` 且出错列指向宏调用的 tiling_struct 参数位；或开发者把宏调用包进 `if constexpr` 分支 / 改用 trait `typename Trait<RANK>::Type` 后，构建日志转为 `[ERROR] TBE ... do not registe tiling struct!!!` 且对应 kernel 的 `.o` 产物缺失。

探针：重新执行 `cd operators && ./build.sh mask_fill_package`；构建后用 `grep -E "error: expected|do not registe tiling struct" /tmp/mask_fill_build*.log` 定位错误模式，并用 `find <opp/vendors/MaskFill/.../kernel/ascend950/mask_fill_apt/> -name "*.o" | wc -l` 检查节级 tiling 注册是否落到产物（直传模板类型阶段：解析错；`if constexpr` / trait 阶段：解析过但 `.o` 数减少 / 缺失）。本 trace 的确切构建命令行可由 `operators/build.sh mask_fill_package` 与 set_env.sh 复原，构建日志逐字取自 `/tmp/mask_fill_build2.log` / `/tmp/mask_fill_build4.log`。

原始观测（构建日志，逐字取自本 trace 构建结果）：

直传模板类型阶段（apt.cpp:43 = `GET_TILING_DATA_WITH_STRUCT(MaskedFillTilingData<RANK>, tilingData, tiling);`）：

```
operators/mask_fill_package/op_kernel/mask_fill_apt.cpp:43:59: error: expected '(' for function-style cast or type construction
mask_fill_apt.cpp:43:61: error: use of undeclared identifier 'tilingData'
```

`if constexpr` / trait 包裹阶段（C++ 解析已过，节级 tiling 注册丢失），构建工具输出（逐字）：

```
[ERROR] TBE(3358753,python3):2026-08-06-14:30:20.018.635 [log_utils.py:183][plog_print] [ascend950]  MaskFill do not registe tiling struct!!!
[2026-08-06 14:30:20] [ERROR] [ascend950] MaskFill do not registe tiling struct!!!
```

同一构建 `=== errors? ===` 计 108 条 error，子 kernel `.o` 产物缺失。

解释：`GET_TILING_DATA_WITH_STRUCT` 宏内部对 `tiling_struct` 参数做 `#` 字符串化，拼进一个 section 名（与 `REGISTER_TILINGDATA_SIZE` 的 `__COUNTER__` 配套做节级 tiling 注册）。当传入 `MaskedFillTilingData<RANK>`（带 `<>`），`#` 字符串化后 `<` `>` 破坏 C++ 解析器对 section 名 / 类型构造的识别 → `expected '(' for function-style cast`。进一步用 `if constexpr (RANK==4) { using TilingDataT = ...; GET_TILING_DATA_WITH_STRUCT(TilingDataT, ...); }` 绕开 `<>`：`if constexpr` 只在编译期选中分支展开，未被选中分支的 `REGISTER_TILINGDATA_SIZE`（`static constexpr ... __attribute__((used, section(...)))` 用 `__COUNTER__` 生成唯一符号）不被发射进 `.ascendc_tiling` section，节级 tiling 注册扫描器找不到该 tiling struct → `do not registe tiling struct`。trait 方式（`typename MaskFillTilingDataTrait<RANK>::Type`）同理：仍是依赖模板的类型，节级注册宏在模板实例化前看不到具体类型。机制链不跳步：宏 `#` 字符串化 tiling_struct 拼 section 名 → `<>` 破坏 C++ 解析 → 直传模板类型报 parse error → `if constexpr` / trait 包裹虽绕开 `<>` 但破坏节级 tiling 注册（`__COUNTER__` 符号在分支 / 依赖类型后丢失或不可见）→ `do not registe tiling struct`。修复方向（非本卡闭环内容）：file-scope 非 template `using` 别名 + `template<>` 显式特化，既无 `<>` 又让每个 RANK 的注册在各自函数体里独立展开，节级注册不丢。

## 验证信号

本卡验证信号来自本 trace 的 kernel 构建工具输出（mask_fill 算子，950 / CANN 9.1.0，ops-registry-invoke-glacier）：

- `mask_fill_apt.cpp:43:59: error: expected '(' for function-style cast or type construction` 与 `:43:61: error: use of undeclared identifier 'tilingData'`，出错行即 `GET_TILING_DATA_WITH_STRUCT(MaskedFillTilingData<RANK>, ...)`（来源平台：950；证据等级: tool_observed）。
- `if constexpr` / trait 包裹后构建输出 `[ERROR] TBE [ascend950] MaskFill do not registe tiling struct!!!`，同一构建 108 条 error、子 kernel `.o` 产物缺失（来源平台：950；证据等级: tool_observed）。
- 上述错误模式可在 `/tmp/mask_fill_build*.log` 与 `find ... -name "*.o" | wc -l` 探针上重现，作为该坑的判别信号（来源平台：950；证据等级: tool_observed）。

> 说明：验证信号段来源 = 本 trace 的构建 bash 输出与构建日志 grep 结果（事件 seq 978 / 989 / 998，raw_record 54257 / 55286）；本 trace 中 file-scope 别名 + 显式特化的修复 edit 内容被 markdown 转写替换为占位符（"_see below_"），agent 叙述的“修后 build exit 0”未由保留的 tool_result 直接佐证，故本卡不声称修复后实测通过，只作为“识别该编译错误 + 注册丢失模式 + 修复方向”的诊断卡。

## 预防

- 用 `GET_TILING_DATA_WITH_STRUCT` 注册 tiling 结构体时，结构体名必须是无 `<>` 的普通标识符：模板类型先 `using` 成非 template 别名再传入。
- 多 RANK 场景用 `template<>` 显式特化而非 `if constexpr` 分支——节级 tiling 注册宏依赖 `__COUNTER__` 全局唯一符号，分支包裹会丢注册。
- 不要用 trait（`typename Trait<RANK>::Type`）传给宏——依赖模板的类型在节级注册宏展开时仍不可解析。

## 坏实践

- 见 `GET_TILING_DATA_WITH_STRUCT(SomeClass<T>, ...)` 直传模板类型 → 基本可判定为触发本坑的 `<>` 字符串化解析错。
- 见用 `if constexpr` 包裹 `GET_TILING_DATA_WITH_STRUCT` 来绕 `<>` → 节级注册会丢，构建产物 `.o` 缺失，不要当成 `__COUNTER__` 符号冲突去查。

## 失效边界

- Ascend950 实测观测；a2 / a3 平台未在本 trace 上板验证，推断可迁移（宏与节级注册机制是 AscendC kernel 侧通用，与 NPU arch 无关），标注「未验证，推断可迁移」。
- 本卡只覆盖「宏不接受 `<>` + 分支 / trait 破坏节级注册」这一根因；tiling 容量数值不匹配、value memcpy segfault 等同算子其它坑不在本卡范围。

## 误诊

- 中间尝试 `if constexpr` / trait 时一度以为是 `REGISTER_TILINGDATA_SIZE` 的 `__COUNTER__` 符号冲突，但根因是宏对 `tiling_struct` 的 `#` 字符串化与节级注册对「具体类型可见性」的要求——非 template 别名 + 显式特化同时满足两者。

<!-- cannbot:related:start -->
## 相关

- [COPY_TILING_WITH_STRUCT](../../apis/simd_api/basic_api/kernel_tiling/copy_tiling_with_struct.md)（`exemplifies`）：焦点处理COPY_TILING_WITH_STRUCT 宏与 Tiling 结构注册、取数的编译契约；GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型正文说明“GET_TILING_DATA_WITH_STRUCT 宏内部对 tiling_struct 做 # 字符串化拼进 section 名，传入带 <> 的模板类型（如 MaskedFillTilingData<RANK>）会触发 C++ 解析错；用 if constexpr 或 t”。候选对应宏展开所需的结构注册、TilingData 读取或已验证的编译失败边界。
- [GET_TILING_DATA](../../apis/simd_api/basic_api/kernel_tiling/get_tiling_data.md)（`exemplifies`）：GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型 与《GET_TILING_DATA》的实质衔接是：GET_TILING_DATA_WITH_STRUCT 会字符串化结构体名并注册 section，模板尖括号因此解析失败；相关宏、结构注册、显式 header/别名和多 struct 冲突卡共同限定可行修法。
- [GET_TILING_DATA_MEMBER](../../apis/simd_api/basic_api/kernel_tiling/get_tiling_data_member.md)（`exemplifies`）：GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型 与《GET_TILING_DATA_MEMBER》的实质衔接是：GET_TILING_DATA_WITH_STRUCT 会字符串化结构体名并注册 section，模板尖括号因此解析失败；相关宏、结构注册、显式 header/别名和多 struct 冲突卡共同限定可行修法。
- [GET_TILING_DATA_PTR_WITH_STRUCT](../../apis/simd_api/basic_api/kernel_tiling/get_tiling_data_ptr_with_struct.md)（`exemplifies`）：“GET_TILING_DATA_PTR_WITH_STRUCT”定义：在使用该宏时，开发者可以通过指定结构体名称来获取相应的Tiling信息，并将其填入对应的Tiling结构体中。完成填充后，该宏将返回一个指向该Tiling结构体的指针，并使用__tiling_data_ptr__修饰符对该指针进行修饰。这种修饰方式能够确保在动静态Shape场景下代码的统一性和兼容性。；“GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型”定义：GET_TILING_DATA_WITH_STRUCT 宏内部对 tiling_struct 做 # 字符串化拼进 section 名，传入带 <> 的模板类型（如 MaskedFillTilingData<RANK>）会触发 C++ 解析错；用 if constexpr 或 trait 绕开 <> 又会破坏节级 tiling 注册，报 do not registe tiling struct。。实质衔接：宏按结构名返回带 __tiling_data_ptr__ 的指针，可再拷到栈；但直调工程没有生成宏、模板类型又会破坏字符串化，两张 runbook 精确界定停止边界。
- [GET_TILING_DATA_WITH_STRUCT](../../apis/simd_api/basic_api/kernel_tiling/get_tiling_data_with_struct.md)（`exemplifies`）：GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型 与《GET_TILING_DATA_WITH_STRUCT》的实质衔接是：GET_TILING_DATA_WITH_STRUCT 会字符串化结构体名并注册 section，模板尖括号因此解析失败；相关宏、结构注册、显式 header/别名和多 struct 冲突卡共同限定可行修法。
- [REGISTER_TILING_DEFAULT](../../apis/simd_api/basic_api/kernel_tiling/register_tiling_default.md)（`exemplifies`）：GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型 与《REGISTER_TILING_DEFAULT》的实质衔接是：GET_TILING_DATA_WITH_STRUCT 会字符串化结构体名并注册 section，模板尖括号因此解析失败；相关宏、结构注册、显式 header/别名和多 struct 冲突卡共同限定可行修法。
- [RegisterNoneTiling](../../apis/simd_api/basic_api/kernel_tiling/register_none_tiling.md)（`exemplifies`）：RegisterNoneTiling：RegisterNoneTiling 与 GET_TILING_DATA 系列共同完成未注册 C++ struct 的 kernel 解码；两个 runbook分别覆盖该宏在生成器与 RESERVED workspace 场景的实际失败，直调限制卡界定不可用边界。 目标卡《GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型》补充：GET_TILING_DATA_WITH_STRUCT 宏内部对 tiling_struct 做 # 字符串化拼进 section 名，传入带 <> 的模板类型（如 MaskedFillTilingData<RANK>）会触发 C++ 解析错；用 if constexpr 或 trait 绕开 <> 又会破坏节级 tiling 注册，报 do not registe tiling struct。
- [TilingData结构注册](../../apis/utils_api/tiling_data_structure_register/tiling_data_struct_register.md)（`exemplifies`）：GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型 与《TilingData结构注册》的实质衔接是：GET_TILING_DATA_WITH_STRUCT 会字符串化结构体名并注册 section，模板尖括号因此解析失败；相关宏、结构注册、显式 header/别名和多 struct 冲突卡共同限定可行修法。
- [Tiling模板编程](../../apis/utils_api/tiling_template_programming/tiling_template_programming.md)（`exemplifies`）：Tiling模板编程 与《GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型》的实质衔接是：Tiling 模板编程依赖参数声明、选择宏和 key 获取；所选编译故障直接约束模板类型与分发实例化。
- [Stub tiling padding 不解 aclnn Segfault](stub_tiling_padding_aclnn_segfault.md)（`related`）：目标卡限定 GET_TILING_DATA_WITH_STRUCT 宏只能接收非模板类型名；本卡展示即使 stub 类型能注册并扩大容量，也不能把 host 侧设备指针 Segfault 归因给该宏。
- [直调不可用 GET_TILING_DATA_WITH_STRUCT 宏](direct_invoke_unavailable_get_tiling_data_with_struct.md)（`related`）：两卡共同限定 GET_TILING_DATA_WITH_STRUCT 的生成期契约：一张处理直调环境根本不可用，另一张处理注册算子环境中模板类型破坏宏字符串化与 section 注册。
- [编译与执行约束说明](../../guides/programming_guide/compilation_and_execution/operator_compilation/constraints.md)（`related`）：《编译与执行约束说明》处理“编译与执行约束说明，包含Kernel类型推导、数据类型与字符串字面量等限制。”。《GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型》明确提供“GET_TILING_DATA_WITH_STRUCT 宏内部对 tiling_struct 做 # 字符串化拼进 section 名，传入带 <> 的模板类型（如 MaskedFillTilingData<RANK>）会触发 C++ 解析错；用 if constexpr 或 trait 绕开 <> 又会破坏节级 tiling 注册，报 do not registe tiling struct。”，其参数、调用或验证步骤直接接入Ascend C 编译约束、AOT/交叉编译、模板宏和编译错误定位。
- [GET_TILING_DATA 首参传类型名致变量遮蔽类型](get_tiling_data.md)（`same_topic`）：GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型 与《GET_TILING_DATA 首参传类型名致变量遮蔽类型》的实质衔接是：GET_TILING_DATA_WITH_STRUCT 会字符串化结构体名并注册 section，模板尖括号因此解析失败；相关宏、结构注册、显式 header/别名和多 struct 冲突卡共同限定可行修法。
- [REGISTER_TILING_DEFAULT 取小档致 NaN](register_tiling_default_nan.md)（`same_topic`）：REGISTER_TILING_DEFAULT 取小档致 NaN 与《GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型》的实质衔接是：REGISTER_TILING_DEFAULT 决定 opParaSize，必须覆盖最大 TilingData struct；注册宏、GET 宏、host/kernel 结构、SetDataSize 与追加越界卡描述同一 buffer 尺寸链。
- [REGISTER_TILING_DEFAULT 多 struct 冲突](register_tiling_default_struct.md)（`same_topic`）：REGISTER_TILING_DEFAULT 多 struct 冲突 与《GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型》的实质衔接是：一个算子只能有一个 REGISTER_TILING_DEFAULT struct；新分支须按 TilingKey 注册，GET 宏、Host/Kernel struct、SetDataSize 与冲突故障共同约束 buffer 和 key。
- [TilingData 须 host 与 kernel 各定义一份](tilingdata_host_kernel.md)（`same_topic`）：GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型 与《TilingData 须 host 与 kernel 各定义一份》的实质衔接是：GET_TILING_DATA_WITH_STRUCT 会字符串化结构体名并注册 section，模板尖括号因此解析失败；相关宏、结构注册、显式 header/别名和多 struct 冲突卡共同限定可行修法。
- [kernel.h 须 include struct.h 才能识别 TPL](ascendc_tpl_kernel_h_must_include_struct_h.md)（`same_topic`）：GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型 与《kernel.h 须 include struct.h 才能识别 TPL》的实质衔接是：GET_TILING_DATA_WITH_STRUCT 会字符串化结构体名并注册 section，模板尖括号因此解析失败；相关宏、结构注册、显式 header/别名和多 struct 冲突卡共同限定可行修法。
- [手动 tiling 头遮蔽自动生成类致 no member 判别](tiling_no_member.md)（`same_topic`）：GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型 与《手动 tiling 头遮蔽自动生成类致 no member 判别》的实质衔接是：GET_TILING_DATA_WITH_STRUCT 会字符串化结构体名并注册 section，模板尖括号因此解析失败；相关宏、结构注册、显式 header/别名和多 struct 冲突卡共同限定可行修法。
<!-- cannbot:related:end -->
