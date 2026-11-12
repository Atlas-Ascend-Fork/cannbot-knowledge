---
type: API
title: SGL 张量并行RMSNorm的局部统计与全局缩放
description: 串联 fused_variance、跨rank AVG 与 fused_rsqrt_mul，区分两个接口的通道约束。
tags:
- task.implementation
- topic.parallelism
- topic.compute.normalization
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/fused_variance.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/fused_rsqrt_mul.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/torch_native/norm/rmsnorm_split.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/norm/rmsnorm_split.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py
  role: implementation
created_at: '2026-11-08T11:03:33Z'
updated_at: '2026-11-09T11:12:51Z'
platforms:
- a2
- a3
- '950'
aliases:
- fused_variance
- fused_rsqrt_mul
---

# SGL 张量并行RMSNorm的局部统计与全局缩放

## 调用入口

```python
from sgl_kernel_npu.operators.norm import fused_variance

def fused_variance(x, *, impl="auto"):
    ...

from sgl_kernel_npu.operators.norm import fused_rsqrt_mul

def fused_rsqrt_mul(x, variance, weight, eps=1e-6, *, impl="auto"):
    ...
```

## 必须保留的通信阶段

`fused_variance(x)`计算每token的局部均方 `sum(x*x)/C`，auto/triton输出`[B,L,1]`（torch_native按输入前导维返回末维为1的统计）；它不是完整RMSNorm。在均匀通道分片的TP路径，调用方须先对该输出做跨rank `all_reduce(AVG)`，再调用 `fused_rsqrt_mul(x,variance,weight,eps)` 得到 `x*rsqrt(variance+eps)*weight`。

下表约束适用于impl="auto"/"triton"，不是所有公共后端的统一准入：

| 项目 | fused_variance | fused_rsqrt_mul |
| --- | --- | --- |
| x | FP32连续NPU `[B,L,C]`，各维正 | FP32连续NPU `[B,L,C]` |
| 通道约束 | C为2的幂 | C不要求2的幂，尾部有mask |
| 额外输入 | 无 | variance为按行连续存储的`[B,L,1]`或`[B*L]`；连续weight `[C]`，均同设备同dtype |
| 返回 | 同dtype的新局部统计 | 同shape同dtype的新归一化结果 |

两个公共入口均不检查输入或执行隐式通信；auto与triton相同且不失败回退。输入及中间值按有限FP32使用，不能把接口名variance解释成减均值方差。

## 参考与验证

torch_native用独立PyTorch表达式复现两阶段；其中fused_variance支持任意前导维度、非连续输入，C不要求2的幂，输出保持前导维并在末维保留1。fused_rsqrt_mul按PyTorch广播计算，不受Triton variance线性连续寻址要求约束；fused_rsqrt_mul将一维统计整理为 `[B,L,1]`。单卡对照只能验证数学和布局；多卡还须验证所有rank参与AVG且统计口径一致。缺少AVG的本地结果不得作为全局归一化参考。分别核对统计与最终输出，使用FP32容差，检查输入未修改。

## 旧模块副本与设备属性缓存

固定提交仍保留 `sgl_kernel_npu.norm.rmsnorm_split` 的 `fused_variance / fused_rsqrt_mul`。与 `implementation.triton.norm.rmsnorm_split` 逐项对照，差异只有设备属性helper的导入位置及部分说明文本；函数、JIT装饰器、autotune配置和Host参数/全局量一致。两个helper的get_device_properties函数及其依赖也相同：读取当前NPU，经Triton driver查询num_aicore/num_vectorcore，要求两者为正。它们是独立模块中的源码副本，并非同一个Python函数对象的转发别名；不保证共享JIT/autotune缓存，也不把旧入口存在作为公共后端准入扩大的依据。

get_device_properties使用无参数functools.cache，缓存键不含device。两个helper模块各自保存首次成功查询的核数；在同一进程切换设备后，不能假定会重新查询新设备拓扑。该事实限定固定源码，未测量异构多卡进程或任何性能影响。

[局部均方的A2/A3源码卡](/model/inference/operators/direct/nn/norm/sgl_variance.md)、[950源码卡](/model/inference/operators/direct/nn/norm/sgl_variance_950.md)。

[rsqrt与权重缩放的A2/A3源码卡](/model/inference/operators/direct/nn/norm/sgl_rsqrt_mul.md)、[950源码卡](/model/inference/operators/direct/nn/norm/sgl_rsqrt_mul_950.md)。


## 固定来源与验证状态

- [norm/fused_variance.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/fused_variance.md)
- [norm/fused_rsqrt_mul.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/fused_rsqrt_mul.md)
- [构建架构与产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md)及[SDK架构表](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json)。文档arch22对应本版本2201构建族A2/A3，arch35对应3510的950；具体子接口限制以上文为准。

本卡为固定提交的公开API契约蒸馏，未展开Host/Tiling/Device全链路。本次知识提取未执行编译、真机、数值或性能测试；上游报告的支持和用例结果不代表本次复测。
