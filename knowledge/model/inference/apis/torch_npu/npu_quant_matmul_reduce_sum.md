---
type: API
title: 量化分组矩阵乘后归约（torch_npu.npu_quant_matmul_reduce_sum）
description: torch_npu.npu_quant_matmul_reduce_sum：执行分组量化矩阵乘，并对各组结果求和。 说明ND/NZ输入、per-token/per-channel尺度和BF16二维输出，保留必传scale限制。
tags:
- task.lookup
- topic.compute.quantization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_quant_matmul_reduce_sum.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_quant_matmul_reduce_sum.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantMatmulReduceSumKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_quant_matmul_reduce_sum.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_quant_matmul_reduce_sum.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_quant_matmul_reduce_sum.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantMatmulReduceSumKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_quant_matmul_reduce_sum.py
  role: example
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/quant_matmul_reduce_sum.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/quant_matmul_reduce_sum.py
  role: implementation
created_at: '2026-11-10T03:38:48Z'
updated_at: '2026-11-14T04:31:20Z'
platforms:
- a2
- a3
aliases:
- torch_npu.npu_quant_matmul_reduce_sum
---


# npu_quant_matmul_reduce_sum：按batch归约的INT8矩阵乘

## 固定版本与范围

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的产品页、Schema与包装实现，具体分支不回推发布基线。未执行上游代码、图编译或NPU实验。

## 接口与归约轴

```text
npu_quant_matmul_reduce_sum(x1, x2, *,
    x1_scale=None, x2_scale=None) -> Tensor
```

x1为INT8 ND(B,M,K)，x2为INT8 NZ(B,K,N)。各batch做矩阵乘并应用x1_scale[b,m]和x2_scale[n]，沿batch维相加，输出BF16 ND(M,N)。这不是输出每组结果的普通GroupedMatmul，也不是沿K之外任意dim可配置的ReduceSum。

x1_scale必须FP32(B,M)，x2_scale必须BF16(N,)；Schema虽给None默认值，产品页和C++/Meta都要求实际存在且形状正确。x2必须真NZ格式，仅contiguous()不产生NZ；来源给npu_format_cast(...,29)转换方式，转换成本应与稳态计算分开评估。

产品表仅A2/A3、推理、静态图；所有输入非空。包装固定dims={0}、keep_dims=False，bias与offset均为空，不从后端接口名字推定已暴露更多量化参数。


## 验证

对照同精度与布局的参考计算，检查输出、输入是否改变、尺度/分组解释及无效输出槽。记录运行库入口、产品和执行模式；静态代码不能代替设备正确性、确定性或性能测量。

## 必传scale、归约含义与两版差异

发布公式把求和终点写为batch，主线改为batch-1；实际包装固定对批轴0归约并移除该轴，不能多算一组。它是本地输入Tensor的分组求和，不执行跨rank通信。两版C++均固定transpose_x1/x2=False、group_size=-1，只调用QuantMatmulReduceSumWeightNz。

主线中文原型把两个scale写成必传关键字，主线英文与发布原型仍写None默认；两版Schema也允许None，但Meta明确要求非None，C++随后检查两者维数。签名可省略不提供合法数值含义，应按FP32(B,M)及BF16(N,)显式提供。

两版Meta未覆盖C++对NZ、相同B、两个scale精确长度等检查，错误rank的报错lambda还引用未定义x或w。不能把Meta只给出(M,N)视为错误输入也会被正确诊断或设备可用。主线单算子示例显式开启allow_internal_format再做NZ转换，图示例本身未重复设置，也不构成独立环境的完整复现证明。

## 静态图和精度测试范围

两固定TorchAir转换器都生成dims=[0]、输出BF16的QuantMatmulReduceSum；注释中的Support声明因NZ表达问题被注释掉，不等于转换器缺失或图模式明确不支持。公开仍仅A2/A3推理及静态图，不从单算子示例扩大所有后端范围。

两版各两个设备测试均skip，拟测A2且采用较大的固定shape。参考比较FP32批量计算后求和并转BF16，以及逐组BF16累加两种顺序，再对最大/平均相对误差和RMSE使用相对门槛；这不是普适设备精度保证，也不是性能测量。本次未执行测试或设置设备确定性状态。

## 已有 OpPlugin 7.3.0 文档与版本边界

### 量化分组矩阵乘后归约：torch_npu.npu_quant_matmul_reduce_sum

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

执行分组量化矩阵乘，并对各组结果求和。

### 文档签名

```text
torch_npu.npu_quant_matmul_reduce_sum(x1, x2, *, x1_scale=None, x2_scale=None) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_quant_matmul_reduce_sum.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_quant_matmul_reduce_sum.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantMatmulReduceSumKernelNpuOpApi.cpp)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_quant_matmul_reduce_sum.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_quant_matmul_reduce_sum.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_quant_matmul_reduce_sum.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantMatmulReduceSumKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_quant_matmul_reduce_sum.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/quant_matmul_reduce_sum.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/quant_matmul_reduce_sum.py)（implementation）
