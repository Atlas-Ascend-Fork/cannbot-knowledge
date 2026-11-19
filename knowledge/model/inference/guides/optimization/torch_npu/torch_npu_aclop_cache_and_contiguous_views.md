---
type: Guide
title: TorchNPU ACL Op 路线：编译缓存与组合连续化
description: 区分单算子编译磁盘缓存、aclop view 连续化和 GE/捕获图缓存的不同生效范围。
tags:
- task.optimization
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_compilation/ACL_OP_COMPILER_CACHE_MODE.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_compilation/ACL_OP_COMPILER_CACHE_DIR.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/COMBINED_ENABLE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/op_compilation/ACL_OP_COMPILER_CACHE_MODE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/op_compilation/ACL_OP_COMPILER_CACHE_DIR.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/op_execution/COMBINED_ENABLE.md
  role: constraint
created_at: '2026-11-09T06:01:51Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# TorchNPU ACL Op 路线：编译缓存与组合连续化

## 固定版本与证据

依据 PyTorch/TorchNPU 固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的环境变量文档，按所列产品和选项限制使用，不推导发布组合具备全部功能。只读来源审阅，未运行上游代码或设备实验。

## 单算子编译缓存

ACL_OP_COMPILER_CACHE_MODE 默认 enable，相同编译与算子参数复用缓存；disable 关闭，force 强制刷新，Python 或依赖发生变化时按实际部署核对是否需要刷新。仅单算子模式支持，不能用于 GE 图或 npugraph_ex 模型缓存。

ACL_OP_COMPILER_CACHE_DIR 的路径优先级为该变量 > ASCEND_CACHE_PATH > 用户目录下 atc_data；两项若同时由 torch_npu_option 在代码中指定，则代码配置优先。设置 ACL_OP_DEBUG_LEVEL 时，仅值 0 或 3 启用该编译缓存，其他值禁用；目录存在不证明编译时命中。

## 非连续 view 的优化

COMBINED_ENABLE 默认 0，进程启动前设 1 开启，严格支持 0/1。针对最多两个组合 view（例如 reshape+slice、permute+select）的连续化，按 view 信息栈减少完整拷贝，仅在 **aclop** 连续化路径生效；aclnn 算子不经过此优化。它不让任意非连续 Tensor 变成无拷贝，也不改变数值或别名契约。

分别确认算子执行路线、缓存日志与实际内存搬运，再比较冷启动和稳态；不能把两个不同层次的优化开关当作统一的图缓存选项。


## 核验

保存解释器、包版本、设备、完整配置及首次生效时机，在新进程中做单项对照。检查数值与实际路径，再分别比较首次启动、稳态时间和资源开销；调试配置关闭后复测。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_compilation/ACL_OP_COMPILER_CACHE_MODE.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_compilation/ACL_OP_COMPILER_CACHE_DIR.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/COMBINED_ENABLE.md)（constraint）

- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/op_compilation/ACL_OP_COMPILER_CACHE_MODE.md)（constraint）

- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/op_compilation/ACL_OP_COMPILER_CACHE_DIR.md)（constraint）

- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/op_execution/COMBINED_ENABLE.md)（constraint）
