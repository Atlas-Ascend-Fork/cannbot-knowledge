---
type: API
title: npu_grouped_matmul_add：K轴累加与输入修改差异
description: 说明FP32累加、分组计数的V2门槛，以及无下划线包装先修改self再clone的契约风险。
tags:
- task.lookup
- topic.compute.composite
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_grouped_matmul_add.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GroupedMatmulAddNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_grouped_matmul_add.md
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
updated_at: '2026-11-10T00:46:44Z'
platforms:
- a2
- a3
- '950'
---

# npu_grouped_matmul_add：K轴累加与输入修改差异

## 固定版本与范围

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的产品页、Schema与包装实现，具体分支不回推发布基线。未执行上游代码、图编译或NPU实验。

## 接口

```text
npu_grouped_matmul_add(self, x, weight, group_list, *,
    transpose_x=True, transpose_weight=False, group_type=2,
    group_list_type=0) -> Tensor
```

self为FP32(g,M,N)，x为FP16/BF16的(K,M)，weight为同dtype的(K,N)，沿K分组。只允许transpose_x=True、transpose_weight=False、group_type=2；不是一般沿M分组的GroupedMatmul。group_list为INT64一维、组数1..1024，0表示非负非递减的累计边界，1表示非负每组计数；末值或总和不超过K，允许空组。

包装只有在aclnnGroupedMatmulAddV2可用且IsAclnnOnly()为真时才向后端传group_list_type；其他分支调用旧入口，不传这一参数。不能认为每组计数模式在所有产品或旧运行库都生效。默认累计边界是审阅两条入口时可共同核对的路径。

## 输入保留与图模式边界

文档列A2/A3和950DT、训练/推理、单算子/图模式及默认确定性。每组x/weight各维按32字节对齐后须小于INT32_MAX，M/N末维小于65536。此产品页不能扩展为950PR保证。

Schema的self无写入alias标记，但C++把self直接作为底层累加目标，完成后返回self.clone()。返回Tensor的新存储不表示原self未被修改，调用者不能依赖无下划线命名作输入保护。图功能化与输入mutation可能受此差异影响，尚未由运行实验消解。

同提交Meta函数返回输入y，且未包含Schema中的group_list_type关键字；这与完整图调用签名存在差异。产品文档列图模式不消除该静态不一致，不能用本卡保证该关键字在图中可用。

- [显式原地版本及其独立产品范围](../../../training/apis/torch_npu/npu_grouped_matmul_add_.md)


## 验证

对照同精度与布局的参考计算，检查输出、输入是否改变、尺度/分组解释及无效输出槽。记录运行库入口、产品和执行模式；静态代码不能代替设备正确性、确定性或性能测量。

## 完整双语范围和发布实现对照

主线完整中英文均只列950DT及A2/A3，训练/推理、单算子/图模式和默认确定性；原地同名页只列950PR/DT训练单算子，两页的支持范围不能互相补齐。公开cumsum例子[64,64,192,256]对应大小[64,0,128,64]，相同累计边界表示空K组，不是遗漏了一个组。

发布和主线C++在是否使用V2、group_list_type是否传入，以及更新原self后返回clone的行为上相同。V2符号检查和IsAclnnOnly结果均被缓存，旧入口不会把type=1的每组计数自动转换成累计边界。两版非原地Meta都缺少group_list_type关键字且返回y，这些差异没有因文档附有输出数值而消除。

## 测试的重复名称、维度和输入保护缺口

两版测试各有四段test定义，但两组同名方法覆盖了前面的A2定义，实际留下两个950方法且均skip。其self还构造成二维(512,256)，CPU参考把分组结果强行reshape到该shape，并未覆盖公开的(g,M,N)输入契约。

测试没有检查非原地函数调用后原self是否保留，也未测返回存储alias、type=1或旧库回退。局部误差比较中的带符号均值不是通用精度保证。本次只保留静态证据，不把跳过测试或同名覆盖算作产品已验证。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_grouped_matmul_add.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GroupedMatmulAddNpuOpApi.cpp)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_grouped_matmul_add.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GroupedMatmulAddNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_grouped_matmul_add.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_grouped_matmul_add.py)（example）
