---
type: API
title: 确定性未初始化内存填充：NPU显式启用
description: 记录fill_uninitialized_memory属性默认值与NPU实际填充条件，区分算子确定性、随机状态和HF32。
tags:
- task.lookup
- topic.precision
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-utils-deterministic.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-utils-deterministic.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-utils-deterministic.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-utils-deterministic.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-utils-deterministic.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-utils-deterministic.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-utils-deterministic.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-utils-deterministic.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-utils-deterministic.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-utils-deterministic.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-utils-deterministic.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-utils-deterministic.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-utils-deterministic.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-utils-deterministic.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_deterministic.py
  role: implementation
created_at: '2026-11-09T13:42:39Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# 确定性未初始化内存填充：NPU显式启用

## 固定版本与范围

依据TorchNPU主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的固定原生支持页，具体文档版本与中英文范围分别保留；未收录不等于已证实不支持，不据支持清单补造参数、默认值或完整实现。产品为所列A2/A3训练系列与950DT，不扩展950PR，不回推26.0/PyTorch2.8发布基线。本卡未执行上游、编译、导出、训练或设备实验。

## 接口与逐版本声明

公开属性为torch.utils.deterministic.fill_uninitialized_memory，中英文七版本均列A2/A3训练系列和950DT；来源给默认值True，但明确TorchNPU在use_deterministic_algorithms开启确定性后默认不执行对应未初始化内存填充，需要手动把该属性设为True才生效。属性默认显示值与实际默认执行行为分别记录。

这不是在此环境执行过的赋值或填充实验，也不证明任何实际包、任意分配路线和图后端组合均已验证。来源未给完整dtype、填充值、写入范围、线程/进程和缓存时机协议，不自行补齐。

## 与其他精度机制的边界

填充未初始化内存不替代算子确定性、随机数状态或通信顺序，不把不支持确定性的算法变成支持；HF32允许精度策略与此属性也分别控制。应记录真实版本、是否开启确定性、显式属性设置、分配/消费路径和参考数值，再检查行为和开销，不只读取一个布尔值便认定全部训练可复现。

- [HF32与精度开关](../../guides/torch_npu_precision_switches_and_deterministic_fill.md)
- [随机状态命名空间](../../../inference/guides/optimization/torch_npu/torch_npu_native_rng_state_scope.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-utils-deterministic.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-utils-deterministic.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-utils-deterministic.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-utils-deterministic.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-utils-deterministic.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-utils-deterministic.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-utils-deterministic.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-utils-deterministic.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-utils-deterministic.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-utils-deterministic.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-utils-deterministic.md)（constraint）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-utils-deterministic.md)（primary）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-utils-deterministic.md)（constraint）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-utils-deterministic.md)（constraint）

## 属性设置的 NPU 同步补丁

主线 `torch_npu/utils/_deterministic.py` 的 `_add_deterministic_patch()` 把 `torch.utils.deterministic.fill_uninitialized_memory` 的属性 setter 包装为两步：先调用上游原 setter（`torch._C._set_deterministic_fill_uninitialized_memory`），再调 `torch_npu._C._npu_set_fill_uninitialized_memory(mode)` 同步 NPU 侧选项（:19-24，文件头注释同述）。因此在该补丁生效的环境里，对该属性赋值会同时翻转 NPU 侧开关，"设 True 才生效"即走这条链；单独改 `torch._C` 内部入口不会同步 NPU 侧。补丁针对 `sys.modules` 的 `_Deterministic` 类替换 property（上游把模块实例类换为 `_Deterministic`），依赖该上游结构，未逐行核对其装载时机（import torch_npu 的补丁组）与发布版本 形态。

## 补充来源

- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_deterministic.py)（implementation）：全文 1-24。
