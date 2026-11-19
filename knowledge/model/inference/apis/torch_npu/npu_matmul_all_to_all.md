---
type: API
title: npu_matmul_all_to_all：先矩阵乘再交换的输出切分
description: 记录输出列整除、AlltoAll Permute 顺序及 A3/950 的 Eager 与图模式范围。
tags:
- task.lookup
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_matmul_all_to_all.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MatmulAlltoAllKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/matmul_allto_all.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_matmul_all_to_all.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_matmul_all_to_all.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_matmul_all_to_all.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MatmulAlltoAllKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_matmul_all_to_all.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/matmul_allto_all.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp
  role: implementation
created_at: '2026-11-09T08:00:45Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a3
- '950'
---

# npu_matmul_all_to_all：先矩阵乘再交换的输出切分

## 版本与范围

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 完整产品页及包装、Meta，另查TorchAir主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` Converter。A3和950PR/DT支持训练/推理及单算子；页面只对950列图模式，不因A3能调用Eager或存在Converter就扩展其图模式支持。A2不在这两个产品页范围。

## 公共输入与配套

x1/x2用相同FP16或BF16、二维ND；x1连续，x2只支持转置产生的非连续视图。除x1首轴可为0外，其他输入不支持空Tensor。bias为一维输出列长度，可同输入dtype或FP32。world_size仅2/4/8/16，hcom为真实通信域名称、长度1..127。

A3 comm_mode为None或ai_cpu，950另可ccu；None在页面语义上使用ai_cpu。950 ccu限单机UB域，ai_cpu可跨机UB域。C++中None实际调用旧aclnn入口，显式给任何通信模式则先检查V2并调用V2；即使显式ai_cpu与None意图相同，也可能有不同交付件依赖。缺V2时不自动将显式模式改为旧调用，不能靠删除参数证明旧包支持当前所有功能。

## 接口与布局

```text
torch_npu.npu_matmul_all_to_all(x1, x2, hcom, world_size, bias=None, all2all_axes=None, comm_mode=None) -> Tensor
```

x1=[BS,H1]，x2=[H1,H2]；先本rank矩阵乘并加bias，再将[BS,H2]视为[BS,r,H2/r]并Permute为[r,BS,H2/r]，最后AlltoAll得到[BS*r,H2/r]连续ND输出。all2all_axes仅None或[-1,-2]，与先通信版本的[-2,-1]相反。

BS*r∈[0,2147483647]，H1∈[1,65535]，H2∈[2,2147483647]且整除r。C++和Meta检查的是x2第1轴能被world_size整除；这里不要求BS本身整除r。不要照搬[先AlltoAll再MatMul](npu_all_to_all_matmul.md)对BS的整除条件。

## 图转换与验收

主线Converter把None axes补成[-1,-2]，按FP16/BF16输入和同dtype/FP32 bias构造GE MatmulAlltoAll，量化参数固定无量化；不能通过该普通入口传低精度scale，另有量化接口。Tensor的逻辑H1/H2应与Meta规格一致，转置标志在包装与Converter中均为False，支持转置视图不意味着可传反向逻辑shape。

输出rank块顺序由真实通信域决定；验证应逐rank比较数值与位置，避免allclose在错误拼接之后掩盖分发错误。页面950图示例是调用方式，不能当作这两个主线快照已配套运行的证据。

## 验证

先用相同rank顺序的分步通信、Permute和MatMul作为参考，检查结果位置与数值，再比较融合调用；不能只比较numel或把两种通信顺序互换。另检查bias的加入阶段、空batch、真实转置视图和所用CANN接口是否存在。训练场景支持不等于任意梯度路径已验证。本次仅静态审阅，未执行上游代码或NPU多卡/图测试。

- [软件栈版本与来源身份](../../concepts/frameworks/ascend_software_stack_baselines.md)

## 发布整除检查和公开范围

主线C++与Meta增加x2输出列整除world_size的检查；发布仅整数除法分配，并未显式检查整除。发布未报错或能推导shape不能放宽文档要求，输出布局始终按计算后AlltoAll的H2/r切分，不能从先通信版本搬来BS整除条件。

主线中文bias允许同输入dtype或FP32，主线英文和发布中文仍分别限定FP16配FP16、BF16配FP32；两GE接受更宽范围也不替代产品契约。发布A3明确单算子且不支持图模式，没有comm_mode关键字；主线950支持图模式不向该发布范围传播。

显式通信模式在主线要求V2及对应GetWorkspaceSize符号；未指定仍用旧入口。该符号门控不说明一个精确最低版本，也不自动校验跨rank一致性或底层算子完整能力。

两版测试仅空白不同，只有950四卡BF16+bias，参考在父进程先做collective却没有文件内可见的父域初始化前提。未建立A3、图、空BS、转置、不同bias或V2的覆盖，未运行该测试。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_matmul_all_to_all.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MatmulAlltoAllKernelNpuOpApi.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/matmul_allto_all.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_matmul_all_to_all.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_matmul_all_to_all.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_matmul_all_to_all.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MatmulAlltoAllKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_matmul_all_to_all.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/matmul_allto_all.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp)（implementation）
