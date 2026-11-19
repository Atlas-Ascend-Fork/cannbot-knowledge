---
type: API
title: npu_weight_quant_preprocess：数据流、预打包与输出alias
description: 说明950八类权重量化预处理、4位物理布局与ND/NZ分支，明确透传输出共享输入存储。
tags:
- task.lookup
- topic.compute.quantization
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_weight_quant_preprocess.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/WeightQuantPreprocessKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_weight_quant_preprocess.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_weight_quant_preprocess.py
  role: example
created_at: '2026-11-09T07:11:38Z'
updated_at: '2026-11-10T00:19:22Z'
platforms:
- '950'
---

# npu_weight_quant_preprocess：数据流、预打包与输出alias

## 固定版本与范围

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的产品页和同提交Schema、Meta/包装实现；未运行上游源码、测试、分布式通信或设备实验，不回推发布基线。

## 接口与用途

```text
npu_weight_quant_preprocess(weight, weight_scale, x_dtype,
    weight_dtype, weight_scale_dtype, weight_offset=None,
    bias=None, x_scale_dtype=None, k_group_size=0)
    -> (out_weight, out_scale, out_offset, out_bias)
```

这是针对已有量化权重的Matmul参数预处理，不是把任意浮点权重直接量化。产品页及C++分派表只确认950。输入weight/scale可非连续，bias若给定必须连续；逻辑dtype参数须与真实容器编码匹配。

INT4/FP4每字节两值：非转置权重物理(K,N/2)，转置视图物理(K/2,N)、stride=(1,K/2)；不能把这里的UINT8容器与其他接口八值/INT32打包互换。Torch2.8及以上编译分支还允许原生FP4 E2M1容器，但INT4仍不能靠逻辑dtype把任意INT32容器放行。

## 按数据流选择

以下K/N为逻辑维，scale必须同时满足对应dtype和stride；A16表示FP16/BF16激活，A8为FP8 E4M3FN激活。

|数据流|权重与尺度|分组/输出路径|
|--|--|--|
|MM/GMM MX A8W4|FP4 E2M1；E8M0尺度，MM为(ceil(K/64),N,2)，GMM增加G轴|K按32分组，K可整除32；weight/scale均需规定转置视图，x_scale_dtype=E8M0；生成NZ物理布局|
|MM A16S4|INT4；FP16/BF16的pertensor、perchannel或pergroup尺度|pertensor全走ND；perchannel/pergroup转置走ND，非转置走NZ_C0_8；pergroup须k_group_size>0|
|MM A16F4|FP4 E2M1；FP16/BF16(G,N)，G>1|仅非转置、pergroup，k_group_size>0，输出NZ_C0_8|
|MM MX A16F4|FP4 E2M1；E8M0(ceil(K/32),N)|k_group_size=32，K%32=0，转置ND/非转置NZ_C0_8，x_scale_dtype=None|
|MM A16INT8|INT8；与激活匹配的FP16/BF16尺度|pertensor/perchannel/pergroup均ND透传，转置和非转置均支持|
|MM A16FP8HIF8|E4M3FN或HiF8；与激活匹配的FP16/BF16(N,)或(1,N)|只perchannel、ND透传、k_group_size=0、无offset|
|MM A8F4 T-CG|FP4 E2M1；FP16/BF16(G,N)，G>1|k_group_size=32、x_scale_dtype=None，转置ND/非转置逻辑NZ_C0_32；不是MX E8M0尺度|

除MX A8W4外，x_scale_dtype均按文档传None；pertensor/perchannel一般k_group_size=0。A16S4/A16INT8支持同scale shape/dtype的offset透传，A8W4、FP4及FP8/HiF8分支不据实现宽传参放开文档禁止的offset。

## 逻辑shape、格式标签和真实存储

四位NZ的Torch侧视图仍为打包字节形状，不能仅凭sizes判断已变成普通ND或未转换。A16W4非转置物理storage按(ceil(N/16),ceil(K/16),16,8)分配，底层逻辑4位解释会恢复每字节两值；T-CG的逻辑C0_32对应另一个标签/容器转换，不等于把INT4的NZ_C0_8直接改名。A8W4的paired MX尺度也保留规定转置stride。

## 输出所有权与Meta边界

C++的ND“直拷”路径实际直接返回输入weight；scale直传、offset和bias直传也直接共享原输入及view，不是独立副本。后续原地修改预处理输出可能改变原参数；释放或缓存策略不能按四份新Tensor估算。NZ和A8W4尺度重排路径则有新分配，分支需分别核对。

Schema未声明这些输出alias，Meta又为各项返回empty_like，占位无法证明独立存储或保留真实NZ描述。可选offset/bias未提供时对应槽无有效数据，不能当数值零使用。涉及图、功能化、参数替换与view复用时应检查实际alias与格式，不把Meta形状相同当作完整预处理等价。

## 验证

固定下游Matmul的逻辑dtype、量化粒度和转置约定，分别核对预处理前后的解码值、stride/storage格式、alias及最终矩阵乘结果。不能只检查调用成功或输出尺寸；预处理成本与稳态推理收益分开测量。

## 参数筛选、可选槽和产品的实现范围

双语公开产品为950PR/DT；固定C++分派表仅登记Ascend950，按顺序选择匹配数据流。判定函数没有提前校验全部K分组、scale长度、offset禁用条件或bias连续性，仍按公开组合使用，不能因某组合通过分派就放宽约束。k_group_size最终确实传给aclnnWeightQuantPreprocess，局部注释中“不下发”的说法不能替代实际调用。

未提供offset/bias时C++保持对应输出为未定义Tensor槽，Meta则构造weight dtype的[0]占位；公开“空Tensor”不表示有效数值零，也不保证两种路径拥有同一对象表示。传入时offset/bias及直接scale分支都共享原输入存储；ND权重也直接alias，不把文档“直拷”计作四份新缓冲。

Torch≥2.8编译分支仅在逻辑类型为FP4 E2M1时放行原生float4_e2m1fn_x2载体，INT4仍要求UINT8 packed；不能将INT8或INT32容器配上逻辑INT4就使用。MM/GMM MX A8W4要求权重与paired尺度各自具有规定转置stride，普通同shape连续Tensor不能替代。

## 预处理测试不能代替下游MatMul验收

主线测试多以全零权重/尺度检查shape、stride、内容和条件格式标签。首个A8W4样例以名为k的值直接生成字节维，未按公开逻辑K/2构造完整一致的非零量化参考；不拿变量名推断物理/逻辑维等价。

原生FP4用例比较转置ND路径的字节，但非转置NZ部分只比较shape、dtype和格式，并未检查任意非零NZ重排的解码值。其他NZ测试注释提到外部STC覆盖，未摄取或运行该外部证明。GMM、HiF8、所有bias/alias组合和完整下游MatMul结果未由此文件证明。

公开最后一个T-CG样例将本接口输出接到npu_quant_matmul，并另用npu_trans_quant_param生成y_scale；这说明权重预处理与输出量化scale是不同环节。例子没有本次计时或全模式数值验证，模型仍需同时核对解码、存储所有权及最终计算。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_weight_quant_preprocess.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/WeightQuantPreprocessKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_weight_quant_preprocess.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_weight_quant_preprocess.py)（example）
