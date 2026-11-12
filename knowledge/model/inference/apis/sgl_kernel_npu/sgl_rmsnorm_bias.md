---
type: API
title: SGL RMSNorm 加偏置及可选INT8接口
description: 说明 rmsnorm_bias 的FP32归一化、逐通道量化和arch35待验证范围。
tags:
- task.implementation
- topic.precision
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/rmsnorm_bias.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/norm/rmsnorm_bias.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_bias.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py
  role: implementation
created_at: '2026-11-08T11:03:33Z'
updated_at: '2026-11-10T07:03:17Z'
platforms:
- a2
- a3
aliases:
- rmsnorm_bias
---

# SGL RMSNorm 加偏置及可选INT8接口

## 调用入口

```python
from sgl_kernel_npu.operators.norm import rmsnorm_bias

def rmsnorm_bias(
    input,
    norm_weight,
    norm_bias,
    eps,
    quant_scale=None,
    quant_offset=None,
    *,
    impl="auto",
):
    ...
```

## 调用契约

input为同一NPU上连续 `[B,H]` FP16/BF16/FP32，B,H>0；norm_weight/norm_bias为连续 `[H]` 浮点向量，建议与input同dtype。每行计算 `input*rsqrt(mean(input**2)+eps)*weight+bias`。eps建议有限正数。未量化时输出input.dtype的新 `[B,H]` Tensor，输入不变。

quant_scale非None时进入INT8分支；quant_scale必须是与input同设备的`[H]`浮点Tensor（推荐FP32），auto/triton要求连续、按通道寻址，不支持标量广播或非连续scale；同时必须提供连续同设备`[H]`浮点quant_offset。scale为None时offset被忽略。变换为 `Y*scale+offset` 后饱和转换INT8，参考实现向零截断、范围[-128,127]，中间保持FP32。这里只定义有限输入及量化中间值，NaN跨后端转换没有约定。

## 实现和范围

auto与triton同入口，没有失败回退。公共层直接透传，不替调用方检查输入；仅quant_scale非None的INT8分支以1024元素切片遍历range(0,H,1024)，最终写回用col<H掩码；该掩码不约束al.extract_slice的源码范围。切片源长度K=next_power_of_2(H)，H<=512时K<1024却仍请求完整1024元素切片，存在逻辑切片越域边界；不能由输出掩码推断任意小H安全，也不据此断言某个编译器版本必报特定错误。非量化分支直接写回完整向量，不执行extract_slice，因此不受这项1024切片限制。torch_native允许非连续输入，但不能因此扩大Triton的布局准入。

上游支持表确认arch22；arch35标注待验证，本卡不将950列为稳定适用平台。包初始化仍依赖torch_npu与原生库。

验证时分别覆盖量化和非量化，显式用torch_native对照；INT8边界不能要求逐位相同。INT8量化分支宽度覆盖不足时先检查固定切片边界，再决定是否用于目标H。

## 旧模块副本与设备属性缓存

固定提交仍保留 `sgl_kernel_npu.norm.rmsnorm_bias` 的 `rmsnorm_bias`。与 `implementation.triton.norm.rmsnorm_bias` 逐项对照，差异只有设备属性helper的导入位置及部分说明文本；函数、JIT装饰器、autotune配置和Host参数/全局量一致。两个helper的get_device_properties函数及其依赖也相同：读取当前NPU，经Triton driver查询num_aicore/num_vectorcore，要求两者为正。它们是独立模块中的源码副本，并非同一个Python函数对象的转发别名；不保证共享JIT/autotune缓存，也不把旧入口存在作为公共后端准入扩大的依据。

get_device_properties使用无参数functools.cache，缓存键不含device。两个helper模块各自保存首次成功查询的核数；在同一进程切换设备后，不能假定会重新查询新设备拓扑。该事实限定固定源码，未测量异构多卡进程或任何性能影响。

[浮点RMSNorm偏置的A2/A3源码卡](/model/inference/operators/direct/nn/norm/sgl_rmsnorm_bias.md)、[950源码卡](/model/inference/operators/direct/nn/norm/sgl_rmsnorm_bias_950.md)。

[INT8分支的A2/A3源码卡](/model/inference/operators/direct/nn/norm/sgl_rmsnorm_bias_int8.md)、[950源码卡](/model/inference/operators/direct/nn/norm/sgl_rmsnorm_bias_int8_950.md)。


## 固定来源与验证状态

- [norm/rmsnorm_bias.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/rmsnorm_bias.md)
- [构建架构与产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md)及[SDK架构表](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json)。文档arch22对应本版本2201构建族A2/A3，arch35对应3510的950；具体子接口限制以上文为准。

本卡为固定提交的公开API契约蒸馏，未展开Host/Tiling/Device全链路。本次知识提取未执行编译、真机、数值或性能测试；上游报告的支持和用例结果不代表本次复测。
