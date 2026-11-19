---
type: Guide
title: Tensor索引与归约：重复索引、排序及CPU回退
description: 保留方法级dtype和版本变化，记录950排序稳定性、scatter_reduce加速条件及数值边界。
tags:
- task.optimization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-Tensor.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ScatterReduceKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-09T13:59:36Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# Tensor索引与归约：重复索引、排序及CPU回退

## 固定版本与表的读法

依据TorchNPU主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的2.7.1、2.9至2.14中英文Tensor支持页，以下默认展示2.14，较早版本的不同表另列。所列三产品指A2/A3训练系列与950DT，不包含950PR，不回推26.0/PyTorch2.8发布基线。

类型表只描述该方法的self，既不是返回值类型，也不是整个模型应转换成的类型。原文未给独立类型表、语言缺项或版本未收录均不等于已证实不支持；明确的产品排除和方法特有限制另列，优先于概括。FP16/FP32/FP64分别对应fp16/fp32/fp64；保留原文DOUBLE名称，不代填转换规则。本卡仅静态核对，未运行上游、编译或进行设备实验。

## 产品与基础类型

本表已收录方法的产品表列三产品，具体类型和附加限制仍各自适用。未给类型表的方法不从其他归约或索引方法推导。index_put/index_put_在本表self为INT64，不能把这误写成所有索引Tensor都只能INT64，也不能由scatter_add_支持更多类型扩展scatter_add。
## 方法级self类型

| 方法/属性 | self类型范围 | 来源 |
| --- | --- | --- |
| `torch.Tensor.std`、`torch.Tensor.var` | BF16/FP16/FP32 | 中英文 |
| `torch.Tensor.mean` | BF16/FP16/FP32/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.Tensor.argmax`、`torch.Tensor.topk` | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64 | 中英文 |
| `torch.Tensor.masked_scatter`、`torch.Tensor.scatter_add_`、`torch.Tensor.unique` | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.Tensor.sum` | BF16/FP16/FP32/INT32 | 中英文 |
| `torch.Tensor.max`、`torch.Tensor.min` | BF16/FP16/FP32/INT64/BOOL | 中英文 |
| `torch.Tensor.masked_fill_` | BF16/FP16/FP32/INT8/INT32/INT64/BOOL | 中英文 |
| `torch.Tensor.median` | BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64 | 中英文 |
| `torch.Tensor.all`、`torch.Tensor.argwhere`、`torch.Tensor.maximum`、`torch.Tensor.minimum`、`torch.Tensor.nansum` | BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.Tensor.count_nonzero` | BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.Tensor.histc`、`torch.Tensor.nanmean` | FP16/FP32 | 中英文 |
| `torch.Tensor.diff` | FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.Tensor.index_copy_`、`torch.Tensor.scatter`、`torch.Tensor.take` | FP16/FP32/INT16/INT32/BOOL | 中英文 |
| `torch.Tensor.index_select`、`torch.Tensor.take_along_dim` | FP16/FP32/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.Tensor.kthvalue` | FP16/FP32/INT32 | 中英文 |
| `torch.Tensor.index_fill` | FP16/FP32/INT32/BOOL | 中英文 |
| `torch.Tensor.index_fill_` | FP16/FP32/INT32/INT64/BOOL | 中英文 |
| `torch.Tensor.gather` | FP16/FP32/INT64 | 中英文 |
| `torch.Tensor.cumsum_`、`torch.Tensor.index_add_`、`torch.Tensor.masked_fill` | FP16/FP32/INT64/BOOL | 中英文 |
| `torch.Tensor.argmin`、`torch.Tensor.argsort`、`torch.Tensor.index_add`、`torch.Tensor.msort`、`torch.Tensor.sort` | FP16/FP32/UINT8/INT8/INT16/INT32/INT64 | 中英文 |
| `torch.Tensor.amax`、`torch.Tensor.amin`、`torch.Tensor.aminmax`、`torch.Tensor.any`、`torch.Tensor.cummax`、`torch.Tensor.cummin`、`torch.Tensor.logsumexp`、`torch.Tensor.nonzero` | FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.Tensor.cumsum`、`torch.Tensor.index_copy`、`torch.Tensor.prod`、`torch.Tensor.sum_to_size` | FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.Tensor.put_` | FP16/FP32/UINT8/INT8/INT16/INT32/INT64/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.Tensor.masked_select` | FP32/BOOL | 中英文 |
| `torch.Tensor.masked_scatter_` | FP32/INT64/BOOL | 中英文 |
| `torch.Tensor.scatter_add` | FP32 | 中英文 |
| `torch.Tensor.index_put`、`torch.Tensor.index_put_` | INT64 | 中英文 |
| `torch.Tensor.bincount` | UINT8/INT8/INT16/INT32/INT64 | 中英文 |
| `torch.Tensor.index_reduce`、`torch.Tensor.index_reduce_`、`torch.Tensor.mode`、`torch.Tensor.quantile`、`torch.Tensor.scatter_`、`torch.Tensor.scatter_reduce`、`torch.Tensor.unique_consecutive` | 未给独立self类型表 | 中英文 |
| `torch.Tensor.cumprod`、`torch.Tensor.cumprod_`、`torch.Tensor.histogram`、`torch.Tensor.logcumsumexp`、`torch.Tensor.nanmedian`、`torch.Tensor.scatter_reduce_` | 未给独立self类型表 | 仅中文 |

## 较早版本的不同类型表

| 方法 | 文档版本 | 当时self表 | 2.14 self表 | 来源 |
| --- | --- | --- | --- | --- |
| `torch.Tensor.mean` | 2.10.0、2.7.1、2.9.0 | BF16/FP16/FP32/FP64/COMPLEX64/COMPLEX128 | BF16/FP16/FP32/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.Tensor.argmin` | 2.10.0、2.7.1、2.9.0 | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64 | FP16/FP32/UINT8/INT8/INT16/INT32/INT64 | 中英文 |
| `torch.Tensor.sum` | 2.10.0、2.7.1、2.9.0 | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | BF16/FP16/FP32/INT32 | 中英文 |
| `torch.Tensor.all`、`torch.Tensor.maximum`、`torch.Tensor.minimum` | 2.10.0、2.7.1、2.9.0 | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.Tensor.gather` | 2.10.0、2.7.1、2.9.0 | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | FP16/FP32/INT64 | 中英文 |
| `torch.Tensor.index_add` | 2.10.0、2.7.1、2.9.0 | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | FP16/FP32/UINT8/INT8/INT16/INT32/INT64 | 中英文 |
| `torch.Tensor.any`、`torch.Tensor.nonzero` | 2.10.0、2.7.1、2.9.0 | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.Tensor.masked_select` | 2.10.0、2.7.1、2.9.0 | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | FP32/BOOL | 中英文 |
| `torch.Tensor.index_put` | 2.10.0、2.7.1、2.9.0 | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | INT64 | 中英文 |
| `torch.Tensor.index_select` | 2.10.0、2.7.1、2.9.0 | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | FP16/FP32/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.Tensor.cumsum` | 2.10.0、2.7.1、2.9.0 | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.Tensor.scatter_add` | 2.10.0、2.7.1、2.9.0 | BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | FP32 | 中英文 |
| `torch.Tensor.index_fill` | 2.10.0、2.7.1、2.9.0 | BF16/FP16/FP32/INT32/INT64/BOOL | FP16/FP32/INT32/BOOL | 中英文 |
| `torch.Tensor.masked_fill` | 2.10.0、2.7.1、2.9.0 | BF16/FP16/FP32/INT8/INT32/INT64/BOOL | FP16/FP32/INT64/BOOL | 中英文 |
| `torch.Tensor.sort` | 2.10.0、2.7.1、2.9.0 | BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64 | FP16/FP32/UINT8/INT8/INT16/INT32/INT64 | 中英文 |
| `torch.Tensor.scatter` | 2.10.0、2.7.1、2.9.0 | FP16/FP32/FP64/INT8/INT16/INT32/INT64/BOOL | FP16/FP32/INT16/INT32/BOOL | 中英文 |
| `torch.Tensor.unique_consecutive` | 2.10.0、2.7.1、2.9.0 | FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | 未给独立self类型表 | 中英文 |
| `torch.Tensor.histc` | 2.10.0、2.7.1、2.9.0 | FP16/FP32/UINT8/INT8/INT16/INT32/INT64 | FP16/FP32 | 中英文 |

## 索引、重复值和回退

bincount要求weights维度与输入维度相同，gather要求index与输入维度数相同。950DT对gather、index_put/index_put_、scatter/scatter_、scatter_add/scatter_add_提示重复索引会导致精度问题，不能把该提示改成任意重复写入次序保证。masked_scatter的950限制为mask中True数量不能超过source元素数，否则报错，来源称与GPU一致。

scatter_要求self/index/src非空且不是标量Tensor，并可能CPU回退。scatter_reduce只有A2/A3、including_self=True、reduce为sum或add且input为FP32的组合走NPU加速，A2/A3其他组合及全部950DT组合走CPU回退。来源参数拼作including_self，这里保留其文字，不据此生成可执行调用；实际签名需对应实现另核。该条件不自动套给只有产品表的scatter_reduce_。index_reduce/index_reduce_、cummax也可能CPU回退；select_scatter见[布局方法](../../inference/guides/optimization/torch_npu/torch_npu_native_tensor_layout.md)。

## 排序、统计和特殊数值

sort/argsort在950DT仅支持stable=True，传False也会强制True。topk仅支持sorted=True及非标量输入，输出indices可能与GPU/CPU不同，不能要求相同值的索引选择完全一致。

nonzero不支持NaN；median的BF16输入不能在size为1的轴上按dim归约。std不支持Scalar Tensor，std/var的correction不得大于INT32最大值。unique结果可能同时存在+0和-0。nansum通用self表含整数及BOOL，但950DT的局部说明排除它们，按产品条件消费。

这些限制会影响结果对齐和性能预期；没有实际测量前不宣称回退已消除、排序开销不变或归约误差已满足某个阈值。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-Tensor.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-Tensor.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-Tensor.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-Tensor.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-Tensor.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-Tensor.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-Tensor.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-Tensor.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-Tensor.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-Tensor.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-Tensor.md)（constraint）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-Tensor.md)（primary）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-Tensor.md)（constraint）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-Tensor.md)（constraint）

## ScatterReduce实际包装：out与普通入口有不同门控

主线OpPlugin实现给出比上面文档更具体的本地路由。以下只描述`d84e9b1...`包装，不把SoC枚举比较自动翻译成所有A2/A3/950产品支持认证，也不将普通入口条件套给out。

| 入口 | 本地选择与准备 |
| --- | --- |
| functional | 仅include_self真、reduce为sum/add、SoC枚举<Ascend950、self为Float时尝试SDK。先兼容探测，成功后self.clone(Contiguous)、CheckMemory，再以克隆同时作为输入和输出调用aclnnScatterReduce |
| inplace | 使用相同四项门控与独立aclnnInplaceScatterReduce兼容探测；CheckMemory后直接更新self，没有functional的显式clone |
| out | 没有前述四项门控；先探测aclnnScatterReduce，再CheckMemory、解析reduce并调用SDK，返回原out。不能由普通入口落CPU推断同参数out一定也落CPU |
| 上述CPU分支 | functional将self/index/src.cpu后执行CPU scatter_reduce，结果to(self.options)；out还将out.cpu，CPU out后copy回原out；inplace在self_cpu更新后copy回原self。没有本地强制Float转换 |

三处使用的是**DO_COMPATIBILITY_COMMON**：静态缓存SDK和GetWorkspaceSize地址；任一缺失则返回给定CPU表达式。宏虽静态读取IsAclnnOnly，却没有用该值作throw分支；这不同于普通DO_COMPATIBILITY。functional/inplace四项条件不满足也会直接CPU，不依赖缺符号触发。CPU执行/复制的失败由调用抛出，本地没有统一回滚。

本地reduce映射为none→0、sum/add→1、prod/mul→2、amax/max→3、amin/min→4、mean→5；未命中时报错。functional/inplace只有其SDK分支才经过此映射，其余由CPU接口处理原字符串；out直接走映射。这个表只证明包装接受并编码哪些名称，不保证每个SDK组合都能执行。

发布固定点中该精确CPP路径和本卡所查Schema均没有scatter_reduce条目；这是局部缺项证据，不能推导发布版本整个公开算子不可用或复制路线相同。现有文档与本地主线实现分别保留。未执行CPU/设备或性能实验。

### ScatterReduce补充证据

- [ScatterReduceKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ScatterReduceKernelNpuOpApi.cpp)（implementation）：1–162。
- [op_api_common.h d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h)（implementation）：121–136。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：4521–4528。
