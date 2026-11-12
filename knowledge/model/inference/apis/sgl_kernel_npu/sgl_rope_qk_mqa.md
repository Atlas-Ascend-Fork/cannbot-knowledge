---
type: API
title: SGL MQA Q/K旋转位置编码与预选频率缓存
description: 说明 fused_rope_qk_mqa 的独立Q/K头数、预先按token选表、两种配对和Triton二次幂约束。
tags:
- task.implementation
- topic.attention
- topic.precision
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/rope/fused_rope_qk_mqa.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/norm/fused_rope_qk_mqa.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/rope/fused_rope_qk_mqa.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/rope/rope_utils.py
  role: implementation
created_at: '2026-11-08T11:03:33Z'
updated_at: '2026-11-09T15:27:12Z'
platforms:
- a2
- a3
- '950'
aliases:
- fused_rope_qk_mqa
---

# SGL MQA Q/K旋转位置编码与预选频率缓存

## 调用入口

```python
from sgl_kernel_npu.operators.rope import fused_rope_qk_mqa

def fused_rope_qk_mqa(
    query, key, cos_sin, rotary_dim, is_neox_style, *, impl="auto"
):
    ...
```

## 输入与旋转

query `[T,Hq,D]` 和key `[T,Hk,D]` 共享token数、head_dim、dtype和同一NPU，头数可不同且不要求整除，不展开K头。类型为FP16/BF16/FP32，正维度。cos_sin `[N,R]` 的N>=T，行布局 `[cos_half|sin_half]`，dtype可与Q/K不同但同设备。

R为正偶数、不超过D。is_neox_style=True在旋转区前后两半配对，False配相邻偶/奇通道；D-R尾部原值复制。缓存第t行直接服务第t个token，接口没有positions或gather，调用方须预先按实际位置选好频率。

返回新Q/K，shape和各输入dtype保持，不修改输入。strided输入可非连续或含零stride只读视图。公共元信息断言失败时不启动kernel。

## 后端差别

auto与triton同入口，无自动回退。Triton要求Hq、Hk、R/2为2的幂，D-R为0或2的幂；T不受该约束。torch_native支持一般合法尺寸，不能据其运行成功放宽Triton约束。

参考运算沿用Triton类型提升：FP16与BF16混合按FP16，有FP32时用FP32，最后写回Q/K类型。低精度舍入和融合乘加可能不同；验证旋转区用dtype容差，尾部应精确保持。不要用未选位置的整张频率表作错误参考。

## 旧MQA入口与新版校验层

旧 `sgl_kernel_npu.norm.fused_rope_qk_mqa.fused_rope_qk_mqa` 与新版 `implementation.triton.rope.fused_rope_qk_mqa` 共享源码相同的 `fused_rope_qk_mqa_kernel_opt`，包括JIT装饰器、完整参数、stride寻址与旋转/尾复制body。Host仍按grid=(T,)返回empty_like的新Q/K，频率第t行直接对应token t，没有positions gather。旧模块与新模块是独立定义的kernel对象，并不是Python转发别名。

新版Host在读shape/分配输出前增加validate_rope_inputs与NPU检查，再明确检查Hq、Hk、R/2为二次幂，D−R为0或二次幂。旧Host没有这组完整dtype/device/stride/尺寸/二次幂保护。上述约束来自相同kernel的arange/reshape等实际准入，不能据旧函数未拒绝就宣传任意head数可用。两边没有引入get_device_properties或自有无参数设备属性cache，不能编造其生命周期。

[MQA完整实现A2/A3](/model/inference/operators/direct/transformer/posembedding/sgl_fused_rope_qk_mqa.md)及[950](/model/inference/operators/direct/transformer/posembedding/sgl_fused_rope_qk_mqa_950.md)保存同body资源/精度；这里不新建重复数学Operator，未做真机、编译或数值验证。

### 增量固定实现来源

- [python/sgl_kernel_npu/sgl_kernel_npu/norm/fused_rope_qk_mqa.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/norm/fused_rope_qk_mqa.py)。
- [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/rope/fused_rope_qk_mqa.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/rope/fused_rope_qk_mqa.py)。
- [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/rope/rope_utils.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/rope/rope_utils.py)。

## 固定来源与验证状态

- [rope/fused_rope_qk_mqa.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/rope/fused_rope_qk_mqa.md)
- [构建架构与产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md)及[SDK架构表](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json)。文档arch22对应本版本2201构建族A2/A3，arch35对应3510的950；具体子接口限制以上文为准。

本卡为固定提交的公开API契约蒸馏，未展开Host/Tiling/Device全链路。本次知识提取未执行编译、真机、数值或性能测试；上游报告的支持和用例结果不代表本次复测。
