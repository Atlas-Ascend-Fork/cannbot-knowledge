---
type: API
title: npu_fused_matmul：950 融合类型、广播与 HF32
description: 说明按 fused_op_type 区分维数、bias、x3 和输出类型，明确 FP32 输入必须开启 HF32。
tags:
- task.lookup
- topic.compute.composite
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_matmul.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modeling_deepseek.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_fused_matmul.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_fused_matmul.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FusedMatmulKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_fused_matmul.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedMatmulKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/fused_matmul.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/fused_matmul.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_utils/check_platform.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/check_platform.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp
  role: implementation
created_at: '2026-11-09T01:58:15Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- '950'
---

# npu_fused_matmul：950 融合类型、广播与 HF32

## 版本与范围

本文依据 `ascend_main_candidate` 中 OpPlugin 的固定主线提交；该候选的软件配套尚未确认。不能据此推定 26.0.0 发布组合支持此接口或下列参数。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_fused_matmul(x1, x2, *, bias=None, x3=None, fused_op_type) -> Tensor
```

按 fused_op_type 融合矩阵乘与后处理；公开原型要求显式传关键字，Schema另有空字符串默认值。"" 不做后处理，"16cast32" 输出 FP32；其他模式通常输出与 x1 同 dtype。add/mul 在 matmul+bias 后与 x3 运算，gelu_erf/gelu_tanh 不接受有效 bias，relu 可使用 bias。

## 参数与组合限制

- x1/x2 为同 dtype ND，支持 FP16/BF16/FP32、非连续；FP32 路线必须开启 HF32，不能作为严格全精度 FP32 替代。
- ""/relu 支持 2–6 维；add/mul 支持二维或三维；GELU/16cast32 限二维。归约轴相等，batch 满足广播或保持一致。
- add/mul 必须提供与 x1 同 dtype 的 x3，其余模式 x3 必须 None。x3 可与输出同 shape；三维输出允许 (M,N) 或 (1,M,N) 的 batch 广播，不允许 M/N 广播。
- bias 连续、形状 (N,) 或 (1,N)，只在 ""/relu/add/mul 生效；FP16 输入需 FP16 bias，BF16 可配 BF16/FP32 bias。GELU 只支持 FP16/BF16 输入。
- 来源确认单算子与静态图；不从其他接口的动态图能力推定本接口支持任意 dynamic=True。

## 验证与模型关联

按确切融合类型和运算顺序对比参考，检查 x3 的 batch 广播与 bias dtype；HF32 单独设精度门槛，再测量融合净收益。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modeling_deepseek.py#L408)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## 发布实现、主线精度分支与Meta输出

主线双语公开950PR/DT。发布快照也有同名C++、Meta和测试，但不能据代码存在把本次主线公开的每种组合回推到发布产品契约。两版Schema的fused_op_type默认为空字符串，公开原型却要求显式提供；使用时区分文档原型和dispatcher默认值。

两版C++都按批轴广播推导形状，16cast32时分配FP32，其余沿用输入类型；两版Meta则始终返回输入dtype，没有实现16cast32的FP32分支。Meta通过不证明这一模式的图类型与Eager一致。分配函数没有完整校验所有融合类型的rank、bias和x3范围，不能据较宽的分配逻辑扩充公开组合。

主线新增兼容精度分支：TORCH_NPU_USE_COMPATIBLE_IMPL=1，并且add/mul的x、x2、x3均为相同FP16/BF16时，将Cube模式覆盖为USE_FP32_ADD=4；其他情形继续使用HF32及全局透传设置取得的模式。该环境变量指针在函数首次读取时缓存，不承诺进程运行中修改变量立即切换。此处记录选择条件，没有测量其精度或收益，也不把它等同16cast32输出模式。

## 图转换与测试的限度

两固定TorchAir转换器均先检查is_arch35，再生成FusedMatMul并传HF32开关；未满足门控时直接返回。主线平台helper比发布多识别Ascend350字符串，但这不扩充本接口公开950PR/DT的产品支持。转换器存在也不是主线三仓已配套的证明。

两版测试各只有二维FP16的add、mul、gelu_erf三例，对照也是NPU上的普通MatMul/激活组合。没有覆盖bias、x3批广播、HF32、16cast32、兼容环境标记或训练梯度；公开图样例还设置suppress_errors=True并随机选择一个模式，不能把打印成功当作所有模式完整捕获的证据。

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_matmul.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_fused_matmul.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_fused_matmul.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FusedMatmulKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_fused_matmul.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedMatmulKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/fused_matmul.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/fused_matmul.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_utils/check_platform.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/check_platform.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp)（implementation）
