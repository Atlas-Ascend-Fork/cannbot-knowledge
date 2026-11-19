---
type: Guide
title: torch索引与统计：函数级类型和排序条件
description: 记录重复索引、isin单双Tensor、统计归约、950稳定排序及CPU回退限制。并含 cummax/cummin helper 的 aclnn 直发、kLong 分叉与 INT32 索引路径。
tags:
- task.optimization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/BincountKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/HistcKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/BincountKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/HistcKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/CummaxKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/CumminKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/CummaxKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/CumminKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/CummaxKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/CumminKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/CummaxKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/CumminKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h
  role: implementation
created_at: '2026-11-09T14:10:41Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# torch索引与统计：函数级类型和排序条件

## 固定来源与参数表的范围

依据TorchNPU主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的2.7.1、2.9至2.14中英文torch页；下表默认2.14，较早版本与实际收录语言另列。产品为A2/A3训练系列和950DT，不扩到950PR，不回推26.0/PyTorch2.8发布基线。

每行的input、dtype、tensors等是该条目的局部字段，不与Tensor方法的self表互换，不表示返回值或整个模型的数据类型。没有独立类型表、未收录语言/版本不等于已证实不支持；显式产品排除和额外条件另列。不借同名别名、父对象或相邻函数补齐参数、默认值与实现。这里仅静态核对，没有运行上游、编译、加载文件或进行设备实验。

## 函数级范围

已收录条目的产品表列三产品。torch.scatter_reduce只有产品表，不能将Tensor.scatter_reduce的A2/A3特定加速组合和全部950回退条件自动移植到这个函数。torch.less_equal的局部表明确含UINT16，le没有同样表，不因名称关系替换它们的范围。isin的两类场景在下节单列。
## 函数级参数类型

| 函数/对象 | 局部参数类型表 | 来源 |
| --- | --- | --- |
| `torch.nanmean`、`torch.norm`、`torch.var` | input=BF16/FP16/FP32 | 中英文 |
| `torch.mean` | input=BF16/FP16/FP32/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.argmax`、`torch.cumprod`、`torch.topk` | input=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64 | 中英文 |
| `torch.all`、`torch.allclose`、`torch.amax`、`torch.any`、`torch.argwhere`、`torch.cummin`、`torch.equal`、`torch.ge`、`torch.greater_equal`、`torch.isfinite`、`torch.sum`、`torch.unique` | input=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.diff`、`torch.isinf`、`torch.isnan`、`torch.scatter` | input=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.less_equal` | input=BF16/FP16/FP32/FP64/UINT8/UINT16/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.index_select` | input=BF16/FP16/FP32/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.max`、`torch.min` | input=BF16/FP16/FP32/INT64/BOOL | 中英文 |
| `torch.median`、`torch.msort` | input=BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64 | 中英文 |
| `torch.greater`、`torch.gt`、`torch.isneginf`、`torch.isposinf`、`torch.le`、`torch.less`、`torch.lt`、`torch.maximum`、`torch.minimum`、`torch.nansum` | input=BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.count_nonzero`、`torch.eq`、`torch.ne`、`torch.not_equal` | input=BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.histc` | input=FP16/FP32 | 中英文 |
| `torch.gather`、`torch.masked_select`、`torch.take` | input=FP16/FP32/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.kthvalue` | input=FP16/FP32/INT32 | 中英文 |
| `torch.index_add` | input=FP16/FP32/INT64/BOOL | 中英文 |
| `torch.argmin`、`torch.argsort`、`torch.bucketize`、`torch.sort` | input=FP16/FP32/UINT8/INT8/INT16/INT32/INT64 | 中英文 |
| `torch.amin`、`torch.aminmax`、`torch.cummax`、`torch.isclose`、`torch.logsumexp`、`torch.nonzero` | input=FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.cumsum`、`torch.prod` | input=FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.index_copy`、`torch.take_along_dim` | input=FP32 | 中英文 |
| `torch.bincount` | input=UINT8/INT8/INT16/INT32/INT64 | 中英文 |
| `torch.searchsorted` | sorted_sequence/values=FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64 | 中英文 |
| `torch.index_reduce`、`torch.nanquantile`、`torch.scatter_reduce`、`torch.std`、`torch.std_mean`、`torch.unique_consecutive`、`torch.var_mean` | 未给独立参数类型表 | 中英文 |
| `torch.isin` | 分场景类型表见正文 | 中英文；单/双Tensor分场景 |
| `torch.fmax`、`torch.fmin`、`torch.histogram`、`torch.isreal`、`torch.logcumsumexp`、`torch.masked_fill`、`torch.mode`、`torch.nanmedian`、`torch.quantile`、`torch.scatter_add`、`torch.unravel_index` | 未给独立参数类型表 | 仅中文 |

## 较早版本的不同参数表

| 函数/对象 | 文档版本 | 当时参数表 | 2.14参数表 | 来源 |
| --- | --- | --- | --- | --- |
| `torch.mean` | 2.10.0、2.7.1、2.9.0 | input=BF16/FP16/FP32/FP64/COMPLEX64/COMPLEX128 | input=BF16/FP16/FP32/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.argmin` | 2.10.0、2.7.1、2.9.0 | input=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64 | input=FP16/FP32/UINT8/INT8/INT16/INT32/INT64 | 中英文 |
| `torch.gt`、`torch.le`、`torch.lt`、`torch.maximum`、`torch.minimum` | 2.10.0、2.7.1、2.9.0 | input=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | input=BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.gather`、`torch.masked_select` | 2.10.0、2.7.1、2.9.0 | input=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | input=FP16/FP32/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.index_add` | 2.10.0、2.7.1、2.9.0 | input=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | input=FP16/FP32/INT64/BOOL | 中英文 |
| `torch.nonzero` | 2.10.0、2.7.1、2.9.0 | input=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | input=FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.eq`、`torch.ne` | 2.10.0、2.7.1、2.9.0 | input=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | input=BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.cumsum` | 2.10.0、2.7.1、2.9.0 | input=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | input=FP16/FP32/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.scatter_add` | 2.10.0、2.7.1、2.9.0 | input=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 未给独立参数类型表 | zh |
| `torch.index_select` | 2.10.0、2.7.1、2.9.0 | input=BF16/FP16/FP32/UINT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | input=BF16/FP16/FP32/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.sort` | 2.10.0、2.7.1、2.9.0 | input=BF16/FP16/FP32/UINT8/INT8/INT16/INT32/INT64 | input=FP16/FP32/UINT8/INT8/INT16/INT32/INT64 | 中英文 |
| `torch.scatter` | 2.10.0、2.7.1、2.9.0 | input=FP16/FP32/FP64/INT8/INT16/INT32/INT64/BOOL | input=BF16/FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL/COMPLEX64/COMPLEX128 | 中英文 |
| `torch.unique_consecutive` | 2.10.0、2.7.1、2.9.0 | input=FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | 未给独立参数类型表 | 中英文 |
| `torch.histc` | 2.10.0、2.7.1、2.9.0 | input=FP16/FP32/UINT8/INT8/INT16/INT32/INT64 | input=FP16/FP32 | 中英文 |

## 文档收录版本与语言

| 函数/对象 | 中文收录版本 | 英文收录版本 |
| --- | --- | --- |
| `torch.scatter_add` | 2.10.0、2.11.0、2.12.0、2.13.0、2.14.0、2.7.1、2.9.0 | 2.10.0、2.7.1、2.9.0 |
| `torch.fmax`、`torch.fmin`、`torch.histogram`、`torch.isreal`、`torch.logcumsumexp`、`torch.mode`、`torch.nanmedian`、`torch.quantile`、`torch.unravel_index` | 2.10.0、2.11.0、2.12.0、2.13.0、2.14.0、2.7.1、2.9.0 | 未收录 |
| `torch.masked_fill` | 2.13.0、2.14.0 | 未收录 |

## 索引与维度

gather要求index与input维度数一致；950DT在gather/index_select/scatter及scatter_add有重复索引时，可能与GPU及A2/A3存在精度差异。英文scatter_add只在较早三版本有独立条目和完整类型表，2.11至2.14把重复索引说明放在Math导言，不能因此说该说明或函数已消失。index_reduce/scatter可能CPU回退。

isin双Tensor输入时，elements/test_elements只列FP16/FP32、UINT8、INT8/16/32/64，第一个Tensor最多7维、第二个最多8维；单Tensor输入场景另加BF16/FP64，Tensor最多8维。保留场景区分，不将BOOL或任意复数加入任一集合。bincount的weights与input维度一致。

## 排序与统计结果

950DT的sort/argsort仅stable=True，False也强制改True；topk不支持sorted=False。不能用Tensor.topk的独立说明补造所有torch.topk的索引相等保证。

sum不支持dtype参数；unique带dim时不支持FP16，包含0的输入可能输出+0与-0。cummin的INT32输入数值范围为[-16777216,16777216]。histc输入在区间交界时归入左右区间可能有误差。norm当dim选到size为1的轴可能有精度误差；std可能CPU回退，950DT不支持double。

英文2.9/2.10/2.14提示norm弃用，向量/矩阵范数分别建议linalg.vector_norm/matrix_norm且参数不同；清单没有保证直接替换语义相同。不要把Tensor.nansum的950整数排除或Tensor.std的correction约束未经证据套到本页函数。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch.md)（constraint）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch.md)（primary）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch.md)（constraint）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch.md)（constraint）

## Bincount与Histc：范围推导会提取Host标量

两个固定OpPlugin版本的这组活动代码相同。模型内的计数/分布统计应同时计算输出申请和范围推导成本；本地出现item读取，但没有单独的EXEC_NPU_CMD_SYNC宏，不能仅据调用行数给出固定同步次数。

| 路线 | 准备、dtype与检查顺序 |
| --- | --- |
| Bincount，一维空输入 | 在普通兼容宏之后处理；minlength≤0申请{0} Long后直接返回，minlength>0申请{minlength} Long并执行SDK。两种都不根据weights改输出dtype，不能把非空weighted规则套到这里 |
| Bincount，其他输入 | 先min(self).item().toLong检查非负，再max(self).item().toLong决定长度：`max < minlength ? minlength : max+1`；按长度申请后调用aclnnBincount |
| Bincount非空输出类型 | 无weights为self options的Long；weights为Float时按weights options申请Float，否则申请Double。这里没有实际cast weights的语句，不能把“weight convert dtype”注释改写为已做输入转换 |
| Histc functional/out | 两者都先做相同范围helper，**然后**才执行普通兼容宏；functional按{bins}申请self dtype，out用self dtype及{bins}检查，不采用out自身dtype推导 |

Histc要求bins>0，先将min/max Scalar转double；二者相等且self非空时，分别self.min().item<double>()和self.max().item<double>()；仍相等就左右各扩1，再拒绝Inf/NaN并要求左<右。因此默认min=max=0并非固定零范围；空输入相等范围同样会扩展，但不先读Tensor min/max。有效且不相等的显式范围可避开这段Tensor读数，不代表SDK内部没有额外成本。

Bincount的非空分支错误文案含“一维非负整数”，但包装自身的这一步只检查提取出的最小值非负，没有因此完成所有rank/dtype/minlength合法性校验；溢出和完整权重要求仍由外部验证。Histc的范围推导发生在兼容选择之前，不能说回到旧ACL时已跳过Host读数。兼容分支缺符号还受普通DO_COMPATIBILITY的AclnnOnly限制，见[兼容门控](../../inference/guides/optimization/torch_npu/torch_npu_cpu_fallback_and_compatible_impl.md)。

以上保留原类型/精度支持页，并增加固定实现准备成本；未执行统计、Host提取或设备实验，不把分桶边界舍入或性能量化为本卡实测结果。

### Bincount与Histc补充证据

- [BincountKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/BincountKernelNpuOpApi.cpp)（implementation）：1–59。
- [HistcKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/HistcKernelNpuOpApi.cpp)（implementation）：1–74。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：1443–1445、2693–2699。
- [BincountKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/BincountKernelNpuOpApi.cpp)（implementation）：1–60。
- [HistcKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/HistcKernelNpuOpApi.cpp)（implementation）：1–74。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：1393–1395、2607–2613。


## Cummax与Cummin：helper直发、kLong分叉与INT32索引

上文“cummin的INT32输入数值范围为[-16777216,16777216]”的文档边界补上实现层机制。主线与发布两版本的yaml只登记`_cummax_helper`/`_cummin_helper`（acl_op+op_api all_version，主线与发布两版本均159–165、逐字相同）；`cummax.dim`/`cummin.dim`Schema在这两份yaml内rg零登记——该缺席限定在这两份OpPlugin YAML，ATen如何把cummax/cummin路由到helper未核对。aclnnCummax/aclnnCummin符号在主线与发布两版本全树仅见于对应手写op_api文件。

| 实际门槛→动作 | 失败/版本边界 |
| --- | --- |
| op_api手写helper（主线CummaxOpApi 23–29、CumminOpApi 23–28；主线与发布两版本整文件已读：与发布差异为排版+已识别的文件尾`// namespace op_api`注释，逻辑结构一致——去除该注释后去空白字符流等值）：`DO_COMPATIBILITY(aclnnCummax/aclnnCummin, acl_op::同名helper(...))`后`check_tensor({self}, values, values.scalar_type(), self.sizes())`与`check_tensor({self}, indices, indices.scalar_type(), self.sizes())`，单次`EXEC_NPU_CMD(aclnnCummax/aclnnCummin, self, dim, values, indices)` | 两个输出都以各自dtype与self.sizes()为参照；文件内无对indices dtype的显式TORCH_CHECK，check_tensor内部与aclnn侧最终约束未核对，不断言host层无其余检查。DO_COMPATIBILITY条件式：符号缺失且Aclnn-only模式抛错、否则ASCEND_LOGW后回退acl_op（主线op_api_common.h 94–119、发布96–110定向读） |
| acl_op _cummax_helper（主线22–32；主线与发布两版本去空白字符流相同）：values按self申请、indices直接按Long+ACL_FORMAT_ND申请，ACE命令"Cummax"（attr "dim"）后copy_回写两输出 | 无dtype分叉、无transpose分支；"Cummax"为host侧ACE命令名，不据此计device kernel |
| acl_op _cummin_helper（主线27–64；主线与发布两版本等值）：self为kLong走独立分支直接下发"Cummin"（attr "axis"）；非kLong且dim≠首轴（首轴由make_warp_dim(0,…)对常量0取wrap；输入dim原样用于perm[dim]与axis attr，本helper不规范化输入dim，ATen调用方的负轴归一化未核对）先单对换transpose（perm仅交换dim与0两轴）→"Cummin"→indices按at::kInt申请、经`_npu_dtype_cast`转Long→values/indices分别transpose回写；dim==首轴直接下发，indices同样Int→Long转写 | aicore分支的indices先按INT32产出再host侧转Long——可见的INT32索引路径（与知识库 npu_max/min INT32 索引结论同族，但不在同一文件核对）；kLong分支注释"process aicpu"、其余"process aicore"是host注释，不作device路由证明；npu_transpose/transpose_npu_output_size/_npu_dtype_cast内部未核对 |
| INT32数值边界[-16777216,16777216]的机制定位 | 实现层对INT32 self无任何显式值cast：非kLong分支self原样传给"Cummin"命令，kLong是唯一按dtype分叉的分支。但该±2^24成因不能由本层缺席定域——wrapper与device之间还有未核对的OpCommand/adapter/公共host转换路径，CANN侧Cummin内核亦未核对，成因留待下游核对、不归因于任一未核对层。cummax文档侧无同类INT32提示、文件内亦无对应cast，不互推 |

aclnnCummax/aclnnCummin与ACE"Cummax"/"Cummin"内核语义在CANN侧未核对；cummax的CPU回退提示属Tensor方法页（见[tensor方法范围](torch_npu_native_tensor_index_reduce_scope.md)），与本节helper路由不互推；静态口径，无运行验证。

### Cummax与Cummin补充证据

- [CummaxKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/CummaxKernelNpuOpApi.cpp)（primary）：1–31；完整本地小文件。
- [CumminKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/CumminKernelNpuOpApi.cpp)（primary）：1–30；完整本地小文件。
- [CummaxKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/CummaxKernelNpu.cpp)（implementation）：1–33；完整本地小文件。
- [CumminKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/CumminKernelNpu.cpp)（implementation）：1–65；完整本地小文件。
- [CummaxKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/CummaxKernelNpuOpApi.cpp)（implementation）：1–32；完整本地小文件；与主线差异为排版+已识别的文件尾`// namespace op_api`注释（去除该注释后去空白字符流等值，整文件diff -u核对）。
- [CumminKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/CumminKernelNpuOpApi.cpp)（implementation）：1–30；同上口径。
- [CummaxKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/CummaxKernelNpu.cpp)（implementation）：1–43；完整本地小文件，与主线去空白字符流相同（仅排版）。
- [CumminKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/CumminKernelNpu.cpp)（implementation）：1–68；同上口径。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：159–165；_cummax_helper/_cummin_helper两条目完整字段，其余注册行未核对。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：159–165；同口径，逐字相同。
- [op_api_common.h d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h)（implementation）：94–119；DO_COMPATIBILITY宏定义定向读。
- [op_api_common.h dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h)（implementation）：96–110；同口径，语义相同仅排版差异。
