---
type: API
title: SGLang 量化共享KV的640字节布局与host调度接口
description: 记录950量化共享KV注意力的混合BF16/FP8/E8M0字节布局、1024整数调度表与图捕获外生成要求，保留重构后待验收状态。
tags:
- task.implementation
- topic.attention
status: draft
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/attention/kv_quant_sparse_attn_sharedkv.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/attention/kv_quant_sparse_attn_sharedkv_metadata_host.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/kv_quant_sparse_attn_sharedkv_metadata/op_host/kv_quant_sparse_attn_sharedkv_metadata.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/kv_quant_sparse_attn_sharedkv_metadata/op_host/kv_quant_sparse_attn_sharedkv_metadata.h
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/kv_quant_sparse_attn_sharedkv/op_kernel/arch35/kv_quant_sparse_attn_sharedkv_scfa_kernel.h
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/kv_quant_sparse_attn_sharedkv/op_kernel/arch35/kv_quant_sparse_attn_sharedkv_scfa_block_vector.h
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/utils/ge_helper.h
  role: implementation
created_at: '2026-11-08T11:04:14Z'
updated_at: '2026-11-10T07:03:17Z'
platforms:
- '950'
aliases:
- kv_quant_sparse_attn_sharedkv
- kv_quant_sparse_attn_sharedkv_metadata_host
---

# SGLang 量化共享KV的640字节布局与host调度接口

## 接口原型

```python
from sgl_kernel_npu.operators.attention import kv_quant_sparse_attn_sharedkv

def kv_quant_sparse_attn_sharedkv(
    q,
    *,
    ori_kv=None,
    cmp_kv=None,
    ori_sparse_indices=None,
    cmp_sparse_indices=None,
    ori_block_table=None,
    cmp_block_table=None,
    cu_seqlens_q=None,
    cu_seqlens_ori_kv=None,
    cu_seqlens_cmp_kv=None,
    seqused_q=None,
    seqused_kv=None,
    sinks=None,
    metadata=None,
    kv_quant_mode=1,
    tile_size=64,
    rope_head_dim=64,
    softmax_scale=1.0,
    cmp_ratio=1,
    ori_mask_mode=4,
    cmp_mask_mode=3,
    ori_win_left=127,
    ori_win_right=0,
    layout_q="BSND",
    layout_kv="PA_ND",
    return_softmax_lse=False,
    impl="auto",
):
    ...
```

```python
from sgl_kernel_npu.operators.attention import kv_quant_sparse_attn_sharedkv_metadata_host

def kv_quant_sparse_attn_sharedkv_metadata_host(
    num_heads_q,
    num_heads_kv,
    head_dim,
    layout_q,
    layout_kv,
    *,
    cu_seqlens_q=None,
    seqused_kv=None,
    batch_size=0,
    max_seqlen_q=0,
    max_seqlen_kv=0,
    cmp_topk=0,
    cmp_ratio=1,
    ori_mask_mode=4,
    cmp_mask_mode=3,
    ori_win_left=127,
    ori_win_right=0,
    has_ori_kv=True,
    has_cmp_kv=True,
    kv_quant_mode=1,
    tile_size=64,
    rope_head_dim=64,
    impl="auto",
):
    ...
```

## 声明范围与字节布局

固定来源只声明arch35原生接口，且明确公共API重构后待重新验证；本卡保留draft，不能作为已完成NPU验收的证据。主算子的`auto`选`ascendc`，metadata_host的`auto`选`host`，均不自动回退。面向DeepSeek-V4/DSpArk，所有query头共享一份K/V，稀疏索引由调用方提供，算子不做TopK。

每行不是普通640维FP8向量，而是640字节包：64个BF16 RoPE占128字节、448个FP8 NoPE、7个E8M0 scale以及padding。每64个NoPE值用 `2**(scale_byte-127)` 解量化并舍入BF16，再重排为 `[NoPE,RoPE]`。Q为BF16 BSND `[B,S,H,512]` 或TND `[T,H,512]`，H=64/128；缓存以FP8 E4M3FN tensor承载 `[blocks,page_size,1,640]`，页大小16对齐且<=1024。

ori_kv、ori_block_table、seqused_kv、FP32 sinks `[H]` 和int32 metadata `[1024]` 实际必需。主算子已提供tensor必须连续且与q同NPU。TND需query累计边界；cu_seqlens_ori_kv和cu_seqlens_cmp_kv当前均不支持，必须保持None。原始物理稀疏索引只覆盖TND、K=512/1024、-1终止且cmp_kv=None；压缩侧需要对应cache/页表、cmp_ratio=4/128。ori_mask_mode固定4、cmp_mask_mode固定3，kv_quant_mode=1、tile_size=64、rope_head_dim=64、layout_kv=PA_ND。返回BF16同Q形输出和FP32空LSE，return_softmax_lse=True不支持。

## CPU调度和graph生命周期

`kv_quant_sparse_attn_sharedkv_metadata_host` 的长度输入必须为CPU连续int32，不能直接传NPU长度。host从长度、窗口与压缩参数生成int32 `[1024]` 再复制到当前NPU：36个Cube槽各9整数、72个Vector槽各8整数，其余保留。128头模式将逻辑Cube任务复制到相邻物理核对；Flash Decode跨核切分未启用。调用者不应自行改写该布局。

metadata_host的has_cmp_kv默认为True；只使用原始KV时必须显式False，不能仅因主调用cmp_kv=None就省略。cmp_topk只支持0、512或1024；has_cmp_kv=True时cmp_ratio须为4或128。所有调度参数与实际主算子路径一致。

主算子捕获要求当前设备已缓存对应tiling配置：捕获前须以相同shape、dtype、optional输入与属性执行eager预热并确认配置已缓存；缓存未初始化或配置未命中时，ge_helper会在capture内拒绝调用。仅在图外生成metadata不足以满足该条件。host调度必须在NPU Graph捕获外完成，重放前拷入地址稳定的NPU缓冲；新调度参数必须与主调用一致。host每次分配输出，NPU profiler不会计入其CPU调度时间，端到端耗时需主机计时与同步。

CPU参考主算子仅支持BSND、未压缩窗口，不覆盖TND/显式稀疏/压缩/graph；参考调度仅支持单请求单query decode、默认127/0窗口、正KV长度，压缩参考仅64头。比较应隔离有效子集，不能把参考未支持模式当作原生不支持，也不能把同一host入口别名对比当独立验证。

## 证据与复核范围

本卡依据固定提交的第一方API说明蒸馏；架构编号按同提交构建说明映射为A2/A3（arch22）及950（arch35），具体子功能仍受正文限制。本次知识提取未执行编译、真机、数值或性能测试，未记录verified事件。

## 固定实现的元数据生成与消费边界

C++ `sglang::npu_kernel::kv_quant_sparse_attn_sharedkv_metadata_host` 在CPU执行 `KvQuantSparseAttnSharedkvMetadataHost::Run`：检查CPU连续int32长度及单调性/非负值，通过当前Runtime查询实际核数和SoC，要求950、AIC≤36/AIV≤72；128头还要求两类核数为偶数。它以 `pinned_memory(true)` 分配全零int32 `[1024]`（4096字节），由CPU填FA/FD表，最后 `host.to(at::Device("npu"), non_blocking=true)`。这是CPU调度及框架H2D拷贝，没有自有Device数学kernel；调用方必须遵守拷贝/当前stream的异步生命周期，不能把Host返回当作Device已经完成。固定实现见[Host入口与拷贝](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/kv_quant_sparse_attn_sharedkv_metadata/op_host/kv_quant_sparse_attn_sharedkv_metadata.cpp#L925-L1012)。

主算子不会自动调用此Host入口。FA区域为36×9整数，FD区域为72×8整数，尾124整数保留；128头逻辑任务复制到相邻物理AIC行，`FA_S2_MAX_NUM=8`（零基索引8，即行内第9个整数、字节偏移32；索引7为FA_FIRST_FD_DATA_WORKSPACE_IDX_INDEX）记录窗口/压缩调度估计的最大S2轮数，disabled行也写该值。当前Flash Decode关闭。graph外生成后应拷入稳定NPU缓冲，保持参数、核数和内容与主调用一致；一个合法dtype/numel的表不等于调度正确。见[GenMetaData](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/kv_quant_sparse_attn_sharedkv_metadata/op_host/kv_quant_sparse_attn_sharedkv_metadata.cpp#L822-L854)。

**128头、TND、原始物理稀疏路线存在额外的条件性同步风险**：metadata Host没有 `ori_sparse_indices` 输入，仍按窗口估算S2；主Device的SWA分支却用当前query非负索引前缀重算S2循环。splitG模式下全部AIV按FA零基索引8（第9项）的S2 max补齐mode0 barrier轮次，active核每次V0也参加全AIV barrier。若实际前缀轮数超过元数据估计，disabled核可能先结束参与而active核继续等待。例如单请求单query、KV长度至少512、H128/TND、无压缩、窗口127/0、512个有效非负原始slot时，窗口估算1轮而实际前缀4轮；这是固定源码的条件化推导，本次未做运行验证，也不假定其它初始化风险之后的路径一定执行。64头没有这一splitG全局协议，不能泛化为64头风险或所有SWA调用必然失败。见[实际稀疏轮数重算](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/kv_quant_sparse_attn_sharedkv/op_kernel/arch35/kv_quant_sparse_attn_sharedkv_scfa_kernel.h#L316-L459)、[V0全AIV barrier](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/kv_quant_sparse_attn_sharedkv/op_kernel/arch35/kv_quant_sparse_attn_sharedkv_scfa_block_vector.h#L647-L689)。

完整Direct入口、12个编译key及其TND稀疏子分支、资源和静态风险见[量化共享KV 950源码算子卡](../../operators/direct/transformer/attention/sgl_kv_quant_sparse_attn_sharedkv_950.md)。闭包标签表示源码可追溯，不表示已验证数值或内存安全。


## 约束与接入的固定源码

- [ge_helper.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/utils/ge_helper.h)：图捕获前同配置eager预热及当前设备tiling缓存命中条件。
