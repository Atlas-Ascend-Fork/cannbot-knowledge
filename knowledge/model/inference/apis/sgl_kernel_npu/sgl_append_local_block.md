---
type: API
title: SGLang追加local块接口的过滤、去重和整数边界
description: 说明append_local_block_to_topk_idx保持候选顺序、只对追加local去重，以及num_blocks容量与int32溢出限制。
tags:
- task.implementation
- topic.compute.indexing
- topic.kv_cache
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/indexer/append_local_block_to_topk_idx.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/indexer/flash_block_score_decode.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/append_local_block_to_topk_idx.py
  role: implementation
created_at: '2026-11-08T11:04:14Z'
updated_at: '2026-11-09T15:35:32Z'
platforms:
- a2
- a3
- '950'
---

# SGLang追加local块接口的过滤、去重和整数边界

## 接口原型

```python
from sgl_kernel_npu.operators.indexer import append_local_block_to_topk_idx

def append_local_block_to_topk_idx(
    topk_idx,
    seq_lens,
    block_size,
    num_blocks,
    *,
    impl="auto",
):
    ...
```

## 输入输出与算法

输入topk_idx为同NPU连续int32 `[N,B,topk]`，N/B/topk均正；seq_lens为连续int32/int64 `[B]`，含当前query可见长度。block_size与num_blocks均正，后者是逻辑块号上界，不是页表容量或每行真实块数，须至少ceil(max_seq_len/block_size)。

每行计算q_pos=max(seq_len-1,0)、local=min(q_pos//block_size,num_blocks-1)，保留满足0<=候选<num_blocks且候选*block_size<=q_pos的输入块，其余-1。前topk槽顺序不变，原有重复块也保留；仅追加末槽的local会检查是否已在保留候选中，已存在则末槽-1，否则写local。seq_len=0仍使q_pos/local=0，并非所有候选都自动清空。

返回新int32 `[N,B,topk+1]`、输入不改。auto与Triton同入口，无执行失败回退，torch_native独立参考。

## 约束与验证

入口主要断言维数/连续性/正标量/topk>0，seq_lens dtype、同设备、空batch合法性仍由调用方保证。Triton按int32读长度，candidate*block_size也为int32；支持范围要求长度0..INT32_MAX且候选乘积不溢出。参考用int64算术，其超范围行为不能当作Triton支持证明。

验证比较合法整数域中的逐位输出，覆盖已含local、未含local、未来块/越界块、输入重复块与零长度；同时检查输入不变。num_blocks过小会把local夹小，不能仅因输出块号合法就认为它代表真实query位置。

## 旧append入口的实际算法与Host差异

旧入口是 `sgl_kernel_npu.indexer.flash_block_score_decode.append_local_block_to_topk_idx`，新版实现位于 `implementation.triton.indexer.append_local_block_to_topk_idx`。两份 `_append_local_block_to_topk_idx_kernel` 的参数、heuristics与JIT装饰器、完整body相同；旧Host注释写in-place，实际两版都分配新out，旧topk_idx不被写入。新版Host仅额外断言topk>0并简化类型注解/说明，其余shape/连续检查与launch相同。旧Host没拒绝topk0不构成工具链可编译或合法输出保证。

### 地址、分核与数据流

BSQ=16，grid=(ceil(B/16),N)，num_warps4、num_stages1；每program负责一个head和最多16个query，Tp=next_power_of_2(topk)。q=pid_qblock*16+lane，head=pid_h。长度按seq_lens_ptr+q**线性读取**，不使用stride，转int32；候选与输出则使用Host传入的三维stride。实际地址为 `head*stride_h+q*stride_b+rank*stride_t`，无效query/超过topk lane均有mask。

```text
length=int32(seq_lens[q]); pos=max(length−1,0)
local=min(pos//block_size,num_blocks−1)
cand=load(topk_idx[head,q,0:Tp], mask=q<B and lane<topk, other=−1)
valid=(cand>=0)&(cand<num_blocks)&(cand*block_size<=pos)
out[head,q,0:topk]=where(valid,cand,−1)  # 不重排、不去除候选彼此重复
hit=sum(where(valid,cand,−1)==local)>0
out[head,q,topk]=hit ? −1 : local
```

num_blocks给逻辑号上界、不是某请求真实块数；length0仍得到pos/local0。local_present在写回候选后由局部cand_out计算，不需要跨program通信；不同head/query写互不重叠的新out。没有tl.dot、atomic、workspace或自有barrier，属于自有Vector逻辑；物理UB/寄存器与跨pipe同步由Triton编译器负责，本Reference不冒称完整VV Operator。

### 资源、精度与生命周期边界

GM输入候选4*N*B*topk字节，输出4*N*B*(topk+1)字节；seq_lens按实际dtype占e_len*B字节。每program逻辑候选/过滤tile为16*Tp项int32，单个tile4*16*Tp字节，另有16项pos/local/hit和bool mask；这些是逻辑活跃值与流量，不能把若干SSA tile相加当作确定物理UB峰值。每合法query候选读写各topk项、额外写1个local，输入未改。

长度转int32与cand*block_size的int32运算没有溢出保护；跨设备、length dtype、slot容量和值域仍需调用方符合原合同。新out由Torch分配，输入/输出要活到当前stream消费完成；源码无额外跨stream/alias保护，也没有设备属性cache。当前API已保存该算法Reference及旧映射，不等同已经完成独立Operator模板/闭包；本次未运行编译、真机、数值或性能测试。

### 增量固定实现来源

- [python/sgl_kernel_npu/sgl_kernel_npu/indexer/flash_block_score_decode.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/indexer/flash_block_score_decode.py)。
- [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/append_local_block_to_topk_idx.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/append_local_block_to_topk_idx.py)。


## 证据与复核范围

本卡依据固定提交的第一方API说明蒸馏；架构编号按同提交构建说明映射为A2/A3（arch22）及950（arch35），具体子功能仍受正文限制。本次知识提取未执行编译、真机、数值或性能测试，未记录verified事件。
