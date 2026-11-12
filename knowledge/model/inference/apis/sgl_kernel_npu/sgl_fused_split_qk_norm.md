---
type: API
title: SGL MLA低秩QK拆分与独立RMSNorm接口
description: 保留 fused_split_qk_norm 的三段布局、对象权重/bias属性、旋转K直拷贝和元信息检查。
tags:
- task.implementation
- topic.attention
- topic.compute.normalization
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/fused_split_qk_norm.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/norm/fused_split_qk_norm.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/fused_split_qk_norm.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/norm_utils.py
  role: implementation
created_at: '2026-11-08T11:03:33Z'
updated_at: '2026-11-10T07:03:17Z'
platforms:
- a2
- a3
- '950'
aliases:
- fused_split_qk_norm
---

# SGL MLA低秩QK拆分与独立RMSNorm接口

## 调用入口

```python
from sgl_kernel_npu.operators.norm import fused_split_qk_norm

def fused_split_qk_norm(
    fused_qkv_a_proj_out,
    q_a_layernorm,
    kv_a_layernorm,
    q_lora_rank,
    kv_lora_rank,
    qk_rope_dim,
    eps=1e-06,
    *,
    impl="auto",
):
    ...
```

## 布局与数学

输入连续浮点 `Z:[N,Rq+Rkv+Dr]` 按Q低秩、K低秩、旋转K三段拼接。前两段各自执行FP32 RMSNorm和对应weight/可选bias；旋转K只复制，不归一化。layernorm对象只提供weight和bias属性，不调用其forward，实际epsilon统一使用显式eps（默认1e-6）。

Rq、Rkv、Dr均为正Python整数并排除bool；eps为有限正实数、排除bool。weight/bias连续且至少分别有Rq/Rkv个元素，可与输入使用不同浮点dtype，但须同设备。浮点类型限FP16/BF16/FP32。

返回新连续 `(q_lora,k_nope,k_pe)`，形状分别 `[N,Rq]`、`[N,1,Rkv]`、`[N,1,Dr]`，均为输入dtype和设备，不改任何输入。N可为0，此时不启动kernel。

## 分发与核验

auto/triton同入口，无自动回退；Triton额外要求NPU。两后端各自独立检查元信息，非法输入在启动前AssertionError，不读取设备值回主机。实现支持表覆盖arch22/arch35，文档同时说明实际硬件执行仍待验证，不能写成已做真机复测。

显式torch_native用独立FP32计算做容差比较，并单独精确核对旋转K的复制与所有输入不变。参考代码可直接做CPU数学对照，但常规包导入仍需要torch_npu、原生库和ACL设备识别。

## 旧Host到同一Device算法的映射

旧 `sgl_kernel_npu.norm.fused_split_qk_norm.fused_split_qk_norm` 与新版 `implementation.triton.norm.fused_split_qk_norm` 的 `fused_split_qk_norm_kernel`（含JIT装饰器、参数/default与body）一致：grid=(B,)，一program处理一token，将Q低秩、K低秩、K旋转三段分别写出；前两段各自FP32平方和/RMS/weight/可选bias，第三段只复制。输入段偏移是0、Rq、Rq+Rkv，输出k_nope/k_pe再由Host各unsqueeze一轴。旧、新模块都只使用对象weight/bias属性，不调用对象forward。

旧Host仅检查三个rank/dim为正，随后解包shape并分配/启动，未检查输入总宽度等于三段之和。新版Host增加 `validate_split_qk_norm` 和NPU断言，由新validator检查rank2及总宽度等于Rq+Rkv+Dr，并统一检查浮点dtype/同设备/连续、正整数排bool、有限正eps和weight/bias容量；分配输出后B==0直接返回，不launch。旧Host没有这些完整检查与显式空B短路。kernel相同只允许复用在新版准入与真实寻址前提都成立的交集，不能把旧入口少检查解释为额外安全支持。这里没有设备属性helper缓存，不能套用其他norm的无参数cache机制。

[自有实现A2/A3](/model/inference/operators/direct/nn/norm/sgl_fused_split_qk_norm.md)与[950](/model/inference/operators/direct/nn/norm/sgl_fused_split_qk_norm_950.md)保存完整Device资源与同步；本段是旧Host映射Reference，未新增独立数学Operator，也未执行真机或编译。

### 增量固定实现来源

- [python/sgl_kernel_npu/sgl_kernel_npu/norm/fused_split_qk_norm.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/norm/fused_split_qk_norm.py)。
- [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/fused_split_qk_norm.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/fused_split_qk_norm.py)。
- [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/norm_utils.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/norm_utils.py)。

## 固定来源与验证状态

- [norm/fused_split_qk_norm.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/fused_split_qk_norm.md)
- [构建架构与产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md)及[SDK架构表](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json)。文档arch22对应本版本2201构建族A2/A3，arch35对应3510的950；具体子接口限制以上文为准。

本卡为固定提交的公开API契约蒸馏，未展开Host/Tiling/Device全链路。本次知识提取未执行编译、真机、数值或性能测试；上游报告的支持和用例结果不代表本次复测。
