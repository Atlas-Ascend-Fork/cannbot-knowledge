---
type: Operator
title: "KpoolAssembleSoftmaxRotateWriteCache 950 Direct Invoke 算子知识"
description: "闭合tail/chunk计划assembly的七写mask源路线与FP32 online softmax、BF16原值cache，记录单pass字节、全tail空chunk及显式grid边界。"
tags: [task.implementation, task.lookup, topic.memory, topic.precision, topic.programming_model]
status: draft
sources:
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/mem_cache/kpool_assemble_softmax_rotate_write_cache.md
    role: primary
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_assemble_softmax_rotate_write_cache.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/mem_cache/kpool_assemble_softmax_rotate_write_cache.py
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
created_at: "2026-11-09T10:24:06Z"
updated_at: "2026-11-10T07:06:47Z"
platforms: ["950"]
cann_versions: ["9.1.0"]
---

# KpoolAssembleSoftmaxRotateWriteCache 950 Direct Invoke 算子知识

## 算子速览

`sgl_kernel_npu.implementation.triton.mem_cache.kpool_assemble_softmax_rotate_write_cache.kpool_assemble_softmax_rotate_write_cache` 按计划拼tail前缀与chunk后缀，以逐通道在线softmax加权key，直接BF16写cache。名字含rotate，实际无旋转/Hadamard/FP8/scale；只cache可变，tail/chunk只读，None返回。完整Host/空计划/掩码与源三类共7执行路线闭合，无dot/Cube，VV。

draft保留计划值域、原地cache写冲突/危险别名、整数与resource边界及无当前运行证据。复用全文读过的[共同Kpool API](../../../../apis/sgl_kernel_npu/sgl_kpool_tail_cache.md)。

## 接口与语义

### 计算语义

每plan：K=APE.shape0，nt=n_from_tail∈[0,K]。前nt slots取tail[req,(tail_base+s)%T]，其余取chunk[chunk_src+s-nt]。每通道128分别沿slot做softmax(score+APE)，pooled=Σsoftmax*key，BF16存cache.view(-1,128)[loc]。maskNone全部active，maskfalse计划不读其它metadata/数据/loc且不写cache。全tail允许空chunk，source用真实if分支而非双load后where。

### 输入、输出与属性

| 项 | 真实Hostcheck/合同 |
|---|---|
| cache | BF16、numel%128=0、contiguous，同device，原地flattenview不copy |
| chunk/tailK | BF16，chunk[Nc,128]、tail[R,T,128]，score同shape且三浮点dtype各自独立 |
| APE | FP32[K,128]，K>0、T>0显式assert |
| 五计划 | 同长A、1D，req/src/locint64，n_tail/tail_baseint32或int64；req/n_tail/src/tailbase要求已contiguous |
| mask | None或bool[A]，可内部contiguous |
| 动态只读copy | chunkK/score、APE、loc、mask各contiguous，cache/tail不复制 |
| device/indices | allsameDevice显式assert但无单独NPUassert；实际索引范围/历史有效、0≤nt≤K、loc容量/不冲突由调用方保证 |
| 返回 | None，仅cache选中行写，inputs/tail不变 |

### 入口与版本

Direct签名(cache,chunk_k,chunk_score,tail_k,tail_score,req_pool_idx,n_from_tail,chunk_src_start,tail_logical_base,ape,loc,write_mask=None,*,num_programs=None)。auto/triton转发，无fallback；Torch参考不补自有body。SGLcommit `dda6d36b0cdb4081e102d14c0a2fb276fc416e69`，CANN9.1.0来自README/CI非本次环境，完整Tritonbinary未固定。

## Host/Launcher 执行流程

### 参数校验与前处理

dtype/shape/128与cache整行数→K/T正→计划长度/dtype及maskshape→只读copy→全部sameDevice/contiguousassert→A0return。空计划仍执行此前checks/copy，不同于scatter的早返。非空num_programsNone用min(A,Pcores)，显式值须>0后min(A,num_programs)；没有显式cap Vector核数。maskNone分配emptybool[1]占位且HASfalse不读；cache.view(-1,128)launch。

### 参数、Workspace 与生命周期

无新cache输出或GM统计/请求方workspace/POD/ACLNN；可能只读copy临时各numel*d B，额外读写各同字节。maskNone实际1bool占位（逻辑1B，非物理allocator对齐证明）。helper仅默认并行度分支调用，无参currentdevicecache/双核数assert；显式num_programs可绕helper但仍需NPU合同，未deviceguard。临时copy/占位/参数异步存活和原地cache完成依framework，未hostwait/显式stream/event。

### 启动图与失败传播

import→checks/onlyreadcopy→A0返回或grid决定→可选mask占位→cacheview→单JITKernel→None。num_programs≤0 ValueError只非空时检查；assert可被Python-O关闭。所有核心online算法自有，无外部Torch数学fallback；异常传播，无回滚，package原生库仅导入前提。

## Route 与参数设计

### 分核与资源计算

grid n，program p轮转plan a=p+j*n<A；每activeplan按K静态slot顺序读取一个实际source，3个核心carry向量m/acc/den各128FP32。其它key/score/prob/newmax/rescale临时同128逻辑，物理峰值/UB寄存器归compiler。payloadchannel128无尾；BLOCK_D128，headmask恒true。在线状态不随K保存完整pool行矩阵，但代码展开/运行量随K增长。

### Route 选择

HAS_WRITE_MASK两编译态；有maskfalse跳所有plan数据，无mask或true各有nt0/0<nt<K/ntK三source执行类，共7。空A纯Host无Kernel。num_programs默认/显式只改变网格Host路线，不改变数学。

### 模板/实现执行矩阵

| Route | mask存在 | 数据域 |
|---|---|---|
| R-001 | false | chunk |
| R-002 | false | mixed |
| R-003 | false | tail |
| R-004 | true | skip |
| R-005 | true | chunk |
| R-006 | true | mixed |
| R-007 | true | tail |

chunk_score/tail_score各FP16/BF16/FP32共9dtype组合，FP32math相同但GM字节不同；n_tail/tail_base各int32/int64参与地址宽度。自有body无dot/Cube/AIC/MIX，选VV不是目录猜测。

### 隐藏性能 Guard

source注释“cap到vectorcore”仅对默认分支成立，显式grid只capA；不造所有手动grid≤core约束。nt值域/req/loc/源row/历史容量无Host值检查，动态分支只保护未选源，不保护非法已选地址。int64req/src/loc不自动证明tailbase+slot及尾地址每乘积64bit，所有算术须可表示。无UB容量/性能收益实测，online不等无限K安全。

### POD/ABI

| 字段 | 分类/消费 |
|---|---|
| cache_ptr/chunk_k_ptr/chunk_score_ptr/tail_k_ptr/tail_score_ptr | runtimepayload指针，cache写其它只读 |
| req_pool_idx_ptr/n_from_tail_ptr/chunk_src_start_ptr/tail_logical_base_ptr/loc_ptr | runtime5计划→拼接/写址 |
| ape_ptr/write_mask_ptr | runtime位置score/可选bool输入 |
| n_pools | runtimeA→轮转 |
| cache_stride_0 | runtimeflattenrow元素stride128→loc地址 |
| chunk_k_stride_0/chunk_score_stride_0 | runtime各自source行stride |
| tail_k_stride_0/1、tail_score_stride_0/1 | runtime各自请求/slotstride |
| ape_stride_0 | runtime位置score行stride |
| POOL_SIZE/TAIL_SIZE/HEAD_DIM | constexprK/T/128 |
| HAS_WRITE_MASK/BLOCK_D | constexprmask存在/128 |
| grid | (n,)；program_count来自num_programs |

无序列化POD/字节offset，全部真实字段列明，JIT ABI/physicalallocation与算术lowering外部不猜。

### Route 源码闭包

完整285行Direct/Device、public适配/helper已读，mem_cache/backendinit无Device。根setup→stage_runtime完整Python包→build_wheel/setup_refactor。exp/max/load/store与physicalallocation为明确primitive边界，外部框架仅metadata/copy/view/empty，不隐藏核心math。

## Kernel 实现

### 公共执行流程

可选mask→active才读plan→初始化online状态→逐slot真实tail/chunk分支load→加APE并rescale更新→BF16cache写。tail/chunk历史完全不修改，无旋转/量化/scoreGM输出。

### Route R-001：无write_mask / chunk

#### 适用条件

##### 选择证据

A>0、HAS_WRITE_MASK=false；active=固定true，n_tail0，K=pool_size=APE行数正、T正，128通道合同。

#### Device 数据流

##### 函数级调用链

`Direct→assert/copy→[helper或显式并行度]→_kpool_assemble_softmax_rotate_write_cache_kernel→chunkload→APE/onlineexp加权→BF16cachestore`，没有Cube/dot或另一个自有Kernel。

##### 源码等价伪码

program p轮转plan a=p+j*n。读n_tail/req/chunk_src/tail_base；m=-inf,acc=den0三个FP32[128]；for slot<K，只从chunk_src+slot读key/score；score+=APE[slot]，m'=max(m,score)，a=exp(m-m'),p=exp(score-m')，den=den*a+p，acc=acc*a+key*p，m=m'；pooled=BF16(acc/den)，cache[loc[row],:]=pooled。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/有效GM |
|---|---|
| mask | 分配1bool占位，flagfalse不读取 |
| 计划 | n_tail/req/chunk_src/tail_base四标量，loc最后读 |
| key/score/APE | K*128*(2+dcs+4) B读 |
| onlineSSA | m/acc/den/key/score/newmax/rescale/prob各128FP32逻辑，单向量512B，不求和当物理峰值 |
| cache | 128*2=256B写 |
| workspace/UB | 无统计GM/请求方workspace，compilerphysical分配外部 |

##### 分层内存布局

GMchunk+APE→FP32online向量[128]→BF16cache[loc,128]。tail/chunk只读、不写；不物化完整K×128 GM统计/softmax矩阵。

##### 字节账与复用顺序

有mask全A计划读A B（bool逻辑1B）；无mask不读占位。每active计划读metadata `8+8+8+dn_tail+dtail_base` B（req/src/loc各int64），payload如表，再写256Bcache。inactive只有mask读。所有只读copy临时按实际发生项各numel*d分配，额外读写各同大小；maskNone额外1B占位。cache原地state持有原storage，流序与异步释放归framework；source与cache危险alias/并发loc冲突须外部排除。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 源选择 | 真实if只读chunk，不读tail数据 |
| online | FP32newmax重缩放acc/den，初始-inf、首个有限score使rescale0；K正且有限参与值保证数学域 |
| 类型 | keyBF16/score三浮点/APEFP32→FP32，acc/den→BF16cache，无Hadamard/FP8 |
| 地址 | req/src/locint64来自Hostdtypeguard；tail_base/slot部分算术随int32/64metadata，未统一显式64 |
| 写集合 | 每plan256B；loc重复或cachealias未读source会race/改变输入，无atomic/锁 |
| 同步 | program独立SSA/循环顺序由compiler，外部state流同步caller管理，无hostwait |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| active/plan | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_assemble_softmax_rotate_write_cache.py#L52-L68) |
| actual source branch | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_assemble_softmax_rotate_write_cache.py#L70-L102) |
| online/cache | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_assemble_softmax_rotate_write_cache.py#L104-L121) |


### Route R-002：无write_mask / mixed

#### 适用条件

##### 选择证据

A>0、HAS_WRITE_MASK=false；active=固定true，0<n_tail<K，K=pool_size=APE行数正、T正，128通道合同。

#### Device 数据流

##### 函数级调用链

`Direct→assert/copy→[helper或显式并行度]→_kpool_assemble_softmax_rotate_write_cache_kernel→tail/chunk条件load→APE/onlineexp加权→BF16cachestore`，没有Cube/dot或另一个自有Kernel。

##### 源码等价伪码

program p轮转plan a=p+j*n。读n_tail/req/chunk_src/tail_base；m=-inf,acc=den0三个FP32[128]；for slot<K，slot<n_tail读tail，否则chunk_src+slot-n_tail；score+=APE[slot]，m'=max(m,score)，a=exp(m-m'),p=exp(score-m')，den=den*a+p，acc=acc*a+key*p，m=m'；pooled=BF16(acc/den)，cache[loc[row],:]=pooled。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/有效GM |
|---|---|
| mask | 分配1bool占位，flagfalse不读取 |
| 计划 | n_tail/req/chunk_src/tail_base四标量，loc最后读 |
| key/score/APE | 128*[nt*(2+dts)+(K-nt)*(2+dcs)+4K] B读 |
| onlineSSA | m/acc/den/key/score/newmax/rescale/prob各128FP32逻辑，单向量512B，不求和当物理峰值 |
| cache | 128*2=256B写 |
| workspace/UB | 无统计GM/请求方workspace，compilerphysical分配外部 |

##### 分层内存布局

GMtail前段/chunk后段+APE→FP32online向量[128]→BF16cache[loc,128]。tail/chunk只读、不写；不物化完整K×128 GM统计/softmax矩阵。

##### 字节账与复用顺序

有mask全A计划读A B（bool逻辑1B）；无mask不读占位。每active计划读metadata `8+8+8+dn_tail+dtail_base` B（req/src/loc各int64），payload如表，再写256Bcache。inactive只有mask读。所有只读copy临时按实际发生项各numel*d分配，额外读写各同大小；maskNone额外1B占位。cache原地state持有原storage，流序与异步释放归framework；source与cache危险alias/并发loc冲突须外部排除。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 源选择 | 真实if逐slot仅读一个源，不是双load后where |
| online | FP32newmax重缩放acc/den，初始-inf、首个有限score使rescale0；K正且有限参与值保证数学域 |
| 类型 | keyBF16/score三浮点/APEFP32→FP32，acc/den→BF16cache，无Hadamard/FP8 |
| 地址 | req/src/locint64来自Hostdtypeguard；tail_base/slot部分算术随int32/64metadata，未统一显式64 |
| 写集合 | 每plan256B；loc重复或cachealias未读source会race/改变输入，无atomic/锁 |
| 同步 | program独立SSA/循环顺序由compiler，外部state流同步caller管理，无hostwait |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| active/plan | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_assemble_softmax_rotate_write_cache.py#L52-L68) |
| actual source branch | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_assemble_softmax_rotate_write_cache.py#L70-L102) |
| online/cache | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_assemble_softmax_rotate_write_cache.py#L104-L121) |


### Route R-003：无write_mask / tail

#### 适用条件

##### 选择证据

A>0、HAS_WRITE_MASK=false；active=固定true，n_tailK，K=pool_size=APE行数正、T正，128通道合同。

#### Device 数据流

##### 函数级调用链

`Direct→assert/copy→[helper或显式并行度]→_kpool_assemble_softmax_rotate_write_cache_kernel→tailload→APE/onlineexp加权→BF16cachestore`，没有Cube/dot或另一个自有Kernel。

##### 源码等价伪码

program p轮转plan a=p+j*n。读n_tail/req/chunk_src/tail_base；m=-inf,acc=den0三个FP32[128]；for slot<K，只从tail[req,(tail_base+slot)%T]读key/score；score+=APE[slot]，m'=max(m,score)，a=exp(m-m'),p=exp(score-m')，den=den*a+p，acc=acc*a+key*p，m=m'；pooled=BF16(acc/den)，cache[loc[row],:]=pooled。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/有效GM |
|---|---|
| mask | 分配1bool占位，flagfalse不读取 |
| 计划 | n_tail/req/chunk_src/tail_base四标量，loc最后读 |
| key/score/APE | K*128*(2+dts+4) B读 |
| onlineSSA | m/acc/den/key/score/newmax/rescale/prob各128FP32逻辑，单向量512B，不求和当物理峰值 |
| cache | 128*2=256B写 |
| workspace/UB | 无统计GM/请求方workspace，compilerphysical分配外部 |

##### 分层内存布局

GMtailring+APE→FP32online向量[128]→BF16cache[loc,128]。tail/chunk只读、不写；不物化完整K×128 GM统计/softmax矩阵。

##### 字节账与复用顺序

有mask全A计划读A B（bool逻辑1B）；无mask不读占位。每active计划读metadata `8+8+8+dn_tail+dtail_base` B（req/src/loc各int64），payload如表，再写256Bcache。inactive只有mask读。所有只读copy临时按实际发生项各numel*d分配，额外读写各同大小；maskNone额外1B占位。cache原地state持有原storage，流序与异步释放归framework；source与cache危险alias/并发loc冲突须外部排除。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 源选择 | 真实if只读tail，空chunk可合法存在 |
| online | FP32newmax重缩放acc/den，初始-inf、首个有限score使rescale0；K正且有限参与值保证数学域 |
| 类型 | keyBF16/score三浮点/APEFP32→FP32，acc/den→BF16cache，无Hadamard/FP8 |
| 地址 | req/src/locint64来自Hostdtypeguard；tail_base/slot部分算术随int32/64metadata，未统一显式64 |
| 写集合 | 每plan256B；loc重复或cachealias未读source会race/改变输入，无atomic/锁 |
| 同步 | program独立SSA/循环顺序由compiler，外部state流同步caller管理，无hostwait |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| active/plan | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_assemble_softmax_rotate_write_cache.py#L52-L68) |
| actual source branch | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_assemble_softmax_rotate_write_cache.py#L70-L102) |
| online/cache | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_assemble_softmax_rotate_write_cache.py#L104-L121) |


### Route R-004：有write_mask / skip

#### 适用条件

##### 选择证据

A>0、HAS_WRITE_MASK=true；mask[row]false，其它计划数值不会读，K=pool_size=APE行数正、T正，128通道合同。

#### Device 数据流

##### 函数级调用链

`Direct→assert/copy→[helper或显式并行度]→_kpool_assemble_softmax_rotate_write_cache_kernel→maskload后跳过`，没有Cube/dot或另一个自有Kernel。

##### 源码等价伪码

program p轮转plan a=p+j*n。读maskfalse，跳过所有metadata/初始化/数据/loc/cache写。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/有效GM |
|---|---|
| mask | 每plan1bool读 |
| 计划 | 无读取 |
| key/score/APE | 不读 |
| onlineSSA | 本分支不计算 |
| cache | 不写 |
| workspace/UB | 无统计GM/请求方workspace，compilerphysical分配外部 |

##### 分层内存布局

GMboolmask→跳过，无其它source访问。tail/chunk只读、不写；不物化完整K×128 GM统计/softmax矩阵。

##### 字节账与复用顺序

有mask全A计划读A B（bool逻辑1B）；无mask不读占位。每active计划读metadata `8+8+8+dn_tail+dtail_base` B（req/src/loc各int64），payload如表，再写256Bcache。inactive只有mask读。所有只读copy临时按实际发生项各numel*d分配，额外读写各同大小；maskNone额外1B占位。cache原地state持有原storage，流序与异步释放归framework；source与cache危险alias/并发loc冲突须外部排除。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 源选择 | inactive不读其它metadata，非法loc不被消费 |
| online | 不计算 |
| 类型 | keyBF16/score三浮点/APEFP32→FP32，acc/den→BF16cache，无Hadamard/FP8 |
| 地址 | req/src/locint64来自Hostdtypeguard；tail_base/slot部分算术随int32/64metadata，未统一显式64 |
| 写集合 | 0B；inactive不读取loc或写cache。每plan256B与loc重复/cachealias写冲突约束仅适用于active路线 |
| 同步 | program独立SSA/循环顺序由compiler，外部state流同步caller管理，无hostwait |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| active/plan | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_assemble_softmax_rotate_write_cache.py#L52-L68) |
| actual source branch | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_assemble_softmax_rotate_write_cache.py#L70-L102) |
| online/cache | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_assemble_softmax_rotate_write_cache.py#L104-L121) |


### Route R-005：有write_mask / chunk

#### 适用条件

##### 选择证据

A>0、HAS_WRITE_MASK=true；active=mask[row]true，n_tail0，K=pool_size=APE行数正、T正，128通道合同。

#### Device 数据流

##### 函数级调用链

`Direct→assert/copy→[helper或显式并行度]→_kpool_assemble_softmax_rotate_write_cache_kernel→chunkload→APE/onlineexp加权→BF16cachestore`，没有Cube/dot或另一个自有Kernel。

##### 源码等价伪码

program p轮转plan a=p+j*n。读n_tail/req/chunk_src/tail_base；m=-inf,acc=den0三个FP32[128]；for slot<K，只从chunk_src+slot读key/score；score+=APE[slot]，m'=max(m,score)，a=exp(m-m'),p=exp(score-m')，den=den*a+p，acc=acc*a+key*p，m=m'；pooled=BF16(acc/den)，cache[loc[row],:]=pooled。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/有效GM |
|---|---|
| mask | 每plan1bool读 |
| 计划 | n_tail/req/chunk_src/tail_base四标量，loc最后读 |
| key/score/APE | K*128*(2+dcs+4) B读 |
| onlineSSA | m/acc/den/key/score/newmax/rescale/prob各128FP32逻辑，单向量512B，不求和当物理峰值 |
| cache | 128*2=256B写 |
| workspace/UB | 无统计GM/请求方workspace，compilerphysical分配外部 |

##### 分层内存布局

GMchunk+APE→FP32online向量[128]→BF16cache[loc,128]。tail/chunk只读、不写；不物化完整K×128 GM统计/softmax矩阵。

##### 字节账与复用顺序

有mask全A计划读A B（bool逻辑1B）；无mask不读占位。每active计划读metadata `8+8+8+dn_tail+dtail_base` B（req/src/loc各int64），payload如表，再写256Bcache。inactive只有mask读。所有只读copy临时按实际发生项各numel*d分配，额外读写各同大小；maskNone额外1B占位。cache原地state持有原storage，流序与异步释放归framework；source与cache危险alias/并发loc冲突须外部排除。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 源选择 | 真实if只读chunk，不读tail数据 |
| online | FP32newmax重缩放acc/den，初始-inf、首个有限score使rescale0；K正且有限参与值保证数学域 |
| 类型 | keyBF16/score三浮点/APEFP32→FP32，acc/den→BF16cache，无Hadamard/FP8 |
| 地址 | req/src/locint64来自Hostdtypeguard；tail_base/slot部分算术随int32/64metadata，未统一显式64 |
| 写集合 | 每plan256B；loc重复或cachealias未读source会race/改变输入，无atomic/锁 |
| 同步 | program独立SSA/循环顺序由compiler，外部state流同步caller管理，无hostwait |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| active/plan | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_assemble_softmax_rotate_write_cache.py#L52-L68) |
| actual source branch | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_assemble_softmax_rotate_write_cache.py#L70-L102) |
| online/cache | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_assemble_softmax_rotate_write_cache.py#L104-L121) |


### Route R-006：有write_mask / mixed

#### 适用条件

##### 选择证据

A>0、HAS_WRITE_MASK=true；active=mask[row]true，0<n_tail<K，K=pool_size=APE行数正、T正，128通道合同。

#### Device 数据流

##### 函数级调用链

`Direct→assert/copy→[helper或显式并行度]→_kpool_assemble_softmax_rotate_write_cache_kernel→tail/chunk条件load→APE/onlineexp加权→BF16cachestore`，没有Cube/dot或另一个自有Kernel。

##### 源码等价伪码

program p轮转plan a=p+j*n。读n_tail/req/chunk_src/tail_base；m=-inf,acc=den0三个FP32[128]；for slot<K，slot<n_tail读tail，否则chunk_src+slot-n_tail；score+=APE[slot]，m'=max(m,score)，a=exp(m-m'),p=exp(score-m')，den=den*a+p，acc=acc*a+key*p，m=m'；pooled=BF16(acc/den)，cache[loc[row],:]=pooled。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/有效GM |
|---|---|
| mask | 每plan1bool读 |
| 计划 | n_tail/req/chunk_src/tail_base四标量，loc最后读 |
| key/score/APE | 128*[nt*(2+dts)+(K-nt)*(2+dcs)+4K] B读 |
| onlineSSA | m/acc/den/key/score/newmax/rescale/prob各128FP32逻辑，单向量512B，不求和当物理峰值 |
| cache | 128*2=256B写 |
| workspace/UB | 无统计GM/请求方workspace，compilerphysical分配外部 |

##### 分层内存布局

GMtail前段/chunk后段+APE→FP32online向量[128]→BF16cache[loc,128]。tail/chunk只读、不写；不物化完整K×128 GM统计/softmax矩阵。

##### 字节账与复用顺序

有mask全A计划读A B（bool逻辑1B）；无mask不读占位。每active计划读metadata `8+8+8+dn_tail+dtail_base` B（req/src/loc各int64），payload如表，再写256Bcache。inactive只有mask读。所有只读copy临时按实际发生项各numel*d分配，额外读写各同大小；maskNone额外1B占位。cache原地state持有原storage，流序与异步释放归framework；source与cache危险alias/并发loc冲突须外部排除。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 源选择 | 真实if逐slot仅读一个源，不是双load后where |
| online | FP32newmax重缩放acc/den，初始-inf、首个有限score使rescale0；K正且有限参与值保证数学域 |
| 类型 | keyBF16/score三浮点/APEFP32→FP32，acc/den→BF16cache，无Hadamard/FP8 |
| 地址 | req/src/locint64来自Hostdtypeguard；tail_base/slot部分算术随int32/64metadata，未统一显式64 |
| 写集合 | 每plan256B；loc重复或cachealias未读source会race/改变输入，无atomic/锁 |
| 同步 | program独立SSA/循环顺序由compiler，外部state流同步caller管理，无hostwait |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| active/plan | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_assemble_softmax_rotate_write_cache.py#L52-L68) |
| actual source branch | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_assemble_softmax_rotate_write_cache.py#L70-L102) |
| online/cache | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_assemble_softmax_rotate_write_cache.py#L104-L121) |


### Route R-007：有write_mask / tail

#### 适用条件

##### 选择证据

A>0、HAS_WRITE_MASK=true；active=mask[row]true，n_tailK，K=pool_size=APE行数正、T正，128通道合同。

#### Device 数据流

##### 函数级调用链

`Direct→assert/copy→[helper或显式并行度]→_kpool_assemble_softmax_rotate_write_cache_kernel→tailload→APE/onlineexp加权→BF16cachestore`，没有Cube/dot或另一个自有Kernel。

##### 源码等价伪码

program p轮转plan a=p+j*n。读n_tail/req/chunk_src/tail_base；m=-inf,acc=den0三个FP32[128]；for slot<K，只从tail[req,(tail_base+slot)%T]读key/score；score+=APE[slot]，m'=max(m,score)，a=exp(m-m'),p=exp(score-m')，den=den*a+p，acc=acc*a+key*p，m=m'；pooled=BF16(acc/den)，cache[loc[row],:]=pooled。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/有效GM |
|---|---|
| mask | 每plan1bool读 |
| 计划 | n_tail/req/chunk_src/tail_base四标量，loc最后读 |
| key/score/APE | K*128*(2+dts+4) B读 |
| onlineSSA | m/acc/den/key/score/newmax/rescale/prob各128FP32逻辑，单向量512B，不求和当物理峰值 |
| cache | 128*2=256B写 |
| workspace/UB | 无统计GM/请求方workspace，compilerphysical分配外部 |

##### 分层内存布局

GMtailring+APE→FP32online向量[128]→BF16cache[loc,128]。tail/chunk只读、不写；不物化完整K×128 GM统计/softmax矩阵。

##### 字节账与复用顺序

有mask全A计划读A B（bool逻辑1B）；无mask不读占位。每active计划读metadata `8+8+8+dn_tail+dtail_base` B（req/src/loc各int64），payload如表，再写256Bcache。inactive只有mask读。所有只读copy临时按实际发生项各numel*d分配，额外读写各同大小；maskNone额外1B占位。cache原地state持有原storage，流序与异步释放归framework；source与cache危险alias/并发loc冲突须外部排除。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 源选择 | 真实if只读tail，空chunk可合法存在 |
| online | FP32newmax重缩放acc/den，初始-inf、首个有限score使rescale0；K正且有限参与值保证数学域 |
| 类型 | keyBF16/score三浮点/APEFP32→FP32，acc/den→BF16cache，无Hadamard/FP8 |
| 地址 | req/src/locint64来自Hostdtypeguard；tail_base/slot部分算术随int32/64metadata，未统一显式64 |
| 写集合 | 每plan256B；loc重复或cachealias未读source会race/改变输入，无atomic/锁 |
| 同步 | program独立SSA/循环顺序由compiler，外部state流同步caller管理，无hostwait |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| active/plan | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_assemble_softmax_rotate_write_cache.py#L52-L68) |
| actual source branch | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_assemble_softmax_rotate_write_cache.py#L70-L102) |
| online/cache | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_assemble_softmax_rotate_write_cache.py#L104-L121) |

## 算子特定优化

### Trick T-001：逐通道online softmax单次读取pool

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_assemble_softmax_rotate_write_cache.py#L104-L117)：

```python
                score += tl.load(
                    ape_ptr + slot * ape_stride_0 + offs,
                    mask=head_mask,
                    other=0.0,
                ).to(tl.float32)
                new_max = tl.maximum(running_max, score)
                rescale = tl.exp(running_max - new_max)
                prob = tl.exp(score - new_max)
                denom = denom * rescale + prob
                acc = acc * rescale + key * prob
                running_max = new_max

            # NPU index cache stores raw BF16 keys: no Hadamard, FP8, or scale.
            pooled = (acc / denom).to(tl.bfloat16)
```

#### 机制与设计原因

newmax变化时将旧acc/den乘exp(oldmax-newmax)，新key按exp(score-newmax)加入，稳定softmax不需两遍读score或保存K行矩阵。GM每slot key/score/APE各读一次，未测速度/误差收益。

#### 迁移边界

K正、参与score/key/APE有限且可定义，slot顺序与FP32近似会影响舍入；不能用其它归约树逐位等价假设。

#### 错误做法

更新max却不rescale旧acc/den，或把softmax沿通道而非poolslot。

### Trick T-002：写mask在所有计划/数据读取之前筛选

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_assemble_softmax_rotate_write_cache.py#L52-L62)：

```python
    for row in range(pid, n_pools, program_count):
        active = True
        if HAS_WRITE_MASK:
            active = tl.load(write_mask_ptr + row)

        if active:
            # Load the plan entry that describes how this pool is assembled.
            n_tail = tl.load(n_from_tail_ptr + row)
            req = tl.load(req_pool_idx_ptr + row)
            chunk_src = tl.load(chunk_src_start_ptr + row)
            tail_base = tl.load(tail_logical_base_ptr + row)
```

#### 机制与设计原因

falsemask计划只读1bool，避免全部元数据及pooldata访问，loc也直到active结束才读。真实sourceif进一步使全tail不触碰空chunk，不能用双load+where替代仍称相同安全域。

#### 迁移边界

mask长度/连续布局合法，active计划值域与cache不冲突；inactive不消费值不等于Host可以缺少计划Tensor/shape。

#### 错误做法

把计划/loc提前load再称mask保护所有无效地址，或将tail/chunk两边先读后select破坏全tail空chunk支持。

## 模板与实现对比

7路线、9score组合、默认/显式grid均登记，inlineonlineVector比decode两pass读取不同，互不套字节/同步。函数名rotate未对应实际旋转，rawBF16cache语义不扩到Hadamard/FP8。

## 平台差异

本卡950归属arch35；公开arch22支持、arch35已验证仅上游报告，README/architectures映射A2/A3、950。无hardware分支，CANN9.1.0 CI配置不是本次复测/compiler或physical资源等同。

## 限制与失败边界

索引/history/loc写冲突/源cache别名未完整guard；断言可关闭，显式grid可>core，tailbase算术/资源域需核对。在线rescale不防FP32 acc/denom中间溢出，有限输入不足以保证所有中间值有限。无构建、上游运行、测试/校验、真机/数值/性能或physicalUB产物，draft保留条件不作原地并发安全保证。

## 源码索引

### 链路索引

| 阶段/源码 | 符号 | 事实 |
|---|---|---|
| [公开合同](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/mem_cache/kpool_assemble_softmax_rotate_write_cache.md) | `kpool_assemble_softmax_rotate_write_cache` | tail+chunk计划/onlinepool/BF16rawcache/平台 |
| [Direct/Device](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_assemble_softmax_rotate_write_cache.py) | `kpool_assemble_softmax_rotate_write_cache/_kpool_assemble_softmax_rotate_write_cache_kernel` | 完整285行/online单pass/掩码 |
| [公开转发](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/mem_cache/kpool_assemble_softmax_rotate_write_cache.py) | `_triton_impl` | 原地cache转发，无fallback |
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

冻结117/legacy共同KpoolAPI已全文读并链接，只新增本assembly唯一Operator，不并入tail写/decode/scatter。全部同repo固定source一primary，无verified。
