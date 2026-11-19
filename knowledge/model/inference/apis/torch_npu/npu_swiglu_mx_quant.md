---
type: API
title: npu_swiglu_mx_quant：950门控模式与MXFP4/8分组
description: 说明四种门控顺序、FP4物理打包、分组尺度容量和预留算法，区分count与cumsum编号。
tags:
- task.lookup
- topic.compute.quantization
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_swiglu_mx_quant.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/models/modeling_glm.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_swiglu_mx_quant.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/SwigluMxQuantOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SwigluMxQuantOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_swiglu_mx_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_swiglu_mx_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-09T01:56:57Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- '950'
---

# npu_swiglu_mx_quant：950门控模式与MXFP4/8分组

## 版本与范围

本文依据 `ascend_main_candidate` 中 OpPlugin 的固定主线提交；该候选的软件配套尚未确认。不能据此推定 26.0.0 发布组合支持此接口或下列参数。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_swiglu_mx_quant(x, *, group_index=None, activate_dim=-1, activate_left=False, swiglu_mode=0, clamp_limit=7.0, glu_alpha=1.702, glu_bias=1.0, group_mode=0, axis=-1, dst_type=296, round_mode="rint", scale_alg=0, max_dtype_value=0) -> (Tensor, Tensor)
```

本卡覆盖FP4/FP8的SwiGLU与MX量化，返回(y,mxscale)；count路线与仍有文字冲突的cumsum路线分别限定。swiglu_mode=0 是普通前后切分；1 为奇偶切分、先截断再激活的变体；2 同变体但前后切分；3 前后切分、先激活再截断且不使用 glu_alpha/glu_bias。

## 参数与组合限制

- x 为 2–7 维 FP16/BF16 ND，被 activate_dim 切分的轴必须为偶数。activate_dim 和 axis 只支持尾轴或倒数第二轴及其正索引。
- 非尾轴激活只支持 swiglu_mode=0；mode=2/3 时量化 axis 必须为 -1。clamp_limit 必须为有限正数。
- FP8 输出只允许 rint，scale_alg∈{0,1}；scale_alg=2 和 max_dtype_value 在此接口为预留能力，不能照搬独立 dynamic_mx_quant 的已支持算法 2。
- group_index 为 1–256 组的一维 INT64；在 count 路线各项>0、总和不超过 x 的非尾轴元素乘积。带分组且任一操作轴非尾轴时，x 必须为二维；超出分组有效 token 区的 y/scale 未清理。
- 来源同时给 group_mode=1 的 cumsum 名称，却在统一约束中仍要求元素求和不越界；累计边界路线需核对实际实现，本卡不把 count 的有效区计算无条件套入。
- FP4的逻辑激活尾维须偶数，两版包装/Meta/GE明确再沿物理尾轴缩2倍并用UINT8承载，详细形状见下文；不混用INT8反量化融合接口的容器。

## 验证与模型关联

按所选激活模式构造参考，检查门控两半、截断时机、FP8 误差和有效 token 区；下游按该接口的 E8M0 表示核对 scale，不能当普通 FP32。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/models/modeling_glm.py#L116)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## 完整FP4形状与两版包装

主线中英文仅950PR及DT推理。设S为输入x在activate_dim轴减半后的逻辑激活形状，FP8物理y就是S；FP4还要求S的最后一维为偶数，再以UINT8把物理尾维除2。尾轴激活时原输入尾长必须被4整除，结果物理尾长是原来的1/4；即使量化轴或激活轴非尾轴，打包仍沿物理尾轴。两固定包装、Meta和GE转换器共同确认，不能再只按公开逻辑y形状理解字节容器。

两固定包装与Meta分配的scale是UINT8承载E8M0：先取S，量化轴改为ceil(S[axis]/64)，再追加尾维2；若有group且量化轴非尾轴，则该轴为floor(S[axis]/64)+G。源码注释写ceil，但实际表达式是floor，不能照注释改动容量。配对维2对应32元素尺度的成对存储，不是将量化块大小改为64。分组容量不等于每槽有效，实际边界值没有由此shape计算验证。

发布包装只接受swiglu_mode=0/1，主线才接受0..3；两版都要求clamp有限正数、glu_alpha/glu_bias有限，并缓存底层符号、缺失即提示升级。公开模式0/2/3的前后切分与模式1的奇偶切分分开；模式1忽略activate_left的普通左右含义，模式3也不使用alpha/bias。scale_alg=2与max_dtype_value仍预留，C++透传不代表公开启用。

group_mode=0是count、1是cumsum，与npu_swiglu_quant的group_list_type编号相反。公开统一求和限制与cumsum含义仍有冲突，包装/Meta只用组数量算容量，没有检查边界值，不把count的有效区规则无条件套给累计边界。group存在且任一操作轴非尾轴时仅二维，非尾轴激活只模式0，模式2/3的axis只-1。两个GE Converter保留E8M0描述并把FP4重打包，但存在转换器不表示所有组合已运行。

中英文例子主动传glu_alpha=1.0、glu_bias=1.702，区别于默认1.702/1.0，不把它当文档笔误自动交换参数。固定发布已有实现而无同名公开页，不回填发布产品支持。

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_swiglu_mx_quant.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_swiglu_mx_quant.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/SwigluMxQuantOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SwigluMxQuantOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_swiglu_mx_quant.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_swiglu_mx_quant.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
