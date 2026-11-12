---
type: API
title: SGL交错token/batch矩阵乘与显式NZ权重打包
description: 说明 batch_matmul_transpose 的MBK布局、四维ND承载NZ、输出原地覆盖和仅A2/A3原生支持。
tags:
- task.implementation
- topic.precision
- topic.memory
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/matmul/batch_matmul_transpose.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/batch_matmul_transpose/op_host/batch_matmul_transpose.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/batch_matmul_transpose/op_host/tiling/tiling_data.h
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/utils/torch_helper.h
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/pytorch_extensions.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/cmake/legacy_kernels.cmake
  role: implementation
created_at: '2026-11-08T11:03:33Z'
updated_at: '2026-11-10T07:03:17Z'
platforms:
- a2
- a3
aliases:
- batch_matmul_transpose
---

# SGL交错token/batch矩阵乘与显式NZ权重打包

## 调用入口

```python
from sgl_kernel_npu.operators.matmul import batch_matmul_transpose

def batch_matmul_transpose(
    tensor_a, tensor_b, tensor_c, format_mode=None, quant_mode=None, *, impl="auto"
):
    ...
```

## 数学与输入布局

计算 `C[m,b,n]=sum_k A[m,b,k]*W[b,k,n]`。A为连续FP16/BF16 `[M,B,K]`，C为同设备同dtype连续 `[M,B,N]`，由调用方预分配且不得与A/B重叠。M范围1..1024，各维正、各Tensor元素数不超过UINT32_MAX。

ND/NZ两种模式下tensor_b均须连续，且与A/C同dtype、同设备。format_mode=None或ND时权重为 `[B,K,N]`。NZ时权重为显式打包的ND Tensor `[B,N/16,K,16]`，需K/N为16倍数，其元素关系是 `Wnz[b,j,k,r]=W[b,k,16*j+r]`。可用reshape/permute/contiguous构造；这里不要求torch_npu不透明格式转换。

## 模式和返回

quant_mode支持per_channel_symm、per_channel_asymm、per_token_symm，None等同首项；这些名称都仍执行浮点运算，不开启量化。两后端FP32累加后写为输入dtype，原地覆盖tensor_c并返回None；A/B不修改。

auto固定ascendc，无失败回退；原生只支持A2/A3的arch22/2201，950的参考路线仍待验证，不列入本卡稳定平台。adapter在当前NPU流调用包内ACLNN；不支持的shape、dtype、布局或选项报错。

## 旧legacy Direct入口与tiling槽

同一Torch调用名还在旧legacy库中注册，Host为`csrc/batch_matmul_transpose/op_host/batch_matmul_transpose.cpp`，直接`EXEC_KERNEL_CMD`下发；前文REFACTOR adapter经ACLNN调用的检查与生命周期不能自动归给这个旧实现。旧函数返回void，写caller提供的tensor_c，不创建结果Tensor。

旧Host检查A/B/C同dtype且仅FP16/BF16、A rank3；ND要求B rank3、A.K=B.axis1，NZ要求B rank4、A.K=B.axis2，并以B.axis1*B.axis3推N；两种都要求A.axis1=B.axis0。format默认ND，quant_mode默认per_channel_symm，另接受per_channel_asymm/per_token_symm。C的sizes被读取后未用于shape校验，Host也未在该函数检查C连续性/同device/别名、NZ末轴16或所有维正值/乘积上界；不能照搬新adapter完整guard。维度先转U32构造OpShape，再调用GetPpMatmulTiling及PpMatmulTilingCheck，后续检查不能保护更早的错误维度读取/窄化。

旧`PpMatmulTilingData`为packed 72B：OpShape七个U32加11个U32调度字段。静态NPU Byte allocation预留1024份（73728B），**设备由第一次调用tensor_a决定**；槽下标为M−1，M来自A.axis0，并非A.axis1的batch数。只有0<=M−1<1024才执行上传，否则抛错；实际每次均用同步aclrtMemcpy H2D重写该槽，不是内容命中后跳过上传的GE cache。

槽地址包装为非拥有`at::from_blob(...,tilingSize,at::kByte)` view，未显式标成NPU Tensor；launch helper只取其data_ptr。static allocation持有真实NPU内存，view不另拥有它；不能据view的默认设备标签对这块指针做普通CPU计算。相同M但其它shape/dtype/format不同会覆盖同一槽，跨设备调用仍引用首设备allocation；没有per-stream隔离或锁来证明并发复用安全，同步H2D返回也不等于先前kernel已经消费完旧POD。输入/输出/tiling地址均需保持到当前stream工作完成。

legacy CMake按A3-family开关纳入该Host与no-workspace Device，构建开关本身不扩大前文公开平台。数学与新核心对应关系可阅读[完整ACLNN实现](../../operators/aclnn/nn/matmul/sgl_batch_matmul_transpose.md)，其生成bridge、额外guard和输出校验仍属于不同入口。这里保存旧Direct的可得合同，不为旧wrapper新增完整Operator或真机通过声明。

## 验证方式

显式torch_native解包NZ后用FP32 bmm，对照独立C缓冲区。分别测ND/NZ等价、C被覆盖及输入未改。上游提供单算子构建和 `tests/python/operators/matmul/test_batch_matmul_transpose.py --impl=ascendc --impl-ref=torch_native --enable-perf=false` 验证入口；本卡不把入口存在当作已运行结果。

## 固定来源与验证状态

- [matmul/batch_matmul_transpose.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/matmul/batch_matmul_transpose.md)
- [构建架构与产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md)及[SDK架构表](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json)。文档arch22对应本版本2201构建族A2/A3，arch35对应3510的950；具体子接口限制以上文为准。

本卡为固定提交的公开API契约蒸馏，未展开Host/Tiling/Device全链路。本次知识提取未执行编译、真机、数值或性能测试；上游报告的支持和用例结果不代表本次复测。
