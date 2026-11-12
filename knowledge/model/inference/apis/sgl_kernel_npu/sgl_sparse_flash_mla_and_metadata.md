---
type: API
title: SGLang Sparse Flash MLA的SWA/CSA/HCA与metadata契约
description: 说明A2/A3 CANN9.2稀疏共享MLA的压缩位置域、强制sink、2048项metadata一致性及vendor导入顺序。
tags:
- task.implementation
- topic.attention
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/attention/sparse_flash_mla.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/attention/sparse_flash_mla_metadata.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/torch_native/attention/sparse_flash_mla.py
  role: constraint
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/attention/sparse_flash_mla.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/third_party/profiles/cann-9.2.0/ops_transformer.json
  role: supporting
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/sparse_flash_mla_metadata/op_host/op_api/aclnn_sparse_flash_mla_metadata.cpp
  role: primary
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/sparse_flash_mla/torch_extension/sparse_flash_mla.py
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/sparse_flash_mla/torch_extension/csrc/sparse_flash_mla.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/torch_extension/cann_ops_transformer/common/aclnn_common.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/sparse_flash_mla/docs/aclnnSparseFlashMla.md
  role: constraint
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/sparse_flash_mla/op_kernel/sparse_flash_mla_kernel_metadata.h
  role: header
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/sparse_flash_mla/op_kernel/arch35/common/smla_metadata_common.h
  role: header
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/sparse_flash_mla/op_kernel/sparse_flash_mla_template_tiling_key.h
  role: header
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/sparse_flash_mla/op_kernel/arch22/sparse_flash_mla_arch22_metadata.h
  role: header
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/sparse_flash_mla_metadata/op_kernel_aicpu/sparse_flash_mla_metadata_aicpu.cpp
  role: implementation
created_at: '2026-11-08T11:04:14Z'
updated_at: '2026-11-10T07:03:17Z'
platforms:
- a2
- a3
cann_versions:
- 9.2.0
aliases:
- sparse_flash_mla
- sparse_flash_mla_metadata
---

# SGLang Sparse Flash MLA的SWA/CSA/HCA与metadata契约

## 接口原型

```python
from sgl_kernel_npu.operators.attention import sparse_flash_mla

def sparse_flash_mla(
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
    seqused_ori_kv=None,
    seqused_cmp_kv=None,
    cmp_residual_kv=None,
    ori_topk_length=None,
    cmp_topk_length=None,
    sinks=None,
    metadata=None,
    softmax_scale=1.0,
    cmp_ratio=1,
    ori_mask_mode=0,
    cmp_mask_mode=0,
    ori_win_left=-1,
    ori_win_right=-1,
    layout_q="BSND",
    layout_kv="BSND",
    topk_value_mode=1,
    return_softmax_lse=False,
    impl="auto",
):
    ...
```

```python
from sgl_kernel_npu.operators.attention import sparse_flash_mla_metadata

def sparse_flash_mla_metadata(
    num_heads_q,
    num_heads_kv,
    head_dim,
    *,
    cu_seqlens_q=None,
    cu_seqlens_ori_kv=None,
    cu_seqlens_cmp_kv=None,
    seqused_q=None,
    seqused_ori_kv=None,
    seqused_cmp_kv=None,
    cmp_residual_kv=None,
    ori_topk_length=None,
    cmp_topk_length=None,
    batch_size=None,
    max_seqlen_q=None,
    max_seqlen_ori_kv=None,
    max_seqlen_cmp_kv=None,
    ori_topk=None,
    cmp_topk=None,
    cmp_ratio=None,
    ori_mask_mode=None,
    cmp_mask_mode=None,
    ori_win_left=None,
    ori_win_right=None,
    layout_q=None,
    layout_kv=None,
    has_ori_kv=None,
    has_cmp_kv=None,
    impl="auto",
):
    ...
```

## 三类共享KV路径

原生仅arch22，依赖CANN9.2.0及wheel内匹配的ops-transformer vendor。Q为FP16/BF16，D=512，Q头只能1/2/4/8/16/32/64/128、KV头1。Query/KV仅支持BSND/BSND、TND/TND、BSND/PA_BBND、TND/PA_BBND四组配对；非分页时必须同名布局，不能将各自布局列表任意组合；K与V共用同一份tensor。SWA只用原始窗口、ratio=1；CSA把原始窗口与稀疏压缩token合并，ratio=1/2/4；HCA使用连续压缩段、ratio=128。

普通SWA/CSA/HCA均必须设置ori_mask_mode=4，CSA/HCA还必须设置cmp_mask_mode=3；主调用与metadata即便统一使用签名默认0，也不能通过这些场景的原生校验。原始窗口右对齐query末端，A2/A3窗口固定127/0。压缩因果上限依据恢复长度 `Lcmp*ratio+residual`，不是直接复用未压缩token位置。CSA的cmp_sparse_indices是压缩token编号、int32、-1终止，最后一维K必须处于[1,8192]。按SGL本提交公开说明，原始ori_sparse_indices/ori_topk_length不支持，ori_topk必须0；这是SGL说明的范围，不能代替实际绑定的e7 CANN发布合同，差异见后文。cmp_topk_length为保留字段，即使CSA也不传。topk_value_mode仅1。

`cmp_kv`存在且cmp_mask_mode=3、ratio!=1时必须给int32 `[B]` cmp_residual_kv，每项小于ratio；mask0或ratio1反而不允许传。分页需对应两侧的block_table和seqused，页大小16对齐且<=1024。FP32 sinks `[num_heads_q]` 在A2/A3必需且非空，不能照签名默认None省略。

## 调度与分发

metadata由 `sparse_flash_mla_metadata` 生成，为不透明int32 `[2048]`。heads、D、layout、长度、KV存在性、压缩率、topk、mask和窗口都必须与主调用完全一致，否则行为未定义。metadata接口中多个属性默认None，而主接口默认1/0/-1，组合时应显式传参。参数改变后需重建，不解析内部调度值。

返回 `(attention_out,softmax_lse)`，输入不改。out同Q；LSE开启时TND为 `[1,T,QH]`，BSND为 `[B,1,S,QH]`，关闭时FP32空tensor。torch_native独立覆盖SWA/CSA/HCA和上述布局、sink与LSE，但TND Query需完整使用每个cu_seqlens_q存储分段，显式seqused_q必须等于相邻累计边界之差；TND原始/压缩KV同样要求各自seqused等于存储分段长度，否则抛NotImplementedError，有效长度短于存储分段不能直接用此参考验算。该参考忽略metadata、不能用于graph捕获；metadata本身没有独立torch_native调度器。

CANN9.2另有同名SparseFlashMla，需在torch_npu之前导入sgl_kernel_npu或启动前设置对应vendor路径；否则可能命中内置实现出现metadata尺寸错误。同环境不能另装声明同名算子的独立ops-transformer vendor覆盖wheel内版本。验证应检查实际vendor来源，再把metadata交给主算子与独立参考组合对比。

## metadata绑定、默认值与环境一致性

固定SGL profile把主算子及metadata同时绑定到ops-transformer e7da；SGL的auto先检查CANN版本严格等于9.2.0，再转包内实现。显式`cann_ops_transformers_cann920`分支自身直接调用绑定，没有重复auto的版本检查，不能把显式选择当兼容其他CANN版本的证据。两分支均有arch22注册范围，缺少vendor时给出构建profile提示而不回退torch_native。

厂商metadata包装对None的具体归一化为：batch和三种max长度、两种topk取0，ratio取1，两个mask取0，左右窗口取-1，Q/KV布局取BSND，`has_ori_kv/has_cmp_kv`都取True。特别是SWA主调用只传ori_kv时，metadata的has_cmp_kv缺省仍为True；必须显式传False并使长度/TopK/窗口与实际主调用一致。不能仅因多个属性都是可选就认为全默认值代表完整的SWA配置。

metadata C++ adapter按首个存在的cuQ、cuOri、cuCmp、usedQ、usedOri、usedCmp、residual、oriTopkLength、cmpTopkLength顺序确定输出device，否则使用当前NPU，分配int32 `[2048]`；缺省输入转换为该device的int32空Tensor，已有Tensor不被该helper迁移。shape外观不证明所有输入同设备或与后续Q一致。

真实两段pair是`aclnnSparseFlashMlaMetadataGetWorkspaceSize/aclnnSparseFlashMlaMetadata`。query读取当前线程AIC/AIV资源（失败回退PlatformInfo）和Soc，并查询`ACL_OPT_DETERMINISTIC`；查询变量以0初始化，返回后仅值等于3设置isBatchConsistency=True；读取失败只记录warning，不中断query。参数检查后分别将九个可选Tensor做框架Contiguous，再把资源/一致性标志和任务加入AICPU launcher，返回executor workspace；执行阶段调用CommonOpExecutorRun。metadata因而还绑定资源配置和一致性模式，不能在改变这些环境后仅凭长度没变就宣称复用安全。这里分析API/adapter契约，没有展开完整AICPU负载均衡算法或给出运行验收；opaque消费者的数值正确性仍需组合主算子核对。

## 证据与复核范围

本卡依据固定提交的第一方API说明蒸馏；架构编号按同提交构建说明映射为A2/A3（arch22）及950（arch35），具体子功能仍受正文限制。本次知识提取未执行编译、真机、数值或性能测试，未记录verified事件。

## e7 CANN合同与SGL说明的原始稀疏差异

同一固定profile实际绑定的e7 CANN文档另明确支持A2/A3的SWA原始稀疏场景：仅ori_kv、同时提供ori_sparse_indices与ori_topk_length，TND Query与PA_BBND KV组合，metadata ori_topk取索引最后轴K；每token的有效索引在[0,ori_topk_length)左对齐，余项建议−1。SGL文档/参考实现对ori分支的较窄描述仍保留，但实际vendor包装会透传参数，不能将说明中的“不支持”写成包装层必然拒绝。

该路径在完整源码卡中按DSpark单列，不把它冒充SGL torch_native已经覆盖的功能。e7 Doc的mask/窗口列举与本固定Host/预编译selector仍须分层核对；不能只按某个通用模板存在就承诺所有layout/mask组合可执行，也不能从CANN文档另支持950推出本SGL arch22入口覆盖950。输入shape、sink、metadata、长度和环境一致性仍由调用方按实际绑定检查。

## 固定metadata生产消费的结构边界

2048个int32是外观容量，e7实际SmlaMetadata只有80×9个FA word加80×8个FD word，共1360word、5440字节；FD从word720开始。AICPU GenMetadata用*metadataPtr={}只清这个结构，再填任务字段，尾部688word不在该初始化范围。主核arch22与AICPU均引用相同公共常量，不存在“一个把FD起点设成别的位置”的已证实格式错配；不应擅自把未初始化尾部当有效调度字段、做全2048项稳定hash比较或填入另一MLA协议。

FA九字段是enable、BN2/M/S2 start、BN2/M/S2 end、firstFD workspace index及S2 max轮数；当前A2/A3主核只读取FA的0..6，FD调度及其工作区字段并不自动成为该consumer的有效计算节点。metadata query的batch-consistency/资源配置仍参与producer，不由“FA/FD结构相同”推导所有一致性路线均已数值验证。

完整公开pair→POD/selector→MIX kernel、五计算族与68 typed selector、metadata生产消费及条件静态边界见[Sparse Flash MLA源码卡](../../operators/aclnn/transformer/attention/sgl_sparse_flash_mla.md)。本节解释固定协议用于匹配与复核，公共调用仍应把metadata作为opaque产物，不手工编辑内部字段。本次未执行真机、数值或性能测试。
