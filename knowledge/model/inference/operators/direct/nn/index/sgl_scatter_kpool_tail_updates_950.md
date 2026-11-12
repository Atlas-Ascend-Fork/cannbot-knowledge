---
type: Operator
title: "ScatterKpoolTailUpdates 950 Direct Invoke 算子知识"
description: "闭合128通道K/score计划scatter与环形地址、inactive参数及原地写集，保留metadata窄化、源目标别名和跨计划冲突边界。"
tags: [task.implementation, task.lookup, topic.memory, topic.precision, topic.programming_model]
status: draft
sources:
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/mem_cache/scatter_kpool_tail_updates.md
    role: primary
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/scatter_kpool_tail_updates.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/mem_cache/scatter_kpool_tail_updates.py
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
created_at: "2026-11-09T10:17:28Z"
updated_at: "2026-11-09T10:17:28Z"
platforms: ["950"]
cann_versions: ["9.1.0"]
---

# ScatterKpoolTailUpdates 950 Direct Invoke 算子知识

## 算子速览

`sgl_kernel_npu.implementation.triton.mem_cache.scatter_kpool_tail_updates.scatter_kpool_tail_updates` 按计划将chunk key/score的连续128列行原值复制到请求tail环，目标slot=(dst_start+slot)%tail_capacity；只更新tail_k/tail_score，返回None，不softmax、不旋转/压缩/量化。完整Host/单Device及空计划闭合，无dot/Cube，VV数据搬运。

draft保留索引/容量/并发和别名合同未guard、int32窄化、currentdevicecache及无运行证据。已全文读[共同tail/cache API](../../../../apis/sgl_kernel_npu/sgl_kpool_tail_cache.md)链接复用，其它三API数学不并入本卡。

## 接口与语义

### 计算语义

计划a给req、src_base、dst_start、n_w；对s∈[0,n_w)：`tail_k[req,(dst_start+s)%T,:]=chunk_k[src_base+s,:]`，score同构。n_w先Device转int32；req/src_base转int64、dst_start转int32。rawDevice循环完整n_w，不以pool.index_kpool裁剪，后者实际Kernel未消费。共同Torch对照合同需0≤n_w≤pool.index_kpool（已有API记录参考只生成pool_size项）；不能把超域两后端当等价。若单计划反复绕环，rawsource顺序重复写同slot，最终是其最后一次写；跨计划冲突无原子保证。

### 输入、输出与属性

| 项 | Host实际检查/前提 |
|---|---|
| pool | 必须有index_kpool属性，读取后传POOL_SIZE但Device不消费 |
| chunk_k/score | [Nchunk,128]且shape相同，内部各contiguous；浮点pair dtype与各自tail兼容，无显式dtype/deviceguard |
| tail_k/score | [R,T,128]shape相同且均contiguous，T>0由调用方保证；原地更新不复制状态 |
| 计划四向量 | 同长A、1D、contiguous；整数dtype与同NPU无完整guard |
| 值域 | req∈[0,R)，src_base≥0且src_base+n_w≤Nchunk，n_w≥0且可int32，dst算术及mod结果在[0,T) |
| 并发/别名 | 跨计划目标不冲突，chunk与可变tail无未读先写alias；不保证任意partialoverlap或并发调用安全 |
| 返回 | None，未选tail保持原值；chunk/metadata只读 |

### 入口与版本

Direct签名(pool,chunk_k,chunk_score,tail_k,tail_score,req_pool_idx,dst_logical_start,chunk_src_start,n_write)。auto/triton转发，无fallback；torch_native外部参考不代替此Device。SGLcommit `dda6d36b0cdb4081e102d14c0a2fb276fc416e69`，CANN9.1.0为README/CI配置非本次运行；完整Tritonbinary未固定。

## Host/Launcher 执行流程

### 参数校验与前处理

先读取pool.index_kpool及A=req_pool_idx.shape[0]，A0直接return（尚未Tensor元信息assert，仍需pool属性）。非空检查chunk2D/128与score同shape、tail3D/128/score同shape/连续、四计划1D同长连续；chunk两只读Tensor各contiguous后n=min(A,Pcores)，grid(n,)launch。不读设备索引值到Host，不检查T正/请求或source范围/dtype/device/写冲突。assert可被Python-O关闭。

### 参数、Workspace 与生命周期

无新outputallocation/调用方workspace/POD/ACLNN。两chunk若需copy，分别临时Nchunk*128*dk/ds B，额外读写各同大小；tail是已有可变GM不能连续化到临时后丢更新。helper无参current_devicecache、AIC/vectorassert正，无deviceguard；属性需与Tensordevice相容。临时copy→Kernel流顺序、原地tail异步就绪与回收归framework，无显式wait/event。

### 启动图与失败传播

import→pool/A读取→A0返回或asserts→chunk连续化→helper→单copyKernel→None。无压缩/softmax/rotation/外部核心Torch数学，只有copy框架边界。异常传播，无fallback；package原生库仅导入前提。

## Route 与参数设计

### 分核与资源计算

n=min(A,P)>0；program p轮转plan a=p+j*n<A。每plan只读四metadata一次，再按n_w串行slotcopy，每次两128元素blockptrload/store。计划拥有者唯一不代表不同计划目标独占，外部需保证地址集合无交叠。全128读取无通道tail/mask。

### Route 选择

| Route | 条件 | 图 |
|---|---|---|
| H-000 | A0 | 无Kernel，检查前返回 |
| R-001 | A>0 | 计划轮转+slot循环；n_w0同body无slotcopy |

### 模板/实现执行矩阵

固定HEAD_DIM128、BLOCK_D128、POOL_SIZE来自pool但后两元参数没有body消费；真实slotmod是TAIL_SIZE。payloadpair dtype由实际指针决定，源注释BF16非Hostdtype白名单；以公开浮点/各自pair同dtype域计字节，不虚构其它dtype支持。metadata整数int32/int64按to转换，控制图同一。无dot/Cube/AIC/MIX节点。

### 隐藏性能 Guard

TAIL_SIZE0未guard，mod编译/运行无定义保证；dst_start/slotint32和可能overflow，负mod不可直接当Python正环索引。n_w输入int64先窄化int32、非法超大值不保持数学原值。POOL_SIZE不限制n_w；BLOCK_D不参与make_block_ptr。完整源/目标row必须有128有效元素，blockptr无边界mask不能靠shape声明补容量。

### POD/ABI

| 字段 | 类别/消费 |
|---|---|
| chunk_k_ptr/chunk_score_ptr | runtime输入指针，连续化后按共享chunk_stride_0寻址 |
| tail_k_ptr/tail_score_ptr | runtime可变指针，共享tailstrides，Host同shape连续保证元素stride相同 |
| req_pool_idx_ptr/dst_logical_start_ptr/chunk_src_start_ptr/n_write_ptr | runtime计划指针→reqint64/dstint32/srcint64/n_wint32 |
| chunk_stride_0 | runtime元素rowstride→toint64乘srcrow |
| tail_stride_0/tail_stride_1 | runtime元素请求/slotstride→toint64乘地址 |
| n_rows | runtime计划A→轮转 |
| POOL_SIZE | constexprpool属性，实际未消费 |
| TAIL_SIZE/HEAD_DIM | constexprT/128→mod与blockshape |
| BLOCK_D | constexprnextpow2(128)=128，实际未消费 |
| NUM_CORES/grid | constexprn/(n,)→轮转 |

无自定义序列化POD/字段offset，显式int64地址项有证据，其它JIT标量ABI/类型容量外部。

### Route 源码闭包

完整167行Direct/Device、public适配/helper已读；mem_cache/backendinit无Device。根setup→stage_runtime完整Python包→build_wheel/setup_refactor；make_block_ptr/load/store/mod是外部primitive，不将物理DMA指令/UB分配按注释填造。没有外部核心数学fallback。

## Kernel 实现

### 公共执行流程

四metadata加载→slot循环→源行+环形目标地址→两128blockptrload→两128blockptrstore。计划、payload之外无GM统计/输出buffer或同步。

### Route R-001：计划轮转的128元素原值scatter

#### 适用条件

##### 选择证据

非空A、Hostchecks通过且值域/写冲突/源目标alias前提成立；n_w0合法无slot读取写入。

#### Device 数据流

##### 函数级调用链

`scatter_kpool_tail_updates→helper→_scatter_kpool_tail_updates_kernel→make_block_ptr/load/store`；无自有JIThelper或其它Kernel。

##### 源码等价伪码

for plan=p;plan<A;plan+=n：loadn_w.toint32/req.toint64/dst.toint32/src.toint64；for s<n_w：srcrow=src+int64(s)，slot=(dst+s)%T；srcoff=srcrow*int64(chunkstride)，dstoff=req*int64(tailstride0)+int64(slot)*int64(tailstride1)；按128元素shape/stride1 load key/score，按相同shape store两个tail指针。不读取旧tail。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑资源/流量 |
|---|---|
| key/score block | 各128元素，128dk/128ds B；实际UB/寄存器分配外部 |
| metadata | 每plan四标量，各自dtype字节dm_req/dm_dst/dm_src/dm_n |
| 地址 | req/src/stride乘显式int64，dst_start/slot加法保int32 |
| tail旧值 | 不读，未选位置也不写 |
| workspace | 无新增，输入连续化可有GM临时 |

##### 分层内存布局

`GMchunk_key/score[srcrow,128]→blockptr逻辑值[128]→GMtail[req,slot,128]`；metadata控制地址，无norm/量化中间。blockptrshape不等实际分配物理UB或完整payloadstorage安全证明。

##### 字节账与复用顺序

令V=Σ_a n_w[a]在合法非负/narrowing未溢出域，metadata读A*(dm_req+dm_dst+dm_src+dm_n) B；payload读写总2*128*V*(dk+ds) B（各pair同dtype），没有旧tail读取。若chunkcopy发生，额外输入GM临时及读写如Host节；不假设cache或真实DMA事务等于逻辑。tail已有GM spanR*T*128*(dk+ds)，本调用不新分配；所有临时和state异步存活由framework/caller负责。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 同plan | slot串行，先loadkey/score后store；多次绕环同slot最终最后copy，未承诺可对拍超pool域 |
| 跨plan | 没有atomic/锁/barrier，必须目标不重叠；相同req不一定冲突，取决slot集合 |
| 别名 | chunk与tail若共享被覆写未来源会改变copy结果，当前contiguous不保证新copy；需外部无危险别名 |
| 类型 | 不显式cast/算payload，同dtypepaircopy；异dtype隐式store转换不作等价支持扩展 |
| 通道尾 | 固定完整128，load/store无mask，必要storage域必须真实存在 |
| 计划尾 | grid轮转row<A；n_w0slotloop0，无payload访问 |
| 同步 | copy依SSA/lowering顺序，框架流/caller负责state串行化，无hostwait |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| metadata/slot地址 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/scatter_kpool_tail_updates.py#L43-L60) |
| 两blockload/store | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/scatter_kpool_tail_updates.py#L62-L109) |
| Host/launch | [入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/scatter_kpool_tail_updates.py#L112-L167) |

## 算子特定优化

### Trick T-001：计划metadata只读一次后串行多个slot

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/scatter_kpool_tail_updates.py#L45-L60)：

```python
    # Each core processes rows with a grid-stride loop.
    for row in range(pid, n_rows, NUM_CORES):
        # Load this row's metadata once.
        n_w = tl.load(n_write_ptr + row).to(tl.int32)
        req = tl.load(req_pool_idx_ptr + row).to(tl.int64)
        dst_start = tl.load(dst_logical_start_ptr + row).to(tl.int32)
        src_base = tl.load(chunk_src_start_ptr + row).to(tl.int64)

        # Iterate over the slots written by this row.
        for slot in range(n_w):
            # Compute the chunk source row and physical tail slot (ring modulo).
            src_row = src_base + slot.to(tl.int64)
            phys_slot = (dst_start + slot) % TAIL_SIZE

            # Compute the offset in chunk.
            src_offset = src_row * chunk_stride_0.to(tl.int64)
```

#### 机制与设计原因

每plan四标量支撑所有n_w次rowcopy，固定grid轮转plan而不为每元素启动任务；源/请求地址项显式int64。未测性能，不把dstint32遗漏写成全地址64bit。

#### 迁移边界

n_w/逻辑slot加法/metadata窄化可表示，TAIL_SIZE正且mod结果合法，跨plan写集无冲突。

#### 错误做法

以pool.index_kpool替代TAIL_SIZE求环地址，或认为NUM_CORES唯一planowner自动消除不同plan目标冲突。

### Trick T-002：固定128通道blockptr整行copy

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/scatter_kpool_tail_updates.py#L62-L71)：

```python
            # Load chunk_k[src_row, :] with a block pointer.
            k_block = tl.make_block_ptr(
                base=chunk_k_ptr + src_offset,
                shape=(HEAD_DIM,),
                strides=(1,),
                offsets=(0,),
                block_shape=(HEAD_DIM,),
                order=(0,),
            )
            k = tl.load(k_block)  # [HEAD_DIM] BF16 full-row DMA
```

score及两个tail同构blockptr见74–109行。

#### 机制与设计原因

shape/stride1/blockshape都固定128，连续整行payloadcopy；源码注释DMA意图不能替代实际compiler物理内存/指令证据。

#### 迁移边界

必须固定128通道及有效src/dststorage；若扩展head_dim/tailstride需重新审查接口与地址。

#### 错误做法

把BLOCK_D当真实通道mask或给短row仍声明shape128而期待自动padding。

## 模板与实现对比

唯一copy路线无softmax/rotate/quant；POOL_SIZE/BLOCK_D字段inactive准确列明。公共跨后端0≤n_w≤pool_size与rawDevice完整循环n_w区别保留，不把超域reference截断当Device行为。空计划早于元信息check。

## 平台差异

本卡950归属arch35；公开arch22支持/arch35已验证，作为上游报告非本次复测，README/architectures映射A2/A3、950。无hardwarebranch，CANN9.1.0 CI配置非本次执行/physicalresource证据。

## 限制与失败边界

metadata值域、positiveT、dtype/device/源目标alias及跨计划并发未完整guard；int32加法/窄化与JIT地址域须匹配。没有构建、上游运行、测试或校验/性能/physicalUB产物，draft保留条件，不推荐无条件原地并发更新。

## 源码索引

### 链路索引

| 阶段/源码 | 符号 | 事实 |
|---|---|---|
| [公开合同](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/mem_cache/scatter_kpool_tail_updates.md) | `scatter_kpool_tail_updates` | 128通道copy/环形计划/平台 |
| [Direct/Device](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/scatter_kpool_tail_updates.py) | `scatter_kpool_tail_updates/_scatter_kpool_tail_updates_kernel` | 完整167行/计划轮转/blockptrcopy |
| [公开转发](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/mem_cache/scatter_kpool_tail_updates.py) | `_triton_impl` | auto/triton只转发 |
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

冻结117/legacy同主题共同KpoolAPI已全文读，链接复用；此唯一scatterOperator不并入其它三种汇聚写cache语义，固定source同repo唯一primary、无verified。
