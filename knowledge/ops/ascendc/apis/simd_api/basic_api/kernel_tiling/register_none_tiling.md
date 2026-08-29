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

- [507035 host tiling workspace 缺 RESERVED](../../../../runbooks/compilation/register_none_tiling_reserved_workspace_507035.md)（`exemplifies`）：“`REGISTER_NONE_TILING` 模式下，框架生成的 kernel wrapper 调用 `SetSysWorkspaceForce(workspace)` 把整个 workspace 起始段留作系统保留区，再计算 `usrWorkspace = workspace + AscendC::RESERVED_WORKSPACE` 并把 `usrWorkspace` 作为 `workspace` 形参传给 kernel。”把 507035 的触发范围锁定在 REGISTER_NONE_TILING 的无 TilingFunc 路径；“Kernel侧使用标准C++语法定义TilingData时，告知框架使用未注册结构体，配套GET_TILING_DATA系列接口获取TilingData。”定义该注册模式的框架入口。两端共同提示此模式下 workspace 总量不能沿用 TilingFunc 路径的假设。
- [REGISTER_NONE_TILING 致 UnboundLocalError](../../../../runbooks/compilation/register_none_tiling_unboundlocalerror.md)（`exemplifies`）：Kernel侧使用标准C++语法定义TilingData时，告知框架使用未注册结构体，配套GET_TILING_DATA系列接口获取TilingData。；op-compile 在 `REGISTER_NONE_TILING` 下抛 `UnboundLocalError: cannot access local variable 'tiling_struct_size'`（ascendc_compile_dfx.py:239 `_generate_binary_for_tiling_without_register`）（来源平台：950；证据等级: tool_observed）；API 给出未注册结构体模式，runbook 提供模板化 TilingData 在 CANN 9.1.0 上的构建失败与替代注册方式。
- [直调不可用 GET_TILING_DATA_WITH_STRUCT 宏](../../../../runbooks/compilation/direct_invoke_unavailable_get_tiling_data_with_struct.md)（`exemplifies`）：Kernel侧使用标准C++语法定义TilingData时，告知框架使用未注册结构体，配套GET_TILING_DATA系列接口获取TilingData。；直调路径下 `REGISTER_TILING_DEFAULT` / `GET_TILING_DATA_WITH_STRUCT` / `TILING_KEY_IS` 不可用，须用上述手动 `__gm__` 拷贝替代；`KERNEL_TASK_TYPE_DEFAULT(KERNEL_TYPE_AIV_ONLY)` 在直调路径仍可用且应保留。；焦点定义打包路径的注册与获取接口，目标给出迁到直调工程时必须改为手工解包的边界。
<!-- cannbot:related:end -->
