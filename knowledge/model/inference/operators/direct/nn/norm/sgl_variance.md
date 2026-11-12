---
type: Operator
title: "FusedVariance A2/A3 Direct Invoke 算子知识"
description: "闭合局部均方的八个Triton候选、FP32行归约与统计量GM流量，明确调用方AVG、block_l96编译准入与未guard输入边界。"
tags: [task.implementation, task.lookup, topic.memory, topic.precision, topic.parallelism]
status: draft
sources:
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/fused_variance.md
    role: primary
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/norm/rmsnorm_split.py
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
created_at: "2026-11-09T09:17:25Z"
updated_at: "2026-11-09T09:24:37Z"
platforms: [a2, a3]
cann_versions: ["9.1.0"]
---

# FusedVariance A2/A3 Direct Invoke 算子知识

## 算子速览

唯一入口 `sgl_kernel_npu.implementation.triton.norm.rmsnorm_split.fused_variance(x)`，计算FP32局部均方 `Σ_c x[b,l,c]²/C`，新输出[B,L,1]。它是TP RMSNorm的第一阶段，不减均值，也不包含归一化或隐式all_reduce。八个autotune配置全部登记；源码闭包与编译/运行成功分开。

保留draft：输入合同未guard；block_l=96候选直接用于arange，是否由对应CANN Triton扩展接受尚未固定；物理资源由compiler决定，未虚构UB峰值。已有[局部统计与缩放API](../../../../apis/sgl_kernel_npu/sgl_tp_rmsnorm_statistics.md)已完整阅读并复用。

## 接口与语义

### 计算语义

`v[b,l,0]=(Σ_{c=0}^{C-1} x[b,l,c]*x[b,l,c])/C`，真实顺序先平方再tl.sum再除C；限定公开生产FP32，不扩大到任意dtype。若均匀通道分片用于TP，调用方随后做all_reduce(AVG)才能得到全局均方；该通信不是本Direct入口可达节点，卡片不把它画作内部launch。

### 输入、输出与属性

| 项 | 合同 |
|---|---|
| x | 有限FP32、连续NPU[B,L,C]、B/L/C>0、C二次幂 |
| 返回output | torch.empty((B,L,1),device=x.device,dtype=x.dtype)，新输出同dtype/device |
| 修改 | 输入只读，无统计累加、无eps/weight或其它属性 |

### 入口与版本

冻结短路径 `implementation.triton.norm.rmsnorm_split.fused_variance` 加包名前缀为精确入口。auto/triton门面只转发，torch_native另属外部参考；同文件fused_rsqrt_mul是另一个逻辑算子，此次不产其卡。固定SGL commit `dda6d36b0cdb4081e102d14c0a2fb276fc416e69`，CANN9.1.0来自README/CI配置，并非本次运行。未固定完整Triton二进制/primitive扩展版本。

## Host/Launcher 执行流程

### 参数校验与前处理

先helper获取P=num_vectorcore，读取x.shape前三维，grid(P,)，新分配[B,L,1]并launch。无dim/stride/dtype/device/Cguard；平铺寻址忽略stride。helper无参cache首次取current_device，assertAIC和vector两核数>0；未按x.device设置guard，切设备后属性相容是外部使用前提。

### 参数、Workspace 与生命周期

无自有tiling、POD、ACLNN executor或workspace；output由Torch持有、Triton异步使用。未显式设置stream、num_warps或num_stages；不能填默认数字/物理缓冲深度。autotune可多次测量候选，框架临时资源及同步由Triton负责；输入只读、有效输出每次覆盖，源码无跨次累计。

### 启动图与失败传播

包import初始化→helper→shape读取→empty→autotune/JIT单Kernel→返回output。helperassert、shape索引、分配、JIT/launch异常直接传播，无fallback。包__init__加载torch_npu和原生动态库是导入前提，不是此body调用原生算子；没有通信stream/collective。

## Route 与参数设计

### 分核与资源计算

N=B*L、P>0、tile b、T=ceil(N/b)。p∈[0,P)处理q=p+jP<T；任务按模P唯一覆盖，每任务b行全C列，余行load other0并maskstore。逻辑输入tile4bC B，统计量各4b B；不能相加为实际UB峰值。所有尺寸/offset须在实际JIT整数类型可表示域。

### Route 选择

八候选b=[96,64,32,16,8,4,2,1]，只显式key num_tokens；内部specialization缓存还归compiler。无静态shape到最佳b规则，不把列表当实际胜者顺序。

### 模板/实现执行矩阵

| Route | b | 逻辑tile | 可达边界 |
|---|---:|---|---|
| R-001 | 96 | 96×C FP32 | arange非二次幂端点须核对扩展合同 |
| R-002 | 64 | 64×C FP32 | 依赖compiler资源准入，未编译 |
| R-003 | 32 | 32×C FP32 | 依赖compiler资源准入，未编译 |
| R-004 | 16 | 16×C FP32 | 依赖compiler资源准入，未编译 |
| R-005 | 8 | 8×C FP32 | 依赖compiler资源准入，未编译 |
| R-006 | 4 | 4×C FP32 | 依赖compiler资源准入，未编译 |
| R-007 | 2 | 2×C FP32 | 依赖compiler资源准入，未编译 |
| R-008 | 1 | 1×C FP32 | 依赖compiler资源准入，未编译 |

自有body无tl.dot/Cube/AIC/MIX节点。读取vector核数不等于可推定其物理寄存器或SIMT映射。

### 隐藏性能 Guard

C二次幂约束不能被dim mask绕开。b96也非二次幂，保留真实候选而不改源；可能扩展支持或拒绝须由具体工具链证据决定。源码无UB容量查询/切C逻辑，大C和大b不可自动保证资源足够。

### POD/ABI

| 参数 | 类别/消费 |
|---|---|
| x_ptr | Tensor→输入maskedload |
| output_ptr | 新Tensor→每行统计store |
| num_tokens | B*L runtime→任务数/rowmask |
| hidden_size | C constexpr→arange、行步长、除数 |
| block_l | autotune constexpr→行块/arange |
| kernel_num | P constexpr→任务步长 |
| grid | (P,) |

无自定义序列化POD，字段位宽、Tensor地址ABI与实际同步是框架边界，不编造字段偏移。

### Route 源码闭包

完整rmsnorm_split文件及public转发/helper已读，实际入口只触发variance body。根setup.py→torch_wheel.stage_runtime复制完整Python包→build_wheel/setup_refactor打包；norm/backend包无新增Device。公共库导入依赖明示，未借另一归一化实现补齐本body。

## Kernel 实现

### 公共执行流程

每任务一次maskedload→平方和→除C→masked统计store；不写原输入，不落平方临时GM，无共享输出行与跨program归约。八配置逐项如下。

### Route R-001：block_l=96

#### 适用条件

##### 选择证据

[配置与key](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L99-L127) 中候选1为block_l=96。公开域为FP32连续NPU[B,L,C]且B/L/C正、C二次幂。本配置96非二次幂而直接参与tl.arange端点；当前Triton扩展是否接受是未固定的compiler准入边界，不能把它当成已编译通过。autotune胜者未知，候选表顺序不是静态优先级。

#### Device 数据流

##### 函数级调用链

`fused_variance→autotune/JIT→fused_variance_kernel→tl.load/sum/store`。只有这一个自有Device body，本候选tile=96×C；不启动文件同居的fused_rsqrt_mul。

##### 源码等价伪码

N=B*L，P>0；program p轮转q=p+jP<ceil(N/96)。r=q*96+arange(96)，c=arange(C)，load x[r*C+c]，r<N掩码、无效补0；sum(x*x,axis1)/C；按r<N写output[r]。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/实际有效GM |
|---|---|
| 输入tile/平方 | 各96C个FP32逻辑元素；每个逻辑张量4*96C B |
| sum/variance | 各96个FP32行量 |
| GM输入 | 有效m行时4mC B读取，m=min(96,N-q*96) |
| GM输出 | 4m B写入，连续[B,L,1] |
| 物理UB/寄存器/工作区 | 无显式分配；不能从SSA元素数推断实际峰值 |

##### 分层内存布局

`GM x[N,C]→masked SSA[96,C]→sum[96]→mean-square[96]→GM output[N,1]`。无TQue/TBuf声明；compiler自行融合/复用/spill，不伪造分层地址。

##### 字节账与复用顺序

在配置可编译且尺寸可表示域内，一次完整有效调用读4NC B、写4N B，总4N(C+1) B，不计autotune重复测量或缓存物理事务。输入只读；新输出在launch前分配，框架持有至异步完成；无请求方workspace、无跨kernel中间缓存或通信资源。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 核间 | q余数唯一覆盖、不共享写，无原子/barrier |
| 核内 | SSA依赖由Triton lowering保序，无显式物理事件 |
| 尾行 | mask同时控制load和store，load other0；C无padding/分片 |
| FP32 | x*x→sum→除C；无减均值、无eps、无rsqrt，溢出/非有限值不修复 |
| 准入 | arange(0,96)的非二次幂端点需要具体CANN Triton合同，未宣称成功或必失败 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| fused_variance_kernel | [完整body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L129-L154) |
| fused_variance | [launcher](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L157-L165) |


### Route R-002：block_l=64

#### 适用条件

##### 选择证据

[配置与key](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L99-L127) 中候选2为block_l=64。公开域为FP32连续NPU[B,L,C]且B/L/C正、C二次幂。本配置行块为二次幂；仍依赖当前Triton编译/资源准入，未实测。autotune胜者未知，候选表顺序不是静态优先级。

#### Device 数据流

##### 函数级调用链

`fused_variance→autotune/JIT→fused_variance_kernel→tl.load/sum/store`。只有这一个自有Device body，本候选tile=64×C；不启动文件同居的fused_rsqrt_mul。

##### 源码等价伪码

N=B*L，P>0；program p轮转q=p+jP<ceil(N/64)。r=q*64+arange(64)，c=arange(C)，load x[r*C+c]，r<N掩码、无效补0；sum(x*x,axis1)/C；按r<N写output[r]。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/实际有效GM |
|---|---|
| 输入tile/平方 | 各64C个FP32逻辑元素；每个逻辑张量4*64C B |
| sum/variance | 各64个FP32行量 |
| GM输入 | 有效m行时4mC B读取，m=min(64,N-q*64) |
| GM输出 | 4m B写入，连续[B,L,1] |
| 物理UB/寄存器/工作区 | 无显式分配；不能从SSA元素数推断实际峰值 |

##### 分层内存布局

`GM x[N,C]→masked SSA[64,C]→sum[64]→mean-square[64]→GM output[N,1]`。无TQue/TBuf声明；compiler自行融合/复用/spill，不伪造分层地址。

##### 字节账与复用顺序

在配置可编译且尺寸可表示域内，一次完整有效调用读4NC B、写4N B，总4N(C+1) B，不计autotune重复测量或缓存物理事务。输入只读；新输出在launch前分配，框架持有至异步完成；无请求方workspace、无跨kernel中间缓存或通信资源。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 核间 | q余数唯一覆盖、不共享写，无原子/barrier |
| 核内 | SSA依赖由Triton lowering保序，无显式物理事件 |
| 尾行 | mask同时控制load和store，load other0；C无padding/分片 |
| FP32 | x*x→sum→除C；无减均值、无eps、无rsqrt，溢出/非有限值不修复 |
| 准入 | 资源/整数lowering属于外部compiler合同 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| fused_variance_kernel | [完整body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L129-L154) |
| fused_variance | [launcher](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L157-L165) |


### Route R-003：block_l=32

#### 适用条件

##### 选择证据

[配置与key](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L99-L127) 中候选3为block_l=32。公开域为FP32连续NPU[B,L,C]且B/L/C正、C二次幂。本配置行块为二次幂；仍依赖当前Triton编译/资源准入，未实测。autotune胜者未知，候选表顺序不是静态优先级。

#### Device 数据流

##### 函数级调用链

`fused_variance→autotune/JIT→fused_variance_kernel→tl.load/sum/store`。只有这一个自有Device body，本候选tile=32×C；不启动文件同居的fused_rsqrt_mul。

##### 源码等价伪码

N=B*L，P>0；program p轮转q=p+jP<ceil(N/32)。r=q*32+arange(32)，c=arange(C)，load x[r*C+c]，r<N掩码、无效补0；sum(x*x,axis1)/C；按r<N写output[r]。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/实际有效GM |
|---|---|
| 输入tile/平方 | 各32C个FP32逻辑元素；每个逻辑张量4*32C B |
| sum/variance | 各32个FP32行量 |
| GM输入 | 有效m行时4mC B读取，m=min(32,N-q*32) |
| GM输出 | 4m B写入，连续[B,L,1] |
| 物理UB/寄存器/工作区 | 无显式分配；不能从SSA元素数推断实际峰值 |

##### 分层内存布局

`GM x[N,C]→masked SSA[32,C]→sum[32]→mean-square[32]→GM output[N,1]`。无TQue/TBuf声明；compiler自行融合/复用/spill，不伪造分层地址。

##### 字节账与复用顺序

在配置可编译且尺寸可表示域内，一次完整有效调用读4NC B、写4N B，总4N(C+1) B，不计autotune重复测量或缓存物理事务。输入只读；新输出在launch前分配，框架持有至异步完成；无请求方workspace、无跨kernel中间缓存或通信资源。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 核间 | q余数唯一覆盖、不共享写，无原子/barrier |
| 核内 | SSA依赖由Triton lowering保序，无显式物理事件 |
| 尾行 | mask同时控制load和store，load other0；C无padding/分片 |
| FP32 | x*x→sum→除C；无减均值、无eps、无rsqrt，溢出/非有限值不修复 |
| 准入 | 资源/整数lowering属于外部compiler合同 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| fused_variance_kernel | [完整body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L129-L154) |
| fused_variance | [launcher](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L157-L165) |


### Route R-004：block_l=16

#### 适用条件

##### 选择证据

[配置与key](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L99-L127) 中候选4为block_l=16。公开域为FP32连续NPU[B,L,C]且B/L/C正、C二次幂。本配置行块为二次幂；仍依赖当前Triton编译/资源准入，未实测。autotune胜者未知，候选表顺序不是静态优先级。

#### Device 数据流

##### 函数级调用链

`fused_variance→autotune/JIT→fused_variance_kernel→tl.load/sum/store`。只有这一个自有Device body，本候选tile=16×C；不启动文件同居的fused_rsqrt_mul。

##### 源码等价伪码

N=B*L，P>0；program p轮转q=p+jP<ceil(N/16)。r=q*16+arange(16)，c=arange(C)，load x[r*C+c]，r<N掩码、无效补0；sum(x*x,axis1)/C；按r<N写output[r]。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/实际有效GM |
|---|---|
| 输入tile/平方 | 各16C个FP32逻辑元素；每个逻辑张量4*16C B |
| sum/variance | 各16个FP32行量 |
| GM输入 | 有效m行时4mC B读取，m=min(16,N-q*16) |
| GM输出 | 4m B写入，连续[B,L,1] |
| 物理UB/寄存器/工作区 | 无显式分配；不能从SSA元素数推断实际峰值 |

##### 分层内存布局

`GM x[N,C]→masked SSA[16,C]→sum[16]→mean-square[16]→GM output[N,1]`。无TQue/TBuf声明；compiler自行融合/复用/spill，不伪造分层地址。

##### 字节账与复用顺序

在配置可编译且尺寸可表示域内，一次完整有效调用读4NC B、写4N B，总4N(C+1) B，不计autotune重复测量或缓存物理事务。输入只读；新输出在launch前分配，框架持有至异步完成；无请求方workspace、无跨kernel中间缓存或通信资源。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 核间 | q余数唯一覆盖、不共享写，无原子/barrier |
| 核内 | SSA依赖由Triton lowering保序，无显式物理事件 |
| 尾行 | mask同时控制load和store，load other0；C无padding/分片 |
| FP32 | x*x→sum→除C；无减均值、无eps、无rsqrt，溢出/非有限值不修复 |
| 准入 | 资源/整数lowering属于外部compiler合同 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| fused_variance_kernel | [完整body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L129-L154) |
| fused_variance | [launcher](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L157-L165) |


### Route R-005：block_l=8

#### 适用条件

##### 选择证据

[配置与key](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L99-L127) 中候选5为block_l=8。公开域为FP32连续NPU[B,L,C]且B/L/C正、C二次幂。本配置行块为二次幂；仍依赖当前Triton编译/资源准入，未实测。autotune胜者未知，候选表顺序不是静态优先级。

#### Device 数据流

##### 函数级调用链

`fused_variance→autotune/JIT→fused_variance_kernel→tl.load/sum/store`。只有这一个自有Device body，本候选tile=8×C；不启动文件同居的fused_rsqrt_mul。

##### 源码等价伪码

N=B*L，P>0；program p轮转q=p+jP<ceil(N/8)。r=q*8+arange(8)，c=arange(C)，load x[r*C+c]，r<N掩码、无效补0；sum(x*x,axis1)/C；按r<N写output[r]。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/实际有效GM |
|---|---|
| 输入tile/平方 | 各8C个FP32逻辑元素；每个逻辑张量4*8C B |
| sum/variance | 各8个FP32行量 |
| GM输入 | 有效m行时4mC B读取，m=min(8,N-q*8) |
| GM输出 | 4m B写入，连续[B,L,1] |
| 物理UB/寄存器/工作区 | 无显式分配；不能从SSA元素数推断实际峰值 |

##### 分层内存布局

`GM x[N,C]→masked SSA[8,C]→sum[8]→mean-square[8]→GM output[N,1]`。无TQue/TBuf声明；compiler自行融合/复用/spill，不伪造分层地址。

##### 字节账与复用顺序

在配置可编译且尺寸可表示域内，一次完整有效调用读4NC B、写4N B，总4N(C+1) B，不计autotune重复测量或缓存物理事务。输入只读；新输出在launch前分配，框架持有至异步完成；无请求方workspace、无跨kernel中间缓存或通信资源。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 核间 | q余数唯一覆盖、不共享写，无原子/barrier |
| 核内 | SSA依赖由Triton lowering保序，无显式物理事件 |
| 尾行 | mask同时控制load和store，load other0；C无padding/分片 |
| FP32 | x*x→sum→除C；无减均值、无eps、无rsqrt，溢出/非有限值不修复 |
| 准入 | 资源/整数lowering属于外部compiler合同 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| fused_variance_kernel | [完整body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L129-L154) |
| fused_variance | [launcher](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L157-L165) |


### Route R-006：block_l=4

#### 适用条件

##### 选择证据

[配置与key](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L99-L127) 中候选6为block_l=4。公开域为FP32连续NPU[B,L,C]且B/L/C正、C二次幂。本配置行块为二次幂；仍依赖当前Triton编译/资源准入，未实测。autotune胜者未知，候选表顺序不是静态优先级。

#### Device 数据流

##### 函数级调用链

`fused_variance→autotune/JIT→fused_variance_kernel→tl.load/sum/store`。只有这一个自有Device body，本候选tile=4×C；不启动文件同居的fused_rsqrt_mul。

##### 源码等价伪码

N=B*L，P>0；program p轮转q=p+jP<ceil(N/4)。r=q*4+arange(4)，c=arange(C)，load x[r*C+c]，r<N掩码、无效补0；sum(x*x,axis1)/C；按r<N写output[r]。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/实际有效GM |
|---|---|
| 输入tile/平方 | 各4C个FP32逻辑元素；每个逻辑张量4*4C B |
| sum/variance | 各4个FP32行量 |
| GM输入 | 有效m行时4mC B读取，m=min(4,N-q*4) |
| GM输出 | 4m B写入，连续[B,L,1] |
| 物理UB/寄存器/工作区 | 无显式分配；不能从SSA元素数推断实际峰值 |

##### 分层内存布局

`GM x[N,C]→masked SSA[4,C]→sum[4]→mean-square[4]→GM output[N,1]`。无TQue/TBuf声明；compiler自行融合/复用/spill，不伪造分层地址。

##### 字节账与复用顺序

在配置可编译且尺寸可表示域内，一次完整有效调用读4NC B、写4N B，总4N(C+1) B，不计autotune重复测量或缓存物理事务。输入只读；新输出在launch前分配，框架持有至异步完成；无请求方workspace、无跨kernel中间缓存或通信资源。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 核间 | q余数唯一覆盖、不共享写，无原子/barrier |
| 核内 | SSA依赖由Triton lowering保序，无显式物理事件 |
| 尾行 | mask同时控制load和store，load other0；C无padding/分片 |
| FP32 | x*x→sum→除C；无减均值、无eps、无rsqrt，溢出/非有限值不修复 |
| 准入 | 资源/整数lowering属于外部compiler合同 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| fused_variance_kernel | [完整body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L129-L154) |
| fused_variance | [launcher](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L157-L165) |


### Route R-007：block_l=2

#### 适用条件

##### 选择证据

[配置与key](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L99-L127) 中候选7为block_l=2。公开域为FP32连续NPU[B,L,C]且B/L/C正、C二次幂。本配置行块为二次幂；仍依赖当前Triton编译/资源准入，未实测。autotune胜者未知，候选表顺序不是静态优先级。

#### Device 数据流

##### 函数级调用链

`fused_variance→autotune/JIT→fused_variance_kernel→tl.load/sum/store`。只有这一个自有Device body，本候选tile=2×C；不启动文件同居的fused_rsqrt_mul。

##### 源码等价伪码

N=B*L，P>0；program p轮转q=p+jP<ceil(N/2)。r=q*2+arange(2)，c=arange(C)，load x[r*C+c]，r<N掩码、无效补0；sum(x*x,axis1)/C；按r<N写output[r]。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/实际有效GM |
|---|---|
| 输入tile/平方 | 各2C个FP32逻辑元素；每个逻辑张量4*2C B |
| sum/variance | 各2个FP32行量 |
| GM输入 | 有效m行时4mC B读取，m=min(2,N-q*2) |
| GM输出 | 4m B写入，连续[B,L,1] |
| 物理UB/寄存器/工作区 | 无显式分配；不能从SSA元素数推断实际峰值 |

##### 分层内存布局

`GM x[N,C]→masked SSA[2,C]→sum[2]→mean-square[2]→GM output[N,1]`。无TQue/TBuf声明；compiler自行融合/复用/spill，不伪造分层地址。

##### 字节账与复用顺序

在配置可编译且尺寸可表示域内，一次完整有效调用读4NC B、写4N B，总4N(C+1) B，不计autotune重复测量或缓存物理事务。输入只读；新输出在launch前分配，框架持有至异步完成；无请求方workspace、无跨kernel中间缓存或通信资源。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 核间 | q余数唯一覆盖、不共享写，无原子/barrier |
| 核内 | SSA依赖由Triton lowering保序，无显式物理事件 |
| 尾行 | mask同时控制load和store，load other0；C无padding/分片 |
| FP32 | x*x→sum→除C；无减均值、无eps、无rsqrt，溢出/非有限值不修复 |
| 准入 | 资源/整数lowering属于外部compiler合同 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| fused_variance_kernel | [完整body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L129-L154) |
| fused_variance | [launcher](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L157-L165) |


### Route R-008：block_l=1

#### 适用条件

##### 选择证据

[配置与key](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L99-L127) 中候选8为block_l=1。公开域为FP32连续NPU[B,L,C]且B/L/C正、C二次幂。本配置行块为二次幂；仍依赖当前Triton编译/资源准入，未实测。autotune胜者未知，候选表顺序不是静态优先级。

#### Device 数据流

##### 函数级调用链

`fused_variance→autotune/JIT→fused_variance_kernel→tl.load/sum/store`。只有这一个自有Device body，本候选tile=1×C；不启动文件同居的fused_rsqrt_mul。

##### 源码等价伪码

N=B*L，P>0；program p轮转q=p+jP<ceil(N/1)。r=q*1+arange(1)，c=arange(C)，load x[r*C+c]，r<N掩码、无效补0；sum(x*x,axis1)/C；按r<N写output[r]。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/实际有效GM |
|---|---|
| 输入tile/平方 | 各1C个FP32逻辑元素；每个逻辑张量4*1C B |
| sum/variance | 各1个FP32行量 |
| GM输入 | 有效m行时4mC B读取，m=min(1,N-q*1) |
| GM输出 | 4m B写入，连续[B,L,1] |
| 物理UB/寄存器/工作区 | 无显式分配；不能从SSA元素数推断实际峰值 |

##### 分层内存布局

`GM x[N,C]→masked SSA[1,C]→sum[1]→mean-square[1]→GM output[N,1]`。无TQue/TBuf声明；compiler自行融合/复用/spill，不伪造分层地址。

##### 字节账与复用顺序

在配置可编译且尺寸可表示域内，一次完整有效调用读4NC B、写4N B，总4N(C+1) B，不计autotune重复测量或缓存物理事务。输入只读；新输出在launch前分配，框架持有至异步完成；无请求方workspace、无跨kernel中间缓存或通信资源。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 核间 | q余数唯一覆盖、不共享写，无原子/barrier |
| 核内 | SSA依赖由Triton lowering保序，无显式物理事件 |
| 尾行 | mask同时控制load和store，load other0；C无padding/分片 |
| FP32 | x*x→sum→除C；无减均值、无eps、无rsqrt，溢出/非有限值不修复 |
| 准入 | 资源/整数lowering属于外部compiler合同 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| fused_variance_kernel | [完整body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L129-L154) |
| fused_variance | [launcher](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L157-L165) |

## 算子特定优化

### Trick T-001：固定核数轮转行块

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L137-L146)：

```python
    pid = tl.program_id(0)
    total_tasks = tl.cdiv(num_tokens, block_l)

    for task_id in range(pid, total_tasks, kernel_num):
        token_offsets = task_id * block_l + tl.arange(0, block_l)
        dim_offsets = tl.arange(0, hidden_size)

        offset = token_offsets[:, None] * hidden_size + dim_offsets[None, :]
        mask_out = token_offsets[:, None] < num_tokens
        mask = mask_out & (dim_offsets[None, :] < hidden_size)
```

#### 机制与设计原因

固定P个program轮转任意N的行块，唯一余数映射省去跨核归约/共享统计。源码呈现此调度机制，没有性能量测。

#### 迁移边界

P正、与实际grid一致，b/C须满足具体arange工具链合同，尺寸可表示。

#### 错误做法

将b96默认判为成功或失败、擅自改成128，或者换grid却不改步长。

### Trick T-002：仅统计量落GM

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L148-L154)：

```python
        x = tl.load(x_ptr + offset, mask=mask, other=0.0)

        x_sq = x * x
        sum_sq = tl.sum(x_sq, axis=1)
        variance = sum_sq / hidden_size

        tl.store(output_ptr + token_offsets[:, None], variance[:, None], mask=mask_out)
```

#### 机制与设计原因

输入每元素一次逻辑读取；只有每token的1个FP32均方值写GM，平方与和在SSA内消费。相比物化x²减少源码中间GM输出，未声称实际交易/速度。

#### 迁移边界

这是局部统计，不含跨rank AVG；全局通道数不等分时简单AVG的权重另需调用方处理。

#### 错误做法

将其叫减均值variance或直接当完整RMSNorm；用SUM collective却沿用AVG口径。

## 模板与实现对比

八配置仅改变逻辑行块。fused_rsqrt_mul/带weight归一化/torch_native reference均非此入口节点。统计API与源码级执行知识分层复用，不重复替换API合同。

## 平台差异

本卡A2/A3归属arch22。公开doc arch22/35均支持Triton，README与architectures映射到A2/A3及950；没有平台分支。CANN9.1.0与a3/950 CI norm组是配置证据，不构成本次运行或A2实测；arange扩展、资源lowering须匹配实际工具链。

## 限制与失败边界

输入合同、无参设备缓存、b96准入边界、实际JIT整数范围均未guard。物理UB/寄存器/spill是外部compiler分配；不能由逻辑4bC推出安全容量。未运行编译、autotune、测试或校验，无精度/性能实测；draft不构成稳定安全实现推荐。源代码闭包仍保留所有真实候选，不因缺陷修正上游。

## 源码索引

### 链路索引

| 阶段/源码 | 符号 | 事实 |
|---|---|---|
| [公开合同](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/fused_variance.md) | `fused_variance` | 局部均方/调用方AVG/arch22与35 |
| [完整launcher/Device](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py) | `fused_variance/fused_variance_kernel` | 8candidate及局部统计输出 |
| [公开转发](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/norm/rmsnorm_split.py) | `_variance_triton_impl` | 不自动通信/不fallback |
| [设备helper](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py) | `get_device_properties` | current_device、无参cache、两核数assert |
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

冻结117/legacy唯一同主题TP统计API已全文读并链接；只创建唯一fused_variance的Direct两平台卡，不合并下一fused_rsqrt_mul。固定同repo唯一primary，无verified。
