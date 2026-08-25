---
type: "Runbook"
title: "ACLNN 561000 非连续张量需 AutoContiguous"
description: "aclnn 算子仓 OpDef 的 Input 未在 OpParamDef 链上声明 AutoContiguous()/IgnoreContiguous() 时，带显式 strides 的 ND 张量在 kernel launch 前被框架判为 non-contiguous，报 errno 226808025 并升级为 561000。判别：grep plog 取 226808025/561000，核查 op_host *_def.cpp 的 Input 链是否声明连续性策略；AutoContiguous 是 OpParamDef 方法而非 OpDef 方法。"
tags: ["task.debugging", "topic.implementation.operator_registration", "topic.data_movement.layout_transform"]
status: stable
sources: []
created_at: "2026-08-18T07:22:13Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
aliases: ["aclnnTriu", "non_contiguous"]
---

# ACLNN 561000 非连续张量需 AutoContiguous

## 现象

在 ascend950 平台完成 Triu 算子 op_kernel 实现后，运行白盒 aclnn ST 时多个用例报 ACLNN 561000 运行时错误，覆盖连续张量与非连续 view（transpose/slice）两类：测试代码经 `aclCreateTensor(..., strides.data(), ...)` 显式传入 strides 后，框架在 kernel launch 前拒绝执行。从 plog 同时观测到 `errno[226808025]`（non-contiguous tensor, policy not configured）与升级后的 `errno[561000]`（NnopbaseExecutorRunWithWorkspace failed）。

## 适用场景

- **工程形态**：aclnn 算子仓开发（ops-registry-invoke 范式，`OpDef` + `aclnn<Op>` API），白盒 ST 经 `aclCreateTensor` 构造输入张量。
- **API 路径**：`OpDef::Input("self").ParamType(...).DataType(...).Format(...)` → `OpParamDef::AutoContiguous()` / `OpParamDef::IgnoreContiguous()`。
- **验证过的平台与 CANN 版本**：ascend950（dav-3510），CANN 9.1.0。
- **适用粒度**：`platform_wide`（所有 aclnn 算子仓的 OpDef Input 均需声明连续性策略）。
- **路线优先级**：`recommended_fastpath`（声明 `AutoContiguous()` 是框架设计的预期入口）。
- **明确不适用或未验证场景**：a2/a3 平台未验证，推断可迁移（aclnn 框架行为应一致）；`IgnoreContiguous()` 路线（kernel 自行处理 strides）未验证。

## 判别方法

1. **触发信号**：白盒 aclnn ST 运行 `aclnn<Op>(workspace, workspaceSize, executor, stream)` 报 `ACLNN error 561000`，且失败集中在带显式 strides 的 ND 张量用例（含行主序连续但显式传入 strides 的用例），属系统性连续性策略缺失，非单 case 精度问题。
2. **可执行探针**：`grep -E "226808025|561000" <plog_path>` 提取框架错误；核查 `op_host/*_def.cpp` 的 `this->Input("self")...` 链尾是否调用 `.AutoContiguous()` 或 `.IgnoreContiguous()`；确认 ST 是否经 `aclCreateTensor(..., strides.data(), ...)` 传入显式 strides。
3. **原始观测**：plog 同时打印两条 errno（verbatim 取自 trace 的 bash grep plog tool_result）：
   ```
   [ERROR] ... [NNOP][NnopbaseExecutorPrintErrMsg] ... errno[226808025] OpName:[Triu_0] ... Parameter self of the operator is a non-contiguous tensor. A processing policy must be configured through the AutoContiguous() or IgnoreContiguous() API of the OpDef class.
   [ERROR] ... [NNOP][NnopbaseExecutorRunWithWorkspace] ... errno[561000] OpName:[Triu_0] Check NnopbaseExecutorUpdateAddr(executor, workspace, workspaceLen) failed
   ```
   关键点：即使张量 strides 是行主序连续的（如 shape `{2,4,4}`、strides `{16,4,1}`），只要 `aclCreateTensor` 显式传入 strides，框架仍将其判为 non-contiguous 并触发检查；真正的非连续 view（transpose/slice）同理触发。
4. **解释**：aclnn 框架在 `NnopbaseExecutorRunWithWorkspace` 执行前检查输入张量的连续性策略声明。OpDef Input 的 `OpParamDef` 链未声明 `AutoContiguous()`/`IgnoreContiguous()` 时，框架以 `errno 226808025`（policy not configured）拒绝执行并升级为 `errno 561000`（kernel launch 失败）。`AutoContiguous()` 是 `OpParamDef`（Input/Output 定义）的方法（`op_def.h` 声明 `OpParamDef &AutoContiguous()`），须在 `this->Input("self")` 返回的 `OpParamDef&` 链尾追加；在 `OpDef` 算子类上调用 `this->AutoContiguous()` 会编译报 `'class ops::<Op>' has no member named 'AutoContiguous'`。**排除项**：UB headroom（缩小 `ubSize` 留 headroom）不是 561000 根因——调整后同样用例仍 561000，证明根因是连续性策略声明缺失而非缓冲区溢出。

## 验证信号

- plog 打印 `errno[226808025]` "Parameter self ... is a non-contiguous tensor ... AutoContiguous() or IgnoreContiguous()"（来源平台:950；证据等级: tool_observed）
- plog 打印 `errno[561000]` "NnopbaseExecutorRunWithWorkspace failed"（来源平台:950；证据等级: tool_observed）
- 在 `Input("self")` 的 `OpParamDef` 链尾追加 `.AutoContiguous()` 后，非连续 view（transpose/slice）用例 ST 通过（来源平台:950；证据等级: tool_observed）

## 失效边界

- ascend950/CANN 9.1.0 实测；a2/a3 未验证，推断可迁移（aclnn 框架连续性检查机制跨平台一致）。
- `IgnoreContiguous()` 路线未验证：若 kernel 需要原始 strides 做语义正确的 view 操作，`AutoContiguous()` 会丢失 view 语义；对按 view 行列定义掩码的算子（如 triu），AutoContiguous 将非连续 view 转为连续拷贝后 kernel 看到正确逻辑行列序；对 stride-sensitive 算子可能不适用。
- 本卡诊断的是 aclnn 框架的连续性策略声明缺失；非 aclnn 路径（kernel 直调）不经 `NnopbaseExecutorRunWithWorkspace`，不触发本检查。

## 预防

- 所有 aclnn 算子仓的 `OpDef` Input，若 kernel 假设连续数据布局，**必须声明 `.AutoContiguous()`**（框架自动转连续）或 `.IgnoreContiguous()`（kernel 自行处理 strides）。
- 即使测试用例传入连续张量，只要 `aclCreateTensor` 带显式 strides，框架仍触发连续性检查——不能以"张量实际连续"为由省略声明。
- `AutoContiguous()` vs `IgnoreContiguous()`：kernel 处理线性存储且不感知 view strides 时用 `AutoContiguous()`；kernel 需要原始 strides 做语义正确的 view 操作时用 `IgnoreContiguous()`。

## 坏实践

- 在 `OpDef`（算子类）上调用 `this->AutoContiguous()`：API 不在 `OpDef` 上，编译报 `has no member named 'AutoContiguous'`；正确做法是在 `Input("self")` 返回的 `OpParamDef&` 链尾追加。
- 用 `IgnoreContiguous()` 但 kernel 仍假设连续：非连续张量传入 kernel 后按线性偏移反推的 (i,j) 与 view 语义不符，产生精度错误。
- 将 UB headroom 调整当作 561000 的修复——掩盖连续性策略声明缺失的真因。

<!-- cannbot:related:start -->
## 相关

- [AutoContiguous](../../apis/utils_api/prototype_register_management/op_param_def/auto_contiguous.md)（`exemplifies`）：ACLNN 561000 非连续张量需 AutoContiguous 与《AutoContiguous》的实质衔接是：561000 来自 OpParamDef 未声明连续性策略；AutoContiguous/IgnoreContiguous、Input/OpDef 和非连续 Load/Store/Slice/Transpose 卡共同决定转换还是保留 strides。
- [IgnoreContiguous](../../apis/utils_api/prototype_register_management/op_param_def/ignore_contiguous.md)（`exemplifies`）：ACLNN 561000 非连续张量需 AutoContiguous 与《IgnoreContiguous》的实质衔接是：561000 来自 OpParamDef 未声明连续性策略；AutoContiguous/IgnoreContiguous、Input/OpDef 和非连续 Load/Store/Slice/Transpose 卡共同决定转换还是保留 strides。
- [Input（OpDef）](../../apis/utils_api/prototype_register_management/op_def/input.md)（`exemplifies`）：焦点处理OpDef Input 的参数类型、格式、可选性和值依赖配置；ACLNN 561000 非连续张量需 AutoContiguous正文说明“aclnn 算子仓 OpDef 的 Input 未在 OpParamDef 链上声明 AutoContiguous()/IgnoreContiguous() 时，带显式 strides 的 ND 张量在 kernel launch 前被框架判为 non-contiguous，报 ”。候选配置 Input 返回的 OpParamDef，或复现输入可选性、格式和值依赖造成的框架故障。
- [Input（原型注册管理）](../../apis/utils_api/prototype_register_management/op_ai_core_config/input.md)（`exemplifies`）：《Input（原型注册管理）》处理“某些场景下，同一个算子在不同的AI处理器型号上，其支持的原型输入不同。 通过该接口，可针对不同的AI处理器型号注册差异化的算子原型。调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。”。《ACLNN 561000 非连续张量需 AutoContiguous》明确“aclnn 算子仓 OpDef 的 Input 未在 OpParamDef 链上声明 AutoContiguous()/IgnoreContiguous() 时，带显式 strides 的 ND 张量在 kernel launch 前被框架判为 non-contiguous，报 errno 226808025 并升级为 561000。判别：grep plog 取 226808025/561000，核查 op_host *_def.cpp 的 Input 链是否声明连续性策略；AutoContiguous 是 OpParamDef 方法而非 OpDef 方法。”，可直接用于核对算子 Input/Output 原型、OpParamDef dtype/format/optional/value-depend 参数及已证注册故障。
- [LoadAlign](../../apis/simd_api/basic_api/reg_vector_compute/reg_data_load/load_align_continuous.md)（`exemplifies`）：ACLNN 561000 非连续张量需 AutoContiguous 与《LoadAlign》的实质衔接是：561000 来自 OpParamDef 未声明连续性策略；AutoContiguous/IgnoreContiguous、Input/OpDef 和非连续 Load/Store/Slice/Transpose 卡共同决定转换还是保留 strides。
- [LoadAlign](../../apis/simd_api/basic_api/reg_vector_compute/reg_data_load/load_align_noncontinuous.md)（`exemplifies`）：ACLNN 561000 非连续张量需 AutoContiguous 与《LoadAlign》的实质衔接是：561000 来自 OpParamDef 未声明连续性策略；AutoContiguous/IgnoreContiguous、Input/OpDef 和非连续 Load/Store/Slice/Transpose 卡共同决定转换还是保留 strides。
- [LoadUnAlign](../../apis/simd_api/basic_api/reg_vector_compute/reg_data_load/load_un_align_continuous.md)（`exemplifies`）：ACLNN 561000 非连续张量需 AutoContiguous 与《LoadUnAlign》的实质衔接是：561000 来自 OpParamDef 未声明连续性策略；AutoContiguous/IgnoreContiguous、Input/OpDef 和非连续 Load/Store/Slice/Transpose 卡共同决定转换还是保留 strides。
- [OpDef](../../apis/utils_api/prototype_register_management/op_def/op_def.md)（`exemplifies`）：ACLNN 561000 非连续张量需 AutoContiguous 与《OpDef》的实质衔接是：561000 来自 OpParamDef 未声明连续性策略；AutoContiguous/IgnoreContiguous、Input/OpDef 和非连续 Load/Store/Slice/Transpose 卡共同决定转换还是保留 strides。
- [OpParamDef](../../apis/utils_api/prototype_register_management/op_param_def/op_param_def.md)（`exemplifies`）：ACLNN 561000 非连续张量需 AutoContiguous 与《OpParamDef》的实质衔接是：561000 来自 OpParamDef 未声明连续性策略；AutoContiguous/IgnoreContiguous、Input/OpDef 和非连续 Load/Store/Slice/Transpose 卡共同决定转换还是保留 strides。
- [Slice（基础API）](../../apis/simd_api/basic_api/data_structure_tensor_api/tensor_structure/slice.md)（`exemplifies`）：ACLNN 561000 非连续张量需 AutoContiguous 与《Slice（基础API）》的实质衔接是：561000 来自 OpParamDef 未声明连续性策略；AutoContiguous/IgnoreContiguous、Input/OpDef 和非连续 Load/Store/Slice/Transpose 卡共同决定转换还是保留 strides。
- [StoreAlignContinuous](../../apis/simd_api/basic_api/reg_vector_compute/reg_data_store/store_align_continuous.md)（`exemplifies`）：ACLNN 561000 非连续张量需 AutoContiguous 与《StoreAlignContinuous》的实质衔接是：561000 来自 OpParamDef 未声明连续性策略；AutoContiguous/IgnoreContiguous、Input/OpDef 和非连续 Load/Store/Slice/Transpose 卡共同决定转换还是保留 strides。
- [StoreAlignNoncontinuous](../../apis/simd_api/basic_api/reg_vector_compute/reg_data_store/store_align_noncontinuous.md)（`exemplifies`）：ACLNN 561000 非连续张量需 AutoContiguous 与《StoreAlignNoncontinuous》的实质衔接是：561000 来自 OpParamDef 未声明连续性策略；AutoContiguous/IgnoreContiguous、Input/OpDef 和非连续 Load/Store/Slice/Transpose 卡共同决定转换还是保留 strides。
- [Transpose](../../apis/simd_api/adv_api/tensor_transform/transpose.md)（`exemplifies`）：《Transpose》处理“对输入数据进行数据排布及Reshape操作，支持NZ与ND格式间的多种轴互换和转置场景。”。《ACLNN 561000 非连续张量需 AutoContiguous》明确提供“aclnn 算子仓 OpDef 的 Input 未在 OpParamDef 链上声明 AutoContiguous()/IgnoreContiguous() 时，带显式 strides 的 ND 张量在 kernel launch 前被框架判为 non-contiguous，报 errno 226808025 并升级为 561000。判别：grep plog 取 226808025/561000，核查 op_host *_def.cpp 的 Input 链是否声明连续性策略；AutoContiguous 是 OpParamDef 方法而非 OpDef 方法。”，其参数、调用或验证步骤直接接入Transpose 的 Tiling、转置搬运、布局转换和轴顺序验证。
- [Transpose](../../apis/simd_api/basic_api/memory_vector_compute/data_layout_conversion/transpose.md)（`exemplifies`）：ACLNN 561000 非连续张量需 AutoContiguous 与《Transpose》的实质衔接是：561000 来自 OpParamDef 未声明连续性策略；AutoContiguous/IgnoreContiguous、Input/OpDef 和非连续 Load/Store/Slice/Transpose 卡共同决定转换还是保留 strides。
- [MulPreferContiguous 稀疏广播拦截失败且慢于 304](../performance/mulprefercontiguous_304.md)（`same_topic`）：《MulPreferContiguous 稀疏广播拦截失败且慢于 304》处理“B 类稀疏广播（首轴稀疏、stride 大）触发 MulPreferContiguous 拦截转连续，baseline GetWorkspaceSize 返回 -1.0（schMode 空）或性能慢于 fixed 直接走 304 nddma_transpose_noLoop。”。《ACLNN 561000 非连续张量需 AutoContiguous》提供“aclnn 算子仓 OpDef 的 Input 未在 OpParamDef 链上声明 AutoContiguous()/IgnoreContiguous() 时，带显式 strides 的 ND 张量在 kernel launch 前被框架判为 non-contiguous，报 errno 226808025 并升级为 561000。判别：grep plog 取 226808025/561000，核查 op_host *_def.cpp 的 Input 链是否声明连续性策略；AutoContiguous 是 OpParamDef 方法而非 OpDef 方法。”，其具体合同或探针直接接入稀疏广播输入的 contiguous 拦截、304 路由和非连续 shape/stride 合同。
- [批次行索引未对 M 回绕致整行置零判别](../precision/m.md)（`same_topic`）：《批次行索引未对 M 回绕致整行置零判别》处理“批次化逐元素掩码 kernel 用线性偏移 gmOffset % (M*N) 反推 (i,j)，在 chunk 循环内推进行索引时 i += newJ/N 未对 M 取模；tile 跨 batch 边界时 batch>0 的行 0 得到 i=M 而非 i=0，使 start_col=clamp(i+diagonal,0,N)=N、keep 区间为空、整行误置零。判别=只在 rank≥3 且 batch>1 的用例失败、且表现为整行置零而非逐元素错位。”。《ACLNN 561000 非连续张量需 AutoContiguous》提供“aclnn 算子仓 OpDef 的 Input 未在 OpParamDef 链上声明 AutoContiguous()/IgnoreContiguous() 时，带显式 strides 的 ND 张量在 kernel launch 前被框架判为 non-contiguous，报 errno 226808025 并升级为 561000。判别：grep plog 取 226808025/561000，核查 op_host *_def.cpp 的 Input 链是否声明连续性策略；AutoContiguous 是 OpParamDef 方法而非 OpDef 方法。”，其具体合同或探针直接接入批次 tile 跨 M 边界的行索引回绕、AutoContiguous 排除和 rank≥3 验证。
<!-- cannbot:related:end -->
