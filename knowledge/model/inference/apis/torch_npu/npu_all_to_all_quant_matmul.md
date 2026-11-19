---
type: API
title: npu_all_to_all_quant_matmul：交换后动态量化与 MX
description: 说明动态量化和 MX 的输入区别、GE 必填量化类型、可选输出及右 scale 文档缺口。
tags:
- task.lookup
- topic.parallelism
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_all_to_all_quant_matmul.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AlltoAllQuantMatmulKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/allto_all_quant_matmul.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_all_to_all_quant_matmul.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_all_to_all_quant_matmul.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AlltoAllQuantMatmulKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_all_to_all_quant_matmul.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/allto_all_quant_matmul.py
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

# npu_all_to_all_quant_matmul：交换后动态量化与 MX

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
npu_all_to_all_quant_matmul(Tensor x1, Tensor x2, str hcom, int world_size, *, bool all2all_out_flag=True, Tensor? bias=None, Tensor? x1_scale=None, Tensor? x2_scale=None, Tensor? common_scale=None, Tensor? x1_offset=None, Tensor? x2_offset=None, int? x1_quant_mode=None, int? x2_quant_mode=None, int? common_quant_mode=None, int[]? group_sizes=None, int[]? all2all_axes=None, int? comm_quant_dtype=None, int? x1_quant_dtype=None, int? x1_dtype=None, int? x2_dtype=None, int? x1_scale_dtype=None, int? x2_scale_dtype=None, int? output_scale_dtype=None, int? comm_scale_dtype=None, int? y_dtype=None, str? comm_mode=None) -> (Tensor, Tensor)
```

公开入口为torch_npu.npu_all_to_all_quant_matmul；星号后均为关键字参数。x1逻辑[BS,H]先AlltoAll/Permute为[BS/r,H*r]，再与x2逻辑[H*r,N]矩阵乘，返回(y,all2all_out)。y=[BS/r,N]；True时第二项是通信及Permute后、动态量化前的输入布局，同x1 dtype，不能当作新量化后的FP8值或其scale。

BS∈[2,2147483647]且整除r，H*r∈[1,65535]，N∈[1,2147483647]；all2all_axes仅None或[-2,-1]。False不取消通信，只取消额外输出；文档/Meta为None，C++使用空指针及无效Tensor占位，GE Converter仍构造两个GE输出，需验证实际返回结构。

## 动态K-C与MX输入

|(x1_quant_mode,x2_quant_mode)|输入及scale|关键差异|
|--|--|--|
|(7,2) 动态K-C|x1为FP16/BF16，x2为FP8；x1_scale=None，x2_scale为FP32[N]|先通信，再动态生成左量化scale|
|(6,6) MX|两输入FP8或两输入FP4，两个E8M0 scale均需提供|通信同时交换左scale；x2必须.t()形成逻辑[H*r,N]，H需64整除|

动态路径x1_quant_dtype指定生成FP8的E4M3FN或E5M2；C++None默认E5M2，而主线GE Converter明确拒绝None，因此图模式应显式传目标FP8 dtype。不能把前一接口(3,2)的FP8左输入及预先生成scale套入本接口(7,2)。

MX左scale按页面为[BS,ceil(H/64),2]，会随x1通信及Permute。右scale参数行却写[BS,ceil(H*r/64),2]，其中BS与右矩阵输出通道N关系未说明；包装与Converter没有给出能独立消除此歧义的scale形状检查。本卡保留该缺口，不把它自动改成已验证的N维配方；MX集成需核对目标交付件的算子规范与实际分组，不以文档一行直接配shape。

MXFP4需指定两输入FP4与两scale E8M0。实现还存在按x2为INT32分配N*8的分支，但公开产品矩阵只列FP8/FP4，不能据分支存在扩展INT4支持，也不能把它误当UINT8打包FP4的N规则。GE对FP4通信输出另有回打包，比较返回物理shape而非只看逻辑H*r。

- [先量化矩阵乘后交换](npu_quant_matmul_all_to_all.md)

## 验证

将目标模式拆成通信、重排、量化/反量化和MatMul参考，检查scale对应的rank/token/channel、bias施加位置、FP4逻辑/物理shape及输出dtype，再比较同负载稳态性能。训练场景支持不等于任意autograd或高层并行组合已验证。本次仅静态审阅，未执行上游代码、NPU、多卡、梯度或性能测试。

- [软件栈版本与来源身份](../../concepts/frameworks/ascend_software_stack_baselines.md)

## 发布GE与主线MX表示的变化

发布实现和转换器虽有该名称，但没有comm_mode关键字，其MX GE只接受两FP8输入，未含主线的UINT8 FP4形状扩展及通信输出回打包。不能把主线公开FP4矩阵或950图样例直接套入发布；主线配套也仍需按实际版本核对。

主线GE只接受模式(7,2)/(6,6)，K-C要求显式x1_quant_dtype；C++省略它却默认E5M2。Schema的None与Converter函数默认值不是同一层，图调用需显式填完整有效模式和类型。主线MX scale要求UINT8承载并显式E8M0，发布会默认补scale类型，两者不能仅按同名dtype推断输入表示等价。

两版C++按INT32右矩阵将N乘8的内部旧分支，与公开UINT8承载FP4的逻辑含义不同；不由该分支扩展INT4能力。公开右scale的BS维度缺口也没有被本次读到的Meta/C++/GE完整shape校验消除，继续保留。

## 动态量化参考为何不能当验收

两版测试逐字节一致，只设950两卡BF16左矩阵、E4M3右矩阵。虽然生成x2_scale列表，子入口没有接收它，API调用也未传必需的x2_scale。参考QuantByToken还忽略传入dtype并固定转为E4M3，而API省略目标量化类型时默认E5M2；因此参考与调用没有形成同一完整量化契约。

父进程参考collective还缺少本文件内可见的初始化前提。未覆盖MX、非零FP4、可选输出False、转置、图模式或任何实际吞吐；未执行这些代码，不把有测试文件计作验证通过。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_all_to_all_quant_matmul.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AlltoAllQuantMatmulKernelNpuOpApi.cpp)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/allto_all_quant_matmul.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_all_to_all_quant_matmul.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_all_to_all_quant_matmul.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AlltoAllQuantMatmulKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_all_to_all_quant_matmul.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/allto_all_quant_matmul.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp)（implementation）
