---
type: Operator
title: "KpoolDecodeUpdateAndMaybeWriteCache 950 Direct Invoke 算子知识"
description: "闭合decode Kpool有效性三路线、两pass逐通道softmax及页表BF16 cache/tail顺序写，记录实际历史读、原地冲突和地址边界。"
tags: [task.implementation, task.lookup, topic.memory, topic.precision, topic.programming_model]
status: draft
sources:
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/mem_cache/kpool_decode_update_and_maybe_write_cache.md
    role: primary
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_decode_update_and_maybe_write_cache.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/mem_cache/kpool_decode_update_and_maybe_write_cache.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/__init__.py
    role: supporting
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
created_at: "2026-11-09T10:20:49Z"
updated_at: "2026-11-09T10:20:49Z"
platforms: ["950"]
cann_versions: ["9.1.0"]
---

# KpoolDecodeUpdateAndMaybeWriteCache 950 Direct Invoke 算子知识

## 算子速览

`sgl_kernel_npu.implementation.triton.mem_cache.kpool_decode_update_and_maybe_write_cache.kpool_decode_update_and_maybe_write_cache` 每row更新有效请求tail；恰满pool时先以当前key/score覆盖逻辑当前槽做FP32逐通道softmax汇聚，按页表写BF16cache，最后才写当前tail。仅buf/tail_k/tail_score可变，None返回，无旋转/Hadamard/FP8量化。全部自有Host及三运行分支闭合，无dot/Cube，VV。

draft保留值域、历史容量、metadata/地址整数和并发别名未guard，公开arch35验证仅上游报告。已有[共同Kpool API](../../../../apis/sgl_kernel_npu/sgl_kpool_tail_cache.md)全文读并复用。

## 接口与语义

### 计算语义

Psize=pool_size，T=tail_capacity，D=head_dim，S=slots_per_page。valid=(req∈[0,Rreq))&&(out_cache_loc!=0)&&(0≤position<seq_len)。valid时当前key/score写tail[req,position%T]。若position%Psize=Psize-1，start=position-(position%Psize)，按s∈[0,Psize)读对应历史；当前s用直接输入替代。每通道h：score_s,h=history_or_current_score+ape[s,h]，softmax沿poolslot s（不沿通道），pooled_h=Σ softmax(score)_s,h*key_s,h，BF16写cache。

cache地址：pool_id=position//Psize，group=pool_id//S，table_col=clamp(group*Psize,0,BTcols-1)，page=int64(block_tables[row,table_col])，slot=pool_id%S，offset=page*BUF_NUMEL_PER_PAGE+slot*D+h。所谓packed_page在源中直接作页号，未解包位域；out_cache_loc只判断非0，不提供page地址。

### 输入、输出与属性

| 项 | 合同/Hostcheck |
|---|---|
| buf | BF16 contiguous，公开2D/4D页布局，stride0=S*D显式检查；页号值域调用方保证 |
| tail_k | BF16 contiguous[Rreq,T,D]，dtype/ndim/D检查；tail_score同shape连续，score支持BF16/FP32，无完整dtype检查 |
| key/slot_score | [B,D]，keyBF16显式check，slot_score BF16/FP32合同；内部各contiguous，但缺完整shape/deviceguard |
| ape | [Psize,D]shape检查，合同FP32，内部contiguous |
| block_tables | int32[B,BTcols]合同，内部contiguous；Host直接shape1，无全部dtype/范围检查 |
| 四metadata | req_pool_indices/positions/seq_lens/out_cache_loc至少B元素，同NPU整数，内部contiguous，无长度/值域全面检查 |
| scalar | Psize/T/S/BTcols正、D匹配tail；这些正域不全Host检查 |
| 返回/状态 | None；仅3状态可变，所有只读输入和元数据保持 |

### 入口与版本

Direct位置参数为buf,tail_k,tail_score,key,slot_score,ape,block_tables,req_pool_indices,positions,seq_lens,out_cache_loc，keyword-only pool_size,slots_per_page,head_dim=128。auto/triton只转发，无fallback；torch_native外部参考不补Device。SGLcommit `dda6d36b0cdb4081e102d14c0a2fb276fc416e69`，CANN9.1.0为README/CI配置非本次运行，完整Tritonbinary未固定。

## Host/Launcher 执行流程

### 参数校验与前处理

B=key.shape0，B0立即return在所有dtype/shapeassert前。非空checkbuf/tailK/key BF16、tail3D/score同shape/D/APEshape、三可变statecontiguous、bufstride0=S*D；不复制state。key/slot_score/APE/BT/四metadata分别contiguous，按真实rowstrides传Kernel，grid(B,)一program一row。无helper核数查询/deviceguard/Host索引值回读，assert可关闭。

### 参数、Workspace 与生命周期

无新outputallocation/GM统计scratch/请求方workspace/POD/ACLNN；只读连续化可有临时，任意复制项i的allocation为numel_i*d_i，逻辑额外读/写各相同字节，不虚构全部必copy。三个原地state始终持有原存储。copy→Kernel及state异步完成/释放归Torch/Triton，未显式stream/wait/event；并发调用不得修改本次读取历史或同目的cache。

### 启动图与失败传播

import→B0返回或asserts→只读copy→单JITKernel→None。所有算法自有Vector源码，无外部核心Torch数学；发生assert/copy/JIT/launch异常直接传播，无回滚/CPUfallback。package原生库导入是前提非图内算法。

## Route 与参数设计

### 分核与资源计算

grid(B,)，BLOCK_D=nextpow2D并maskoffs<D，非二次幂D可mask化。无效row不earlyreturn，仍metadata/currentload；只有压缩if和tailmask抑制状态更新。满pool两pass逐slot静态循环，逻辑向量max/acc/denom长度BD，不物化Psize×D tile/GM；循环展开/physical资源归compiler。

### Route 选择

| Route | 条件 | 状态修改 |
|---|---|---|
| H-000 | B0 | 无Kernel |
| R-001 | pos_validfalse | 无，但current/metadata读取 |
| R-002 | valid、slot≠Psize-1 | tailK/tailScore |
| R-003 | valid、slot=Psize-1 | poolcache后tailK/tailScore |

R-003对current槽仍先loadtail再where选择输入，副本值不参与结果不等于没有物理读。无可选norm/quant/rotate分支。

### 模板/实现执行矩阵

BF16key/tailK/cache，slot_score与tail_score公开各BF16/FP32兼容dtype实例，APEFP32；三个runtimevalidity类共用body。HEAD_DIM可正D且匹配tail，不将默认128误写为唯一Host许可。所有自有节点无dot/Cube/AIC/MIX，选VV。

### 隐藏性能 Guard

Psize/T/S/BTcols与Rreq容量要合法；safe_pos=max(pos,0)不能修复除0常量。reqclamp只使无效req地址尽量落范围，Rreq0并不生成有效state；invalidrowcurrentload仍要求真实storage。页表列被clamp不验证页号、out_cache_loc非0也不验证页号。需要完整历史表示（通用情况T≥Psize），所有tail地址req/pos乘stride未显式统一int64，只有page转int64确定；超大metadata/地址JIT域未guard。

### POD/ABI

| 字段 | 类别/消费 |
|---|---|
| buf_bf16_ptr/tail_k_ptr/tail_score_ptr | runtime可变state→cache写、history读/tail写 |
| key_ptr/slot_score_ptr/ape_ptr | runtime只读current/位置score |
| block_tables_ptr | runtimeint32table→页号 |
| req_pool_indices_ptr/positions_ptr/seq_lens_ptr/out_cache_loc_ptr | runtime四metadata，按row线性读取 |
| tail_k_stride_0/1、tail_score_stride_0/1 | runtime元素请求/slotstride，分别传入 |
| key_stride_0/slot_score_stride_0/ape_stride_0 | runtime只读元素rowstride |
| block_tables_stride_0/1 | runtimeBT二维元素stride |
| REQ_POOL_SIZE/BUF_NUMEL_PER_PAGE | constexprRreq/真实bufstride0 |
| POOL_SIZE/TAIL_SIZE/HEAD_DIM | constexprPsize/T/D |
| BLOCK_TABLE_COLS/SLOTS_PER_PAGE/BLOCK_D | constexprBTcols/S/nextpow2D |
| grid | (B,) |

无自定义序列化POD/字节offset，原始metadata dtype决定部分算术，page显式toint64，不能伪造全tail地址均64bit。

### Route 源码闭包

完整241行Direct/Device与public适配、mem_cache/backendinit已读；无额外自有helper。根setup→stage_runtime完整Python包→build_wheel/setup_refactor。exp/max/load/store/where为外部primitive，copy/empty框架边界不隐藏算法；无dot/Cube节点。

## Kernel 实现

### 公共执行流程

metadata→safe req/pos与validity→currentload→条件两pass历史汇聚/页表cachewrite→最后maskedtailwrite。当前token不用先写tail再读，避免当前更新和历史汇聚顺序被误解；无效请求只保证不修改状态。

### Route R-001：无效行仅加载当前数据

#### 适用条件

##### 选择证据

row<B，pos_valid=(0≤req_raw<Rreq)&&(out_cache_loc!=0)&&(0≤pos<seq_len)。本路线pos_validfalse；Psize/T/S/页表列数须正。Kernel并无早退无效行。

#### Device 数据流

##### 函数级调用链

`Direct→contiguous只读参数→_kpool_decode_update_and_maybe_write_cache_kernel→metadata/clamp→key/scoreFP32load→maskedofftailstore`。无自有helper/其它Kernel/dot/Cube。

##### 源码等价伪码

req=clamp(reqraw,0,Rreq-1)，safe_pos=max(pos,0)，slot=safe_pos%Psize，phys=safe_pos%T；所有行读当前key/score转FP32。跳pool分支，pos_validfalse。最后tail_k/tail_score在dim_mask&&pos_valid下store，因此无状态写，但当前key/score与metadata仍读。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/有效GM |
|---|---|
| 当前key/score | BLOCK_DFP32各一逻辑张量；每row读D*(2+dsc) B，连无效行也读 |
| metadata | 每row四标量req/pos/seqlen/cacheloc |
| tail写 | 0 |
| 历史/ape | 不读 |
| cache | 不读写 |
| workspace/physical UB | 无GM临时/请求方workspace，Vector逻辑BLOCK_D不等实际物理峰值 |

##### 分层内存布局

GMcurrent/metadata→FP32current[BD]→tailstoremaskfalse。不物化poolsize×D GM矩阵；原地状态持续由调用方持有。

##### 字节账与复用顺序

以全调用公式统一：B行metadata与当前输入读 `B*(dm_req+dm_pos+dm_seq+dm_loc+D*(2+dsc))`；V有效行tail写V*D*(2+dts)；C满pool有效行额外 `C*(Psize*D*(2dts+10)+4+2D)` B。本路线贡献V/C分别0/0每row。历史tail/ape读取已含当前槽被where丢弃的物理load，不能替成Psize-1。无workspace交接，当前tail更新/无效mask；并发rows/调用的state一致性由调用方保证。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 精度 | key/score/history/ape转FP32；无汇聚，tailstore转目标dtype |
| 读有效性 | 无效请求也读当前key/score与metadata，不能用pos_valid保护短输入storage |
| 历史 | 不读历史 |
| 页表 | 不读页表/不写cache |
| 尾列 | BLOCK_D=nextpow2D，maskoffs<D，loadother0/storemask；D可非二次幂 |
| 并发 | 无原子/barrier/锁；req/slot/cache目标写冲突和读历史/他行写交叠须外部排除 |
| 同步 | 同programSSA顺序交compiler，state完成/跨流交接依framework，无hostwait |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| validity/current | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_decode_update_and_maybe_write_cache.py#L43-L67) |
| 两pass/cache | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_decode_update_and_maybe_write_cache.py#L69-L145) |
| tail末尾更新 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_decode_update_and_maybe_write_cache.py#L147-L154) |


### Route R-002：有效行未满pool只写tail

#### 适用条件

##### 选择证据

row<B，pos_valid=(0≤req_raw<Rreq)&&(out_cache_loc!=0)&&(0≤pos<seq_len)。本路线pos_validtrue且safe_pos%Psize≠Psize-1；Psize/T/S/页表列数须正。Kernel并无早退无效行。

#### Device 数据流

##### 函数级调用链

`Direct→contiguous只读参数→_kpool_decode_update_and_maybe_write_cache_kernel→metadata/clamp→key/scoreFP32load→tailstore`。无自有helper/其它Kernel/dot/Cube。

##### 源码等价伪码

req=clamp(reqraw,0,Rreq-1)，safe_pos=max(pos,0)，slot=safe_pos%Psize，phys=safe_pos%T；所有行读当前key/score转FP32。跳pool分支。最后tail_k/tail_score在dim_mask&&pos_valid下store，当前数据写phys_slot。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/有效GM |
|---|---|
| 当前key/score | BLOCK_DFP32各一逻辑张量；每row读D*(2+dsc) B，连无效行也读 |
| metadata | 每row四标量req/pos/seqlen/cacheloc |
| tail写 | D*(2+dts) B |
| 历史/ape | 不读 |
| cache | 不读写 |
| workspace/physical UB | 无GM临时/请求方workspace，Vector逻辑BLOCK_D不等实际物理峰值 |

##### 分层内存布局

GMcurrent/metadata→FP32current[BD]→GMtail。不物化poolsize×D GM矩阵；原地状态持续由调用方持有。

##### 字节账与复用顺序

以全调用公式统一：B行metadata与当前输入读 `B*(dm_req+dm_pos+dm_seq+dm_loc+D*(2+dsc))`；V有效行tail写V*D*(2+dts)；C满pool有效行额外 `C*(Psize*D*(2dts+10)+4+2D)` B。本路线贡献V/C分别1/0每row。历史tail/ape读取已含当前槽被where丢弃的物理load，不能替成Psize-1。无workspace交接，当前tail更新/无效mask；并发rows/调用的state一致性由调用方保证。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 精度 | key/score/history/ape转FP32；无汇聚，tailstore转目标dtype |
| 读有效性 | 无效请求也读当前key/score与metadata，不能用pos_valid保护短输入storage |
| 历史 | 不读历史 |
| 页表 | 不读页表/不写cache |
| 尾列 | BLOCK_D=nextpow2D，maskoffs<D，loadother0/storemask；D可非二次幂 |
| 并发 | 无原子/barrier/锁；req/slot/cache目标写冲突和读历史/他行写交叠须外部排除 |
| 同步 | 同programSSA顺序交compiler，state完成/跨流交接依framework，无hostwait |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| validity/current | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_decode_update_and_maybe_write_cache.py#L43-L67) |
| 两pass/cache | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_decode_update_and_maybe_write_cache.py#L69-L145) |
| tail末尾更新 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_decode_update_and_maybe_write_cache.py#L147-L154) |


### Route R-003：有效行满pool先汇聚cache再写tail

#### 适用条件

##### 选择证据

row<B，pos_valid=(0≤req_raw<Rreq)&&(out_cache_loc!=0)&&(0≤pos<seq_len)。本路线pos_validtrue且safe_pos%Psize=Psize-1；Psize/T/S/页表列数须正。Kernel并无早退无效行。

#### Device 数据流

##### 函数级调用链

`Direct→contiguous只读参数→_kpool_decode_update_and_maybe_write_cache_kernel→metadata/clamp→key/scoreFP32load→两passpoolsoftmax/加权→页表/BF16cache→tailstore`。无自有helper/其它Kernel/dot/Cube。

##### 源码等价伪码

req=clamp(reqraw,0,Rreq-1)，safe_pos=max(pos,0)，slot=safe_pos%Psize，phys=safe_pos%T；所有行读当前key/score转FP32。start=safe_pos-slot；pass1遍历poolslot，tail_score[(start+s)%T]仍先load，当前槽用score_current替换，加ape，求逐通道max；pass2重复score/ape再读tailK，当前槽用key替换，acc+=k*exp(score-max)，denom+=exp；compressedBF16写到页表给出的page/slot。最后tail_k/tail_score在dim_mask&&pos_valid下store，当前数据写phys_slot。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/有效GM |
|---|---|
| 当前key/score | BLOCK_DFP32各一逻辑张量；每row读D*(2+dsc) B，连无效行也读 |
| metadata | 每row四标量req/pos/seqlen/cacheloc |
| tail写 | D*(2+dts) B |
| 历史/ape | Psize*D*(2dts+2+8) B读，含current槽物理load再替换 |
| cache | 页表int32一项4B读，compressed BF16 D*2B写 |
| workspace/physical UB | 无GM临时/请求方workspace，Vector逻辑BLOCK_D不等实际物理峰值 |

##### 分层内存布局

GMtailScore/APE→FP32max[BD]；第二遍同score+GMtailK/current→FP32acc/denom[BD]→BF16GMcache，最后current→GMtail。不物化poolsize×D GM矩阵；原地状态持续由调用方持有。

##### 字节账与复用顺序

以全调用公式统一：B行metadata与当前输入读 `B*(dm_req+dm_pos+dm_seq+dm_loc+D*(2+dsc))`；V有效行tail写V*D*(2+dts)；C满pool有效行额外 `C*(Psize*D*(2dts+10)+4+2D)` B。本路线贡献V/C分别1/1每row。历史tail/ape读取已含当前槽被where丢弃的物理load，不能替成Psize-1。无workspace交接，压缩读取历史先于当前tail覆盖；并发rows/调用的state一致性由调用方保证。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 精度 | key/score/history/ape转FP32；逐通道稳定softmax weighted key，acc/denom后BF16cache，tailstore转目标dtype |
| 读有效性 | 无效请求也读当前key/score与metadata，不能用pos_valid保护短输入storage |
| 历史 | 需要除当前token外完整Psize-1个逻辑历史有效；tail容量应能表示所需历史且无并发覆盖，当前槽虽读但where替换 |
| 页表 | token_page_row被clamp到合法表列，但packed_page值未校验，必须指向真实buf页 |
| 尾列 | BLOCK_D=nextpow2D，maskoffs<D，loadother0/storemask；D可非二次幂 |
| 并发 | 无原子/barrier/锁；req/slot/cache目标写冲突和读历史/他行写交叠须外部排除 |
| 同步 | 同programSSA顺序交compiler，state完成/跨流交接依framework，无hostwait |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| validity/current | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_decode_update_and_maybe_write_cache.py#L43-L67) |
| 两pass/cache | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_decode_update_and_maybe_write_cache.py#L69-L145) |
| tail末尾更新 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_decode_update_and_maybe_write_cache.py#L147-L154) |

## 算子特定优化

### Trick T-001：当前SSA值替代历史槽，压缩后才写tail

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_decode_update_and_maybe_write_cache.py#L116-L125)：

```python
            k_buf = tl.load(
                tail_k_ptr + req * tail_k_stride_0 + phys * tail_k_stride_1 + offs,
                mask=dim_mask,
                other=0.0,
            ).to(tl.float32)
            k = tl.where(is_current, key, k_buf)
            acc += k * prob

        # BF16: no Hadamard, no FP8 quantize — just write directly
        compressed = (acc / denom).to(tl.bfloat16)
```

末尾tail更新在147–154行，先压缩/页表write后tailstore是实际顺序。

#### 机制与设计原因

直接当前key/score与历史行拼成完整pool，避免必须依赖先写tail再从GM取当前值；但source仍load当前槽后where替换，未减少该物理load。无性能量测。

#### 迁移边界

其余历史有效且无并发覆盖；原地tail/cache写集外部排冲突，不用tl.where证明不读被丢弃地址。

#### 错误做法

在字节账删掉current槽tail读、或将tailupdate搬到历史读前导致覆盖仍需的环形槽。

### Trick T-002：pool位置到token页表列的映射

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_decode_update_and_maybe_write_cache.py#L127-L143)：

```python
        # Compute write location in buf
        pool_id = safe_pos // POOL_SIZE
        pool_page_group = pool_id // SLOTS_PER_PAGE
        token_page_row = pool_page_group * POOL_SIZE
        token_page_row = tl.minimum(tl.maximum(token_page_row, 0), BLOCK_TABLE_COLS - 1)
        packed_page = tl.load(
            block_tables_ptr
            + row * block_tables_stride_0
            + token_page_row * block_tables_stride_1,
        )
        loc_page_index = packed_page.to(tl.int64)
        loc_token_offset_in_page = pool_id % SLOTS_PER_PAGE
        out_k_offsets = (
            loc_page_index * BUF_NUMEL_PER_PAGE
            + loc_token_offset_in_page * HEAD_DIM
            + offs
        )
```

#### 机制与设计原因

先pool_id/S分page组，再乘Psize索引token页表列，clamp表列；rawpage转int64形成扁平cacheoffset。此映射不同于用out_cache_loc直接当地址。

#### 迁移边界

正Psize/S/BTcols、真实页号/buf容量及stride0=S*D，clamp仅保护表列范围不保证page值合法。

#### 错误做法

丢失token_page_row的Psize乘数、把packed_page自行按位解包，或把out_cache_loc作pooledslot。

## 模板与实现对比

三runtime分支、空BHost及全部只读copy闭合；BF16汇聚无Hadamard/FP8/scale，不能因旧FP8注释自行加入不同数学。current/metadata无效行仍读，score储存dtype可影响后续历史精度，不能把两个score类型简化为同storage。

## 平台差异

本卡950归属arch35；公开arch22支持、arch35已验证是上游报告非本次复测，README/architectures映射A2/A3、950。自有body无hardware分支，CANN9.1.0 CI配置非compiler/physical资源一致性证明。

## 限制与失败边界

Device值域、页号、历史容量/有效性、跨rowstate读写冲突和alias未完整guard；metadata短storage不能靠pos_valid保护current读。整数/physical资源与非有限softmax边界外部，未构建、上游运行、测试或校验/真机/性能，draft保留条件不作并发安全推荐。

## 源码索引

### 链路索引

| 阶段/源码 | 符号 | 事实 |
|---|---|---|
| [公开合同](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/mem_cache/kpool_decode_update_and_maybe_write_cache.md) | `kpool_decode_update_and_maybe_write_cache` | 有效请求/FP32poolsoftmax/页表BF16写/平台 |
| [Direct/Device](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/kpool_decode_update_and_maybe_write_cache.py) | `kpool_decode_update_and_maybe_write_cache/_kpool_decode_update_and_maybe_write_cache_kernel` | 完整241行/三运行分支 |
| [公开转发](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/mem_cache/kpool_decode_update_and_maybe_write_cache.py) | `_triton_impl` | 参数转发，无回退 |
| [mem_cache包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/__init__.py) | `module init` | 无Device |
| [import边界](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py) | `_load_sgl_kernel_npu` | torch_npu/原生库与vendor初始化 |
| [backend包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/__init__.py) | `module init` | 懒加载包，无另一Device节点 |
| [构建入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/setup.py) | `main` | 完整Python wheel路径；本次未构建 |
| [源码打包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/build_tools/torch_wheel.py) | `stage_runtime/build_torch/build_wheel/setup_refactor` | 复制完整Python包、原生运行库与wheel |
| [平台/包说明](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md) | `REFACTOR/arch22/35 mapping` | 全部Python实现包含、产品映射、CANN9.1.0构建例 |
| [产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json) | `2201/3510` | a2/a3/950对应构建族 |
| [版本配置](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernels.yml) | `test-norm-ops` | CANN9.1.0/a3/950配置，非本次运行 |
| [CI消费](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernel-group.yml) | `run-kernel-group` | 对应版本容器/测试组参数 |

### 实现复用检查

冻结117/legacy共同KpoolAPI已全文读并链接，此唯一decodeOperator不并入scatter/assembly/prefill写tail等其它数学。全部固定同repo一primary，无verified。
