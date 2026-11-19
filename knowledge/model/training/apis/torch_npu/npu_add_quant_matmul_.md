---
type: API
title: npu_add_quant_matmul_：950量化梯度原地累加
description: 说明FP8 MX与HiF8两类尺度、group_sizes固定组合和CANN 9.0入口检查。
tags:
- task.lookup
- topic.compute.quantization
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_add_quant_matmul_.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantBatchMatmulInplaceAddNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_add_quant_matmul_.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantBatchMatmulInplaceAddNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantBatchMatmulAddNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_quant_matmul_inplace_add.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantBatchMatmulAddNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_quant_matmul_inplace_add.py
  role: example
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/quant_matmul_inplace_add.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/quant_matmul_inplace_add.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_utils/check_platform.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/check_platform.py
  role: implementation
created_at: '2026-11-09T06:56:17Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- '950'
---

# npu_add_quant_matmul_：950量化梯度原地累加

## 固定版本与范围

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的完整产品分支、Schema与同提交C++/Meta。以下是文档和静态包装核对，未执行上游源码、编译图或设备实验，不回推发布基线。

## 接口

```text
npu_add_quant_matmul_(self, x1, x2, x2_scale, *,
    x1_scale=None, group_sizes=None, x1_dtype=None,
    x2_dtype=None, x1_scale_dtype=None, x2_scale_dtype=None)
    -> self
```

两个接口均用于950训练micro-batch梯度累加，self为FP32、Schema写入alias并返回self，Meta也返回输入缓冲。不要用未初始化Tensor当第一次累加基底，也不要把原地累加误当作自动清零的优化器更新。

MX路径x1/x2为FP8 E4M3FN或E5M2、scale为逻辑E8M0；HiF8路径使用hifloat8输入和FP32尺度。逻辑dtype参数是按位解释容器，不执行数值转换；明确指定E8M0/HiF8时仍须匹配8bit物理容器和shape，不能把FP32 Tensor直接通过逻辑dtype声明变成8bit数据。

## 单矩阵与量化粒度

self=(M,N)。产品页以x1=(K,M)、x2=(K,N)描述源布局；包装固定传两个transpose标志False，未提供Python转置开关。不能只按shape公式假定连续(K,M)的矩阵已经满足所有后端布局；替换原梯度乘法时须核对实际stride和算子约定。

MX尺度分别为(ceil(K/64),M,2)、(ceil(K/64),N,2)，每32元素一个E8M0值、尾维2配对；T-T HiF8路径两份FP32尺度均(1,)的pertensor。签名x1_scale虽可None，文档已列的两种计算组合都使用对应尺度，不能从None默认值推导缺失尺度自动为1。

group_sizes若非空必须恰3项[M粒度,N粒度,K粒度]：MX仅[1,1,32]、T-T仅[0,0,0]，0按输入/尺度推断。包装会把三项编码给底层，不代表任意三元组受支持。

包装要求aclnnQuantBatchMatmulInplaceAdd存在，错误信息指向CANN≥9.0；版本号最低门槛与实际运行库有对应符号均需核对。产品页支持单算子与TorchAir图模式，但输入mutation、原缓冲复用及跨微批同步仍须验证。

## 验证与关联

对照解码、矩阵乘、反量化再加到既有FP32 self的结果，连续执行两个不同micro-batch并检查alias与累计值。图使用不能只检查Meta返回self。

- [按专家K轴分组的量化累加](npu_add_quant_gmm_.md)
- [非量化分组累加](npu_grouped_matmul_add_.md)

## 双语形状、公式与图样例的边界

主线双语及两张公式图均确认950PR/DT训练。MX按K轴32元素块分别乘两份尺度后累加到原有self，T-T则对完整点积乘两份标量尺度再累加。一般参数段把scale写三维，T-T专门表格和例子却是一维(1,)，须按具体模式解释，不能用一般段覆盖细分组合。

参数表把x1写为(K,M)，示例实际先生成(K,M)再transpose成(M,K)视图，左尺度也由(ceil(K/64),M,2)转成(M,ceil(K/64),2)。包装没有Python转置开关且两个底层transpose标志固定False，不能同时照抄源shape与转换后shape而重复转置。最终以目标运行库的实际stride及编码口径核对。

MX图样例没有显式传公开限定的[1,1,32]；两版C++在group_sizes=None或空列表时编码0，不自行证明它与显式MX配置完全等价。内部编码helper只检查非空时三项，没有GE helper的非负和65535上界检查，通用签名不扩大公开模式范围。

## 原地副作用与发布图转换差异

两版原地C++和Meta直接返回self；对应非原地C++先clone再把副本交底层。主线GE非原地转换器也先TensorMove并使用副本，但发布GE同分支虽创建y_copy，实际仍把原y传给InplaceAdd。这是功能化或输入保留需要核对的固定版本差异，不能把所有非原地内部路径都视为已保护原缓冲。

原地GE两版都调用dont_prune_me标记结果；逻辑dtype使用Bitcast及GE描述更新，不能把它当作数值量化。平台helper门控与公开产品表分别保留，主线额外识别的设备名字不扩充产品支持。

两版测试均有未定义的小写k、y1/y2及对NumPy数组调用clone.npu等问题，还把尺度类型误用于数据逻辑dtype，未形成有效可执行参考。测试未skip也不能计作数值或连续微批覆盖。C++对入口符号的缓存检查及错误提示CANN≥9.0独立于这些无效测试。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_add_quant_matmul_.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantBatchMatmulInplaceAddNpuOpApi.cpp)（implementation）

- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_add_quant_matmul_.md)（constraint）

- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantBatchMatmulInplaceAddNpuOpApi.cpp)（implementation）

- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantBatchMatmulAddNpuOpApi.cpp)（implementation）

- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_quant_matmul_inplace_add.py)（example）

- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantBatchMatmulAddNpuOpApi.cpp)（implementation）

- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_quant_matmul_inplace_add.py)（example）

- [固定来源 13](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/quant_matmul_inplace_add.py)（implementation）

- [固定来源 14](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/quant_matmul_inplace_add.py)（implementation）

- [固定来源 15](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_utils/check_platform.py)（implementation）

- [固定来源 16](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/check_platform.py)（implementation）
