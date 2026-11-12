---
type: API
title: SGLang CATLASS softFP8 W8A16矩阵乘与分组前缀合同
description: 说明已注册softfp8_w8a16_matmul/grouped_matmul的E4M3位容器、128块scale、BF16输出及GMM前缀，标明BMM仅有文档。
tags:
- task.implementation
- topic.compute.composite
- topic.compute.quantization
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/catlass/README.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/pytorch_extensions.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/cmake/legacy_kernels.cmake
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_mm_wfp8a16.py
  role: evidence
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_gmm_wfp8a16.py
  role: evidence
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/catlass/utils/gemm/tile/cast_fp8_to_bf16_with_scale.hpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/catlass/op_host/catlass_matmul_fp8.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/catlass/op_host/catlass_gmm_fp8.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/catlass/op_host/catlass_op_utils.h
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/catlass/op_host/catlass_op_utils.cpp
  role: implementation
created_at: '2026-11-08T11:03:55Z'
updated_at: '2026-11-09T15:01:42Z'
platforms:
- a2
- a3
---

# SGLang CATLASS softFP8 W8A16矩阵乘与分组前缀合同

## 适用范围与含义

固定README明确此soft-FP8路线适用于Atlas A2/A3，在910B/C以位容器保存E4M3 FP8权重，按128x128块scale反量化成BF16后执行GEMM，输出BF16；不是声明硬件原生FP8乘法。MM/GMM受 `BUILD_CATLASS_MODULE` 与 `SGL_KERNEL_ENABLE_A3_ONLY_OPS` 双重构建门控，支持ND/连续RowMajor，不支持NZ。

```python
import sgl_kernel_npu
torch.ops.npu.softfp8_w8a16_matmul(mat1, mat2, scale, "bf16")
torch.ops.npu.softfp8_w8a16_grouped_matmul(mat1, mat2, scale, groupList, "bf16")
```

| 入口 | 输入与返回 |
| --- | --- |
| MM | BF16 `[M,K]`、uint8 E4M3 FP8 bits `[K,N]`、FP32 `[ceil(K/128),ceil(N/128)]` scale，返回BF16 `[M,N]`。 |
| GMM | BF16 `[M,K]`、uint8 E4M3 FP8 bits `[g,K,N]`、FP32 `[g,ceil(K/128),ceil(N/128)]`，返回BF16 `[M,N]`。 |
| BMM（仅文档） | README描述BF16 `[b,M,K]`与int8位容器 `[b,K,N]`，但本快照无对应实现注册、Host/Kernel或构建条目，不能作为可调用入口。 |

README将输出字符串参数称为 outDType，但实际 Torch schema 将必填字符串注册为 c，未定义 outDType 关键字或默认值；上述示例按测试使用位置参数 "bf16"。MM/GMM权重编码限定为 E4M3（测试用 torch.float8_e4m3fn），Device固定移位/掩码解码，没有E5M2等格式选择参数，不能只按uint8容器接受任意FP8位模式。

GMM的groupList为int64一维长度g，**累计结束位置**，不是每组独立长度；首项为首组行数，其余为前缀和。规模与最后前缀须匹配M，不能把 `[256,128,...]` 的组大小直接作为该接口前缀。

## 文档差异与边界

README的总述使用int8称谓，但MM/GMM精确签名和约束使用uint8；按各接口具体位容器合同准备数据。BMM在本快照仅有README描述：pytorch_extensions.cpp只声明并绑定MM/GMM，legacy_kernels.cmake也仅纳入这两种实现，未发现对应BMM Host/Kernel。其scale shape不只是文档缺口，当前没有可执行实现合同，不能从GMM推断BMM调用或广播能力。

README也介绍 `catlass_matmul_basic(a,b,out,format_mode=None)`，其写入调用方输出与上述返回新Tensor的接口不同，不应互换。本文不把这段基础接口的dtype列举提升成softFP8支持类型，也不声称完成CATLASS内部Device闭包。

## 固定实现的输出、数值与资源边界

公开合法输出仍为BF16，位置参数传"bf16"。Host没有把这个字符串限制为BF16：通用helper接受float32/float16/int8/int32/bf16，未知字符串默认为float16，并据此申请current NPU的输出Tensor；Device入口只有固定BF16写出，不随字符串分发。其他字符串仅改变allocation，没有对应正确输出数学fallback；尤其int8申请MN字节而BF16写2MN字节，宽dtype申请也不等于正确宽dtype结果。这里只记录源码静态边界，未运行这些非法合同调用。

软件位解码先得到FP16(w/256)，Cast FP32后乘预先计算的scale*256，再以CAST_RINT转BF16，随后才执行BF16 Cube；应在BF16反量化之后建reference。有限E4M3权重与有界scale可按上文公式解释，但0x7f/0xff在此实现得到±480有限数而非E4M3FN NaN；scale*256中间溢出也未由Host校验，不能把任意uint8位模式都当标准FP8特殊值。

每core两BF16反量化GM槽共262144字节。AIV每次MN tile将整个K的相关scale行缓存于UB147968字节之后，行补32字节；选中AtlasA2 UB192KiB只剩48640字节，因此ceil(K/128)≤1520是当前实例的缓存容量必要条件，Host没有该K上限guard或超限分批fallback。Host workspace实际使用sizeof(aclDataType枚举)的公式，不能把它解释成输出元素dtype byte数。完整两个scheduler、资源、mode2握手、groupList差分和尾块见[普通矩阵乘源码卡](../../operators/direct/nn/matmul/sgl_softfp8_w8a16_matmul.md)与[分组矩阵乘源码卡](../../operators/direct/nn/matmul/sgl_softfp8_w8a16_grouped_matmul.md)。

两Host均未统一验证NPU/同device/连续/stride或U32尺寸范围，GMM也未读groupList数值验证单调性/最后前缀M；输出分配在current NPU而workspace随输入device。裸指针异步寿命依匹配Torch NPU allocator/OpCommand协议，固定源码不能代替安装binary、设备数值或图捕获验证。测试脚本的case循环在__main__中返回bool并打印汇总，没有assert/非零退出失败链，不从测试文件存在推导已经通过。

## 验证方式

先按E4M3编码（torch.float8_e4m3fn）与scale构造独立BF16反量化reference，再分别验证MM、GMM零/不均匀分组、矩阵尾块和输出dtype。README的随机uint8/int8示例只是占位位数据，不能直接作为正确FP8数值基线。本次未编译或运行真机/数值/性能测试。
