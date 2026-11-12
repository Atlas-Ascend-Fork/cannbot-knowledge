---
type: API
title: SGL分组LayerNorm/RMSNorm与SiLU门控接口
description: 说明 layer_norm_fwd 的门控顺序、group-major统计布局、输出复用和被忽略的activation参数。
tags:
- task.implementation
- topic.compute.normalization
- topic.memory
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/layer_norm_fwd.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
  role: supporting
created_at: '2026-11-08T11:03:33Z'
updated_at: '2026-11-08T11:03:33Z'
platforms:
- a2
- a3
- '950'
aliases:
- layer_norm_fwd
---

# SGL分组LayerNorm/RMSNorm与SiLU门控接口

## 调用入口

```python
from sgl_kernel_npu.operators.norm import layer_norm_fwd

def layer_norm_fwd(
    x,
    weight,
    bias,
    eps,
    z=None,
    out=None,
    group_size=None,
    norm_before_gate=True,
    is_rms_norm=False,
    activation=None,
    *,
    impl="auto",
):
    ...
```

## 计算与分组

输入x `[M,N]` 按组宽H=group_size归一化，默认H=N，G=N/H。is_rms_norm=False执行减均值LayerNorm，True执行不减均值RMSNorm。存在z且norm_before_gate=False时先计算 `x*SiLU(z)`再归一化；True时在归一化、weight/bias仿射之后乘SiLU(z)。activation仅兼容占位，传不同字符串不改变门控函数。

weight是 `[N]` 浮点必填；bias也占必填参数位但允许None。z可选 `[M,N]`。x支持FP16/BF16/FP32；所有参与Tensor同设备，末维stride=1，允许行stride大于N。group_size须正且整除N，不能超过 `65536 // x.element_size()`。

## 输出与别名

返回 `(out,mean,rstd)`。out默认新建为x.dtype的 `[M,N]`；传入同shape、末维连续的out时原地写入并返回该对象，输出dtype取缓冲区dtype。LayerNorm mean与rstd都是FP32 `[G*M]`，RMSNorm的mean为None。统计值按 `g*M+m` 索引，需view(G,M)而非view(M,G)。

公共层检查shape、stride、分组与宽度，但不自动连续化或补全设备/dtype检查。Triton需NPU、FP32中间计算，使用真实行stride；未提供out时其余输入只读。auto选择triton，不自动回退。

## 验证信号

显式torch_native对比两种norm和门控顺序，单独检查统计布局及out别名；不同实现使用独立输出缓冲区，以免覆盖先前结果。activation不会切换激活函数，不能用它请求GELU等分支。

## 固定来源与验证状态

- [norm/layer_norm_fwd.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/layer_norm_fwd.md)
- [构建架构与产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md)及[SDK架构表](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json)。文档arch22对应本版本2201构建族A2/A3，arch35对应3510的950；具体子接口限制以上文为准。

本卡为固定提交的公开API契约蒸馏，未展开Host/Tiling/Device全链路。本次知识提取未执行编译、真机、数值或性能测试；上游报告的支持和用例结果不代表本次复测。
