---
type: Operator
title: "KpoolWriteTailAndMaybeCompress 950 Direct Invoke 算子知识"
description: "闭合全N draft tail写后条件压缩的六effective路线与FP32在线softmax，记录score存储舍入、GM重读、候选cache及原地冲突边界。"
tags: [task.implementation, task.lookup, topic.memory, topic.precision, topic.programming_model]
status: draft
sources:
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/mem_cache/kpool_write_tail_and_maybe_compress.md
    role: primary
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_write_tail_and_maybe_compress.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/mem_cache/kpool_write_tail_and_maybe_compress.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/__init__.py
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/__init__.py
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/setup.py
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/build_tools/torch_wheel.py
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernels.yml
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernel-group.yml
    role: supporting
created_at: "2026-11-09T10:27:40Z"
updated_at: "2026-11-09T10:27:40Z"
platforms: ["950"]
cann_versions: ["9.1.0"]
---

# KpoolWriteTailAndMaybeCompress 950 Direct Invoke 算子知识

## 算子速览

`sgl_kernel_npu.implementation.triton.mem_cache.kpool_write_tail_and_maybe_compress.kpool_write_tail_and_maybe_compress` 对有效batch先写全N条draft的tail，再依据effective_n计算完成pool数并从tail重读、逐通道online softmax汇聚后BF16写cache。只cache/tailK/tailScore可变，None返回；没有旋转、FP8、scale。完整Host及6个有效N/skip/压缩执行类闭合，无dot/Cube，VV。

draft保留设备值域/整数窄化、GMstore后重读、历史/并发别名与resource边界；复用全文读的[共同Kpool API](../../../../apis/sgl_kernel_npu/sgl_kpool_tail_cache.md)，不以本源码替代其它入口。

## 接口与语义

### 计算语义

N=num_draft_tokens，K=APE行数，B=key.rows/N，tail容量T=K+N。batch有效当out_cache_loc[b*N]!=0；有效时所有d∈[0,N)将key/score[bN+d]写tail[req,(write_start+d)%T]，effective0也照写。e=N若无effective，否则e=clamp(int32(effective[b]),0,N)。C_b=clamp((ws+e)//K-ws//K,0,ceil(N/K))，只有前C_b个候选pool压缩。第p个pool起点tail_logical_start+pK，读取K行tailscore+APE的逐通道softmax，加权tailK、BF16写write_loc[b,p]指定cache行。位置参数值域及历史窗口由调用方保证。

score输入与tail_score dtype可不同，storetail会转换，随后的pool输入是写回后的tailstorage精度，不是原始FP32score直接混合。代码先写tail再压缩，是不可省略的数学/内存边。

### 输入、输出与属性

| 项 | Host合同 |
|---|---|
| cache | BF16、`numel % 128 == 0`、同device/contiguous，view[-1,128]原地 |
| key/score | [B*N,128]，keyBF16、scoreFP16/BF16/FP32，内部contiguous |
| tail | [R,K+N,128]且score同shape，tailKBF16、tailScore三浮点；必须已contiguous，不复制state |
| APE | FP32[K,128]，K>0 |
| metadata | reqint64、ws/tailstartint32或int64、至少B项；outlocint32或int64至少BN项；内部contiguous |
| write_loc | int64[B,ceil(N/K)]且连续，不能copy更新state时丢语义（此张量实际只读） |
| effective | None或int32/int64至少B，内部contiguous，值先narrow后clamp；只压缩门控 |
| N/grid | N>0且整除keyrows；num_programs显式>0只非空检查，默认min(B,cores) |
| 返回 | None；所有输入计划只读，3state原地写；req/loc值域、不冲突和历史有效由调用方保证 |

### 入口与版本

Direct位置参数cache,key,score,tail_k,tail_score,ape,req_pool_indices,write_start,tail_logical_start,write_loc,out_cache_loc,num_draft_tokens,effective_n_per_batch=None，keyword-only num_programs=None。auto/triton转发，reference独立不补自有Kernel。固定SGLcommit `dda6d36b0cdb4081e102d14c0a2fb276fc416e69`；CANN9.1.0为README/CI配置非本次运行，完整Tritonbinary未固定。

## Host/Launcher 执行流程

### 参数校验与前处理

先N>0、payload/APE/cache dtype/shape/128与cache整行数；total_rows0此时返回，在K正/T=K+N/metadata/device/contiguous/grid检查之前。非空assertrows%N0、K正、T==K+N、metadata形状/dtype、write_locshape/末stride1、outloc/effective长度；只读key/score/APE/req/ws/tailstart/outloc/effective可contiguous，再allsameDevice/contiguous（包括cache/tails/write_loc）检查。

默认grid=min(B,Pcores)，显式>0后仅min(B,explicit)，不额外capcore。effectiveNone分配emptyint32[1]4B占位、HASfalse不读取；cacheview后launch。没有Host读设备值/全局同步，assert可关闭。

### 参数、Workspace 与生命周期

无新输出/统计GM或请求方workspace/POD/ACLNN；可选onlyreadcopy每项临时numel*d，额外读/写各同字节；effective占位4B逻辑非allocator物理对齐证明。三state保持原存储，helper仅默认grid分支调用、无参currentdevicecache，无deviceguard；allsameDevice不等显式NPUassert。copy→Kernel、原地异步完成和回收归框架/caller，没有显式stream/event/wait。

### 启动图与失败传播

import→earlychecks→rows0return或完整checks/copy/grid→effective占位→cacheview→单JITKernel→None。无外部Torch核心数学/fallback；异常传播，无回滚，package原生库导入仅前提。

## Route 与参数设计

### 分核与资源计算

grid n，program p轮转batch b=p+j*n<B。首outlocflag筛整个batch；有效才读req/ws，全部Ntailwrite后才读e并计算C_b、读取tailstart。MAX=ceil(N/K)，K/N/MAX均静态循环上限，runtime p<C_b筛候选。128通道固定BLOCK_D128，无实际通道尾。在线carry m/acc/den不保存完整K行矩阵，编译展开/运行量仍随N/K/MAX增长。

### Route 选择

HAS_EFFECTIVE_N两编译态×每batch skip/allNtailonly/allNtail+compress三类，共6；C_b可0..MAX，输入e负/超N先int32再clamp影响C_b。effective0属于tailonly，不是skip。空totalrowsHost单独列，元信息检查顺序真实保留。

### 模板/实现执行矩阵

| Route | HAS_EFFECTIVE_N | 状态类 |
|---|---|---|
| R-001 | false | skip |
| R-002 | false | tail |
| R-003 | false | compress |
| R-004 | true | skip |
| R-005 | true | tail |
| R-006 | true | compress |

score/tailScore独立三dtype共9storage组合，key/tailK/cacheBF16、APEFP32；metaint32/int64影响算术。全部自有Vector/elementwise/reduction，无dot/Cube/AIC/MIX，选VV。

### 隐藏性能 Guard

firstflag只读outloc[bN]，其余N-1值不逐token屏蔽。e先int32，超int32metadata窄化后再clamp，不按原int64数值理解。req/src写值域、ws+e及tailbase+slot算术和loc容量无Hostguard；req/locint64不证明各slot项已统一64bit。T=K+N保护常规历史容量，不保证任意tail_logical_start历史有效/无别名。sameprogramGMstore→reloadordering必须由compilerprimitive保持，不能自行插源码未有barrier来掩盖。无physicalUB查询或性能结论。

### POD/ABI

| 字段 | 分类/消费 |
|---|---|
| key_ptr/score_ptr | runtime只读draft |
| tail_k_ptr/tail_score_ptr/cache_ptr | runtime可变state→tail写/重读、cache写 |
| ape_ptr | runtime位置score只读 |
| req_pool_indices_ptr/write_start_ptr/tail_logical_start_ptr | runtime计划：reqint64/ws与tailbaseint32或64 |
| write_loc_ptr/out_cache_loc_ptr/effective_n_ptr | runtime候选cache行/首flag/effective或占位 |
| batch_size | runtimeB→轮转 |
| key_stride_0/score_stride_0 | runtime各draft元素rowstride |
| tail_k_stride_0/1、tail_score_stride_0/1 | runtime各request/slotstride |
| ape_stride_0/write_loc_stride_0/cache_stride_0 | runtimeAPE位置/候选batch/cache行stride |
| N/POOL_SIZE/TAIL_SIZE/HEAD_DIM | constexprN/K/K+N/128 |
| MAX_CLOSED_POOLS/HAS_EFFECTIVE_N/BLOCK_D | constexprceil(N/K)/effective存在/128 |
| grid | (n,)；实际program_count作步长 |

无POD序列化/字节offset，明确effective.toint32和读取其他intmetadata类型，JITABI/physicalallocation不猜测。

### Route 源码闭包

330行Direct/Device、public适配/helper完整读取，mem_cache/backendinit无Device。根setup→stage_runtime完整Python包→build_wheel/setup_refactor。框架只copy/metadata/view/empty，核心在线math自有；exp/max/load/store/GMordering为明确primitive边界，不以reference假闭合。

## Kernel 实现

### 公共执行流程

firstflag→有效batch全部N tailstores→读取/夹effective→完成poolcount→依C_b从已更新tail读历史→online池化cachewrite。rawBF16无Hadamard或quant，stateGM的真实先写后读必须体现。

### Route R-001：HAS_EFFECTIVE_N=false / skip

#### 适用条件

##### 选择证据

B>0、HAS_EFFECTIVE_N=false；out_cache_loc[b*N]==0。MAX=ceil(N/K)，K=pool_size，T=K+NHostassert。

#### Device 数据流

##### 函数级调用链

`Direct→checks/copy/grid→_kpool_write_tail_and_maybe_compress_kernel→首cachelocflag后跳过`，无其它自有Kernel/dot/Cube。

##### 源码等价伪码

program轮转batch b；读outloc[bN]。若0则跳全部元数据/数据/状态读写。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/GM |
|---|---|
| skipflag | 每batch仅out_cache_loc[bN]一标量，余N-1项不读取 |
| 当前draft | 不读 |
| 计划/effective | 不读 |
| pool数据 | 不读历史/loc、不写cache |
| FP32online | 不构建poolcarry |
| workspace | 无统计GM/请求方workspace，onlyreadcopy/可选4B占位另计 |

##### 分层内存布局

GMoutloc首项→跳过。同Kernel内tailstore→historyreload是实际GM依赖，不能画成直接寄存器值喂压缩。

##### 字节账与复用顺序

总调用令V有效batch数、C=Σ有效C_b，D128：`B*dloc + V*(8+dw+dt+N*D*(4+ds+dts)) + C*(K*D*(6+dts)+8+2D)` B。此route每rowV/C贡献0/0；C0仍读tailstart、e0仍全部N tail写。先store再读tail依compilerGMordering；状态/只读临时异步生命周期、跨调用同步由framework/caller，无显式workspace交接/free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 有效性 | 首outloc[bN]0即跳整batch，不单独看其它draft项 |
| 精度 | draftscore写入tail_score时可转换dtype，压缩读的是该storage舍入后值；keyBF16 |
| effective | Nconstexpr，4B占位不读取；仅压缩数门控 |
| 历史/顺序 | T=K+N可容纳常规历史窗口，但逻辑start/读入历史必须正确；allN写可能覆盖非法窗口，调用方保证 |
| 并发 | 不同batch同req/loc或cachealias未读input有风险，无锁/atomics/barrier |
| online | FP32逐channel重缩放，finite输入不保证acc/den中间不溢出 |
| 尾 | N/POOL/MAX静态slot，D128blockmask；只处理p<C_b，剩余loc不读 |
| 同步 | tailstore→poolreload依同programload/storelowering；没有可引用的MTEevent或hostwait |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| allN tailwrite | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_write_tail_and_maybe_compress.py#L54-L92) |
| effective/closed | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_write_tail_and_maybe_compress.py#L94-L110) |
| online/cache | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_write_tail_and_maybe_compress.py#L111-L156) |


### Route R-002：HAS_EFFECTIVE_N=false / tail

#### 适用条件

##### 选择证据

B>0、HAS_EFFECTIVE_N=false；out_cache_loc[b*N]!=0，C_b=0，e=N。MAX=ceil(N/K)，K=pool_size，T=K+NHostassert。

#### Device 数据流

##### 函数级调用链

`Direct→checks/copy/grid→_kpool_write_tail_and_maybe_compress_kernel→allN drafttailstores→effective/closedpool计算`，无其它自有Kernel/dot/Cube。

##### 源码等价伪码

program轮转batch b；读outloc[bN]。读req/ws；for d<N：key/score[bN+d]读，tail[req,(ws+d)%T]写（不看e）。e=N，clamp0..N；base=ws//K，C_b=clamp((ws+e)//K-base,0,MAX)；始终读tail_logical_start。C_b0不读write_loc/历史、不写cache。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/GM |
|---|---|
| skipflag | 每batch仅out_cache_loc[bN]一标量，余N-1项不读取 |
| 当前draft | 读N*128*(2+ds) B，写tailN*128*(2+dts) B |
| 计划/effective | req8/ws(dw)/tailstart(dt)，占位effective不读 |
| pool数据 | 不读历史/loc、不写cache |
| FP32online | 不构建poolcarry |
| workspace | 无统计GM/请求方workspace，onlyreadcopy/可选4B占位另计 |

##### 分层内存布局

GMkey/score→GMtail先覆盖全部N；无cache压缩。同Kernel内tailstore→historyreload是实际GM依赖，不能画成直接寄存器值喂压缩。

##### 字节账与复用顺序

总调用令V有效batch数、C=Σ有效C_b，D128：`B*dloc + V*(8+dw+dt+N*D*(4+ds+dts)) + C*(K*D*(6+dts)+8+2D)` B。此route每rowV/C贡献1/0；C0仍读tailstart、e0仍全部N tail写。先store再读tail依compilerGMordering；状态/只读临时异步生命周期、跨调用同步由framework/caller，无显式workspace交接/free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 有效性 | 首outloc[bN]0即跳整batch，不单独看其它draft项 |
| 精度 | draftscore写入tail_score时可转换dtype，压缩读的是该storage舍入后值；keyBF16 |
| effective | Nconstexpr，4B占位不读取；仅压缩数门控 |
| 历史/顺序 | T=K+N可容纳常规历史窗口，但逻辑start/读入历史必须正确；allN写可能覆盖非法窗口，调用方保证 |
| 并发 | 不同batch同req/loc或cachealias未读input有风险，无锁/atomics/barrier |
| online | FP32逐channel重缩放，finite输入不保证acc/den中间不溢出 |
| 尾 | N/POOL/MAX静态slot，D128blockmask；只处理p<C_b，剩余loc不读 |
| 同步 | tailstore→poolreload依同programload/storelowering；没有可引用的MTEevent或hostwait |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| allN tailwrite | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_write_tail_and_maybe_compress.py#L54-L92) |
| effective/closed | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_write_tail_and_maybe_compress.py#L94-L110) |
| online/cache | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_write_tail_and_maybe_compress.py#L111-L156) |


### Route R-003：HAS_EFFECTIVE_N=false / compress

#### 适用条件

##### 选择证据

B>0、HAS_EFFECTIVE_N=false；out_cache_loc[b*N]!=0，C_b>0，e=N。MAX=ceil(N/K)，K=pool_size，T=K+NHostassert。

#### Device 数据流

##### 函数级调用链

`Direct→checks/copy/grid→_kpool_write_tail_and_maybe_compress_kernel→allN drafttailstores→effective/closedpool计算→onlinepool从tail重读→BF16cache`，无其它自有Kernel/dot/Cube。

##### 源码等价伪码

program轮转batch b；读outloc[bN]。读req/ws；for d<N：key/score[bN+d]读，tail[req,(ws+d)%T]写（不看e）。e=N，clamp0..N；base=ws//K，C_b=clamp((ws+e)//K-base,0,MAX)；始终读tail_logical_start。for p<MAX且p<C_b：逻辑start=tail_logical_start+pK，从tail环重读K行、加APE逐通道online softmax，BF16pool写cache[write_loc[b,p]]。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/GM |
|---|---|
| skipflag | 每batch仅out_cache_loc[bN]一标量，余N-1项不读取 |
| 当前draft | 读N*128*(2+ds) B，写tailN*128*(2+dts) B |
| 计划/effective | req8/ws(dw)/tailstart(dt)，占位effective不读 |
| pool数据 | 每完成pool读K*128*(2+dts+4) B（key/score/APE单pass），write_loc8B读、cache256B写 |
| FP32online | m/acc/den/key/score/newmax/rescale/prob各128逻辑向量，单向量512B |
| workspace | 无统计GM/请求方workspace，onlyreadcopy/可选4B占位另计 |

##### 分层内存布局

GMkey/score→GMtail先覆盖全部N；GMtail重读/APE→FP32online向量→BF16cache。同Kernel内tailstore→historyreload是实际GM依赖，不能画成直接寄存器值喂压缩。

##### 字节账与复用顺序

总调用令V有效batch数、C=Σ有效C_b，D128：`B*dloc + V*(8+dw+dt+N*D*(4+ds+dts)) + C*(K*D*(6+dts)+8+2D)` B。此route每rowV/C贡献1/C_b；C0仍读tailstart、e0仍全部N tail写。先store再读tail依compilerGMordering；状态/只读临时异步生命周期、跨调用同步由framework/caller，无显式workspace交接/free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 有效性 | 首outloc[bN]0即跳整batch，不单独看其它draft项 |
| 精度 | draftscore写入tail_score时可转换dtype，压缩读的是该storage舍入后值；keyBF16 |
| effective | Nconstexpr，4B占位不读取；仅压缩数门控 |
| 历史/顺序 | T=K+N可容纳常规历史窗口，但逻辑start/读入历史必须正确；allN写可能覆盖非法窗口，调用方保证 |
| 并发 | 不同batch同req/loc或cachealias未读input有风险，无锁/atomics/barrier |
| online | FP32逐channel重缩放，finite输入不保证acc/den中间不溢出 |
| 尾 | N/POOL/MAX静态slot，D128blockmask；只处理p<C_b，剩余loc不读 |
| 同步 | tailstore→poolreload依同programload/storelowering；没有可引用的MTEevent或hostwait |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| allN tailwrite | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_write_tail_and_maybe_compress.py#L54-L92) |
| effective/closed | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_write_tail_and_maybe_compress.py#L94-L110) |
| online/cache | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_write_tail_and_maybe_compress.py#L111-L156) |


### Route R-004：HAS_EFFECTIVE_N=true / skip

#### 适用条件

##### 选择证据

B>0、HAS_EFFECTIVE_N=true；out_cache_loc[b*N]==0。MAX=ceil(N/K)，K=pool_size，T=K+NHostassert。

#### Device 数据流

##### 函数级调用链

`Direct→checks/copy/grid→_kpool_write_tail_and_maybe_compress_kernel→首cachelocflag后跳过`，无其它自有Kernel/dot/Cube。

##### 源码等价伪码

program轮转batch b；读outloc[bN]。若0则跳全部元数据/数据/状态读写。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/GM |
|---|---|
| skipflag | 每batch仅out_cache_loc[bN]一标量，余N-1项不读取 |
| 当前draft | 不读 |
| 计划/effective | 不读 |
| pool数据 | 不读历史/loc、不写cache |
| FP32online | 不构建poolcarry |
| workspace | 无统计GM/请求方workspace，onlyreadcopy/可选4B占位另计 |

##### 分层内存布局

GMoutloc首项→跳过。同Kernel内tailstore→historyreload是实际GM依赖，不能画成直接寄存器值喂压缩。

##### 字节账与复用顺序

总调用令V有效batch数、C=Σ有效C_b，D128：`B*dloc + V*(8+dw+dt+de+N*D*(4+ds+dts)) + C*(K*D*(6+dts)+8+2D)` B。此route每rowV/C贡献0/0；C0仍读tailstart、e0仍全部N tail写。先store再读tail依compilerGMordering；状态/只读临时异步生命周期、跨调用同步由framework/caller，无显式workspace交接/free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 有效性 | 首outloc[bN]0即跳整batch，不单独看其它draft项 |
| 精度 | draftscore写入tail_score时可转换dtype，压缩读的是该storage舍入后值；keyBF16 |
| effective | 先toint32再clamp，不能以int64原值clamp解释；仅压缩数门控 |
| 历史/顺序 | T=K+N可容纳常规历史窗口，但逻辑start/读入历史必须正确；allN写可能覆盖非法窗口，调用方保证 |
| 并发 | 不同batch同req/loc或cachealias未读input有风险，无锁/atomics/barrier |
| online | FP32逐channel重缩放，finite输入不保证acc/den中间不溢出 |
| 尾 | N/POOL/MAX静态slot，D128blockmask；只处理p<C_b，剩余loc不读 |
| 同步 | tailstore→poolreload依同programload/storelowering；没有可引用的MTEevent或hostwait |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| allN tailwrite | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_write_tail_and_maybe_compress.py#L54-L92) |
| effective/closed | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_write_tail_and_maybe_compress.py#L94-L110) |
| online/cache | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_write_tail_and_maybe_compress.py#L111-L156) |


### Route R-005：HAS_EFFECTIVE_N=true / tail

#### 适用条件

##### 选择证据

B>0、HAS_EFFECTIVE_N=true；out_cache_loc[b*N]!=0，C_b=0，e=clamp(int32(effective[b]),0,N)。MAX=ceil(N/K)，K=pool_size，T=K+NHostassert。

#### Device 数据流

##### 函数级调用链

`Direct→checks/copy/grid→_kpool_write_tail_and_maybe_compress_kernel→allN drafttailstores→effective/closedpool计算`，无其它自有Kernel/dot/Cube。

##### 源码等价伪码

program轮转batch b；读outloc[bN]。读req/ws；for d<N：key/score[bN+d]读，tail[req,(ws+d)%T]写（不看e）。读effective转int32，clamp0..N；base=ws//K，C_b=clamp((ws+e)//K-base,0,MAX)；始终读tail_logical_start。C_b0不读write_loc/历史、不写cache。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/GM |
|---|---|
| skipflag | 每batch仅out_cache_loc[bN]一标量，余N-1项不读取 |
| 当前draft | 读N*128*(2+ds) B，写tailN*128*(2+dts) B |
| 计划/effective | req8/ws(dw)/tailstart(dt)/effective(de) |
| pool数据 | 不读历史/loc、不写cache |
| FP32online | 不构建poolcarry |
| workspace | 无统计GM/请求方workspace，onlyreadcopy/可选4B占位另计 |

##### 分层内存布局

GMkey/score→GMtail先覆盖全部N；无cache压缩。同Kernel内tailstore→historyreload是实际GM依赖，不能画成直接寄存器值喂压缩。

##### 字节账与复用顺序

总调用令V有效batch数、C=Σ有效C_b，D128：`B*dloc + V*(8+dw+dt+de+N*D*(4+ds+dts)) + C*(K*D*(6+dts)+8+2D)` B。此route每rowV/C贡献1/0；C0仍读tailstart、e0仍全部N tail写。先store再读tail依compilerGMordering；状态/只读临时异步生命周期、跨调用同步由framework/caller，无显式workspace交接/free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 有效性 | 首outloc[bN]0即跳整batch，不单独看其它draft项 |
| 精度 | draftscore写入tail_score时可转换dtype，压缩读的是该storage舍入后值；keyBF16 |
| effective | 先toint32再clamp，不能以int64原值clamp解释；仅压缩数门控 |
| 历史/顺序 | T=K+N可容纳常规历史窗口，但逻辑start/读入历史必须正确；allN写可能覆盖非法窗口，调用方保证 |
| 并发 | 不同batch同req/loc或cachealias未读input有风险，无锁/atomics/barrier |
| online | FP32逐channel重缩放，finite输入不保证acc/den中间不溢出 |
| 尾 | N/POOL/MAX静态slot，D128blockmask；只处理p<C_b，剩余loc不读 |
| 同步 | tailstore→poolreload依同programload/storelowering；没有可引用的MTEevent或hostwait |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| allN tailwrite | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_write_tail_and_maybe_compress.py#L54-L92) |
| effective/closed | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_write_tail_and_maybe_compress.py#L94-L110) |
| online/cache | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_write_tail_and_maybe_compress.py#L111-L156) |


### Route R-006：HAS_EFFECTIVE_N=true / compress

#### 适用条件

##### 选择证据

B>0、HAS_EFFECTIVE_N=true；out_cache_loc[b*N]!=0，C_b>0，e=clamp(int32(effective[b]),0,N)。MAX=ceil(N/K)，K=pool_size，T=K+NHostassert。

#### Device 数据流

##### 函数级调用链

`Direct→checks/copy/grid→_kpool_write_tail_and_maybe_compress_kernel→allN drafttailstores→effective/closedpool计算→onlinepool从tail重读→BF16cache`，无其它自有Kernel/dot/Cube。

##### 源码等价伪码

program轮转batch b；读outloc[bN]。读req/ws；for d<N：key/score[bN+d]读，tail[req,(ws+d)%T]写（不看e）。读effective转int32，clamp0..N；base=ws//K，C_b=clamp((ws+e)//K-base,0,MAX)；始终读tail_logical_start。for p<MAX且p<C_b：逻辑start=tail_logical_start+pK，从tail环重读K行、加APE逐通道online softmax，BF16pool写cache[write_loc[b,p]]。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/GM |
|---|---|
| skipflag | 每batch仅out_cache_loc[bN]一标量，余N-1项不读取 |
| 当前draft | 读N*128*(2+ds) B，写tailN*128*(2+dts) B |
| 计划/effective | req8/ws(dw)/tailstart(dt)/effective(de) |
| pool数据 | 每完成pool读K*128*(2+dts+4) B（key/score/APE单pass），write_loc8B读、cache256B写 |
| FP32online | m/acc/den/key/score/newmax/rescale/prob各128逻辑向量，单向量512B |
| workspace | 无统计GM/请求方workspace，onlyreadcopy/可选4B占位另计 |

##### 分层内存布局

GMkey/score→GMtail先覆盖全部N；GMtail重读/APE→FP32online向量→BF16cache。同Kernel内tailstore→historyreload是实际GM依赖，不能画成直接寄存器值喂压缩。

##### 字节账与复用顺序

总调用令V有效batch数、C=Σ有效C_b，D128：`B*dloc + V*(8+dw+dt+de+N*D*(4+ds+dts)) + C*(K*D*(6+dts)+8+2D)` B。此route每rowV/C贡献1/C_b；C0仍读tailstart、e0仍全部N tail写。先store再读tail依compilerGMordering；状态/只读临时异步生命周期、跨调用同步由framework/caller，无显式workspace交接/free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 有效性 | 首outloc[bN]0即跳整batch，不单独看其它draft项 |
| 精度 | draftscore写入tail_score时可转换dtype，压缩读的是该storage舍入后值；keyBF16 |
| effective | 先toint32再clamp，不能以int64原值clamp解释；仅压缩数门控 |
| 历史/顺序 | T=K+N可容纳常规历史窗口，但逻辑start/读入历史必须正确；allN写可能覆盖非法窗口，调用方保证 |
| 并发 | 不同batch同req/loc或cachealias未读input有风险，无锁/atomics/barrier |
| online | FP32逐channel重缩放，finite输入不保证acc/den中间不溢出 |
| 尾 | N/POOL/MAX静态slot，D128blockmask；只处理p<C_b，剩余loc不读 |
| 同步 | tailstore→poolreload依同programload/storelowering；没有可引用的MTEevent或hostwait |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| allN tailwrite | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_write_tail_and_maybe_compress.py#L54-L92) |
| effective/closed | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_write_tail_and_maybe_compress.py#L94-L110) |
| online/cache | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_write_tail_and_maybe_compress.py#L111-L156) |

## 算子特定优化

### Trick T-001：有效草稿数仅门控压缩，tail写覆盖全N

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_write_tail_and_maybe_compress.py#L94-L110)：

```python
            if HAS_EFFECTIVE_N:
                effective_n = tl.load(effective_n_ptr + batch).to(tl.int32)
            else:
                effective_n = N
            effective_n = tl.minimum(tl.maximum(effective_n, 0), N)

            base_pool = write_start // POOL_SIZE
            completed_pools = (write_start + effective_n) // POOL_SIZE - base_pool
            completed_pools = tl.minimum(
                tl.maximum(completed_pools, 0), MAX_CLOSED_POOLS
            )
            tail_logical_start = tl.load(tail_logical_start_ptr + batch)

            # write_loc[b, p] maps the p-th candidate pool to its cache row.
            # Only the runtime-completed prefix is reduced and written.
            for pool_offset in tl.static_range(0, MAX_CLOSED_POOLS):
                if pool_offset < completed_pools:
```

全部Ntailwrites发生在此段之前62–92行，不能因effective0删除它们。

#### 机制与设计原因

对图内固定N行保持完整tail写入，effective只决定跨过几个pool边界；C_b上限MAX预分配候选loc，未完成候选不读loc/不压缩。源码语义机制可复验，无性能量测。

#### 迁移边界

N/K正、ws与tailstart映射/历史正确，int32effective窄化与ws+e算术可表示；不能把effective当直接tokenmask。

#### 错误做法

effective0跳整batch、用其它draft的outloc逐个屏蔽，或把MAX所有候选都压缩。

### Trick T-002：在线pool读取更新后的tailstorage

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_write_tail_and_maybe_compress.py#L128-L149)：

```python
                        pool_key = tl.load(
                            tail_k_ptr + pool_tail_k_offset,
                            mask=dim_mask,
                            other=0.0,
                        ).to(tl.float32)
                        pool_score = tl.load(
                            tail_score_ptr + pool_tail_score_offset,
                            mask=dim_mask,
                            other=0.0,
                        ).to(tl.float32)
                        pool_score += tl.load(
                            ape_ptr + slot * ape_stride_0 + offs,
                            mask=dim_mask,
                            other=0.0,
                        ).to(tl.float32)

                        new_max = tl.maximum(running_max, pool_score)
                        rescale = tl.exp(running_max - new_max)
                        prob = tl.exp(pool_score - new_max)
                        denom = denom * rescale + prob
                        acc = acc * rescale + pool_key * prob
                        running_max = new_max
```

#### 机制与设计原因

每slot tailK/tailScore/APE各读一次，online状态3carry向量重缩放；缓存写BF16，不保存pool矩阵。score先tailstore的dtype舍入与此处FP32load连接，不能直接拿原score代替。

#### 迁移边界

GMstore→load同programordering、历史有效与写集无并发冲突；finite输入仍可能FP32acc/den溢出，不将稳定maxshift当全部数值安全。

#### 错误做法

先压缩再写draft改变已完成pool内容，或省tailScore舍入仍宣称相同精度。

## 模板与实现对比

6执行类/9score组合、默认与显式grid/空rows顺序闭合；不同于decode先压缩后tail，本入口先写所有N后压缩。assembly直接从两种只读源拼接，不可套这里store后reload字节账。

## 平台差异

本卡950归属arch35；公开arch22支持、arch35已验证是上游报告非本次复测，README/architectures映射A2/A3、950。自有无hardwarebranch，CANN9.1.0 CI配置非实际compiler或physicalresource一致。

## 限制与失败边界

值域/历史/loc及req冲突/危险alias未完全guard，assert可关闭；staticloops/整数/资源与GMordering要匹配工具链。无构建、上游运行、测试/校验或真机/性能/physical产物，draft不推荐无条件原地并发安全复用。

## 源码索引

### 链路索引

| 阶段/源码 | 符号 | 事实 |
|---|---|---|
| [公开合同](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/mem_cache/kpool_write_tail_and_maybe_compress.md) | `kpool_write_tail_and_maybe_compress` | allN tail写/effective仅poolgate/BF16rawcache/平台 |
| [Direct/Device](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_write_tail_and_maybe_compress.py) | `kpool_write_tail_and_maybe_compress/_kpool_write_tail_and_maybe_compress_kernel` | 完整330行/三状态更新/有效N |
| [公开转发](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/mem_cache/kpool_write_tail_and_maybe_compress.py) | `_triton_impl` | 参数转发，无fallback |
| [mem_cache包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/__init__.py) | `module init` | 无Device |
| [属性helper](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py) | `get_device_properties` | 无参缓存/currentdevice/双核数assert |
| [import边界](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py) | `_load_sgl_kernel_npu` | torch_npu/原生库与vendor初始化 |
| [backend包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/__init__.py) | `module init` | 懒加载包，无另一Device节点 |
| [构建入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/setup.py) | `main` | 完整Python wheel路径；本次未构建 |
| [源码打包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/build_tools/torch_wheel.py) | `stage_runtime/build_torch/build_wheel/setup_refactor` | 复制完整Python包、原生运行库与wheel |
| [平台/包说明](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md) | `REFACTOR/arch22/35 mapping` | 全部Python实现包含、产品映射、CANN9.1.0构建例 |
| [产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json) | `2201/3510` | a2/a3/950对应构建族 |
| [版本配置](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernels.yml) | `test-norm-ops` | CANN9.1.0/a3/950配置，非本次运行 |
| [CI消费](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernel-group.yml) | `run-kernel-group` | 对应版本容器/测试组参数 |

### 实现复用检查

冻结117/legacy共同KpoolAPI全文读并链接，新增唯一drafttail+pool压缩Direct两平台卡，不合并decode/scatter/assembly其它数学。source同repo固定一primary，无verified。
