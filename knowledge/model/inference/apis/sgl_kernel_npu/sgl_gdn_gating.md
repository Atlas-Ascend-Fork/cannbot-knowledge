---
type: API
title: SGLang GDN门控的softplus阈值与输出精度
description: 说明fused_gdn_gating的对数衰减和sigmoid双输出、beta乘阈值语义、连续指针寻址及extend/decode区别。
tags:
- task.implementation
- topic.attention
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/attention/gdn/fused_gdn_gating.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
created_at: '2026-11-08T11:04:14Z'
updated_at: '2026-11-08T11:05:18Z'
platforms:
- a2
- a3
- '950'
---

# SGLang GDN门控的softplus阈值与输出精度

## 接口原型

```python
from sgl_kernel_npu.operators.attention.gdn import fused_gdn_gating

def fused_gdn_gating(A_log, a, b, dt_bias, beta=1.0, threshold=20.0, *, impl="auto"):
    ...
```

## 公式与精度

`fused_gdn_gating` 为GDN extend/chunk流程生成gate。令x=a+dt_bias，若beta*x<=threshold，则softplus=log(1+exp(beta*x))/beta，否则直接x；再算 `g=-exp(A_log)*softplus` 和 `beta_output=sigmoid(b)`。参数beta是softplus斜率，不是返回的sigmoid更新权重。

A_log/dt_bias为每头 `[H]` 浮点，生产常用FP32，a/b为相同 `[R,H]` FP16/BF16/FP32，R>0、beta>0，同NPU。Triton直接指针寻址要求全部连续，A_log/dt_bias即使只检查元素数也必须保证stride正确。输出g为FP32、beta_output为b.dtype，都是 `[R,H]` 新tensor，不改输入。

auto默认Triton且无执行失败回退；torch_native独立按同公式计算。此入口服务非target_verify的extend门控，decode通常由融合递推入口内部算门控，不能把生成g的独立步骤机械插入所有decode路径。

验证应覆盖beta*x接近threshold的两分支、非默认beta以及b低精度输出；按输出dtype分别比较，不能把sigmoid结果误判为对数gate或再额外softplus。

## 证据与复核范围

本卡依据固定提交的第一方API说明蒸馏；架构编号按同提交构建说明映射为A2/A3（arch22）及950（arch35），具体子功能仍受正文限制。本次知识提取未执行编译、真机、数值或性能测试，未记录verified事件。

## 相关知识

- [块内线性系统与WY链](sgl_gdn_chunk_linear_system.md)
- [融合单token decode](sgl_fused_gdn_decode.md)
