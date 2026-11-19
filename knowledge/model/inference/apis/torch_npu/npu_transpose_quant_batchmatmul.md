---
type: API
title: npu_transpose_quant_batchmatmul：950 三维量化矩阵乘
description: 区分 K-C、MX 与 T-C 的输入、scale 形状和排列限制，不沿用浮点 transpose_batchmatmul。
tags:
- task.lookup
- topic.compute.quantization
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_transpose_quant_batchmatmul.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modeling_deepseek.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_transpose_quant_batchmatmul.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_transpose_quant_batchmatmul.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_transpose_quant_batchmatmul.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/TransposeQuantBatchMatMulKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/transpose_quant_batchmatmul.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp
  role: implementation
created_at: '2026-11-09T01:56:57Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- '950'
---

# npu_transpose_quant_batchmatmul：950 三维量化矩阵乘

## 版本与范围

本文依据 `ascend_main_candidate` 中 OpPlugin 的固定主线提交；该候选的软件配套尚未确认。不能据此推定 26.0.0 发布组合支持此接口或下列参数。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_transpose_quant_batchmatmul(x1, x2, dtype, *, bias=None, x1_scale=None, x2_scale=None, group_sizes=None, perm_x1=None, perm_x2=None, perm_y=None, batch_split_factor=1, x1_dtype=None, x2_dtype=None) -> Tensor
```

完成三维量化矩阵乘与排列，返回 (M,B,N) 的 ND Tensor，dtype 由必选参数指定为 FP16/BF16/HiFloat8。x1 为 (M,B,K)，x2 为 (B,K,N) 或 (B,N,K)，K 相等。

## 参数与组合限制

- perm_x1 只支持 [1,0,2]、perm_y 只支持 [1,0,2]，perm_x2 为 [0,1,2] 或 [0,2,1]；bias 不支持、保持 None，batch_split_factor 只支持 1。
- K-C 路线：x1/x2 为 FP8/HiFloat8 支持表中的类型，x2 仅 ND，K=512、N=128，perm_x2=[0,1,2]；一维 scale 分别为 (M,) 与 (N,)。
- MX 路线：x1/x2 仅 E4M3 FP8，K 为 64 的倍数；x1_scale=(M,B,K/64,2)，x2_scale 按排列为 (B,K/64,N,2) 或 (B,N,K/64,2)。group_sizes 仅支持 [0,0,32]、[0,1,32]、[1,0,32]、[1,1,32]。
- T-C 路线：仅 HiFloat8、x2 仅 ND，一维 x2_scale=(N,)，x1_scale 可 None 或 (1,)；来源图模式仅确认 K-C 和 MX，不把 T-C 的 Eager 路线扩大到图模式。
- MX scale 的四维及交织布局与普通逐通道一维 scale 不兼容，不能仅靠改 dtype 接入。

## 验证与模型关联

对每种量化粒度分别执行解码、排列与参考 matmul；核对转置后 scale 布局及输出 dtype，以 K/N 不符合 K-C 限制作为反例。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modeling_deepseek.py#L1752)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## 发布生成包装与主线逻辑dtype

发布快照已有生成Schema和测试，但没有本次主线公开产品页，也没有x1_dtype/x2_dtype参数；不据此回推950主线契约到发布基线。主线改用手写包装，对提供的逻辑dtype建立TensorWrapper；它解释底层编码，不把任意UINT8数值自动转换成正确FP8或HiF8数据。

主线在x2为NZ且x1非NZ时要求aclnnTransposeQuantBatchMatMulWeightNz符号可用；缺失时明确报错，消息要求CANN≥9.1或改用ND。该检查依据实际符号，不意味着只改版本字符串或采用一份未配套的TorchAir主线即可使用。

## 默认参数、图转换与公开范围

C++为None排列补全[1,0,2]、[0,1,2]和[1,0,2]，两版Meta却直接对传入排列调用.index，没有同样的None补全。因此公开示例显式传排列与省略排列是不同路径，不凭Eager默认成功推定图捕获默认也能通过。

发布Meta仅允许FP16/BF16输出；主线扩大枚举映射及UINT8分配，并不使公开输出FP16/BF16/HiF8范围扩展成所有枚举。主线TorchAir转换器对显式逻辑dtype使用Bitcast及GE描述更新，然后生成TransposeQuantBatchMatMul，也不是数值转换。

group_sizes的三项经C++按16位字段打包，分别要求0..65535；省略或空列表在该helper中为0。主线GE helper却要求列表恰有三项，显式空列表会报错，不能把空列表与None当作全路径等价。这个通用编码范围也不放宽MX公开仅四种[0/1,0/1,32]组合及其他模式约束。

## 测试证据的具体缺口

发布十个测试入口全部skip；主线原十个也skip，新增NZ用例未skip但文件没有导入其使用的np，不能计为可用数值覆盖。原四个正例还给只接受一个scale的参考函数传两个scale，MX参考也不能把原始E8M0字节直接当一般数值scale配方。没有执行这些测试，未证明全部模式、HiF8、逻辑dtype覆盖或950产品的运行结果。

主线公开950PR/DT训练及推理，图模式只明确K-C和MX。包装接受更多可选形状、Meta给出shape或转换器存在，不扩大T-C图模式、split>1或bias的公开支持。

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_transpose_quant_batchmatmul.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_transpose_quant_batchmatmul.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_transpose_quant_batchmatmul.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_transpose_quant_batchmatmul.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/TransposeQuantBatchMatMulKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/transpose_quant_batchmatmul.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp)（implementation）
