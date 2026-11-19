---
type: Guide
title: 自动预编译缓存：序列化、Guard 放宽与正确性边界
description: 说明 TORCH_CACHING_PRECOMPILE 的自动加载保存及不可序列化 Guard 过滤，不与 GE 函数缓存混同。
tags:
- task.implementation
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/TORCH_CACHING_PRECOMPILE.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/TORCH_CACHING_PRECOMPILE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/megacache/overview.md
  role: primary
created_at: '2026-11-09T06:01:51Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# 自动预编译缓存：序列化、Guard 放宽与正确性边界

## 固定版本与证据

依据 PyTorch/TorchNPU 固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的环境变量文档，按所列产品和选项限制使用，不推导发布组合具备全部功能。只读来源审阅，未运行上游代码或设备实验。

## 实验开关与缓存层

TORCH_CACHING_PRECOMPILE 默认 0，1 开启，进程启动前配置，运行中修改无效。torch.compile 自动查找 DynamoCache，编译后保存 Dynamo 条目与后端产物，例如 AOTAutograd cache；save_cache_artifacts 也包含 PrecompileContext 条目，可与 load_cache_artifacts 配合。

## 放宽 Guard 的代价

为支持跨进程序列化，会过滤不能序列化的 Guard，包括 ID_MATCH、CLOSURE_MATCH、WEAKREF_ALIVE、DICT_VERSION。缓存命中条件因此可能放宽，不能把成功加载当作源码、闭包和对象状态均已完全一致。

跨进程复用是此工具的设计目标，并不覆盖其他后端的临时回调限制；例如 GE 零交付件产物仍要求同进程，不能用本变量消除该限制。对实际后端、版本、模型状态及输入域检查缓存复用是否合法，并核对输出。

分别记录无缓存首次编译、命中后启动与稳态耗时，变更模型/闭包/状态后重新确认正确性。这不是 torchair.inference.cache_compile 的等价替代接口。


## 核验

保存解释器、包版本、设备、完整配置及首次生效时机，在新进程中做单项对照。检查数值与实际路径，再分别比较首次启动、稳态时间和资源开销；调试配置关闭后复测。

## MegaCache打包不等于Guard或CppWrapper全兼容

同提交内部MegaCache说明仅列950DT，将PRECOMPILE、PGO、AOT_AUTOGRAD、INDUCTOR、AUTOTUNE统一导出，PRECOMPILE仍需本卡实验开关。save_cache_artifacts无可导出时可能None，有数据返回bytes和CacheInfo；load恢复后仍须正常compile查询，硬件型号与软件编译环境一致是跨机复用前提，不是加载即可证明命中。

该页暂不支持CppWrapper制品打包；动态shape、Catlass缓存支持不扩大此限制，也不消除本卡Guard过滤的正确性边界。详细返回值和产物范围见[MegaCache API](../../../apis/torch_npu/megacache_artifacts.md)，本卡其他产品的预编译入口支持不被用于扩大950DT MegaCache页的范围。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/TORCH_CACHING_PRECOMPILE.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/TORCH_CACHING_PRECOMPILE.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/megacache/overview.md)（primary）
