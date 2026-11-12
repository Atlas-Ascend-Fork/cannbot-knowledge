---
type: API
title: SGLang Flash MLA 与配套调度信息接口
description: 说明950/CANN9.2非量化分页MLA的576/512共享KV、sink与右对齐mask，以及metadata重建条件。
tags:
- task.implementation
- topic.attention
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/attention/flash_mla.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/attention/flash_mla_metadata.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/torch_native/attention/flash_mla.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/attention/flash_mla.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/third_party/profiles/cann-9.2.0/ops_transformer.json
  role: supporting
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/flash_mla_metadata/op_host/op_api/aclnn_flash_mla_metadata.cpp
  role: primary
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/flash_mla_metadata/op_host/op_api/aclnn_flash_mla_metadata.h
  role: header
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/flash_mla_metadata/op_host/op_api/l0_flash_mla_metadata.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/flash_mla/torch_extension/flash_mla.py
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/flash_mla/torch_extension/csrc/flash_mla.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/flash_mla/op_host/checkers/seq_len_checker.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/flash_mla/op_host/checkers/metadata_checker.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/flash_mla/docs/torchapi_flash_mla.md
  role: implementation
created_at: '2026-11-08T11:04:14Z'
updated_at: '2026-11-10T07:03:17Z'
platforms:
- '950'
cann_versions:
- 9.2.0
aliases:
- flash_mla
- flash_mla_metadata
---

# SGLang Flash MLA 与配套调度信息接口

## 接口原型

```python
from sgl_kernel_npu.operators.attention import flash_mla

def flash_mla(
    q,
    k_cache,
    block_table=None,
    cache_seqlens=None,
    cu_seqlens_q=None,
    seqused_q=None,
    sinks=None,
    attn_mask=None,
    metadata=None,
    head_dim_v=512,
    softmax_scale=1.0,
    mask_mode=0,
    win_left=-1,
    win_right=-1,
    max_seqlen_q=-1,
    max_seqlen_kv=-1,
    layout_q="BSND",
    layout_kv="PA_BBND",
    layout_out="BSND",
    return_softmax_lse=False,
    *,
    impl="auto",
):
    ...
```

```python
from sgl_kernel_npu.operators.attention import flash_mla_metadata

def flash_mla_metadata(
    cache_seqlens,
    num_heads_q,
    num_heads_kv,
    cu_seqlens_q=None,
    seqused_q=None,
    max_seqlen_q=-1,
    max_seqlen_kv=-1,
    head_dim_qk=576,
    head_dim_v=512,
    mask_mode=0,
    win_left=-1,
    win_right=-1,
    layout_q="BSND",
    *,
    impl="auto",
):
    ...
```

## 主接口与缓存布局

原生Flash MLA是CANN9.2.0引入的非正式接口，`auto`选择包内 `cann_ops_transformers_cann920`，仅arch35；不能因torch_native也支持arch22而扩大原生范围。它将共享KV的全部576通道作为K、前512通道作为V。Q为FP16/BF16，支持TND `[T,N,576]`、BSND `[B,S,N,576]`、BNSD `[B,N,S,576]`，1<=N<=128；KV仅1头，页大小128。

KV物理布局可为PA_BBND `[P,128,1,576]`、PA_BNBD `[P,1,128,576]`、PA_NZ `[P,1,36,128,16]`。分页时int32 block_table `[B,L]` 与cache_seqlens `[B]` 实际必需，表容量覆盖有效长度。TND需int32 `[B+1]` cu_seqlens_q，其他布局不传。seqused_q可限制物理分段内有效query长度。

固定e7实际Host还检查：cu_seqlens_q与seqused_q均缺省/空时，`max_seqlen_q`必须等于Q的物理序列轴S。因此BSND/BNSD无used长度时，原型默认-1并不是可直接执行的配置，需显式传S或按合同提供seqused_q；单属性只检查>=-1不代表通过组合检查。TND另有必需cuQ的存在性检查，不能通过这项BSND补值绕过。这里区分SGL原型默认、公开说明与实际vendor准入，不推定别的接口也有同一限制。

softmax_scale默认1.0，需自行设置常规缩放。FP32 sinks `[N]` 是额外零value的标量logit，与GQA稀疏接口的 `[QH,D]` sink向量不同。mask_mode为0/3/4，3按 `j<=Lkv-Lq+i` 右对齐因果；4为独立BAND窗口，令p=i+Lkv−Lq，可见范围为p−win_left<=j<=p+win_right（另与实际KV范围取交集），-1表示对应侧无界，左右均默认-1时全可见，不能先套mode3的因果上界；3/4需int8 `[2048,2048]` 标准压缩上三角mask，0不传。

返回 `(out,lse)`，不改输入。out维512，布局跟随Q，TND额外可用NTD；开启LSE时FP32形状为TND下 `[N,T]`、其他 `[B,N,S]`，关闭时 `[0]`。

## metadata与验证边界

`flash_mla_metadata(cache_seqlens,num_heads_q,num_heads_kv,...)` 返回当前NPU上的不透明int32 `[M]`，M由输入和设备决定。固定QK维576/V维512，KV头1；长度、heads、mask、窗口、Q布局及设备必须与主调用一致，任一变化需要重新生成。不能用其他MLA算子的1024或2048格式代替。固定e7原生后端的MetadataChecker强制metadata非空且第一维长度>0；原型metadata=None不是可直接执行的原生配置，须先生成并传入与主调用匹配的产物。torch_native忽略此参数的独立边界见下段。

torch_native仅覆盖TND Q、单头PA_BBND、TND/NTD输出、mask0/3、正Q/KV长度、无sink及默认窗口/最大长度，seqused_q 只能省略或等于各物理 Query 分段的完整长度，不支持部分有效 Query；mask_mode=3 还要求每请求 Lq<=Lkv。它忽略metadata且不适合图捕获。原生还依赖含两个算子的wheel和首次适配编译环境。复核应把metadata交给真实主接口后与覆盖范围内的独立参考比较；opaque tensor外观相同不证明调度正确。

## 固定producer的容量、设备及资源

实际SGL profile固定ops-transformer e7da，而API说明引用的旧提交文档仅作接口说明，不能覆盖profile的实际绑定。auto检查CANN严格等于9.2.0；显式包内实现分支直接加载绑定而不重复版本检查，这不是其他版本兼容证明。主算子与metadata都限定arch35注册，无独立调度回退。

厂商Python按cache_seqlens.size(0)取B，读取当前设备cube/vector核数C/Vc；读取属性异常时使用128/128作为分配估计。metadata容量为`M=align_up(16*((C+Vc)*B+1),4096)`个int32，字节数`4*M`，这里4096的单位是int32元素而非字节。C++按传入核数重复计算所需字节并检查output.nbytes，不以1024/2048固定尺寸替代。fake/meta路径也用相同容量公式，但构造meta Tensor不生成任何实际调度内容。

Python用`device="npu"`在当前NPU分配output；C++虽然从cuQ或cache长度选择outputDevice变量，该变量只用于缺省输入的空Tensor，并不会迁移已经分配的output。调用方应按公开合同把长度Tensor与当前设备对齐；不能将某长度位于另一NPU解释为输出随它自动迁移。

真实pair为`aclnnFlashMlaMetadataGetWorkspaceSize/aclnnFlashMlaMetadata`。query再次优先读取当前线程有效AIC/AIV资源，失败才取PlatformInfo核数；参数检查后分别将cuQ/cache长度/usedQ做框架Contiguous，加入AICPU任务，并返回executor workspace。Python分配估计与query实际采用的资源属于不同层，不能假定流控核数改变时二者永远相同，也不能仅因buffer容量足够就认为旧调度内容仍匹配新资源。

opaque结果不修改输入；长度、资源、设备、mask/窗口和布局改变后应重新生成并由对应主核消费。本节只展开API、容量与launcher边界，没有把CPU调度算法或Torch/CANN异步执行视为本次已验收；未执行编译、真机、图或数值测试。

## 证据与复核范围

本卡依据固定提交的第一方API说明蒸馏；架构编号按同提交构建说明映射为A2/A3（arch22）及950（arch35），具体子功能仍受正文限制。本次知识提取未执行编译、真机、数值或性能测试，未记录verified事件。

## 相关知识

- [稀疏共享MLA及2048项调度协议](sgl_sparse_flash_mla_and_metadata.md)

完整固定e7的Host/POD、48个typed layout/PA/mask/dtype selector与空域终点、FA/FD循环及资源同步，见[950 Flash MLA源码卡](../../operators/aclnn/transformer/attention/sgl_flash_mla_950.md)。其中的metadata生产消费按本接口单独闭合，不能沿上面Sparse链接复用其2048word协议；来源闭合仍不代表执行、数值或性能已验证。

## 约束与接入的固定源码

- [metadata_checker.cpp](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/flash_mla/op_host/checkers/metadata_checker.cpp)：原生metadata存在性和正长度检查。
- [torchapi_flash_mla.md](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/flash_mla/docs/torchapi_flash_mla.md)：独立BAND窗口语义。
