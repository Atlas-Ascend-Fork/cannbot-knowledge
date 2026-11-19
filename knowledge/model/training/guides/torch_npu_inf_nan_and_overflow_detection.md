---
type: Guide
title: TorchNPU Inf/NaN：计算模式与溢出检测分开配置
description: 区分饱和模式改变数值、非饱和模式检测与 950 的查询限制，说明 FORCE_OVERFLOW_CHECK 的 CANN 门槛。
tags:
- task.debugging
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/INF_NAN_MODE_ENABLE.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/INF_NAN_MODE_FORCE_DISABLE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/FORCE_OVERFLOW_CHECK.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/appendixes/inf_nan_difference_apis.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/appendixes/inf_nan_difference_apis.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/op_execution/INF_NAN_MODE_ENABLE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/op_execution/INF_NAN_MODE_FORCE_DISABLE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/op_execution/FORCE_OVERFLOW_CHECK.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-clear_npu_overflow_flag.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-clear_npu_overflow_flag.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-clear_npu_overflow_flag.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-get_npu_overflow_flag.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-get_npu_overflow_flag.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-get_npu_overflow_flag.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-utils-is_support_inf_nan.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-utils-is_support_inf_nan.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-utils-is_support_inf_nan.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-utils-npu_check_overflow.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-utils-npu_check_overflow.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-utils-npu_check_overflow.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_alloc_float_status.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_alloc_float_status.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_alloc_float_status.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_clear_float_status.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_clear_float_status.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_clear_float_status.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_get_float_status.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_get_float_status.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_get_float_status.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/FloatStatusKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/FloatStatusKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/interface/AclInterface.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/interface/AclInterface.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NpuVariables.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NpuVariables.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionsManager.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/register/OptionsManager.cpp
  role: implementation
created_at: '2026-11-09T06:01:51Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
---

# TorchNPU Inf/NaN：计算模式与溢出检测分开配置

## 固定版本与证据

依据 PyTorch/TorchNPU 固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的环境变量文档，按所列产品和选项限制使用，不推导发布组合具备全部功能。只读来源审阅，未运行上游代码或设备实验。

## A2/A3 的数值模式

INF_NAN_MODE_ENABLE 默认 1 使用 Inf/NaN 模式；0 的饱和模式把溢出结果饱和为对应浮点极值，把 NaN 变为 0，会改变后续计算。A2/A3 对关闭 Inf/NaN 模式有拦截，如确需饱和路线还要满足 INF_NAN_MODE_FORCE_DISABLE=1；后者默认 0。两项均只允许 0/1，进程启动前配置，运行中修改不生效。

来源列举旧 Atlas 产品仅支持饱和模式、950 仅支持 Inf/NaN 模式，相关切换变量对它们不生效。本卡元数据选 A2/A3，不能把它作为 950 的模式切换教程。关闭 Inf/NaN 后看不到 NaN 不证明模型原本没有数值溢出。

## 非饱和模式的异步检测

FORCE_OVERFLOW_CHECK 默认 0，1 在 Inf/NaN 模式开启溢出检测，**不改变浮点计算模式**。要求 CANN≥9.1.0，不满足时告警并忽略；仅 0/1，其他值视作未配，进程启动前设置。该版本门槛低于本卡登记的 CANN9.0 发布基线，不回推其已有能力。

A2/A3 可通过文档列举的 get_npu_overflow_flag、npu_check_overflow、clear_npu_overflow_flag 查询/清除状态，避免把整份梯度搬到 Host 判断造成额外同步。950 文档明确不支持这些状态查询接口，开关生效要看ASCEND_GLOBAL_LOG_LEVEL=1时plog中aclrtSetStreamOverflowSwitch相关记录；开关或日志存在也不代表能在 950 调用查询接口。

该检测有性能开销，仅作为数值定位工具。记录计算模式、检测开关、溢出窗口和清除时机，分别检查原始数值与状态，不用检测开关替代 GradScaler 的正确生命周期。


## 核验

保存解释器、包版本、设备、完整配置及首次生效时机，在新进程中做单项对照。检查数值与实际路径，再分别比较首次启动、稳态时间和资源开销；调试配置关闭后复测。

## 与原生结果比较时区分异常输入与计算溢出

固定主线inf_nan_difference_apis附录另外列出Tensor.sign、torch.sign、torch.linalg.svd、torch.linalg.qr：输入含Inf/NaN时，其行为可能与原生实现不同。不要把异常输入上的差异直接归因为HF32或确定性开关；也不能据此认定这些入口在所有有限输入上都不一致。

附录还说明，即使输入本身有限，溢出后可能出现原生NaN而NPU为±Inf、原生±Inf而NPU为NaN、双方均Inf但符号不同。来源将这些特定差异归因于硬件计算机制；这一解释不表示可以忽略模型真实溢出、非法输入或普通有限值误差。分别记录输入是否有限、首次溢出位置、计算模式与溢出状态，再选择参考与验收条件。

该附录没有提供新的逐产品矩阵；本节不扩大本卡A2/A3平台范围，也不改变前述950查询限制。只完成文档审阅，没有异常值或设备复测。

## 英文附录对异常值分类的核对

同提交英文inf_nan_difference_apis与中文列同四个异常输入入口和同三种溢出输出差异。它没有逐产品矩阵或误差阈值，不将“硬件行为差异而非精度问题”扩为任何有限输入误差都可忽略，也不改变本指南A2/A3模式切换范围和950查询接口限制。

## 查询API的模式、副作用及950冲突

[溢出状态API](../apis/torch_npu/overflow_state.md)保存普通Inf/NaN下FP32求和转Host、饱和下忽略grad并在查到溢出后清标志的区别。OpPlugin主线clear及npu_check_overflow产品页列950DT，但本指南所引环境页明确950不能做硬件状态查询；产品表和输入检查能力不消除此冲突，不提供950状态查询配方。FORCE的CANN>=9.1不回推CANN9.0发布实现。

## 旧状态Tensor接口单独消费

[alloc/get/clear_float_status](../apis/torch_npu/legacy_float_status.md)属于计划废弃且底层不维护的旧Tensor接口，不等同npu命名空间的现代溢出查询。V2/debug clear路径没有向返回result写零，get又有INT32新输出和返回self的分支；不要把返回值类型或全零样例当跨版本状态判断协议。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/INF_NAN_MODE_ENABLE.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/INF_NAN_MODE_FORCE_DISABLE.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/FORCE_OVERFLOW_CHECK.md)（constraint）

- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/appendixes/inf_nan_difference_apis.md)（constraint）

- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/appendixes/inf_nan_difference_apis.md)（constraint）

- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/op_execution/INF_NAN_MODE_ENABLE.md)（constraint）

- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/op_execution/INF_NAN_MODE_FORCE_DISABLE.md)（constraint）

- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/op_execution/FORCE_OVERFLOW_CHECK.md)（constraint）

- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-clear_npu_overflow_flag.md)（constraint）

- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-clear_npu_overflow_flag.md)（primary）

- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-clear_npu_overflow_flag.md)（constraint）

- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-get_npu_overflow_flag.md)（constraint）

- [固定来源 13](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-get_npu_overflow_flag.md)（primary）

- [固定来源 14](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-get_npu_overflow_flag.md)（constraint）

- [固定来源 15](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-utils-is_support_inf_nan.md)（constraint）

- [固定来源 16](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-utils-is_support_inf_nan.md)（primary）

- [固定来源 17](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-utils-is_support_inf_nan.md)（constraint）

- [固定来源 18](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-utils-npu_check_overflow.md)（constraint）

- [固定来源 19](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-utils-npu_check_overflow.md)（primary）

- [固定来源 20](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-utils-npu_check_overflow.md)（constraint）

- [固定来源 21](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/utils.py)（implementation）

- [固定来源 22](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/utils.py)（implementation）

- [固定来源 23](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_alloc_float_status.md)（constraint）

- [固定来源 24](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_alloc_float_status.md)（primary）

- [固定来源 25](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_alloc_float_status.md)（constraint）

- [固定来源 26](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_clear_float_status.md)（constraint）

- [固定来源 27](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_clear_float_status.md)（primary）

- [固定来源 28](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_clear_float_status.md)（constraint）

- [固定来源 29](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_get_float_status.md)（constraint）

- [固定来源 30](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_get_float_status.md)（primary）

- [固定来源 31](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_get_float_status.md)（constraint）

- [固定来源 32](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/FloatStatusKernelNpu.cpp)（implementation）

- [固定来源 33](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/FloatStatusKernelNpu.cpp)（implementation）


## FORCE_OVERFLOW_CHECK 的生效点与解析方式

生效点在**流创建**而非全局初始化：`AclrtCreateStreamWithConfig`（主线 AclInterface.cpp :202-253）在每条新流创建成功后决定是否 `AclrtSetStreamOverflowSwitch(stream, 1)`。环境读取是首次建流时的一次性静态求值（:223-237）：`std::getenv` 后 `strcmp(env, "1")`——只有精确字符串 "1" 视为开启，"01"、"true"、带空格的值都**静默当作未配置**（无告警无报错），与 OptionsManager 系「should be 0 or 1」的 TORCH_CHECK 校验风格不同；随后过 `IsGteCANNVersion("9.1.0")`，不满足时 ASCEND_LOGW 并忽略。

置开关的判定是 `!IsSupportInfNan() || forceOverflowCheck`（:238-241）：非 Inf/NaN 设备（IsSupportInfNan 为 false，见 NpuVariables.cpp :73-102 的 SoC 序判断）**每条流恒置 overflow switch=1，与该环境变量无关**——文档把开关描述为「非饱和模式下开启溢出检测」，实现上非饱和设备本来就常开，开关真正影响的是 Inf/NaN 模式设备。

发布差异（文档-实现配对）：发布快照 f3ecfe4a 的 csrc 全树零命中 `FORCE_OVERFLOW_CHECK`——发布实现完全不读取该变量，只剩 `!IsSupportInfNan()` 的常开分支（release AclInterface.cpp :212-213）。即该开关语义只存在于主线；发布版配置它是无告警空操作，排查时不能把发布版未检出溢出归因于此开关。

边界：同函数还有流失败模式副作用——TORCHINDUCTOR_NPU_BACKEND 取 mlir/default/triton_experimental 之一时流设 `ACL_CONTINUE_ON_FAILURE`，否则 `ACL_STOP_ON_FAILURE`（主线 :244-251）；发布版只认 mlir（release :215-221）。溢出开关与失败模式是同一建流点的两个独立设置，不互相推导。

## 补充来源

- [固定来源 34](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/interface/AclInterface.cpp)（primary）：:202-253。

- [固定来源 35](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/interface/AclInterface.cpp)（primary）：:191-221；负向证据：csrc 全树 rg FORCE_OVERFLOW_CHECK 零命中。

- [固定来源 36](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NpuVariables.cpp)（implementation）：:73-102。

- [固定来源 37](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NpuVariables.cpp)（implementation）：IsSupportInfNan 同构行段。

## INF_NAN 两键解析层与 A2/A3 拦截链

两键解析均为函数内 static lambda 一次性求值：`CheckInfNanModeEnable` 缺省 1、`CheckInfNanModeForceDisable` 缺省 0（主线 OptionsManager.cpp :156-165/:167-176），经 `GetBoolTypeOption`（:213-217）=`get_and_log_env`+`strtol`(base10)+`envFlag!=0?1:0`——**真值归一化而非 0/1 集合校验**：任何非零数值（含 "2"、"100"、"-5"）归一为 1，非数字串归一为 0；随后 map 查找 `{0,1}` 恒命中，"should be 0 or 1" 的 TORCH_CHECK 分支不可达。文档页「仅支持配置为 0 或 1」在实现层不成立：无告警、无拒绝，越界数值静默落入 0/1 语义；该文档与实现的偏差为静态核对结论，正负向均未运行验证。

消费链 `IsSupportInfNan`（主线 NpuVariables.cpp :74-103，扩展核对 :55-112）：Ascend950 及以上提前返回 true，两环境变量被忽略（:75-79 注释原文，对应文档「950 仅支持 INF_NAN 模式、不生效」）；`default_support_inf_nan` 一次性求值为 `[910B1, 310B1) ∪ [910_9391, ∞)`（:80-82）；`INF_NAN_MODE_ENABLE=0` 且设备默认支持且未配 `FORCE_DISABLE=1` 时 `AT_ERROR` "INF_NAN_MODE_ENABLE shouldn't be set to 0 on the current device. If you want to disable inf-nan mode, please export INF_NAN_MODE_FORCE_DISABLE=1"（:83-88，A2/A3 拦截的行级锚定）；`FORCE_DISABLE=1` 无条件返回 false——即使 `ENABLE` 保持默认 1 也切饱和（:91-93）；存在 `IsExistGetCannAttribute` 探针时以 `AclGetCannAttribute(ACL_CANN_ATTR_INF_NAN)` 一次性求值结果为准（:94-101），否则回落 default_support（:102）。旧 Atlas 产品 `ENABLE=1` 时最终由探针/default_support 给出假值（饱和），与文档「不生效」一致；静态口径不核对探针运行返回值。

发布差异：发布 `NpuVariables.cpp` :76-97 同构但**没有 950 提前返回层**（直入 default_support 判断）；发布 `OptionsManager.cpp` :86-112 同为 static lambda + `GetBoolTypeOption` 真值归一化（map 助手移至头文件），即归一化偏差两版同型。发布版对 950 的实际行为取决于其 SocVersion 枚举是否含该型号，未核发布枚举表，不外推。上一补充小节（FORCE_OVERFLOW_CHECK 建流点与 `!IsSupportInfNan()` 常开分支）已持消费侧；本节补解析与拦截层，不重述溢出开关语义。

## 补充来源

- [主线 OptionsManager.cpp @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionsManager.cpp)（implementation；:30-80、:120-176、:213-217）
- [发布 OptionsManager.cpp @f3ecfe4a](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/register/OptionsManager.cpp)（implementation；:86-112）

已列来源的扩展阅读窗（不新增条目）：主线 NpuVariables.cpp 增读 :55-112（含 :74-103 全函数）；发布版 NpuVariables.cpp 增读 :70-100。
