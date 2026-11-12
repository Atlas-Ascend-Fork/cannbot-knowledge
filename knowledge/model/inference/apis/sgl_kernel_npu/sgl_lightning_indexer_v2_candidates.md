---
type: API
title: SGLang Lightning Indexer V2的候选块与稀疏消费者
description: 说明A3/CANN9.2加权ReLU打分、候选块位置域、两种返回协议、sparse consumer和不被主核消费的metadata。
tags:
- task.implementation
- topic.attention
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/indexer/lightning_indexer_v2.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/indexer/lightning_indexer_v2_metadata.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/indexer/sparse_lightning_indexer.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/indexer/lightning_indexer_v2_metadata.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/indexer/lightning_indexer_v2.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/indexer/sparse_lightning_indexer.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/indexer/indexer_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/third_party/profiles/cann-9.2.0/ops_transformer.json
  role: supporting
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/lightning_indexer_v2/docs/aclnnLightningIndexerV3.md
  role: primary
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/lightning_indexer_v2/torch_extension/lightning_indexer.py
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/lightning_indexer_v2/torch_extension/csrc/lightning_indexer.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/lightning_indexer_v2/op_host/op_api/aclnn_lightning_indexer_v2.h
  role: header
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/lightning_indexer_v2/op_host/op_api/aclnn_lightning_indexer_v2.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/lightning_indexer_v2/op_host/op_api/aclnn_lightning_indexer_v3.h
  role: header
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/lightning_indexer_v2/op_host/op_api/aclnn_lightning_indexer_v3.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/lightning_indexer_v2/op_host/lightning_indexer_v2_tiling.h
  role: header
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/lightning_indexer_v2/op_host/lightning_indexer_v2_tiling.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/lightning_indexer_v2/op_kernel/lightning_indexer_v2.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/lightning_indexer_v2/op_kernel/arch22/lightning_indexer_v2_kernel_arch22.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/sparse_lightning_indexer/docs/aclnnSparseLightningIndexer.md
  role: supporting
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/sparse_lightning_indexer/op_host/sparse_lightning_indexer_tiling.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/sparse_lightning_indexer/op_host/sparse_lightning_indexer_tiling.h
  role: header
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/version.cmake
  role: supporting
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/lightning_indexer_v2_metadata/op_host/op_api/aclnn_lightning_indexer_v2_metadata.h
  role: header
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/lightning_indexer_v2_metadata/op_host/op_api/aclnn_lightning_indexer_v2_metadata.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/lightning_indexer_v2_metadata/op_host/op_api/lightning_indexer_v2_metadata.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/lightning_indexer_v2_metadata/op_host/lightning_indexer_v2_metadata_check.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/lightning_indexer_v2/op_kernel/lightning_indexer_v2_metadata.h
  role: header
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/lightning_indexer_v2_metadata/op_kernel_aicpu/lightning_indexer_v2_metadata_aicpu.h
  role: header
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/lightning_indexer_v2_metadata/op_kernel_aicpu/lightning_indexer_v2_metadata_aicpu.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/attention/common/op_kernel/aicpu_common.h
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/torch_extension/cann_ops_transformer/common/aclnn_common.h
  role: implementation
created_at: '2026-11-08T11:04:14Z'
updated_at: '2026-11-10T07:03:17Z'
platforms:
- a3
cann_versions:
- 9.2.0
aliases:
- lightning_indexer_v2
- lightning_indexer_v2_metadata
- sparse_lightning_indexer
---

# SGLang Lightning Indexer V2的候选块与稀疏消费者

## 接口原型

```python
from sgl_kernel_npu.operators.indexer import lightning_indexer_v2

def lightning_indexer_v2(
    q,
    k,
    w,
    topk,
    *,
    cu_seqlens_q=None,
    cu_seqlens_k=None,
    seqused_q=None,
    seqused_k=None,
    cmp_residual_k=None,
    block_table=None,
    output_idx_offset=None,
    metadata=None,
    max_seqlen_q=-1,
    layout_q='BSND',
    layout_k='BSND',
    mask_mode=0,
    cmp_ratio=1,
    return_value=0,
    candidate_topk_blocks=None,
    candidate_block_size=None,
    impl='auto'
):
    ...
```

```python
from sgl_kernel_npu.operators.indexer import lightning_indexer_v2_metadata

def lightning_indexer_v2_metadata(
    num_heads_q,
    num_heads_k,
    head_dim,
    topk,
    cu_seqlens_q=None,
    cu_seqlens_k=None,
    seqused_q=None,
    seqused_k=None,
    cmp_residual_k=None,
    batch_size=None,
    max_seqlen_q=None,
    max_seqlen_k=None,
    layout_q=None,
    layout_k=None,
    mask_mode=None,
    cmp_ratio=None,
    *,
    impl='auto'
):
    ...
```

```python
from sgl_kernel_npu.operators.indexer import sparse_lightning_indexer

def sparse_lightning_indexer(
    q,
    k,
    w,
    topk,
    candidate_block_indices,
    *,
    cu_seqlens_q=None,
    cu_seqlens_k=None,
    seqused_q=None,
    seqused_k=None,
    cmp_residual_k=None,
    block_table=None,
    output_idx_offset=None,
    metadata=None,
    max_seqlen_q=-1,
    layout_q='BSND',
    layout_k='BSND',
    mask_mode=0,
    cmp_ratio=1,
    return_value=0,
    candidate_block_length=None,
    candidate_block_size=8,
    impl='auto'
):
    ...
```

## 打分与输入

三接口面向CANN9.2.0/A3，auto固定选包内cann_ops_transformers_cann920，不回退。Q为FP16/BF16 `[B,Q,H,128]` 或TND `[Tq,H,128]`，H=1..64；K只有1头、同dtype，可BSND/TND/PA_BBND；W是FP32、shape=q去掉末维。打分为 `sum_h(w_h*relu(dot(q_h,k_j)))` 再选TopK。mask_mode=0/3，3为右对齐因果，cmp_ratio为1..128的2次幂，压缩位置域遵循上游。

TND两侧需各自int32累计边界；分页KV需int32页表和seqused_k，页大小16..1024且16对齐，仅分页K第0轴允许非连续。两个主算子在压缩ratio!=1且mask3时需cmp_residual_k，每项<ratio；ratio=1或mask_mode=0时必须为None，非空余数会被Dense和Sparse Host分别拒绝。此禁用条件属于两个主算子，metadata producer的校验另见后文。两个主算子 lightning_indexer_v2/sparse_lightning_indexer 在A3不支持seqused_q/output_idx_offset，必须None，且其 max_seqlen_q 只接受-1。这项 -1 限制不适用于 lightning_indexer_v2_metadata：metadata 的 max_seqlen_q/max_seqlen_k 表示调度长度，None 转为-1，来源示例显式传 max_seqlen_q=1、max_seqlen_k=512，包装器按值透传。所有索引值合法性由调用方保证，不在launch前读回设备值。


固定 e7da 实现进一步限定 layout：Sparse Host 的 `GetQueryKeyAndOutLayout` 之前属性检查要求非PA时 Q/K 同名，只能 BSND/BSND、TND/TND 或 BSND/PA_BBND、TND/PA_BBND；SGL 各自枚举合法不等于任意2×3组合都可达。已单独核对 Dense LI 的 `LIV2InfoParser::GetAndCheckAttrParaInfo`，其 arch22 路线同样有非PA同名检查；这是该实现的独立证据，不是由 Sparse 限制泛化。

## 普通、候选及稀疏返回

普通V2 topk为1..2048或3072/4096/5120/6144/7168/8192，candidate_topk_blocks=None时返回 `(indices,values)`。仅当candidate_topk_blocks显式传非None值（包括-1关闭候选）时切换四输出 `(indices,values,blocks,length)`；只设置candidate_block_size不触发四输出。正候选数为64..2048的64倍数，候选块大小2/4/8/16/32/64，默认8；启用候选要求topk<=2048。


固定绑定的真实 ACLNN pair 如下，不能按 SGL 函数名 `lightning_indexer_v2` 将所有调用都归到 V2：

| SGL/厂商 Python 选择 | C++ adapter | 实际两段式入口 | 返回与内部复用 |
|---|---|---|---|
| candidate_topk_blocks=None | LightningIndexer | aclnnLightningIndexerV2GetWorkspaceSize / aclnnLightningIndexerV2 | 两返回；V2兼容层固定 candidateTopkBlocks=-1、candidateBlockSize=8，以空候选输出占位转发 aclnnInnerLightningIndexerV2 |
| candidate_topk_blocks 非None，包括显式 -1 | LightningIndexerCandidateMode | aclnnLightningIndexerV3GetWorkspaceSize / aclnnLightningIndexerV3 | 四返回；V3保留off/on属性及候选输出参数，转发同 aclnnInnerLightningIndexerV2；-1时后两返回空，不等于调用V2 |
| sparse_lightning_indexer | SparseLightningIndexer | aclnnSparseLightningIndexerGetWorkspaceSize / aclnnSparseLightningIndexer | 两返回；只消费候选，独立consumer实现 |

只指定 candidate_block_size 不触发四返回，default 分支不把它传入V2旧签名；显式四返回分支中 None 块大小转为8。这里描述版本接入与复用关系，不将V2/V3旧接口改名或替换成 Sparse，也不把同一 inner bridge 误当两个独立数学算子。Sparse完整源码级实现另见[稀疏消费者A3算子卡](../../operators/aclnn/transformer/attention/sgl_sparse_lightning_indexer.md)。

普通indices为int32 `[B,Q,1,topk]` 或 `[Tq,1,topk]`，无效-1；values开启时FP32同shape、无效-inf，否则空。启用候选时blocks为int32 `[B,Q,1,C]` 或 `[Tq,1,C]`，C=candidate_topk_blocks，无效槽-1；关闭候选时为空。候选以块内最大位置分数打分，最后可达块用+inf固定进入候选；候选块号是压缩后batch内相对块号、不带offset、槽位无序，length为保留空int32 tensor。候选只能同一次forward复用，消费者须同块大小和兼容KV位置域。

`sparse_lightning_indexer` 仅在candidate_block_indices内选位置，候选C为64..2048的64倍数；topk<=2048、candidate_block_length仅None/空tensor。负值、越界和重复候选不增加新位置。返回两项，indices无效-1，启用的values无效为0，这一点不同于普通V2的-inf。

## metadata、依赖与验证

配套metadata返回NPU int32 `[2048]`、底层经AICPU调用。固定 e7da 的 A3/arch22 **Dense LI V2/V3** 路线允许 `metadata=None`；若传入，`ValidateInputShapesMatch` 要求 numel=2048，主 arch22 body 不消费其调度内容。这与 Sparse consumer 的合同不同：**`sparse_lightning_indexer` 的 CANN 主入口必须 `metadata=None`**，`SparseLIInfoParser::GetAndCheckOptionalInput` 对非空 metadata 指针直接报错。SGL wrapper 只做 int32/同设备检查，且文档写“不消费/可省略”，不能据此推导 vendor 接收非空 Tensor；即便先生成 `[2048]` metadata，也不能直接传入本 Sparse CANN 入口。

metadata 与依赖打包用于完整绑定符号，但不应为 arch22 中未被消费的 opaque 调度内容构造数值golden。Dense/Sparse 的相关长度、head、mask、ratio仍须符合各自合同。下文补充实际metadata producer的调用与内部格式，不将 arch22 结论外推到其它架构的 metadata 快路径，也不将格式分析写成AICPU工程运行验收。

wheel需含vendor、绑定、LICENSE、manifest及metadata AICPU资源，首次调用可能JIT编译。独立torch_native只覆盖BSND/BSND、ratio1、mask0/3和可选有效Q/K长度，不支持packed/paged/compressed；同分顺序不保证。验证候选复用时检查块位置域和padding，不用同分严格索引顺序充当数值正确性唯一信号。

## metadata producer的实际校验与定义域

独立pair是`aclnnLightningIndexerV2MetadataGetWorkspaceSize/aclnnLightningIndexerV2Metadata`，不要因主接口已有V3就改称V3Metadata。厂商Python将None的batch_size/max_seqlen_q/max_seqlen_k/layout_q/layout_k/mask_mode/cmp_ratio依次转换为`0/-1/-1/BSND/BSND/0/1`；这些是默认值，未保证默认组合可执行。特别是实际query检查BSND侧对应max_seqlen必须正，即使提供seqused也仍检查；全部省略会被拒绝。TND侧须有累计边界，PA_BBND须有seqused_k；非PA仍要求Q/K布局同名。

C++输出设备按第一个存在的`cuQ→cuK→usedQ→usedK→residual` Tensor选择，否则用当前NPU，分配int32 `[2048]`。缺省Tensor被替换成该设备的int32空Tensor后交框架转换；不会自动把调用方已有的不同设备Tensor迁移到输出设备。准备主调用时应统一设备，不能把存在一个NPU长度Tensor等同所有元数据已一致。

query先获得当前线程资源核数，获取失败才回退PlatformInfo；AIC/AIV各要求1..80，再校验headsQ1..64、headsK1、D128、topk1..8192、batch_size非负、max长度>=-1、mask0/3及ratio1..128。这里ratio只有区间检查、topk只有连续区间检查，弱于主算子的2次幂ratio与TopK合法集合；producer返回成功不能代替主算子准入。所有存在的长度/余数Tensor须一维int32，输出必须一维int32且长2048；非连续可选输入随后分别经框架Contiguous，失败返回错误。

有效batch从used优先、TND累计长度减1其次、显式batch最后推导，Q/K推导须一致；TND同时给used时其长度须与累计边界匹配，residual长度须等于有效batch。CPU Prepare还检查累计边界首项0且单调不减，used非负且不超过BSND最大长度或TND实际分段，residual在`[0,ratio)`；所以query通过不等于异步AICPU执行必成功。部分公开属性是int64，但CPU成员与batch推导含int32窄化，不能将任意大属性视为已支持。

## metadata的调度机制与opaque边界

固定CPU流程为Prepare、BalanceSchedule、GenMetadata，成功后才尝试GenFastMetadata。长度优先used、其次TND差分、最后BSND最大长度；压缩K通过`K*ratio+residual`还原因果位置域。A3所选分支以S1基本长度4、M=4*headsQ、S2基本块2048估算工作；成本为`6*ceil(M/16)+10*ceil(S2/64)`，并区分满/尾块和右对齐causal有效K范围。

调度按batch、M行、K块依次装入核负载预算，使用末块成本一半的容差，并在必要时强制分配一块以推进游标；K跨核拆分另记录归约工作区索引和份数，再按`split份数*M行数`对AIV归约任务分行。全零工作仍启用一个AIC范围，普通计划保留末尾零成本batch给最后一个有效核，以便对应消费者处理空输出。这里描述producer计划，不保证本卡A3主核实际使用该计划。

内存头文件将前80*8个uint32用于AIC范围，后80*8个用于AIV归约；每AIC含enable、BN2/M/S2起止和首归约workspace索引，每AIV含enable、BN2/M、workspace索引/份数、M起点/行数，第8word保留。其后是仅供匹配版本的fast header与两组32核tile起止。`GenMetadata`仅将该1346word结构清零再写字段，Tensor实际有2048word：尾部702word没有本实现的初始化保证，不能对整个返回Tensor做逐位golden或把尾部当协议。

GenFastMetadata的Soc门只接受Ascend950且另有32核、head/D/TopK/ratio、长度及利用率等限制；本SGL公开metadata入口仍限A3，不能据CPU文件存在此分支扩大本卡平台。opaque元数据应与同包主算子、设备资源和长度配套；不要把内部成本或word偏移当跨版本公共ABI。该AICPU节点未含Cube计算，查询设备核数也不意味着执行族是Cube，不能为套用VV/CV分类改写成AIV算子。

## 证据与复核范围

本卡依据固定 SGL dda6 公开说明及其 profile 精确固定的 ops-transformer e7da（version.cmake=9.2.0）实现蒸馏；架构编号按同提交构建说明映射为A2/A3（arch22）及950（arch35），具体子功能仍受正文限制。本次知识提取未执行编译、真机、数值或性能测试，未记录verified事件。
