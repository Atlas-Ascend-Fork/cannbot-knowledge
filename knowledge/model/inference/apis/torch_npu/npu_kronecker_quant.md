---
type: API
title: npu_kronecker_quant：双侧旋转与两种4位布局
description: 说明950双矩阵乘的INT4 pertoken与FP4 pergroup差异，按C++和Meta修正FP4物理输出shape。
tags:
- task.lookup
- topic.compute.quantization
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_kronecker_quant.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/KroneckerQuantKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_kronecker_quant.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/KroneckerQuantKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/flat_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/flat_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-09T06:53:58Z'
updated_at: '2026-11-09T21:57:27Z'
platforms:
- '950'
---

# npu_kronecker_quant：双侧旋转与两种4位布局

## 固定版本与范围

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的产品分支与同提交包装/Meta，未运行上游算子或设备实验。新参数和产品支持不回推发布基线。

## 接口与形状

```text
npu_kronecker_quant(x, kronecker_p1, kronecker_p2,
    clip_ratio=None, dst_dtype=None, dst_type_max=None)
    -> (out, quant_scale)
```

对x先右乘P2，再左乘P1，然后量化。x为同dtype FP16/BF16的(K,M,N)，P1=(M,M)、P2=(N,N)；K=1..262144，M/N=1..256，N为偶数。FP4专节允许P2=(0,0)，但不据空矩阵自行推导其他输入都可为空。

## 两种量化模式

- 默认INT4 pertoken：clip_ratio=None按1.0，其余须(0,1]；每个首轴切片共享FP32尺度(K,)，八个INT4打包成一个INT32，输出(K,M,N/8)，N必须8整除。
- 指定FP4 E2M1 pergroup：把后两轴合并，每32值共享MX E8M0尺度，配对尾维2。产品文档将out写成逻辑(K,M*N)，C++和Meta实际分配物理(K,M*N/2)，Meta为UINT8，不能按逻辑元素数重新reshape字节容器。尺度物理(K,ceil(M*N/64),2)，不是FP32(K,)。

这两种输出不能只修改dtype后共用同一解码/下游矩阵乘。dst_type_max仅FP4可设0或[6,12]，0采用默认幅度。包装有aclnnFlatQuantV2才传该新增幅度，旧入口不传；配置被接受不能证明旧库已使用。

产品页仅950推理，单算子与TorchAir图模式。Meta处理类型与输出形状，不能代替尺度数值、裁剪和两次矩阵乘顺序的设备对照。

## 验证

按P1@(x@P2)建立参考，分别检查整数与FP4的物理打包、尺度和重建误差；记录V2符号存在与目标dtype，分开测旋转、量化及融合稳态开销。

## 全文公式与GE打包修正的版本

主线中英文仅950PR及950DT的推理、单算子和TorchAir图模式。INT4的(K,)尺度按每个首轴切片在M×N内求最大绝对值，不是沿K归约；公开公式写到x''[K]是索引上界歧义，不应照抄成越界参考。FP4公式对emax及log2(reduceMax)的表述也不足以独立定义负数、全零块及舍入边界，不自行生成未经设备核验的数值实现。

固定发布schema/包装/Meta没有dst_type_max，主线才增加该参数；FlatQuantV2是否存在是运行库符号条件，不由日期或GE FlatQuant名称推出最低CANN版本。clip_ratio=None在两固定Converter均按1.0，主线dst_type_max=None按0。

图输出还有实际版本差异：发布Converter的FP4分支直接返回GE逻辑FP4结果，未像INT4分支那样打包到Python物理容器；主线才新增FP4的Reshape/Bitcast，返回UINT8的(K,M*N/2)，与Meta物理分配一致。主线参数检查接受297并注释成E2M1，但实际FP4分支按torch_npu.float4_e2m1fn_x2（296）判断；297是E1M2且会落入另一分支，不能当作本接口受支持的E2M1别名或修复方案。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_kronecker_quant.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/KroneckerQuantKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_kronecker_quant.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/KroneckerQuantKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/flat_quant.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/flat_quant.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
