---
type: API
title: SGL图像视频patch展平与时间补帧接口
description: 说明 flatten_patches 的末帧重复、空间合并整除、输出网格及可能共享输入存储的边界。
tags:
- task.implementation
- topic.multimodal
- topic.data_pipeline
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/multimodal/flatten_patches.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/multimodal/flatten_patches.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/torch_native/multimodal/flatten_patches.py
  role: implementation
created_at: '2026-11-08T11:03:33Z'
updated_at: '2026-11-09T11:06:56Z'
platforms:
- '950'
aliases:
- flatten_patches
---

# SGL图像视频patch展平与时间补帧接口

## 调用入口

```python
from sgl_kernel_npu.operators.multimodal import flatten_patches

def flatten_patches(patches, patch_size, merge_size, temporal_patch_size, *, impl="auto"):
    ...
```

## 输入布局与输出

输入NPU像素patches为 `[B,T,C,H,W]`，维度全正，支持非连续，固定文档测试包括FP32/FP16/BF16。patch_size=P、merge_size=M、temporal_patch_size=TP为正整数，H和W须可被P*M整除。

若T不能组成完整时间patch，则重复最后一帧补齐；按M组织空间patch后展平。输出Tensor `[B,grid_t*grid_h*grid_w,C*TP*P*P]`，dtype/device同输入，grid_t为补齐T/TP、grid_h=H/P、grid_w=W/P。M影响排列而不减少返回的grid_h/grid_w。

## 分发、别名与验证

只有torch_native，auto也选它；使用帧扩展、拼接和不超过八维的两步布局转换。输入不变，但恒等布局可使输出与输入共享存储，不能假定总是独立新Tensor。固定文档只把950标为已验证，arch22未验证，故稳定平台限定950。

验证用可区分帧/通道/位置的内容检查展平顺序、末帧补齐及非连续输入；仅shape正确不足以证明patch顺序正确。例如 `[1,3,3,28,28]`，P=14、M=2、TP=2，输出 `[1,8,1176]`，网格为(2,2,2)。

## 固定实现的patch顺序

设补齐后的T'=ceil(T/TP)*TP、gt=T'/TP、gh=H/P、gw=W/P。源码先把末帧expand为T'-T帧并cat到时间轴（仅不足整组时），随后严格执行以下布局链，不能用任意相同shape的reshape替代：

```text
[B,T',C,H,W]
→ reshape [B*gt, TP*C, gh/M, M, P, gw/M, M, P]
→ permute(0,1,2,5,3,6,4,7)
→ reshape [B,gt,TP,C,gh*gw,P,P]
→ permute(0,1,4,3,2,5,6)
→ reshape [B,gt*gh*gw,C*TP*P*P]
```

最大中间rank是8，不需要九维Tensor。空间合并M改变patch枚举次序，时间TP进入每patch内部向量；接口不做像素归一化或视觉编码。非连续输入可由reshape产生拷贝，不能保证零拷贝；部分恒等配置又可能共享原存储，不能保证总是新storage。本文shape例是固定源码推导，不是本次运行结果。dtype/device保留，公开FP32/FP16/BF16用例也不证明所有Torch dtype在NPU均已验证。

## 固定来源与验证状态

- [multimodal/flatten_patches.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/multimodal/flatten_patches.md)
- [构建架构与产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md)及[SDK架构表](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json)。文档arch22对应本版本2201构建族A2/A3，arch35对应3510的950；具体子接口限制以上文为准。

本卡为固定提交的公开API契约蒸馏，未展开Host/Tiling/Device全链路。本次知识提取未执行编译、真机、数值或性能测试；上游报告的支持和用例结果不代表本次复测。
