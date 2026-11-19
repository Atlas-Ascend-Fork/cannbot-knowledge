---
type: API
title: npu_rms_norm_quant：归一化后静态量化与 INT4 打包
description: 说明 RMSNorm、beta 与乘法 scale 的融合顺序及必填 offset、打包和 shape 约束。
tags:
- task.lookup
- topic.compute.quantization
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_rms_norm_quant.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modeling_deepseek.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_rms_norm_quant.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_rms_norm_quant.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/RmsNormQuantKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RmsNormQuantKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-09T01:52:44Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# npu_rms_norm_quant：归一化后静态量化与 INT4 打包

## 版本与范围

本文依据 `ascend_26_0_pt28` 发布来源组合中 OpPlugin 的固定提交；仅描述下列平台及参数路径。来源配套与实际部署验证分别核对。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_rms_norm_quant(x, gamma, beta, scale, offset, epsilon=1e-06, *, dst_dtype=None) -> Tensor
```

先计算 RMSNorm(x)*gamma+beta，再按 round(quant_in*scale+offset) 量化，只返回 y。默认 INT8；quint4x2 实际返回 INT32 打包，末维缩小为原来的 1/8，不返回独立的动态 scale 或 rstd。

## 参数与组合限制

- A2/A3 的 x 支持 1–8 维 FP16/BF16 ND，支持非连续、不支持空；gamma/beta 与 x 同 dtype，形状为 (D,) 或 (1,D)，D 为 x 末维。
- scale 是单元素一维 Tensor、与 x 同 dtype，值不能为 0；offset 为相同 shape 的 INT8 Tensor。beta/scale/offset 都是该签名的必选入参。
- epsilon 默认 1e-6。打包 INT4 必须核对末维 8 对齐，来源对 A2 还明确 gamma/beta 末维为偶数；不能将普通 INT8 输出形状沿用到打包输出。
- 这是静态 scale 路径，不能与生成 MXFP block scale 的新主线融合接口混为同一 API。

## 验证与模型关联

按 RMSNorm、beta、乘法 scale 和 round 的相同顺序建立参考；检查 INT4 解包、offset dtype 和静态 scale 是否来自模型量化参数。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modeling_deepseek.py#L1892)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## 主线950组合与Schema默认值

固定发布和主线schema均为int? dst_dtype=None、必须用关键字传入；None按INT8。发布公开原型写字符串'int8'，主线英文仍有字符串式取值总述，不能照此生成字符串参数。beta、scale、offset仍是必填位置参数，不能沿用v2的可选偏置签名。

主线中英文新增950PR及DT：FP32输入的x/gamma/beta/scale/offset全FP32；FP16/BF16输入可同dtype scale配INT8或同dtype offset，或FP32 scale配INT32/FP32 offset。950的FP8/HiFloat8、混合scale类型只按这些组合，不能按单参数名单任意组合。HiFloat8的物理dtype按Meta映射为UINT8容器；不是普通无符号整数量化。老Atlas200I/500A2与旧Atlas推理仍仅FP16，旧Atlas推理尾轴限制是32 Bytes，不能改写成32元素。

两固定C++只有quint4x2走八值INT32打包并检查N被8整除，不能因为动态融合接口支持torch_npu.int4就自动增加本接口别名。若输入内部格式为NZ，打包分支另按NZ分配；公开页只列ND，代码路径不是任意私有格式的公开支持保证。两版均直接调用aclnnRmsNormQuant，固定乘法scale方向不因新增FP8类型改变，也不返回动态scale或rstd。

主线扩大了产品和类型，不代表其与TorchAir主线已经配套；本次没有在两个固定GE Converter树中找到注册本入口的转换器，局部搜索结果不扩成所有后端运行时不支持的断言。

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_rms_norm_quant.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_rms_norm_quant.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_rms_norm_quant.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/RmsNormQuantKernelOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RmsNormQuantKernelOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
