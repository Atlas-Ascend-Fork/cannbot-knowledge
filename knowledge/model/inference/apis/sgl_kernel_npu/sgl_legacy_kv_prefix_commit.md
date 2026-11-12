---
type: API
title: 旧KV缓存按请求有效前缀提交接口
description: 保存旧KV前缀提交的Host检查、行stride与Triton双plane搬运，明确有效长度、槽位冲突、异步生命周期和未知平台边界。
tags: [task.implementation, topic.data_movement]
status: draft
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/mem_cache/kv_cache_store.py
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py
  role: header
created_at: "2026-11-09T16:04:17Z"
updated_at: "2026-11-09T16:04:17Z"
platforms: []
---

# 旧KV缓存按请求有效前缀提交接口

## 入口与状态语义

```python
from sgl_kernel_npu.mem_cache.kv_cache_store import (
    store_kv_cache_prefix_valid_npu_triton,
)
store_kv_cache_prefix_valid_npu_triton(
    dst_k, dst_v, src_k, src_v, loc_2d, commit_lens,
)  # 返回None，原地写dst_k/dst_v
```

固定sgl-kernel-npu提交 `dda6d36b0cdb4081e102d14c0a2fb276fc416e69` 的旧mem_cache模块。loc为[B,W]，源K/V第0维均M=B*W，row r对应请求b=r//W与请求内j=r%W。只在j<commit_lens[b]时，把源第r行K/V复制到物理slot loc[b,j]。它是显式prefix commit，不做nonzero/index_select、槽位分配、请求排序、attention或SSM state rollback。

平台证据不足，保持draft API Reference与platforms=[]，不猜CANN版本，不称完整Operator/source_closed。名称中的npu、docstring的DSpark/graph-safe意图不构成指定产品、graph捕获或真实运行证明。本次未执行编译、测试、真机、graph或性能验证。

## Host输入检查与布局

| 对象/检查 | 实际行为 |
|---|---|
| loc_2d | 必须rank2[B,W]；非连续时.contiguous()，没有dtype/值域检查 |
| commit_lens | rank1且长度=B；非连续时.contiguous()；没有整数dtype、0..W数值检查 |
| dst_k/dst_v | 各rank3[slots,heads,dim]，两个slot数可以不同 |
| src_k/src_v | 各rank3[M,heads,dim]，两者第0维必须等loc.numel() |
| 行shape | dst_k.shape[1:]==src_k.shape[1:]，V同理；不要求K与V行宽相同 |
| dtype | 四K/V必须完全相同dtype；没有具体dtype白名单 |
| device | 四K/V、loc、commit_lens六者必须完全同device；不额外assert NPU |
| 内层stride | 四K/V必须stride(-1)=1且stride(-2)=shape[-1]，保证heads×dim行内连续 |
| 行stride | 通过stride(0)显式传入，可有行间padding；未检查行间storage不重叠或src/dst无alias |
| 空loc | 上述检查后若M=0立即return，不复制metadata/不启动Kernel |

设DK=src_k.heads*dim，DV同理。K/V保持原storage，不做contiguous copy；与只接受完全packed tensor的旧activation不同，这里Device确实消费四个row_stride。metadata的contiguous可能新分配/拷贝，也可能复用原storage；不在Host读回内容。非空M时W>0，Device的请求内除余由shape保障不除0。若M>0而DK=DV=0，仍形成第二grid维为0的launch表达式，无专门短路，不据此宣称框架会接受。

## 精确选择与地址

唯一自有Device为@triton.jit `_store_kv_cache_prefix_valid_npu_kernel`，固定BLOCK=128，T=ceil(max(DK,DV)/128)，grid=(M,T,2)，无autotune/设备核数cache。每个program绑定一个源row、一个列block和K/V plane：

```text
r=program_id(0); t=program_id(1); kv=program_id(2)
b=r//W; j=r%W
active = j < load(commit_lens+b)
slot = load(loc+r,mask=active,other=0).int64
c=t*128+arange(128)
if kv==0:
    m=active & (c<DK)
    value=load(src_k+r*src_k_stride+c,mask=m,other=0)
    store(dst_k+slot*dst_k_stride+c,value,mask=m)
else:
    m=active & (c<DV)
    value=load(src_v+r*src_v_stride+c,mask=m,other=0)
    store(dst_v+slot*dst_v_stride+c,value,mask=m)
```

每plane都使用同slot和active条件，K/V行宽/rowstride独立。较窄plane的额外block全部列mask，最后block按各自行宽处理尾；不需要DK/DV为128倍数。loc在active=False时不读，填0仅用于无效地址表达式，K/V所有load/store也被抑制，不能将未提交行的garbage loc说成必发生访问。每program仍先读commit_lens，K/V与不同列block重复读取metadata，不在Host生成活动列表。

### JIT ABI

| 参数族 | 实际消费 |
|---|---|
| 六runtime ptr | dst_k/dst_v/src_k/src_v/loc/commit_lens |
| 四runtime stride | dst_k_row_stride,dst_v_row_stride,src_k_row_stride,src_v_row_stride，单位为元素 |
| 四constexpr | K_ROW_DIM=DK,V_ROW_DIM=DV,PREFIX_WIDTH=W,BLOCK=128 |

共14形参，无自定义序列化POD、workspace参数、Cube、tl.dot或第二Kernel。slot显式转int64后乘dst_stride；源row*src_stride没有源码显式int64 cast，其他索引的实际位宽/大shape范围不能由Python整数推断无限可用。

## 值域、冲突与状态边界

合法调用方合同应为整数commit_len且0<=commit_len<=W，所有active slot分别在两dst的第0维范围内。Host没有验证：负长度使相应请求无active row，超过W只会让该请求已有W行全active，不会凭长度凭空创建额外源row；这不免除非法合同。metadata dtype也未限制，loc即使能被Triton接受仍被转int64，不是类型安全的槽位检查。

active负slot/超capacity没有mask或clamp，会构成分配外目标地址；只对inactive loc的垃圾值有屏蔽。两dst slot数未要求相等，合法slot必须同时落在各自容量内。多个active源row若指向同一slot，同plane不同program可以并发写同列；没有定义最后一个请求获胜，K/V两plane也不构成原子成对提交。跨列chunk可能观察到混合来源，需调用方提供不冲突的slot集合或外部同步安排。

源与目标若alias，Kernel没有先克隆全部源或建立依赖图，某slot写可能覆盖另一个尚未读取的源row；不能当通用memmove/任意置换安全算法。即使同slot的自拷贝在某域数值不变，也不推广到任意交叉alias。dst的行stride若使不同行overlap，亦会引入写冲突；Host只验证行内连续，不验证这一点。

Payload无数学转换/量化，四KV dtype相同；load/store传递同元素类型。metadata比较、除余与slot转换仍为实际Triton操作，不能借“copy”掩盖位置整数域或异常dtype问题。

## 逻辑字节、同步与生命周期

令A为active源row总数，e为KV元素字节，dl/dc为loc/commit元素字节。非空M、T>0域：

| 对象 | 逻辑字节/访问 |
|---|---|
| src K/V | 容量按各rowstride与storage；有效payload读A*(DK+DV)*e B |
| dst K/V | 有效payload写同量；未提交slot保持；没有新KV输出分配 |
| metadata | contiguous loc M*dl、commit B*dc B；若需copy，框架额外读写同量 |
| commit读 | 每M*T*2个program一项，共2*M*T*dc B逻辑读取 |
| loc读 | 只active row，每plane/column block读取，共2*A*T*dl B |
| program局部值 | 128个KV元素=128e B，另有128lane列索引/mask与slot/length标量 |
| 请求方workspace | 无；metadata copy为Torch临时，不是显式kernel workspace |

有效KV逻辑流量2*A*(DK+DV)*e B，再加metadata重复读与可选contiguous拷贝。没有手工UB/L1/L0/queue/event、atomic、barrier或hostwait；compiler安排单program的load→store。纯搬运而无Cube节点，但平台未知不能自动升级VV Operator。

K与V的两个plane及各列block没有成对发布屏障，后续attention消费者需在同一流顺序或显式事件依赖之后读取。调用方保持四KV与metadata（包括contiguous临时）到异步执行完成，不并发修改commit/loc或重用slot；Torch/Triton管理copy/launch的普通流生命周期，源码没有自有跨stream事务协议。Kernel不缓存metadata，也不查询/缓存设备核数。

## 核验方向与固定源码

可用不同请求commit长度（0、W、部分）、不同DK/DV、128列尾、行间padding和非连续metadata，逐项检查只写active loc目标、非active槽保持；冲突slot/越界slot/交叉alias应先按合同排除或作为静态边界分析。不能把slot prefix提交等同SSM speculative state搬运。上述均为未执行核验方向。

- [python/sgl_kernel_npu/sgl_kernel_npu/mem_cache/kv_cache_store.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/mem_cache/kv_cache_store.py)（primary）。
- [python/sgl_kernel_npu/sgl_kernel_npu/__init__.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py)（header）。
