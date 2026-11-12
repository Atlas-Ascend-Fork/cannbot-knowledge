---
type: Operator
title: "SplitQkvgateGemmaRmsnormRope 950 Direct Invoke 算子知识"
description: "闭合逐head Q/gate解交错、Gemma1+weight的FP32 RMSNorm与NeoX、gate/V输出，保留完整Host及PASS_DIM0和arange编译准入。"
tags: [task.implementation, task.lookup, topic.memory, topic.precision, topic.programming_model]
status: draft
sources:
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/split_qkvgate_gemma_rmsnorm_rope.md
    role: primary
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/norm_utils.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/norm/split_qkv_rmsnorm_rope.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/__init__.py
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/__init__.py
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
created_at: "2026-11-09T09:41:44Z"
updated_at: "2026-11-09T09:41:44Z"
platforms: ["950"]
cann_versions: ["9.1.0"]
---

# SplitQkvgateGemmaRmsnormRope 950 Direct Invoke 算子知识

## 算子速览

唯一入口 `sgl_kernel_npu.implementation.triton.norm.split_qkv_rmsnorm_rope.split_qkvgate_gemma_rmsnorm_rope`，从逐head交错[q0,gate0,q1,gate1,…,K,V]解交错，只对Q/K做FP32 RMSNorm×(1+原始weight)，再NeoX RoPE；gate与V不激活/归一化。完整Host校验、空输入和部分/全旋转两路线闭合。

draft保留全旋转PASS_DIM0的外部slice合同、R/组宽非二次幂arange准入、JIT整数/资源及devicecache边界，公开支持仍注明硬件待验证。复用已全文读的[Gemma API](../../../../apis/sgl_kernel_npu/sgl_qkvgate_gemma_rope.md)，不并入普通QKV、量化或位置cache其它语义。

## 接口与语义

### 计算语义

D维head，`A(x,w)=float(x)*rsqrt(mean(float(x)²)+eps)*(1+float(w))`。Q/K前R列NeoX两半rho=[-x2,x1]：a*cos+rho(a)*sin；后D-R列保留A。gate从对应head的第二D段提取、V从尾部提取，各返回inputdtype；不做Gate sigmoid/SiLU，不加bias。weight必须是原始Gemma偏移，调用方不能预先加1。

### 输入、输出与属性

| 项 | 校验/合同 |
|---|---|
| input | 连续strided三浮点dtype二维[N,2Q+2K]、NPU |
| Q/K/D | 正Pythonint排bool，Q%K=0、K%D=0，D二次幂 |
| R | 正Pythonint、正偶≤D、等于sin/cos末维；未guard二次幂 |
| sin/cos | 连续同deviceFP16/BF16/FP32、ndim≥2、各numel=N*R、重复半表合同 |
| eps | 必选有限正Pythonreal排bool，无跳norm模式 |
| qw/kw | 连续同device三浮点可独立dtype、numel≥D |
| 四输出 | 新连续Q[N,Q]、K/V[N,K]、gate[N,Q]，同inputdtype/device，N0新空，输入不写 |

### 入口与版本

Direct签名(input,sin,cos,q_hidden_size,kv_hidden_size,head_dim,rope_dim,eps,q_weight,k_weight)。冻结短路径加包名前缀精确。auto/triton独立_gate_impl转发；同文件普通QKV函数不可达，torch_native外部参考。SGLcommit `dda6d36b0cdb4081e102d14c0a2fb276fc416e69`；CANN9.1.0为README/CI固定版本非本次运行，完整Triton/CANNextension二进制未固定。

## Host/Launcher 执行流程

### 参数校验与前处理

validate_split_qkvgate→qkv_shape(gatedTrue)/floating/正整及整除/输入宽→D二次幂→rope正整数与trig_tables相等→epsilon→affine/weight；launcher再assertNPU。N0在全部元信息后返回四空Tensor，不查询核数。nonemptyhelper得P，KVblock=nextpow2(D)再assert等D，g=Q/K，Qblock=gD，Qgateblock=2gD，分配四Tensor，nc=K/D、nr=ceil(P/nc)。

### 参数、Workspace 与生命周期

输出GM总N(2Q+2K)dx B，无额外输入连续化/中间激活GM/scoreworkspace。无POD/ACLNN、显式stream/wait/warp/stage。helper无参cache取current_device、双核数正assert，不绑定input.device；多设备属性需相容。Tensor及参数存活/异步流排序由Torch/Triton负责，不虚构物理UB或释放事件。

### 启动图与失败传播

import→validator树→NPUassert→N0空返回或helper/分配→一个JITKernel的Qgate/K/V阶段→返回。assert可被Python-O关闭；分配/JIT异常直接传播，无fallback。全局空dictkernels未参与自有缓存，编译缓存归Triton；包原生库仅导入前提。

## Route 与参数设计

### 分核与资源计算

grid(nr,nc,1)，nc=K/D，nr=ceil(P/nc)；col j处理g组Qgatehead（共2gD输入）与K/V第j个D列head。rowpid以nr步长覆盖N，每payload列恰一次；总programnrnc可能>P，循环前weight在idleprogram也读。Qgate reshape[g,2D]，切出Q/gate各[g,D]。

### Route 选择

H-000=N0无Device；R-001=0<R<D，PASS=D-R正；R-002=R=D，PASS0。没有DO_PARTIAL或is_neoxstyle开关，Kernel总是调用rot/pass的extract/insert；R=D零长度slice不得省略为“源码自动跳过”。

### 模板/实现执行矩阵

两路线均固定必选GemmaRMS、NeoX、无bias；input、sin/cos、qw/kw各独立三浮点dtype组合，共享控制流但字节宽独立。无autotune/tl.dot/Cube/AIC/MIX自有节点。D已二次幂guard，R和2gD的编译准入另需工具链合同。

### 隐藏性能 Guard

g可非二次幂使Qgateblock非二次幂，R也直接用于arange；具体Triton扩展准入未知，不宣称成功/失败。PASS0的extract/insert尺寸为0，源无分支避开，不能用torch_native填补primitive合同。大g/D无UB资源查询，所有rowoffset整数乘积需实际JIT可表示，未显式int64化。

### POD/ABI

| 字段 | 分类/消费 |
|---|---|
| input_ptr/sin_ptr/cos_ptr | runtime输入→packed/trigload |
| q_ptr/k_ptr/v_ptr/gate_ptr | runtime新输出→各store |
| q_weight_ptr/k_weight_ptr | runtime→loadFP32后+1 |
| batch_size | runtimeN→行循环 |
| q_hidden_size/kv_hidden_size/total_hidden_size | constexprQ/K/2Q+2K→偏移/列边界/步长 |
| eps | constexpr→必选RMS分母 |
| Q_BLOCK_SIZE/Q_GATE_BLOCK_SIZE/KV_BLOCK_SIZE | constexprgD/2gD/D→arange/reshape |
| HEAD_DIM/ROPE_DIM/HALF_ROPE_DIM/PASS_DIM | constexprD/R/R2/D-R→统计/切片 |
| grid | (nr,nc,1) |

无自定义序列化POD/字节offset；指针/标量ABI、integerlowering归Triton，不编造位宽。

### Route 源码闭包

实际464–786行完整读取；norm_utils validate_split_qkvgate/qkv_shape/trig_tables/epsilon/affine及vector/floating全部已读；public_gate转发完整读。根setup→stage_runtime完整Python包→build_wheel/setup_refactor，norm/backendinit无Device。al.extract_slice/insert_slice是外部primitive边界，物理拷贝/别名/零尺寸准入不伪造。

## Kernel 实现

### 公共执行流程

循环前读Qweight+1→每token交错Qgate读/切片→Qnorm/NeoX/gate输出；再读Kweight+1→Knorm/NeoX；最后Vcopy。Qgate中gate先转FP32再转回原dtype，V直接原dtype，不能把两个复制过程的位级行为一概等同。

### Route R-001：R<D部分旋转

#### 适用条件

##### 选择证据

N>0、0<R<D；同一个Kernel总是构建rot/pass切片，无DO_PARTIAL分支。PASS_DIM=D-R>0。D已guard二次幂；R及2gD的arange准入仍外部。

#### Device 数据流

##### 函数级调用链

`split_qkvgate_gemma_rmsnorm_rope→validate_split_qkvgate树→helper→split_qkvgate_gemma_rmsnorm_rope_kernel→al.slice/deinterleave→GemmaRMS→NeoX→Q/K/gate/Vstore`，无另一个自有Kernel。

##### 源码等价伪码

col j读交错输入2gD列→reshape[g,2D]→extract第一D为Q、第二D为gate；Q按headFP32rms→乘(1+q_weight)，前R做NeoXrho=[-x2,x1]、后D-R保留，写packedQ；gate从FP32cast回输入dtype写packedgate。K从输入2Q+jD读、按head同GemmaRMS/NeoX；V从2Q+K+jD原dtypecopy。row以nr步长循环。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/流量 |
|---|---|
| Qgate输入 | [g,2D]FP32，8gD B逻辑；Q/gate各[g,D] |
| Q/Knorm与rot/pass | FP32[g,D]/[1,D]、rot[g,R]/[1,R]、pass [g,D-R]/[1,D-R] |
| weight | 每programQ/K各D项读后FP32+1；nr*nc*D*(dwq+dwk) B |
| trig | 每token/col Q/K两阶段各读R项sin/cos：2N*nc*R*(ds+dc) B |
| payload | 输入2Q+2K、四输出合计2Q+2K，各N*(2Q+2K)*dx B |
| workspace/物理UB | 无显式请求，compiler外部；不将切片逻辑规模累加成峰值 |

##### 分层内存布局

`GM交错Q/gate→FP32[g,2D]→Q/gate切片→Qnorm/rope→Q/gateGM；KFP32norm/rope→KGM；V原dtype→VGM`。slice是否别名/复制、寄存器/UB/spill没有产物证据。

##### 字节账与复用顺序

完整调用总逻辑GM `2N*(2Q+2K)*dx + 2N*nc*R*(ds+dc) + nr*nc*D*(dwq+dwk)` B；weightload位于row循环外，无任务program也读。无GM统计矩阵、无workspace交接；全部输入只读，新输出packed，异步存活/stream由框架负责，Q/K阶段不保证物理buffer复用。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 分核 | nr行轮转、ncKVhead列；每列g个Qgatehead，输出不重叠，无atomics/barrier |
| 元信息 | D二次幂、Q/K及K/D整除；R正偶≤D但不guard二次幂 |
| Gemma | loadweight.toFP32后+1只一次，Q/Kfp32rms及rsqrt；没有bias/可选norm |
| RoPE | 仅NeoX两半，不提供GPT-J开关；norm→rope无低精度中间 |
| gate | loadtoFP32后cast回同输入dtype，无norm/激活/rope；有限三浮点值保持数值，不宣称NaNpayload位同 |
| V | 原dtype直接copy；partial尾 保留归一化值 |
| 同步 | SSA与循环由compiler保序，框架stream/物理事件外部 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| 解交错/归一化 | [Qbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L492-L525) |
| NeoX/pass/gate | [Q后续](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L527-L598) |
| K/V | [K/Vbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L602-L703) |


### Route R-002：R=D全旋转与PASS_DIM0

#### 适用条件

##### 选择证据

N>0、R=D；同一个Kernel总是构建rot/pass切片，无DO_PARTIAL分支。PASS_DIM=0，al.extract_slice/insert_slice的零长度sizes合同须具体compiler支持，未假定运行成功或必失败。D已guard二次幂；R及2gD的arange准入仍外部。

#### Device 数据流

##### 函数级调用链

`split_qkvgate_gemma_rmsnorm_rope→validate_split_qkvgate树→helper→split_qkvgate_gemma_rmsnorm_rope_kernel→al.slice/deinterleave→GemmaRMS→NeoX→Q/K/gate/Vstore`，无另一个自有Kernel。

##### 源码等价伪码

col j读交错输入2gD列→reshape[g,2D]→extract第一D为Q、第二D为gate；Q按headFP32rms→乘(1+q_weight)，前R做NeoXrho=[-x2,x1]、后D-R保留，写packedQ；gate从FP32cast回输入dtype写packedgate。K从输入2Q+jD读、按head同GemmaRMS/NeoX；V从2Q+K+jD原dtypecopy。row以nr步长循环。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/流量 |
|---|---|
| Qgate输入 | [g,2D]FP32，8gD B逻辑；Q/gate各[g,D] |
| Q/Knorm与rot/pass | FP32[g,D]/[1,D]、rot[g,R]/[1,R]、pass 零列 |
| weight | 每programQ/K各D项读后FP32+1；nr*nc*D*(dwq+dwk) B |
| trig | 每token/col Q/K两阶段各读R项sin/cos：2N*nc*R*(ds+dc) B |
| payload | 输入2Q+2K、四输出合计2Q+2K，各N*(2Q+2K)*dx B |
| workspace/物理UB | 无显式请求，compiler外部；不将切片逻辑规模累加成峰值 |

##### 分层内存布局

`GM交错Q/gate→FP32[g,2D]→Q/gate切片→Qnorm/rope→Q/gateGM；KFP32norm/rope→KGM；V原dtype→VGM`。slice是否别名/复制、寄存器/UB/spill没有产物证据。

##### 字节账与复用顺序

完整调用总逻辑GM `2N*(2Q+2K)*dx + 2N*nc*R*(ds+dc) + nr*nc*D*(dwq+dwk)` B；weightload位于row循环外，无任务program也读。无GM统计矩阵、无workspace交接；全部输入只读，新输出packed，异步存活/stream由框架负责，Q/K阶段不保证物理buffer复用。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 分核 | nr行轮转、ncKVhead列；每列g个Qgatehead，输出不重叠，无atomics/barrier |
| 元信息 | D二次幂、Q/K及K/D整除；R正偶≤D但不guard二次幂 |
| Gemma | loadweight.toFP32后+1只一次，Q/Kfp32rms及rsqrt；没有bias/可选norm |
| RoPE | 仅NeoX两半，不提供GPT-J开关；norm→rope无低精度中间 |
| gate | loadtoFP32后cast回同输入dtype，无norm/激活/rope；有限三浮点值保持数值，不宣称NaNpayload位同 |
| V | 原dtype直接copy；partial尾 0列slice需要实际扩展合同 |
| 同步 | SSA与循环由compiler保序，框架stream/物理事件外部 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| 解交错/归一化 | [Qbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L492-L525) |
| NeoX/pass/gate | [Q后续](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L527-L598) |
| K/V | [K/Vbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L602-L703) |

## 算子特定优化

### Trick T-001：按head切片解交错而非先搬运重排输入

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L500-L519)：

```python
        col_indices = col_pid * Q_GATE_BLOCK_SIZE + tl.arange(0, Q_GATE_BLOCK_SIZE)
        valid_mask = col_indices < qgate_hidden_size
        input_values = (
            tl.load(input_ptr + input_offset + col_indices, mask=valid_mask, other=0.0)
            .to(tl.float32)
            .reshape(Q_BLOCK_SIZE // HEAD_DIM, HEAD_DIM * 2)
        )
        q = al.extract_slice(
            input_values,
            offsets=(0, 0),
            sizes=(Q_BLOCK_SIZE // HEAD_DIM, HEAD_DIM),
            strides=(1, 1),
        ).reshape(Q_BLOCK_SIZE // HEAD_DIM, HEAD_DIM)

        gate = al.extract_slice(
            input_values,
            offsets=(0, HEAD_DIM),
            sizes=(Q_BLOCK_SIZE // HEAD_DIM, HEAD_DIM),
            strides=(1, 1),
        ).reshape(Q_BLOCK_SIZE // HEAD_DIM, HEAD_DIM)
```

#### 机制与设计原因

输入reshape[g,2D]，以两个D列slice分Q/gate；无需GM预先整理全部Q和全部gate。物理slice可能由compiler重新编排，不声称零copy或具体UB布局。

#### 迁移边界

输入必须逐headQ/gate交错、g组一列，错误的“全Q后全gate”会消费错值。gate不激活，仅输出。

#### 错误做法

把Q_GATE_BLOCK_SIZE解释为连续Q块，或对gate也乘Gemmaweight/做sigmoid。

### Trick T-002：原始Gemma偏移只加一次1

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L615-L621)：

```python
        squares = input_values * input_values
        variances = tl.sum(squares, axis=1) / HEAD_DIM
        reciprocal_std = tl.rsqrt(variances + eps).reshape(KV_BLOCK_SIZE // HEAD_DIM, 1)
        normalized_values = (
            input_values * reciprocal_std
        )  # (KV_BLOCK_SIZE/HEAD_DIM, HEAD_DIM)
        normalized_values = normalized_values * weight_values
```

Q/K循环外分别第492/603行loadweightFP32后+1，此连续K片段消费已加1的weight_values。

#### 机制与设计原因

把1+w准备在token循环外，FP32norm后直接乘它，避免每个token重复加1；权重读取次数按nrnc计。无性能实测。

#### 迁移边界

qw/kw须原始偏移，norm与rope间保FP32；不要用普通RMSNorm已经准备的实际乘数。

#### 错误做法

调用前加1又在Kernel加1，或套普通QKV带bias/跳norm语义。

## 模板与实现对比

两路线仅旋转长度及PASS0的primitive准入不同；非空固定必选norm/NeoX。Gemma1+w、gate交错/返回与普通QKV不同，独立冻结任务建卡；poscache两次BF16语义未混入。支持声明/源码closure与真机成功分开。

## 平台差异

本卡950归属arch35；公开arch22/35支持但实际硬件执行待验证，README/architectures映射A2/A3、950。无hardware分支，CANN9.1.0 CI配置不是实际compiler版本一致性/A2实测；资源lowering及零尺寸slice合同需匹配工具链。

## 限制与失败边界

assert可关闭，R/组宽arange、PASS0slice、资源/地址整数域未完整guard。FP32可溢出、NaNpayload不保证位同；只在公开有限输入及可定义中间值域做数学参考。无构建、运行、测试或校验/性能/物理UB产物，draft保留实际边界。

## 源码索引

### 链路索引

| 阶段/源码 | 符号 | 事实 |
|---|---|---|
| [公开合同](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/split_qkvgate_gemma_rmsnorm_rope.md) | `split_qkvgate_gemma_rmsnorm_rope` | 逐headQ/gate/Gemma1+w/NeoX/平台 |
| [Direct/Device](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py) | `split_qkvgate_gemma_rmsnorm_rope[_kernel]` | 独立可达464–786行 |
| [校验树](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/norm_utils.py) | `validate_split_qkvgate/qkv_shape/trig_tables/affine` | 含D二次幂与eps必选 |
| [公开转发](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/norm/split_qkv_rmsnorm_rope.py) | `_gate_triton_impl` | 独立Gemma入口 |
| [属性helper](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py) | `get_device_properties` | 无参cache/currentdevice |
| [import边界](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py) | `_load_sgl_kernel_npu` | torch_npu/原生库与vendor初始化 |
| [backend包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/__init__.py) | `module init` | 懒加载包，无另一Device节点 |
| [norm包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/__init__.py) | `module init` | 无附加启动节点 |
| [构建入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/setup.py) | `main` | 完整Python wheel路径；本次未构建 |
| [源码打包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/build_tools/torch_wheel.py) | `stage_runtime/build_torch/build_wheel/setup_refactor` | 复制完整Python包、原生运行库与wheel |
| [平台/包说明](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md) | `REFACTOR/arch22/35 mapping` | 全部Python实现包含、产品映射、CANN9.1.0构建例 |
| [产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json) | `2201/3510` | a2/a3/950对应构建族 |
| [版本配置](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernels.yml) | `test-norm-ops` | CANN9.1.0/a3/950配置，非本次运行 |
| [CI消费](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernel-group.yml) | `run-kernel-group` | 对应版本容器/测试组参数 |

### 实现复用检查

冻结117/legacy唯一GemmaAPI已全文读并链接，不重复API；普通QKV只共享文件/校验helper并非同语义Operator。全部固定同repo唯一primary、无verified。
