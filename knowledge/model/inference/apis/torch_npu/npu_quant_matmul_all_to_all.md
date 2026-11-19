---
type: API
title: npu_quant_matmul_all_to_all：量化矩阵乘后交换
description: 记录静态 K-C 与 MX 量化组合、输出列切分、转置权重和 950 通信依赖。
tags:
- task.lookup
- topic.parallelism
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_quant_matmul_all_to_all.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantMatmulAlltoAllKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/quant_matmul_allto_all.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_quant_matmul_all_to_all.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_quant_matmul_all_to_all.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantMatmulAlltoAllKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_quant_matmul_all_to_all.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/quant_matmul_allto_all.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp
  role: implementation
created_at: '2026-11-09T08:14:46Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- '950'
---

# npu_quant_matmul_all_to_all：量化矩阵乘后交换

## 版本与范围

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 完整产品页、Schema、Meta和C++包装，图转换另核对TorchAir主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c`。仅950PR/DT，页面列训练、推理、单算子和图模式；不扩展A2/A3，也不声明两主线快照已完成配套或NPU验证。

## 公共条件与数据类型

world_size只2/4/8/16，hcom为真实通信域名、长度1..127，输入输出均不支持空Tensor。x1连续二维ND，x2仅允许转置视图导致的非连续；bias可None或FP32一维输出列长度。量化模式只支持下面各接口列出的两组，不因枚举表含0..7就支持所有组合。

FP8 E4M3FN/E5M2可按页面矩阵混用，MXFP4要求两输入均为FP4。y_dtype=None默认FP32，也可显式选择FP16/BF16/FP32；这里的Torch/TorchNPU枚举不能与GE/ACL编码互换。C++将-1按默认处理，但Meta对非None直接查类型表，采用None或明确浮点dtype，不能假设所有undefined哨兵在各后端一致。

common_scale、x1_offset、x2_offset、common_quant_mode、comm_quant_dtype、output_scale_dtype、comm_scale_dtype为预留项，保持默认。GE Converter还固定common_quant_mode=0、comm_quant_dtype=-1，output_scale_dtype/comm_scale_dtype这两个预留字段不证明接口已经提供低比特通信或输出再量化功能。

## MX存储与交付件

MX用E8M0 scale，group_sizes需[1,1,32]，或在满足整除条件时推导出相同结果；其他模式分组参数不生效。三项[M,N,K]每项0..65535，C++None/空列表编码0，但GE显式非None列表必须恰有三项。FP4输入以每字节两值存储时，x1_dtype/x2_dtype指定实际FP4含义，不是自动量化/转换。

主线GE Converter的MX分支检查scale底层为UINT8，再要求x1_scale_dtype/x2_scale_dtype显式E8M0并Bitcast；不能从文档列原生E8M0就认定任何底层表示都等价入图。需核对实际scale存储和图产物。

comm_mode=None在C++调用旧aclnn入口；显式ai_cpu/ccu则要求并调用V2，缺V2不回退。页面None语义为AI CPU，ccu限单机UB域、ai_cpu可跨机UB域；不能只因None与显式ai_cpu含义接近就抹平版本依赖。

## 接口与输出布局

```text
npu_quant_matmul_all_to_all(Tensor x1, Tensor x2, str hcom, int world_size, Tensor? bias=None, Tensor? x1_scale=None, Tensor? x2_scale=None, Tensor? common_scale=None, Tensor? x1_offset=None, Tensor? x2_offset=None, int? x1_quant_mode=None, int? x2_quant_mode=None, int? common_quant_mode=None, int[]? group_sizes=None, int[]? all2all_axes=None, int? comm_quant_dtype=None, int? x1_dtype=None, int? x2_dtype=None, int? x1_scale_dtype=None, int? x2_scale_dtype=None, int? output_scale_dtype=None, int? comm_scale_dtype=None, int? y_dtype=None, str? comm_mode=None) -> Tensor
```

公开入口为torch_npu.npu_quant_matmul_all_to_all。x1逻辑[BS,H1]、x2逻辑[H1,H2]；先量化矩阵乘/反量化，再把[BS,H2]切成rank份并Permute、AlltoAll，输出[BS*r,H2/r]，r=world_size。all2all_axes仅None或[-1,-2]，H2须整除r，不能照搬先通信接口的BS整除条件。

BS*r∈[1,2147483647]，H1∈[1,65535]，H2∈[2,2147483647]。返回单个Tensor，不返回通信中间值或量化scale。

## K-C与MX参数

|模式对(x1_quant_mode,x2_quant_mode)|输入与scale|额外条件|
|--|--|--|
|(3,2) K-C|两输入FP8；x1_scale FP32[BS]、x2_scale FP32[H2]|两个scale均必传；不是动态计算左scale|
|(6,6) MX|两输入FP8或两输入FP4；E8M0 scale分别[BS,ceil(H1/64),2]、[H2,ceil(H1/64),2]|x2必须.t()后逻辑形状为[H1,H2]，group_sizes=[1,1,32]|

MXFP4另要求H1为偶数且ceil(H1/32)为偶数；x1/x2显式FP4、scale显式E8M0提示。不要为“连续化”而删除MX右矩阵要求的转置布局。C++/Meta输出列按x2.size(1)/r分配，对应转置后逻辑H2，不能照搬其他非转置FP4接口的N翻倍规则。

K-C页面公式把bias置于scale乘积之前，MX公式在分组反量化求和后加bias；这两种bias的数值空间不同，不能仅因均为FP32就复用同一偏置配方。C++省略模式时取(3,2)，入图建议显式填写允许的模式对，避免将文档Optional=None与Converter函数默认值视为同一层次。

- [先交换再动态量化矩阵乘](npu_all_to_all_quant_matmul.md)

## 验证

将目标模式拆成通信、重排、量化/反量化和MatMul参考，检查scale对应的rank/token/channel、bias施加位置、FP4逻辑/物理shape及输出dtype，再比较同负载稳态性能。训练场景支持不等于任意autograd或高层并行组合已验证。本次仅静态审阅，未执行上游代码、NPU、多卡、梯度或性能测试。

- [软件栈版本与来源身份](../../concepts/frameworks/ascend_software_stack_baselines.md)

## 默认模式、显式通信与发布图差异

两版C++均将省略模式设为(3,2)，并将y_dtype=None或-1分配为FP32；Meta对非None直接查枚举，不保证-1等哨兵可通用。主线才增加comm_mode关键字，显式值要求V2执行及GetWorkspaceSize两个符号，发布不接受该关键字。

发布GE只检查两FP8输入，MX scale可补默认E8M0；主线新增FP4容器形状扩展，并要求两scale实际UINT8及显式逻辑E8M0。GE对子模式的检查不等于完整形状、转置或跨rank合法性，公开的右矩阵转置、ceil(H1/32)偶数等条件仍需逐项保持。

预留common_quant_mode与comm_quant_dtype在GE分别固定0/-1，output_scale_dtype与comm_scale_dtype没有进入计算节点；C++接受这些形参不表示公开低比特通信或输出再量化已实现。group_sizes空列表在C++编码0、GE却拒绝，跨模式应采用共同合法输入。

## 固定测试的分组和尺度错误

两版测试除末尾空行相同，仅950两卡E4M3及FP32尺度/bias。调用显式传group_sizes=[0]，必然触发三元素分组检查，不能据“测试未skip”判断可运行。参考又把shape=[BS]的左尺度直接乘[BS,H2]矩阵，本例BS=16、H2=32不能按预期行广播，应明确增加通道广播轴才能构造独立正确参考。

参考含父进程collective而文件未给出其通信域初始化前提，也没有MX、FP4、图、空输入或不同卡数的验收。本文仅静态确认这些缺口，未运行上游代码或设备测试。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_quant_matmul_all_to_all.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantMatmulAlltoAllKernelNpuOpApi.cpp)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/quant_matmul_allto_all.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_quant_matmul_all_to_all.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_quant_matmul_all_to_all.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantMatmulAlltoAllKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_quant_matmul_all_to_all.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/quant_matmul_allto_all.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp)（implementation）
