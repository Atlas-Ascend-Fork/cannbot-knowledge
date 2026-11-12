---
type: API
title: SGL 无权重RMSNorm的输入与精度边界
description: 说明 fused_rmsnorm_without_weight 的连续三维输入、二次幂通道和低精度平方边界。
tags:
- task.implementation
- topic.precision
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/fused_rmsnorm_without_weight.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/norm/rmsnorm_without_weight.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_without_weight.py
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
- fused_rmsnorm_without_weight
---

# SGL 无权重RMSNorm的输入与精度边界

## 调用入口

```python
from sgl_kernel_npu.operators.norm import fused_rmsnorm_without_weight

def fused_rmsnorm_without_weight(x, eps, *, impl="auto"):
    ...
```

## 接口语义

对 `[B,L,C]` 每行执行 `x*rsqrt(sum(x*x)/C+eps)`，不带权重和bias，返回同shape同dtype的新Tensor。x支持FP16/BF16/FP32，Triton要求NPU上的连续三维布局，C必须为2的幂；eps由调用方提供并建议有限正数。输入不被修改。

auto对应triton，公共入口直接透传，不检查输入、不自动回退。Triton按token数自动选择行块、以向量核数为grid。kernel的平方沿用输入类型，FP16与FP32参考的数值差异可能更明显；BF16归约通常被Triton提升为FP32，不代表整个计算都与FP32平方等价。

## 验证与边界

torch_native先转FP32求均方和rsqrt，再写回输入dtype，可处理一般前导维及非连续视图；这不是Triton准入扩大。按dtype设置容差并覆盖大幅值，不能因语义同为RMSNorm就省掉中间精度差异。NaN跨后端行为未定义；接口不量化，也不返回方差。包导入仍依赖torch_npu和原生库。

## 旧模块副本与设备属性缓存

固定提交仍保留 `sgl_kernel_npu.norm.rmsnorm_without_weight` 的 `fused_rmsnorm_without_weight`。与 `implementation.triton.norm.rmsnorm_without_weight` 逐项对照，差异只有设备属性helper的导入位置及部分说明文本；函数、JIT装饰器、autotune配置和Host参数/全局量一致。两个helper的get_device_properties函数及其依赖也相同：读取当前NPU，经Triton driver查询num_aicore/num_vectorcore，要求两者为正。它们是独立模块中的源码副本，并非同一个Python函数对象的转发别名；不保证共享JIT/autotune缓存，也不把旧入口存在作为公共后端准入扩大的依据。

get_device_properties使用无参数functools.cache，缓存键不含device。两个helper模块各自保存首次成功查询的核数；在同一进程切换设备后，不能假定会重新查询新设备拓扑。该事实限定固定源码，未测量异构多卡进程或任何性能影响。

[无权重RMSNorm的A2/A3源码卡](/model/inference/operators/direct/nn/norm/sgl_rmsnorm_without_weight.md)、[950源码卡](/model/inference/operators/direct/nn/norm/sgl_rmsnorm_without_weight_950.md)。


## 固定来源与验证状态

- [norm/fused_rmsnorm_without_weight.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/fused_rmsnorm_without_weight.md)
- [构建架构与产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md)及[SDK架构表](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json)。文档arch22对应本版本2201构建族A2/A3，arch35对应3510的950；具体子接口限制以上文为准。

本卡为固定提交的公开API契约蒸馏，未展开Host/Tiling/Device全链路。本次知识提取未执行编译、真机、数值或性能测试；上游报告的支持和用例结果不代表本次复测。
