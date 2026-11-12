---
type: API
title: SGL缩放偏移的元素数量分发与常数分支
description: 说明 fused_scale_shift 的三类shift广播、逐元素优先、scale_constant只在一条分支生效。
tags:
- task.implementation
- topic.compute.elementwise.arithmetic
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/elementwise/fused_scale_shift.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/norm/scale_shift.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/scale_shift.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py
  role: implementation
created_at: '2026-11-08T11:03:33Z'
updated_at: '2026-11-09T15:27:12Z'
platforms:
- a2
- a3
- '950'
aliases:
- fused_scale_shift
---

# SGL缩放偏移的元素数量分发与常数分支

## 调用入口

```python
from sgl_kernel_npu.operators.elementwise import fused_scale_shift

def fused_scale_shift(x, scale, shift, scale_constant=1.0, *, impl="auto"):
    ...
```

## 参数与实际分支

x为同NPU连续 `[B,L,H]` FP16/BF16/FP32，所有维正。scale按numel为1或H解释；shift按numel为1、H或B*L*H解释，均先展平，dtype可与x不同。返回同shape、x.dtype的新连续Tensor，不与输入别名，不修改输入。

| shift元素数 | 数学及额外约束 |
| --- | --- |
| 等于全部输入元素数 | 优先逐元素分支，`y=x*(scale_constant+scale)+shift`；Triton要求scale恰有H项，H=1才可单项。 |
| 不等于全部输入且为1或H | 标量/通道广播，`y=x*(1+scale)+shift`，忽略scale_constant。 |

B*L=1时通道shift也等于全输入大小，会走第一条，不能因调用者想表达通道广播就选第二条。scale_constant是有限Python实数且不接受bool，只在第一条有效。不支持按batch/帧提供多于H项的scale。

## 分发与验证

auto选择triton，无自动回退；Triton检查上述shape/dtype/连续性约定，非法输入AssertionError。显式torch_native用于精度参考，有限值按dtype容差，不承诺逐位等价。

验证覆盖scalar/channel/full shift及B*L=1的重合分支，使用scale_constant=0区分真实公式；比较输入不变和输出独立存储。不能用通用 `x*(scale_constant+scale)+shift` 作为所有分支共同参考。

## 旧scale_shift模块的同body与较弱检查

旧入口实际位于 `sgl_kernel_npu.norm.scale_shift.fused_scale_shift`，新版实现位于 `implementation.triton.elementwise.scale_shift.fused_scale_shift`。两个实际JIT `fused_scale_shift_kernel`、`fused_scale_shift_kernel_2` 的参数、装饰器和全部body相同，Host原有shape解释、元素数分支和launch常数一致；不能因旧模块挂在norm就当作归一化算法。

新版Host增加Tensor/strided浮点/同设备/连续/NPU、三维正尺寸、finite非bool scale_constant检查，并在shift.numel()==x.numel()时强制scale.numel()==H。旧Host只检查scale/shift元素数量，允许scalar scale进入该逐元素shift分支；当H>1时第二kernel实际按channel读取scale_ptr+col，而非标量广播，不能把旧Host“断言通过”视为安全调用。B*L=1的channel shift也等于全输入大小，同样走这一分支。合法交集内的两种公式和scale_constant生效条件与本卡公开合同相同。

两份get_device_properties helper具有相同实现，但分别是两个Python模块内的独立无参数functools.cache：首次成功查询当前NPU的num_aicore/num_vectorcore后缓存，key不含device。进程切换设备不保证重新读取核数，两个模块也不保证共享JIT/autotune/属性缓存；不是同一个函数对象的转发别名。

[缩放偏移完整实现A2/A3](/model/inference/operators/direct/math/math/sgl_scale_shift.md)及[950](/model/inference/operators/direct/math/math/sgl_scale_shift_950.md)可复用同Device算法；本段保留旧Host差异与缓存所有权，不改公开平台，也没有实测编译/越界或性能结果。

### 增量固定实现来源

- [python/sgl_kernel_npu/sgl_kernel_npu/norm/scale_shift.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/norm/scale_shift.py)。
- [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/scale_shift.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/scale_shift.py)。
- [python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py)。
- [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py)。

## 固定来源与验证状态

- [elementwise/fused_scale_shift.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/elementwise/fused_scale_shift.md)
- [构建架构与产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md)及[SDK架构表](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json)。文档arch22对应本版本2201构建族A2/A3，arch35对应3510的950；具体子接口限制以上文为准。

本卡为固定提交的公开API契约蒸馏，未展开Host/Tiling/Device全链路。本次知识提取未执行编译、真机、数值或性能测试；上游报告的支持和用例结果不代表本次复测。
