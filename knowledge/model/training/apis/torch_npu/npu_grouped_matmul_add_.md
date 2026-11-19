---
type: API
title: npu_grouped_matmul_add_：微批梯度的原地FP32累加
description: 说明950训练单算子的输入alias与K轴分组，不继承无下划线页的图及产品范围。
tags:
- task.lookup
- topic.compute.composite
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_grouped_matmul_add_.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GroupedMatmulAddNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_grouped_matmul_add_.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GroupedMatmulAddNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_grouped_matmul_add.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_grouped_matmul_add.py
  role: example
created_at: '2026-11-09T06:52:35Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- '950'
---

# npu_grouped_matmul_add_：微批梯度的原地FP32累加

## 固定版本与范围

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的产品页、Schema与包装实现，具体分支不回推发布基线。未执行上游代码、图编译或NPU实验。

## 接口与输入输出

```text
npu_grouped_matmul_add_(self, x, weight, group_list, *,
    transpose_x=True, transpose_weight=False, group_type=2,
    group_list_type=0) -> self
```

用于micro-batch梯度累加，将分组矩阵乘与原地Add融合。Schema声明self为Tensor(a!)并返回同一alias，C++与Meta也返回self。需按训练计划初始化累加缓冲，跨micro-batch重复调用会继续累加。

self为FP32(g,M,N)，x为FP16/BF16的(K,M)，weight为同dtype的(K,N)，沿K分组。只允许transpose_x=True、transpose_weight=False、group_type=2；不是一般沿M分组的GroupedMatmul。group_list为INT64一维、组数1..1024，0表示非负非递减的累计边界，1表示非负每组计数；末值或总和不超过K，允许空组。

包装只有在aclnnGroupedMatmulAddV2可用且IsAclnnOnly()为真时才向后端传group_list_type；其他分支调用旧入口，不传这一参数。不能认为每组计数模式在所有产品或旧运行库都生效。默认累计边界是审阅两条入口时可共同核对的路径。

本页仅确认950PR/DT、训练、单算子；不从[npu_grouped_matmul_add](../../../inference/apis/torch_npu/npu_grouped_matmul_add.md)的宽产品页反向扩展本原地接口的图支持或A2/A3支持。x/weight各维按32字节对齐后须小于INT32_MAX。


## 验证

对照同精度与布局的参考计算，检查输出、输入是否改变、尺度/分组解释及无效输出槽。记录运行库入口、产品和执行模式；静态代码不能代替设备正确性、确定性或性能测量。

## 独立产品契约和原地状态

完整双语明确本接口仅950PR/DT训练、仅单算子；无下划线页中的图支持、A2/A3和950DT范围不反向扩充本页。公开示例按(K,M)/(K,N)源矩阵与transpose_x=True使用，不能照搬量化接口先显式转置后的view再重复套用本标志。

两版Schema、C++和Meta均返回原self alias，旧入口不传group_list_type的限制也都相同；Meta只检查group_type=2，没有验证所有维度、分组值或数据类型。文档示例中的out is self_t只作为源调用语义，不是本卡实测。

两版测试同名定义覆盖早期A2入口，留下的方法均skip，并使用不符合公开三维self的二维缓冲。不能据这些用例为原地API增加A2支持，也未证明有效三维连续微批累积、空组、计数模式或多步梯度正确性。需要按训练计划初始化和复用同一FP32缓冲，再与清晰的逐组参考比较。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_grouped_matmul_add_.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GroupedMatmulAddNpuOpApi.cpp)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_grouped_matmul_add_.md)（constraint）

- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GroupedMatmulAddNpuOpApi.cpp)（implementation）

- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_grouped_matmul_add.py)（example）

- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_grouped_matmul_add.py)（example）
