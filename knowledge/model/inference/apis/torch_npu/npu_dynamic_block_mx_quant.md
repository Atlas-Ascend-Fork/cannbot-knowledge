---
type: API
title: npu_dynamic_block_mx_quant：32×32 MX块与FP4物理形状
description: 以Meta和C++包装纠正文档FP4输出形状，说明E8M0尺度、两个轴的pad布局及算法可选值。
tags:
- task.lookup
- topic.compute.quantization
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dynamic_block_mx_quant.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DynamicBlockMxQuantKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_dynamic_block_mx_quant.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DynamicBlockMxQuantKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dynamic_block_mx_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dynamic_block_mx_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-09T06:25:22Z'
updated_at: '2026-11-09T21:57:27Z'
platforms:
- '950'
---

# npu_dynamic_block_mx_quant：32×32 MX块与FP4物理形状

## 版本和支持范围

依据 OpPlugin 固定主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda`，按产品表和具体参数分支使用，不回推发布基线，不从单页类型名单推导任意混合组合。未执行上游代码、设备算子或图编译。

## 接口与算法

```text
npu_dynamic_block_mx_quant(input, *, round_mode='rint',
    dst_type=torch_npu.float4_e2m1fn_x2, scale_alg=0,
    dst_type_max=0.0) -> (y, scale1_out, scale2_out)
```

仅950推理，文档列单算子和图模式。input为2..3维FP16/BF16 ND，不支持空、可非连续。基本块32×32共享尺度，再分别沿两轴广播输出E8M0尺度。算法0按块最大绝对值的指数和目标emax生成2的幂尺度；emax对FP4 E2M1/E1M2、FP8 E4M3FN/E5M2分别为2/0/8/15。

scale_alg仅0或2；2仅FP4 E2M1，按目标幅度生成浮点scale并上取整到E8M0可表示的尺度，尾块不足时按零补。dst_type_max只在该组合可设0、6、7，0取目标默认最大值。FP4 round_mode支持rint/floor/round，FP8仅rint。

## 逻辑类型与物理存储

文档称y形状同input，但同提交Meta与C++均明确：FP4以UINT8每字节承载两个值，输入末轴必须偶数，**y物理末轴=N/2**；FP8才保持原形状。不能按原N个字节分配/读写FP4输出，也不把UINT8容器当普通无符号整数。

scale1/scale2逻辑E8M0，实际UINT8、rank比input多1，尾轴为2。对(B,M,N)，物理形状分别为(B,M,ceil(ceil(N/32)/2),2)和(B,ceil(ceil(M/32)/2),N,2)；尺度组数做偶数pad，补0，scale2还需按两行交织解释。不是常规FP32单行scale，也不是两个独立任意缩放矩阵。

这些形状来自静态实现与Meta的一致证据，不是设备结果；布局解码和低精度数值仍需目标版本实验。


## 验证

先核对计算顺序、分组语义、scale方向与真实存储形状，再比较量化/反量化数值；覆盖空组、尾块、非连续和打包解码的实际需要。分别测内存与稳态收益，本文只有静态证据。

## 完整版本与图输出布局

主线中英文确认950PR及950DT的推理场景。固定发布快照没有同名公开页，但已有schema、Meta、C++包装和TorchAir Converter；这些声明或分配不能回填出该发布组合的公开产品支持。两版包装都把FP4输出物理尾维除2，公开“y.shape同input”只能视为逻辑形状。

两个固定TorchAir Converter接GE DynamicBlockMxQuant后将FP4通过Reshape/Bitcast恢复UINT8打包输出，而scale1/scale2的GE描述仍为E8M0。图内逻辑dtype和Eager的UINT8容器需分别接线，不把打印dtype或单纯view当通用解码。两尺度是同一个32×32基本块scale的两种广播布局，不是各轴独立求最大值。

两版Meta均以int(math.ceil(...))计算尺度维度；C++仅要求输入至少二维，公开页却只允许二维/三维、非空。不能从包装缺少上界检查扩大公开秩范围，也不能把文档dynamic=True小尾块示例当任意符号形状都可成图的证明。算法2的目标仅E2M1且dst_type_max只0/6/7，不借基础MX的[6,12]范围扩展。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dynamic_block_mx_quant.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DynamicBlockMxQuantKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_dynamic_block_mx_quant.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DynamicBlockMxQuantKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dynamic_block_mx_quant.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dynamic_block_mx_quant.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
