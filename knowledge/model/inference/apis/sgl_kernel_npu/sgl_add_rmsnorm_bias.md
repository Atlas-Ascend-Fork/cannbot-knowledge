---
type: API
title: SGL 残差相加与RMSNorm偏置融合接口
description: 明确 add_rmsnorm_bias 的输入dtype残差和、FP32归一化、双返回值以及量化切片边界。
tags:
- task.implementation
- topic.precision
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/add_rmsnorm_bias.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/add_rmsnorm_bias.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/norm/add_rmsnorm_bias.py
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
- '950'
aliases:
- add_rmsnorm_bias
---

# SGL 残差相加与RMSNorm偏置融合接口

## 调用入口

```python
from sgl_kernel_npu.operators.norm import add_rmsnorm_bias

def add_rmsnorm_bias(
    input,
    residual,
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

## 语义和返回值

先在input.dtype下计算 `A=input+residual`，再以FP32对A逐行RMSNorm、乘norm_weight、加norm_bias。返回 `(output,add_output)`：add_output保留输入dtype的残差和，output在非量化分支为输入dtype，在量化分支为INT8。两者均是新 `[B,H]` Tensor，不原地修改input或residual。

input为连续同NPU二维FP16/BF16/FP32，B,H>0；residual同shape并建议同dtype；weight/bias为同设备连续 `[H]` 浮点向量。eps建议有限正数。

## 可选量化和分发

quant_scale非None时，quant_scale和quant_offset均须为 `[H]` 浮点Tensor、与input同设备，且必须同时提供二者。auto/triton分支还要求量化向量连续，不提供标量广播或stride寻址；torch_native仍按自身参考路径处理。计算 `Y*scale+offset` 后饱和INT8；torch_native以FP32中间值向零截断到[-128,127]。quant_scale为None时不使用offset。输入和转换中间值按有限值使用，NaN转换没有跨后端保证。

auto选择triton而非动态回退；公共层不做输入检查或连续化。实际launcher取BLOCK_SIZE=next_power_of_2(H)、COL_BLOCK_SIZE=2048、n_rows=min(B,向量核数)，每次调用普通`@triton.jit`入口；它没有维护显式的已编译kernel字典。固定API文档把`(n_rows,hidden_size,eps,BLOCK_SIZE,COL_BLOCK_SIZE,SCALE)`描述为缓存键，但Triton内部specialization/缓存合同不在该固定实现中，不能把这组文档参数写成已还原的真实缓存键。

量化的`al.extract_slice(buffered_values,(block_offset,),(2048,),(1,))`始终请求2048元素；store的列mask不缩短这一slice。H较小导致BLOCK_SIZE<2048时，slice请求尺寸超过源逻辑向量，具体工具链准入与结果未验证，不能用输出mask推导已安全覆盖。torch_native支持非连续输入，但不改变Triton的连续存储和量化切片边界。

## 验证信号

同时比较两个返回值：add_output应与输入dtype残差相加一致，归一化/量化输出按适合dtype的容差与显式torch_native比较。FP16/BF16残差相加后的舍入是接口语义，不能把FP32相加当等价参考。

## 旧模块映射与独立Gemma外部入口

固定提交的旧 `sgl_kernel_npu.norm.add_rmsnorm_bias.add_rmsnorm_bias` 与 `implementation.triton.norm.add_rmsnorm_bias.add_rmsnorm_bias`，Host参数/default、JIT `add_rmsnorm_bias_kernel`、装饰器、launch形状和数学body相同；差异是设备属性helper导入路径，旧模块还导入torch_npu供下述另一函数使用。旧入口没有impl分发；同body映射不意味着扩大当前公共API的合法dtype、layout、量化切片或平台范围。

两份get_device_properties helper具有相同实现，但分别是两个Python模块内的独立无参数functools.cache：首次成功查询当前NPU的num_aicore/num_vectorcore后缓存，key不含device。进程切换设备不保证重新读取核数，两个模块也不保证共享JIT/autotune/属性缓存；不是同一个函数对象的转发别名。

该旧模块另有 `add_gemma_rms_norm(hidden_state,weight,residual,variance_epsilon)`，它直接调用 `torch_npu.npu_add_rms_norm(hidden_state,residual,1.0+weight,variance_epsilon)`，取三返回值中的norm_output与add_output，丢弃中间统计。它不是上述Triton bias融合kernel的另一名字：gamma为原始Gemma偏移加1，没有独立norm_bias或本卡INT8路径。表达式1.0+weight在weight自身dtype中求值，BF16附近1的舍入会进入实际gamma；不能改写为先FP32加1后再归一化而声称位级等价。此固定文件的docstring明确保留这种低精度有效scale选择。

这里仅闭合了wrapper、参数表达式和返回选择；torch_npu.npu_add_rms_norm核心Device实现不在该固定源码集合，不能把它记为完整Triton/VV Operator、source_closed或假定支持相同平台。它也不因函数名中add而提供任意residual省略合同。

[浮点实现A2/A3](/model/inference/operators/direct/nn/norm/sgl_add_rmsnorm_bias.md)、[950](/model/inference/operators/direct/nn/norm/sgl_add_rmsnorm_bias_950.md)，以及[INT8实现A2/A3](/model/inference/operators/direct/nn/norm/sgl_add_rmsnorm_bias_int8.md)、[950](/model/inference/operators/direct/nn/norm/sgl_add_rmsnorm_bias_int8_950.md)保存自有Triton body；这些链接不关闭上述外部Gemma核心边界。本次仅静态读取，未执行编译或数值验证。

### 增量固定实现来源

- [python/sgl_kernel_npu/sgl_kernel_npu/norm/add_rmsnorm_bias.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/norm/add_rmsnorm_bias.py)。
- [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/add_rmsnorm_bias.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/add_rmsnorm_bias.py)。
- [python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py)。
- [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py)。

## 固定来源与验证状态

- [norm/add_rmsnorm_bias.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/add_rmsnorm_bias.md)
- [构建架构与产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md)及[SDK架构表](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json)。文档arch22对应本版本2201构建族A2/A3，arch35对应3510的950；具体子接口限制以上文为准。

本卡为固定提交的公开API契约蒸馏，未展开Host/Tiling/Device全链路。本次知识提取未执行编译、真机、数值或性能测试；上游报告的支持和用例结果不代表本次复测。
