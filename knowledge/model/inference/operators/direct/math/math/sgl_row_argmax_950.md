---
type: Operator
title: "RowArgmax 950 Direct Invoke 算子知识"
description: "闭合FP32行argmax的扫描获胜tile再重读策略、NaN与并列最小索引、空行和编译launcher缓存，区分逻辑32KB tile与物理分配。"
tags: [task.implementation, task.lookup, topic.memory, topic.precision, topic.programming_model]
status: draft
sources:
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/sample/row_argmax.md
    role: primary
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/row_argmax.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/sample/row_argmax.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/__init__.py
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
created_at: "2026-11-09T09:26:36Z"
updated_at: "2026-11-09T09:26:36Z"
platforms: ["950"]
cann_versions: ["9.1.0"]
---

# RowArgmax 950 Direct Invoke 算子知识

## 算子速览

精确入口 `sgl_kernel_npu.implementation.triton.sample.row_argmax.row_argmax(x)`，FP32二维逐行argmax，新int64[B]输出；并列取最小索引、存在NaN取第一个NaN。完整自有Host、NaN归约helper与单Kernel闭合：先8192元素tile扫描找获胜tile，再只重读该tile解析索引；缓存的是编译launcher而非Tensor数据。

draft表示未构建/执行或检查物理编译分配；公开支持不等于真机验证。复用已全文阅读的[API合同](../../../../apis/sgl_kernel_npu/sgl_row_argmax.md)。物理UB/双缓冲大小不能仅凭源码注释当本次编译结果。

## 接口与语义

### 计算语义

对行r：若存在NaN，返回最小NaN列；否则返回最大值的最小列。严格跨tile比较保留最早获胜tile；重读该tile用最小候选索引完成并列规则。包括全-inf、+inf、多个NaN，源码显式传播NaN而不依赖默认max。若实际primitive遵守指定ALL/min/比较合同，可由路径推导语义；未宣称运行结果。

### 输入、输出与属性

| 项 | 合同/检查 |
|---|---|
| x | NPU FP32[B,V]，V>0、stride(1)=1；B可0，行stride SX可含额外padding |
| Hostassert | ndim2/dtypeFP32/列stride1、V正；没有显式NPUassert或Tensor/layout检查 |
| output | empty(B,int64,device=x.device)，新输出；输入不写 |
| 属性 | 无用户tile/stream/epsilon参数，TILE固定8192 |

### 入口与版本

冻结短路径加包名前缀即精确Direct函数。auto/triton延迟转发；torch_native另属外部参考，不是本图子节点。SGLcommit `dda6d36b0cdb4081e102d14c0a2fb276fc416e69`，CANN9.1.0来自README/CI固定版本，非本次运行或实际Triton二进制核验。未固定完整compiler/lowering版本。

## Host/Launcher 执行流程

### 参数校验与前处理

assert二维/FP32/stride1及V正→分配输出→B0立即返回。非空key=(x.device,B,V,SX,x.data_ptr()%16)。cache miss时对完整constexprwarmup，取得kernel[(B,1,1)]并保存；hit直接复用。warmup的编译行为由Triton，源码没有读x设备值回Host。assert可被Python-O移除，NPU合同仍由调用方保证。

### 参数、Workspace 与生命周期

无workspace、自定义POD、核数helper或显式物理buffer。缓存dict保存compiled launcher，不保存x/output数据；每次launch(x,out)传新Tensor，源码注释指出当前stream仍runtime获取。输出Tensor及输入存活按框架异步规则，stream交接/释放不由本函数显式同步。cache无淘汰路径，shape/stride/alignment/device变多会保留更多launcher，不是数据泄露结论。

### 启动图与失败传播

import→assert/empty→B0返回或key查找→可选warmup编译→同单Kernellaunch→返回。无CPUfallback、无第二个索引Kernel。异常分配/编译/启动传播；缓存成功编译不证明本次执行正确。包__init__原生库/torch_npu加载是导入前提，不是argmax数学图节点。

## Route 与参数设计

### 分核与资源计算

grid=(B,)，Kernel以row=program_id、步长num_programs循环覆盖ROWS=B；当前实际grid通常每program1行，循环也写明完整映射。每行TILES=ceil(V/8192)，扫描所有tile后重读获胜tile；第一遍每tile逻辑8192FP32=32768 B，实际尾mask只读合法列。

### Route 选择

| Host路线 | 条件 | 可达Device |
|---|---|---|
| H-000 | B=0 | 无 |
| H-001 | B>0,key miss | warmup/缓存后R-001 |
| H-002 | B>0,key hit | 直接R-001 |

无autotune、dtype分支或另一个Kernel，三Host路线不能漏空输入或误写cache保存Tensor。

### 模板/实现执行矩阵

| Device Route | dtype | constexpr | 图 |
|---|---|---|---|
| R-001 | X FP32、OUT int64 | N=V,SX,ROWS=B,TILES=ceil(V/8192),TILE8192 | 扫描获胜tile→重读/索引min，同Kernel |

无tl.dot/Cube/AIC/MIX自有节点。代码没有warp/stage显式值，实际线程/UB分配外部。

### 隐藏性能 Guard

注释给32KB tile/DMA和compiler双缓冲动机，以及上游吞吐比较；本卡不复述为本次或普遍性能证据。真实tile常量可证，是否有双缓冲/峰值UB需编译产物。尺寸/指针offset须在实际JIT类型可表示域，row转int64后乘SX只是源码明确的一项保护，不保证tile*8192等其它算术无限范围。

### POD/ABI

| 参数 | 类别/消费 |
|---|---|
| X/OUT | runtime Tensor指针→load/store |
| N | V constexpr→mask/sentinel |
| SX | x.stride(0) constexpr→row指针；row.to(int64)*SX |
| ROWS | B constexpr→行循环上限 |
| TILES | ceil(V/8192) constexpr→扫描循环 |
| TILE | 8192constexpr→arange/步长 |
| grid | warmup(B,)及compiled(B,1,1) |

无自定义序列化/字段位宽、偏移；compiled launcher只接x/outruntime，constexpr被specialization捕获。指针ABI/实际stream获取归Triton，不伪造C++POD。

### Route 源码闭包

90行含全部Host、JIT helper及Device；public wrapper仅转发；sample/backend包无附加Device。根setup→stage_runtime复制完整Python包→build_wheel/setup_refactor打包路径已读；package原生库导入依赖明示。max/min/where/load/store的具体指令/物理资源是外部primitive边界。

## Kernel 实现

### 公共执行流程

一行按SX定位，逐tile做显式NaN传播最大值，严格更新best/best_start；重读获胜tile，sel按best是否NaN选isnan或相等，最小索引store。输入只读，无GM scratch、无跨行同步。

### Route R-001：扫描tile再重读解析索引

#### 适用条件

##### 选择证据

Host B>0、V>0、FP32/列stride1；两cacheHost路线均启动此body，tile固定8192。

#### Device 数据流

##### 函数级调用链

`row_argmax→[warmup/cache]→_row_argmax_kernel→tl.reduce(_maximum_with_nan)→tl.maximum(...ALL)→tl.min/where→store`。helper只做一次二元max，完整body已读，无未知自有Device调用。

##### 源码等价伪码

对每row：base=X+int64(row)*SX；best=-inf,start=0；for tile=0..TILES-1，v=maskedload(base+tile*8192+arange,other=-inf)，cur=NaN传播max；若cur>best或curNaN且best非NaN，更新best/start。扫描结束重读start的tile，若bestNaN则sel=isnan(w)，否则sel=(w==best)；min(where(sel,idx,V))转int64写OUT[row]。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/访问 |
|---|---|
| 第一遍v/off | 8192FP32、8192索引逻辑SSA；每合法输入列一次读取 |
| best/best_start/cur | 跨tile标量carry，编译器物理存储未知 |
| 第二遍w/idx/sel | 8192FP32/索引/布尔逻辑SSA，不假设与v同时占用 |
| GM output | 每行8 B写 |
| UB/TQue/TBuf/workspace | 无显式分配，N/A；不以逻辑张量求物理峰值 |

##### 分层内存布局

`GM row[V]→scan SSA[8192]→carry max/start→GM winning tile→SSA候选索引→min标量→GM int64 output`。没有firstpass统计GM落盘或第二Kernel。

##### 字节账与复用顺序

每行r获胜start s_r，W_r=min(8192,V-s_r)>0；完整调用GM逻辑读 `4*(B*V+Σ_r W_r)` B，写8B B，总4BV+4ΣW_r+8B B；最坏额外重读每行min(8192,V)。不假设第二遍命中缓存或实际DMA事务等于逻辑流量。统计仅任务内SSA；无workspace。输入/输出异步生命周期归Torch/Triton，compiled launcher跨调用不持有输入数据。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 证明/边界 |
|---|---|
| tile间 | best scalar carry体现前后依赖，由compiler保序；没有物理event声明 |
| row间 | 输出各8B槽唯一，无atomics/共享写 |
| 最大值并列 | 仅cur>best更新，早tile保留；同tile最后min索引 |
| NaN | ALL传播；首个NaN tile更新后bestNaN阻止后续替换，重读isnan取首个 |
| 全-inf | best初始-inf/start0不更新；tile0真实列也匹配，N>0保证最小真实索引0先于padding |
| 尾列 | 两遍load越界补-inf，未额外给sel加idx<N；padding索引≥V，真实最优候选<V，min仍保真实索引 |
| 数值 | 无浮点加乘/精度转换，比较/max依赖指定primitiveNaN合同；索引最终int64 |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| _maximum_with_nan | [helper](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/row_argmax.py#L26-L28) |
| scan与index | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/row_argmax.py#L41-L58) |
| cache | [Host](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/row_argmax.py#L61-L90) |

## 算子特定优化

### Trick T-001：第一遍只找获胜tile，避免每tile索引归约

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/row_argmax.py#L45-L58)：

```python
        for tile in range(TILES):
            start = tile * TILE
            off = start + tl.arange(0, TILE)
            v = tl.load(base + off, off < N, float("-inf"))
            cur = tl.reduce(v, 0, _maximum_with_nan)
            # NaN is maximal, matching torch.argmax, and only the first is taken;
            # Explicit propagation avoids relying on backend-specific max defaults.
            take = (cur > best) | ((cur != cur) & (best == best))  # noqa: PLR0124
            best_start = tl.where(take, start, best_start)
            best = tl.where(take, cur, best)
        idx = best_start + tl.arange(0, TILE)
        w = tl.load(base + idx, idx < N, float("-inf"))
        sel = tl.where(best != best, w != w, w == best)  # noqa: PLR0124
        tl.store(OUT + row, tl.min(tl.where(sel, idx, N), 0).to(tl.int64))
```

#### 机制与设计原因

把完整索引解析限制到获胜tile，用一次额外tile重读换掉每tile的索引向量比较/select/min；保留tie/NaN语义。源码注释的速度数字不是本次或跨平台性能结论。

#### 迁移边界

跨tile用严格比较且NaN优先；padding为-inf，V>0且索引sentinel=V，才可用最后min规则。不能泛化到自定义不兼容NaN排序。

#### 错误做法

用cur>=best覆盖后tile会破坏最小并列索引，普通不传播NaN的max也会改变语义。

### Trick T-002：只缓存编译launcher并含指针对齐键

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/row_argmax.py#L72-L75)：

```python
    # Cache only compiled launchers. Tensor data and the current stream remain
    # runtime arguments. Include pointer alignment in the specialization key.
    key = (x.device, rows, n, x.stride(0), x.data_ptr() % 16)
    launch = _row_argmax_launchers.get(key)
```

#### 机制与设计原因

shape/stride/device/16B对齐决定编译缓存实例，调用时仍传实际x/out；避免重复Python JIT分发的源码意图可见，无实测收益。

#### 迁移边界

新影响specialization的属性必须纳入key或由框架可靠区分；当前代码不保留Tensor数据，stream由runtime处理。

#### 错误做法

把第一次Tensor或旧stream闭包缓存为后续固定参数，或只按shape忽略stride/alignment。

## 模板与实现对比

唯一Device路线含两个pass但只有一个Kernel；Host空行/cold/hit三路线均已登记。与普通finite max不同，本实现显式NaN及tie合同；Torch reference只作外部独立路径，不补实现。逻辑tile32KB确切，物理双缓冲仅源码动机，未当产物事实。

## 平台差异

本卡950归属arch35；公开doc arch22/35支持但注册不保证全部芯片验证，README/architectures映射A2/A3、950。无硬件宏/平台body分支；CANN9.1.0 CI配置非本次执行、非实际compiler或A2实测。

## 限制与失败边界

没有显式NPU/deviceguard，assert可关闭，极大V/ROWS的JIT算术可表示范围需另核对；未知物理UB/lowering不可当安全上限。缓存无清理策略。未编译、执行、测试/校验或测性能，draft保留边界，不宣称上游注释数字被复现。

## 源码索引

### 链路索引

| 阶段/源码 | 符号 | 事实 |
|---|---|---|
| [公开合同](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/sample/row_argmax.md) | `row_argmax` | FP32/rowstride/tie与NaN/arch22与35 |
| [Direct及Device](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/row_argmax.py) | `row_argmax/_row_argmax_kernel/_maximum_with_nan` | 完整90行/两pass/编译launcher缓存 |
| [公开转发](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/sample/row_argmax.py) | `_triton_impl` | auto/triton直达 |
| [sample包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/__init__.py) | `module init` | 无附加Device |
| [import边界](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py) | `_load_sgl_kernel_npu` | torch_npu/原生库与vendor初始化 |
| [backend包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/__init__.py) | `module init` | 懒加载包，无另一Device节点 |
| [构建入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/setup.py) | `main` | 完整Python wheel路径；本次未构建 |
| [源码打包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/build_tools/torch_wheel.py) | `stage_runtime/build_torch/build_wheel/setup_refactor` | 复制完整Python包、原生运行库与wheel |
| [平台/包说明](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md) | `REFACTOR/arch22/35 mapping` | 全部Python实现包含、产品映射、CANN9.1.0构建例 |
| [产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json) | `2201/3510` | a2/a3/950对应构建族 |
| [版本配置](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernels.yml) | `test-norm-ops` | CANN9.1.0/a3/950配置，非本次运行 |
| [CI消费](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernel-group.yml) | `run-kernel-group` | 对应版本容器/测试组参数 |

### 实现复用检查

冻结117/legacy候选row_argmax API已全文阅读并链接，新增唯一Direct两平台实现卡；不重复API，不混入sampling/softmax不同数学语义。全部同repo固定source恰一primary，无verified。
