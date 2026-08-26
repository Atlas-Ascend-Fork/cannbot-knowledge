---
type: Operator
title: "UnsortedSegmentSum A5 Direct Invoke 算子知识"
description: "说明 launch_unsorted_segment_sum 在 A5 上的接口语义、Launcher 参数生成、15 条 Route、启动图与逐节点实现。"
tags: [task.implementation, task.lookup, topic.data_movement, topic.memory, topic.precision, topic.programming_model]
status: stable
verified:
  - by: process:ops-knowledge-route-priority
    at: "2026-08-25T20:47:20Z"
  - by: process:ops-knowledge-direct53-ingest
    at: "2026-08-25T20:03:11Z"
sources:
  - resource: https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/index/unsorted_segment_sum/README.md
    role: header
  - resource: https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/index/unsorted_segment_sum/CMakeLists.txt
    role: implementation
  - resource: https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/index/unsorted_segment_sum/op_host/unsorted_segment_sum_def.cpp
    role: implementation
  - resource: https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/index/unsorted_segment_sum/op_host/arch35/unsorted_segment_sum_tiling_base.cpp
    role: implementation
  - resource: https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/index/unsorted_segment_sum/op_host/arch35/unsorted_segment_sum_simt_tiling.h
    role: header
  - resource: https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/index/unsorted_segment_sum/op_host/arch35/unsorted_segment_sum_simt_tiling.cpp
    role: implementation
  - resource: https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/index/unsorted_segment_sum/op_host/arch35/unsorted_segment_sum_simd_non_sort_tiling.cpp
    role: implementation
  - resource: https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/index/unsorted_segment_sum/op_kernel/arch35/unsorted_segment_base.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/index/unsorted_segment_sum/op_kernel/arch35/unsorted_segment_sum.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/index/unsorted_segment_sum/op_kernel/arch35/uss_simd_non_sort.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/index/unsorted_segment_sum/op_kernel/arch35/uss_simd_split_col.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/index/unsorted_segment_sum/op_kernel/unsorted_segment_sum_apt.cpp
    role: implementation
created_at: "2026-08-25T19:30:50Z"
updated_at: "2026-08-25T20:47:20Z"
platforms: ["950"]
cann_versions: ["9.1.0"]
---

# UnsortedSegmentSum A5 Direct Invoke 算子知识

## 算子速览

| 项目 | 内容 |
|---|---|
| 实际入口 | <code>cann_bench::unsorted_segment_sum</code> → <code>unsorted_segment_sum_npu</code> → <code>launch_unsorted_segment_sum</code>；Direct Invoke |
| 计算语义 | data[N,*tail] 按一维 segment_ids[N] 分段求和，空段为 0 |
| 输入输出 | Direct 子域：data 为 FP16/BF16/FP32/INT32/INT64，ids 为 INT32/INT64，rank 1..8，输出 [num_segments,*tail] |
| 执行类型 | AIV_VECTOR 或 AIV-only entry 内 <code>asc_vf_call</code> 的 SIMT；无 AIC/Cube、无 MIX_CV |
| Kernel 路线 | R-001～R-015；1、2 或 3 Kernel |
| 核心资源 | GM data/ids/output；low FP32 accumulator；FP32 partials；显式 TBuf 峰值 192 KiB |
| 来源闭包 | direct_implementation_closed：plugin、POD、blockDim、全部可达分支、entry/body、stream 边和构建接线闭合 |
| 验证状态 | 已完成源码闭包检查；本次知识提取未执行编译、真机、数值或性能测试。 |

Frontmatter 只列固定 Commit 的官方 A5/arch35 相关源码，证明公开语义、平台接线及 SIMT/SIMD 转换基线。后文“交付 Direct”事实来自最终非官方 Direct 转换源码；它们不是官方 TilingKey，也没有伪造交付 URL。

## 接口与语义

### 计算语义

令 <code>N=data.shape[0]</code>、<code>A=Π data.shape[1:]</code>、<code>S=num_segments</code>：

~~~text
y[s,a] = Σ data[n,a],  n∈[0,N) and segment_ids[n]=s
~~~

每个可达 body 在形成地址前检查 <code>id&lt;0 || id&gt;=S</code>，非法 id 跳过。FP16/BF16 在 FP32 中累加后一次 CAST_RINT；其余保持本 dtype。官方 README 还公开 UINT32/UINT64，但 Direct 不支持。

### 输入、输出与属性

| 参数 | shape/layout | dtype | 约束、默认值与语义 |
|---|---|---|---|
| data | [N,*tail]，转 contiguous | FP16/BF16/FP32/INT32/INT64 | rank 1..8 |
| segment_ids | [N]，转 contiguous | INT32/INT64 | 一维且长度 N；值域 Device 防护 |
| num_segments | Host 标量 | INT64 | S&gt;0；不同于官方 tensor ABI |
| y | [S,*tail]，ND contiguous | 同 data | 分段和，空段 0 |
| accumulator | 内部 GM | FP32 | low 为 [S,*tail]；R-004 为 [blockDim] |

### 入口与版本

官方 README、OpDef 和 CMake 把算子接到 <code>ascend950</code>/<code>arch35</code>。本卡覆盖 CANN 9.1.0、A5/950 Direct：Torch PrivateUse1 取 current NPU stream，经 <code>OpCommand::RunOpApi</code> 调 launcher。官方图 kernel 按 1000/5000/6000 等 key 路由；Direct 不消费这些 key，而按 dtype/shape 自定义分发。

## Host/Launcher 执行流程

### 参数校验与前处理

依次检查 rank/首维/S/dtype；data/ids contiguous；计算 N、A、S；创建 y；计算 tiling；low 分配 FP32 [S,*tail]，R-004 分配 FP32 [blockDim]；取 current stream 后 launch。无显式 same-device、shape 乘积溢出或 UB capacity 检查。

### 参数、Workspace 与生命周期

令 <code>C=max(GetCoreNumAiv(),1)</code>、<code>I=N*A</code>、<code>O=S*A</code>、<code>Binit=4</code>（low）或 data bytes：

~~~text
computeCores=min(ceil(I/2048),C)
perCoreInit=max(ceil(O/C),2048/Binit)
initCores=min(ceil(O/perCoreInit),C)
blockDim=max(1,max(computeCores,initCores))
~~~

low workspace=<code>4*O</code> B；R-004=<code>4*blockDim</code> B。allocator 物理对齐不可见。POD 按值传 Device，外层 launch struct 只在 Host bridge 使用。

### 启动图与失败传播

~~~text
R001/002/003: compute
R004: partial -> partials -> finish
R005/006..010: init FP32 -> compute -> cast
R011/012/013/014: init output -> compute
R015: SIMT init -> SIMT compute
~~~

节点均在同一 stream，无显式 event。launcher 为 void、Host lambda 固定返回 0，异步 fault 和 tensor 生命周期的最终保证属于框架边界。

## Route 与参数设计

### 分核与资源计算

各 body 用 <code>ceil(extent/blockDim)</code> 分行、列或 flattened 元素，空核返回。Vector 列域按 32 B 对齐但 GM 尾写只用有效 elements；SIMT 固定 2048 lanes。常量：wide=256 B，vector tile=8192，cast tile=16384，low small N/S=4，FP32 small N/S=16，hist N≥65536/S≤4096/window=1024，FP32 vector A≥256，INT64 column A≥512。

### Route 选择

#### 重要性顺序

下表的 P0→P2 只定义知识卡的阅读与复用优先级，不改变 launcher 的运行时选择顺序。

| 优先级 | Route | Route 特征 | 复用时首先锁定 | Host 位置 |
|---|---|---|---|---|
| P0 | R-011 | FP32/INT32 宽尾主干；2D MTE + native vector atomic | 256 B/256 elements 门槛、batch4、128 KiB dataBuf | dtype 主分支 |
| P0 | R-006 | low+INT32 中宽尾；batch8×tile4096，FP32 workspace | 192 KiB allocation、升精度与一次降精度 | low wide 分支 |
| P0 | R-001 | low 小 N/S 超宽尾；列独占、UB FP32 累加 | N/S guard、176 KiB UB、无 GM atomic | 顶层 if-1 |
| P0 | R-005 | low 标量长行域；1024-bin window histogram | window owner、UB/GM 两级 atomic、cast 边 | low histogram 分支 |
| P1 | R-003 | INT64 宽尾列独占；SIMT 直接 GM 累加 | A≥512、列域互斥、无 init kernel | 顶层 if-3 |
| P1 | R-002 | FP32 小 N/S 宽尾；列独占 UB 累加 | N/S≤16、64 KiB UB、一次写回 | 顶层 if-2 |
| P1 | R-004 | FP32 单段标量；partial→finish 两阶段归约 | 32 B blockSum、partials lifetime、barrier | 顶层 if-4 |
| P1 | R-007 | low+INT32 长尾；batch4×tile8192 | 2D stride、192 KiB allocation | low wide 分支 |
| P1 | R-008 | low+INT64 中长尾；batch2×tile8192 | INT64 id guard、active/allocated UB 区分 | low wide 分支 |
| P1 | R-009 | low+INT64 超长尾；batch1×tile8192 | 单行复用、exact-byte tail | low wide 分支 |
| P2 | R-010 | low 短尾通用 SIMT；FP32 GM atomic | flattened row 映射、three-kernel ordering | low fallback |
| P2 | R-012 | FP32 短尾 u32 specialization | magic/shift producer、u32 guard | FP32 branch |
| P2 | R-014 | INT32 短尾通用 SIMT | native integer atomic、zero edge | INT32 fallback |
| P2 | R-015 | INT64 短尾通用 SIMT | SIMT zero、INT64 atomic、stream edge | INT64 fallback |
| P2 | R-013 | FP32 超 u32 flattened 域 fallback | power-of-two/u32/u64 地址映射 | FP32 final fallback |

#### Host 真实选择顺序

| 顺序 | Route | Key/模板 | 精确选择条件与优先级 | 不适用去向 |
|---:|---|---|---|---|
| 1 | R-001 low small-owned | Direct if-1 | low,N≤4,S≤4,A≥128 | 2 |
| 2 | R-002 FP32 small-owned | if-2 | FP32,N≤16,S≤16,A≥64 | 3 |
| 3 | R-003 INT64 column | if-3 | INT64,A≥512 | 4 |
| 4 | R-004 single reduce | if-4 | FP32,S=A=1 | dtype 分支 |
| 5 | R-005 low histogram | low-1 | low,A=1,S≤4096,N≥65536 | wide |
| 6 | R-006 low vec i32-short | low-2a | low+i32,128≤A≤4096,非R001 | 后序 |
| 7 | R-007 low vec i32-long | low-2b | low+i32,A&gt;4096,非R001 | 后序 |
| 8 | R-008 low vec i64-mid | low-2c | low+i64,128≤A&lt;8192,非R001 | 后序 |
| 9 | R-009 low vec i64-long | low-2d | low+i64,A≥8192,非R001 | 后序 |
| 10 | R-010 low SIMT | low fallback | low,非R001/R005,A&lt;128 | 终点 |
| 11 | R-011 native vector | FP32/INT32 | FP32 A≥256非R002；INT32 A≥64 | SIMT |
| 12 | R-012 FP32 magic | FP32 | 非前序,A&lt;256,I≤UINT32_MAX | R013 |
| 13 | R-013 FP32 generic | FP32 | 非前序,A&lt;256,I&gt;UINT32_MAX | 终点 |
| 14 | R-014 INT32 generic | INT32 | A&lt;64 | 终点 |
| 15 | R-015 INT64 generic | INT64 | A&lt;512 | 终点 |

~~~text
if R001; else if R002; else if R003; else if R004;
else low: histogram -> four wide subroutes -> SIMT
else FP32: vector -> magic32 -> generic64
else INT32: vector -> generic
else INT64: generic
~~~

### 模板/实现执行矩阵

| Route | key/selector | dtype/shape/platform 完整命中条件 | 执行拓扑与 Kernel 节点 | 实际模板/body | 内存与同步特征 | tail/fallback |
|---|---|---|---|---|---|---|
| R-011 | FP32/INT32 vector | FP32 A≥256且非R-002；INT32 A≥64；A5 | init→vector | NativeRowVectorScatter | init 32 KiB；scatter 128 KiB；stream+GM atomic | 8192-element exact tail |
| R-006 | low i32 short | low+i32，128≤A≤4096，非R-001；A5 | init→vec→cast | LowRowVectorScatter batch8,tile4096 | 192 KiB；4*O GM；PIPE+stream | R-010 / exact bytes |
| R-001 | top if-1 | low，N/S≤4，A≥128；A5 | single Vector | SmallRowsVectorOwned | 176 KiB；列独占 | 8192 tail / 后续 Host 判断 |
| R-005 | low histogram | low，A=1，S≤4096，N≥65536；A5 | init→hist→cast | HistogramScatter/Chunk | peak 96 KiB；UB/GM atomic；stream | 1024-bin window / low fallback |
| R-003 | top if-3 | INT64，A≥512；A5 | single SIMT | NativeColumnOwnedVf | GM 直访；列独占 | thread-stride / INT64 fallback |
| R-002 | top if-2 | FP32，N/S≤16，A≥64；A5 | single Vector | SmallNativeVectorOwned | 64 KiB；列独占 | 8192 tail / 后续 Host 判断 |
| R-004 | top if-4 | FP32，S=A=1；A5 | partial→finish | two reduce VF | 32 B UB + 4*blockDim GM；barrier+stream | empty block partial=0 |
| R-007 | low i32 long | low+i32，A>4096，非R-001；A5 | init→vec→cast | batch4,tile8192 | 192 KiB；4*O GM | exact bytes / R-010 |
| R-008 | low i64 mid | low+i64，128≤A<8192，非R-001；A5 | init→vec→cast | batch2,tile8192 | 192 KiB allocated；4*O GM | exact bytes / R-010 |
| R-009 | low i64 long | low+i64，A≥8192，非R-001；A5 | init→vec→cast | batch1,tile8192 | 192 KiB allocated；4*O GM | exact bytes / R-010 |
| R-010 | low fallback | low，非R-001/R-005，A<128；A5 | init→SIMT→cast | Fp32ScatterVf | peak 96 KiB；4*O GM；atomic+stream | flattened tail |
| R-012 | FP32 magic | FP32，前序未命中，A<256，I≤UINT32_MAX；A5 | init→SIMT | NativeScatterMagicF32Vf | init 32 KiB；GM atomic | u32 domain / R-013 |
| R-014 | INT32 fallback | INT32，A<64；A5 | init→SIMT | NativeScatterVf<int32,Index> | init 32 KiB；GM atomic | flattened tail |
| R-015 | INT64 fallback | INT64，A<512；A5 | SIMT init→SIMT | ZeroOutputVf/NativeScatterVf | no explicit TBuf；stream+atomic | flattened tail |
| R-013 | FP32 final fallback | FP32，前序未命中，A<256，I>UINT32_MAX；A5 | init→SIMT | NativeScatterVf<float,Index> | init 32 KiB；GM atomic | u64-capable tail |

### 隐藏性能 Guard

| Guard | Host/Tiling 条件 | Device/资源原因 | 影响 Route | 不满足时去向 | 源码符号 |
|---|---|---|---|---|---|
| wide | low 2*A≥256；INT32 4*A≥256 | 2D MTE/vector atomic | R001/006..011 | SIMT | wideTail |
| column | small N/S 或 INT64 A≥512 | 消除atomic | R001..003 | 后序 | if-1..3 |
| hist | A=1,N≥65536,S≤4096 | 每核1024 bins | R005 | 后序 | localHistogram |
| hist coverage | 隐含 blockDim≥ceil(S/1024) | window必须有owner | R005 | 无fallback | HistogramScatter |
| low UB | 固定32768 low+32768 float | 192 KiB | R006..009 | 无IsCapable | LowRowVectorScatter |
| magic | I≤u32 | u32 index | R012 | R013 | magic entry |
| id | id&lt;0 or id≥S | 防越界 | 全部 | skip | bodies |
| ordering | same stream | 节点GM可见性 | multi-kernel | 无event fallback | launcher |

### POD/ABI

| 结构 | 字段 | 类型/位宽 | ABI 布局 | 单位 | Host/launcher producer | Device consumer | 边界 |
|---|---|---|---|---|---|---|---|
| SimtTilingData | inputOuterDim | u64/64 | sizeof32,align8,off0 | rows | =N | loops | N*A unchecked |
| 同上 | outputOuterDim | u64/64 | off8 | segments | =S | guard/address | S&gt;0 |
| 同上 | innerDim | u64/64 | off16 | elements | =A | route/address | unchecked |
| 同上 | maxThread | u64/64 | off24 | lanes | =2048 | VF launch | some entries constant |
| LaunchTiling | data | struct/256 | sizeof40,align8,off0 | POD | calc | launcher | Host-only |
| 同上 | blockDim | u32/32 | off32+4B tail padding | blocks | formula | grid/partials | C=0→1 |

### Route 源码闭包

| Route | Key/selector | Host/Tiling producer | POD/参数 | Kernel entry/router 节点 | Kernel body/直接依赖 | 构建接线 |
|---|---|---|---|---|---|---|
| R-011 | native vector | 交付 launcher | td | init→vec entries | NativeRowVectorScatter | Direct CMake |
| R-006 | low i32 short | launcher+body selector | td,acc | init→vec_i32→cast | LowRowVectorScatter | 同上 |
| R-001 | if-1 | launcher | td,tags | small entries | SmallRowsVectorOwned | 同上 |
| R-005 | histogram | launcher | td,acc | init→hist→cast | HistogramScatter/Chunk | 同上 |
| R-003 | if-3 | launcher | td | col_i64 entries | NativeColumnOwnedVf | 同上 |
| R-002 | if-2 | launcher | td | owned_f32 entries | SmallNativeVectorOwned | 同上 |
| R-004 | if-4 | plugin+launcher | N,blockDim | partial→finish | two reduce VF | 同上 |
| R-007 | low i32 long | launcher+body selector | td,acc | init→vec_i32→cast | LowRowVectorScatter | 同上 |
| R-008 | low i64 mid | launcher+body selector | td,acc | init→vec_i64→cast | LowRowVectorScatter | 同上 |
| R-009 | low i64 long | launcher+body selector | td,acc | init→vec_i64→cast | LowRowVectorScatter | 同上 |
| R-010 | low fallback | launcher | td,acc | init→acc→cast | Fp32ScatterVf | 同上 |
| R-012 | FP32 magic | launcher | td | init→magic entries | MagicF32Vf | 同上 |
| R-014 | INT32 generic | launcher | td | init→native_i32 | NativeScatterVf | 同上 |
| R-015 | INT64 generic | launcher | td | simt-init→native_i64 | Zero/NativeScatterVf | 同上 |
| R-013 | FP32 generic | launcher | td | init→native_f32 | NativeScatterVf | 同上 |

交付定义但 launcher 不可达的 <code>uss_native_f16/bf16</code>、<code>uss_init_f16/bf16</code>、<code>uss_single_f32_*</code>、<code>uss_col_f32/i32/low_*</code> 不构成 Route。

## Kernel 实现

### 公共执行流程

全部 entry 为 AIV_ONLY。Vector body 使用 TPipe/TBuf、DataCopyPad、Duplicate/Cast/Add 与 PIPE_ALL；SIMT 由 entry 以 2048 lanes 启动。地址统一为 <code>data[n*A+a]</code> 和 <code>output[id*A+a]</code>。atomic Route 先零 GM；列所有权 Route 自行写零并独占列；low 多节点只写 FP32 accumulator，最终 cast 写 y。

### Route R-011：Native Row-Vector

#### 适用条件
##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Direct | 交付 kernel.cpp | FP32/INT32 branches | FP32 A≥256非R002；INT32 A≥64 | uss_vec_* |

#### Device 数据流
##### 函数级调用链

~~~text
VectorZeroOutput<T> -> NativeRowVectorScatter<T,Index>(batch4,tile8192)
~~~

##### 源码等价伪码

zero y；4-row 2D CopyIn；valid id => native vector atomic UB row to y[id]。

#### 内存与数据搬运
##### 资源与搬运表

| 缓冲区 | offset/容量 | dtype | producer→consumer | lifetime/复用 |
|---|---|---|---|---|
| init/dataBuf/y | 32/128 KiB / id*A+off | FP32/INT32 | zero→Copy→atomic | two nodes |

##### 分层内存布局

~~~mermaid
block-beta
  columns 2
  init["init 32 KiB"]
  scatter["data 128 KiB"]
~~~

##### 字节账与复用顺序

~~~text
peak UB=128 KiB; workspace=0
~~~

| 复用子区 | 写入者 | 读取者 | 下一覆盖 | 依据 | 条件 |
|---|---|---|---|---|---|
| dataBuf/y | Copy/zero+atomic | MTE3/caller | batch/call | PIPE_ALL/stream | AtomicNone |

#### 同步、精度与尾块
##### 同步与数值边界表

| 阶段 | 机制 | 保护对象 | 精度/尾块 |
|---|---|---|---|
| vector atomic | SetAtomicAdd<T> | repeated ids | native dtype；exact bytes |

#### 关键实现
##### 符号证据表

| 阶段 | 文件 | 符号 | 实现事实 |
|---|---|---|---|
| Host/entry/body | 交付 kernel.cpp | vector branch / NativeVector entries / RowVectorScatter | two kernels |

### Route R-006：Low Row-Vector INT32 Short

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Direct | 交付 kernel.cpp | LowRowVectorScatter | i32,128≤A≤4096 | batch8,tile4096 |

#### Device 数据流

##### 函数级调用链

~~~text
init FP32 -> uss_vec_low_i32 -> LowRowVectorScatter -> cast
~~~

##### 源码等价伪码

~~~text
8-row 2D CopyIn; cast aligned rows FP32; valid id => vector atomic acc; final RINT
~~~

#### 内存与数据搬运

##### 资源与搬运表

| 缓冲区 | offset/容量 | dtype | producer→consumer | lifetime/复用 |
|---|---|---|---|---|
| low/float/acc | row*align:64+128 KiB / id*A+off:4*O | low/FP32 | MTE→Cast→atomic→cast | batch/call |

##### 分层内存布局

~~~mermaid
block-beta
  columns 2
  low["low 64 KiB"]
  fp["fp32 128 KiB"]
~~~

##### 字节账与复用顺序

~~~text
scatter UB=192 KiB; init=32 KiB; cast=96 KiB; workspace=4*O B
~~~

| 复用子区 | 写入者 | 读取者 | 下一覆盖 | 依据 | 条件 |
|---|---|---|---|---|---|
| batch buffers | Copy/Cast | atomic MTE3 | next batch | PIPE_ALL/AtomicNone | write complete |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | 机制 | 保护对象 | 精度/尾块 |
|---|---|---|---|
| 2D MTE/atomic | exact blockLen, padded UB stride | row tile | padding not written to GM |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号 | 实现事实 |
|---|---|---|---|
| Host/entry/body | 交付 kernel.cpp | low wide / vec_i32 / LowRowVectorScatter | batch8/tile4096 |

### Route R-001：Low 小 N/S 列所有权

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Direct | 交付 kernel.cpp | launcher if-1 | low,N/S≤4,A≥128 | uss_small_* |

#### Device 数据流

##### 函数级调用链

~~~text
uss_small_* -> SmallRowsVectorOwned -> Duplicate sums -> CopyIn/Cast/Add -> Cast/CopyOut
~~~

##### 源码等价伪码

~~~text
owned column tile: zero sum[S]; scan N in order; valid id => sum[id]+=float(row); cast_rint each S once
~~~

#### 内存与数据搬运

##### 资源与搬运表

| 缓冲区 | offset/容量 | dtype | producer→consumer | lifetime/复用 |
|---|---|---|---|---|
| low/float/sum TBuf | 0:16 KiB / 0:32 KiB / s*8192:128 KiB | low/FP32 | MTE→Cast→Add→Cast→MTE3 | row/tile |

##### 分层内存布局

~~~mermaid
block-beta
  columns 3
  low["low 16 KiB"]
  fp["fp32 32 KiB"]
  sum["sum 128 KiB"]
~~~

##### 字节账与复用顺序

~~~text
UB=176 KiB; workspace=0; PIPE_ALL 后覆盖 low/float，tile 完成后覆盖 sum
~~~

| 复用子区 | 写入者 | 读取者 | 下一覆盖 | 依据 | 条件 |
|---|---|---|---|---|---|
| low/float/sum | Copy/Cast/Add | next stage | next row/tile | PIPE_ALL | 消费完成 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | 机制 | 保护对象 | 精度/尾块 |
|---|---|---|---|
| pipeline | PIPE_ALL+列独占 | UB/y | low→FP32，输入顺序加，一次RINT；有效elements写 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号 | 实现事实 |
|---|---|---|---|
| Host/entry/body | 交付 kernel.cpp | if-1 / uss_small_* / SmallRowsVectorOwned | 完整单节点 |

### Route R-005：Low 局部 Histogram

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Direct | 交付 kernel.cpp | localHistogram | low,A=1,S≤4096,N≥65536 | init→hist→cast |

#### Device 数据流

##### 函数级调用链

~~~text
VectorZeroOutput -> LocalHistogramScatter -> LocalHistogramChunkVf -> vector atomic merge -> VectorCastFromFp32
~~~

##### 源码等价伪码

~~~text
zero acc; block owns 1024-bin window+row slice; SIMT atomic UB; vector atomic UB->GM; final cast
~~~

#### 内存与数据搬运

##### 资源与搬运表

| 缓冲区 | offset/容量 | dtype | producer→consumer | lifetime/复用 |
|---|---|---|---|---|
| init/hist/cast UB | 0:32/4/96 KiB | FP32/low | three nodes | per-node |
| accumulator | window*1024 / 4*S B | FP32 | init/hist→cast | call |

##### 分层内存布局

~~~mermaid
block-beta
  columns 3
  init["init 32 KiB"]
  hist["hist 4 KiB"]
  cast["cast 96 KiB"]
~~~

##### 字节账与复用顺序

~~~text
peak UB=96 KiB; workspace=4*S B
~~~

| 复用子区 | 写入者 | 读取者 | 下一覆盖 | 依据 | 条件 |
|---|---|---|---|---|---|
| histogram/acc | SIMT/GM atomic | merge/cast | node/call end | PIPE_ALL/stream | window owner |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | 机制 | 保护对象 | 精度/尾块 |
|---|---|---|---|
| hist | UB atomic+GM vector atomic | FP32 acc | window tail≤1024；one RINT |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号 | 实现事实 |
|---|---|---|---|
| Host/entry/body | 交付 kernel.cpp | predicate / uss_hist_* / HistogramScatter/Chunk | three kernels |

### Route R-003：INT64 列所有权

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Direct | 交付 kernel.cpp | if-3 | INT64,A≥512 | uss_col_i64_* |

#### Device 数据流

##### 函数级调用链

~~~text
uss_col_i64_* -> AIV column partition -> NativeColumnOwnedVf(2048)
~~~

##### 源码等价伪码

~~~text
each thread owns a: zero y[:,a]; scan N; valid id => y[id,a]+=data[n,a]
~~~

#### 内存与数据搬运

##### 资源与搬运表

| 缓冲区 | offset/容量 | dtype | producer→consumer | lifetime/复用 |
|---|---|---|---|---|
| GM data/y | n*A+a / s*A+a，scalar | INT64 | caller→thread→caller | column unique |

##### 分层内存布局

N/A：SIMT registers + GM，无 InitBuffer。

##### 字节账与复用顺序

~~~text
explicit UB=0; workspace=0
~~~

| 复用子区 | 写入者 | 读取者 | 下一覆盖 | 依据 | 条件 |
|---|---|---|---|---|---|
| y[:,a] | owner thread | same thread | next row | ownership | columns disjoint |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | 机制 | 保护对象 | 精度/尾块 |
|---|---|---|---|
| zero/add | thread order | column | INT64；no atomic；invalid id skip |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号 | 实现事实 |
|---|---|---|---|
| Host/entry/body | 交付 kernel.cpp | if-3 / uss_col_i64_* / NativeColumnOwnedVf | single SIMT |

### Route R-002：FP32 小 N/S 列所有权

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Direct | 交付 kernel.cpp | if-2 | FP32,N/S≤16,A≥64 | uss_owned_f32_* |

#### Device 数据流

##### 函数级调用链

~~~text
uss_owned_f32_* -> SmallNativeVectorOwned -> per output row Duplicate/scan/Add/CopyOut
~~~

##### 源码等价伪码

~~~text
for owned tile, for s: sum=0; scan rows with valid id==s; sum+=data; write y[s] once
~~~

#### 内存与数据搬运

##### 资源与搬运表

| 缓冲区 | offset/容量 | dtype | producer→consumer | lifetime/复用 |
|---|---|---|---|---|
| dataBuf/sumBuf | 0/32 KiB each | FP32 | MTE→Add→MTE3 | row/S reuse |

##### 分层内存布局

~~~mermaid
block-beta
  columns 2
  data["data 32 KiB"]
  sum["sum 32 KiB"]
~~~

##### 字节账与复用顺序

~~~text
UB=64 KiB; workspace=0
~~~

| 复用子区 | 写入者 | 读取者 | 下一覆盖 | 依据 | 条件 |
|---|---|---|---|---|---|
| data/sum | Copy/Duplicate/Add | Add/CopyOut | next row/S | PIPE_ALL | stage complete |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | 机制 | 保护对象 | 精度/尾块 |
|---|---|---|---|
| accumulate | PIPE_ALL+列独占 | sum/y | FP32 input order；8192 tail |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号 | 实现事实 |
|---|---|---|---|
| Host/entry/body | 交付 kernel.cpp | if-2 / uss_owned_* / SmallNativeVectorOwned | 无 init kernel/atomic |

### Route R-004：FP32 单段两阶段归约

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | 交付 plugin/kernel.cpp | accumulator / if-4 | FP32,S=A=1 | partial→finish |

#### Device 数据流

##### 函数级调用链

~~~text
uss_single_partial_* -> SingleSegmentPartialF32Vf -> partials[block]
same stream -> uss_single_finish_f32 -> FinishSingleSegmentF32Vf -> y[0]
~~~

##### 源码等价伪码

~~~text
threads sum id==0; asc_reduce_add; lane0 atomic UB blockSum; barrier; thread0 writes partial; one thread finishes
~~~

#### 内存与数据搬运

##### 资源与搬运表

| 缓冲区 | offset/容量 | dtype | producer→consumer | lifetime/复用 |
|---|---|---|---|---|
| blockSum/partials | 0:32 B / blockIdx:4*blockDim B | FP32 UB/GM | lanes→thread0→finish | two nodes |

##### 分层内存布局

~~~mermaid
block-beta
  columns 2
  ub["blockSum 32 B"]
  gm["partials 4*blockDim B"]
~~~

##### 字节账与复用顺序

~~~text
UB(partial)=32 B; UB(finish)=0; workspace=4*blockDim B
~~~

| 复用子区 | 写入者 | 读取者 | 下一覆盖 | 依据 | 条件 |
|---|---|---|---|---|---|
| blockSum/partials | lane0/partial | thread0/finish | kernel/call end | syncthreads/stream | producer complete |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | 机制 | 保护对象 | 精度/尾块 |
|---|---|---|---|
| reduce | asc_reduce_add+AtomicAdd+barrier | UB/partials | FP32；id!=0 skip；空核写0 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号 | 实现事实 |
|---|---|---|---|
| Host/entry/body | 交付 plugin/kernel.cpp | partial alloc / two entries / two VF | two-kernel closure |

### Route R-007：Low Row-Vector INT32 Long

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Direct | 交付 kernel.cpp | LowRowVectorScatter | i32,A&gt;4096 | batch4,tile8192 |

#### Device 数据流

##### 函数级调用链

~~~text
init -> low vector i32(batch4) -> cast
~~~

##### 源码等价伪码

同 R-006，改为 4 行×8192 elements。

#### 内存与数据搬运

##### 资源与搬运表

| 缓冲区 | offset/容量 | dtype | producer→consumer | lifetime/复用 |
|---|---|---|---|---|
| scatter/acc | 192 KiB / 4*O B | low/FP32 | Copy/Cast→atomic→cast | batch/call |

##### 分层内存布局

~~~mermaid
block-beta
  columns 1
  scatter["low 64 KiB + fp32 128 KiB"]
~~~

##### 字节账与复用顺序

~~~text
peak UB=192 KiB; workspace=4*O B
~~~

| 复用子区 | 写入者 | 读取者 | 下一覆盖 | 依据 | 条件 |
|---|---|---|---|---|---|
| batch | Copy/Cast | atomic | next | PIPE_ALL | rows≤4 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | 机制 | 保护对象 | 精度/尾块 |
|---|---|---|---|
| pipeline | 2D MTE+CAST_NONE+atomic | acc | exact tail；final RINT |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号 | 实现事实 |
|---|---|---|---|
| Host/entry/body | 交付 kernel.cpp | A&gt;4096 / vec_i32 / LowRowVectorScatter | batch4 |

### Route R-008：Low Row-Vector INT64 Mid

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Direct | 交付 kernel.cpp | LowRowVectorScatter | i64,128≤A&lt;8192 | batch2,tile8192 |

#### Device 数据流

##### 函数级调用链

~~~text
init -> low vector i64(batch2) -> cast
~~~

##### 源码等价伪码

同 R-006，ids 为 INT64、每批两行。

#### 内存与数据搬运

##### 资源与搬运表

| 缓冲区 | offset/容量 | dtype | producer→consumer | lifetime/复用 |
|---|---|---|---|---|
| allocated/active UB | 192/96 KiB | low/FP32 | MTE→Cast→atomic | only first2 slots |

##### 分层内存布局

~~~mermaid
block-beta
  columns 2
  alloc["allocated 192 KiB"]
  active["active 96 KiB"]
~~~

##### 字节账与复用顺序

~~~text
allocated UB=192 KiB; workspace=4*O B
~~~

| 复用子区 | 写入者 | 读取者 | 下一覆盖 | 依据 | 条件 |
|---|---|---|---|---|---|
| first2 slots | Copy/Cast | atomic | next | PIPE_ALL | inactive slots unread |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | 机制 | 保护对象 | 精度/尾块 |
|---|---|---|---|
| id/data | i64 guard+vector atomic | address/acc | guard before address |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号 | 实现事实 |
|---|---|---|---|
| Host/entry/body | 交付 kernel.cpp | i64 mid / vec_i64 / LowRowVectorScatter | batch2 |

### Route R-009：Low Row-Vector INT64 Long

#### 适用条件
##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Direct | 交付 kernel.cpp | LowRowVectorScatter | i64,A≥8192 | batch1,tile8192 |

#### Device 数据流
##### 函数级调用链

~~~text
init -> low vector i64(batch1) -> cast
~~~

##### 源码等价伪码

一行一 tile 搬运、升 FP32、vector atomic，最后统一降精度。

#### 内存与数据搬运
##### 资源与搬运表

| 缓冲区 | offset/容量 | dtype | producer→consumer | lifetime/复用 |
|---|---|---|---|---|
| allocated/active UB | 192/48 KiB | low/FP32 | Copy→Cast→atomic | slot0 reuse |

##### 分层内存布局

~~~mermaid
block-beta
  columns 2
  alloc["allocated 192 KiB"]
  active["active 48 KiB"]
~~~

##### 字节账与复用顺序

~~~text
allocated UB=192 KiB; workspace=4*O B
~~~

| 复用子区 | 写入者 | 读取者 | 下一覆盖 | 依据 | 条件 |
|---|---|---|---|---|---|
| slot0 | Copy/Cast | atomic | next row | PIPE_ALL/AtomicNone | write complete |

#### 同步、精度与尾块
##### 同步与数值边界表

| 阶段 | 机制 | 保护对象 | 精度/尾块 |
|---|---|---|---|
| tail | exact DataCopyPad bytes | acc | no padded GM write；final RINT |

#### 关键实现
##### 符号证据表

| 阶段 | 文件 | 符号 | 实现事实 |
|---|---|---|---|
| Host/entry/body | 交付 kernel.cpp | i64 long / vec_i64 / LowRowVectorScatter | batch1 |

### Route R-010：Low 通用 SIMT

#### 适用条件
##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Direct | 交付 kernel.cpp | low fallback | A&lt;128，非hist | uss_acc_* |

#### Device 数据流
##### 函数级调用链

~~~text
VectorZeroOutput(acc) -> LaunchFp32Scatter -> Fp32ScatterVf -> VectorCastFromFp32
~~~

##### 源码等价伪码

flatten I；shift/u32/u64 映射 row；guard id；AtomicAdd FP32 accumulator；final RINT。

#### 内存与数据搬运
##### 资源与搬运表

| 缓冲区 | offset/容量 | dtype | producer→consumer | lifetime/复用 |
|---|---|---|---|---|
| init/scatter/cast | 32 KiB / id*A+a:4*O B / 96 KiB | FP32/low | init→atomic→cast | stream/call |

##### 分层内存布局

~~~mermaid
block-beta
  columns 3
  init["32 KiB"]
  simt["registers+GM"]
  cast["96 KiB"]
~~~

##### 字节账与复用顺序

~~~text
peak UB=96 KiB; workspace=4*O B
~~~

| 复用子区 | 写入者 | 读取者 | 下一覆盖 | 依据 | 条件 |
|---|---|---|---|---|---|
| accumulator | init/atomic | cast | call end | same stream | producers complete |

#### 同步、精度与尾块
##### 同步与数值边界表

| 阶段 | 机制 | 保护对象 | 精度/尾块 |
|---|---|---|---|
| atomic/cast | Simt::AtomicAdd+stream+RINT | FP32 acc | local&lt;count；one cast |

#### 关键实现
##### 符号证据表

| 阶段 | 文件 | 符号 | 实现事实 |
|---|---|---|---|
| Host/entry/body | 交付 kernel.cpp | low fallback / DEFINE_LOW_ENTRY / Fp32ScatterVf | three kernels |

### Route R-012：FP32 Magic-Div SIMT

#### 适用条件
##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Direct | 交付 kernel.cpp | FP32 branch | A&lt;256,I≤u32,非前序 | uss_magic_f32_* |

#### Device 数据流
##### 函数级调用链

~~~text
VectorZeroOutput -> GetUintDivMagicAndShift -> NativeScatterMagicF32Vf
~~~

##### 源码等价伪码

row=UintDiv(u32 index,magic,shift)；a=index-row*A；guard id；FP32 atomic。

#### 内存与数据搬运
##### 资源与搬运表

| 缓冲区 | offset/容量 | dtype | producer→consumer | lifetime/复用 |
|---|---|---|---|---|
| init/scatter | 32 KiB / scalar GM | FP32 | Duplicate/lane→y | u32 domain |

##### 分层内存布局

~~~mermaid
block-beta
  columns 2
  init["32 KiB"]
  simt["registers+GM"]
~~~

##### 字节账与复用顺序

~~~text
peak UB=32 KiB; workspace=0
~~~

| 复用子区 | 写入者 | 读取者 | 下一覆盖 | 依据 | 条件 |
|---|---|---|---|---|---|
| y | init/atomic | caller | call end | same stream | I≤u32 |

#### 同步、精度与尾块
##### 同步与数值边界表

| 阶段 | 机制 | 保护对象 | 精度/尾块 |
|---|---|---|---|
| map/update | magic UintDiv+AtomicAdd | y | count clamp |

#### 关键实现
##### 符号证据表

| 阶段 | 文件 | 符号 | 实现事实 |
|---|---|---|---|
| Host/entry/body | 交付 kernel.cpp | I guard / magic entry / MagicF32Vf | u32 specialization |

### Route R-014：INT32 通用 SIMT

#### 适用条件
##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Direct | 交付 kernel.cpp | INT32 fallback | A&lt;64 | uss_native_i32_* |

#### Device 数据流
##### 函数级调用链

~~~text
VectorZeroOutput<int32> -> NativeScatterVf<int32,Index>
~~~

##### 源码等价伪码

同 R-013 flattened map，目标为 INT32 atomic。

#### 内存与数据搬运
##### 资源与搬运表

| 缓冲区 | offset/容量 | dtype | producer→consumer | lifetime/复用 |
|---|---|---|---|---|
| init/y | 32 KiB / 4*O B | INT32 | zero→atomic | call |

##### 分层内存布局

~~~mermaid
block-beta
  columns 2
  init["32 KiB"]
  simt["no TBuf"]
~~~

##### 字节账与复用顺序

~~~text
peak UB=32 KiB; workspace=0
~~~

| 复用子区 | 写入者 | 读取者 | 下一覆盖 | 依据 | 条件 |
|---|---|---|---|---|---|
| y | zero/atomic | caller | call end | stream | native atomic |

#### 同步、精度与尾块
##### 同步与数值边界表

| 阶段 | 机制 | 保护对象 | 精度/尾块 |
|---|---|---|---|
| update | AtomicAdd<int32> | y | Device INT32 overflow semantics |

#### 关键实现
##### 符号证据表

| 阶段 | 文件 | 符号 | 实现事实 |
|---|---|---|---|
| Host/entry/body | 交付 kernel.cpp | INT32 else / native entry / NativeScatterVf | two kernels |

### Route R-015：INT64 通用 SIMT

#### 适用条件
##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Direct | 交付 kernel.cpp | INT64 fallback | A&lt;512 | simt init→native |

#### Device 数据流
##### 函数级调用链

~~~text
uss_init_i64 -> ZeroOutputVf; same stream -> uss_native_i64_* -> NativeScatterVf<int64,Index>
~~~

##### 源码等价伪码

SIMT zero O；SIMT flatten I；guard id；INT64 atomic。

#### 内存与数据搬运
##### 资源与搬运表

| 缓冲区 | offset/容量 | dtype | producer→consumer | lifetime/复用 |
|---|---|---|---|---|
| y | begin+local / id*A+a; 8*O B | INT64 GM | zero→atomic→caller | call |

##### 分层内存布局

N/A：两节点均 SIMT registers + GM，无 InitBuffer/dynamic UB。

##### 字节账与复用顺序

~~~text
explicit UB=0; workspace=0
~~~

| 复用子区 | 写入者 | 读取者 | 下一覆盖 | 依据 | 条件 |
|---|---|---|---|---|---|
| y | zero | atomic | caller | same stream | zero complete |

#### 同步、精度与尾块
##### 同步与数值边界表

| 阶段 | 机制 | 保护对象 | 精度/尾块 |
|---|---|---|---|
| nodes/update | stream+AtomicAdd<int64> | y | count clamp；INT64 semantics |

#### 关键实现
##### 符号证据表

| 阶段 | 文件 | 符号 | 实现事实 |
|---|---|---|---|
| Host/entry/body | 交付 kernel.cpp | INT64 branch / init+native / Zero+Native VF | two SIMT kernels |

### Route R-013：FP32 通用 SIMT

#### 适用条件
##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Direct | 交付 kernel.cpp | FP32 fallback | A&lt;256,I&gt;u32 | uss_native_f32_* |

#### Device 数据流
##### 函数级调用链

~~~text
VectorZeroOutput -> LaunchNativeScatter -> NativeScatterVf<float,Index>
~~~

##### 源码等价伪码

power-of-two shift，否则按当前 AIV 区间选择 u32/u64 divide；guard；atomic。

#### 内存与数据搬运
##### 资源与搬运表

| 缓冲区 | offset/容量 | dtype | producer→consumer | lifetime/复用 |
|---|---|---|---|---|
| init/y | 32 KiB / id*A+a | FP32 | zero→atomic | call |

##### 分层内存布局

~~~mermaid
block-beta
  columns 2
  init["32 KiB"]
  simt["no TBuf"]
~~~

##### 字节账与复用顺序

~~~text
peak UB=32 KiB; workspace=0
~~~

| 复用子区 | 写入者 | 读取者 | 下一覆盖 | 依据 | 条件 |
|---|---|---|---|---|---|
| y | zero/atomic | caller | call end | stream | guard first |

#### 同步、精度与尾块
##### 同步与数值边界表

| 阶段 | 机制 | 保护对象 | 精度/尾块 |
|---|---|---|---|
| update | FP32 atomic | y | repeated-id order nondeterministic |

#### 关键实现
##### 符号证据表

| 阶段 | 文件 | 符号 | 实现事实 |
|---|---|---|---|
| Host/entry/body | 交付 kernel.cpp | FP32 else / native entry / NativeScatterVf | u64 fallback |

## 算子特定优化

### Trick T-001：同 Stream Kernel 边替代图模式全局屏障

#### 触发与源码依据

- 适用 Route：所有 init→compute Route。
- 触发条件：Direct scaffold 不复刻官方 <code>SetScheduleMode(1)</code>。
- Golden 来源：[<code>op_kernel/arch35/unsorted_segment_base.h:109-124</code>](https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/index/unsorted_segment_sum/op_kernel/arch35/unsorted_segment_base.h)

**官方源码（固定 Commit 连续逐字摘录）**：

~~~cpp
for (COM_T inputIndex = block_idx * blockDim.x + threadIdx.x; inputIndex < inputLength;
     inputIndex = inputIndex + blockNums * blockDim.x) {
    COM_T inputSegmentIndex = Simt::UintDiv(inputIndex, magic, shift);
    COM_T segmentOffset = inputIndex - inputSegmentIndex * innerDimSize;
    const Index outputSegmentIndex = segmentIdsGm[inputSegmentIndex];
    if (outputSegmentIndex < 0 || outputSegmentIndex >= outputOuterDimSize) {
        continue;
    }
    const uint64_t outputIndex = outputSegmentIndex * innerDimSize + segmentOffset;
    asc_atomic_add(outputGm + outputIndex, xGm[inputIndex]);
}
~~~

#### 机制与设计原因

官方 generic 在 <code>InitGm</code> 后 <code>SyncAll</code>，Host 设置 schedule mode。Direct 保留 flatten、guard、atomic，把 zero/scatter 拆为同 stream kernels，以 kernel 边提供跨 AIV ordering；low 再加 cast 边。

#### 迁移边界

- 适用：Direct 全局初始化→跨核 atomic。
- 前提：同一有序 stream，GM 生命周期覆盖后继。
- 失效：跨 stream 必须 event。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

不同 stream 无 event 会使 zero/scatter 竞争；官方 <code>SyncAll</code> 是可验证反例边界。

### Trick T-002：二维整行搬运加 Vector Atomic

#### 触发与源码依据

- 适用 Route：R-006～R-009、R-011。
- 触发条件：wide tail 且前序列所有权未命中。
- Golden 来源：[<code>op_kernel/arch35/uss_simd_non_sort.h:91-109</code>](https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/index/unsorted_segment_sum/op_kernel/arch35/uss_simd_non_sort.h)

**官方源码（固定 Commit 连续逐字摘录）**：

~~~cpp
LocalTensor<X_T> xLocal = xQue_.AllocTensor<X_T>();
uint64_t offset = blockOffsetX + sLoop * td_->baseS * td_->innerDim + aLoop * td_->baseA;
CopyIn(xLocal, xGm_, offset, rows, cols, td_->innerDim - cols);
xQue_.EnQue<X_T>(xLocal);
xLocal = xQue_.DeQue<X_T>();
event_t eventIDMTE2ToS = static_cast<event_t>(GetTPipePtr()->FetchEventID(HardEvent::MTE2_S));
SetFlag<HardEvent::MTE2_S>(eventIDMTE2ToS);
WaitFlag<HardEvent::MTE2_S>(eventIDMTE2ToS);
SetAtomicAdd<X_T>();
~~~

#### 机制与设计原因

官方 non-sort 用 2D MTE 后 vector atomic。Direct native 固定 batch4×8192；low 先把最多 32768 low elements 升 FP32 再写 accumulator，消除逐元素 row division/标量 atomic。192 KiB 是 allocation，不是 active bytes。

#### 迁移边界

- 适用：连续尾维、同一行目标段相同。
- 前提：保持 blockLen/srcStride/dstStride 单位；low 需 FP32 GM 和 final cast。
- 失效：短 tail 回 SIMT；INT64 大 tail回列所有权。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

把 aligned elements 当有效长度会写坏下一行；Direct 只写 <code>elements*sizeof(T)</code>。

### Trick T-003：列所有权消除初始化 Kernel 与 GM Atomic

#### 触发与源码依据

- 适用 Route：R-001～R-003。
- 触发条件：small N/S wide tail，或 INT64 A≥512。
- Golden 来源：[<code>op_kernel/arch35/uss_simd_split_col.h:98-113</code>](https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/index/unsorted_segment_sum/op_kernel/arch35/uss_simd_split_col.h)

**官方源码（固定 Commit 连续逐字摘录）**：

~~~cpp
for (uint64_t i = 0; i < rows; i++) {
    uint64_t dstIdx = idsLocal.GetValue(i);
    if (dstIdx < 0 || dstIdx >= td_->outputOuterDim) {
        continue;
    }
    uint64_t dstOffset = dstIdx * colsAlign;
    Add(yLocal[dstOffset], yLocal[dstOffset], xLocal[i * colsAlign], cols);
}
~~~

#### 机制与设计原因

官方 split-column 让 core 独占列、UB 累加后一次写回。Direct R-001/002 复用该原则；R-003 在 SIMT 直接串行更新 GM INT64。没有两个 worker 写同一列，所以无需 GM atomic 和独立 zero kernel。

#### 迁移边界

- 适用：列数足够，扫描 N×S 受 guard 控制。
- 前提：列域不重叠；owner 写出全部 S 行。
- 失效：shape guard 失败转 row-vector/SIMT。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

只写命中段会使空段未初始化；R-001/002 先 Duplicate，R-003 逐段写零。

### Trick T-004：复用官方 Compute/Init Core 取最大公式

#### 触发与源码依据

- 适用 Route：全部。
- 触发条件：同 launcher 同时覆盖 input compute 与 output init。
- Golden 来源：[<code>op_host/arch35/unsorted_segment_sum_simt_tiling.cpp:45-54</code>](https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/index/unsorted_segment_sum/op_host/arch35/unsorted_segment_sum_simt_tiling.cpp)

**官方源码（固定 Commit 连续逐字摘录）**：

~~~cpp
usedCoreNum_ = Ops::Base::CeilDiv(dataShapeSize_, static_cast<uint64_t>(maxThread_));
usedCoreNum_ = std::min(usedCoreNum_, totalCoreNum_);
uint64_t outSize = outputOuterDim_ * innerDim_;
uint64_t normBlockData = Ops::Base::CeilDiv(outSize, totalCoreNum_);
normBlockData = std::max(normBlockData, UB_MIN_FACTOR / valueTypeBytes_);
uint64_t initUsedCore = Ops::Base::CeilDiv(outSize, normBlockData);
usedCoreNum_ = std::max(usedCoreNum_, initUsedCore);
~~~

#### 机制与设计原因

Direct 保留“input/2048 lanes”和“至少 2 KiB init block”两侧取最大并限于 AIV cores。low 初始化 FP32 accumulator，故 Binit=4。统一 blockDim 也匹配 R-004 partial 数。

#### 迁移边界

- 适用：节点共享 grid 且空核受保护。
- 前提：乘法/ceil-div 不溢出。
- 失效：每节点不同 grid 或 hist windows&gt;blockDim 时重算。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

low 按 2 B 算 init 粒度会偏离实际 FP32 accumulator；Direct 明确用 4 B。

## 模板与实现对比

| 对比维度 | R001..003 | R004/005 | R006..011 | R012..015 | 设计选择依据 |
|---|---|---|---|---|---|
| 命中/优先级 | column最高 | specialized reduce | wide tail | short/fallback | 先去冲突再放大搬运 |
| 模板/dtype | low/FP32/INT64 | FP32或low | low/FP32/INT32 | native dtype | Direct子域 |
| 循环/分核 | columns | partial/windows | rows+column tiles | flattened | shape |
| TBuf | 176/64/0 KiB | 32 B/4/96 KiB | 192/128 KiB | scatter 0 B | InitBuffer |
| workspace | 0 | partials或4*O | low 4*O | low 4*O/其它0 | FP32 contract |
| API | UB/GM column | reduce/hist | 2D MTE+vector atomic | scalar atomic | tail width |
| 同步/精度 | ownership | barriers+stream | PIPE+stream | stream+atomic | one RINT |
| fallback | next | shape next | SIMT | terminal | source priority |

## 平台差异

| 项目 | A2 | A3 | A5 |
|---|---|---|---|
| 支持状态 | 官方 README 不支持 | 官方 README 不支持 | 官方支持 950PR/950DT |
| Host/Launcher | 不适用 | 不适用 | 官方 ascend950/arch35；Direct GetCoreNumAiv/current stream |
| Kernel/资源 | 不适用 | 不适用 | 2048 SIMT lanes，AIV-only，max TBuf 192 KiB |

## 限制与失败边界

- Direct 不支持 UINT32/UINT64、多维 ids 或 tensor num_segments。
- Host 无显式 same-device、乘积溢出、输出容量和 UB IsCapable 检查。
- R-005 隐含 <code>blockDim≥ceil(S/1024)</code>，无断言。
- R-006..009 固定 192 KiB，不得无条件迁移到非 A5。
- 多 Kernel 只依赖同 stream；跨 stream 必须 event。
- launcher void、lambda 返回 0；异步 fault 在框架边界。
- low FP32 atomic 顺序可能不确定；只保证最后一次降精度。
- integer overflow 遵循 Device dtype，不饱和。
- dormant entry 与官方更多 deterministic/sort key 均不属于 Direct dispatch。
- 本次知识提取未执行编译、真机、数值或性能测试。

## 源码索引

### 链路索引

| 链路阶段 | 文件 | 关键符号 | 支撑内容 |
|---|---|---|---|
| 语义/平台 | index/unsorted_segment_sum/README.md | 产品支持/公式 | A5与语义 |
| 构建 | index/unsorted_segment_sum/CMakeLists.txt | SUPPORT_COMPUTE_UNIT/TILING_DIR | ascend950/arch35 |
| OpDef | index/unsorted_segment_sum/op_host/unsorted_segment_sum_def.cpp | UnsortedSegmentSum | dtype/ND/A5 |
| 公共 Tiling | index/unsorted_segment_sum/op_host/arch35/unsorted_segment_sum_tiling_base.cpp | GetPlatformInfo/FlatInput | core/thread/flatten |
| SIMT POD | index/unsorted_segment_sum/op_host/arch35/unsorted_segment_sum_simt_tiling.h | SimtTilingData | ABI |
| SIMT producer | index/unsorted_segment_sum/op_host/arch35/unsorted_segment_sum_simt_tiling.cpp | DoOpTiling/PostTiling | blockDim/schedule |
| non-sort selector | index/unsorted_segment_sum/op_host/arch35/unsorted_segment_sum_simd_non_sort_tiling.cpp | IsCapable | 256 B/UB |
| SIMT helper | index/unsorted_segment_sum/op_kernel/arch35/unsorted_segment_base.h | SimtComputeSegment/InitGm | zero/guard/atomic |
| generic body | index/unsorted_segment_sum/op_kernel/arch35/unsorted_segment_sum.h | KernelUnsortedSegmentSum | POD consumer |
| non-sort body | index/unsorted_segment_sum/op_kernel/arch35/uss_simd_non_sort.h | USSKernelSimdNonSort | 2D MTE/atomic |
| split-col body | index/unsorted_segment_sum/op_kernel/arch35/uss_simd_split_col.h | USSKernelSimdSplitCol | column owner |
| official router | index/unsorted_segment_sum/op_kernel/unsorted_segment_sum_apt.cpp | unsorted_segment_sum | key→body，区别Direct |

### 实现复用检查

| 检查项 | 可复用事实 | 不得改变的约束 | 源码符号 |
|---|---|---|---|
| ABI/POD | 4×u64 arch35 fields | order/width/by-value | SimtTilingData |
| 调用顺序 | zero→scatter、acc→cast、partial→finish | same stream/event | launcher |
| workspace | low=4*S*A，partials=4*blockDim | owner覆盖后继；192 KiB为allocation | plugin/InitBuffer |
| 同步 | PIPE/barrier/atomic/stream | AtomicNone；producer先完成 | bodies |
| 精度/tail | low→FP32→one RINT；exact bytes | no low atomic/padding write | LowRowVector/Cast |
| 失败边界 | invalid id skip、empty core return | guard before address；dormant unreachable | NativeScatterVf/DataTag |
