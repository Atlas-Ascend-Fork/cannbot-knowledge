---
type: API
title: SGLang compressor 的压缩输出与缓存续接
description: 说明 DeepSeek-V4 compressor 的重叠分组、有效输出行、模式2跨架构缓存表差异及 rotary_mode=2 的强制边界。
tags:
- task.implementation
- topic.attention
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/attention/compressor.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/compressor/op_host/compressor.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/cmake/legacy_kernels.cmake
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/pytorch_extensions.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/compressor/op_host/arch22/compressor_tiling.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/compressor/op_host/arch35/compressor_tiling.cpp
  role: implementation
created_at: '2026-11-08T11:04:14Z'
updated_at: '2026-11-10T07:03:17Z'
platforms:
- a2
- a3
- '950'
---

# SGLang compressor 的压缩输出与缓存续接

## 接口原型

```python
from sgl_kernel_npu.operators.attention import compressor

compressor(
    x, wkv, wgate, state_cache, ape, norm_weight, rope_sin, rope_cos,
    state_block_table=None, cu_seqlens=None, seqused=None, start_pos=None,
    rope_head_dim=64, cmp_ratio=4, coff=1, norm_eps=1e-6,
    rotary_mode=2, cache_mode=1, state_cache_stride_dim0=0, *, impl="auto",
)
```

## 压缩语义

`compressor` 将 hidden states 投影为 KV 与 score，按完整的 cmp_ratio-token 组逐特征做 softmax 加权聚合，再做 RMSNorm 与末64维交错 RoPE，同时原地更新 FP32 状态缓存。`coff=2` 会纳入前一组；调用开始前的有效历史必须已在缓存中。`rotary_mode` 现在默认且仅支持 2，显式 1 在启动前被拒绝，不能沿用旧默认假设。

令 `r=cmp_ratio`、`c=coff`、D 为 norm_weight 长度、W=c*D。X 为 FP16/BF16 `[B,S,H]` 或 `[T,H]`，H 在1024..10240内且512对齐；D=128/512，权重 `[W,H]` 与X同dtype。APE为FP32 `[r,W]`，norm_weight为FP32 `[D]`，缓存是可变FP32 `[P,L,2*W]`，前后两半分别存KV和score。r可为2/4/8/16/32/64/128，c=1/2，RoPE宽度固定64。

起点p、有效长度n的输出有效行数为 `floor((p+n)/r)-floor(p/r)`。BSH输出容量 `[B,ceil(S/r),D]`，每请求仅前部有效；TH容量 `[min(T,T//r+B),D]`，有效结果按请求紧密排列。其余槽未定义，不应参与消费或精度比较。

## 元数据与状态生命周期

`state_block_table` 实际必需。cache_mode=1 用分页表，虚拟页0不写；cache_mode=2在arch22使用 `[B,c*r+capacity]` 的展平token位置表，列为 `c*r+t-p`，在arch35则用 `[B]` 请求bank和 `bank*L+t%L` 环形位置，二者不能互换；arch35的cache_mode=2还要求缓存第一维P>=B，Host在blockNum<batchSize时拒绝，索引合法/无写冲突不能替代该形状条件。arch35兼容连续二维表时取展平后的前B项，并非自动按每行首项读取。

TH必须给int32累计边界 `[B+1]`，BSH禁止cu_seqlens；可选seqused限制有效长度，start_pos为非负绝对起点。所有tensor须同NPU且连续，调用方保证索引合法、历史充足、请求间无写冲突；元数据检查不读取设备值。连续调用必须沿用更新后的cache和正确start_pos。

模式2保存尾部原始token；NORMAL路径还为验证保留额外尾部，arch35短BSH FULL_LOAD路径（S<=4且B*S<=256）采用不同保留边界。因此只对语义规定的cache写入区域作比较，不假设所有架构写入相同冗余历史。

`auto`选择Ascend C且不回退。CPU FP32 torch_native会拷回结果和cache，不支持NPU graph capture。验证应覆盖不对齐start_pos、分段续接、coff=2、空输入、两个cache模式及有效输出掩码；不要把参考计算时间当成kernel性能。

## 旧Direct入口的Host准备与workspace初始化

固定树另外注册 `torch.ops.npu.compressor`，定义在 `csrc/compressor/op_host/compressor.cpp::compressor`，经ge_helper准备tiling并`EXEC_KERNEL_CMD(compressor,...)`，没有先调用公开`aclnnSglCompressorGetWorkspaceSize`。它与上文公开Python合同及独立raw ACLNN入口的Host职责必须分别核对；本节保存旧Direct可见事实，不新建重复数学Operator。

`ComputeCompressorShape`在进入完整tiling检查**之前**分配输出：x.rank3视为BSH，其他rank先按TH取x.size(0)；D取norm_weight.size(0)，rope_sin参数不参与形状计算。TH的B由cu_seqlens存在且numel≥2时取size0−1，否则取1；容量`min(T,T/cmp_ratio+B)`，BSH容量`ceil(S/cmp_ratio)`。原始Direct函数只先显式检查x为NPU；cmp_ratio=0会在这些除法中提前失败，不能把后续tiling的合法attr检查当成它的先行保护。公开wrapper的完整有效域仍按前文，不因raw弱guard扩大。

属性rope_head_dim/cmp_ratio/coff/rotary_mode/cache_mode转int32，norm_eps转float；state_cache_stride_dim0也转int32。传入stride属性为0且cache.rank≥3时，默认用**size1*size2逻辑乘积**，并非自动读取storage stride(0)；两代CompressorTiling::CheckFeature均要求此值等于L*2*W（即size1*size2）；即使传入实际非连续首轴步幅，只要不等于该逻辑乘积仍返回GRAPH_FAILED，不能靠显式stride绕过连续缓存限制。随后按12个输入槽顺序RegisterTensor（包括缺省optional），再注册cmp_kv输出，state_cache作为input/output共同传入launch；不能省略空optional而移动后续索引。

旧Host选择对应arch22/arch35的CompressorTiling，ConvertContext/RunBigKernelTiling失败抛出；成功后把context key拷入POD。workspaceSize读取context，若为0则仅回落`sizeof(CompressorTilingData)`，这不是任意非空route真实workspace需求的保证。旧Direct以`(tilingKey>>11)&3 ==1`识别EMPTY_X，直接返回已分配的空输出，发生在GetTilingTensor和workspace分配之前。

### 950旧Direct的readGen producer

旧Host在`SGL_KERNEL_ARCH_35`编译域、非EMPTY_X时，除了分配byte workspace，还显式执行Torch `zero_()`，初始化AIV双buffer释放代数计数：

```text
genFlagsBytes = aivNum * dbWorkspaceRatio * sizeof(uint32_t)
gmSlabBytes = (usedCoreNum + 1 + aivNum) * dbWorkspaceRatio * sizeof(uint32_t)
flagsOffset = workspaceSize - libapiSize - gmSlabBytes
if flagsOffset >= 0:
    workspace.narrow(0,flagsOffset,genFlagsBytes).view(int32).zero_()
```

readGen起点是**整个GM同步slab的开头**，不是`workspaceSize−libapiSize−genFlagsBytes`。本代码只清genFlagsBytes，不声称整个workspace、writeGen或其余同步片全部清零。negative offset分支会跳过zero，源码没有为它另补初始化。窄化范围/真实workspace容量、tiling中的各计数与Device布局仍需一致，zero_只提供这里可见的readGen producer。

zero_是Torch算子准备节点，之后同调用链进入Direct launch；依赖Torch current stream顺序，不是Host同步完成证明。它与raw ACLNN的caller-owned workspace初值边界不同：不能把此旧Direct初始化自动归于`aclnnSglCompressor`内部，也不能反过来描述旧Direct“完全未初始化readGen”。该Torch准备节点的Device实现不在本固定kernel仓，因而本节不把整个旧Direct宣称为完整源码Operator闭包。

### Tiling缓存、placeholder与异步所有权

旧Direct将value-initialized POD交给`context->GetTilingTensor(tilingData)`；类型/设备分区、完整字节键、eager预热、512条容量和overflow复用/流同步限制见[GE Helper缓存机制](../../guides/integration/sgl_kernel_npu/sgl_ge_helper_tiling_cache.md)。源码中局部tilingSize变量不是额外动态内存或另一份上传的producer。

None的state_block_table/cu_seqlens/seqused/start_pos各自转同设备INT32空Tensor[0]，不是None指针；它们仍位于固定launch槽。workspace为x设备byteTensor；tiling cache持有其自己的GM地址，输入、cache、输出、workspace与临时placeholder在launch queue/allocator中合法存活属于框架和caller合同，不能从本地变量自动推断已同步或确定悬空。

旧Direct实际调用顺序与Device资源/数值域可配合[A2/A3完整源码卡](../../operators/aclnn/transformer/attention/sgl_compressor.md)和[950完整源码卡](../../operators/aclnn/transformer/attention/sgl_compressor_950.md)阅读。两卡属于独立公开ACLNN入口；仅复用已证的设备算法事实，旧Direct的额外Torch zero、tiling缓存和失败时机按本节分层，不赋予它们相同ABI或完整生命周期保证。

## 证据与复核范围

本卡依据固定提交的第一方API说明蒸馏；架构编号按同提交构建说明映射为A2/A3（arch22）及950（arch35），具体子功能仍受正文限制。本次知识提取未执行编译、真机、数值或性能测试，未记录verified事件。

## 约束与接入的固定源码

- [compressor_tiling.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/compressor/op_host/arch22/compressor_tiling.cpp)：arch22缓存首轴stride检查。
- [compressor_tiling.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/compressor/op_host/arch35/compressor_tiling.cpp)：arch35缓存stride与模式2的P>=B检查。
