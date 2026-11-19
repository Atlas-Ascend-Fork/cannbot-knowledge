---
type: API
title: npu_quant_matmul_gelu：bias位置、输出dtype与A4图差异
description: 说明A2/A3量化矩阵乘融合GELU，保留INT4物理K校验及BF16 bias的Meta差异。
tags:
- task.lookup
- topic.compute.quantization
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_quant_matmul_gelu.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantMatmulGeluKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_quant_matmul_gelu.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_quant_matmul_gelu.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_quant_matmul_gelu.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantMatmulGeluKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_quant_matmul_gelu.py
  role: example
created_at: '2026-11-09T06:56:17Z'
updated_at: '2026-11-10T00:33:17Z'
platforms:
- a2
- a3
---

# npu_quant_matmul_gelu：bias位置、输出dtype与A4图差异

## 固定版本与范围

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的完整产品分支、Schema与同提交C++/Meta。以下是文档和静态包装核对，未执行上游源码、编译图或设备实验，不回推发布基线。

## 接口与计算

```text
npu_quant_matmul_gelu(x1, x2, x1_scale, x2_scale, *,
    bias=None, approximate='gelu_erf') -> Tensor
```

先量化矩阵乘和反量化，再GELU。INT32 bias加在反量化乘scale之前，浮点bias加在之后；两者不能通过单纯dtype转换互换。approximate只gelu_erf或gelu_tanh，默认erf，与[npu_gelu](npu_gelu.md)的接口取值需分别核对。

x1/x2均rank2..6、类型匹配，A8W8为INT8，A4W4为INT32打包或quint4x2对应INT4。x1 ND，x2在A8W8可ND/NZ，A4仅ND。批维按广播规则推导，两个二维输入的输出仍二维(M,N)，不强制添加batch=1维。

x1_scale=FP32(M,)，x2_scale=FP32或BF16的(N,)或(1,)，所有必选输入非空。A4的bias只INT32或None且(N,)；A8可INT32/FP16/BF16/FP32或None，允许(N,)或匹配单batch轴输出的(B,1,N)。末维不能超过65535。

## 输出dtype与Meta差异

C++依据x2_scale选择FP16或BF16，且BF16 bias优先强制BF16。Meta只看x2_scale，没实现bias优先级；因此x2_scale=FP32且bias=BF16时Eager分配与Meta不同。稳定使用需优先核对无该冲突的匹配组合，不能从产品dtype总表推定任意跨精度组合成图一致。

## A4物理K不是逻辑K

INT32每个物理元素容纳8个INT4，x1物理(M,K/8)、x2物理(K,N/8)。C++在x1末维*8等于x2倒数第二维时恢复N；Meta却对两者均INT32检查物理x1末维==x2倒数第二维，同时恢复N。这会与常见打包形状冲突，不能把Meta成功当作正确A4形状保证，也不能声称该提交已具备可直接复制的A4图配方。

C++只接受成对相同输入类型，Meta中的混合INT32/quint4x2分支不扩大Eager范围。按stride推导的转置与最后一维打包必须共同核对，不能只在常规matmul前加view(int32)。

产品页确认A2/A3推理，未据包装注册推导所有图后端可用。以匹配A8W8作为静态一致的基础契约，A4与上述BF16 bias组合保留为待实际图/设备核验的分支。

## 验证

参考应保持bias添加位置、scale粒度和GELU近似方式；比较形状、dtype及数值，分别覆盖ND/NZ转换成本、批广播和打包布局。

## 两版共同约束、None及文档表格差异

发布中文与主线双语均只公开A2/A3推理，950未列而非明确No。发布NOTICE引用旧版本说明，不改变本卡对固定提交的限定。两版包装依据权重格式选择FusedQuantMatmul或FusedQuantMatmulWeightNz，A4的公开ND限制不因共用NZ判断而放宽。

公开文字、两版C++都令BF16 bias优先输出BF16；公开组合表却把FP32 scale与各种bias统一列为FP16，两版Meta也只看scale。该组合同时存在文档表格与Meta冲突，保留已有精度边界。Schema还允许approximate=None，C++将其回退为erf，而Meta仅接受两个字符串，不能把None视作所有模式均等价的默认表达。

## 跳过的测试不是完整INT4参考

主线测试全文及发布完整差异均已核对，两版16个入口全部skip，拟测仅A2。CPU参考把quint4x2视为字节、把INT32直接按packed shape做矩阵乘，没有完整的有符号4位解包，不能当作A4数值黄金参考。

该参考对所有bias都在乘scale后相加，不适用于公开要求在scale前加入的INT32 bias。A4用例实际只检查shape、有限性及dtype，batch用例虽计算CPU结果却未对该结果作数值断言。BF16 bias优先级、六维广播、转置打包和所有图路径也未由这些跳过的用例证明。

公开A4样例中的随机INT32值用于展示载体shape，并没有对八个独立4位数逐项打包；其注释也要求实际使用时先量化和打包。输出shape与Meta不一致的分支继续按前文限定，不据样例调用形式宣称已可直接用于模型。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_quant_matmul_gelu.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantMatmulGeluKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_quant_matmul_gelu.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_quant_matmul_gelu.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_quant_matmul_gelu.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantMatmulGeluKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_quant_matmul_gelu.py)（example）
