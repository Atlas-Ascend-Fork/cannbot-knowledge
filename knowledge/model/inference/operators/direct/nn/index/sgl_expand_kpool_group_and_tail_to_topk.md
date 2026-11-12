---
type: Operator
title: "Kpool选块展开与尾token追加 A2/A3 Direct Invoke 算子知识"
description: "闭合pool-major索引展开与tail追加的四种行tile，区分128KiB启发式与实际UB、物理对齐view、有效行裁剪及扩展shape准入。"
tags: [task.implementation, task.lookup, topic.data_movement, topic.memory, topic.kv_cache, topic.programming_model]
status: draft
sources:
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/indexer/expand_kpool_group_and_tail_to_topk.md
    role: primary
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/expand_kpool_group_and_tail_to_topk.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/indexer/expand_kpool_group_and_tail_to_topk.py
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/__init__.py
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
created_at: "2026-11-09T09:59:16Z"
updated_at: "2026-11-09T09:59:16Z"
platforms: [a2, a3]
cann_versions: ["9.1.0"]
---

# Kpool选块展开与尾token追加 A2/A3 Direct Invoke 算子知识

## 算子速览

| 项目 | 内容 |
|---|---|
| 实际入口 | `sgl_kernel_npu.implementation.triton.indexer.expand_kpool_group_and_tail_to_topk._expand_kpool_group_and_tail_to_topk`，Direct Invoke |
| 计算语义 | 将每个选中pool展开成连续token索引，保持pool顺序，再追加未压缩tail，填充行/剩余tail为-1 |
| 输入输出 | INT32 pool_indices[rows,N]与连续INT32 seq_lens[rows]；返回INT32[Qpad,K+P-1]的切片view |
| 执行类型 | 一个自有Triton整数搬运/变形Kernel，无dot/Cube/AIC或MIX_CV；前置Torch分配并常量填充为框架边界 |
| Kernel路线 | R-001不launch；R-002至R-005分别BLOCK_B=8/4/2/1 |
| 核心资源 | GM物理输出按8个INT32对齐行宽；无自有scratch；BB×N×P逻辑tile，物理存储由编译器分配 |
| 来源闭包 | direct_implementation_closed：launcher、裁剪/校验、资源启发式、两阶段body和属性helper/打包闭合 |
| 验证状态 | 本次知识提取未执行编译、真机、数值或性能测试；代码中的UB预算不是实际资源测量 |

## 接口与语义

### 计算语义

N=pool_indices.shape[1]，P=pool_size>=4，K=index_topk=N*P，D=P-1，W=K+D，A=ceil(W/8)*8。请求有效行数n_req被裁剪为`R=min(n_req,pool_indices.shape[0],seq_lens.shape[0])`，Qpad=num_q_padded须不小于R。

对0<=r<R、第i个有效pool索引p[r,i]、0<=j<P，`out[r,i*P+j]=p[r,i]*P+j`。尾部令L=seq_lens[r]、start=(L//P)*P、count=L-start；在非负且INT32不溢出的长度域，0<=count<P。`out[r,K+j]=start+j`当j<count，否则-1，0<=j<D。r>=R的padding行保持-1。输入不写，没有按序列因果长度过滤选中pool，也不排序、去重或修复非法pool值。

原始body未把负pool归一为-1；若调用方违反值域传-1，会计算成[-P,...,-1]，不是统一-1。这一静态公式不能被“padding为-1”文档摘要覆盖，公开正常输入仍须为有效pool位置。

### 输入、输出与属性

| 参数 | shape/layout | dtype | 约束、默认值与语义 |
|---|---|---|---|
| pool_indices | [input_rows,N] | INT32 | 两维stride都传入Kernel；值须有效、同NPU |
| seq_lens_per_token | [input_rows]，连续 | INT32 | 每query长度；Kernel直接ptr+r，须非负并不溢出 |
| n_real | Host int | 非Device原始值 | 请求有效行数；实际先min裁剪到两输入行数 |
| num_q_padded | Host int | 非Device参数 | 输出物理行数Qpad>=R；合法分配还要求非负 |
| pool_size | Host int、constexpr | 编译时整数P | 显式assert P>=4；arange/reshape具体准入见限制 |
| index_topk | Host int、constexpr | K=N*P | 显式检查相等 |
| 返回out | [Qpad,W] view | INT32 | base存储[Qpad,A]，stride(0)=A、stride(1)=1；W<A且多行时一般不连续 |

### 入口与版本

公开`operators.indexer.expand_kpool_group_and_tail_to_topk`的auto/triton延迟导入此Direct函数；torch_native独立参考，无失败自动回退。本卡不伪造ACLNN或自定义POD。

固定SGL提交`dda6d36b0cdb4081e102d14c0a2fb276fc416e69`。公开文档arch22支持、arch35已验证，README/architectures映射为A2/A3、950；上游验证声明不等于本次verified。CANN9.1.0取固定CI基线，未固定完整Triton/torch_npu二进制。

## Host/Launcher 执行流程

### 参数校验与前处理

先读取pool_indices.shape[1]，assert P>=4，计算D/W/A，再将n_real裁剪为R；这在ndim校验之前，低rank张量可能先因shape访问失败。随后检查pool二维且行数覆盖R，seq一维且行数覆盖R，Qpad>=R、两输入INT32、seq连续、N*P==K。没有显式检查同device、N>0、请求R非负、长度/索引值合法或算术范围。

用`torch.full((Qpad,A),-1,dtype=int32,device=pool_indices.device)`分配并初始化全物理输出，assert输出列stride1。R>0时计算BLOCK_B和核数并launch；否则只返回[:, :W] view，没有自有Kernel。n_req超过输入行数会裁剪，不抛“数据不足”错误；负R未被拒绝，也走不launch分支，但不是推荐有效域。

### 参数、Workspace 与生命周期

物理GM输出payload为4Qpad*A字节，逻辑view可见4Qpad*W字节；切片不复制、不能仅用逻辑宽W推导行pitch。没有自有workspace、临时GM矩阵或executor。Torch full的分配/常量初始化和最终view是框架操作，实际fill kernel/allocator/stream集成内部不在固定仓中。

要求full初始化完成后Triton才能覆盖有效行；源码不显式传stream或event，依赖安装框架的同设备/当前流排序。调用方必须保证两输入就绪、相同NPU及异步对象寿命，跨流依赖不能靠Host调用书写顺序代替。返回view持有base storage，所有权随Torch对象；下游不能假设连续W宽行。

### 启动图与失败传播

```text
Direct -> 读取shape/P检查 -> R裁剪 -> shape/dtype/布局检查
 -> Torch full分配+全物理输出填-1（框架边界）
 -> R<=0：切片view返回
 -> R>0：_choose_block_b -> get_device_properties
    -> C=min(ceil(R/BB),vectorcore_count)
    -> _expand_kpool_group_and_tail_to_topk_kernel grid(C,)
    -> out[:, :W]返回view
```

分配、assert、属性查询、JIT/launch失败直接传播，无Torch参考fallback和小tile重试。get_device_properties无参cache记住首次current_device属性，同时要求num_aicore和num_vectorcore>0；只用后者分核，不能假设后续切换设备会刷新属性。

## Route 与参数设计

### 分核与资源计算

源码常量UB_SPECIFICATION=192KiB，UB_TILE_BUDGET=128KiB；不是从当前硬件UB接口查询。启发式每行估算`tile_bytes_per_row=4*N*P*4=16K`，max_rows=max(1,floor(131072/(16K)))，BB=min(8,2^floor(log2(max_rows)))，C=min(ceil(R/BB),Vcores)。K>0时BB区间见下表；K=0且R>0时选择器除零，Host没有N>0 guard。

program p∈[0,C)处理`r0=p*BB+j*C*BB<R`，每轮BB行。前半同时展开BB×N个pool为BB×K索引；后半static_range(BB)逐行追加D列tail。row_mask保护最后不足BB行。Host没有显式num_warps/num_stages，不能借别的Kernel配置补数值。

### Route 选择

| 顺序 | Route | Key/模板 | 精确选择条件与优先级 | 不适用去向 |
|---:|---|---|---|---|
| 1 | R-001 | R<=0 | 分配/校验完成后有效R不大于0 | 不查属性、不launch |
| 2 | R-002 | BB8 | R>0,0<K<=1024 | 继续资源公式 |
| 3 | R-003 | BB4 | R>0,1024<K<=2048 | 同上 |
| 4 | R-004 | BB2 | R>0,2048<K<=4096 | 同上 |
| 5 | R-005 | BB1 | R>0,K>4096 | 固定最小1，没有保证估算仍<=128KiB |

```text
全部校验/输出full初始化 -> R<=0 ? R-001
否则计算16K每行估算 -> BB=8/4/2/1 -> C=正vector核数裁剪
 -> 单个自有Triton Kernel；K=0发生Host除零，无fallback
```

### 模板/实现执行矩阵

| Route | key/selector | dtype/shape/platform完整命中条件 | 执行拓扑与Kernel节点 | 实际模板/body | 内存与同步特征 | tail/fallback |
|---|---|---|---|---|---|---|
| R-001 | R<=0 | 输出分配/输入元数据检查成功，正常空域R=0 | 只有框架full/view，无自有Device节点 | Direct return view | 全base填-1，4Qpad*A字节 | 不声称负R是推荐域 |
| R-002 | BB8 | R>0,0<K<=1024，完整输入与工具链合同 | 框架full→单自有Kernel grid(C,) | kernel<N,P,K,D,C,8> | 8×K展开向量+逐行tail，行轮转 | row_mask；无dtype/平台fallback |
| R-003 | BB4 | R>0,1024<K<=2048，其余同上 | 同上 | kernel<N,P,K,D,C,4> | 4×K展开 | 同上 |
| R-004 | BB2 | R>0,2048<K<=4096，其余同上 | 同上 | kernel<N,P,K,D,C,2> | 2×K展开 | 同上 |
| R-005 | BB1 | R>0,K>4096，其余同上 | 同上 | kernel<N,P,K,D,C,1> | 1×K展开；源注释称reshape融合减少物化，物理效果未验证 | 大K仍可能超预算，无重试 |

### 隐藏性能 Guard

| Guard | Host/Tiling条件 | Device/资源原因 | 影响Route | 不满足时去向 | 源码符号 |
|---|---|---|---|---|---|
| pool_size | assert P>=4 | 编译器对短轴transpose的源内约束 | 全部 | assert失败 | Direct开头 |
| 行覆盖 | R=min(请求,两输入行数)，Qpad>=R | row_mask以裁剪后的R判断 | 全部 | Qpad不足assert，其余裁剪 | Direct与row_mask |
| K一致 | assert N*P==K，未检查N>0 | 前半写K列，tail从TOPK开始 | 自有Kernel各Route | 不一致assert；R>0/K0选择器除零 | _choose_block_b/Direct |
| 输出行对齐 | A=ceil(W/8)*8 | 32字节行pitch，view只隐藏padding | 全部 | 不返回连续拷贝 | out_cols_pad/return |
| UB启发式 | 16K每行、128KiB预算，BB最低1 | transpose/reshape的逻辑物化成本 | R-002..005 | 不检测实际UB；无硬件fallback | _choose_block_b |
| arange准入 | 未检查N/P/K/D为合法扩展shape | arange直接使用这些constexpr；D=P-1通常非二次幂 | R-002..005 | CANN Triton扩展合同未固定，不推定成功或编译失败 | kernel四处arange |
| 属性cache | 无参cache，首次current_device | C来自缓存vectorcore数 | R-002..005 | 属性不正assert，不按新device自动刷新 | get_device_properties |
| 设备/索引 | 未检查同device或值域 | 无pool值和因果长度过滤 | 全部 | 合同外无安全/语义保证 | Direct与整数算式 |

### POD/ABI

无自定义POD/sizeof/offsetof合同。下表逐项描述实际Kernel字段；constexpr无Device POD偏移，其他机器位宽/指针ABI由Triton推导。

| 结构 | 字段 | 类型/位宽 | ABI布局 | 单位 | Host/launcher producer | Device consumer | 边界 |
|---|---|---|---|---|---|---|---|
| JIT参数 | pool_indices_ptr | INT32指针；指针机器ABI外部 | 无自定义POD偏移 | 元素/索引/列；常量为编译参数 | pool_indices | 二维stride load | 有效pool值 |
| JIT参数 | seq_lens_per_token_ptr | INT32指针；指针机器ABI外部 | 无自定义POD偏移 | 元素/索引/列；常量为编译参数 | seq_lens_per_token | ptr+r | 连续一维 |
| JIT参数 | out_ptr | INT32指针；指针机器ABI外部 | 无自定义POD偏移 | 元素/索引/列；常量为编译参数 | full输出base | main/tail store | base宽A |
| JIT参数 | stride_pi0 | tl.constexpr int；指针机器ABI外部 | 无自定义POD偏移 | 元素/索引/列；常量为编译参数 | pool_indices.stride(0) | row*stride_pi0 | 元素/行 |
| JIT参数 | stride_pi1 | tl.constexpr int；指针机器ABI外部 | 无自定义POD偏移 | 元素/索引/列；常量为编译参数 | pool_indices.stride(1) | pool_col*stride_pi1 | 元素/列 |
| JIT参数 | stride_o0 | tl.constexpr int；指针机器ABI外部 | 无自定义POD偏移 | 元素/索引/列；常量为编译参数 | out.stride(0)=A | row*stride_o0 | 元素/行 |
| JIT参数 | stride_o1 | tl.constexpr int；指针机器ABI外部 | 无自定义POD偏移 | 元素/索引/列；常量为编译参数 | out.stride(1)=1 | col*stride_o1 | 元素/列 |
| JIT参数 | n_real | runtime int，位宽外部；指针机器ABI外部 | 无自定义POD偏移 | 元素/索引/列；常量为编译参数 | min(请求R,两输入行数) | range终点/row_mask | 裁剪后有效行 |
| JIT参数 | N_POOL_TOPK | tl.constexpr int；指针机器ABI外部 | 无自定义POD偏移 | 元素/索引/列；常量为编译参数 | pool_indices.shape[1] | arange(N)/reshape | N>0才可资源选择 |
| JIT参数 | POOL_SIZE | tl.constexpr int；指针机器ABI外部 | 无自定义POD偏移 | 元素/索引/列；常量为编译参数 | pool_size | arange(P)/pool展开/tail整数除法 | P>=4 |
| JIT参数 | TOPK | tl.constexpr int；指针机器ABI外部 | 无自定义POD偏移 | 元素/索引/列；常量为编译参数 | index_topk=N*P | tail列起点 | token列 |
| JIT参数 | TAIL_LEN | tl.constexpr int；指针机器ABI外部 | 无自定义POD偏移 | 元素/索引/列；常量为编译参数 | pool_size-1 | arange(D)/tail store | P-1列 |
| JIT参数 | NUM_CORES | tl.constexpr int；指针机器ABI外部 | 无自定义POD偏移 | 元素/索引/列；常量为编译参数 | min(ceil(R/BB),Vcores) | 循环步长C*BB | 仅非空生成且须正 |
| JIT参数 | BLOCK_B | tl.constexpr int；指针机器ABI外部 | 无自定义POD偏移 | 元素/索引/列；常量为编译参数 | _choose_block_b(N,P) | arange(BB)/static_range(BB) | 1/2/4/8 |

### Route 源码闭包

| Route | Key/selector | Host/Tiling producer | POD/参数 | Kernel entry/router节点 | Kernel body/直接依赖 | 构建接线 |
|---|---|---|---|---|---|---|
| R-001 | R<=0 | _expand_kpool_group_and_tail_to_topk | full及slice参数 | 无自有Device节点 | Torch常量初始化/view框架边界 | stage_runtime复制Python树 |
| R-002 | BB8 | Direct/_choose_block_b/helper | 14个字段，BB8 | 唯一kernel grid(C,) | impl两阶段body，helper属性 | 运行时JIT，Python打包 |
| R-003 | BB4 | 同上 | 同字段，BB4 | 同一entry | 同body，4行tile | 同上 |
| R-004 | BB2 | 同上 | 同字段，BB2 | 同一entry | 同body，2行tile | 同上 |
| R-005 | BB1 | 同上 | 同字段，BB1 | 同一entry | 同body，1行tile | 同上 |

## Kernel 实现

### 公共执行流程

前置full写完整base为-1，然后自有Kernel仅覆盖前R行可见W列。无自有跨Kernel scratch；交接介质即最终GM输出，extent=4Qpad*A，owner为Torch对象；同流framework初始化→Triton写和返回view所需排序由框架提供，跨流需调用方保证。不对实际Torch fill节点的内部实现作source_closed宣称。

### Route R-001：仅初始化输出并返回view

#### 适用条件

##### 选择证据

完整元数据检查/full分配之后，`if n_real > 0`为假；正常域R=0，原始函数也接受负R进入此分支。

#### Device 数据流

##### 函数级调用链

`Direct -> torch.full([Qpad,A],-1) -> out[:, :W]`。无自有Kernel、属性查询、BB选择或device body。

##### 源码等价伪码

```text
R=min(n_req,input_rows,seq_rows); validate metadata
base=full([Qpad,A],-1,int32)
if R<=0: return base[:, :W]
```

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | offset/extent | producer/consumer | owner/lifetime | 复用 |
|---|---|---|---|---|
| GM base | 4Qpad*A字节 | 框架full/返回view | Torch；view持有storage | 全部初始化为-1 |
| 输出view | shape[Qpad,W],rowstride A | slice/下游 | 同base | 零复制，未去除物理padding |

##### 分层内存布局

N/A：无自有AIV UB/TQue/TBuf或dynamic UB，只有框架分配/常量初始化。

##### 字节账与复用顺序

base有效payload容量4Qpad*A，逻辑初始化写同量；自有Kernel流量0、workspace0。框架实际物理填充过程和allocator取整不在固定源内。

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer/consumer | 保护对象 | 精度/尾块 |
|---|---|---|---|---|
| 输出准备 | Torch full/view框架 | full/返回view | 全base | INT32 -1，所有padding行/列都已初始化 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号 | 实现事实 |
|---|---|---|---|
| Host | impl | _expand_kpool_group_and_tail_to_topk | full后仅R>0才launch |
| Entry | impl | R<=0分支 | 不调用自有kernel |
| Device | impl | 无 | 不伪造copy/compute流程 |

### Route R-002：每tile展开8行

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | impl | _choose_block_b | R>0,0<K<=1024，16K启发式 | BB=8 |
| Launcher | impl/helper | Direct/get_device_properties | C=min(ceil(R/8),Vcores)，Vcores>0 | grid(C,) |
| Entry | impl | _expand_kpool_group_and_tail_to_topk_kernel<...,8> | p=program_id(0) | 两阶段body |

#### Device 数据流

##### 函数级调用链

```text
full输出初始化 -> Direct JIT launch
 -> kernel<...,BLOCK_B=8>
 -> for r0=p*8;r0<R;r0+=C*8
    -> load pool tile -> multiply/add token offsets -> trans/reshape -> main store
    -> static_range(8)：load逐行seq -> div/mul/sub tail -> where -> tail store
```

##### 源码等价伪码

```text
for r0 in range(p*8,R,C*8):
 rows=r0+arange(8); rm=rows<R
 pidx=int32(load(pool+rows[:,None]*spi0+arange(N)[None,:]*spi1,rm[:,None],other=0))
 base=pidx*P
 tmp=arange(P)[None,:,None]+base[:,None,:]  # [BB,P,N]
 result=reshape(trans(tmp,[0,2,1]),[8,N*P])  # [BB,N,P] -> pool-major columns
 masked_store(out+rows[:,None]*so0+arange(K)[None,:]*so1,result,rm[:,None])
 for m in static_range(8):
  r=r0+m; valid=r<R
  L=int32(masked_load(seq+r,valid,other=0))
  start=(L//P)*P; count=L-start
  j=arange(D); vals=where(j<count,start+j,-1)
  masked_store(out+r*so0+K*so1+j*so1,vals,valid)
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/对象 | offset/地址公式 | extent/容量 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| pool GM | row*spi0+i*spi1 | 每有效行4N字节 | INT32[rows,N] | 调用方 | pidx/base | 调用方至完成 | 两stride，不自动连续化 |
| seq GM | r | 每有效行4字节 | 连续INT32 | 调用方 | tail start/count | 同上 | 未传seq stride |
| 输出base GM | row*A+col；tail从K开始 | 总4Qpad*A，当前每有效行写4W | INT32 | full先-1，本Kernel覆盖 | 返回view/下游 | Torch/view持有base | A为8元素对齐，W可能较窄 |
| 展开逻辑tile | [8,P,N]→[8,N,P]→[8,K] | 逻辑INT32 8K元素/视图 | Triton SSA | base+offset | trans/reshape/main store | 单轮 | 物理拷贝次数不能仅据源注释断言 |
| tail逻辑向量 | D=P-1 lane，逐m处理 | INT32[D]与mask | Triton SSA | seq算式/where | tail store | static迭代，实际物理复用外部 | 不是手工InitBuffer |

##### 分层内存布局

N/A：源码无AIV InitBuffer/TQue/TBuf，也无显式dynamic UB。真实层级是GM pool/seq→Triton展开/变形/tail SSA→最终GM。planner对当前BB=8使用`16*8*K`字节估算；它不是已经分配的UB账本。

##### 字节账与复用顺序

有效行集合只访问输入pool 4RN、seq4R、写输出4RW；前置full初始化额外写4Qpad*A。总逻辑流量`4*(Qpad*A+R*(N+1+W))`，workspace0；忽略实际cache/指令事务/编译临时。末tile无效行load other0、store被row/valid mask禁止；全padding行及base中隐藏列仍保留full的-1。

当前planner估算为16*8*K。在本K区间该启发式不超过128KiB，但不能推导实际物理峰值或所有平台UB安全。

| 复用子区 | 写入者 | 消费点 | 下一次覆盖 | 同步依据 | 安全条件 |
|---|---|---|---|---|---|
| GM有效行 | 框架full→本program | 下游 | 无同launch重叠写；后续调用另分配base | 框架同流排序，跨流调用方负责 | C>0、循环步长C*8，输入元数据/整数计算有效 |
| 展开/tail SSA | 当前r0轮 | store | 下一个r0/m | 编译器数据依赖 | 无可手工操作的Queue深度或barrier合同 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| pool load | tl.load(mask=row_mask[:,None],other=0) | GM pool | int32 base | 有效行 | N列没有尾mask；arange(N)直接用N |
| 展开 | INT32 mul/add,tl.trans,tl.reshape | pool*P+offset | main store | pool-major顺序 | 源注释shape标注可能颠倒，真实广播先[BB,P,N]再转[BB,N,P] |
| main store | row_mask[:,None] | BB×K结果 | 最终GM | 前R行前K列 | K列无额外tail padding |
| tail | int32 load/div/mul/sub/where | 每行L | D列store | 最后不足P token | L非负时count在0..P-1；未guard负数/溢出 |
| tail store | mask=r<R | D宽vals | GM列K..K+D-1 | 有效行尾 | 不足tail位置写-1，padding行保持原full值 |
| 全launch | 无barrier/atomic | 独占行program | 下游 | tensor与stream寿命 | 不是同步返回；实际Triton布局外部 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/实例 | 实现事实 |
|---|---|---|---|
| Host producer | impl/helper | Direct/_choose_block_b/get_device_properties | BB=8、C及所有stride/constexpr |
| Entry/router | impl | kernel<...,8> | 固定C个program，r0轮转 |
| Device body | impl | kernel的Phase1/Phase2 | 展开/转置/reshape与逐行tail，全部mask和GM地址 |

### Route R-003：每tile展开4行

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | impl | _choose_block_b | R>0,1024<K<=2048，16K启发式 | BB=4 |
| Launcher | impl/helper | Direct/get_device_properties | C=min(ceil(R/4),Vcores)，Vcores>0 | grid(C,) |
| Entry | impl | _expand_kpool_group_and_tail_to_topk_kernel<...,4> | p=program_id(0) | 两阶段body |

#### Device 数据流

##### 函数级调用链

```text
full输出初始化 -> Direct JIT launch
 -> kernel<...,BLOCK_B=4>
 -> for r0=p*4;r0<R;r0+=C*4
    -> load pool tile -> multiply/add token offsets -> trans/reshape -> main store
    -> static_range(4)：load逐行seq -> div/mul/sub tail -> where -> tail store
```

##### 源码等价伪码

```text
for r0 in range(p*4,R,C*4):
 rows=r0+arange(4); rm=rows<R
 pidx=int32(load(pool+rows[:,None]*spi0+arange(N)[None,:]*spi1,rm[:,None],other=0))
 base=pidx*P
 tmp=arange(P)[None,:,None]+base[:,None,:]  # [BB,P,N]
 result=reshape(trans(tmp,[0,2,1]),[4,N*P])  # [BB,N,P] -> pool-major columns
 masked_store(out+rows[:,None]*so0+arange(K)[None,:]*so1,result,rm[:,None])
 for m in static_range(4):
  r=r0+m; valid=r<R
  L=int32(masked_load(seq+r,valid,other=0))
  start=(L//P)*P; count=L-start
  j=arange(D); vals=where(j<count,start+j,-1)
  masked_store(out+r*so0+K*so1+j*so1,vals,valid)
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/对象 | offset/地址公式 | extent/容量 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| pool GM | row*spi0+i*spi1 | 每有效行4N字节 | INT32[rows,N] | 调用方 | pidx/base | 调用方至完成 | 两stride，不自动连续化 |
| seq GM | r | 每有效行4字节 | 连续INT32 | 调用方 | tail start/count | 同上 | 未传seq stride |
| 输出base GM | row*A+col；tail从K开始 | 总4Qpad*A，当前每有效行写4W | INT32 | full先-1，本Kernel覆盖 | 返回view/下游 | Torch/view持有base | A为8元素对齐，W可能较窄 |
| 展开逻辑tile | [4,P,N]→[4,N,P]→[4,K] | 逻辑INT32 4K元素/视图 | Triton SSA | base+offset | trans/reshape/main store | 单轮 | 物理拷贝次数不能仅据源注释断言 |
| tail逻辑向量 | D=P-1 lane，逐m处理 | INT32[D]与mask | Triton SSA | seq算式/where | tail store | static迭代，实际物理复用外部 | 不是手工InitBuffer |

##### 分层内存布局

N/A：源码无AIV InitBuffer/TQue/TBuf，也无显式dynamic UB。真实层级是GM pool/seq→Triton展开/变形/tail SSA→最终GM。planner对当前BB=4使用`16*4*K`字节估算；它不是已经分配的UB账本。

##### 字节账与复用顺序

有效行集合只访问输入pool 4RN、seq4R、写输出4RW；前置full初始化额外写4Qpad*A。总逻辑流量`4*(Qpad*A+R*(N+1+W))`，workspace0；忽略实际cache/指令事务/编译临时。末tile无效行load other0、store被row/valid mask禁止；全padding行及base中隐藏列仍保留full的-1。

当前planner估算为16*4*K。在本K区间该启发式不超过128KiB，但不能推导实际物理峰值或所有平台UB安全。

| 复用子区 | 写入者 | 消费点 | 下一次覆盖 | 同步依据 | 安全条件 |
|---|---|---|---|---|---|
| GM有效行 | 框架full→本program | 下游 | 无同launch重叠写；后续调用另分配base | 框架同流排序，跨流调用方负责 | C>0、循环步长C*4，输入元数据/整数计算有效 |
| 展开/tail SSA | 当前r0轮 | store | 下一个r0/m | 编译器数据依赖 | 无可手工操作的Queue深度或barrier合同 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| pool load | tl.load(mask=row_mask[:,None],other=0) | GM pool | int32 base | 有效行 | N列没有尾mask；arange(N)直接用N |
| 展开 | INT32 mul/add,tl.trans,tl.reshape | pool*P+offset | main store | pool-major顺序 | 源注释shape标注可能颠倒，真实广播先[BB,P,N]再转[BB,N,P] |
| main store | row_mask[:,None] | BB×K结果 | 最终GM | 前R行前K列 | K列无额外tail padding |
| tail | int32 load/div/mul/sub/where | 每行L | D列store | 最后不足P token | L非负时count在0..P-1；未guard负数/溢出 |
| tail store | mask=r<R | D宽vals | GM列K..K+D-1 | 有效行尾 | 不足tail位置写-1，padding行保持原full值 |
| 全launch | 无barrier/atomic | 独占行program | 下游 | tensor与stream寿命 | 不是同步返回；实际Triton布局外部 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/实例 | 实现事实 |
|---|---|---|---|
| Host producer | impl/helper | Direct/_choose_block_b/get_device_properties | BB=4、C及所有stride/constexpr |
| Entry/router | impl | kernel<...,4> | 固定C个program，r0轮转 |
| Device body | impl | kernel的Phase1/Phase2 | 展开/转置/reshape与逐行tail，全部mask和GM地址 |

### Route R-004：每tile展开2行

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | impl | _choose_block_b | R>0,2048<K<=4096，16K启发式 | BB=2 |
| Launcher | impl/helper | Direct/get_device_properties | C=min(ceil(R/2),Vcores)，Vcores>0 | grid(C,) |
| Entry | impl | _expand_kpool_group_and_tail_to_topk_kernel<...,2> | p=program_id(0) | 两阶段body |

#### Device 数据流

##### 函数级调用链

```text
full输出初始化 -> Direct JIT launch
 -> kernel<...,BLOCK_B=2>
 -> for r0=p*2;r0<R;r0+=C*2
    -> load pool tile -> multiply/add token offsets -> trans/reshape -> main store
    -> static_range(2)：load逐行seq -> div/mul/sub tail -> where -> tail store
```

##### 源码等价伪码

```text
for r0 in range(p*2,R,C*2):
 rows=r0+arange(2); rm=rows<R
 pidx=int32(load(pool+rows[:,None]*spi0+arange(N)[None,:]*spi1,rm[:,None],other=0))
 base=pidx*P
 tmp=arange(P)[None,:,None]+base[:,None,:]  # [BB,P,N]
 result=reshape(trans(tmp,[0,2,1]),[2,N*P])  # [BB,N,P] -> pool-major columns
 masked_store(out+rows[:,None]*so0+arange(K)[None,:]*so1,result,rm[:,None])
 for m in static_range(2):
  r=r0+m; valid=r<R
  L=int32(masked_load(seq+r,valid,other=0))
  start=(L//P)*P; count=L-start
  j=arange(D); vals=where(j<count,start+j,-1)
  masked_store(out+r*so0+K*so1+j*so1,vals,valid)
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/对象 | offset/地址公式 | extent/容量 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| pool GM | row*spi0+i*spi1 | 每有效行4N字节 | INT32[rows,N] | 调用方 | pidx/base | 调用方至完成 | 两stride，不自动连续化 |
| seq GM | r | 每有效行4字节 | 连续INT32 | 调用方 | tail start/count | 同上 | 未传seq stride |
| 输出base GM | row*A+col；tail从K开始 | 总4Qpad*A，当前每有效行写4W | INT32 | full先-1，本Kernel覆盖 | 返回view/下游 | Torch/view持有base | A为8元素对齐，W可能较窄 |
| 展开逻辑tile | [2,P,N]→[2,N,P]→[2,K] | 逻辑INT32 2K元素/视图 | Triton SSA | base+offset | trans/reshape/main store | 单轮 | 物理拷贝次数不能仅据源注释断言 |
| tail逻辑向量 | D=P-1 lane，逐m处理 | INT32[D]与mask | Triton SSA | seq算式/where | tail store | static迭代，实际物理复用外部 | 不是手工InitBuffer |

##### 分层内存布局

N/A：源码无AIV InitBuffer/TQue/TBuf，也无显式dynamic UB。真实层级是GM pool/seq→Triton展开/变形/tail SSA→最终GM。planner对当前BB=2使用`16*2*K`字节估算；它不是已经分配的UB账本。

##### 字节账与复用顺序

有效行集合只访问输入pool 4RN、seq4R、写输出4RW；前置full初始化额外写4Qpad*A。总逻辑流量`4*(Qpad*A+R*(N+1+W))`，workspace0；忽略实际cache/指令事务/编译临时。末tile无效行load other0、store被row/valid mask禁止；全padding行及base中隐藏列仍保留full的-1。

当前planner估算为16*2*K。在本K区间该启发式不超过128KiB，但不能推导实际物理峰值或所有平台UB安全。

| 复用子区 | 写入者 | 消费点 | 下一次覆盖 | 同步依据 | 安全条件 |
|---|---|---|---|---|---|
| GM有效行 | 框架full→本program | 下游 | 无同launch重叠写；后续调用另分配base | 框架同流排序，跨流调用方负责 | C>0、循环步长C*2，输入元数据/整数计算有效 |
| 展开/tail SSA | 当前r0轮 | store | 下一个r0/m | 编译器数据依赖 | 无可手工操作的Queue深度或barrier合同 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| pool load | tl.load(mask=row_mask[:,None],other=0) | GM pool | int32 base | 有效行 | N列没有尾mask；arange(N)直接用N |
| 展开 | INT32 mul/add,tl.trans,tl.reshape | pool*P+offset | main store | pool-major顺序 | 源注释shape标注可能颠倒，真实广播先[BB,P,N]再转[BB,N,P] |
| main store | row_mask[:,None] | BB×K结果 | 最终GM | 前R行前K列 | K列无额外tail padding |
| tail | int32 load/div/mul/sub/where | 每行L | D列store | 最后不足P token | L非负时count在0..P-1；未guard负数/溢出 |
| tail store | mask=r<R | D宽vals | GM列K..K+D-1 | 有效行尾 | 不足tail位置写-1，padding行保持原full值 |
| 全launch | 无barrier/atomic | 独占行program | 下游 | tensor与stream寿命 | 不是同步返回；实际Triton布局外部 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/实例 | 实现事实 |
|---|---|---|---|
| Host producer | impl/helper | Direct/_choose_block_b/get_device_properties | BB=2、C及所有stride/constexpr |
| Entry/router | impl | kernel<...,2> | 固定C个program，r0轮转 |
| Device body | impl | kernel的Phase1/Phase2 | 展开/转置/reshape与逐行tail，全部mask和GM地址 |

### Route R-005：每tile展开1行

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | impl | _choose_block_b | R>0,K>4096，16K启发式 | BB=1 |
| Launcher | impl/helper | Direct/get_device_properties | C=min(ceil(R/1),Vcores)，Vcores>0 | grid(C,) |
| Entry | impl | _expand_kpool_group_and_tail_to_topk_kernel<...,1> | p=program_id(0) | 两阶段body |

#### Device 数据流

##### 函数级调用链

```text
full输出初始化 -> Direct JIT launch
 -> kernel<...,BLOCK_B=1>
 -> for r0=p*1;r0<R;r0+=C*1
    -> load pool tile -> multiply/add token offsets -> trans/reshape -> main store
    -> static_range(1)：load逐行seq -> div/mul/sub tail -> where -> tail store
```

##### 源码等价伪码

```text
for r0 in range(p*1,R,C*1):
 rows=r0+arange(1); rm=rows<R
 pidx=int32(load(pool+rows[:,None]*spi0+arange(N)[None,:]*spi1,rm[:,None],other=0))
 base=pidx*P
 tmp=arange(P)[None,:,None]+base[:,None,:]  # [BB,P,N]
 result=reshape(trans(tmp,[0,2,1]),[1,N*P])  # [BB,N,P] -> pool-major columns
 masked_store(out+rows[:,None]*so0+arange(K)[None,:]*so1,result,rm[:,None])
 for m in static_range(1):
  r=r0+m; valid=r<R
  L=int32(masked_load(seq+r,valid,other=0))
  start=(L//P)*P; count=L-start
  j=arange(D); vals=where(j<count,start+j,-1)
  masked_store(out+r*so0+K*so1+j*so1,vals,valid)
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/对象 | offset/地址公式 | extent/容量 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| pool GM | row*spi0+i*spi1 | 每有效行4N字节 | INT32[rows,N] | 调用方 | pidx/base | 调用方至完成 | 两stride，不自动连续化 |
| seq GM | r | 每有效行4字节 | 连续INT32 | 调用方 | tail start/count | 同上 | 未传seq stride |
| 输出base GM | row*A+col；tail从K开始 | 总4Qpad*A，当前每有效行写4W | INT32 | full先-1，本Kernel覆盖 | 返回view/下游 | Torch/view持有base | A为8元素对齐，W可能较窄 |
| 展开逻辑tile | [1,P,N]→[1,N,P]→[1,K] | 逻辑INT32 1K元素/视图 | Triton SSA | base+offset | trans/reshape/main store | 单轮 | 物理拷贝次数不能仅据源注释断言 |
| tail逻辑向量 | D=P-1 lane，逐m处理 | INT32[D]与mask | Triton SSA | seq算式/where | tail store | static迭代，实际物理复用外部 | 不是手工InitBuffer |

##### 分层内存布局

N/A：源码无AIV InitBuffer/TQue/TBuf，也无显式dynamic UB。真实层级是GM pool/seq→Triton展开/变形/tail SSA→最终GM。planner对当前BB=1使用`16*1*K`字节估算；它不是已经分配的UB账本。

##### 字节账与复用顺序

有效行集合只访问输入pool 4RN、seq4R、写输出4RW；前置full初始化额外写4Qpad*A。总逻辑流量`4*(Qpad*A+R*(N+1+W))`，workspace0；忽略实际cache/指令事务/编译临时。末tile无效行load other0、store被row/valid mask禁止；全padding行及base中隐藏列仍保留full的-1。

当前planner估算为16*1*K。即使BB降为1也没有检查这项是否仍超128KiB，且源码注释声称BB1仅两份物化；这些都不能代替实际lowering和UB准入。

| 复用子区 | 写入者 | 消费点 | 下一次覆盖 | 同步依据 | 安全条件 |
|---|---|---|---|---|---|
| GM有效行 | 框架full→本program | 下游 | 无同launch重叠写；后续调用另分配base | 框架同流排序，跨流调用方负责 | C>0、循环步长C*1，输入元数据/整数计算有效 |
| 展开/tail SSA | 当前r0轮 | store | 下一个r0/m | 编译器数据依赖 | 无可手工操作的Queue深度或barrier合同 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| pool load | tl.load(mask=row_mask[:,None],other=0) | GM pool | int32 base | 有效行 | N列没有尾mask；arange(N)直接用N |
| 展开 | INT32 mul/add,tl.trans,tl.reshape | pool*P+offset | main store | pool-major顺序 | 源注释shape标注可能颠倒，真实广播先[BB,P,N]再转[BB,N,P] |
| main store | row_mask[:,None] | BB×K结果 | 最终GM | 前R行前K列 | K列无额外tail padding |
| tail | int32 load/div/mul/sub/where | 每行L | D列store | 最后不足P token | L非负时count在0..P-1；未guard负数/溢出 |
| tail store | mask=r<R | D宽vals | GM列K..K+D-1 | 有效行尾 | 不足tail位置写-1，padding行保持原full值 |
| 全launch | 无barrier/atomic | 独占行program | 下游 | tensor与stream寿命 | 不是同步返回；实际Triton布局外部 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/实例 | 实现事实 |
|---|---|---|---|
| Host producer | impl/helper | Direct/_choose_block_b/get_device_properties | BB=1、C及所有stride/constexpr |
| Entry/router | impl | kernel<...,1> | 固定C个program，r0轮转 |
| Device body | impl | kernel的Phase1/Phase2 | 展开/转置/reshape与逐行tail，全部mask和GM地址 |

## 算子特定优化

### Trick T-001：按展开tile估算裁剪批量行数

#### 触发与源码依据

- 适用Route：R-002..005。
- 触发条件：R>0、N*P>0。
- Golden 来源：[BLOCK_B选择](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/expand_kpool_group_and_tail_to_topk.py#L15-L21)。

**官方源码（固定Commit连续逐字摘录）**：

```python
def _choose_block_b(n_pool_topk: int, pool_size: int) -> int:
    # Once BLOCK_B > 1 the expanded tile is materialised four times per row (tmp,
    # transpose, reshape and the pipeline copy); BLOCK_B == 1 fuses the transpose
    # into the reshape and only keeps two.
    tile_bytes_per_row = 4 * n_pool_topk * pool_size * 4
    max_rows = max(1, UB_TILE_BUDGET * 1024 // tile_bytes_per_row)
    return min(8, 1 << (max_rows.bit_length() - 1))
```

#### 机制与设计原因

把4份INT32展开物化的源内估算写成16K字节/行，从128KiB常量预算反推max_rows，再取不大于它的二次幂并封顶8。它会改变同program批量行数、局部tile大小及轮转次数；未查询真实UB，也没有测得跨平台吞吐。源码关于BB1融合为两份物化的注释属于实现意图，最终物理分配要看工具链。

#### 迁移边界

- 适用：pool展开量K变化大，需控制批量行数的整数重排。
- 前提：非零K、合法编译shape、Vcores正、128KiB预算适合目标lowering。
- 失效：BB最小1仍可能过大，没有硬件cap检查或更细列切分fallback；不能直接迁用常量192KiB到任意平台。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

固定仓未提供可验证反例；不要把planner估算或注释物化数当成实际InitBuffer/峰值UB测量。

### Trick T-002：转置再reshape保持pool内token连续顺序

#### 触发与源码依据

- 适用Route：R-002..005。
- 触发条件：BB行、N个pool、每pool P个token的逻辑广播与reshape准入满足。
- Golden 来源：[展开layout](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/expand_kpool_group_and_tail_to_topk.py#L69-L71)。

**官方源码（固定Commit连续逐字摘录）**：

```python
        tmp = o_offs[None, :, None] + base[:, None, :]  # [BLOCK_B, P, N]
        tmp = tl.trans(tmp, [0, 2, 1])  # [BLOCK_B, N, P]
        result = tl.reshape(tmp, (BLOCK_B, N_POOL_TOPK * POOL_SIZE))
```

#### 机制与设计原因

offset广播[1,P,1]与base[BB,1,N]先形成[BB,P,N]，交换后两轴成为[BB,N,P]，再展平为[BB,N*P]。因此每个pool的P个连续token相邻，pool选择顺序不变；若省去transpose，会变成按pool内offset交错的另一种输出顺序。逻辑变形在同一个Triton Kernel中，不物化GM中间矩阵。

#### 迁移边界

- 适用：分组索引扩展、同一输出还需追加逐行tail。
- 前提：固定广播轴、reshape元素数、stride和K=N*P一致，INT32乘加不溢出。
- 失效：改变轴次序、把逻辑W当物理行pitchA、非法pool索引都不能靠row_mask修复。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

固定仓未提供可验证反例；源公式已经区分pool-major与offset-major顺序，不以两种输出的集合相同替代顺序相同。

## 模板与实现对比

| 维度 | R-001 | BB8/4/2/1四Route | 设计依据 |
|---|---|---|---|
| 命中/优先级 | R<=0 | R>0按K区间选择BB | 先full初始化、再分支 |
| 模板/dtype | 无自有Kernel | INT32输入/输出，14参数 | 不按dtype选不同数学 |
| 循环/分核 | 无 | C核program轮转r0，后半static_range(BB) | pool并行展开，tail逐行保持布局 |
| Queue/TBuf/dynamic UB | 无 | 无手工申请，只有Triton SSA | 不臆造物理字节 |
| 内存/复用 | 4Qpad*A初始化 | 同base，覆盖4RW，无GM scratch | view保留对齐pitch |
| 搬运/API | 框架full/view | load/add/mul/trans/reshape/where/store | 两阶段一自有Kernel |
| 同步/精度/tail | 全-1 | INT32算式，row/valid mask，D宽tail | 无跨programbarrier |
| fallback/失败 | 不查属性 | 无UB重试/参考回退 | 原异常传播 |

## 平台差异

| 项目 | A2 | A3 | Ascend950 |
|---|---|---|---|
| 支持状态 | arch22公开支持，2201→910b | arch22公开支持，2201→910_93 | arch35文档已验证声明，非本次复测 |
| Host/Launcher | 共享128KiB预算/属性helper | 同A2 | 同源常量，未读取950实际UB |
| Kernel/资源 | 同Triton逻辑body，实际lowering外部 | 不推断相同物理资源 | 无源内平台分支，不推断与arch22相同物化/吞吐 |

## 限制与失败边界

- draft：元数据检查不涵盖同device、非负请求/长度、合法pool值、INT32范围或实际编译资源；source closure不等于这些条件已满足。
- 输出是[Qpad,A]的[:,:W] view，W不等于A时不能按连续W行消费。隐藏列和padding行保持-1，不等于所有无效输入pool都会被规范化成-1。
- 有效R会被min裁剪；没有负R检查。R>0/K0使资源选择除零，R<=0不进入该选择器。
- arange直接使用N、P、K及D=P-1；Host只检查P>=4而不检查二次幂，具体CANN扩展准入未固定，不能断言必然可编译或必然失败。
- 128KiB是源内常量启发式，BB最低1并无进一步可行性guard；编译器物理UB/寄存器、transpose/reshape临时数没有本次验证。
- get_device_properties是无参cache，设备切换与异步stream集成由调用方/框架负责；包导入还要求native库完整。未设置verified。
- 本次知识提取未执行编译、真机、数值或性能测试。

## 源码索引

### 链路索引

| 链路阶段 | 文件 | 关键符号 | 支撑内容 |
|---|---|---|---|
| primary | [docs/api/zh/operators/indexer/expand_kpool_group_and_tail_to_topk.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/indexer/expand_kpool_group_and_tail_to_topk.md) | 芯片支持/参数表 | 平台、pool_size与view合同 |
| implementation | [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/expand_kpool_group_and_tail_to_topk.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/expand_kpool_group_and_tail_to_topk.py) | Direct/_choose_block_b/kernel | 全部Host资源选择与两阶段body |
| supporting | [python/sgl_kernel_npu/sgl_kernel_npu/operators/indexer/expand_kpool_group_and_tail_to_topk.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/indexer/expand_kpool_group_and_tail_to_topk.py) | _triton_impl/公开入口 | auto/triton延迟转发、无自动回退 |
| implementation | [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py) | get_device_properties | 无参cache、current_device、两类核数检查 |
| supporting | [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/__init__.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/__init__.py) | 模块初始化 | 无额外算法调用 |
| supporting | [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/__init__.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/__init__.py) | 模块初始化 | 无额外算法调用 |
| implementation | [python/sgl_kernel_npu/sgl_kernel_npu/__init__.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py) | _load_sgl_kernel_npu | 原生库导入前提 |
| implementation | [python/sgl_kernel_npu/build_tools/torch_wheel.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/build_tools/torch_wheel.py) | stage_runtime/setup_refactor | 完整Python树打包 |
| supporting | [setup.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/setup.py) | main | wheel入口 |
| supporting | [python/sgl_kernel_npu/README.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md) | REFACTOR builds | 架构/Python源范围 |
| supporting | [csrc/cmake/architectures.json](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json) | 2201/3510 | 产品对应 |
| supporting | [.github/workflows/pr-test-kernels.yml](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernels.yml) | cann_version9.1.0 | 任务基线配置，非执行结果 |

正文impl为完整Triton实现文件，helper为同源属性工具；其它逻辑算子与torch_native参考未并入此Direct图。

### 实现复用检查

| 检查项 | 可复用事实 | 不得改变的约束 | 源码符号 |
|---|---|---|---|
| ABI/POD | 3指针、4stride constexpr、R、6meta constexpr | 参数单位/顺序及原stride | kernel签名/launch |
| 调用顺序 | min裁剪→检查→full→选择/launch→view | 初始化先于覆盖，跨流需排序 | Direct |
| workspace/内存 | 无GM scratch，物理pitchA | 不用逻辑W替代stride(0) | out_cols_pad/return |
| 同步 | 独占行轮转，无atomic | C>0、rowmask、输入就绪/对象寿命 | for r0/row_mask |
| 精度与尾块 | INT32 pool扩展、非负seq tail | K=N*P，P>=4，工具链shape准入 | trans/reshape/where |
| 失败边界 | BB1仍可能超预算，无fallback | 不把常量预算当实测UB | _choose_block_b/helper |
