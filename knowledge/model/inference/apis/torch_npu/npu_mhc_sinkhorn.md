---
type: API
title: npu_mhc_sinkhorn：迭代顺序和中间缓存开关
description: 说明950双随机归一化、带eps的有限次迭代及out_flag控制的扁平缓存容量。
tags:
- task.lookup
- topic.compute.composite
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_mhc_sinkhorn.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MhcSinkhornKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_mhc_sinkhorn.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MhcSinkhornKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_mhc_sinkhorn.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_mhc_sinkhorn.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_mhc_sinkhorn_backward.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml
  role: implementation
created_at: '2026-11-09T06:52:35Z'
updated_at: '2026-11-09T23:51:27Z'
platforms:
- '950'
---

# npu_mhc_sinkhorn：迭代顺序和中间缓存开关

## 固定版本与范围

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的产品页、Schema与包装实现，具体分支不回推发布基线。未执行上游代码、图编译或NPU实验。

## 接口与算法

```text
npu_mhc_sinkhorn(x, *, eps=1e-6, num_iters=20,
    out_flag=0) -> (y, norm_out, sum_out)
```

x为非空FP32 ND(T,n,n)或(B,S,n,n)，n仅4/6/8，可非连续。num_iters为1..100。先沿末轴Softmax加eps，再沿倒数第二轴求和加eps后相除；剩余迭代交替行归一化、列归一化。y同shape/dtype，是有限步带eps的近似双随机结果，不把每一行/列和严格等于1当作任意输入的保证。

## 可选缓存与内存

out_flag只按文档使用0/1。0时公开仍是三返回槽，后两项无有效Tensor；1时两者同时有效。把T解释为packed长度或B*S，n_align=8，norm_out物理元素数2*num_iters*T*n*8，sum_out为2*num_iters*T*8，均FP32的一维缓存。尾轴对齐空间不等于模型残差路数增加到8。

推理无需中间结果时不启用缓存；启用后不能只按y的容量估计显存。Schema虽用SymInt迭代数，C++会expect_int，不据此保证运行时任意符号迭代次数。产品页仅950PR及DT推理、单算子与TorchAir图模式；缓存供反向使用的描述本身不提升该产品页的训练支持范围。

- [前处理投影](npu_mhc_pre.md)
- [残差合并](npu_mhc_post.md)


## 验证

对照同精度与布局的参考计算，检查输出、输入是否改变、尺度/分组解释及无效输出槽。记录运行库入口、产品和执行模式；静态代码不能代替设备正确性、确定性或性能测量。

## 中英文缓存与两版分配差异

主线中文给出一维、末轴按8补齐的物理缓存，与主线C++/Meta相符；主线英文仍写未对齐的多维迭代布局，并提到training/prefill的token范围。不能把英文逻辑展示直接reshape成内核缓存，也不据这段文字扩充产品页仅推理的范围。

发布C++在out_flag=1时把norm_out与sum_out都按x.shape分配，发布Meta还不区分开关、始终返回三份x形状；主线修正为两种不同长度的一维容量，关闭时Meta返回None、C++返回未定义的可选Tensor槽。两版不能混用缓存形状，也不能因同名接口有三槽就读取关闭的后两项。

主线Meta用out_flag真值判断，而C++只在等于1时分配，故公开0/1之外的值不能由Meta通过推断有效。num_iters的SymInt最终由C++转成确定整数；Meta主要检查rank、末轴n和迭代次数，没有完整检查非空、正方形或dtype，少检查不放宽公开契约。

## 反向缓存是不透明的消费协议

主线新增npu_mhc_sinkhorn_backward(grad_y,norm,sum)，生成包装输出与grad_y同shape/dtype；Meta要求grad_y为三/四维、末轴4/6/8，且两个缓存不为None，错误信息明确要求前向out_flag=1。自动求导只令y可微、保存两个缓存，不自动开启前向开关。

反向参考把缓存按核与token分块交错打包，并依赖固定实现常数；这说明缓存不能按英文的普通迭代维度任意构造。应用应直接消费同一配套前向的缓存，不复制测试中的Tiling或设备常数作为可移植协议。这里摄取的是模型消费者的缓存边界，不推广内核生产者实现。

反向测试保存的初始norm缓存是未加eps的Softmax，而公开算法说明的初始norm写成Softmax+eps；sum的初始槽也没有在公开公式中完整定义。最终y的计算和供反向使用的内部保存值分别核对，不能要求所有缓存逐项等于公开简式。

两份前向测试仅比较out_flag=0、n=4、20次迭代的最终y；发布测试还以位置参数传递schema中关键字专用的选项，主线已改关键字。主线反向的独立用例使用CPU构造并打包的缓存；编译用例使用aot_eager，比较Eager自动求导，没有验证TorchAir GE或aclgraph反向。所有测试仅作静态来源，未运行设备或扩大训练支持。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_mhc_sinkhorn.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MhcSinkhornKernelNpuOpApi.cpp)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_mhc_sinkhorn.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MhcSinkhornKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_mhc_sinkhorn.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_mhc_sinkhorn.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_mhc_sinkhorn_backward.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml)（implementation）
