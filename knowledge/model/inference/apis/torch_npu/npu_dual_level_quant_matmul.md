---
type: API
title: npu_dual_level_quant_matmul：两级FP4尺度与NZ权重
description: 说明512/32固定分组、FP4物理打包以及E8M0配对尺度的文档测试差异。
tags:
- task.lookup
- topic.compute.quantization
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dual_level_quant_matmul.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DualLevelQuantMatmulKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_dual_level_quant_matmul.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_dual_level_quant_matmul.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DualLevelQuantMatmulKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_dual_level_quant_matmul.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-09T06:52:35Z'
updated_at: '2026-11-14T01:59:28Z'
platforms:
- '950'
---

# npu_dual_level_quant_matmul：两级FP4尺度与NZ权重

## 固定版本与范围

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的产品页、Schema与包装实现，具体分支不回推发布基线。未执行上游代码、图编译或NPU实验。

## 接口

```text
npu_dual_level_quant_matmul(x1, x2, x1_level0_scale,
    x2_level0_scale, x1_level1_scale, x2_level1_scale, *,
    bias=None, output_dtype=15) -> Tensor
```

主线产品页仅950PR/DT、训练/推理、单算子，所有张量连续且非空。左矩阵不转置、右矩阵转置，逻辑形状为(M,K)与(N,K)，输出(M,N)，默认BF16，可选FP16。bias若提供为连续FP32(N,)；Schema规定bias/output_dtype为关键字参数，不能按文档原型的位置写法推断调用规则。

输入逻辑FP4 E2M1每字节打包两值，包装按物理x1.size(1)*2恢复K，x2同理，并检查K相等。x1为ND，x2必须真FRACTAL_NZ，不能把物理(K/2)当成量化算法的逻辑K。

## 两级尺度不是可互换的一份scale

level0为每512个K元素的FP32尺度：左(M,ceil(K/512))，右(ceil(K/512),N)。level1为每32元素的MX E8M0尺度。矩阵乘先在各块应用MX尺度，再按对应512组的level0尺度加权累加，不能用一份普通per-token scale替代两级。

产品页把level1写为(M或N,ceil(K/32),2)，但同提交测试构造(M或N,ceil(K/32/2),2)，即两个E8M0指数放在尾维2。该测试用K=1024、UINT8尺度容器和INT8打包FP4输入，包装将其解释为对应逻辑dtype；此静态样例支持布局核对，未实际执行，不能扩展成任意尾块都验证通过。

与[npu_dynamic_dual_level_mx_quant](npu_dynamic_dual_level_mx_quant.md)配对仍须检查权重NZ转换、逻辑/物理K与尺度pad，不能直接照产品页公式再扩大一倍尺度容量。


## 验证

对照同精度与布局的参考计算，检查输出、输入是否改变、尺度/分组解释及无效输出槽。记录运行库入口、产品和执行模式；静态代码不能代替设备正确性、确定性或性能测量。

## 发布实现与文档的证据强度

主线双语页均明确950PR/DT，训练/推理、仅单算子。OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5虽也有同名Schema、C++和逐字节相同的测试，该发布没有产品文档，不能仅凭实现存在认定与主线产品声明、运行库能力完全相同。[v2.1,newest]生成范围也不表示历史版本及所有设备都支持。

两C++仅局部检查二维、真实NZ与恢复后的K相等，并固定512/32及左不转置、右转置。它们不完整验证scale形状/类型、bias、空Tensor、连续性及输出类型；能分配结果不等于满足产品契约。右权重必须经过正确FP4编码及NZ转换，不能靠改shape或普通数值cast得到。产品仅单算子，不从其他MX接口借用TorchAir支持或自动梯度。

双语产品页的level1形状都写ceil(K/32)再接尾维2，示例与测试却使用ceil(K/32/2)再接2。两Cpp不检查该容量，不能消除文字冲突；只在所示K=1024时，测试的两个尾值分别对应两组32元素尺度。非整除尾块、padding或其他K必须重新核对实际编码与内核契约。

## 非零参考覆盖的实际范围

两测试完全同SHA，只有950单例M=256、K=1024、N=2048，输出BF16、带FP32 bias。参考从FP4值出发做位打包，按E8M0指数位解码尺度，512段内执行32分组反量化与FP32矩阵乘，乘level0尺度累加后转BF16，设定1e-3容差。这是有用的独立参考结构，本文没有运行，不能写成设备验收通过。

该文件没有FP16输出、无bias、奇数/非整除K、错误尺度、空Tensor、图或反向验证；仅设torch随机种子也不固定NumPy随机输入。文档样例只打印输出，不新增精度或吞吐证据。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dual_level_quant_matmul.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DualLevelQuantMatmulKernelNpuOpApi.cpp)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_dual_level_quant_matmul.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_dual_level_quant_matmul.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DualLevelQuantMatmulKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_dual_level_quant_matmul.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
