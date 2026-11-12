---
type: Operator
title: "SwigluOaiFloat 950 Direct Invoke 算子知识"
description: "闭合need_quantFalse的浮点OAI激活与三group有效前缀，明确所有scale未定义、无1536量化slice及整行/整数/编译资源边界。"
tags: [task.implementation, task.lookup, topic.memory, topic.precision, topic.programming_model]
status: draft
sources:
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/activation/swiglu_oai_quant.md
    role: primary
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/swiglu_oai_quant.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/activation/swiglu_oai_quant.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/__init__.py
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
created_at: "2026-11-09T09:54:21Z"
updated_at: "2026-11-09T09:54:21Z"
platforms: ["950"]
cann_versions: ["9.1.0"]
---

# SwigluOaiFloat 950 Direct Invoke 算子知识

## 算子速览

精确入口 `sgl_kernel_npu.implementation.triton.activation.swiglu_oai_quant.swiglu_oai_quant`，本次独立冻结 `need_quant=false`。分半gate/up经OAI单侧/双侧裁剪、sigmoid及up加1，输出inputdtype浮点，scale缓冲全部未定义；只写合法group有效前缀，不重排token。

自有Direct/单Device/三group路线源码闭合，实际无dot/Cube，选VV；draft保留Direct绕过公共check、arange/整数/物理资源及无当前运行证据。已全文读的[公开API](../../../../apis/sgl_kernel_npu/sgl_swiglu_oai_quant.md)复用，另一need_quant域独立任务不混卡。

## 接口与语义

### 计算语义

x[...,2D]=[gate|up]，g=min(gate,limit)，u=clamp(up,-limit,limit)，y=g*sigmoid(alpha*g)*(u+1)。out=cast_xdtype(y)，返回scale仅占位未写，不能当有意义统计或恢复系数。有限输入/中间值与实际promotion为数值前提，未宣称逐位Torch等价。

### 输入、输出与属性

| 项 | 合同/真实入口 |
|---|---|
| x | FP16/BF16/FP32strided，至少1维且末2D、D>0；reshape/contiguous支持非连续；前导可空 |
| alpha/limit | 可FP32表示有限实数，limit正；Direct只float()转换未全面验证 |
| need_quant | 冻结false，不覆盖另一精度语义 |
| group | None全部S行；或同device非空int32/int64[E]，type0累积末项/type1计数和，R合法且可int32 |
| 输出 | out[...,D] inputdtype；scale[S]FP32，全部未定义；out仅[0,R)有效，输入不写 |

### 入口与版本

Direct签名(x,alpha,limit,need_quant=True,group_list=None,group_list_type=None)，本域显式设置need_quant=false。public operator才_check_inputs group编码/dtype，Direct不调用；两者都未全面guard D/数值/布局。auto/triton转发，torch_native参考不并入图。SGLcommit `dda6d36b0cdb4081e102d14c0a2fb276fc416e69`；CANN9.1.0来自README/CI，非本次环境，完整Tritonextension二进制未固定。

## Host/Launcher 执行流程

### 参数校验与前处理

D=x.last//2→group可选contiguous→x.reshape(-1,last).contiguous→out/scale分配→S0空返回。nonempty E、A=64//dg、E_A=ceil(E/A)*A（无group用E/A1）；helper取P，float(alpha/limit)，launch multibufferTrue。Direct未重复public编码/dtypecheck，也未验证group非空、D1536倍数/末偶、标量范围；合同由调用方保证。E_A是64B倍数而非必二次幂。

### 参数、Workspace 与生命周期

输出out为SD*dx B，scale4S B；可选输入packedcopy2SDdx B、groupcopyE*dg B。无请求方workspace/POD/ACLNN或统计GM，物理UB/寄存器及multibuffer深度归compiler。helper无参cache/current_device，要求调用方先设置x.device；无deviceguard/显式stream/wait。临时copy及输出异步生存由框架allocator负责。

### 启动图与失败传播

import→groupcopy/xpacked→输出/scale分配→S0返回或helper→单JITKernel→reshapeout返回。无fallback或其它数学Kernel。Direct异常传播，publicValueError在绕过门面时不会发生。包原生库导入仅依赖，未列为图内算法。

## Route 与参数设计

### 分核与资源计算

Pprogram各自先读group，R有效总行数，q=ceil(R/P)，各program区间[pq,min((p+1)q,R))；空段return。每有效行整2Dload/激活，SCALEfalse直接全Dstore。N/S和row*2D没有显式int64转换，须实际JIT整数可表示与roundup余量；没有SiTU那种N≤2³¹-PHostguard。

### Route 选择

H-000=S0，已分配空buffer无Kernel；R-001dense、R-002cumulative、R-003count。SCALEfalse冻结，无quantcast/scale计算/1536循环。无autotune，固定multibufferTrue不等depth2。

### 模板/实现执行矩阵

| Route | HAS_GROUP_LIST | TYPE | R |
|---|---|---|---|
| R-001 | false | 占位0 | S |
| R-002 | true | 0 | int32(last) |
| R-003 | true | 1 | sum(int32(group)) |

x三浮点dtype、group两整数dtype；每group模式同body，但metadata字节/精度不同。无dot/Cube/AIC/MIX，只有Vector/elementwise/row-reduce自有语义，compiler物理映射外部。

### 隐藏性能 Guard

整行2D SSA不受1536outputtile约束；arange TOTAL_COLS/COL1536/E_A可能非二次幂，固定CANNextension准入未知，不宣称必失败或成功。未见UB容量查询、group数值与Nroundup/rowoffsetguard。64B对齐只是logicalrange，mask限定E内load，不能据此证明读取padding或物理DMA越界。

### POD/ABI

| 参数 | 分类/消费 |
|---|---|
| x_ptr/group_list_ptr/out_ptr/scale_ptr | runtimeTensor，输入读/out写；scale不消费 |
| alpha/limit | runtime float(alpha/limit)→clamp/sigmoid；实际JIT标量dtype外部 |
| total_rows | runtimeS→denseR；group时覆盖 |
| TOTAL_COLS/HALF_COLS/COL_BLOCK_SIZE | constexpr2D/D/1536→整行arange/slice/output |
| NUM_EXPERTS/NUM_EXPERTS_ALGIN | constexprE/E_A→last/maskedreduce |
| GROUP_LIST_TYPE/NUM_CORES | constexprtype/P→group/分行 |
| DTYPE_MAX/SCALE/HAS_GROUP_LIST | constexpr127/false/groupbool→量化/metadata |
| multibuffer/grid | True/(P,) |

无自定义序列化POD/字节offset；int32group窄化明确，其它JITABI/物理分配不猜测。

### Route 源码闭包

完整146行Direct/Device、helper和publiccheck已读，核心算法无外部Torch数学（reshape/contiguous/empty是框架边界）。根setup→stage_runtime完整Python包→build_wheel/setup_refactor，activation/backend包无Device。需要的primitive算术/cast/al.slice合同明确外部，不以publicFP32文字补造源中cast。

## Kernel 实现

### 公共执行流程

metadata→分行→整行load及split→clamp/sigmoid/OAI→floatstore。合法R0无输出写，尾部全未定义，空S无Kernel。

### Route R-001：group=none

#### 适用条件

##### 选择证据

冻结need_quant=false，SCALE constexpr=false；非空S，无group，R=S。合法有效前缀0≤R≤S。不进入1536量化slice，浮点输出仅有效前缀定义。

#### Device 数据流

##### 函数级调用链

`swiglu_oai_quant→[group.contiguous]/x.reshape.contiguous→helper→_swiglu_oai_quant_kernel→group读取/分行→整行clamp/sigmoid→浮点store`。无tl.dot/Cube/AIC/MIX或其它自有Kernel，选VV。

##### 源码等价伪码

各program先得到R，q=ceil(R/P)，分行[pq,min((p+1)q,R))并空段返回。每row整行load2D，slice为gate/up；g=min(gate,limit)只限上界，u=clamp(up,-limit,limit)，y=g*sigmoid(g*alpha)*(u+1)。直接store y.to(x.dtype)；不写scale任何元素。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| cur_x/gate/up/y | 整行2D/D/D/D，算术dtype随实际Tritonpromotion；源码不显式先castFP32 |
| group | 无读取 |
| quant | 无scale计算/1536临时；返回scaleGM未定义 |
| payload | read2RDdx、write RDdx B |
| workspace/physical UB | 无显式请求/分配；整行SSA与multibufferTrue不确定实际峰值 |

##### 分层内存布局

`strided x→可选packedcopy GM[S,2D]→whole-row SSA→clamp/sigmoid→GMfloatout；scale不写`。groupcontiguouscopy可能另有临时，不将64B逻辑对齐当成无mask读取padding。

##### 字节账与复用顺序

Kernel有效payload逻辑 3RDdx B，再加group 0 B（所有program在earlyreturn前取group）。Host out分配S*D*dx B、scale4S B；x若copy临时2SDdx B且额外读写各2SDdx B，group若copy临时E*dg且额外读写各E*dg。无显式workspace；输出与临时异步存活由Torch/Triton，未定义尾部不得读取。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 分行 | 合法R及int32调度可表示域内无共享写；无atomics/barrier |
| group | R=S runtime；S/Proundup缺Hostheadroomguard |
| 全行 | 无maskload2D，需packedlayout/storage；整行arange非pow2准入需CANN扩展 |
| 激活精度 | doc称FP32；source loadgate/up未显式toFP32，alpha/limit以float传JIT，实际promotion归compiler，不能补造cast |
| 量化 | SCALEfalse剪去quant全部节点；scale所有元素未定义 |
| tail | 非quant无1536约束，仍受arange/资源准入 |
| lifetime | copy/Kernel框架流依赖，无hostwait；多设备调用先设置currentdevice=x.device |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| group/分核 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/swiglu_oai_quant.py#L37-L56) |
| 激活/选择分支 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/swiglu_oai_quant.py#L58-L99) |
| launcher | [入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/swiglu_oai_quant.py#L102-L146) |


### Route R-002：group=cumulative

#### 适用条件

##### 选择证据

冻结need_quant=false，SCALE constexpr=false；非空S，HAS_GROUP_LISTtrue/type0，R=int32(last)。合法有效前缀0≤R≤S。不进入1536量化slice，浮点输出仅有效前缀定义。

#### Device 数据流

##### 函数级调用链

`swiglu_oai_quant→[group.contiguous]/x.reshape.contiguous→helper→_swiglu_oai_quant_kernel→group读取/分行→整行clamp/sigmoid→浮点store`。无tl.dot/Cube/AIC/MIX或其它自有Kernel，选VV。

##### 源码等价伪码

各program先得到R，q=ceil(R/P)，分行[pq,min((p+1)q,R))并空段返回。每row整行load2D，slice为gate/up；g=min(gate,limit)只限上界，u=clamp(up,-limit,limit)，y=g*sigmoid(g*alpha)*(u+1)。直接store y.to(x.dtype)；不写scale任何元素。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| cur_x/gate/up/y | 整行2D/D/D/D，算术dtype随实际Tritonpromotion；源码不显式先castFP32 |
| group | 每P program读last 1项 |
| quant | 无scale计算/1536临时；返回scaleGM未定义 |
| payload | read2RDdx、write RDdx B |
| workspace/physical UB | 无显式请求/分配；整行SSA与multibufferTrue不确定实际峰值 |

##### 分层内存布局

`strided x→可选packedcopy GM[S,2D]→whole-row SSA→clamp/sigmoid→GMfloatout；scale不写`。groupcontiguouscopy可能另有临时，不将64B逻辑对齐当成无mask读取padding。

##### 字节账与复用顺序

Kernel有效payload逻辑 3RDdx B，再加group P*dg B（所有program在earlyreturn前取group）。Host out分配S*D*dx B、scale4S B；x若copy临时2SDdx B且额外读写各2SDdx B，group若copy临时E*dg且额外读写各E*dg。无显式workspace；输出与临时异步存活由Torch/Triton，未定义尾部不得读取。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 分行 | 合法R及int32调度可表示域内无共享写；无atomics/barrier |
| group | 只last转int32，无单调/范围guard；S/Proundup缺Hostheadroomguard |
| 全行 | 无maskload2D，需packedlayout/storage；整行arange非pow2准入需CANN扩展 |
| 激活精度 | doc称FP32；source loadgate/up未显式toFP32，alpha/limit以float传JIT，实际promotion归compiler，不能补造cast |
| 量化 | SCALEfalse剪去quant全部节点；scale所有元素未定义 |
| tail | 非quant无1536约束，仍受arange/资源准入 |
| lifetime | copy/Kernel框架流依赖，无hostwait；多设备调用先设置currentdevice=x.device |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| group/分核 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/swiglu_oai_quant.py#L37-L56) |
| 激活/选择分支 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/swiglu_oai_quant.py#L58-L99) |
| launcher | [入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/swiglu_oai_quant.py#L102-L146) |


### Route R-003：group=count

#### 适用条件

##### 选择证据

冻结need_quant=false，SCALE constexpr=false；非空S，HAS_GROUP_LISTtrue/type1，R=sum(int32(group))。合法有效前缀0≤R≤S。不进入1536量化slice，浮点输出仅有效前缀定义。

#### Device 数据流

##### 函数级调用链

`swiglu_oai_quant→[group.contiguous]/x.reshape.contiguous→helper→_swiglu_oai_quant_kernel→group读取/分行→整行clamp/sigmoid→浮点store`。无tl.dot/Cube/AIC/MIX或其它自有Kernel，选VV。

##### 源码等价伪码

各program先得到R，q=ceil(R/P)，分行[pq,min((p+1)q,R))并空段返回。每row整行load2D，slice为gate/up；g=min(gate,limit)只限上界，u=clamp(up,-limit,limit)，y=g*sigmoid(g*alpha)*(u+1)。直接store y.to(x.dtype)；不写scale任何元素。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| cur_x/gate/up/y | 整行2D/D/D/D，算术dtype随实际Tritonpromotion；源码不显式先castFP32 |
| group | 每P program读E项，按align64B的E_A张量mask后int32sum |
| quant | 无scale计算/1536临时；返回scaleGM未定义 |
| payload | read2RDdx、write RDdx B |
| workspace/physical UB | 无显式请求/分配；整行SSA与multibufferTrue不确定实际峰值 |

##### 分层内存布局

`strided x→可选packedcopy GM[S,2D]→whole-row SSA→clamp/sigmoid→GMfloatout；scale不写`。groupcontiguouscopy可能另有临时，不将64B逻辑对齐当成无mask读取padding。

##### 字节账与复用顺序

Kernel有效payload逻辑 3RDdx B，再加group P*E*dg B（所有program在earlyreturn前取group）。Host out分配S*D*dx B、scale4S B；x若copy临时2SDdx B且额外读写各2SDdx B，group若copy临时E*dg且额外读写各E*dg。无显式workspace；输出与临时异步存活由Torch/Triton，未定义尾部不得读取。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 分行 | 合法R及int32调度可表示域内无共享写；无atomics/barrier |
| group | 先转int32再sum，非负且和≤int32前提；S/Proundup缺Hostheadroomguard |
| 全行 | 无maskload2D，需packedlayout/storage；整行arange非pow2准入需CANN扩展 |
| 激活精度 | doc称FP32；source loadgate/up未显式toFP32，alpha/limit以float传JIT，实际promotion归compiler，不能补造cast |
| 量化 | SCALEfalse剪去quant全部节点；scale所有元素未定义 |
| tail | 非quant无1536约束，仍受arange/资源准入 |
| lifetime | copy/Kernel框架流依赖，无hostwait；多设备调用先设置currentdevice=x.device |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| group/分核 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/swiglu_oai_quant.py#L37-L56) |
| 激活/选择分支 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/swiglu_oai_quant.py#L58-L99) |
| launcher | [入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/swiglu_oai_quant.py#L102-L146) |

## 算子特定优化

### Trick T-001：设备端group控制有效前缀且不回Host

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/swiglu_oai_quant.py#L37-L49)：

```python
    # MoE: derive total_rows from group_list; dense: use the passed-in total_rows.
    if HAS_GROUP_LIST:
        if (
            GROUP_LIST_TYPE == 0
        ):  # cusum (group_list length = NUM_EXPERTS, last element = total)
            total_rows = tl.load(group_list_ptr + NUM_EXPERTS - 1).to(tl.int32)
        else:
            gl_offsets = tl.arange(0, NUM_EXPERTS_ALGIN)
            gl_mask = gl_offsets < NUM_EXPERTS
            group_list = tl.load(group_list_ptr + gl_offsets, gl_mask, other=0).to(
                tl.int32
            )
            total_rows = tl.sum(group_list)
```

#### 机制与设计原因

累计编码读last，计数编码对E_A范围maskE后转int32sum；总行数留设备端，无Host.item同步。每program重复metadata访问如字节账，不宣称一次全局读。

#### 迁移边界

合法group值/连续化后storage、int32窄化与sum容量；输出padding不定义，调用方只消费R行。

#### 错误做法

把累计表当额外起始哨兵、将group数值回Host校验而仍宣称相同图捕获行为。

### Trick T-002：SCALEfalse编译期剪去量化路径

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/swiglu_oai_quant.py#L96-L99)：

```python
        else:
            # store out
            o_offsets = row_idx * HALF_COLS + tl.arange(0, HALF_COLS)
            tl.store(out_ptr + o_offsets, out.to(out_ptr.dtype.element_ty))
```

#### 机制与设计原因

直接按D列将OAI结果转输入dtypestore，不产生scale值；虽Host仍分配scale，但不应当作已初始化统计。无运行性能结论。

#### 迁移边界

不受1536量化切片约束，仍有整行arange与资源边界；返回scale不可读。

#### 错误做法

把未定义scale当1或0、将float域混入INT8卡。

## 模板与实现对比

本卡只冻结need_quant=false，另一精度域独立producer/文件；三group分支同数学，输入copy与未写前缀边界完整。source不显式先转FP32，公开FP32合同和具体JITpromotion需对应，未虚构指令或physicalUB。

## 平台差异

本卡950归属arch35；公开arch22/35均支持，README/architectures映射A2/A3、950；源无hardware分支。CANN9.1.0 CI固定版本非本次执行/实际binarycompiler一致性；arange、1536slice、multibuffer资源需对应工具链，未扩大成性能保证。

## 限制与失败边界

Direct绕过publiccheck，group数值/标量/shape/device均必要前提；整行、非二次幂扩展、int32roundup和rowoffset容量未guard。仅有效前缀可读，全部scale未定义。未编译、上游运行、测试或校验，无真机/性能/物理分配证据；draft保留明确支持与尚未验证的区分。

## 源码索引

### 链路索引

| 阶段/源码 | 符号 | 事实 |
|---|---|---|
| [公开合同](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/activation/swiglu_oai_quant.md) | `swiglu_oai_quant` | OAI激活/分组/INT8及float两独立语义/平台 |
| [Direct/Device](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/swiglu_oai_quant.py) | `swiglu_oai_quant/_swiglu_oai_quant_kernel` | 完整146行/固定SCALE=false |
| [公共check/转发](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/activation/swiglu_oai_quant.py) | `_check_inputs/_triton_impl` | 只group编码/dtype；Direct不调用 |
| [activation包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/__init__.py) | `module init` | 无Device |
| [设备helper](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py) | `get_device_properties` | current_device、无参cache、两核数assert |
| [import边界](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py) | `_load_sgl_kernel_npu` | torch_npu/原生库与vendor初始化 |
| [backend包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/__init__.py) | `module init` | 懒加载包，无另一Device节点 |
| [构建入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/setup.py) | `main` | 完整Python wheel路径；本次未构建 |
| [源码打包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/build_tools/torch_wheel.py) | `stage_runtime/build_torch/build_wheel/setup_refactor` | 复制完整Python包、原生运行库与wheel |
| [平台/包说明](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md) | `REFACTOR/arch22/35 mapping` | 全部Python实现包含、产品映射、CANN9.1.0构建例 |
| [产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json) | `2201/3510` | a2/a3/950对应构建族 |
| [版本配置](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernels.yml) | `test-norm-ops` | CANN9.1.0/a3/950配置，非本次运行 |
| [CI消费](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernel-group.yml) | `run-kernel-group` | 对应版本容器/测试组参数 |

### 实现复用检查

冻结117/legacy唯一API已全文读并链接，独立冻结浮点语义只创建对应两平台卡，不替换API。全部固定同repo一primary，无verified。
