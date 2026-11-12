---
type: API
title: SGLang decode块索引器的score-only与packed边界
description: 说明flash_decode_bnsd_with_topk_idx的支持分支、逻辑块索引、local追加、packed单KV头及调度参数边界。
tags:
- task.implementation
- topic.attention
- topic.compute.indexing
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/indexer/flash_decode_bnsd_with_topk_idx.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/flash_decode_bnsd_with_topk_idx.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/torch_native/indexer/flash_decode_bnsd_with_topk_idx.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/indexer/flash_block_score_decode.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/append_local_block_to_topk_idx.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/attention/gqa_share_sparse_attention.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/flash_decode_bnsd_with_gqa_share_sparse.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/pytorch_extensions.cpp
  role: implementation
created_at: '2026-11-08T11:04:14Z'
updated_at: '2026-11-10T07:03:17Z'
platforms:
- a2
- a3
- '950'
---

# SGLang decode块索引器的score-only与packed边界

## 接口原型

```python
from sgl_kernel_npu.operators.indexer import flash_decode_bnsd_with_topk_idx

def flash_decode_bnsd_with_topk_idx(
    q,
    sink,
    k_cache_bnsd,
    v_cache_bnsd,
    block_table,
    seq_lens,
    max_seqlen,
    block_size,
    topk,
    init_blocks,
    local_blocks,
    sm_scale=None,
    score_type="max",
    disable_index_value=False,
    num_kv_chunks=None,
    max_num_kv_chunks=8,
    use_triton_topk=None,
    num_topk_chunks=None,
    use_chunked_score=True,
    score_blocks_per_chunk=16,
    score_max_chunks=32,
    req_to_token=None,
    req_pool_indices=None,
    max_num_blocks=None,
    num_pages=None,
    sanitize_page_ids=False,
    packed_seq_lens=False,
    runtime_fill_only=False,
    runtime_score_short_max_blocks=0,
    runtime_score_short_chunks=0,
    fused_append_local=False,
    use_native=True,
    *,
    impl="auto",
):
    ...
```

## 受支持入口

auto与Triton同入口，没有Ascend C或TileLang实现，use_native只是无作用兼容参数。公开支持的是 `disable_index_value=True`：topk<=0返回 `(None,empty[QH,B,0])`，topk>0返回 `(None,topk_idx)`。disable_index_value=False的全量attention仅保留在Triton中、不在支持/验证范围，torch_native明确拒绝。

Q为FP16/BF16 `[B,QH,D]`，K为 `[numPages,BS,KVH,D]`，QH是KVH的整数倍；score-only不需要V，可传None。块分数为缩放QK的max或logsumexp，默认scale=D^-0.5；init_blocks与local_blocks分别把候选分数改为1e30/1e29，同类强制块产生同分、顺序与超topk取舍未定义，不基于有冲突的文字优先级假设稳定排序。

页表和direct映射二选一；direct需要req_to_token、req_pool_indices、正max_num_blocks/num_pages且满足max_num_blocks * block_size <= req_to_token.shape[1]；这项完整容量断言在topk<=0空输出分支之前也执行，不能只保证块首地址可访问，sanitize只夹direct物理页。block_table列宽必须覆盖实际块数，即使未断言也不可越界。BS应为2次幂，生产常用128。packed_seq_lens只支持score-only且KVH=1，否则score与merge行映射不一致。seq_lens可为逐request或packed逐行长度。

## 输出、local与验证

topk_idx是int32逻辑块号 `[QH,B,topk]`；topk>0且fused_append_local=True变为topk+1，页表路径此时也必须max_num_blocks。无效/去重槽为-1，但有效候选耗尽后可能重复块0；不能把它按唯一集合解释。参考全段计算仅适合正确性，topk同分顺序未定义。

max_seqlen、score_blocks_per_chunk和score_max_chunks共同决定score分片与静态FILL_ONLY分支，不能无条件视为仅调度。调参不改变无并列分数TopK的前提包括候选完整：FILL_ONLY时每个运行期分片的实际块数不超过topk，merge读取范围涵盖全部有效候选，packed行组的阈值选择须与各行一致。runtime短上下文参数须成对有效；packed行组跨短阈值时可能截断候选。

非packed也存在静态失效组合：BS=128、topk=16、max_seqlen=8192、实际长度4096、runtime_score_short_max_blocks=32、runtime_score_short_chunks=1，默认score_blocks_per_chunk=16由64块上界分为4片并启用FILL_ONLY，运行期却把32块放到1片，直接写入超过每片16候选容量，短分支merge只读前16项；改为score_blocks_per_chunk=32会关闭FILL_ONLY、走分片内TopK。因此互异分数也不足以保证两配置等价，应避开该容量不一致组合并以独立参考验证；这是固定源码分支分析，未完成真机复现。use_triton_topk/num_topk_chunks/use_chunked_score/use_native为兼容无作用参数。

验证用互不相同的块分数比较score-only，覆盖max/lse、direct/page表、local追加和packed单KV头。不要使用未获支持的全量attention分支、同分确定顺序或只检查返回宽度推导正确性。

## 旧decode入口、同body映射与外部native边界

本节旧入口是 `sgl_kernel_npu.indexer.flash_block_score_decode.flash_decode_bnsd_with_topk_idx`，不是上文 `operators.indexer` 公共入口。旧Host保留use_native=True，尝试外部native；新版 `implementation.triton.indexer.flash_decode_bnsd_with_topk_idx` 删除这条分支，并删除use_triton_topk/num_topk_chunks/use_chunked_score等已无作用的内部形参，公共wrapper仍可接兼容参数但不转成native执行。新版还多seq_lens.rank1、block_table.rank2，以及packed_seq_lens时KVH==1检查。旧Host少检查不使多KVH packed域自动合法。

两版全部共享的实际Triton body、参数/default和helpers相同。唯一JIT装饰器差异是旧 `_decode_bnsd_score_topk_chunk_kernel` 外面重复一层H/D heuristics，两层H/D lambda相同，新版只保留含H/D/T的一层；数学和选择值一致，不是一个新的算法。_SCORE_CHUNK_NW/NS均4/2，_choose_num_kv_chunks/_choose_num_score_chunks及merge/attention kernels一致。独立定义的两个模块不共享同一Python函数/JIT缓存对象。

### 外部minimax符号不是SAS或Lightning的别名

旧_get_native_minimax_indexer以无参数lru_cache(maxsize=1)缓存lookup结果：先import sgl_kernel_npu，再getattr(torch.ops.npu,"minimax_indexer",None)，ImportError/RuntimeError时返回None。固定提交csrc没有该符号的注册/实现；已注册的npu_sparse_attention_score与lightning_indexer名称、ABI均不同，不能根据注释把它们替换进这个callee。若首次得到None，后续环境注册变化不会自动重查；也不能保证不同模块共享这份缓存。

旧native选择完整条件是disable_index_value=True、topk>0、lookup非None、use_native=True、QH为偶数、D=128、seq_lens长度为B或B*(QH/KVH)。它把Q reshape[B,1,QH,D]，创建未初始化w_dummy[B,1,QH]、ones int32[B]，长度转int32；block_table转int32或direct模式传None，另外传req_to_token/req_pool_indices。实际forward序列如下：

```text
external_minimax_indexer(q_in, K, w_dummy, aq_dummy, sl_int32, bt_int32_or_None,
  "BSND", "PA_BSND", topk, 0, init_blocks, local_blocks, float(sm_scale),
  req_to_token_or_None, req_pool_indices_or_None, int(fused_append_local), packed_mode)
return None, external_output.view(QH,B,topk+append_local)
```

这仅闭合wrapper转换与forward，外部callee核心、w_dummy是否消费、布局/精度/平台与workspace未在固定集合证明；score_type没有被传给它，不能声称旧native的max/lse与Triton等价。没有lookup或guard不成立时才回到下面Triton。该外部可选分支不扩大本页公共平台支持，也不冒称source_closed。

### Score-only的地址、分块与TopK

设G=QH/KVH，Hp=max(16,nextPOT(G))，Dp=nextPOT(D)，Tp=nextPOT(topk)，Np=nextPOT(block_size)。C由max_seqblock=ceil(max_seqlen/BS)、blocks_per_chunk、max_chunks、program_cap32768与B*KVH网格上界选向下二次幂，至少1。grid=(B*C,KVH)，program将pid除余得到request b、chunk c、KV头hkv；head基为hkv*G。Q tile[Hp,Dp]按真实stride加载，K tile[Dp,Np]按physical_page、页内offset、KV头和D stride加载，尾head/D以mask补0。

普通seq_lens布局stride_sl_b=1、stride_sl_h=0；packed为G、1，使第b组各row有独立可见长度。kernel取这些row块数的最大值划chunk，逐row应用causal key_pos<row_length。页表模式从block_table[b,logical]读物理页；direct模式先取req_idx=req_pool_indices[b]，列min(logical*BS,max_cols−1)，slot=req_to_token[req_idx,col]，physical=slot//BS；sanitize仅direct把physical夹0..num_pages−1，不检查request/列元数据容量。K读以row最大长度mask，再对qk各行作各自causal mask。BS非二次幂时Np可能跨出物理页内域，不能由nextPOT放宽原合同的BS约束。

每块 `qk=tl.dot(Q,K)*(sm_scale*1.4426950409)`，FP32 max或log2-sum-exp归约；lse的NaN显式变−inf。init_blocks使有效首块score=1e30，local_blocks使有效尾块score=1e29（后覆盖前）；影响选择，不改变QK。Q在块循环外加载，direct req_idx也循环外读取，减少重复load。

```text
candidate_scores[C,QH,B,topk] 全部−inf；candidate_indices 同shape全部−1
若当前行组max_blocks<=topk:
  仅chunk0枚举各row有效逻辑块号，score=0，不计算dot，随后return
否则按当前active_chunks划连续chunk
  空chunk return
  for logical block in chunk:
    dot/reduce得到各row score
    FILL_ONLY: 直接写step位置到GM candidate
    或runtime_fill_only && runtime_chunk_span<=topk: 同直接写
    否则:
      current_min=min(top_scores)           # 注意包含Tp padded lane
      min_position=最低有效rank且score==current_min
      仅new_score>current_min时替换该rank
  非direct-fill分支末尾写寄存器top_scores/top_indices到candidate
```

FILL_ONLY在Host以ceil(max_seqblock/C)<=topk静态决定；runtime adaptive可使较少chunk承载更多块，候选容量必须重新满足，不能将调参无条件视为纯性能。runtime短参数先把short_chunks夹至C，再要求两参数都正、short_chunks二次幂且≤C。score用row组最大长度选择短/长active_chunks，guarded merge按单row长度选择short/long候选范围；packed行组跨阈值时两者不一致，可能截断候选，原API已给具体容量反例。

还有非二次幂topk的静态边界：top_scores初值−inf且Tp>topk时padded lane始终−inf，current_min没有先mask它们。实际chunk含多于topk个有限候选并走寄存器替换路径时，填满topk有效lane后，current_min仍为−inf而有效rank已无该值，min_position变Tp，后来的更高分不会替换；因此不能一般保证真TopK。该结论排除short枚举、FILL_ONLY、运行时direct-fill等绕过替换循环的子域，且未执行编译或数值复现。

### Merge、local与顺序规则

_merge_bnsd_score_topk_candidates(_adaptive)每program处理一个(head,b)，候选扁平索引为chunk*topk+rank，分数/索引均按Host四维stride读，invalid index<0使score=−inf。每轮找最大分，tie取最低扁平candidate位置，再选对应index并将该位置分数置−inf。全候选耗尽而已有候选score为−inf时，重复轮次不保证全为新−1，不能把输出当唯一集合。自有merge输出int32[QH,B,topk]。

fused_append_local使用_merge_topk_append_local(_adaptive)：同样merge，再过滤index>=0、index<num_blocks、index*BS<=query_pos；末槽追加min(max(seq_len−1,0)//BS,num_blocks−1)，若已保留则−1。它是新[QH,B,topk+1]输出，无额外append launch。adaptive短/长各launch guarded merge，按各row块数分别return，两个launch写互斥row；它们共享candidate owner和output，顺序/可见性由同stream的Triton launch承担，没有自有跨Kernel event。

独立_append_local helper的实际过滤/非原地合同见[追加local块API](sgl_append_local_block.md)。旧模块另导出的_normalize_topk_idx_for_gqa会将QH输入view成[KVH,G,B,K]取组内首head，非聚合；_native_sanitize_topk_kernel把>=ceil(seq_len/BS)的条目改−1，并统计>=0项写select_num，其他负值不统一改−1。这两个helper有GQA调用方，不因新decode叶子没有import就认定dead；它们也不用于当前score-only merge的通用清洗。

### Raw全量attention路线，不能扩大公开支持

当旧/新raw实现disable_index_value=False时，还保留_decode_bnsd_score_attn_chunk_kernel + TopK merge + _merge_bnsd_attn_out_kernel；公共API文档不支持该功能，torch_native拒绝，故只在Reference保存实际可见body。num_kv_chunks必须正二次幂，默认根据缓存向量核数*8/(B*KVH)与max_num_kv_chunks选向下二次幂。每chunk扫描K/V并同时算块score和在线softmax：m初值−inf、l0、FP32 acc0；sink存在且chunk0时以FP32点积计算m=(Q·sink)*sm_scale*log2(e)、l=1，sink不提供V贡献。QK max/lse和init/local仅改变选择分数，attention用原QK；p降至V.dtype再tl.dot(p,V)，FP32累加/归一化，写T chunk输出和FP32 log2-lse。空chunk在sink处理前就return，merge依真实valid_chunks mask忽略未写chunk。

attention merge每row遍历C个chunk，以log2-lse做exp2权重合并FP32 chunk输出再转Q dtype。seq_len=0时valid_chunks0、归一化分母0，无有限输出保证；不能将未支持路线用于零长度安全承诺。full-attn的register TopK也有上述Tp padded-min边界，不自动因同时算attention而修复。fused_append_local只在score-only分支启用，不能推定raw全量输出也必增末槽。

### 逻辑资源、cache与生命周期

| 节点/缓冲 | GM容量 | 主要program逻辑值 | 同步/owner |
|---|---|---|---|
| score candidate | 分数4*C*QH*B*K + 索引同量，共8*C*QH*B*K B | Q Hp*Dp*e，K Dp*Np*e，qk Hp*Np*4，top_scores/top_indices各Hp*Tp*4及行向量 | 分片写不同chunk/head域；candidate初填来自Torch；后续merge同stream消费。 |
| merge/output | 4*QH*B*(K+append) B | padded Cp=nextPOT(C*K)分数/索引各Cp*4、argmax向量 | 每head/request唯一写者，adaptive两个guard互斥，不需atomic。 |
| raw attention | o_chunk=e*C*B*QH*D；lse=4*C*B*QH；candidate同上；新O=e*B*QH*D | 另有V Np*Dp*e、p Hp*Np*4、acc Hp*Dp*4和m/l | empty分配的无效chunk靠merge有效mask；全空不保证有限输出。 |
| 外部native临时 | Q reshape可能view/copy，w_dummy e*B*QH、aq_dummy4B、sl4*length及bt32副本 | callee内部资源未知 | 仅记录forward，不能推造external workspace或同步。 |

上述为逻辑payload/traffic，不是确定UB/L0/L1/寄存器峰值；Triton dot lowering、pipe同步和物理资源由编译器处理。源码无显式workspace Tensor、手写跨programbarrier/atomic。Q/K/V、metadata/candidate/output必须存活至同stream消费结束，不能从Host书写顺序推断跨stream可见性或允许别名竞争。

_get_vectorcore_num_safe使用独立模块无参数lru_cache(maxsize=1)，首次current_device属性或fallback32被缓存；device不在key，切设备不自动重查，32是异常fallback而非平台核数证明。native symbol lookup也独立缓存None/符号。此Reference完整保存已读自有算法与外部核心边界，不等于完整Operator闭包，未执行编译、真机、数值、graph或性能测试。

### 增量固定实现来源

- [python/sgl_kernel_npu/sgl_kernel_npu/indexer/flash_block_score_decode.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/indexer/flash_block_score_decode.py)。
- [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/flash_decode_bnsd_with_topk_idx.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/flash_decode_bnsd_with_topk_idx.py)。
- [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/append_local_block_to_topk_idx.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/append_local_block_to_topk_idx.py)。
- [python/sgl_kernel_npu/sgl_kernel_npu/attention/gqa_share_sparse_attention.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/attention/gqa_share_sparse_attention.py)。
- [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/flash_decode_bnsd_with_gqa_share_sparse.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/flash_decode_bnsd_with_gqa_share_sparse.py)。
- [csrc/pytorch_extensions.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/pytorch_extensions.cpp)。


## 证据与复核范围

本卡依据固定提交的第一方API说明蒸馏；架构编号按同提交构建说明映射为A2/A3（arch22）及950（arch35），具体子功能仍受正文限制。本次知识提取未执行编译、真机、数值或性能测试，未记录verified事件。

## 相关知识

- [消费已选块的GQA稀疏注意力](sgl_gqa_shared_sparse_decode.md)
- [独立追加local块](sgl_append_local_block.md)
