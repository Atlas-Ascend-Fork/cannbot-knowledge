---
type: Operator
title: "SplitQkvTpRmsnormRopeTp1 A2/A3 Direct Invoke 算子知识"
description: "闭合tp_world1的QKV拆分本地均方与RMS/RoPE双Kernel图，记录补偿式累加、8B统计GM与低dtype写回重读精度边。"
tags: [task.implementation, task.lookup, topic.memory, topic.precision, topic.programming_model]
status: draft
sources:
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/split_qkv_tp_rmsnorm_rope.md
    role: primary
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_tp_rmsnorm_rope.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/norm/split_qkv_tp_rmsnorm_rope.py
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
created_at: "2026-11-09T10:16:37Z"
updated_at: "2026-11-10T07:06:47Z"
platforms: [a2, a3]
cann_versions: ["9.1.0"]
---

# SplitQkvTpRmsnormRopeTp1 A2/A3 Direct Invoke 算子知识

## 算子速览

`sgl_kernel_npu.implementation.triton.norm.split_qkv_tp_rmsnorm_rope.split_qkv_tp_rmsnorm_rope` 独立冻结 `tp_world=1,tp_group=None`：Q/K本地全通道均方并copyQ/K/V→带通道weight归一化、写回低dtype、再同Kernel重读NeoX旋转。两自有Device节点均无dot/Cube，按VV完整闭合；原多卡dist.all_reduce缺Device源仍defer，不以此TP1卡替代全域。

draft保留未完整guard的输入、arange/资源与整数范围、GM写后重读的compiler/流合同及无运行证据；复用全文读过的[TP API](../../../../apis/sgl_kernel_npu/sgl_qkv_tp_rmsnorm_rope.md)。

## 接口与语义

### 计算语义

输入[B,Q+2K]按Q/K/V拆。每token Q在整个Q宽求均方、K在整个K宽求均方，不是每head独立均方。TP1时globalvar=localvar。`qn=cast_inputdtype(FP32(q)*rsqrt(qvar+eps)*qw)`，kn同理；随后重读qn/kn转FP32，仅每head前R做NeoX两半旋转，再转inputdtype。后D-R保留已归一化低dtype值。V原值copy。qw/kw为本地Q/K各通道向量，不是共享D元素权重。

### 输入、输出与属性

| 项 | 公开合同/Direct |
|---|---|
| input | 同NPU稠密FP16/BF16/FP32[B,Q+2K]；Direct未检查连续/宽/全部dtype |
| Q/K/D | Q为K整数倍，K含完整Dhead，D正二次幂；Direct仅Dpow2与Q%Kassert |
| cos/sin | 同device稠密[B,R]浮点，各只使用每行前R/2项 |
| qw/kw | 同device稠密[Q]/[K]浮点，可按公开合同独立dtype |
| R/eps | R正偶≤D；eps正有限建议，Direct无完整guard |
| TP | 冻结world1/groupNone，inv_tp_world1，all_reduce分支不可达 |
| output | 新连续Q[B,Q]、K/V[B,K] inputdtype/device；B0新空三Tensor，输入不写 |

### 入口与版本

Direct签名(input,cos,sin,Q,K,D,eps,q_weight,k_weight,rotary_dim,tp_world,tp_group)。无新wrapper，冻结参数域明确。auto/triton只转发，torch_native独立参考不并入图。固定SGLcommit `dda6d36b0cdb4081e102d14c0a2fb276fc416e69`，CANN9.1.0为README/CI配置非本次运行，Triton二进制未完整固定。

## Host/Launcher 执行流程

### 参数校验与前处理

KVblock=nextpow2(D)assert==D，assertQ%K0；Qblock=(Q/K)D；分配Q/K/V后B0返回。nonemptyhelper得P，grid n=min(B,P)，qheads=Q//D、kheads=K//D，分配qk_var[B,2]FP32。PAD_Q/K/QH/KH/HALF均nextpow2对应宽/heads/R2。没有public额外输入guard或contiguouscopy。

### 参数、Workspace 与生命周期

输出payload B(Q+2K)dx B，内部GM统计scratch8B B；无请求方workspace/POD/ACLNN。helper无参cache/current_device双核数assert，未绑定inputdevice；输出/统计跨两Kernel存活在launcher局部引用中，函数返回后临时异步释放由frameworkallocator负责，无手动free/wait/stream。

### 启动图与失败传播

import→assert/输出→B0返回或helper→qk_var→K1(split/copy/localvar)→TP1跳collective→K2(norm/rope)→return。按当前框架流顺序保证K1统计/输出对K2可见，源码无独立event/hostwait。world>1的dist.all_reduce在本冻结域不可达，它是原全域核心节点缺源，不当普通框架前处理隐藏。异常传播，无fallback。

## Route 与参数设计

### 分核与资源计算

两Kernel相同grid n；pid先toint64，循环idx=pid+j*n<B，一token一owner。K1对Q/K按Qblock/KVblock分块，遍历范围PAD_Q/PAD_K并mask真实Q/K；chunk平方和以补偿式scalar更新sum/comp。K2分块归一化同Q/K块，旋转则以PAD_QH/KH×PAD_HALF逻辑矩阵处理所有head，不由Qblock限制峰值。

### Route 选择

| Host/Route | 条件 | 图 |
|---|---|---|
| H-000 | B0且先前assert通过 | 仅空输出 |
| R-001 K1 | B>0 TP1 | 全Q/K本地均方+Q/K/Vcopy |
| R-002 K2 | K1完成 TP1 | norm→低dtype写/重读→全或部分NeoX |

R是正偶≤D参数，不含GPT-J/跳norm/bias选项；全R=D与部分R<D使用相同mask化旋转body，尾无额外copyKernel。

### 模板/实现执行矩阵

输入三浮点、weight/trig独立浮点，显式FP32平方/scale/rope，输出inputdtype两次边界；Qblock/KVblock和PADwidth/head/half specialization均列入ABI。自有节点无tl.dot/Cube/AIC/MIX，确认为VV而非按目录默认。

### 隐藏性能 Guard

Qblock=(Q/K)D可能非二次幂而直接arange，具体CANNextension准入未知；Dpow2不足以保证所有Q/K比合法编译。旋转PADheads×PADhalf可能大，无UB容量查询/guard。直接参数R非法可使head内读跨越D，公共合同必须保证。pid.toint64有利rowoffset，但所有尺寸/参数乘积仍需实际JIT可表示，不宣称无限范围。

### POD/ABI

| 节点/字段 | 消费 |
|---|---|
| K1 input_ptr/q_out_ptr/k_out_ptr/v_out_ptr/qk_var_ptr | runtime输入读/三个payload写/两统计写 |
| K1 batch_size | runtimeB→token循环 |
| K1 q_cols/k_cols | constexprQ/K→段起点/行步长/mask/均方除数 |
| K1 PAD_Q/PAD_K | constexprnextpow2Q/K→staticchunk范围 |
| K1 KV_BLOCK_SIZE/Q_BLOCK_SIZE | constexprD/(Q/K)D→chunkarange |
| K2 q_ptr/k_ptr | runtime自有输出，norm与rope原地读写 |
| K2 cos_ptr/sin_ptr/q_weight_ptr/k_weight_ptr/qk_global_var_ptr | runtime只读输入/统计 |
| K2 rotary_dim/eps/inv_tp_world | constexprR/eps/1→旋转/分母 |
| K2 batch_size/q_num_heads/k_num_heads | runtimeB/QD/KD→循环/headmask |
| K2 q_cols/k_cols/head_dim | constexprQ/K/D→地址/headstride |
| K2 PAD_Q/PAD_K/PAD_QH/PAD_KH/PAD_HALF | constexpr向上二次幂宽/heads/R2→chunk与旋转mask |
| K2 Q_BLOCK_SIZE/KV_BLOCK_SIZE | constexpr同K1→normchunk |
| grids | 均(n,) |

无自定义序列化POD/offset，指针/标量ABI外部。所有真实字段均列，无collectiveworkspace或多卡通信参数在TP1Device中消费。

### Route 源码闭包

完整249行Direct及两Kernel、public转发/helper已读；无自有未知函数。根setup→stage_runtime完整Python包→build_wheel/setup_refactor，norm/backendinit无Device。外部框架分配/primitive明确，原all_reduce缺口只因冻结TP1排除，不宣称全域已闭合。

## Kernel 实现

### 公共执行流程

K1完整定义Q/K/V及qk_var，K2消费统计并在自有Q/K输出上norm再rope；V保持K1结果。两个Kernel和K2内部GM往返是完整任务图，不简化成单Kernel全FP32表达式。

### Route R-001：拆分与补偿式本地均方

#### 适用条件

##### 选择证据

B>0、合法稠密shape/参数、TP1；K1grid min(B,P)。

#### Device 数据流

##### 函数级调用链

`launcher→_split_qkv_and_compute_local_qk_var_kernel→load/toFP32/sum→scalarcompensation→store`。Q/K/Vcopy与统计都在此节点。

##### 源码等价伪码

pidint64，逐idx：对Q每Qblock从PAD_Q范围maskedload真实Q，平方sumFP32得chunk；y=chunk-comp,t=sum+y,comp=(t-sum)-y,sum=t；原dtype值写Qout，var=sum/Q。K同样D块→var/K；V原dtypecopy，写qk_var[idx,0/1]。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模 |
|---|---|
| Q/K chunk | Qblock/D原dtype及FP32值/平方，physical峰值未知 |
| scalar carry | q_sum/q_comp/k_sum/k_comp FP32，各独立更新 |
| input/output | 读/写各B(Q+2K)dx B |
| qk_var | 写8B B，GM[B,2]FP32 |
| workspace | 无额外请求，自有统计scratch已由Host分配 |

##### 分层内存布局

GMpackedQKV→chunkFP32square→sum/comp→GMlocalvar；payload原dtype直接写三GM输出。不物化完整FP32输入或平方GM。

##### 字节账与复用顺序

K1读B(Q+2K)dx、写同量payload+8B B。输出与统计全部定义后经框架流交K2；无手动free；变量comp的数学补偿意图可见，不承诺具体compiler重排后的误差界。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| chunk尾 | q/k/vmask真实宽，other0；PAD范围多做的lane不读真实GM |
| 归约 | chunkFP32平方和，chunk间补偿式scalar更新；均方除Q/K，不除PAD |
| 索引 | pid显式int64，idx来自该循环；其它参数可表示域仍须核对 |
| output | 原dtypecopy，qk_varFP32 |
| 核间 | tokenowner唯一，无atomic/barrier；K1→K2框架流顺序 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| Q补偿/copy | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_tp_rmsnorm_rope.py#L24-L46) |
| K/V/统计 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_tp_rmsnorm_rope.py#L48-L74) |

### Route R-002：全通道RMS后低dtype往返与NeoX

#### 适用条件

##### 选择证据

K1完成，TP1 inv_tp_world1，R正偶≤D、完整head；没有多卡收集路线。

#### Device 数据流

##### 函数级调用链

`launcher→_apply_global_rmsnorm_kernel→loadvar/sqrt→Q/K分块norm并cast/store→GMreload→FP32NeoX/store`，无第二个旋转Kernel。

##### 源码等价伪码

idx行读q/kvar×1，scale=1/sqrt(var+eps)。Q/K分块读原dtype值与逐通道weight.toFP32，乘scale/weight→to原dtype→写回。读cos/sin前R/2FP32，headmask与halfmask构造两半地址，重读Q/K低dtype→FP32，算两式→cast原dtype写旋转区。尾部保留前norm写回。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/流量 |
|---|---|
| normchunk | Qblock/D FP32，weight同块；每token权重Q/K |
| rope matrices | PAD_QH/KH×PAD_HALF原dtype/FP32/结果；无physicalbuffer证据 |
| var | 每token2FP32共8B B读 |
| Q/Knorm | 读/写各B(Q+K)dx B；weight读B(Qdwq+Kdwk) B |
| Q/Krope | 旋转区读/写各B(Hq+Hk)Rdx B |
| trig | 每token前R/2两表，共B*(R/2)*(dc+ds) B |
| V | 不再读写，保持K1结果 |

##### 分层内存布局

`GMqk_var→scaleFP32；GMQ/K→normFP32→原dtypeGM→重新load→FP32rope→原dtypeGM`。此显式GM往返是精度边界，不能仅以融合Kernel消除。

##### 字节账与复用顺序

K2逻辑总 `8B + 2B(Q+K)dx + B(Qdwq+Kdwk) + 2B(Hq+Hk)Rdx + B*(R/2)*(dc+ds)` B。stat8B scratch、payload自有Q/KGM贯穿K2；normstore→rope load为同program的潜在别名GM读后写依赖，由Triton load/store/lowering合同保证真实顺序，源码没有显式barrier，不能填造MTEevent或hostwait。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 精度 | FP32norm后明确to(q_vals.dtype)/store，旋转重读低dtype，不能替代全FP32融合 |
| 旋转mask | head_index<真实q_num_heads或k_num_heads（按Q/K分别）且half<R2；PAD_QH/PAD_KH仅决定arange补齐规模，使用真实Dheadstride，不要求heads/R2二次幂 |
| trig | 只读各行前R2，other0padding，后半物理不读 |
| tail | norm已写全部Q/K列，rope只改前R，后D-R保留norm低dtype |
| 同步 | K1→K2依流；K2内部GMstore/reload依compilerprimitive顺序，无显式event |
| 数值 | finite也可能平方/乘法溢出，eps未guard；未证明误差/性能 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| norm写低dtype | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_tp_rmsnorm_rope.py#L106-L132) |
| 重读与NeoX | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_tp_rmsnorm_rope.py#L134-L170) |

## 算子特定优化

### Trick T-001：分块平方和使用补偿式scalar更新

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_tp_rmsnorm_rope.py#L35-L46)：

```python
        for q_off in tl.static_range(0, PAD_Q, Q_BLOCK_SIZE):
            q_offsets = q_off + tl.arange(0, Q_BLOCK_SIZE)
            q_mask = q_offsets < q_cols
            q_vals = tl.load(q_in_base + q_offsets, mask=q_mask, other=0.0)
            q_vals_f32 = q_vals.to(tl.float32)
            q_chunk = tl.sum(q_vals_f32 * q_vals_f32, axis=0)
            y = q_chunk - q_comp
            t = q_sum + y
            q_comp = (t - q_sum) - y
            q_sum = t
            tl.store(q_out_base + q_offsets, q_vals, mask=q_mask)
        q_var = q_sum / q_cols
```

#### 机制与设计原因

每chunkFP32平方和后用sum/comp修正累加误差，避免整QFP32常驻归约；Qcopy复用同次原dtype加载。源码意图可复验，不给未测误差或物理UB上限。

#### 迁移边界

Q/K真实宽作均方分母，chunkmaskother0与compiler不破坏所需数值顺序；Qblockarange准入需实际工具链。

#### 错误做法

按每headD归约改变TP全通道统计，或除PAD_Q而非Q。

### Trick T-002：保留归一化到RoPE间的dtype舍入

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_tp_rmsnorm_rope.py#L113-L121)：

```python
        for q_off in tl.static_range(0, PAD_Q, Q_BLOCK_SIZE):
            q_offsets = q_off + tl.arange(0, Q_BLOCK_SIZE)
            q_mask = q_offsets < q_cols
            q_vals = tl.load(q_base + q_offsets, mask=q_mask, other=0.0)
            q_weight = tl.load(q_weight_ptr + q_offsets, mask=q_mask, other=1.0).to(
                tl.float32
            )
            q_vals = (q_vals.to(tl.float32) * q_scale * q_weight).to(q_vals.dtype)
            tl.store(q_base + q_offsets, q_vals, mask=q_mask)
```

随后第151–158行重新load原dtypeQ并FP32旋转；K第124–132/163–170同构。

#### 机制与设计原因

norm结果先to原dtype写GM，后续读取再提升FP32，符合该入口明确的精度边界；没有把融合单Kernel当作消除rounding的许可。

#### 迁移边界

必须保持cast/store/reload语义与compilerordering，weight为逐本地Q/K通道。TP1不包含多卡collective。

#### 错误做法

保留FP32normSSA直接rope、套非TP按head共享Dweight，或宣称本卡闭合了HCCL。

## 模板与实现对比

两Kernel唯一TP1域，空B只Host；原world>1核心all_reduce缺源继续defer。两次低dtype写回与非TPFP32连算不同。stat8B GM临时与K2内部GM再读均完整计费，无物理UB猜测。

## 平台差异

本卡A2/A3归属arch22；公开arch22/35支持，README/architectures映射A2/A3、950，无hardwarebranch。CANN9.1.0 CI配置非本次执行/A2实测或二进制同版本一致；资源lowering/GMordering需实际compiler合同。

## 限制与失败边界

冻结TP1必须保持，Direct缺完整dtype/shape/stride/R/epsguard；Qblock非二次幂、资源/整数域未全guard。无构建、真机、上游测试/校验、数值/性能结果，draft不作无条件安全复用；未修源/未冒充多卡实现。

## 源码索引

### 链路索引

| 阶段/源码 | 符号 | 事实 |
|---|---|---|
| [公开合同](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/split_qkv_tp_rmsnorm_rope.md) | `split_qkv_tp_rmsnorm_rope` | 通道RMS/TP/低dtype边界/NeoX/平台 |
| [Direct及两Device](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_tp_rmsnorm_rope.py) | `split_qkv_tp_rmsnorm_rope/_split_qkv_and_compute_local_qk_var_kernel/_apply_global_rmsnorm_kernel` | 完整249行；冻结TP1跳collective |
| [公开转发](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/norm/split_qkv_tp_rmsnorm_rope.py) | `_triton_impl` | 无guard只转发 |
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

冻结117同主题TP API已全文读并链接，原全TPdefer；本独立TP1predicate新增两卡，未覆盖API/未把collective当框架前处理。全部固定同repo一primary，无verified。
