---
type: API
title: npu_all_to_all_matmul：先交换再矩阵乘的布局契约
description: 说明 BS 分片、隐藏维拼接、可选通信输出和显式 comm_mode 的 V2 依赖。
tags:
- task.lookup
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_all_to_all_matmul.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AlltoAllMatmulKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/allto_all_matmul.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_all_to_all_matmul.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_all_to_all_matmul.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_all_to_all_matmul.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AlltoAllMatmulKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_all_to_all_matmul.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/allto_all_matmul.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp
  role: implementation
created_at: '2026-11-09T08:00:45Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a3
- '950'
---

# npu_all_to_all_matmul：先交换再矩阵乘的布局契约

## 版本与范围

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 完整产品页及包装、Meta，另查TorchAir主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` Converter。A3和950PR/DT支持训练/推理及单算子；页面只对950列图模式，不因A3能调用Eager或存在Converter就扩展其图模式支持。A2不在这两个产品页范围。

## 公共输入与配套

x1/x2用相同FP16或BF16、二维ND；x1连续，x2只支持转置产生的非连续视图。除x1首轴可为0外，其他输入不支持空Tensor。bias为一维输出列长度，可同输入dtype或FP32。world_size仅2/4/8/16，hcom为真实通信域名称、长度1..127。

A3 comm_mode为None或ai_cpu，950另可ccu；None在页面语义上使用ai_cpu。950 ccu限单机UB域，ai_cpu可跨机UB域。C++中None实际调用旧aclnn入口，显式给任何通信模式则先检查V2并调用V2；即使显式ai_cpu与None意图相同，也可能有不同交付件依赖。缺V2时不自动将显式模式改为旧调用，不能靠删除参数证明旧包支持当前所有功能。

## 接口与布局

```text
torch_npu.npu_all_to_all_matmul(x1, x2, hcom, world_size, bias=None, all2all_axes=None, all2all_out_flag=True, comm_mode=None) -> (Tensor, Tensor)
```

x1=[BS,H]，先按rank拆BS轴AlltoAll，接着Permute为[BS/r,H*r]连续布局，再乘x2=[H*r,N]并加bias。最终y=[BS/r,N]，r=world_size。all2all_axes仅None或[-2,-1]，不是任意两轴交换。

BS∈[0,2147483647]且整除r，H*r∈[2,65535]，N∈[1,2147483647]；不能仅验证普通MatMul K轴而遗漏通信后的H*r。关闭all2all_out_flag只省可选通信中间结果，不取消内部通信或Permute。

## 可选输出与图边界

True时第二项是Permute后的[BS/r,H*r]同dtype连续ND Tensor，不是原始rank优先布局的commOut。False时文档与Meta为None，C++向底层传空指针并使用无效Tensor返回占位；Schema仍写两个Tensor。不能假定关闭时返回0元素的普通Tensor，或无条件读取其shape。

TorchAir主线Converter将None axes补成[-2,-1]并始终构建两个GE输出，将flag下传；它没有在返回处显式改第二项为None。此静态差异不证明运行故障，但False路径需核对最终Python返回结构，不能只凭Meta认定所有后端完全一致。图模式仅使用页面列出的950范围。

- [先矩阵乘再AlltoAll](npu_matmul_all_to_all.md)：通信顺序与切分轴不同。

## 验证

先用相同rank顺序的分步通信、Permute和MatMul作为参考，检查结果位置与数值，再比较融合调用；不能只比较numel或把两种通信顺序互换。另检查bias的加入阶段、空batch、真实转置视图和所用CANN接口是否存在。训练场景支持不等于任意梯度路径已验证。本次仅静态审阅，未执行上游代码或NPU多卡/图测试。

- [软件栈版本与来源身份](../../concepts/frameworks/ascend_software_stack_baselines.md)

## 双语bias差异与发布签名

主线中文允许FP16输入配FP16/FP32 bias、BF16输入配BF16/FP32 bias，主线英文及发布中文仍写FP16配FP16、BF16配FP32。两版GE检查允许同输入dtype或FP32，但转换器接受不等于所有产品已公开同一范围；已有共同输入段按主线中文理解，部署时保留语言/版本差异。

发布仅公开A3并明确不支持图模式，Schema、Meta、C++和GE都没有comm_mode参数；主线950图模式和显式模式不能回推到发布。主线显式comm_mode要求V2执行符号和相应GetWorkspaceSize符号都存在，错误提示升级包没有提供能据此推断的最低精确CANN版本。None走旧入口也不证明旧交付件支持所有新功能。

C++只有二维、卡数和BS整除等局部检查，Meta也没有覆盖完整K关系、dtype、bias、stride、hcom和轴组合。允许传入或推断出shape不能作为合法部署证明。

## 参考测试的通信前提

两版测试逐字节相同，仅950两卡BF16及非零BF16 bias。参考计算先在父进程调用all_to_all_single，本文件的进程组初始化却位于后续子入口；文件内没有自足的父进程通信域准备。该参考还依赖NPU矩阵乘，不能作为独立CPU黄金结果或完整可运行部署证明。

测试只比较最终y，没有验收可选通信输出、关闭flag、空BS、真实转置视图、图模式、V2或A3。本文没有运行这些多进程或设备代码。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_all_to_all_matmul.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AlltoAllMatmulKernelNpuOpApi.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/allto_all_matmul.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_all_to_all_matmul.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_all_to_all_matmul.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_all_to_all_matmul.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AlltoAllMatmulKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_all_to_all_matmul.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/allto_all_matmul.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp)（implementation）
