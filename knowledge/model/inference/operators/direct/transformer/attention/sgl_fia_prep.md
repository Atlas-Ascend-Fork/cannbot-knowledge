---
type: Operator
title: "FIA稀疏物理页表准备 A2/A3 Direct Invoke 算子知识"
description: "闭合fia_prep的逐query寻址、exclusive scan稳定重排、slot转页与双输出，记录own无条件追加、INT64窄化、容量和零长度边界。"
tags: [task.implementation, task.lookup, topic.attention, topic.kv_cache, topic.data_movement, topic.precision]
status: draft
sources:
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/attention/fia_prep.md
    role: primary
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/fia_prep.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/attention/fia_prep.py
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/__init__.py
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/__init__.py
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/build_tools/torch_wheel.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/setup.py
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernels.yml
    role: supporting
created_at: "2026-11-09T09:48:57Z"
updated_at: "2026-11-09T09:52:37Z"
platforms: [a2, a3]
cann_versions: ["9.1.0"]
---

# FIA稀疏物理页表准备 A2/A3 Direct Invoke 算子知识

## 算子速览

| 项目 | 内容 |
|---|---|
| 实际入口 | `sgl_kernel_npu.implementation.triton.attention.fia_prep.fia_prep`，Direct Invoke |
| 计算语义 | 稀疏逻辑块稳定重排、当前块置末、token槽转物理页，并生成有效因果长度 |
| 输入输出 | ti INT32[T,S]、逐query长度/请求号、请求槽表；输出INT32[T,S]和INT32[T] |
| 执行类型 | 单个Triton load/scan/reduce/scatter/store Kernel，无dot/Cube/AIC或MIX_CV节点 |
| Kernel路线 | R-001，constexpr S与block_size；own是否出现改变数据和kvl，不改变启动图/资源族 |
| 核心资源 | GM四输入两输出；无算子workspace或手工UB，S宽逻辑SSA向量由Triton分配 |
| 来源闭包 | direct_implementation_closed：完整launcher、逐参数producer、唯一Kernel body及Python打包链 |
| 验证状态 | 本次知识提取未执行编译、真机、数值或性能测试 |

## 接口与语义

### 计算语义

令s=seq_lens[t]、b=block_size>0，a=max(s-1,0)，own=a//b，off=a%b。ti[t]中所有非负且不等于own的项按原次序输出，不去重其它页；所有own项被移除，再在这些nonown项之后追加一个own物理页。负数都不属于有效页，合同使用-1填充。

物理页为`int32(req_to_token[req,min(max(logical,0)*b,C-1)])//b`，C为槽表列数；own也经一次独立无条件标量gather。这里不是直接把逻辑页号作为物理页，也没有校验超范围页的真实含义。公开有效域应保证页首列存在；min上界截断不证明请求或页合法。

n为非负nonown项数，present表示至少出现一个own。block_table先全S列写0，再写n个nonown页，再无条件写own到第n列。`actual_kvlen=n*b+(off+1 if present else 0)`。own没有被选中时仍追加到页表，但有效长度不包含它；必须保留一槽，n<S。重复own被合成一次，重复nonown仍重复计完整页。seq_len==0没有独立空域分支：若ti包含逻辑页0，公式仍可能返回1；不能借源码注释宣称零长度总得到零kvl。

### 输入、输出与属性

| 参数 | shape/layout | dtype | 约束、默认值与语义 |
|---|---|---|---|
| ti | [T,S]，公开合同连续 | INT32 | S为正二次幂；逻辑块、-1 padding，own未选时留槽 |
| seq_lens | 逐query[T] | INT32 | Device按pid读取，不通过request索引查长度；文档[B]表述不能替代展开 |
| per_query_req | [T] | INT32/INT64 | Device转INT64后参与请求行偏移，请求号须合法 |
| req_to_token | [requests,C] | INT32/INT64 | C>0，同NPU；每个载入slot先窄化INT32再整除b |
| block_size | Host正int，constexpr | 编译时整数 | b>0，乘法、除法与计数不溢出 |
| block_table_out | 可选[T,S] | INT32 | 默认empty；传入直接复用，实际两维stride传给Kernel；容量/不重叠由调用方保证 |
| actual_kvlen_out | 可选连续[T] | INT32 | 默认empty；Kernel按ptr+pid写，未传输出stride |

### 入口与版本

公开auto/triton延迟转发到该Direct函数；torch_native是独立参考，无自动回退。已有[接口卡](../../../../apis/sgl_kernel_npu/sgl_fia_prep.md)已区分逐query长度与文档[B]，本卡进一步展开内核。

固定源码为SGL提交`dda6d36b0cdb4081e102d14c0a2fb276fc416e69`。公开文档arch22/arch35均支持，README及architectures映射为A2/A3与950。CANN9.1.0来自固定CI配置任务基线，不是本次环境或完整Triton/torch_npu二进制版本证明。

## Host/Launcher 执行流程

### 参数校验与前处理

`total_q,topk1=ti.shape`先进行二元解包；没有显式dtype、device、连续性、S二次幂、b正值、长度、页表索引、输出shape/容量或别名校验。分别选择传入输出或用ti.device上的INT32 empty分配，然后读取输入/页表stride并launch。没有contiguous复制、长度展开、请求号校验或CPU参考回退。

seq_lens/per_query_req的dim()==0会使launcher传stride0，但这仅是原始实现行为，不属于公开[T]合同。actual_kvlen_out的stride从未传入，因此非连续输出不能借输入stride支持来推导正确性。

### 参数、Workspace 与生命周期

没有自定义POD、executor、workspace或跨Kernel scratch。默认输出有效payload共4TS+4T字节，框架allocator取整外部；传入输出按对象身份返回。四输入只读，两个输出不得重叠或覆盖仍在读取的输入。Torch/调用方持有张量到异步任务结束；函数不等待，不管理graph或跨stream event。

### 启动图与失败传播

```text
包初始化：vendor检查/torch_npu/native库加载
Direct fia_prep -> 解包ti.shape -> 准备两个输出 -> 读取stride/槽表C
 -> _fia_prep_kernel grid(T,),num_warps=1,num_stages=1
 -> 返回block_table与actual_kvlen
```

没有显式T==0早返回；零grid是否可启动由Triton runtime准入决定，不能改写成已保证的空域成功路线。原生库是包导入依赖，本Kernel没有调用其中的数学算子。分配、shape/stride访问、JIT或launch错误直接传播，没有自有cleanup和fallback。

## Route 与参数设计

### 分核与资源计算

每program处理一行t，grid=(T,)，不循环轮转核数。S直接作为tl.arange和scan/reduce宽度；b为constexpr。num_warps/num_stages都显式为1，但不据此推断AIV实际核数、thread布局、dynamic UB字节或硬件warp模型。

每行设u为非负ti项数、n为非负nonown项数，d_req/d_slot为实际INT32/INT64输入元素字节。有效逻辑读取为4S+4+d_req+(u+1)*d_slot；写入为4S（初始零填）+4n（scatter）+4（own）+4（kvl）。总逻辑流量`8S+12+d_req+(u+1)*d_slot+4n`字节/行，不含cache、DMA取整或编译器额外访问。own已选时仍从向量gather读取其slot，之后又有独立own标量gather；源码未合并这两次读取。

### Route 选择

| 顺序 | Route | Key/模板 | 精确选择条件与优先级 | 不适用去向 |
|---:|---|---|---|---|
| 1 | R-001 | _fia_prep_kernel<S,b> | Host能准备参数即尝试launch；安全合同另需S/b/容量/索引有效 | 原异常，无其它实现 |

```text
解包/分配/取stride成功 -> 唯一JIT Kernel
失败 -> 异常；没有自动Torch fallback、空域返回或小S重试
```

### 模板/实现执行矩阵

| Route | key/selector | dtype/shape/platform完整命中条件 | 执行拓扑与Kernel节点 | 实际模板/body | 内存与同步特征 | tail/fallback |
|---|---|---|---|---|---|---|
| R-001 | constexpr S,b | 公开有效域、T行，S正二次幂、b>0、n<S、所有访问有效；平台同整卡 | 单Kernel grid(T,),warp1/stage1 | _fia_prep_kernel，逐行scan/gather/scatter | 无GM scratch；S宽SSA；两输出同program写 | 无slot load尾mask；仅非负/非own scatter mask；无fallback |

### 隐藏性能 Guard

| Guard | Host/Tiling条件 | Device/资源原因 | 影响Route | 不满足时去向 | 源码符号 |
|---|---|---|---|---|---|
| S二次幂 | 文档要求，Host未检查 | arange(0,S)、S宽cumsum/sum | R-001 | 无自有padding，工具链准入/错误外部 | TOPK1/arange |
| 预留own槽 | Host未检查n<S | own无条件store到n | R-001 | n==S会访问本行外 | count_real/store |
| 每query长度 | Host仅传stride | seq_lens按pid读取，不按req映射 | R-001 | B<T且仅供[B]可能越界 | seq_lens_ptr+pid*stride_sl |
| C及索引 | Host只读shape[1] | own无mask读取，min只夹上界；请求行未mask | R-001 | C==0、非法req、算术溢出无安全保证 | token_col/own_col |
| INT64 slot范围 | 没有范围检查 | load后先转INT32再除b | R-001 | 大slot窄化改变物理页 | slots.to(int32)/own_slot |
| 输出layout | 不检查/修复 | actual_kvlen只写ptr+pid；table按给定两stride写 | R-001 | 非连续kvl或容量不足不能保证语义 | 输出实参/两类store |
| tile资源 | 无UB/cap裁剪 | S宽scan/reduce/多路向量 | R-001 | 无小tile重试；物理准入外部 | JIT launch |

### POD/ABI

无自定义POD及sizeof/offsetof合同。以下每行一个真实Kernel字段；runtime scalar和指针机器位宽由Triton推导，不伪造C++偏移。

| 结构 | 字段 | 类型/位宽 | ABI布局 | 单位 | Host/launcher producer | Device consumer | 边界 |
|---|---|---|---|---|---|---|---|
| JIT参数 | topk_idx_ptr | INT32指针；机器ABI外部 | 无算子POD偏移 | 元素/索引；constexpr为编译常量 | ti | log_blk load | [T,S] |
| JIT参数 | seq_lens_ptr | INT32指针；机器ABI外部 | 无算子POD偏移 | 元素/索引；constexpr为编译常量 | seq_lens | pid*stride_sl load | 逐query |
| JIT参数 | req_pool_ptr | INT32/64指针；机器ABI外部 | 无算子POD偏移 | 元素/索引；constexpr为编译常量 | per_query_req | load转INT64 | 合法请求行 |
| JIT参数 | req_to_token_ptr | INT32/64指针；机器ABI外部 | 无算子POD偏移 | 元素/索引；constexpr为编译常量 | req_to_token | vector/scalar slot load | slot先窄化INT32 |
| JIT参数 | block_table_ptr | INT32指针；机器ABI外部 | 无算子POD偏移 | 元素/索引；constexpr为编译常量 | block_table | zero/scatter/own写 | 至少每行n+1槽 |
| JIT参数 | actual_kvlen_ptr | INT32指针；机器ABI外部 | 无算子POD偏移 | 元素/索引；constexpr为编译常量 | actual_kvlen | ptr+pid store | 连续输出 |
| JIT参数 | max_req_to_token_cols | runtime int；机器ABI外部 | 无算子POD偏移 | 元素/索引；constexpr为编译常量 | req_to_token.shape[1] | col=min(...,C-1) | C>0 |
| JIT参数 | stride_ti_t | runtime int；机器ABI外部 | 无算子POD偏移 | 元素/索引；constexpr为编译常量 | ti.stride(0) | pid*stride_ti_t | 元素/行 |
| JIT参数 | stride_ti_k | runtime int；机器ABI外部 | 无算子POD偏移 | 元素/索引；constexpr为编译常量 | ti.stride(1) | off*stride_ti_k | 元素/列 |
| JIT参数 | stride_sl | runtime int；机器ABI外部 | 无算子POD偏移 | 元素/索引；constexpr为编译常量 | seq_lens.stride(0) if dim else 0 | pid*stride_sl | 标量raw行为不扩公开合同 |
| JIT参数 | stride_req | runtime int；机器ABI外部 | 无算子POD偏移 | 元素/索引；constexpr为编译常量 | per_query_req.stride(0) if dim else 0 | pid*stride_req | 同上 |
| JIT参数 | stride_rtt_r | runtime int；机器ABI外部 | 无算子POD偏移 | 元素/索引；constexpr为编译常量 | req_to_token.stride(0) | INT64 req*stride_rtt_r | 请求行 |
| JIT参数 | stride_rtt_t | runtime int；机器ABI外部 | 无算子POD偏移 | 元素/索引；constexpr为编译常量 | req_to_token.stride(1) | token_col/own_col*stride_rtt_t | 列 |
| JIT参数 | stride_bt_t | runtime int；机器ABI外部 | 无算子POD偏移 | 元素/索引；constexpr为编译常量 | block_table.stride(0) | pid*stride_bt_t | 行不重叠 |
| JIT参数 | stride_bt_k | runtime int；机器ABI外部 | 无算子POD偏移 | 元素/索引；constexpr为编译常量 | block_table.stride(1) | off/rank/count_real*stride_bt_k | 列不重叠 |
| JIT参数 | TOPK1 | tl.constexpr；机器ABI外部 | 无算子POD偏移 | 元素/索引；constexpr为编译常量 | ti.shape[1] | arange/cumsum/sum宽度 | S为正二次幂 |
| JIT参数 | BLOCK_SIZE | tl.constexpr；机器ABI外部 | 无算子POD偏移 | 元素/索引；constexpr为编译常量 | block_size | 逻辑页/slot除法及长度乘法 | 正整数b |

### Route 源码闭包

| Route | Key/selector | Host/Tiling producer | POD/参数 | Kernel entry/router节点 | Kernel body/直接依赖 | 构建接线 |
|---|---|---|---|---|---|---|
| R-001 | S,b，warp1/stage1 | impl::fia_prep:90–120 | 6tensor+9scalar/stride+2constexpr，逐项见表 | _fia_prep_kernel，pid=program_id(0) | impl:33–78全部自有body；tl.cumsum/sum等编译primitive | stage_runtime复制Python树、setup_refactor发现包；运行时JIT |

## Kernel 实现

### 公共执行流程

没有AIC/Cube节点或其它自有Kernel。每个program自己的GM行和S宽SSA数据相互隔离；源内无barrier、atomic、队列或显式UB复用。Triton lowering负责scan归约树、各store的实际指令排序及局部临时分配；不将其外推为手写AscendC的pipe/event配方。

### Route R-001：融合稳定压缩与物理页gather

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | impl | fia_prep | 直接grid(T,),TOPK1=ti.shape[1],BLOCK_SIZE=block_size | 唯一Kernel |
| Entry | impl | _fia_prep_kernel | t=program_id(0) | 逐行body，无其它router |

#### Device 数据流

##### 函数级调用链

```text
fia_prep -> _fia_prep_kernel
 -> load(seq_len,req,log_blk) -> own/nonown predicates
 -> INT32 cumsum-exclusive-rank + two reductions
 -> vector selected-slot gather + scalar own-slot gather
 -> zero table row -> scatter nonown -> own append -> kvl store
```

##### 源码等价伪码

```text
t=program_id(0); s=int32(load(seq+t*stride_sl)); req=int64(load(req+t*stride_req))
a=max(s-1,0); own=a//b; ownoff=a%b
x=int32(load(ti+t*stride_ti_t+arange(S)*stride_ti_k))
isown=(x==own)&(x>=0); nonown=(x>=0)&(x!=own); rn=int32(nonown)
rank=cumsum(rn)-rn; n=sum(rn); present=sum(int32(isown))>0
col=min(max(x,0)*b,C-1)
slots=int32(masked_load(rtt+req*stride_rtt_r+col*stride_rtt_t,x>=0,0))
phys=slots//b
owncol=min(own*b,C-1); ownphys=int32(load(rtt+req*stride_rtt_r+owncol*stride_rtt_t))//b
store(table+t*stride_bt_t+arange(S)*stride_bt_k,0)
masked_store(table+t*stride_bt_t+rank*stride_bt_k,phys,nonown)
store(table+t*stride_bt_t+n*stride_bt_k,ownphys)
kvl=where(present,n*b+ownoff+1,n*b)
store(actual_kvlen+t,int32(kvl))
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/对象 | offset/地址公式 | extent/容量 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| ti | t*stride_ti_t+i*stride_ti_k | S元素/行，无load尾mask | INT32 | 调用方 | 页谓词/scan/gather | 调用方至完成 | 公开连续，原始实现带stride |
| seq_lens | t*stride_sl | 1元素/行 | INT32 | 调用方先展开 | own/ownoff | 同上 | 不按req查长度 |
| per_query_req | t*stride_req | 1元素/行 | INT32/INT64→INT64 | 调用方 | 槽表请求行偏移 | 同上 | req行不mask |
| req_to_token | req*stride_rtt_r+col*stride_rtt_t | u个vector读取+1个own读取 | INT32/INT64→INT32 | 调用方 | phys整数除法 | 同上 | col上界min，不验证合法页 |
| block_table | t*stride_bt_t+column*stride_bt_k | 默认4TS有效容量，当前先S后n+1次写 | INT32 | 本program | 后续FIA消费者 | Torch/调用方 | supplied stride及容量必须自洽 |
| actual_kvlen | t | 默认4T有效容量 | INT32 | 本program | 后续FIA消费者 | 同上 | 硬编码连续输出寻址 |
| 逻辑SSA | S宽log_blk/rn/rank/slot/phys和谓词 | INT32向量与布尔mask；最终物理峰值未知 | Triton内部 | load/scan/reduce | gather/scatter/store | 单program | 非InitBuffer、无可手工相加的物理字节合同 |

##### 分层内存布局

N/A：无显式AIV UB、TQue/TBuf、SIMT dynamic UB或通信window。真实源码层级为GM四输入→S宽Triton SSA→GM双输出；不虚构block-beta缓冲区。

##### 字节账与复用顺序

workspace=0；默认输出payload=4T(S+1)。每行流量`8S+12+d_req+(u+1)*d_slot+4n`，输出零填和后续覆盖都计入，未把被覆盖的写省略。物理load合并、store排序、cache及SSA存储分配由编译器决定；Host没有对应UB大小guard。

| 复用子区 | 写入者 | 消费点 | 下一次覆盖 | 同步依据 | 安全条件 |
|---|---|---|---|---|---|
| table同一行 | 先zero，再nonown scatter，再own append | 后续消费者 | 下次调用可覆盖 | 源码同program次序；实际lowering外部 | n<S且每有效rank唯一、row strides不重叠 |
| actual_kvlen | 当前program | 后续消费者 | 下次调用 | 框架stream；跨流调用方负责 | ptr+t对应真实输出布局 |
| 两输出对象 | Torch或调用方准备 | 本Kernel→后续FIA | 重放/后续调用 | 调用方持有到完成 | 旧消费者完成后复用，无输入/输出别名 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| 页压缩rank | cumsum(rn)-rn | 0/1 INT32 nonown | scatter地址 | 一行稳定次序 | 同一向量exclusive scan；不跨program |
| own检测 | sum(int32(isown))>0 | 原ti值 | kvl where | own前缀是否计入 | 多个own只形成一次present |
| 槽映射 | tl.load→to(int32)→整数除法 | INT32/INT64 slot | phys/own_phys | 页编号 | 先窄化后除法；不是INT64全程 |
| 输出mask | nonown只用于scatter | 负页/own谓词 | n个scatter写 | 有效rank | 初始S列zero和own写没有此mask |
| 长度 | INT32 mul/add/where | n/b/ownoff | kvl store | 有效KV长度 | 不防溢出；seq0不单独清零 |
| 全图 | 无跨programbarrier/atomic | 调用方输入 | 逐行输出 | tensor寿命与stream | 返回tuple不等于同步完成 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host producer | impl | fia_prep:90–120 | shape/输出对象/全部stride、warp1/stage1 |
| Kernel entry/router | impl | _fia_prep_kernel<S,b>:9–32 | 一维program到query行 |
| Device body/helper | impl | 同函数:33–78 | 完整predicate/scan/gather/zero/scatter/append/kvl |

## 算子特定优化

### Trick T-001：0/1 exclusive scan直接构造稳定压缩位置

#### 触发与源码依据

- 适用Route：R-001。
- 触发条件：S宽合法向量，n<S，own与负页从nonown中排除。
- Golden 来源：[stable rank](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/fia_prep.py#L41-L47)。

**官方源码（固定Commit连续逐字摘录）**：

```python
    is_own = (log_blk == own) & (log_blk >= 0)
    real_nonown = (log_blk >= 0) & (log_blk != own)
    rn = real_nonown.to(tl.int32)
    # exclusive scan -> output rank for each non-own real slot (0..count_real-1)
    rank = tl.cumsum(rn, axis=0) - rn  # [TOPK1]
    count_real = tl.sum(rn, axis=0)  # scalar
    own_present = tl.sum(is_own.to(tl.int32), axis=0) > 0
```

#### 机制与设计原因

将nonown转为INT32 0/1，包含式cumsum减去当前rn，得到每个有效项之前的计数，直接作为输出rank。有效rank为0..n-1且保持原次序，无需GM临时索引、Host排序或单独压缩Kernel。sum(is_own)>0只决定有效长度是否加当前页前缀，不改变无条件own写的位置。

#### 迁移边界

- 适用：小S稀疏页列表的稳定过滤、追加特殊项。
- 前提：S满足工具链scan/arange准入、输出至少n+1槽、INT32计数不溢出。
- 失效：S不满足准入、n==S或非独占输出行时没有自有fallback；不能当作任意宽全局压缩算法。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

固定仓未提供可验证反例；源码无条件own写要求额外槽，不能把S个nonown项原样塞满输出后再追加一页。

### Trick T-002：物理页gather与双输出在同一program完成

#### 触发与源码依据

- 适用Route：R-001。
- 触发条件：请求行/逻辑页/slot范围合法，own物理页可读取，输出对象容量与布局正确。
- Golden 来源：[页表覆盖与有效长度](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/fia_prep.py#L69-L78)。

**官方源码（固定Commit连续逐字摘录）**：

```python
    bt_base = block_table_ptr + pid * stride_bt_t
    tl.store(bt_base + off * stride_bt_k, tl.zeros((TOPK1,), tl.int32))
    tl.store(bt_base + rank * stride_bt_k, phys, mask=real_nonown)
    tl.store(bt_base + count_real * stride_bt_k, own_phys)

    # actual_kvlen: real blocks full + own causal (offset+1)
    kvl = tl.where(
        own_present, count_real * BLOCK_SIZE + own_offset + 1, count_real * BLOCK_SIZE
    )
    tl.store(actual_kvlen_ptr + pid, kvl.to(tl.int32))
```

#### 机制与设计原因

一个program先填零，再按稳定rank写入物理nonown页，最后追加own并写实际长度；省去GM重排中间表与独立长度Kernel。有效长度和物理表必须配套消费：own未选时追加槽处于有效长度之外，不能仅凭页表中出现该页就扩大可见范围。

#### 迁移边界

- 适用：FIA需要已重排物理页与对应因果长度，调用方预分配双输出。
- 前提：INT32算术/slot窄化有效；连续kvl；stream和buffer寿命正确。
- 失效：负/越界req、C为0、超INT32 slot、kvl非连续或未预留own槽均不能靠padding zero兜底。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

固定仓未提供可验证反例；不要把未选own的追加页计入kvl，也不要将req_to_token的INT64类型当作大slot完整保持精度的保证。

## 模板与实现对比

| 维度 | 当前唯一实现 | 无需伪造的其它路线 | 设计依据 |
|---|---|---|---|
| 命中/优先级 | 参数准备后直接launch | 没有空域/失败回退 | launcher无selector |
| 模板/dtype | S,b constexpr；req/slot可INT32/64 | 没有FP32数学分支 | req升64，slot降32 |
| 分核 | 一个program/query | 不按AIC核数轮转 | grid(T,) |
| Queue/TBuf/dynamic UB | 无显式申请 | 不虚构AscendC缓冲 | Triton SSA lowering |
| 内存/复用 | 两输出、无GM scratch | 无单独prefix/reorder数组 | fused scan/gather |
| 搬运/API | load/cumsum/sum/两类scatter/store | 无CPU排序或通信 | 完整body |
| 同步/精度/tail | 一行独占，INT32计数 | 不保证seq0自动零、无非法索引修复 | own无条件读写 |
| fallback/失败 | 异常原样传播 | torch_native仅显式选择 | 公开wrapper |

## 平台差异

| 项目 | A2 | A3 | Ascend950 |
|---|---|---|---|
| 支持状态 | arch22公开支持，2201→910b | arch22公开支持，2201→910_93 | arch35公开支持，3510→950 |
| Host/Launcher | 共享Direct实现 | 同A2 | 同一实现、无source内平台分支 |
| Kernel/资源 | S宽scan/gather由对应Triton编译 | 不推断相同物理配置 | 不从warp1/stage1推断相同UB/吞吐 |

## 限制与失败边界

- draft/source closure不代表完整输入检查或运行正确。Host没有验证公开dtype/device/layout、S/b、请求索引、slot范围、输出容量与别名。
- seq_lens必须是逐query长度；原始scalar stride0行为不自动成为公开支持。actual_kvlen_out必须连续，因为Device写ptr+pid。
- n<S是无条件own追加的必要容量条件；即使own未选，仍会读取并写出own物理页。C>0和own页首可读取也是必要条件。
- INT64 slot在除法前降为INT32；logical*b、count*b、seq-1及地址中间算术仍需不溢出。上界min不能替代完整索引验证。
- 零seq在选中own0时实际公式可给kvl1；T==0仍尝试零grid，无本次执行结果或通用成功保证。
- 包初始化仍加载原生库；Python源已打包不能保证任意subset wheel可导入。未固定完整Triton二进制或物理资源布局。
- 本次知识提取未执行编译、真机、数值或性能测试；未设置verified。

## 源码索引

### 链路索引

| 链路阶段 | 文件 | 关键符号 | 支撑内容 |
|---|---|---|---|
| primary | [docs/api/zh/operators/attention/fia_prep.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/attention/fia_prep.md) | 芯片支持/参数表 | 公开平台和二次幂/own容量合同 |
| implementation | [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/fia_prep.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/fia_prep.py) | fia_prep/_fia_prep_kernel | 完整launcher和Device body |
| supporting | [python/sgl_kernel_npu/sgl_kernel_npu/operators/attention/fia_prep.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/attention/fia_prep.py) | _triton/fia_prep | auto/triton转发与显式reference |
| supporting | [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/__init__.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/__init__.py) | 模块初始化 | 没有额外算法调用 |
| supporting | [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/__init__.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/__init__.py) | 模块初始化 | 没有额外算法调用 |
| implementation | [python/sgl_kernel_npu/sgl_kernel_npu/__init__.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py) | _load_sgl_kernel_npu | 包导入原生库前提 |
| implementation | [python/sgl_kernel_npu/build_tools/torch_wheel.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/build_tools/torch_wheel.py) | stage_runtime/setup_refactor | 复制Python树及包发现 |
| supporting | [setup.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/setup.py) | main | wheel打包入口 |
| supporting | [python/sgl_kernel_npu/README.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md) | REFACTOR builds | 平台映射/Python源打包 |
| supporting | [csrc/cmake/architectures.json](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json) | 2201/3510 | 910b/910_93/950对应 |
| supporting | [.github/workflows/pr-test-kernels.yml](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernels.yml) | cann_version9.1.0 | CI配置证据，非运行结果 |

正文impl即上表完整Triton实现；torch_native仅独立参考，不进入该Direct启动图。

### 实现复用检查

| 检查项 | 可复用事实 | 不得改变的约束 | 源码符号 |
|---|---|---|---|
| ABI/POD | 6tensor、9runtime scalar/stride、2constexpr | 参数顺序、元素单位、kvl无stride | launch/Kernel签名 |
| 调用顺序 | 准备双输出→单Kernel→返回同对象 | 不加入隐式Host同步或fallback | fia_prep |
| workspace/内存 | 无GM scratch，table先zero再scatter | n<S，输出与输入不重叠 | 三次table store |
| 同步 | program独占行 | 跨stream生产/复用由调用方排序 | grid(T,) |
| 精度与尾块 | INT32页/长度，req升INT64 | slot先降INT32、own无mask读写 | to/int div/store |
| 失败边界 | 无输入修复或重试 | S/b/索引/容量由调用方保证 | Direct launcher |
