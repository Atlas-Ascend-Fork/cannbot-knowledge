---
type: Operator
title: "请求因果长度展开 950 Direct Invoke 算子知识"
description: "闭合DSA请求长度展开的Host校验、四类query tile与双输出，说明局部prefix归约、预分配地址复用及INT32/长度一致性边界。"
tags: [task.implementation, task.lookup, topic.data_movement, topic.memory, topic.precision, topic.programming_model]
status: draft
sources:
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/indexer/expand_causal_seqlens.md
    role: primary
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/expand_causal_seqlens.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/indexer/expand_causal_seqlens.py
    role: supporting
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
created_at: "2026-11-09T09:39:33Z"
updated_at: "2026-11-09T09:39:33Z"
platforms: ["950"]
cann_versions: ["9.1.0"]
---

# 请求因果长度展开 950 Direct Invoke 算子知识

## 算子速览

| 项目 | 内容 |
|---|---|
| 实际入口 | `sgl_kernel_npu.implementation.triton.indexer.expand_causal_seqlens.expand_causal_seqlens`，独立Direct Invoke |
| 计算语义 | 为请求r的第j个query生成`max(S[r]-q[r]+1,0)+j`及请求号r，按请求顺序packed |
| 输入输出 | 两个连续INT32[B]长度；输出连续INT32[T]和INT64[T]，可分别复用调用方缓冲 |
| 执行类型 | 单个Triton load/reduce/store Kernel；源码没有dot/Cube/AIC或MIX_CV节点 |
| Kernel路线 | R-001纯Host空域；R-002至R-005为Q=32/64/128/256四种query tile |
| 核心资源 | GM两个输入、两个输出；无算子自有workspace；逻辑BB长度prefix向量与Q长度输出向量，物理UB/寄存器由编译器决定 |
| 来源闭包 | direct_implementation_closed：完整launcher、参数、唯一Device body、延迟导入上下文及Python打包来源已闭合 |
| 验证状态 | 本次知识提取未执行编译、真机、数值或性能测试；不把文档的“已验证”转写为本次verified事件 |

## 接口与语义

### 计算语义

记B为请求数，q[r]为本次query数，S[r]为包括本次query的KV总长，T=total_q，M=max_query_len。调用方保证q与S非负、T=sum(q)、M>=max(q)，以及INT32加减、prefix和输出索引不溢出。令p[r]=sum(q[i],i<r)，则0<=j<q[r]时，`seqlens[p[r]+j]=max(S[r]-q[r]+1,0)+j`，`token_to_batch[p[r]+j]=r`。当S<q时实际公式从0递增，不能改成直接S-q+1，也不能声称最后一项恒为S。q[r]=0没有输出。

输出缓冲既不被读取也不保留旧有效值；它们可以分别传入或分别分配。传入对象按identity返回。两个输入保持只读，输出不得与任何输入或彼此重叠。这是调用方合同，launcher没有重叠检测。

### 输入、输出与属性

| 参数 | shape/layout | dtype | 约束、默认值与语义 |
|---|---|---|---|
| cache_seqlens | 连续一维[B] | INT32 | 与device完全一致，S[r]；支持合法storage_offset，不按通用stride寻址 |
| query_lens | 连续一维[B] | INT32 | 与device完全一致，q[r]>=0；长度值不在Host回读校验 |
| device | Host torch.device | 非Device数据 | 所有张量device比较必须相等；规范入口要求NPU，函数本身未显式检查device.type |
| total_q | Host int | Kernel标量类型由Triton推导 | T>=0且等于sum(q)，T>0要求M>0 |
| max_query_len | Host int | 不直接传给Kernel | M>=0并覆盖每个q，决定Q及grid第二维 |
| seqlens_out | 可选连续一维[T] | INT32 | 默认None则empty分配；传入则原地覆盖此输出对象 |
| token_to_batch_out | 可选连续一维[T] | INT64 | 默认None则empty分配；传入则复用 |

### 入口与版本

公共`operators.indexer.expand_causal_seqlens`的auto/triton延迟导入并转发该Direct函数；torch_native是独立实现，未进入本启动图，没有失败后自动切换。这里选择Direct函数作为完整算子入口，不伪造ACLNN封装或自定义Tiling。

固定SGL源码提交`dda6d36b0cdb4081e102d14c0a2fb276fc416e69`。公开文档分别列arch22支持、arch35已验证；README及architectures.json给出2201/3510到910B/910_93/950的对应。本卡使用CANN9.1.0任务基线，依据固定CI的9.1配置；未固定Triton/torch_npu二进制，也未承诺任意同版本编译产物一致。

## Host/Launcher 执行流程

### 参数校验与前处理

先执行`batch_size=cache_seqlens.shape[0]`，再按源码顺序校验两输入一维、相同B、stride(0)==1、INT32、与device相等，T/M非负及T>0时M>0。零维cache输入可能在自定义一维检查之前因shape[0]失败，不保证统一ValueError。

随后先分配/校验seqlens，再分配/校验token_to_batch。传入输出须一维、长度T、正确dtype/device及stride1。没有读取q值来验证非负、sum(q)、max(q)、INT32可表示性或输出互不重叠；也没有contiguous复制、CPU回退、npu属性查询或设备guard。分配和JIT异常直接传播。

### 参数、Workspace 与生命周期

无自定义POD/executor或workspace。新分配输出的有效payload容量为4T+8T=12T字节，不含框架allocator取整；输入payload共8B字节。复用两输出时不新增这12T容量，混合传入仅分配缺失者。所有输入、输出须存活到异步Kernel完成；返回tuple不包含同步等待。调用方保证跨stream生产者完成，框架持有实际stream、JIT代码及launch参数的生命周期。

### 启动图与失败传播

```text
包初始化：可选vendor路径处理 -> import torch/torch_npu -> load libsgl_kernel_npu.so
Direct launcher -> 输入检查 -> 输出分配/检查
  -> B==0 or T==0：直接返回两个输出
  -> BB=next_power_of_2(B), Q=clamp(next_power_of_2(M),32,256)
  -> grid=(B,ceil(M/Q)) -> 唯一_expand_causal_seqlens_kernel -> 返回同一输出对象
```

原生库加载是包导入条件；该Kernel不调用库中的数学算子。launcher没有前后自有Device节点、workspace边、event或cleanup节点。输出分配/检查先于空域返回；若B=0但调用方错误地给T>0，会返回未写的新分配缓冲或原缓冲，不能将此路径概括为“必为空输出”。正常合同下B=0必有T=0。

## Route 与参数设计

### 分核与资源计算

非空时BB=next_power_of_2(B)，Q取32/64/128/256，P=ceil(M/Q)。grid中的program(r,c)覆盖请求r与query区间[cQ,(c+1)Q)。每个program重新加载r个先前q值，归约为p[r]，再读取q[r]和S[r]。满足合同且无溢出时，各请求prefix区间互不重叠，各chunk也互不重叠，不需要atomic或跨program barrier。

每program输入逻辑GM读取4r+8字节；有效query数v=max(0,min(Q,q[r]-cQ))，输出写12v字节。整个launch逻辑流量为`P*(2B(B-1)+8B)+12T`字节；不计编译器重读、cache及物理事务取整。掩码prefix向量逻辑大小BB，只有索引<r的lane发起有效读取，不将全部4BB计为GM输入流量。M过大增大P并重复prefix工作，即使某些query chunk没有输出仍读取输入。

### Route 选择

| 顺序 | Route | Key/模板 | 精确选择条件与优先级 | 不适用去向 |
|---:|---|---|---|---|
| 1 | R-001 空域 | 无Kernel | 所有检查/输出准备之后，B==0或T==0 | 非空继续计算BB/Q |
| 2 | R-002 | BLOCK_QUERY=32 | B>0,T>0,1<=M<=32 | 下一Q区间 |
| 3 | R-003 | BLOCK_QUERY=64 | B>0,T>0,33<=M<=64 | 下一Q区间 |
| 4 | R-004 | BLOCK_QUERY=128 | B>0,T>0,65<=M<=128 | 下一Q区间 |
| 5 | R-005 | BLOCK_QUERY=256 | B>0,T>0,M>=129；M>256仍固定256 | 不做其它fallback |

```text
检查失败 -> Python异常
检查成功 -> 准备两个输出 -> B==0或T==0 ? R-001
否则按M选择Q=32/64/128/256 -> R-002/R-003/R-004/R-005
```

### 模板/实现执行矩阵

| Route | key/selector | dtype/shape/platform完整命中条件 | 执行拓扑与Kernel节点 | 实际模板/body | 内存与同步特征 | tail/fallback |
|---|---|---|---|---|---|---|
| R-001 | B==0或T==0 | 输入/输出检查通过；平台同整卡 | 纯Host，0节点 | expand_causal_seqlens直接return | 分配/复用输出，无Device读写 | 非零T与空B的合同错误未guard |
| R-002 | Q32 | 合同域、B/T>0、M1..32 | 单Kernel，grid(B,ceil(M/32)) | _expand_causal_seqlens_kernel<BB,32> | BB归约，32query lane，无自有workspace | 两个上界mask，无fallback |
| R-003 | Q64 | 合同域、B/T>0、M33..64 | 单Kernel，grid(B,ceil(M/64)) | _expand_causal_seqlens_kernel<BB,64> | BB归约，64query lane | 同上 |
| R-004 | Q128 | 合同域、B/T>0、M65..128 | 单Kernel，grid(B,ceil(M/128)) | _expand_causal_seqlens_kernel<BB,128> | BB归约，128query lane | 同上 |
| R-005 | Q256 | 合同域、B/T>0、M>=129 | 单Kernel，grid(B,ceil(M/256)) | _expand_causal_seqlens_kernel<BB,256> | BB归约，256query lane；M>256分多chunk | 同上 |

### 隐藏性能 Guard

| Guard | Host/Tiling条件 | Device/资源原因 | 影响Route | 不满足时去向 | 源码符号 |
|---|---|---|---|---|---|
| 一维连续与INT32 | ndim/stride/dtype/device逐项检查 | Device用线性指针且强制INT32长度 | 全部 | 抛异常 | expand_causal_seqlens |
| T和M的一致性 | 仅检查非负和T>0=>M>0，未检查设备长度 | prefix与grid需要T=sum(q)、M覆盖q | R-002..005 | 未提供修复fallback，可截断/漏写/未写输出 | 同函数及kernel mask |
| 长度/索引范围 | 未guard非负q或INT32不溢出 | prefix、causal_start及query_offsets为INT32，mask不检查output_offsets>=0 | R-002..005 | 合同外无安全保证 | tl.sum/.to(tl.int32)/mask |
| prefix tile资源 | BB仅随B取二次幂，无UB/cap裁剪 | 每program加载并归约BB逻辑lane | R-002..005 | 编译/运行准入由工具链决定，无自有fallback | block_batch |
| query tile封顶 | Q=max(32,min(256,next_power_of_2(M))) | 控制query向量逻辑宽度，M大时多program | R-002..005 | 固定分块，不随物理UB自适应 | block_query/grid |
| 输出别名 | 文档禁止，Host未检查 | 同时store两个输出并读长度 | 全部 | 合同外可能产生竞争或破坏输入 | 输出校验与tl.store |

### POD/ABI

无自定义序列化POD、sizeof/offsetof合同或固定C++布局。下表逐字段给出真实JIT调用参数；指针/标量的最终机器ABI和寄存器分配属于Triton编译器边界。

| 结构 | 字段 | 类型/位宽 | ABI布局 | 单位 | Host/launcher producer | Device consumer | 边界 |
|---|---|---|---|---|---|---|---|
| JIT参数 | cache_seqlens_ptr | INT32元素指针，机器指针ABI外部 | 无算子POD | 元素 | cache_seqlens | load(ptr+r) | 连续[B]，r来自grid |
| JIT参数 | query_lens_ptr | INT32元素指针 | 同上 | 元素 | query_lens | prefix load及load(ptr+r) | 仅prefix lane<r加载 |
| JIT参数 | seqlens_expanded_ptr | INT32元素指针 | 同上 | 元素 | 分配/传入seqlens_out | store(ptr+p[r]+j) | [T]，输入不重叠 |
| JIT参数 | token_to_batch_ptr | INT64元素指针 | 同上 | 元素 | 分配/传入token_to_batch_out | store请求号r | store转换到INT64不拓宽此前prefix计算 |
| JIT参数 | total_q | Python int传入，标量机器位宽由JIT推导 | 同上 | token | total_q | output_offsets<T | Host非负，设备不核验sum |
| constexpr | BLOCK_BATCH | tl.constexpr整数 | 编译时，无Device POD偏移 | lane | next_power_of_2(B) | arange和sum向量宽度 | 仅非空分支生成 |
| constexpr | BLOCK_QUERY | tl.constexpr整数 | 同上 | token/lane | clamp(next_power_of_2(M),32,256) | chunk*Q+arange(Q) | 32/64/128/256 |

### Route 源码闭包

| Route | Key/selector | Host/Tiling producer | POD/参数 | Kernel entry/router节点 | Kernel body/直接依赖 | 构建接线 |
|---|---|---|---|---|---|---|
| R-001 | B==0或T==0 | impl::expand_causal_seqlens:68–113 | Torch输出对象，无POD | 无Device节点 | 两输出准备后return | stage_runtime复制Python树 |
| R-002 | Q32 | 同函数:115–126 | 7个逐项参数，BB/32 | _expand_causal_seqlens_kernel | impl:20–49完整body | setup.py→stage_runtime；JIT运行时编译 |
| R-003 | Q64 | 同上 | 同字段，BB/64 | 同一entry | 同body，64query lane | 同上 |
| R-004 | Q128 | 同上 | 同字段，BB/128 | 同一entry | 同body，128query lane | 同上 |
| R-005 | Q256 | 同上 | 同字段，BB/256 | 同一entry | 同body，256query lane/多chunk | 同上 |

## Kernel 实现

### 公共执行流程

launcher不设置num_warps、num_stages、numBlocks、threadsPerBlock或dynamic UB。不得从grid=(B,P)推导每program占一个AIV核或线程数。Triton lowerings、tl.sum的具体归约树、load/store物理事务及stream调度属于外部编译/框架primitive边界；自有计算闭包中没有其它算法节点。

### Route R-001：纯Host空域

#### 适用条件

##### 选择证据

输入和输出检查完成后`if batch_size == 0 or total_q == 0`直接return。T>0且M==0早于此分支抛异常；不能借B==0绕过此前的检查。

#### Device 数据流

##### 函数级调用链

`expand_causal_seqlens -> 两输出分配/检查 -> return tuple`，无Device节点、entry或跨节点边。

##### 源码等价伪码

```text
prepare/check seqlens_out INT32[T]
prepare/check token_to_batch_out INT64[T]
if B==0 or T==0: return both objects without writing them
```

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 地址/extent | producer/consumer | owner/lifetime | 复用 |
|---|---|---|---|---|
| seqlens_out | Torch对象，4T有效payload字节 | 分配或调用方/直接返回 | 调用方持有 | 不读不写，原值不被清零 |
| token_to_batch_out | Torch对象，8T有效payload字节 | 同上 | 同上 | 同上 |

##### 分层内存布局

N/A：无Kernel、UB、TQue/TBuf或dynamic UB；仅已有/新分配GM对象。

##### 字节账与复用顺序

输出有效容量12T；Device流量0、workspace0。正常空合同T=0；空B/非零T是未guard的调用方错误，不能保证任何输出值。

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer/consumer | 保护对象 | 精度/尾块 |
|---|---|---|---|---|
| Host返回 | 无Device launch/同步 | 对象准备/返回 | 输出对象身份 | 未发生数值变换或有效值初始化 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号 | 实现事实 |
|---|---|---|---|
| Host | impl | expand_causal_seqlens:86–113 | 分配/校验后空域返回 |
| Entry | impl | 同函数空分支 | 不调用kernel |
| Device | impl | 无 | 不虚构CopyIn/Compute/CopyOut |

### Route R-002：query tile 32

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | impl | expand_causal_seqlens | 检查通过且B>0,T>0,1<=M<=32 | Q=32,BB=next_power_of_2(B),P=ceil(M/32) |
| Entry | impl | _expand_causal_seqlens_kernel<BB,32> | grid(B,P)，无其它router | program(r,c) |

#### Device 数据流

##### 函数级调用链

```text
expand_causal_seqlens -> JIT grid(B,P)
 -> _expand_causal_seqlens_kernel<BB,32>
 -> prefix masked load -> INT32 sum -> current q/S load
 -> INT32 causal_start/query offsets -> two masked stores
```

##### 源码等价伪码

```text
r=program_id(0); c=program_id(1)
i=arange(BB)
prefix=sum(int32(load(query_lens+i, mask=i<r, other=0)))
qr=int32(load(query_lens+r)); sr=int32(load(cache_seqlens+r))
a=max(sr-qr+1,0)
j=int32(c*32+arange(32)); o=prefix+j
mask=(j<qr) and (o<T)
store(seqlens+o, a+j, mask)
store(token_to_batch+o, r, mask)
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/对象 | offset/地址公式 | extent/容量 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM query_lens | r及i<r | 4B字节，其中每program读取4r+4 | 连续INT32 | 调用方 | prefix归约/qr | 调用方，直到完成 | 不复制或改写 |
| GM cache_seqlens | r | 4B字节，每program读取4 | 连续INT32 | 调用方 | causal_start | 同上 | 线性索引 |
| GM seqlens | p[r]+j，j=c*32+lane | 4T容量，当前写4v | 连续INT32 | 当前program | 后续调用方消费者 | Torch/调用方 | 有效lane唯一写 |
| GM token_to_batch | 同输出offset | 8T容量，当前写8v | 连续INT64 | 当前program | 同上 | 同上 | 请求号在store处转换 |
| 编译逻辑prefix值 | BB个lane | INT32逻辑向量4BB，mask后无效lane0 | Triton SSA | load/cast | tl.sum | 单program表达式生命周期 | 未声明共享内存或Queue |
| 编译逻辑query值 | 32个lane | offsets与seqlens各INT32[32]，mask逻辑[32] | Triton SSA | arange/INT32算式 | store | 单program | 不是物理UB申请合同 |

##### 分层内存布局

N/A：源码没有AIV InitBuffer、TQue/TBuf或显式SIMT dynamic UB。实际层级是GM输入→Triton SSA prefix/归约/向量→GM双输出；不能把4BB或4*32直接画成已分配UB区。

##### 字节账与复用顺序

每program有效输入4r+8字节；v=max(0,min(32,q[r]-c*32))，有效输出12v字节；全launch为`ceil(M/32)*(2B(B-1)+8B)+12T`逻辑字节，无自有GM scratch/workspace。输出只在mask有效时写，不先读取旧值；prefix向量、query offsets和mask的寄存器/UB别名与峰值固定仓不可见，不以相加逻辑向量尺寸充当物理资源证明。没有Host UB上限或选小Q重试。

| 复用对象 | 写入者 | 消费点 | 下一次覆盖 | 同步依据 | 安全条件 |
|---|---|---|---|---|---|
| 两个输出 | 本launch的各program | 后续算子 | 下次调用可复用 | 当前stream由框架安排；跨流由调用方显式排序 | 每次T/dtype/device不变且不重叠；前次消费者结束后才覆盖 |
| prefix/query SSA | load/算术 | sum/store | 编译器内部 | 数据依赖 | 无可供调用方操作的手工buffer生命周期 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| prefix | masked tl.load(other=0),tl.sum(axis=0) | q[i],i<r | p[r]计算 | 当前program输入 | 强制INT32；i>=r为0，无全局cumsum |
| causal | INT32 load/cast,maximum | S[r],q[r] | a+j | 长度算式 | 无FP32转换，溢出未guard；max在减加之后 |
| query chunk | arange(32)及int32 cast | c/lane | output_offsets/mask | 输出有效域 | j<q[r]且o<T；没有o>=0检查 |
| 双输出 | 两个tl.store，共同mask | a+j及请求号r | GM后续消费者 | 各唯一packed位置 | INT32长度、INT64请求号；无atomics/barrier |
| 异步返回 | 无显式event/wait | launch | 调用方 | 所有tensor生命周期 | 返回对象不等于Device已完成 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/实例 | 实现事实 |
|---|---|---|---|
| Host producer | impl | expand_causal_seqlens:115–126 | Q=32，BB二次幂、grid(B,ceil(M/32))及7项实参 |
| Entry/router | impl | _expand_causal_seqlens_kernel<BB,32>:11–21 | 二维program_id，无额外分发 |
| Device body | impl | 同函数:26–49 | INT32 prefix/两长度、query mask与双store |

### Route R-003：query tile 64

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | impl | expand_causal_seqlens | 检查通过且B>0,T>0,33<=M<=64 | Q=64,BB=next_power_of_2(B),P=ceil(M/64) |
| Entry | impl | _expand_causal_seqlens_kernel<BB,64> | grid(B,P)，无其它router | program(r,c) |

#### Device 数据流

##### 函数级调用链

```text
expand_causal_seqlens -> JIT grid(B,P)
 -> _expand_causal_seqlens_kernel<BB,64>
 -> prefix masked load -> INT32 sum -> current q/S load
 -> INT32 causal_start/query offsets -> two masked stores
```

##### 源码等价伪码

```text
r=program_id(0); c=program_id(1)
i=arange(BB)
prefix=sum(int32(load(query_lens+i, mask=i<r, other=0)))
qr=int32(load(query_lens+r)); sr=int32(load(cache_seqlens+r))
a=max(sr-qr+1,0)
j=int32(c*64+arange(64)); o=prefix+j
mask=(j<qr) and (o<T)
store(seqlens+o, a+j, mask)
store(token_to_batch+o, r, mask)
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/对象 | offset/地址公式 | extent/容量 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM query_lens | r及i<r | 4B字节，其中每program读取4r+4 | 连续INT32 | 调用方 | prefix归约/qr | 调用方，直到完成 | 不复制或改写 |
| GM cache_seqlens | r | 4B字节，每program读取4 | 连续INT32 | 调用方 | causal_start | 同上 | 线性索引 |
| GM seqlens | p[r]+j，j=c*64+lane | 4T容量，当前写4v | 连续INT32 | 当前program | 后续调用方消费者 | Torch/调用方 | 有效lane唯一写 |
| GM token_to_batch | 同输出offset | 8T容量，当前写8v | 连续INT64 | 当前program | 同上 | 同上 | 请求号在store处转换 |
| 编译逻辑prefix值 | BB个lane | INT32逻辑向量4BB，mask后无效lane0 | Triton SSA | load/cast | tl.sum | 单program表达式生命周期 | 未声明共享内存或Queue |
| 编译逻辑query值 | 64个lane | offsets与seqlens各INT32[64]，mask逻辑[64] | Triton SSA | arange/INT32算式 | store | 单program | 不是物理UB申请合同 |

##### 分层内存布局

N/A：源码没有AIV InitBuffer、TQue/TBuf或显式SIMT dynamic UB。实际层级是GM输入→Triton SSA prefix/归约/向量→GM双输出；不能把4BB或4*64直接画成已分配UB区。

##### 字节账与复用顺序

每program有效输入4r+8字节；v=max(0,min(64,q[r]-c*64))，有效输出12v字节；全launch为`ceil(M/64)*(2B(B-1)+8B)+12T`逻辑字节，无自有GM scratch/workspace。输出只在mask有效时写，不先读取旧值；prefix向量、query offsets和mask的寄存器/UB别名与峰值固定仓不可见，不以相加逻辑向量尺寸充当物理资源证明。没有Host UB上限或选小Q重试。

| 复用对象 | 写入者 | 消费点 | 下一次覆盖 | 同步依据 | 安全条件 |
|---|---|---|---|---|---|
| 两个输出 | 本launch的各program | 后续算子 | 下次调用可复用 | 当前stream由框架安排；跨流由调用方显式排序 | 每次T/dtype/device不变且不重叠；前次消费者结束后才覆盖 |
| prefix/query SSA | load/算术 | sum/store | 编译器内部 | 数据依赖 | 无可供调用方操作的手工buffer生命周期 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| prefix | masked tl.load(other=0),tl.sum(axis=0) | q[i],i<r | p[r]计算 | 当前program输入 | 强制INT32；i>=r为0，无全局cumsum |
| causal | INT32 load/cast,maximum | S[r],q[r] | a+j | 长度算式 | 无FP32转换，溢出未guard；max在减加之后 |
| query chunk | arange(64)及int32 cast | c/lane | output_offsets/mask | 输出有效域 | j<q[r]且o<T；没有o>=0检查 |
| 双输出 | 两个tl.store，共同mask | a+j及请求号r | GM后续消费者 | 各唯一packed位置 | INT32长度、INT64请求号；无atomics/barrier |
| 异步返回 | 无显式event/wait | launch | 调用方 | 所有tensor生命周期 | 返回对象不等于Device已完成 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/实例 | 实现事实 |
|---|---|---|---|
| Host producer | impl | expand_causal_seqlens:115–126 | Q=64，BB二次幂、grid(B,ceil(M/64))及7项实参 |
| Entry/router | impl | _expand_causal_seqlens_kernel<BB,64>:11–21 | 二维program_id，无额外分发 |
| Device body | impl | 同函数:26–49 | INT32 prefix/两长度、query mask与双store |

### Route R-004：query tile 128

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | impl | expand_causal_seqlens | 检查通过且B>0,T>0,65<=M<=128 | Q=128,BB=next_power_of_2(B),P=ceil(M/128) |
| Entry | impl | _expand_causal_seqlens_kernel<BB,128> | grid(B,P)，无其它router | program(r,c) |

#### Device 数据流

##### 函数级调用链

```text
expand_causal_seqlens -> JIT grid(B,P)
 -> _expand_causal_seqlens_kernel<BB,128>
 -> prefix masked load -> INT32 sum -> current q/S load
 -> INT32 causal_start/query offsets -> two masked stores
```

##### 源码等价伪码

```text
r=program_id(0); c=program_id(1)
i=arange(BB)
prefix=sum(int32(load(query_lens+i, mask=i<r, other=0)))
qr=int32(load(query_lens+r)); sr=int32(load(cache_seqlens+r))
a=max(sr-qr+1,0)
j=int32(c*128+arange(128)); o=prefix+j
mask=(j<qr) and (o<T)
store(seqlens+o, a+j, mask)
store(token_to_batch+o, r, mask)
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/对象 | offset/地址公式 | extent/容量 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM query_lens | r及i<r | 4B字节，其中每program读取4r+4 | 连续INT32 | 调用方 | prefix归约/qr | 调用方，直到完成 | 不复制或改写 |
| GM cache_seqlens | r | 4B字节，每program读取4 | 连续INT32 | 调用方 | causal_start | 同上 | 线性索引 |
| GM seqlens | p[r]+j，j=c*128+lane | 4T容量，当前写4v | 连续INT32 | 当前program | 后续调用方消费者 | Torch/调用方 | 有效lane唯一写 |
| GM token_to_batch | 同输出offset | 8T容量，当前写8v | 连续INT64 | 当前program | 同上 | 同上 | 请求号在store处转换 |
| 编译逻辑prefix值 | BB个lane | INT32逻辑向量4BB，mask后无效lane0 | Triton SSA | load/cast | tl.sum | 单program表达式生命周期 | 未声明共享内存或Queue |
| 编译逻辑query值 | 128个lane | offsets与seqlens各INT32[128]，mask逻辑[128] | Triton SSA | arange/INT32算式 | store | 单program | 不是物理UB申请合同 |

##### 分层内存布局

N/A：源码没有AIV InitBuffer、TQue/TBuf或显式SIMT dynamic UB。实际层级是GM输入→Triton SSA prefix/归约/向量→GM双输出；不能把4BB或4*128直接画成已分配UB区。

##### 字节账与复用顺序

每program有效输入4r+8字节；v=max(0,min(128,q[r]-c*128))，有效输出12v字节；全launch为`ceil(M/128)*(2B(B-1)+8B)+12T`逻辑字节，无自有GM scratch/workspace。输出只在mask有效时写，不先读取旧值；prefix向量、query offsets和mask的寄存器/UB别名与峰值固定仓不可见，不以相加逻辑向量尺寸充当物理资源证明。没有Host UB上限或选小Q重试。

| 复用对象 | 写入者 | 消费点 | 下一次覆盖 | 同步依据 | 安全条件 |
|---|---|---|---|---|---|
| 两个输出 | 本launch的各program | 后续算子 | 下次调用可复用 | 当前stream由框架安排；跨流由调用方显式排序 | 每次T/dtype/device不变且不重叠；前次消费者结束后才覆盖 |
| prefix/query SSA | load/算术 | sum/store | 编译器内部 | 数据依赖 | 无可供调用方操作的手工buffer生命周期 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| prefix | masked tl.load(other=0),tl.sum(axis=0) | q[i],i<r | p[r]计算 | 当前program输入 | 强制INT32；i>=r为0，无全局cumsum |
| causal | INT32 load/cast,maximum | S[r],q[r] | a+j | 长度算式 | 无FP32转换，溢出未guard；max在减加之后 |
| query chunk | arange(128)及int32 cast | c/lane | output_offsets/mask | 输出有效域 | j<q[r]且o<T；没有o>=0检查 |
| 双输出 | 两个tl.store，共同mask | a+j及请求号r | GM后续消费者 | 各唯一packed位置 | INT32长度、INT64请求号；无atomics/barrier |
| 异步返回 | 无显式event/wait | launch | 调用方 | 所有tensor生命周期 | 返回对象不等于Device已完成 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/实例 | 实现事实 |
|---|---|---|---|
| Host producer | impl | expand_causal_seqlens:115–126 | Q=128，BB二次幂、grid(B,ceil(M/128))及7项实参 |
| Entry/router | impl | _expand_causal_seqlens_kernel<BB,128>:11–21 | 二维program_id，无额外分发 |
| Device body | impl | 同函数:26–49 | INT32 prefix/两长度、query mask与双store |

### Route R-005：query tile 256

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | impl | expand_causal_seqlens | 检查通过且B>0,T>0,M>=129 | Q=256,BB=next_power_of_2(B),P=ceil(M/256) |
| Entry | impl | _expand_causal_seqlens_kernel<BB,256> | grid(B,P)，无其它router | program(r,c) |

#### Device 数据流

##### 函数级调用链

```text
expand_causal_seqlens -> JIT grid(B,P)
 -> _expand_causal_seqlens_kernel<BB,256>
 -> prefix masked load -> INT32 sum -> current q/S load
 -> INT32 causal_start/query offsets -> two masked stores
```

##### 源码等价伪码

```text
r=program_id(0); c=program_id(1)
i=arange(BB)
prefix=sum(int32(load(query_lens+i, mask=i<r, other=0)))
qr=int32(load(query_lens+r)); sr=int32(load(cache_seqlens+r))
a=max(sr-qr+1,0)
j=int32(c*256+arange(256)); o=prefix+j
mask=(j<qr) and (o<T)
store(seqlens+o, a+j, mask)
store(token_to_batch+o, r, mask)
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/对象 | offset/地址公式 | extent/容量 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM query_lens | r及i<r | 4B字节，其中每program读取4r+4 | 连续INT32 | 调用方 | prefix归约/qr | 调用方，直到完成 | 不复制或改写 |
| GM cache_seqlens | r | 4B字节，每program读取4 | 连续INT32 | 调用方 | causal_start | 同上 | 线性索引 |
| GM seqlens | p[r]+j，j=c*256+lane | 4T容量，当前写4v | 连续INT32 | 当前program | 后续调用方消费者 | Torch/调用方 | 有效lane唯一写 |
| GM token_to_batch | 同输出offset | 8T容量，当前写8v | 连续INT64 | 当前program | 同上 | 同上 | 请求号在store处转换 |
| 编译逻辑prefix值 | BB个lane | INT32逻辑向量4BB，mask后无效lane0 | Triton SSA | load/cast | tl.sum | 单program表达式生命周期 | 未声明共享内存或Queue |
| 编译逻辑query值 | 256个lane | offsets与seqlens各INT32[256]，mask逻辑[256] | Triton SSA | arange/INT32算式 | store | 单program | 不是物理UB申请合同 |

##### 分层内存布局

N/A：源码没有AIV InitBuffer、TQue/TBuf或显式SIMT dynamic UB。实际层级是GM输入→Triton SSA prefix/归约/向量→GM双输出；不能把4BB或4*256直接画成已分配UB区。

##### 字节账与复用顺序

每program有效输入4r+8字节；v=max(0,min(256,q[r]-c*256))，有效输出12v字节；全launch为`ceil(M/256)*(2B(B-1)+8B)+12T`逻辑字节，无自有GM scratch/workspace。输出只在mask有效时写，不先读取旧值；prefix向量、query offsets和mask的寄存器/UB别名与峰值固定仓不可见，不以相加逻辑向量尺寸充当物理资源证明。没有Host UB上限或选小Q重试。

| 复用对象 | 写入者 | 消费点 | 下一次覆盖 | 同步依据 | 安全条件 |
|---|---|---|---|---|---|
| 两个输出 | 本launch的各program | 后续算子 | 下次调用可复用 | 当前stream由框架安排；跨流由调用方显式排序 | 每次T/dtype/device不变且不重叠；前次消费者结束后才覆盖 |
| prefix/query SSA | load/算术 | sum/store | 编译器内部 | 数据依赖 | 无可供调用方操作的手工buffer生命周期 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| prefix | masked tl.load(other=0),tl.sum(axis=0) | q[i],i<r | p[r]计算 | 当前program输入 | 强制INT32；i>=r为0，无全局cumsum |
| causal | INT32 load/cast,maximum | S[r],q[r] | a+j | 长度算式 | 无FP32转换，溢出未guard；max在减加之后 |
| query chunk | arange(256)及int32 cast | c/lane | output_offsets/mask | 输出有效域 | j<q[r]且o<T；没有o>=0检查 |
| 双输出 | 两个tl.store，共同mask | a+j及请求号r | GM后续消费者 | 各唯一packed位置 | INT32长度、INT64请求号；无atomics/barrier |
| 异步返回 | 无显式event/wait | launch | 调用方 | 所有tensor生命周期 | 返回对象不等于Device已完成 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/实例 | 实现事实 |
|---|---|---|---|
| Host producer | impl | expand_causal_seqlens:115–126 | Q=256，BB二次幂、grid(B,ceil(M/256))及7项实参 |
| Entry/router | impl | _expand_causal_seqlens_kernel<BB,256>:11–21 | 二维program_id，无额外分发 |
| Device body | impl | 同函数:26–49 | INT32 prefix/两长度、query mask与双store |

## 算子特定优化

### Trick T-001：每个请求块局部归约prefix，省去全局中间prefix

#### 触发与源码依据

- 适用Route：R-002..005。
- 触发条件：有效B/T/M合同；BB为B的二次幂上界，program的请求号r<B。
- Golden 来源：[prefix读取与归约](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/expand_causal_seqlens.py#L26-L32)。

**官方源码（固定Commit连续逐字摘录）**：

```python
    request_offsets = tl.arange(0, BLOCK_BATCH)
    prior_query_lens = tl.load(
        query_lens_ptr + request_offsets,
        mask=request_offsets < request_idx,
        other=0,
    ).to(tl.int32)
    request_output_start = tl.sum(prior_query_lens, axis=0)
```

#### 机制与设计原因

只加载query_lens中i<r的元素，other=0补齐参与tl.sum的BB宽度向量，直接得到该请求的packed起点；不物化cumsum数组，也不启动额外cumsum/repeat_interleave节点。每query chunk都会重新计算，代价是prefix读取按P重复、总量随B平方增长。源码注释的小batch动机不能代替真机性能比较。

#### 迁移边界

- 适用：已有Host总token数、短请求长度向量的packed metadata生成。
- 前提：非负q、INT32范围、BB资源可编译/运行、调用前输入已就绪。
- 失效：大B或过大M可能增大归约/重复读；源中没有切换到全局cumsum的fallback。其它实现须另行验证。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

固定仓未提供可验证反例；不能将“无中间prefix”推导为任意B下更快，或省略q非负和不溢出的必要条件。

### Trick T-002：双输出共用packed寻址与mask，支持预分配地址复用

#### 触发与源码依据

- 适用Route：R-002..005。
- 触发条件：两个输出shape/dtype/device及不重叠合同满足，o=p[r]+j。
- Golden 来源：[共同mask与双store](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/expand_causal_seqlens.py#L41-L49)。

**官方源码（固定Commit连续逐字摘录）**：

```python
    output_offsets = request_output_start + query_offsets
    mask = (query_offsets < query_len) & (output_offsets < total_q)

    tl.store(
        seqlens_expanded_ptr + output_offsets,
        causal_start + query_offsets,
        mask=mask,
    )
    tl.store(token_to_batch_ptr + output_offsets, request_idx, mask=mask)
```

#### 机制与设计原因

同一Kernel同时生成INT32长度和INT64请求号，共用prefix及有效lane判定，无第二个映射生成Kernel或输出中间展开。launcher在调用方提供合法缓冲时直接使用其指针；这使消费者可保留地址，但算子本身不管理graph捕获、重放、跨流同步或Host/device镜像。o<T是额外上界保护，不等于对sum(q)或负prefix的完整验证。

#### 迁移边界

- 适用：DSA消费者同时需要可见长度与请求ID，预分配缓冲需要保持地址。
- 前提：复用时T、dtype/device和连续性不变；旧消费者完成后才允许覆盖；输出互不重叠。
- 失效：错误T/M可能截断或漏写；T过大尾部未写，负q或溢出可能绕过下界保护。无自动修复。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

固定仓未提供可验证反例；不得将两个输出指向同一storage，或将跨stream对象地址稳定当作读写已经排序。

## 模板与实现对比

| 维度 | R-001 | R-002/003/004/005 | 选择依据 |
|---|---|---|---|
| 命中 | B==0或T==0 | Q32/64/128/256的互斥M区间 | 空分支优先于tile计算 |
| 模板/dtype | 无Device | 共同INT32输入，INT32/INT64输出；BB与Q为constexpr | 不按输入dtype动态改数学 |
| 循环/分核 | 0节点 | grid(B,ceil(M/Q))，每program一个请求chunk | M>256分多chunk，不循环核数轮转 |
| Queue/TBuf/dynamic UB | 无 | 无显式申请，物理资源由编译器决定 | 不沿用AscendC的手工队列模型 |
| 内存/复用 | 仅两输出对象 | 同两输出，无GM scratch；prefix在program内 | 预分配保持对象身份 |
| 搬运/API | 无 | masked load/sum/maximum/store | 两输出一次融合 |
| 同步/精度/tail | 无运算 | INT32运算、共同尾mask，无跨program同步 | 依赖非重叠区间证明 |
| fallback | 不launch | 无Torch fallback或UB重试 | 原异常向调用方传播 |

## 平台差异

| 项目 | A2 | A3 | Ascend950 |
|---|---|---|---|
| 公开支持 | arch22支持，2201包含910b | arch22支持，2201包含910_93 | arch35文档已验证声明；不是本次执行结果 |
| Host/Launcher | 共享Python实现 | 同A2 | 同一实现 |
| Kernel/资源 | 同一Triton body；物理lowering外部 | 同A2，不推断物理配置相同 | 无源内平台分支；不推断与arch22相同UB/寄存器分配 |

## 限制与失败边界

- draft原因是设备长度一致性、INT32运算和不重叠均依赖调用方，以及实际工具链资源/运行结果未验证；源码闭包不等于这些条件已被检查。
- Host不验证T=sum(q)或M覆盖q。T过小按上界mask截断，T过大可能留下未写尾部；M过小可能使launch覆盖不足。B=0/T>0直接返回未写输出的特殊边界仍存在。
- Device只有j<q和o<T两个上界条件，不防负prefix或INT32溢出；INT64请求号输出不修复先前INT32索引计算。
- 输入与输出仅按一维连续合同寻址。没有重叠检测、设备类型guard、显式npu设备切换、跨流event或失败回退。
- Python文件被打包不证明任何安装的subset wheel可成功导入；包初始化仍需要其原生库及vendor完整。源码读取不能代表编译、导入或真机成功。
- 未设置verified；CANN9.1.0配置不冻结完整Triton、PyTorch和torch_npu ABI。

## 源码索引

### 链路索引

| 链路阶段 | 文件 | 关键符号 | 支撑内容 |
|---|---|---|---|
| 入口约束 | [docs/api/zh/operators/indexer/expand_causal_seqlens.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/indexer/expand_causal_seqlens.md) | 芯片支持/参数表 | 平台与长度/别名合同 |
| Launcher/Device | [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/expand_causal_seqlens.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/expand_causal_seqlens.py) | expand_causal_seqlens/_expand_causal_seqlens_kernel | 完整分发、7项参数、prefix与双store |
| 公开上下文 | [python/sgl_kernel_npu/sgl_kernel_npu/operators/indexer/expand_causal_seqlens.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/indexer/expand_causal_seqlens.py) | _triton_impl/expand_causal_seqlens | auto/triton延迟转发；独立reference无fallback |
| 包模块 | [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/__init__.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/__init__.py) | 模块初始化 | Triton/indexer模块无额外算法调用 |
| 包模块 | [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/__init__.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/__init__.py) | 模块初始化 | Triton/indexer模块无额外算法调用 |
| 包初始化 | [python/sgl_kernel_npu/sgl_kernel_npu/__init__.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py) | _load_sgl_kernel_npu | 导入native库的前置条件 |
| Python打包 | [python/sgl_kernel_npu/build_tools/torch_wheel.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/build_tools/torch_wheel.py) | stage_runtime/setup_refactor | 复制完整Python源树及包发现 |
| 打包入口 | [setup.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/setup.py) | main | wheel路径进入build_torch/build_wheel |
| 平台/打包 | [python/sgl_kernel_npu/README.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md) | REFACTOR builds | all Python sources与架构说明 |
| 平台映射 | [csrc/cmake/architectures.json](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json) | 2201/3510 | 910b/910_93/950对应 |
| 版本配置 | [.github/workflows/pr-test-kernels.yml](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernels.yml) | cann_version:9.1.0 | 固定CI配置证据，非测试结果 |

正文中impl指上表的完整Triton实现文件；wrapper仅提供公开分发上下文，不把torch_native当作本Direct图节点。

### 实现复用检查

| 检查项 | 可复用事实 | 不得改变的约束 | 源码符号 |
|---|---|---|---|
| ABI/POD | 4tensor+T+2constexpr，无自定义POD | dtype、元素单位与BB/Q生成规则 | launch参数/Kernel签名 |
| 调用顺序 | 检查→分配/检查输出→空分支→单Kernel | 空分支仍在输出准备之后 | expand_causal_seqlens |
| workspace/内存 | 无自有scratch，新输出payload12T | 预分配长度与device/dtype/不重叠 | 两个empty及输出检查 |
| 同步 | 无跨program数据依赖，无显式barrier | 调用方保证输入就绪与输出复用顺序 | program_id/共同mask |
| 精度/尾块 | INT32 prefix/因果值，双store共同mask | 非负与不溢出，T和M一致性 | tl.sum/maximum/to(int32) |
| 失败边界 | Python异常/JIT失败原样传播 | 无自动torch_native/小tile重试 | Direct launcher |
