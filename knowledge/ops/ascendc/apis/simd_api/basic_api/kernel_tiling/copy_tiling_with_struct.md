---
type: API
title: COPY_TILING_WITH_STRUCT
description: 拷贝Tiling结构体，并返回指向拷贝后的Tiling结构体的指针。该宏适用于嵌套结构体场景，可拷贝结构体的子结构体成员变量。该宏将指定结构体拷贝至栈上，适用于频繁访问Tiling数据的场景，能够加快数据访问速度。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.tiling]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/Kernel-Tiling/COPY_TILING_WITH_STRUCT.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# COPY_TILING_WITH_STRUCT

以结构体方式拷贝 Tiling 数据。通过宏展开从 GM 搬运 Tiling 数据到 Local Memory 并填充到结构体。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型](../../../../runbooks/compilation/get_tiling_data_with_struct.md)（`exemplifies`）：焦点处理COPY_TILING_WITH_STRUCT 宏与 Tiling 结构注册、取数的编译契约；GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型正文说明“GET_TILING_DATA_WITH_STRUCT 宏内部对 tiling_struct 做 # 字符串化拼进 section 名，传入带 <> 的模板类型（如 MaskedFillTilingData<RANK>）会触发 C++ 解析错；用 if constexpr 或 t”。候选对应宏展开所需的结构注册、TilingData 读取或已验证的编译失败边界。
- [RmsNormTiling 与 CANN 内置类型冲突 — 改名隔离](../../../../runbooks/compilation/tiling_type_name_does_not_shadow_cann_builtin.md)（`exemplifies`）：焦点处理COPY_TILING_WITH_STRUCT 宏与 Tiling 结构注册、取数的编译契约；RmsNormTiling 与 CANN 内置类型冲突 — 改名隔离正文说明“CANN kernel_tiling.h 已导出 RmsNormTiling，自定义同名结构体会触发声明冲突与引用歧义；给本地类型增加区分后缀可恢复编译”。候选对应宏展开所需的结构注册、TilingData 读取或已验证的编译失败边界。
- [kernel.h 须 include struct.h 才能识别 TPL](../../../../runbooks/compilation/ascendc_tpl_kernel_h_must_include_struct_h.md)（`exemplifies`）：焦点处理COPY_TILING_WITH_STRUCT 宏与 Tiling 结构注册、取数的编译契约；kernel.h 须 include struct.h 才能识别 TPL正文说明“给算子加 RANK 模板参数（ASCENDC_TPL_ARGS_DECL）后，若 *_kernel.h 未 include *_struct.h，asc_opc 在 apt.cpp 预处理 include 树里看不到 TPL 宏，退化成非模板调用，kernel 编译失败被 wra”。候选对应宏展开所需的结构注册、TilingData 读取或已验证的编译失败边界。
- [手动 tiling 头遮蔽自动生成类致 no member 判别](../../../../runbooks/compilation/tiling_no_member.md)（`exemplifies`）：焦点处理COPY_TILING_WITH_STRUCT 宏与 Tiling 结构注册、取数的编译契约；手动 tiling 头遮蔽自动生成类致 no member 判别正文说明“JOIN_OP_DEF True 工程里，op_host 用 BEGIN_TILING_DATA_DEF 定义 TilingData 后构建系统会自动生成 kernel 侧同名类并经 kernel_tiling/kernel_tiling.h 注入；若 kernel 又手动 #i”。候选对应宏展开所需的结构注册、TilingData 读取或已验证的编译失败边界。
- [直调不可用 GET_TILING_DATA_WITH_STRUCT 宏](../../../../runbooks/compilation/direct_invoke_unavailable_get_tiling_data_with_struct.md)（`exemplifies`）：焦点处理COPY_TILING_WITH_STRUCT 宏与 Tiling 结构注册、取数的编译契约；直调不可用 GET_TILING_DATA_WITH_STRUCT 宏正文说明“`<<<>>>` 直调工程无法使用自定义算子编译期生成的 GET_TILING_DATA_WITH_STRUCT/REGISTER_TILING_DEFAULT 宏，需逐字段从 __gm__ 拷贝 tiling 到 local；其它 void*→GM_ADDR、std::stri”。候选对应宏展开所需的结构注册、TilingData 读取或已验证的编译失败边界。
- [COPY_TILING_WITH_ARRAY](copy_tiling_with_array.md)（`related`）：COPY_TILING_WITH_STRUCT说明拷贝Tiling结构体，并返回指向拷贝后的Tiling结构体的指针。该宏适用于嵌套结构体场景，可拷贝结构体的子结构体成员变量。该宏将指定结构体拷贝至栈上，适用于频繁访问Tiling数据的场景，能够加快数据访问速度；对COPY_TILING_WITH_ARRAY而言，数组 TilingData 的复制宏与结构体宏互为声明方案，Kernel 侧再按整对象或成员宏解析同一块 GM Tiling 数据。
- [GET_TILING_DATA_PTR_WITH_STRUCT](get_tiling_data_ptr_with_struct.md)（`related`）：“GET_TILING_DATA_PTR_WITH_STRUCT”定义：在使用该宏时，开发者可以通过指定结构体名称来获取相应的Tiling信息，并将其填入对应的Tiling结构体中。完成填充后，该宏将返回一个指向该Tiling结构体的指针，并使用__tiling_data_ptr__修饰符对该指针进行修饰。这种修饰方式能够确保在动静态Shape场景下代码的统一性和兼容性。；“COPY_TILING_WITH_STRUCT”定义：拷贝Tiling结构体，并返回指向拷贝后的Tiling结构体的指针。该宏适用于嵌套结构体场景，可拷贝结构体的子结构体成员变量。该宏将指定结构体拷贝至栈上，适用于频繁访问Tiling数据的场景，能够加快数据访问速度。。实质衔接：宏按结构名返回带 __tiling_data_ptr__ 的指针，可再拷到栈；但直调工程没有生成宏、模板类型又会破坏字符串化，两张 runbook 精确界定停止边界。
- [GET_TILING_DATA](get_tiling_data.md)（`same_topic`）：焦点处理COPY_TILING_WITH_STRUCT 宏与 Tiling 结构注册、取数的编译契约；GET_TILING_DATA正文说明“用于获取算子kernel入口函数传入的Tiling信息，并填入注册的TilingData结构体中，此函数会以宏展开的方式进行编译。对应的算子host实现中需要定义TilingData结构体，实现并注册计算TilingData的Tiling函数。如果用户通过TilingData结构”。候选对应宏展开所需的结构注册、TilingData 读取或已验证的编译失败边界。
- [GET_TILING_DATA_MEMBER](get_tiling_data_member.md)（`same_topic`）：焦点处理COPY_TILING_WITH_STRUCT 宏与 Tiling 结构注册、取数的编译契约；GET_TILING_DATA_MEMBER正文说明“用于获取tiling结构体的成员变量”。候选对应宏展开所需的结构注册、TilingData 读取或已验证的编译失败边界。
- [GET_TILING_DATA_WITH_STRUCT](get_tiling_data_with_struct.md)（`same_topic`）：焦点处理COPY_TILING_WITH_STRUCT 宏与 Tiling 结构注册、取数的编译契约；GET_TILING_DATA_WITH_STRUCT正文说明“使用该接口指定结构体名称，可获取指定的tiling信息，并填入对应的Tiling结构体中，此函数会以宏展开的方式进行编译。与GET_TILING_DATA的区别是：GET_TILING_DATA只能获取默认注册的结构体，该接口可以根据指定的结构体名称获取对应的结构体，常用于针对不”。候选对应宏展开所需的结构注册、TilingData 读取或已验证的编译失败边界。
- [Kernel Tiling](kernel_tiling.md)（`same_topic`）：焦点处理COPY_TILING_WITH_STRUCT 宏与 Tiling 结构注册、取数的编译契约；Kernel Tiling正文说明“Kernel Tiling 宏与接口集，包含 GET_TILING_DATA、TILING_KEY_IS、REGISTER_TILING_FOR_TILINGKEY 等 Tiling 数据获取与注册接口”。候选对应宏展开所需的结构注册、TilingData 读取或已验证的编译失败边界。
- [REGISTER_TILING_DEFAULT](register_tiling_default.md)（`same_topic`）：焦点处理COPY_TILING_WITH_STRUCT 宏与 Tiling 结构注册、取数的编译契约；REGISTER_TILING_DEFAULT正文说明“用于在kernel侧注册用户使用标准C++语法自定义的默认TilingData结构体。 注册TilingData结构体用于告知框架侧用户使用标准C++语法来定义TilingData，同时告知框架TilingData结构体类型，用于框架做tiling数据解析”。候选对应宏展开所需的结构注册、TilingData 读取或已验证的编译失败边界。
- [REGISTER_TILING_FOR_TILINGKEY](register_tiling_for_tilingkey.md)（`same_topic`）：焦点处理COPY_TILING_WITH_STRUCT 宏与 Tiling 结构注册、取数的编译契约；REGISTER_TILING_FOR_TILINGKEY正文说明“用于在kernel侧注册与TilingKey相匹配的TilingData自定义结构体；该接口需提供一个逻辑表达式，逻辑表达式以字符串“TILING_KEY_VAR”代指实际TilingKey，表达TilingKey所满足的范围”。候选对应宏展开所需的结构注册、TilingData 读取或已验证的编译失败边界。
- [RegisterNoneTiling](register_none_tiling.md)（`same_topic`）：焦点处理COPY_TILING_WITH_STRUCT 宏与 Tiling 结构注册、取数的编译契约；RegisterNoneTiling正文说明“Kernel侧使用标准C++语法定义TilingData时，告知框架使用未注册结构体，配套GET_TILING_DATA系列接口获取TilingData”。候选对应宏展开所需的结构注册、TilingData 读取或已验证的编译失败边界。
<!-- cannbot:related:end -->
