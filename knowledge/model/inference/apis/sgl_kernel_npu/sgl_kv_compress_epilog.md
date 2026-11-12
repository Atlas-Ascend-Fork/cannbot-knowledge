---
type: API
title: SGL KV压缩写回的FP8/MXFP8字节布局
description: 说明KV压缩的FP8/MX字节布局、旧Direct Host的Tiling缓存与原地ABI，并区分新raw ACLNN的检查和生命周期。
tags:
- task.implementation
- topic.kv_cache
- topic.compute.quantization
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/mem_cache/kv_compress_epilog.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/kv_compress_epilog/op_host/kv_compress_epilog.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/kv_compress_epilog/op_host/tiling/kv_compress_epilog_tiling_data.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/mem_cache/kv_compress_epilog/torch_adapter.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/pytorch_extensions.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/cmake/legacy_kernels.cmake
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/utils/torch_helper.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/utils/common.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/utils/common_tiling.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/utils/defines.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/kv_compress_epilog/op_kernel/kv_compress_epilog.h
  role: implementation
created_at: '2026-11-08T11:03:33Z'
updated_at: '2026-11-10T07:03:17Z'
platforms:
- '950'
aliases:
- kv_compress_epilog
---

# SGL KV压缩写回的FP8/MXFP8字节布局

## 调用入口

```python
from sgl_kernel_npu.operators.mem_cache import kv_compress_epilog

def kv_compress_epilog(
    kv_compress_cache, x, slot_mapping, quant_group_size, quant_mode,
    round_scale_flag, layout, *, impl="auto",
): ...
```

## 行语义与后端

x是连续同NPU BF16 `[N,D]`，N>0。前D-64列参与量化，末64列RoPE以BF16字节原样保存。根据int32/int64 slot_mapping `[N]`写缓存，slot=-1跳过；未写槽位保留旧值，返回None。auto选择950上的ascendc，不能据torch_native支持arch22推断原生兼容。

## 模式和物理排列

| 模式/布局 | 值区与scale |
| --- | --- |
| quant_mode=1，layout=1 | 每128值一个FP32 scale，槽位记录顺序为FP8量化值、BF16 RoPE、scale。 |
| quant_mode=2，layout=1 | quant_group_size为64或128，E8M0指数字节；顺序为RoPE、量化值、scale。 |
| quant_mode=2，layout=2 | 每block先放所有槽位的值区，再放所有槽位的scale区；不支持FP8模式。 |

cache以FP8 E4M3FN/E5M2 Tensor承载打包字节；layout1按槽位分行，也可 `[slots,1,width]`；layout2为 `[blocks,block_size,width]` 或加单head维。layout1行宽上取整到128字节；layout2每槽scale区上取整到8字节，仅有效组的字节有规定值。round_scale_flag在MX模式把非零带偏置指数加1，不能当普通FP32 scale取整。

## 验证信号

复制cache作独立参考，对比选定槽位的有效字节区、RoPE原始字节及slot=-1/未写槽位的哨兵。不要比较layout2的未规定填充字节，不要把量化行宽当原始D。调用前确保选中的布局、cache容量和slot映射一致；torch_native只作为显式参考，不参与自动回退。

## 固定来源与验证状态

- [mem_cache/kv_compress_epilog.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/mem_cache/kv_compress_epilog.md)
- [构建架构与产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md)及[SDK架构表](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json)。文档arch22对应本版本2201构建族A2/A3，arch35对应3510的950；具体子接口限制以上文为准。

本卡为固定提交的公开API契约蒸馏，未展开Host/Tiling/Device全链路。本次知识提取未执行编译、真机、数值或性能测试；上游报告的支持和用例结果不代表本次复测。

## 旧Direct Host的准备与原地ABI

[FP8完整数学实现](../../operators/aclnn/nn/index/sgl_kv_compress_epilog_fp8_950.md)与[MXFP8完整数学实现](../../operators/aclnn/nn/index/sgl_kv_compress_epilog_mxfp8_950.md)已覆盖量化/布局body；旧 `csrc/kv_compress_epilog/op_host/kv_compress_epilog.cpp` 仍有独立Torch Host与Tiling缓存，采用本API增量保存，不另建重复Operator。

旧 `torch.ops.npu.kv_compress_epilog` schema把cache标为Tensor(a!)、返回空tuple/None，七个参数均无默认值；PrivateUse1绑定sglang::npu_kernel::kv_compress_epilog。legacy_kernels.cmake仅在SGL_KERNEL_ENABLE_A5_ONLY_OPS下加入旧Host与workspace_kernel；默认该开关只对Ascend950前缀打开。新CANN构建的同名Torch schema则绑定mem_cache域torch_adapter，调用 `aclnnSglKvCompressEpilogGetWorkspaceSize/aclnnSglKvCompressEpilog`，不是旧裸launcher的另一种数学。

| 准备项 | 旧Host的实际行为 |
| --- | --- |
| 基础guard | x二维、N/D>0、BF16；slot一维、长度N、INT32/INT64；cache只能FP8 E4M3FN/E5M2 |
| cache视图 | 四维cache要求dim2==1后squeeze(2)，是同storage视图，不做数据搬运或连续化 |
| quant/layout层差 | quant_mode==2时检查G64/128；layout==2时额外要求mode2、cache rank>=2与blockSize=shape1>0；旧wrapper**没有**独立mode∈{1,2}/layout∈{1,2}白名单，不能据else分支扩大公开支持。新Torch adapter补了这两项白名单 |
| stride | 读取cache.stride(0)，正值要求≥自动行/块字节，否则使用自动值；没有额外Torch block_stride参数 |
| 核数 | platform AIV<=0修为1；R=ceil(N/AIV)，used=min(ceil(N/R),AIV)，tail=N-(used-1)R |
| width | Q=D-64，S=ceil(Q/(mode2?G:128))；concat=Q+128+S·(mode2?1:4)，P=align128(concat) |
| layout2 | valuePerToken=Q+128、scalePerToken=align8(S)，blockStride至少B·(valuePerToken+scalePerToken) |
| UB试探 | 输入/输出双缓冲、索引缓冲的字节估算与layout2 scale合计；Host按4*align8(rowFactor)字节估算tmpBufferSize，Device实际indexBuf为随slot类型变化的INT32/INT64索引（非FP32数据）；逐row增加；放不下一行可将rowFactor降0，随后%rowFactor没有独立guard，不能保证宽D安全拒绝 |
| dtype/POD | bit0=slot INT64、bit1=cache E4；packed POD为21个I64+I32+U32，176B，上传slot按32B对齐为192B |
| workspace/launch | 旧每调用分配32B Byte workspace；blockDim=usedCoreNums；cache同一指针同时传入input/output槽，配合schema原地写，返回None |

旧本地guard未完整覆盖同NPU/同device、连续/内层dense、D>=64、slot内容/容量/重复/别名，也未因为schema存在就自动修复输入。这不否定前文公开调用合同，而是明确哪些条件仍由caller保证。mode1的quant_group_size未进入分组宽度计算，实际固定128；mode2才使用64/128。新raw query的workspace包含其框架库区，不能把旧固定32B原样当作aclnn查询结果。

### 旧1024项Tiling缓存与raw指针生命周期

旧Host以TupleHasher的64位hash直接索引captureMap，没有保存完整参数/POD作碰撞核对；函数内static globalTilingBuffer首次按输入设备分配1024个固定slot，map/counter没有device维度或mutex。cache hit只返回该slot的from_blob非拥有视图；新key且未满则CPU Byte tensor memcpy(POD)→pin_memory→to当前NPU device→copy_入固定slot；超过1024项的新key改为每次一次性上传，不加入map。源码不查询capture状态，不拒绝capture中的首次miss；“capture cache”命名和注释不代表本次graph重放验证。

TorchNpuHelper的CopyTensorHostToDevice选择**当前**NPU设备，不是自动读取x/cache的device；旧静态slab又保留首调用设备且key不含device，不能当作多设备隔离。EXEC_KERNEL_CMD只把Tensor转换成data_ptr，用当前stream调用ACLRT_LAUNCH_KERNEL；lambda捕获的是指针tuple，没有输入/输出/workspace/一次性tiling Tensor owners或record_stream，也没有独立DeviceGuard。宏不检查launch返回值并固定返回0。这里记录本层边界，不臆测RunOpApi内部完成方式或宣称已观察悬空指针故障。

新raw ACLNN adapter则有DeviceGuard、ACL descriptor owners、tensor/workspace record_stream、两段式状态检查，并在lambda捕获Tensor/descriptor/workspace/executor；没有把上述旧1024项slab缓存搬到新adapter。两者可复用量化数学知识，不能互相继承缓存和生命周期保证。
KV的cache key包含上述尺寸、模式/round/group/布局/stride/分核/dtype/key等派生字段；POD176B的32B对齐upload slot为192B，旧持有slab大小192×1024=196608B，未据此宣称可用于多设备或任意capture。此处不宣称旧wrapper整个source_closed，未执行上游、构建、真机、数值、性能或graph测试；保留原API生命周期/平台字段，无新增verified。

## 约束与接入的固定源码

- [kv_compress_epilog.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/kv_compress_epilog/op_kernel/kv_compress_epilog.h)：indexBuf的INT32/INT64类型与字节分配。
