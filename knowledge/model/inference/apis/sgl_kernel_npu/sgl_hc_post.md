---
type: API
title: SGL HC后混合的四路残差与CANN9.1厂商绑定
description: 说明 hc_post 的矩阵方向、固定四流/隐藏宽度、recipes profile依赖和版本不回退。
tags:
- task.implementation
- topic.model_architecture
- topic.compilation
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/hyper_conn/hc_post.md
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
- hc_post
---

# SGL HC后混合的四路残差与CANN9.1厂商绑定

## 调用入口

```python
from sgl_kernel_npu.operators.hyper_conn import hc_post

def hc_post(x, residual, post, comb, *, impl="auto"):
    ...
```

## 输入与残差映射

对输出流j计算 `post[j]*x[d]+sum_i comb[i,j]*residual[i,d]`，comb的第一流维是输入、第二是输出，直接传入不转置。新输出与residual同shape/dtype/device，不修改输入。

输入连续同NPU，各维正。x为 `[T,D]` 或 `[B,S,D]`，FP16/BF16/FP32；residual增加4流维，post为对应前导维加 `[4]`，comb加 `[4,4]`。residual dtype同x，comb dtype同post；D仅4096或7168，残差流固定4。

## Vendor与参考范围

auto在CANN9.1.0选择cann_recipes_infer_cann910，其他版本直接报错。wheel构建须包含cann_recipes_infer profile，所需内核和Torch绑定随wheel提供；不因实现名字cann910就忽略文档对arch35的支持声明。

torch_native独立FP32中间计算再转x.dtype，需显式选择，非9.1环境不会自动回退。验证应选非对称comb以区分矩阵方向、使用独立参考，并检查各前导布局和返回新存储。不能把此固定4流接口推广到任意流数。

## 固定来源与验证状态

- [hyper_conn/hc_post.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/hyper_conn/hc_post.md)
- [构建架构与产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md)及[SDK架构表](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json)。文档arch22对应本版本2201构建族A2/A3，arch35对应3510的950；具体子接口限制以上文为准。

本卡为固定提交的公开API契约蒸馏，未展开Host/Tiling/Device全链路。本次知识提取未执行编译、真机、数值或性能测试；上游报告的支持和用例结果不代表本次复测。
