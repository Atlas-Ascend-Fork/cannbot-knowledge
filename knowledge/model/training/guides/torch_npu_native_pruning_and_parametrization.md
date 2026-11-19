---
type: Guide
title: 原生剪枝与参数化：方法限制和950DT差异
description: 区分随机剪枝类与函数的产品表、mask和weight数据角色、参数化正交入口与真实稀疏执行边界。并含 aten::_weight_norm 本地包装的同设备守卫与纯 aten 组合。
tags:
- task.optimization
- topic.precision
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-nn.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/WeightNormKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/WeightNormKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-09T12:17:09Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
- '950'
---

# 原生剪枝与参数化：方法限制和950DT差异

## 固定版本与范围

依据TorchNPU固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的PyTorch2.7.1、2.9至2.14支持页及完整子方法，产品按A2/A3训练系列与950DT逐项记录，不扩展950PR或发布组合。文档版本差异不直接证明发行历史或实际包回归。上游“已验证产品”属于清单口径，本卡仅静态审阅，未执行上游、NPU或性能实验。

先区分接口产品表、权重/Mask、注册的参数化以及真正执行Kernel；剪枝支持不直接证明模型变小、权重释放或底层采用稀疏加速。

## 随机非结构化剪枝的冲突范围

RandomUnstructured类在七版本列三类产品支持，input列FP32；但apply/apply_mask/prune/remove子方法的950DT行均为不支持。functional random_unstructured却又列950DT支持。保留类、方法、函数三个层次，不能把函数条目当作已经验证的绕过方案，也不能将类支持直接提升到完整流程。

## 其他剪枝与数据角色

L1Unstructured、LnStructured、RandomStructured类input列FP32；L1Unstructured各列出方法、LnStructured的apply/apply_mask/compute_mask/prune/remove、RandomStructured的apply/apply_mask/compute_mask等self条目也列FP32。BasePruningMethod的apply_mask/prune/remove、PruningContainer的compute_mask/prune/remove有相同self条目。

CustomFromMask类及apply和custom_from_mask函数把input/self列为INT64，不能据此将被剪权重全转整数，或自行推导任意浮点Mask/参数的组合合同。中文Identity类没有独立产品表，但其apply/apply_mask/prune/remove有三类产品与FP32条目；子方法范围不替代缺失的类级规格。

identity、l1_unstructured、random_structured、ln_structured、global_unstructured、remove、is_pruned及部分apply/compute_mask等仅列产品，未提供完整dtype/shape/反向细表；不把不同类的宽类型或参数并入。类级支持不免除子方法的具体限制。

## 参数化与正交入口

旧式weight_norm/spectral_norm及各自remove入口，parametrizations.weight_norm/spectral_norm，parametrize的register_parametrization/remove_parametrizations/cached/is_parametrized与ParametrizationList均列三类产品。ParametrizationList.right_inverse另列self仅FP32。

中文parametrizations.orthogonal在A2/A3条件段，只列这两类产品，未列950；不能从另外两种参数化补齐它的产品范围。skip_init也只列产品，不据名称推定所有初始化、存储分配或启动开销都已被消除。

## 验证边界

对实际版本检查参数、Mask、梯度、序列化/恢复与注册/移除后的结果；再核对执行图和Kernel，比较端到端耗时和内存。没有本地稀疏性能观测，不把更多零值或支持清单写成收益承诺。

## 英文类表与参数化弃用说明

中文prune.Identity没有独立类级产品表，英文七版本则明确A2/A3支持、950DT不支持；其apply/apply_mask/prune/remove仍列三类产品。类/子方法的不一致保留，不能由方法表补齐完整Identity流程。parametrizations.orthogonal的中文页只列A2/A3，英文七版本明确950DT不支持，其他参数化的950支持不覆盖它。

英文2.9/2.10/2.14对旧weight_norm提示已弃用，改用parametrizations.weight_norm，并指向参数访问/移除迁移说明；其余英文版本和中文未重复。新旧注册、参数访问、序列化及remove协议需分别核对，不把重命名当作已验证的无损替换。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-nn.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-nn.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-nn.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-nn.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-nn.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-nn.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-nn.md)（primary）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-nn.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-nn.md)（constraint）

## aten::_weight_norm 本地包装：同设备守卫与纯 aten 组合

『参数化与正交入口』的产品表只说明注册面；本节补入底层 aten 入口的本地包装事实。aten::_weight_norm（Schema `int dim=0`）在主线与发布两版本 均由 opapi 目录下的手写包装实现（WeightNormKernelNpuOpApi.cpp，主线 25 行、发布 26 行，去空白字符流相同，仅排版）：op_api 命名空间内只有 `const int DIMENSION_2D = 2` 与 `_weight_norm(v_in, g_in, dim)` 一个函数。

| 环节 | 实际门槛与动作 | 失败/版本边界 |
| --- | --- | --- |
| 入口守卫 | `TORCH_CHECK(v_in.device() == g_in.device())`，原文文案 "weight_norm: expected v_in and g_in to be on the same device, but v_in is on <v_in设备> and g_in is on <g_in设备>"（ErrCode::PARAM） | 设备类型或卡号不一致（含 NPU/CPU 混用）直接抛出；本地包装内没有设备迁移、CPU 回退，也无显式格式分支或 format cast |
| 输入整理 | `auto v = v_in.contiguous(); auto g = g_in.contiguous();` | 已连续输入 contiguous() 原样返回，非连续输入先经 aten 整理；本地包装内无显式 format cast 或格式专用分支，contiguous() 的后端实现未核对，不依据该可移植 API 名称排除后端的格式准备工作 |
| 计算组合 | `return v * g.div(at::norm_except_dim(v, 2, dim));` | mul/div/norm_except_dim 是对相应 ATen 算子的委托，下游后端选择/回退/融合未核对，不构成全 NPU 执行保证；本地包装内无显式 CPU 拷贝、无 aclnn 调用、无融合 kernel 调用，传递行为未知；耗时与精度特征由被组合的算子决定 |
| 登记 | yaml 主线 776–778、发布 751–753：仅 `op_api: all_version` + `internal_format_opapi: all_version`，无 acl_op 条目 | 没有 DO_COMPATIBILITY 回退目标；internal_format_opapi 登记在本地包装源内未见兑现（无显式格式转换或格式专用分支），不据此排除后端路径的格式准备工作（未核对） |

`dim` 的越界/负值行为由 norm_except_dim 的 ATen 语义承担，未核对其实现。英文页对旧 weight_norm 的弃用与迁移提示（见『英文类表与参数化弃用说明』）不受本节影响：包装事实既不证明新旧参数化入口等价，也不构成数值或性能结论。未运行、未度量。

### _weight_norm 补充证据

- [WeightNormKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/WeightNormKernelNpuOpApi.cpp)（implementation）：1–25；完整本地小文件。
- [WeightNormKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/WeightNormKernelNpuOpApi.cpp)（implementation）：1–26；完整本地小文件，与主线去空白字符流相同（仅排版）。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：776–778；仅 _weight_norm 一条完整条目。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：751–753；仅 _weight_norm 一条完整条目。
