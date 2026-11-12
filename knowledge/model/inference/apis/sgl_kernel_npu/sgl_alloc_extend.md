---
type: API
title: SGL分页KV新增槽位的分配索引接口
description: 说明 alloc_extend 的旧页补满、新页顺序消费和values[0]条件写入，区分索引计算与KV搬运。
tags:
- task.implementation
- topic.kv_cache
- topic.memory
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/mem_cache/alloc_extend.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/torch_native/mem_cache/alloc_extend.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/mem_cache/allocator.py
  role: implementation
created_at: '2026-11-08T11:03:33Z'
updated_at: '2026-11-09T16:06:19Z'
platforms:
- a2
- a3
- '950'
aliases:
- alloc_extend
---

# SGL分页KV新增槽位的分配索引接口

## 调用入口

```python
from sgl_kernel_npu.operators.mem_cache import alloc_extend

def alloc_extend(
    pre_lens, seq_lens, last_loc, free_pages, page_size, out_indices, values,
    *, impl="auto",
): ...
```

## 分配语义

根据各请求已有长度、目标长度和最后槽位，先使用旧页剩余位置，再顺序使用free_pages，按请求顺序把新增token槽位紧密写进out_indices。这里只产生编号，不移动KV，也不替调用方弹出空闲页。

pre_lens、seq_lens、last_loc都是同NPU int64 `[B]`，B>0；seq_lens>=pre_lens，空前缀last_loc=-1。free_pages是足量的有序int64空闲页ID，page_size是int32可表示的正数。输出由调用方分配，out_indices长度必须恰好等于全部新增token数sum(seq_lens-pre_lens)；复用更大的缓冲区时须传入该长度的切片，values是至少一个int64元素的缓冲区，均为稠密一维存储。

## 条件副作用

返回None并原地更新out_indices。仅当最后一个请求结束在新分配且未满的页时，values[0]才被写为整批新增页数；其他情况下保留旧值。消费values的代码必须结合条件或初值，不能把旧值当本批计数。

auto选择ascendc；显式torch_native按相同缓冲区协议写入。验证应覆盖旧页有余量、恰好填满、新页尾部不足及多请求打包顺序。例如page_size=4，原长度3、目标6、last_loc=22、free_pages=[8]时新增编号是[23,32,33]，并写values[0]=1。比较两个后端前复制所有可变输出，分别检查未触发计数写入时的哨兵保留。

## 实现风险与源码分析

上述为公开分配合同。固定快照的新CANN实现存在UB分配字节与LocalTensor元素偏移不一致的静态风险，不能由该合同推出原生结果正确或可安全复用；详见[A2/A3源码草稿](/model/inference/operators/aclnn/nn/index/sgl_alloc_extend.md)与[950源码草稿](/model/inference/operators/aclnn/nn/index/sgl_alloc_extend_950.md)。未在设备复现该风险；`auto`不会因为原生执行失败自动改用参考后端。

## 旧raw Triton页索引Kernel补充

此节仅记录同一kernel commit的 `sgl_kernel_npu.mem_cache.allocator.alloc_extend_kernel`，不是上面的公共operators.mem_cache.alloc_extend，也不是其auto分派后端。旧文件只有@triton.jit定义，虽然导入get_device_properties但未调用，未提供Host launcher、缓冲区分配/检查、grid选择或values参数。保留自有body全部可读机制，不把公共API的A2/A3/950、版本、dtype检查或完整Operator闭包转移到这个旧raw入口；这也不改变本卡原有公共API平台与status。

### ABI、输入与未定义归约边界

| 参数 | 实际消费 |
|---|---|
| pre_lens_ptr/seq_lens_ptr/last_loc_ptr | runtime GM元数据，按pid与prefix向量读取 |
| free_page_ptr | runtime GM空闲物理页ID，有序消费但不修改 |
| out_indices | runtime GM输出编号，原地写；无返回新Tensor/values |
| bs_upper | constexpr，arange(0,bs_upper)前缀向量长 |
| page_size | constexpr P，arange(P)、页ceil/floor/除余 |
| max_num_extend_tokens | constexpr，决定整页循环次数 |
| BLOCK_SIZE | constexpr T，默认2048，整页token tile |

没有参数dtype转换/白名单，实际整数位宽、除法与溢出由传入指针类型及Triton表达式决定；不能补造新版int64缓冲区检查。源码有9形参，不收batch_size；pid范围必须由外部grid与真实元数据长度约束。page_size>0、有效arange shape、足量可写输出、物理页与last_loc一致性、各请求seq>=pre及无整数溢出均需要调用方保证。

实际prefix读取为：

```text
i=arange(bs_upper)
seq=load(seq_lens+i,mask=i<=pid)  # 没有other
pre=load(pre_lens+i,mask=i<=pid)  # 没有other
output_start=sum(seq-pre) - (seq_pid-pre_pid)
new_page_start=sum(ceil(seq/P)-ceil(pre/P))
               - (ceil(seq_pid/P)-ceil(pre_pid/P))
```

两load没有给masked lane的other值，而后续对**整个向量**进行减法、ceil及tl.sum，没有重新对i<=pid置0。只要存在masked lane，就不能从这些源码证明prefix归约仅由有效请求唯一确定；不能默默用0补齐并称算法对所有pid正确，也未在设备证明某个特定错误值。没有masked lane的条件子域或另有明确外部primitive证据时，才可按下面的数学前缀公式推导。另有标量seq_len/pre_len/last_loc按pid直接无mask读取，外部grid不能超真实请求数；bs_upper小于需覆盖前缀也没有安全补偿。

### 条件化三段编号算法

以下以归约得到预期prefix值、0<=pre<=seq、P>0且整型计算可表示为条件。对请求i，设p=pre[i]，s=seq[i]，e=s-p，c=ceil(p/P)，a=ceil(s/P)-c，O=sum_{j<i}(seq[j]-pre[j])，F=sum_{j<i}(ceil(seq[j]/P)-ceil(pre[j]/P))：

| 阶段 | 数量/地址 | 提前终点 |
|---|---|---|
| 旧页剩余 | n1=min(s,cP)-p；对t in [0,P) masked t<n1，out[O+t]=last_loc+1+t | 若p+n1==s立即return |
| 新整页 | n2=floor(s/P)*P-cP；t分T=BLOCK_SIZE片，out[O+n1+t]=free_pages[F+floor(t/P)]*P+t%P，mask t<n2 | 若p+n1+n2==s立即return |
| 新尾页 | n3=s-floor(s/P)*P；读free_pages[F+a-1]，out[O+n1+n2+t]=pageID*P+t，mask t<n3 | 无额外计数副作用 |

n1阶段不读free_pages；没有新页的请求可在第一阶段return。整页循环固定为ceil(max_num_extend_tokens/T)次，不由每请求n2动态增长。完整覆盖的精确条件是这个次数*T>=n2；缺少外部Host时不能假定max_num_extend_tokens一定足够。低估时其余控制流仍可继续，不能把只写部分整页说成完整结果。整页free_page load按token lane重复同页ID，load/store都用t<n2 mask；masked load无other但该lane的最终store也被同mask抑制，与前述“未mask归约消费”缺口不同。

旧尾页slot从last_loc线性+1，调用方需保证last_loc与已有长度及实际物理页尾一致；空前缀、旧页已满时n1=0，不从last_loc分配。新页ID的顺序由F/a取自free_pages，不实际弹出/回收列表。尾页阶段不写values，也不报告整批消耗页数；公共API的条件values[0]合同不能套到这里。合法且无冲突前提下，各请求输出区间[O,O+e)不重叠，不移动KV数据。

### 资源、精度、同步与生命周期

令B为外部实际请求数，U=bs_upper，T=BLOCK_SIZE，P=page_size，元数据元素字节按各指针dtype计。每program的prefix seq/pre向量各U项，extend/page-count等逻辑向量也各U项；每请求读取i+1项prefix、另读seq/pre/last各1项，prefix重复读取总量随B平方增长，而非一个全局prefix-scan Kernel。前缀masked未定义lane仍不能用于有效数值推导。

Part1/3各有P lane offset与编号，Part2有T lane offset/pageID/编号；大小为lane数乘实际整数元素字节，compiler可融合复用，不能直接相加为物理UB峰值。out写e个slot编号（覆盖条件满足时），整页free_page逻辑读n2项并可能反复读同一个页ID，尾页另读1项。没有显式UB/L1/L0、workspace、queue/event、atomic、barrier、hostwait或设备属性cache；primitive编译资源为外部边界。

各program依赖只读prefix元数据计算偏移，无自有跨program通信。它只在正确prefix/不重叠out、free_pages无非法复用及storage不alias的前提下无需同步；没有原子页表分配、重复页检测、snapshot或跨stream发布协议。调用方应保持元数据、free_pages和out直到异步执行/consumer结束，不能把这个raw body当完整分配器生命周期。

[分页分配器集成Guide](/model/inference/guides/integration/sglang_ascend_runtime/sglang_ascend_cache_page_allocator.md)另记录固定SGLang调用方的少于200新页分支、临时输出和空闲页消费；该来源不是本文件自有Host，更不消除这里masked归约的静态边界。本次未执行旧Kernel，以上是可用源码事实和条件化推导，不是运行正确性保证。


## 固定来源与验证状态

- [mem_cache/alloc_extend.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/mem_cache/alloc_extend.md)
- [构建架构与产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md)及[SDK架构表](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json)。文档arch22对应本版本2201构建族A2/A3，arch35对应3510的950；具体子接口限制以上文为准。

- [旧raw allocator.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/mem_cache/allocator.py)是独立Triton body的implementation来源，仅用于上面的旧入口补充，不替代公共ACLNN实现。

本卡为固定提交的公开API契约蒸馏，未展开Host/Tiling/Device全链路。本次知识提取未执行编译、真机、数值或性能测试；上游报告的支持和用例结果不代表本次复测。
