---
type: API
title: npu_add_quant_gmm_：分组量化梯度和尺度容量
description: 说明K轴累计边界/计数、未更新区域、组间MX尺度pad和group_sizes只能None。
tags:
- task.lookup
- topic.compute.quantization
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_add_quant_gmm_.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantGroupedMatmulInplaceAddNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_add_quant_gmm_.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantGroupedMatmulInplaceAddNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantGroupedMatmulAddNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_quant_grouped_matmul_inplace_add.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantGroupedMatmulAddNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_quant_grouped_matmul_inplace_add.py
  role: example
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/quant_grouped_matmul_inplace_add.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/quant_grouped_matmul_inplace_add.py
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

# npu_add_quant_gmm_：分组量化梯度和尺度容量

## 固定版本与范围

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的完整产品分支、Schema与同提交C++/Meta。以下是文档和静态包装核对，未执行上游源码、编译图或设备实验，不回推发布基线。

## 接口

```text
npu_add_quant_gmm_(self, x1, x2, x2_scale, group_list, *,
    x1_scale=None, group_list_type=0, group_sizes=None,
    x1_dtype=None, x2_dtype=None, x1_scale_dtype=None,
    x2_scale_dtype=None) -> self
```

两个接口均用于950训练micro-batch梯度累加，self为FP32、Schema写入alias并返回self，Meta也返回输入缓冲。不要用未初始化Tensor当第一次累加基底，也不要把原地累加误当作自动清零的优化器更新。

MX路径x1/x2为FP8 E4M3FN或E5M2、scale为逻辑E8M0；HiF8路径使用hifloat8输入和FP32尺度。逻辑dtype参数是按位解释容器，不执行数值转换；明确指定E8M0/HiF8时仍须匹配8bit物理容器和shape，不能把FP32 Tensor直接通过逻辑dtype声明变成8bit数据。

## 分组不是量化块大小

self=(g,M,N)，x1/x2产品布局(K,M)/(K,N)，沿K分组。group_list为INT64(g,)，g=1..1024；group_list_type=0是非负非递减累计边界，1是每组非负计数，末值/总和不超过K。未指定的有效区域不参与更新，不能假设一次调用覆盖并清空整个self。

M/N/K要求正且≤INT32_MAX；作为输入最内轴时小于2097152。group_sizes在本接口**只能None**，C++和Meta均拒绝显式提供；不继承[npu_add_quant_matmul_](npu_add_quant_matmul_.md)可传三元组的规则。

## 尺度与运行入口

HiF8 T-T/T-C：x1_scale为(g,)或(g,1)，x2_scale可(g,)/(g,1)的pertensor或(g,N)的perchannel。MX：x1_scale物理容量(K//64+g,M,2)，x2_scale为(K//64+g,N,2)，组边界独立pad；分配容量不等于每个槽都有效，不能按全局K无分组的尺度布局替换。

包装探测aclnnQuantGroupedMatmulInplaceAdd，不存在直接拒绝并要求升级，未给出可推定的最低CANN精确版本。实际原地实现直接传self并返回self；另一个无下划线实现会先clone，不混淆两者的显存和alias。

产品页列950训练、单算子和TorchAir图模式。显式逻辑x dtype只HiF8，显式scale dtype只E8M0，其他类型不能由宽签名推导。检查每个group的累加和未更新区域，并用含空组、非满32块的参考验证尺度pad。

## 两版实现、Meta筛选和容量含义

主线两份公开页均为950PR/DT训练、单算子与TorchAir图模式；发布有包装及转换器不推定发布公开产品契约。两版C++明确拒绝任何显式group_sizes，包括空列表。GE转换器没有消费该参数，不表示可绕过公开及Meta/C++的None约束。

主线Meta比发布增加非空M/N时K必须为正的检查，M取x1.shape[0]、N/K取x2对应轴；它仍没有完整验证self、group_list及所有尺度容量，返回self的shape并非合法输入的完整证明。

MX公式允许各组末尾不足32的块，公开额外g的尺度容量也不等于所有位置有效。本卡只核对应用消费约定，没有读取下层内核的全部尺度打包实现，不据(K//64+g)手工构造一个通用组间偏移协议。参数表的x1源布局与例子转置后视图也应分开。

## 函数式副本、图副作用和测试缺口

两版非原地量化C++都先clone self后更新；两固定GE非原地转换器也TensorMove后使用副本。原地路径直接使用原y并标记dont_prune_me，逻辑dtype的Bitcast不执行数值转换。该消费语义与非量化GroupedMatmulAdd的“更新原self后clone”实现不同，不能按函数名统一估计副作用和显存。

两版量化GMM测试的NumPy数组被当作有clone.npu方法的Tensor，并引用未定义y1/y2，输入dtype/shape也未形成公开HiF8或MX配套。不能把这些未skip的测试计为真实数值、group_list_type=1、空组或部分K块的覆盖；符号探测要求升级CANN也没有给出可由此反推的最低精确版本。

主线样例用不等长组及累计边界展示调用，并不自动证明所有尺度pad槽的内容。实际验收应同时检查各组累计量、未指定区域、物理尺度布局和连续微批复用。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_add_quant_gmm_.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantGroupedMatmulInplaceAddNpuOpApi.cpp)（implementation）

- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_add_quant_gmm_.md)（constraint）

- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantGroupedMatmulInplaceAddNpuOpApi.cpp)（implementation）

- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantGroupedMatmulAddNpuOpApi.cpp)（implementation）

- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_quant_grouped_matmul_inplace_add.py)（example）

- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantGroupedMatmulAddNpuOpApi.cpp)（implementation）

- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_quant_grouped_matmul_inplace_add.py)（example）

- [固定来源 13](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/quant_grouped_matmul_inplace_add.py)（implementation）

- [固定来源 14](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/quant_grouped_matmul_inplace_add.py)（implementation）

- [固定来源 15](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_utils/check_platform.py)（implementation）

- [固定来源 16](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/check_platform.py)（implementation）
