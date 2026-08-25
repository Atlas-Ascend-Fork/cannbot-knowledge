---
type: API
title: RegisterNoneTiling
description: Kernel侧使用标准C++语法定义TilingData时，告知框架使用未注册结构体，配套GET_TILING_DATA系列接口获取TilingData。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.tiling]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/Kernel-Tiling/REGISTER_NONE_TILING.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# RegisterNoneTiling

Kernel侧使用标准C++语法定义TilingData时，告知框架使用未注册结构体，配套GET_TILING_DATA系列接口获取TilingData。

使用该接口指定结构体名称，可获取指定的tiling信息，并填入对应的Tiling结构体中，此函数会以宏展开的方式进行编译。与GET_TILING_DATA的区别是：GET_TILING_DATA只能获取默认注册的结构体，该接口可以根据指定的结构体名称获取对应的结构体，常用于针对不同的TilingKey注册了不同结构体的情况下。

本接口组包含 GET_TILING_DATA_WITH_STRUCT, GET_TILING_DATA_MEMBER, GET_TILING_DATA_PTR_WITH_STRUCT, GET_TILING_DATA, 5.11.1-GET_TILING_DATA。

本接口属于 Kernel 侧 Tiling 接口，用于 Host 侧向 Kernel 侧传递 Tiling 参数。

约束：本函数需在算子Kernel代码处使用，并且传入的tiling_data参数不需要声明类型。；暂不支持Kernel直调工程。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [507035 host tiling workspace 缺 RESERVED](../../../../runbooks/compilation/register_none_tiling_reserved_workspace_507035.md)（`exemplifies`）：507035 host tiling workspace 缺 RESERVED 与《RegisterNoneTiling》的实质衔接是：REGISTER_NONE_TILING wrapper 会先预留系统 workspace，再把用户指针偏移 RESERVED_WORKSPACE；RegisterNoneTiling、Get/SetSysWorkspace、GetUserWorkspace 与指南构成同一地址契约。
- [GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型](../../../../runbooks/compilation/get_tiling_data_with_struct.md)（`exemplifies`）：RegisterNoneTiling：RegisterNoneTiling 与 GET_TILING_DATA 系列共同完成未注册 C++ struct 的 kernel 解码；两个 runbook分别覆盖该宏在生成器与 RESERVED workspace 场景的实际失败，直调限制卡界定不可用边界。 目标卡《GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型》补充：GET_TILING_DATA_WITH_STRUCT 宏内部对 tiling_struct 做 # 字符串化拼进 section 名，传入带 <> 的模板类型（如 MaskedFillTilingData<RANK>）会触发 C++ 解析错；用 if constexpr 或 trait 绕开 <> 又会破坏节级 tiling 注册，报 do not registe tiling struct。
- [REGISTER_NONE_TILING 致 UnboundLocalError](../../../../runbooks/compilation/register_none_tiling_unboundlocalerror.md)（`exemplifies`）：RegisterNoneTiling：RegisterNoneTiling 与 GET_TILING_DATA 系列共同完成未注册 C++ struct 的 kernel 解码；两个 runbook分别覆盖该宏在生成器与 RESERVED workspace 场景的实际失败，直调限制卡界定不可用边界。 目标卡《REGISTER_NONE_TILING 致 UnboundLocalError》补充：按 DESIGN 规范在模板化 TilingData 的 kernel 入口写 REGISTER_NONE_TILING 时，CANN 9.1.0 op-compile 的 dfx 生成器在 _generate_binary_for_tiling_without_register 抛 UnboundLocalError；判别后改用 REGISTER_TILING_DEFAULT(具体模板实例化) 规避。
- [Stub tiling padding 不解 aclnn Segfault](../../../../runbooks/compilation/stub_tiling_padding_aclnn_segfault.md)（`exemplifies`）：REGISTER_NONE_TILING 是 stub kernel 的无 tiling 注册入口；与结构化注册对照可明确何时根本没有 tiling 参数、何时必须为真实 Host Tiling 预留容量。
- [直调不可用 GET_TILING_DATA_WITH_STRUCT 宏](../../../../runbooks/compilation/direct_invoke_unavailable_get_tiling_data_with_struct.md)（`exemplifies`）：RegisterNoneTiling：RegisterNoneTiling 与 GET_TILING_DATA 系列共同完成未注册 C++ struct 的 kernel 解码；两个 runbook分别覆盖该宏在生成器与 RESERVED workspace 场景的实际失败，直调限制卡界定不可用边界。 目标卡《直调不可用 GET_TILING_DATA_WITH_STRUCT 宏》补充：`<<<>>>` 直调工程无法使用自定义算子编译期生成的 GET_TILING_DATA_WITH_STRUCT/REGISTER_TILING_DEFAULT 宏，需逐字段从 __gm__ 拷贝 tiling 到 local；其它 void*→GM_ADDR、std::string、goto 限制为次要附带项，见对应卡。
- [kernel侧获取Tiling信息不正确](../../../../guides/programming_guide/appendix/faq/kernel_tiling_info_incorrect.md)（`explains`）：RegisterNoneTiling：RegisterNoneTiling 与 GET_TILING_DATA 系列共同完成未注册 C++ struct 的 kernel 解码；两个 runbook分别覆盖该宏在生成器与 RESERVED workspace 场景的实际失败，直调限制卡界定不可用边界。 目标卡《kernel侧获取Tiling信息不正确》补充：通过算子在kernel侧实现代码中添加PRINTF打印发现kernel侧获取的Tiling信息不正确。
- [GET_TILING_DATA_MEMBER](get_tiling_data_member.md)（`related`）：RegisterNoneTiling：RegisterNoneTiling 与 GET_TILING_DATA 系列共同完成未注册 C++ struct 的 kernel 解码；两个 runbook分别覆盖该宏在生成器与 RESERVED workspace 场景的实际失败，直调限制卡界定不可用边界。 目标卡《GET_TILING_DATA_MEMBER》补充：用于获取tiling结构体的成员变量。
- [GET_TILING_DATA_PTR_WITH_STRUCT](get_tiling_data_ptr_with_struct.md)（`related`）：RegisterNoneTiling：RegisterNoneTiling 与 GET_TILING_DATA 系列共同完成未注册 C++ struct 的 kernel 解码；两个 runbook分别覆盖该宏在生成器与 RESERVED workspace 场景的实际失败，直调限制卡界定不可用边界。 目标卡《GET_TILING_DATA_PTR_WITH_STRUCT》补充：在使用该宏时，开发者可以通过指定结构体名称来获取相应的Tiling信息，并将其填入对应的Tiling结构体中。完成填充后，该宏将返回一个指向该Tiling结构体的指针，并使用__tiling_data_ptr__修饰符对该指针进行修饰。这种修饰方式能够确保在动静态Shape场景下代码的统一性和兼容性。
- [GET_TILING_DATA_WITH_STRUCT](get_tiling_data_with_struct.md)（`related`）：RegisterNoneTiling：RegisterNoneTiling 与 GET_TILING_DATA 系列共同完成未注册 C++ struct 的 kernel 解码；两个 runbook分别覆盖该宏在生成器与 RESERVED workspace 场景的实际失败，直调限制卡界定不可用边界。 目标卡《GET_TILING_DATA_WITH_STRUCT》补充：使用该接口指定结构体名称，可获取指定的tiling信息，并填入对应的Tiling结构体中，此函数会以宏展开的方式进行编译。与GET_TILING_DATA的区别是：GET_TILING_DATA只能获取默认注册的结构体，该接口可以根据指定的结构体名称获取对应的结构体，常用于针对不同的TilingKey注册了不同结构体的情况下。
- [Kernel Tiling](kernel_tiling.md)（`related`）：RegisterNoneTiling：RegisterNoneTiling 与 GET_TILING_DATA 系列共同完成未注册 C++ struct 的 kernel 解码；两个 runbook分别覆盖该宏在生成器与 RESERVED workspace 场景的实际失败，直调限制卡界定不可用边界。 目标卡《Kernel Tiling》补充：Kernel Tiling 宏与接口集，包含 GET_TILING_DATA、TILING_KEY_IS、REGISTER_TILING_FOR_TILINGKEY 等 Tiling 数据获取与注册接口。
- [COPY_TILING_WITH_STRUCT](copy_tiling_with_struct.md)（`same_topic`）：焦点处理COPY_TILING_WITH_STRUCT 宏与 Tiling 结构注册、取数的编译契约；RegisterNoneTiling正文说明“Kernel侧使用标准C++语法定义TilingData时，告知框架使用未注册结构体，配套GET_TILING_DATA系列接口获取TilingData”。候选对应宏展开所需的结构注册、TilingData 读取或已验证的编译失败边界。
<!-- cannbot:related:end -->
