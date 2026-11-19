---
type: API
title: npu_group_norm_swish：缩放、反向分组与确定性
description: 说明同 dtype 仿射、每组通道数不超过4000的训练约束及 A2/A3/950 的反向确定性差异。
tags:
- task.lookup
- topic.compute.normalization
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_group_norm_swish.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_group_norm_swish.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_group_norm_swish.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml
  role: implementation
created_at: '2026-11-09T06:17:11Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
- '950'
---

# npu_group_norm_swish：缩放、反向分组与确定性

## 版本与范围

依据 OpPlugin 固定主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的接口产品页及同提交 Schema，仅描述下列产品和参数路径，不回推到发布快照。文档支持、来源配套和设备验证分别核对。

## 接口

```text
npu_group_norm_swish(input, num_groups, weight, bias,
    eps=1e-5, swish_scale=1.0) -> (y, mean, rstd)
```

先GroupNorm，再以swish_scale控制y/(1+exp(-scale*y))，默认1。input为2..8维FP16/BF16/FP32，第1轴C能被num_groups整除；weight/bias均为必填一维C元素，dtype与input相同，不能借用SiLU接口允许高精度仿射的规则。input、weight、bias不支持Inf、-Inf或NaN。

y是激活后结果，同input形状/dtype；mean/rstd为(N,num_groups)，dtype同input。需要反向时C/num_groups≤4000，纯推理不受此条限制，不能把训练约束套到全部前向，也不能只用前向通过证明反向有效。

前向默认确定性；A2/A3反向默认非确定性，950反向默认确定性，需要可重复梯度时按该版本确定性开关核验。num_groups=1的归一化域覆盖本样本非batch轴，不是任意常见尾轴LayerNorm的无条件替代；组数=C则按通道归一化。

- [SiLU 接口的不同仿射与图模式限制](../../../inference/apis/torch_npu/npu_group_norm_silu.md)


## 核验

按同一计算顺序、激活模式和量化参数建立参考，检查输出数量、dtype、shape与别名；训练还需验证反向及保存的中间值。再比较正常负载的稳态时间和内存。本卡未执行算子、图编译或设备性能测试。

## 发布确定性提示与主线950DT差异

发布中文仅A2/A3训练，并提示反向需要确定性时设置开关；主线中英文仅新增950DT，未列950PR，进一步明确前向默认确定性、A2/A3反向默认非确定性而950DT反向默认确定性。两个版本的清单和接口页分别消费，不因主线总清单未列本名便撤销接口提示。

两版生成式声明指定NCHW、eps无值取1e-5、swish_scale无值取1.0、激活swish=True，统计shape=(N,num_groups)、dtype按weight；公开要求全部同dtype，Meta按input给统计在该共同子集一致。反向传原input、weight、bias、mean/rstd，不从文档“保存y”省略实际反向所需输入。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_group_norm_swish.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_group_norm_swish.md)（primary）

- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_group_norm_swish.md)（constraint）

- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml)（implementation）

- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml)（implementation）
