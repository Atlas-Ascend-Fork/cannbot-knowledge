---
type: API
title: SGLang prefill双索引入口的全局行掩码与选块分支
description: 比较带索引attention输出与纯选块两个prefill接口，明确全局query行因果语义、topk宽度变化和host同步。
tags:
- task.implementation
- topic.attention
- topic.compute.indexing
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/indexer/flash_prefill_bnsd_with_topk_idx.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/indexer/flash_prefill_bnsd_indexer.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/flash_prefill_bnsd_topk_from_score.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/indexer/flash_block_score_prefill.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/indexer/flash_block_score_decode.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/flash_prefill_bnsd_score.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/flash_prefill_bnsd_score_attn.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/flash_prefill_bnsd_indexer.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/flash_prefill_bnsd_with_topk_idx.py
  role: implementation
created_at: '2026-11-08T11:04:14Z'
updated_at: '2026-11-09T15:35:32Z'
platforms:
- a2
- a3
- '950'
aliases:
- flash_prefill_bnsd_with_topk_idx
- flash_prefill_bnsd_indexer
---

# SGLang prefill双索引入口的全局行掩码与选块分支

## 接口原型

```python
from sgl_kernel_npu.operators.indexer import flash_prefill_bnsd_with_topk_idx

def flash_prefill_bnsd_with_topk_idx(
    q,
    k_cache_bnsd,
    cu_seqlens,
    seq_lens,
    req_to_token,
    req_pool_indices,
    block_size_q,
    block_size_k,
    topk,
    sm_scale,
    score_type="max",
    qblock_mappings=None,
    per_query_seq_lens=None,
    *,
    impl="auto",
):
    ...
```

```python
from sgl_kernel_npu.operators.indexer import flash_prefill_bnsd_indexer

def flash_prefill_bnsd_indexer(
    q,
    k_cache_bnsd,
    v_cache_bnsd,
    cu_seqlens,
    seq_lens,
    req_to_token,
    req_pool_indices,
    block_size_q,
    block_size_k,
    topk,
    sm_scale,
    score_type="max",
    qblock_mappings=None,
    per_query_seq_lens=None,
    *,
    impl="auto",
):
    ...
```

## 两个入口与打分语义

纯选块 `flash_prefill_bnsd_with_topk_idx` 不接V、不返回attention；`flash_prefill_bnsd_indexer` 多接V并返回 `(idx_o,topk_idx)`。其余公共参数及选块规则相同，auto固定Triton，无失败回退。

Q为FP16/BF16 `[total_q,idx_heads,D]`，K/V为 `[pages,P,kv_heads,D]`，idx_heads是kv_heads的整数倍；每个query使用对应GQA的KV头。cu_seqlens `[bs+1]` 是packed query边界、seq_lens `[bs]` 是KV总长度，整数32/64；req_to_token的块首slot//P和req_pool_indices给物理页，P=block_size_k应2次幂。block_size_q只需正，不要求2次幂。

关键限制：有效key需 `p<L_request` 且 `p<=t`，t为打包后的全局query行，不是request内query位置，也不加历史KV前缀。per_query_seq_lens只影响选块边界，不能修复打分mask。因此有KV历史或多个request时不能当作标准右对齐causal。块分数在log2域做max或log2-sum-exp，空块-inf。带V入口的idx_o用全部可见key，而非选出的topk，不受topk或score_type改变。

## 两条选块路径

当per_query_seq_lens非None且idx_heads=kv_heads时，走融合路径：按分数逐轮选择，同分取较小块号；候选需分数>-inf且块首<=query_pos才写，否则-1且不补选，末槽再追加未选过的local。返回宽topk+1，要求topk>0，per_query长度total_q且int32，并须连续存储；Triton按 seq_lens_ptr+q_tok 读取而不使用stride，非连续切片即使长度/dtype正确也不能直接传入。

其他情况调用torch.topk取min(topk,K)，K=ceil(max(seq_lens)/P)，不足补-1；该路径不剔除-inf列、不追加local、同分顺序不保证，宽topk且允许topk=0。不能仅按接口名假定总有local或永远同shape。

可预给qblock_mappings六元组：4个连续int32映射、一张物理页表和host分组数；只有query边界/KV长度/页映射等元数据不变才能复用。入口仍读设备标量同步，给预计算映射也不能消除全部同步，不可直接用于graph捕获。

纯选块Triton可通过MINIMAX_NPU_PREFILL_SCORE_BLOCKS_PER_STEP=1/2/4调每步块数，语义不变。独立参考保留同掩码/选块行为，不能用它证明标准因果语义；验证应特别构造多request与历史前缀、同分/空分数块、融合与回退两种输出宽度。

## 旧prefill模块与新版分叶实现的映射

旧 `sgl_kernel_npu.indexer.flash_block_score_prefill` 包含score、score_attn、topk三个自有JIT及两个组合Host。完整逐项比较后，`_prefill_bnsd_score_kernel`、`_prefill_bnsd_score_attn_kernel`、`_prefill_topk_from_score_kernel`（含装饰器/参数）与新版对应分叶实现相同。`_build_qblock_mappings`及从旧decode复制到新score文件的_next_power_of_2/_choose_num_score_chunks也相同；score NW/NS=4/2、score_attn=8/2的globals一致，不因分文件改变算法。它们是源码副本，非共享同一Python函数/JIT缓存的转发别名。

新版score/score_attn Host只多score_type早期断言，topk Host多topk>0断言；旧kernel已有score_type static_assert但失败阶段不同。两个组合Host除说明文字/import分叶路径外执行逻辑/default相同。当前页保存**完整已读算法Reference**，没有把这些叶子说成已有完整Operator，也不把含torch.topk的组合入口冒称source_closed。

### 映射生成、POD式参数与GM布局

设T=total_q，H=idx_heads，Hkv=KVH，G=H/Hkv，D=head_dim，P=page_size=block_size_k，Kmax=ceil(max(seq_lens)/P)。Host对seq_lens.max().item()做Device标量同步；不给qblock_mappings时，再用q_lens=cu[1:]−cu[:-1]、qb_per_req=ceil(q_lens/block_size_q)，sum().item()求总query-block数Qb。repeat_interleave/cumsum构造每block的request、qstart、qend、local qblock及KV长度；逻辑块首列 `min(blockId*P,req_to_token.shape[1]−1)` 的slot//P成为物理页表[Qb,Kmax]。输出六元组为四个int32[Qb]映射、int32[Qb,Kmax]页表、Host整数Qb。四映射加页表逻辑容量4*Qb*(4+Kmax)字节，另有Torch int64转换/重复/索引临时，物理峰值与allocator生命周期未在本源证明。

Device标量和所有stride直接由Host传入，没有自有C++ POD：Q地址 `token*s_qt+head*s_qh+d*s_qd`；K/V地址 `physical*s_page+offset_in_page*s_token+kvhead*s_head+d*s_d`；页表 `qb*s_bq+logical_block*s_bn`；score布局FP32[H,T,Kmax]。metadata映射直接线性读，预给六元组必须保持真实shape/类型/连续和值域，不能因Host不重建就忽略生产者。元数据复用不检查内容版本，req、cu、seq、页映射变化后须由调用方重建；来源没有自有tensor_cache。

### 纯score的Cube逻辑与多块trick

Qp=nextPOT(block_size_q)，Hp=nextPOT(G)，Dp=nextPOT(D)，M=Qp*Hp；kernel把(query_lane,group_head)展成M行，qi=offM//Hp、hh=offM%Hp，head=kvhead*G+hh，raw_token=qstart+local_qblock*Qp+qi。load token先夹在[qstart,qend−1]，有效row仍以raw_token<qend与hh<G为mask，故尾部phantom不跨request取Q。地址中的local步长为Qp；query-block映射按原block_size_q计数，非二次幂时可能产生额外的全mask尾program，但连续Qp tile仍覆盖request且raw_token<qend约束写回，不能据此新增block_size_q须二次幂的限制。

score-chunk数C先按blocks_per_chunk16、max_chunks32与program_cap32768选向下二次幂，再Host限在[1,Kmax]。每program=(qb,chunk,kvhead)，grid=(Qb*C,Hkv)；实际每request num_blocks=ceil(Lkv/P)，chunk_span=max(1,ceil(num_blocks/C))，逐chunk覆盖对应块。空chunk直接return，score先torch.full(−inf)初始化。

```text
Q = load [M,Dp], masked row/head/feature tails → input dtype
for each assigned logical KV block:
  physical = block_table[qb,logical]
  K = load [Dp,Np]
  qk = tl.dot(Q,K) * (sm_scale * 1.4426950409)  # FP32 accumulator/log2域
  qk = where(key_pos<Lkv && key_pos<=raw_token,qk,−inf)
  score = max(qk) or max(qk)+log2(sum(exp2(qk−max)))
  lse NaN显式改−inf
  store score[head,raw_token,logical] for valid row
```

env MINIMAX_NPU_PREFILL_SCORE_BLOCKS_PER_STEP只接受1/2/4。1时Np=nextPOT(P)，每次一块；2/4时Np=nextPOT(P*BPS)，把BPS个连续逻辑块并成一次dot，以offN//P选页、offN%P选页内token，页表越本chunk尾时clamp到最后有效块，逐子块mask归约并只写logical<chunk_end项。这样减少dot调用/共享Q读，但不把不同dot tile下的舍入关联声明为逐位相同。P非二次幂时单块Np可超过实际page宽，kernel的K页内offN没有P额外mask，故原合同中P应二次幂不能由“已nextPOT”放宽。

### score_attn的在线归一化与精度

grid=(Qb,Hkv)，Np=nextPOT(P)，没有score chunk；同一组Q/K dot同时写每块score与全可见KV attention。局部m初值−1e30、l=0、acc[M,Dp]=0 FP32：
```text
submax=max(qk); m_new=max(m,submax)
p=exp2(qk−m_new)
acc = acc*exp2(m−m_new) + tl.dot(p.to(V.dtype), V)
l = l*exp2(m−m_new) + sum(p)
m = m_new
idx_o = acc/l
```

P先降到V.dtype再PV dot，acc/l保持FP32再写Q dtype。score_type只影响块score，不改变idx_o；topk筛选在其后，不把attention限制到已选块。有限m floor使单个全mask块可不增加l/acc，但若一行整个域没有任何有效key，l一直0，最终acc/l仍无有限输出保证，不能按注释“no NaN”泛化。lse score中的NaN有显式−inf替换，max score和attention最终结果没有统一NaN清洗。

### 自有topk与local追加

融合topk仅当per_query_seq_lens存在且H==Hkv被组合Host选择；独立Host还检查score FP32、length int32且长度T，新版多topk>0。Kp=nextPOT(Kmax)，每program处理BSQ个query和一head：BSQ从1开始，在BSQ<16且下一倍tile的4*(2*BSQ)*Kp≤32768时翻倍；这限制逻辑score tile，Kp过大时最小BSQ1也没有额外资源fallback。

```text
score_tile = load [BSQ,Kp], row/column tails→−inf
for rank=0..topk−1:
  best=max(scores); pos=min index where score==best
  valid=(best>−inf) && pos<Kmax && pos*P<=max(length−1,0)
  out[rank]=valid?pos:−1
  scores[pos]=−inf                         # 先选再判causal，不补选
local=min(max(length−1,0)//P,Kmax−1)
out[topk]=local已在已写候选中?−1:local
```

同分取低块号；候选彼此不额外去重，末local只与候选去重。无有限score时topk槽−1仍可能追加local0；kernel加载out[0:TOPK]用于去重，tl.arange直接使用TOPK，Host没有二次幂检查，任意正topk的工具链准入未在本次编译验证。score NaN没有独立通用scrub；整数pos*P/length转int32需防溢出。

### 逻辑资源、同步与闭包边界

| 节点 | GM交接与容量 | program逻辑活跃值 | ordering/lifetime |
|---|---|---|---|
| score | FP32 score 4*H*T*Kmax B，预填−inf | Q:M*Dp*e；K:Dp*Np*e；qk:M*Np*4；score向量M*4 | 不同(qb,chunk,head)写独立score域；Host buffer活至后续topk消费。 |
| score_attn | 同score；idx_o e*H*T*D B，Host先zeros | 另有V:Np*Dp*e，p:M*Np*4，acc:M*Dp*4，m/l各M*4 | 单program在线循环；最后归一化写Q dtype，无跨programbarrier。 |
| Triton topk | 输出4*H*T*(topk+1) B | score tile4*BSQ*Kp、选中索引BSQ*topk及mask/向量 | 同stream消费完整score；无atomic或自有workspace，局部输出唯一owner。 |
| torch.topk回退 | 输出indices转int32、可选cat补−1 | 核心TopK实现/workspace不在固定集合 | 不是普通view/copy边界，不能为组合入口伪造完整Operator闭包。 |

上述为逻辑tensor payload/traffic，Triton实际UB/L1/L0、寄存器、dot lowering、pipeline和跨pipe同步由编译器实现，不能把逻辑数组简单相加当物理峰值。Host映射的repeat_interleave/cumsum/gather和标量同步是外部Torch元数据生产；组合路径的torch.topk是独立核心数学边界，现有Reference只说明参数、顺序和可见资源。没有自有Tensor owner/event跨stream保护，调用方须维持metadata、score、中间与输出到当前流消费结束。

本段保留旧/新相同Device算法与真实差异，不新建重复或冒名Operator，不将旧raw检查较弱当额外平台支持；本次未执行编译、数值、真机、graph或性能测试。

### 增量固定实现来源

- [python/sgl_kernel_npu/sgl_kernel_npu/indexer/flash_block_score_prefill.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/indexer/flash_block_score_prefill.py)。
- [python/sgl_kernel_npu/sgl_kernel_npu/indexer/flash_block_score_decode.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/indexer/flash_block_score_decode.py)。
- [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/flash_prefill_bnsd_score.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/flash_prefill_bnsd_score.py)。
- [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/flash_prefill_bnsd_score_attn.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/flash_prefill_bnsd_score_attn.py)。
- [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/flash_prefill_bnsd_topk_from_score.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/flash_prefill_bnsd_topk_from_score.py)。
- [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/flash_prefill_bnsd_indexer.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/flash_prefill_bnsd_indexer.py)。
- [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/flash_prefill_bnsd_with_topk_idx.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/flash_prefill_bnsd_with_topk_idx.py)。


## 证据与复核范围

本卡依据固定提交的第一方API说明蒸馏；架构编号按同提交构建说明映射为A2/A3（arch22）及950（arch35），具体子功能仍受正文限制。本次知识提取未执行编译、真机、数值或性能测试，未记录verified事件。

## 相关知识

- [逻辑块转FIA页表与长度](sgl_fia_prep.md)
- [消费选块的GQA入口](sgl_gqa_shared_sparse_decode.md)
