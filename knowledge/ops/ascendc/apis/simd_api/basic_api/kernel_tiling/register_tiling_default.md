---
type: API
title: REGISTER_TILING_DEFAULT
description: 用于在kernel侧注册用户使用标准C++语法自定义的默认TilingData结构体。 注册TilingData结构体用于告知框架侧用户使用标准C++语法来定义TilingData，同时告知框架TilingData结构体类型，用于框架做tiling数据解析。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.tiling]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/Kernel-Tiling/REGISTER_TILING_DEFAULT.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# REGISTER_TILING_DEFAULT

用于在kernel侧注册用户使用标准C++语法自定义的默认TilingData结构体。 注册TilingData结构体用于告知框架侧用户使用标准C++语法来定义TilingData，同时告知框架TilingData结构体类型，用于框架做tiling数据解析。

用于在kernel侧注册用户使用标准C++语法自定义的默认TilingData结构体。 注册TilingData结构体用于告知框架侧用户使用标准C++语法来定义TilingData，同时告知框架TilingData结构体类型，用于框架做tiling数据解析。

本接口属于 Kernel 侧 Tiling 接口，用于 Host 侧向 Kernel 侧传递 Tiling 参数。

约束：若TilingData结构体在命名空间内，注册时需要携带对应的命名空间作用域符。；暂不支持Kernel直调工程。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

<!-- cannbot:related:start -->
## 相关

- [ACLNN 507035 — stub kernel tiling 数据未初始化](../../../../runbooks/compilation/aclnn_507035_stub_tilingfunc_must_init_tiling_buffer.md)（`exemplifies`）：stub TilingFunc 必须调用 `context->GetTilingData<TilingDataT>()` 取得指针并写入至少一个字段（如 `totalLength`），再 `SetBlockDim`/workspace；kernel 侧保持接口桩不变。修复后 11/11 冒烟通过。；用于在kernel侧注册用户使用标准C++语法自定义的默认TilingData结构体。 注册TilingData结构体用于告知框架侧用户使用标准C++语法来定义TilingData，同时告知框架TilingData结构体类型，用于框架做tiling数据解析。。运行手册的修复要求 Host 初始化与 Kernel 接口桩保持同一 TilingDataT，REGISTER_TILING_DEFAULT 卡说明该注册向框架声明结构体类型供解析，因而支撑 507035 复现与修复中的类型注册步骤。
- [REGISTER_TILING_DEFAULT 取小档致 NaN](../../../../runbooks/compilation/register_tiling_default_nan.md)（`exemplifies`）：用于在kernel侧注册用户使用标准C++语法自定义的默认TilingData结构体；修复前 `opParaSize=132` 对所有 binary 成立。接口卡定义 default TilingData 注册，运行手册展示 default 选成小档后框架推导出的 opParaSize 截断大档结构并造成全 NaN 的实证。
- [REGISTER_TILING_DEFAULT 多 struct 冲突](../../../../runbooks/compilation/register_tiling_default_struct.md)（`exemplifies`）：用于在kernel侧注册用户使用标准C++语法自定义的默认TilingData结构体；若存在 ≥2 个**不同**的 struct 被注册为 default，即为根因。接口卡定义 default 注册槽位，运行手册把同一算子多分支注册不同 struct 的 opbuild 冲突收敛到该槽位唯一性。
- [FastGelu 950 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/fast_gelu_950.md)（`related`）：“Host 的 `GetTilingData<EleBaseTilingDataV2>` 与 entry 的 `REGISTER_TILING_DEFAULT/GET_TILING_DATA_WITH_STRUCT` 使用同一声明。”说明 FastGelu 注册与读取共享 ABI；“用于在kernel侧注册用户使用标准C++语法自定义的默认TilingData结构体。”给出 REGISTER_TILING_DEFAULT 在该链中的职责。
<!-- cannbot:related:end -->
