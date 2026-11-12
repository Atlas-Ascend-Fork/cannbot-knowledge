---
type: Operator
title: "FusedRmsnormWithoutWeight 950 Direct Invoke 算子知识"
description: "闭合无权重RMSNorm的六个Triton行块候选、固定核数任务轮转与按行归约，明确无显式FP32平方、属性缓存与编译器物理分配边界。"
tags: [task.implementation, task.lookup, topic.memory, topic.precision, topic.programming_model]
status: draft
sources:
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/fused_rmsnorm_without_weight.md
    role: primary
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_without_weight.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/norm/rmsnorm_without_weight.py
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
created_at: "2026-11-09T09:11:57Z"
updated_at: "2026-11-09T09:24:37Z"
platforms: ["950"]
cann_versions: ["9.1.0"]
---

# FusedRmsnormWithoutWeight 950 Direct Invoke 算子知识

## 算子速览

固定源码的无权重 RMSNorm，连续三维输入 [B,L,C] 展平为 N=B*L 行，每行输出 `x/sqrt(mean(x²)+eps)`；不含可学习 weight、bias 或 residual。Direct Invoke 是 `sgl_kernel_npu.implementation.triton.norm.rmsnorm_without_weight.fused_rmsnorm_without_weight(x, eps)`。六个行块候选均源代码闭合，autotune 实际选型、物理分配及框架 primitive 为外部边界。

保留 draft：公开形状/布局/设备/eps 前提未在此 launcher 校验，核数 helper 的无参 cache 依赖当前设备；没有编译或运行结果。不能把源码闭合当作任意输入安全保证。已有[公开 API](../../../../apis/sgl_kernel_npu/sgl_rmsnorm_without_weight.md)复用接口合同；本卡只展开冻结 Direct backend。

## 接口与语义

### 计算语义

理想实数语义：`y[b,l,c]=x[b,l,c]/sqrt((Σ_j x[b,l,j]²)/C+eps)`。真实表达式顺序为 x*x → tl.sum(axis=1) → *(1/C) → +eps → rsqrt → 乘 x → store。平方前没有 FP32 cast，公开说明明确低精度平方可能与 FP32 参考路径不同；不承诺逐位等价。此入口无 Torch reference 子节点。

### 输入、输出与属性

| 名称 | 合同/真实读取 |
|---|---|
| x | FP32/FP16/BF16 NPU 连续 [B,L,C]；正 C 为二次幂；按裸指针连续行寻址，不读取 stride |
| eps | Python 标量传 JIT；公开推荐正且有限，launcher 不检查 |
| output | torch.empty_like(x)，同 shape/dtype；有效三维域内全覆盖新输出，输入不写 |
| 返回 | output；无原地残差或统计输出 |

### 入口与版本

冻结入口短路径 `implementation.triton.norm.rmsnorm_without_weight.fused_rmsnorm_without_weight` 与上方带包名前缀的符号指向同函数。公开门面 auto/triton 均延迟导入这一实现；torch_native 属于另一外部参考实现，不并入本图。SGL commit `dda6d36b0cdb4081e102d14c0a2fb276fc416e69`；CANN 9.1.0 来自 README 和 CI norm 组固定参数/容器消费，不是当前机器版本或本次运行记录。未固定完整 Triton compiler 二进制，源码支持与 compiler lowering 能力须分别核对。

## Host/Launcher 执行流程

### 参数校验与前处理

先调用缓存的 `get_device_properties()`，从 torch.npu.current_device 和 Triton driver 获得 AIC/vector 核数；两者均须 >0，虽然此算法只用 vector 数 P。随后直接读 x.shape[0:3]，新分配 output；没有 shape、stride、dtype、设备一致性、C、eps guard。helper 的 `@functools.cache` 无设备参数，因此后续切换设备并不会重新按 x.device 查询。使用时需确保当前设备、输入设备与缓存属性相容，不能仅凭这段源码推定异设备执行结果。

### 参数、Workspace 与生命周期

无自定义 Host tiling/POD、ACLNN executor 或 workspace 请求。参数与输出由 Python/Torch/Triton 管理；empty_like 失败或属性 assert/索引/JIT/launch 错误直接向上抛，未见恢复。启动只传 grid=(P,)，没有 num_warps/num_stages、stream 或 host wait 显式设置。编译器 JIT 缓存/临时资源、框架异步完成及跨流使用均属于框架合同，卡片不虚构物理释放点。

### 启动图与失败传播

`import package(native library/torch_npu initialization) → Direct launcher → current-device helper → empty_like → autotune候选/JIT → 单kernel计算 → 返回output`。autotune 可能为测量多次执行候选；这是同一语义的候选启动，不是六个串联算子。输入只读且每次完整覆盖有效输出，源码无累积状态。没有 CPU/torch_native fallback。包导入需要原生 libsgl_kernel_npu.so 的现有加载路径，不代表此 Kernel 调用那些原生算子。

## Route 与参数设计

### 分核与资源计算

N=B*L，P=num_vectorcore>0，tile=L_b，T=ceil(N/L_b)。program p∈[0,P) 处理 q=p+jP<T；每个 q 具有唯一余数 p，故所有任务恰覆盖一次，行区间互不相交。P>T 的 program 无任务；N=0 时源码循环无迭代，但运行时空张量/autotune 行为未实测。C=0 不属于有效域。

### Route 选择

显式六 configs 只有 block_l={64,32,16,8,4,2}；用户声明的 autotune key 为 num_tokens。内部缓存/选型规则仍归 Triton，不推定其仅以 N 区分所有 specialization。没有静态 shape→胜者表；六候选必须全部视为可能运行。

### 模板/实现执行矩阵

| Route | block_l | dtype 实例 | 逻辑 tile |
|---|---:|---|---|
| R-001 | 64 | FP32 / FP16 / BF16 | 64×C |
| R-002 | 32 | FP32 / FP16 / BF16 | 32×C |
| R-003 | 16 | FP32 / FP16 / BF16 | 16×C |
| R-004 | 8 | FP32 / FP16 / BF16 | 8×C |
| R-005 | 4 | FP32 / FP16 / BF16 | 4×C |
| R-006 | 2 | FP32 / FP16 / BF16 | 2×C |

无 tl.dot、Cube/AIC 或 MIX_CV 自有节点。grid 取 vector 核数，具体线程/指令编排仍是 Triton compiler 边界，不把 CUDA warp 或 Ascend 物理寄存器布局写成固定事实。

### 隐藏性能 Guard

C 与行块越大，逻辑 tile 越大，但未见源码 UB 查询/容量阈值；不能用逻辑 SSA 字节数宣称所有 C 都可编译、无 spill 或高效。公开二次幂约束来自 arange(0,C) 的该实现边界，dim mask 不使非二次幂 C 自动有效。flat 指针访问要求连续三维布局；高维输出并非受支持扩展。

### POD/ABI

| 参数 | 分类 | 生产/消费 |
|---|---|---|
| x_ptr | Tensor 指针 | x → load，生命周期覆盖异步任务 |
| eps | runtime 标量 | 调用方 → var+eps；JIT ABI/标量位宽未在自有代码定义 |
| output_ptr | Tensor 指针 | empty_like → store |
| num_tokens | runtime 整数 | B*L → cdiv/mask |
| hidden_size | tl.constexpr | C → arange/行步长/除数 |
| block_l | tl.constexpr | 六配置 → 行块 |
| kernel_num | tl.constexpr | P → task 循环步长 |
| grid | launcher 值 | (P,) → program 范围 |

没有自定义序列化结构或字段偏移；Tensor 地址/标量 ABI、整数 overflow lowering 归框架，不能伪造 int32/uint64 POD。所有尺寸乘积及地址算术须在实际 JIT 类型可表示范围内。

### Route 源码闭包

同一78行文件含全部 launcher/kernel；helper 完整读，公开门面只延迟导入/转发，norm/backend __init__ 无附加 Device。根 setup.py→torch_wheel 的 stage_runtime 复制完整 Python 包→build_wheel/setup_refactor 收集包；没有为此 Direct 入口单独 CMake/ACLNN 注册。包 __init__ 中原生库加载属于 import 前提。六配置唯一数学语义，未混入带 weight 的 RMSNorm。

## Kernel 实现

### 公共执行流程

行块创建 r,c 二维广播偏移；有效行 load、其余补零；按 C 归约、rsqrt、广播乘；相同 mask 写新输出。所有 route 共用这条源码，以下列清各配置的具体 tile 与边界。

### Route R-001：block_l=64

#### 适用条件

##### 选择证据

autotune 候选 1：`triton.Config({"block_l": 64})`；有效输入为公开约定的 NPU 连续 [B,L,C]、C 为正二次幂、FP32/FP16/BF16。六配置无静态 shape 分支；运行时基准选择的胜者和编译器隐式缓存键属于外部 Triton 行为，列表顺序不是优先级证明。

#### Device 数据流

##### 函数级调用链

launcher → autotune/JIT → `fused_rmsnorm_without_weight_kernel`，本实例 `block_l=64`；源码没有另一自有 Kernel。`tl.load/sum/math.rsqrt/store` 是框架 primitive 边界，没有 Cube/tl.dot 节点。

##### 源码等价伪码

`p=program_id(0); T=ceil(N/64); for q=p; q<T; q+=P`：令 `r=q*64+arange(64)`，`c=arange(C)`，按 `r<N` 掩码读 `x[r*C+c]`，无效行补零；按行算平方和、乘 `1/C`、加 eps、rsqrt；广播乘 x，将有效元素写到新 output。行归约没有跨 program 交换。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑元素/访问 | 存储与生命周期 |
|---|---|---|
| x/x_sq | 每任务 64C，输入字节宽 d | load 后的 Triton SSA；x_sq 前无显式转换 |
| var/rstd | 各 64 个行标量 | sum/rsqrt 的实际 dtype 由 Triton 语义决定 |
| y | 64C 逻辑元素 | 广播乘结果，store 转为输出 dtype |
| GM x/output | 最多各 64Cd B/任务 | 有效尾行各 mCd B，m=min(64,N-q*64) |
| TQue/TBuf/显式 UB/workspace | N/A | 源码未声明，不将逻辑张量当物理缓冲分配 |

##### 分层内存布局

`GM x[N,C] → masked SSA[64,C] → row sum[64] → rsqrt[64] → broadcast SSA[64,C] → GM output[N,C]`。物理 UB、寄存器、spill、线程布局由外部编译器决定，固定源码不足以给出其字节数。

##### 字节账与复用顺序

本配置完整计算一次的有效 GM 读写总量各 NCd B，合计 2NCd B。每任务逻辑 load 上界 64Cd B；平方值逻辑规模亦 64C，不能据此与 x/y 相加作为 UB 峰值。SSA 可融合或复用；无显式 workspace、无请求方 workspace 生命周期。输入只读，output 在 launch 前分配、由调用方接收并按当前框架流语义管理；未见显式 stream 参数或同步。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 已证边界 |
|---|---|
| program 间 | q=p+jP 唯一覆盖任务，无共享写、无 atomics、无跨块 barrier |
| program 内 | SSA 依赖由 Triton lowering 保序；未指定物理事件 |
| 尾块 | r<N mask 同时控制 load/store；补零行不写回；C 为正二次幂时 dim mask 恒真 |
| 精度 | x*x 前无 FP32 cast；归约隐式提升依赖框架，不能把参考实现 FP32 平方等价套入 |
| 异常数/eps | 不检查 eps 正且有限；溢出、Inf/NaN、负或零分母按真实 primitive 传播，未作数值稳定补偿 |

#### 关键实现

##### 符号证据表

| 符号 | 定位与用途 |
|---|---|
| config 64 | [候选配置](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_without_weight.py#L9-L30) |
| task 分配 | [kernel](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_without_weight.py#L42-L52)，tile=64、stride=P |
| math/store | [行归约](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_without_weight.py#L54-L60)，无额外参数结构 |


### Route R-002：block_l=32

#### 适用条件

##### 选择证据

autotune 候选 2：`triton.Config({"block_l": 32})`；有效输入为公开约定的 NPU 连续 [B,L,C]、C 为正二次幂、FP32/FP16/BF16。六配置无静态 shape 分支；运行时基准选择的胜者和编译器隐式缓存键属于外部 Triton 行为，列表顺序不是优先级证明。

#### Device 数据流

##### 函数级调用链

launcher → autotune/JIT → `fused_rmsnorm_without_weight_kernel`，本实例 `block_l=32`；源码没有另一自有 Kernel。`tl.load/sum/math.rsqrt/store` 是框架 primitive 边界，没有 Cube/tl.dot 节点。

##### 源码等价伪码

`p=program_id(0); T=ceil(N/32); for q=p; q<T; q+=P`：令 `r=q*32+arange(32)`，`c=arange(C)`，按 `r<N` 掩码读 `x[r*C+c]`，无效行补零；按行算平方和、乘 `1/C`、加 eps、rsqrt；广播乘 x，将有效元素写到新 output。行归约没有跨 program 交换。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑元素/访问 | 存储与生命周期 |
|---|---|---|
| x/x_sq | 每任务 32C，输入字节宽 d | load 后的 Triton SSA；x_sq 前无显式转换 |
| var/rstd | 各 32 个行标量 | sum/rsqrt 的实际 dtype 由 Triton 语义决定 |
| y | 32C 逻辑元素 | 广播乘结果，store 转为输出 dtype |
| GM x/output | 最多各 32Cd B/任务 | 有效尾行各 mCd B，m=min(32,N-q*32) |
| TQue/TBuf/显式 UB/workspace | N/A | 源码未声明，不将逻辑张量当物理缓冲分配 |

##### 分层内存布局

`GM x[N,C] → masked SSA[32,C] → row sum[32] → rsqrt[32] → broadcast SSA[32,C] → GM output[N,C]`。物理 UB、寄存器、spill、线程布局由外部编译器决定，固定源码不足以给出其字节数。

##### 字节账与复用顺序

本配置完整计算一次的有效 GM 读写总量各 NCd B，合计 2NCd B。每任务逻辑 load 上界 32Cd B；平方值逻辑规模亦 32C，不能据此与 x/y 相加作为 UB 峰值。SSA 可融合或复用；无显式 workspace、无请求方 workspace 生命周期。输入只读，output 在 launch 前分配、由调用方接收并按当前框架流语义管理；未见显式 stream 参数或同步。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 已证边界 |
|---|---|
| program 间 | q=p+jP 唯一覆盖任务，无共享写、无 atomics、无跨块 barrier |
| program 内 | SSA 依赖由 Triton lowering 保序；未指定物理事件 |
| 尾块 | r<N mask 同时控制 load/store；补零行不写回；C 为正二次幂时 dim mask 恒真 |
| 精度 | x*x 前无 FP32 cast；归约隐式提升依赖框架，不能把参考实现 FP32 平方等价套入 |
| 异常数/eps | 不检查 eps 正且有限；溢出、Inf/NaN、负或零分母按真实 primitive 传播，未作数值稳定补偿 |

#### 关键实现

##### 符号证据表

| 符号 | 定位与用途 |
|---|---|
| config 32 | [候选配置](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_without_weight.py#L9-L30) |
| task 分配 | [kernel](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_without_weight.py#L42-L52)，tile=32、stride=P |
| math/store | [行归约](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_without_weight.py#L54-L60)，无额外参数结构 |


### Route R-003：block_l=16

#### 适用条件

##### 选择证据

autotune 候选 3：`triton.Config({"block_l": 16})`；有效输入为公开约定的 NPU 连续 [B,L,C]、C 为正二次幂、FP32/FP16/BF16。六配置无静态 shape 分支；运行时基准选择的胜者和编译器隐式缓存键属于外部 Triton 行为，列表顺序不是优先级证明。

#### Device 数据流

##### 函数级调用链

launcher → autotune/JIT → `fused_rmsnorm_without_weight_kernel`，本实例 `block_l=16`；源码没有另一自有 Kernel。`tl.load/sum/math.rsqrt/store` 是框架 primitive 边界，没有 Cube/tl.dot 节点。

##### 源码等价伪码

`p=program_id(0); T=ceil(N/16); for q=p; q<T; q+=P`：令 `r=q*16+arange(16)`，`c=arange(C)`，按 `r<N` 掩码读 `x[r*C+c]`，无效行补零；按行算平方和、乘 `1/C`、加 eps、rsqrt；广播乘 x，将有效元素写到新 output。行归约没有跨 program 交换。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑元素/访问 | 存储与生命周期 |
|---|---|---|
| x/x_sq | 每任务 16C，输入字节宽 d | load 后的 Triton SSA；x_sq 前无显式转换 |
| var/rstd | 各 16 个行标量 | sum/rsqrt 的实际 dtype 由 Triton 语义决定 |
| y | 16C 逻辑元素 | 广播乘结果，store 转为输出 dtype |
| GM x/output | 最多各 16Cd B/任务 | 有效尾行各 mCd B，m=min(16,N-q*16) |
| TQue/TBuf/显式 UB/workspace | N/A | 源码未声明，不将逻辑张量当物理缓冲分配 |

##### 分层内存布局

`GM x[N,C] → masked SSA[16,C] → row sum[16] → rsqrt[16] → broadcast SSA[16,C] → GM output[N,C]`。物理 UB、寄存器、spill、线程布局由外部编译器决定，固定源码不足以给出其字节数。

##### 字节账与复用顺序

本配置完整计算一次的有效 GM 读写总量各 NCd B，合计 2NCd B。每任务逻辑 load 上界 16Cd B；平方值逻辑规模亦 16C，不能据此与 x/y 相加作为 UB 峰值。SSA 可融合或复用；无显式 workspace、无请求方 workspace 生命周期。输入只读，output 在 launch 前分配、由调用方接收并按当前框架流语义管理；未见显式 stream 参数或同步。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 已证边界 |
|---|---|
| program 间 | q=p+jP 唯一覆盖任务，无共享写、无 atomics、无跨块 barrier |
| program 内 | SSA 依赖由 Triton lowering 保序；未指定物理事件 |
| 尾块 | r<N mask 同时控制 load/store；补零行不写回；C 为正二次幂时 dim mask 恒真 |
| 精度 | x*x 前无 FP32 cast；归约隐式提升依赖框架，不能把参考实现 FP32 平方等价套入 |
| 异常数/eps | 不检查 eps 正且有限；溢出、Inf/NaN、负或零分母按真实 primitive 传播，未作数值稳定补偿 |

#### 关键实现

##### 符号证据表

| 符号 | 定位与用途 |
|---|---|
| config 16 | [候选配置](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_without_weight.py#L9-L30) |
| task 分配 | [kernel](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_without_weight.py#L42-L52)，tile=16、stride=P |
| math/store | [行归约](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_without_weight.py#L54-L60)，无额外参数结构 |


### Route R-004：block_l=8

#### 适用条件

##### 选择证据

autotune 候选 4：`triton.Config({"block_l": 8})`；有效输入为公开约定的 NPU 连续 [B,L,C]、C 为正二次幂、FP32/FP16/BF16。六配置无静态 shape 分支；运行时基准选择的胜者和编译器隐式缓存键属于外部 Triton 行为，列表顺序不是优先级证明。

#### Device 数据流

##### 函数级调用链

launcher → autotune/JIT → `fused_rmsnorm_without_weight_kernel`，本实例 `block_l=8`；源码没有另一自有 Kernel。`tl.load/sum/math.rsqrt/store` 是框架 primitive 边界，没有 Cube/tl.dot 节点。

##### 源码等价伪码

`p=program_id(0); T=ceil(N/8); for q=p; q<T; q+=P`：令 `r=q*8+arange(8)`，`c=arange(C)`，按 `r<N` 掩码读 `x[r*C+c]`，无效行补零；按行算平方和、乘 `1/C`、加 eps、rsqrt；广播乘 x，将有效元素写到新 output。行归约没有跨 program 交换。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑元素/访问 | 存储与生命周期 |
|---|---|---|
| x/x_sq | 每任务 8C，输入字节宽 d | load 后的 Triton SSA；x_sq 前无显式转换 |
| var/rstd | 各 8 个行标量 | sum/rsqrt 的实际 dtype 由 Triton 语义决定 |
| y | 8C 逻辑元素 | 广播乘结果，store 转为输出 dtype |
| GM x/output | 最多各 8Cd B/任务 | 有效尾行各 mCd B，m=min(8,N-q*8) |
| TQue/TBuf/显式 UB/workspace | N/A | 源码未声明，不将逻辑张量当物理缓冲分配 |

##### 分层内存布局

`GM x[N,C] → masked SSA[8,C] → row sum[8] → rsqrt[8] → broadcast SSA[8,C] → GM output[N,C]`。物理 UB、寄存器、spill、线程布局由外部编译器决定，固定源码不足以给出其字节数。

##### 字节账与复用顺序

本配置完整计算一次的有效 GM 读写总量各 NCd B，合计 2NCd B。每任务逻辑 load 上界 8Cd B；平方值逻辑规模亦 8C，不能据此与 x/y 相加作为 UB 峰值。SSA 可融合或复用；无显式 workspace、无请求方 workspace 生命周期。输入只读，output 在 launch 前分配、由调用方接收并按当前框架流语义管理；未见显式 stream 参数或同步。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 已证边界 |
|---|---|
| program 间 | q=p+jP 唯一覆盖任务，无共享写、无 atomics、无跨块 barrier |
| program 内 | SSA 依赖由 Triton lowering 保序；未指定物理事件 |
| 尾块 | r<N mask 同时控制 load/store；补零行不写回；C 为正二次幂时 dim mask 恒真 |
| 精度 | x*x 前无 FP32 cast；归约隐式提升依赖框架，不能把参考实现 FP32 平方等价套入 |
| 异常数/eps | 不检查 eps 正且有限；溢出、Inf/NaN、负或零分母按真实 primitive 传播，未作数值稳定补偿 |

#### 关键实现

##### 符号证据表

| 符号 | 定位与用途 |
|---|---|
| config 8 | [候选配置](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_without_weight.py#L9-L30) |
| task 分配 | [kernel](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_without_weight.py#L42-L52)，tile=8、stride=P |
| math/store | [行归约](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_without_weight.py#L54-L60)，无额外参数结构 |


### Route R-005：block_l=4

#### 适用条件

##### 选择证据

autotune 候选 5：`triton.Config({"block_l": 4})`；有效输入为公开约定的 NPU 连续 [B,L,C]、C 为正二次幂、FP32/FP16/BF16。六配置无静态 shape 分支；运行时基准选择的胜者和编译器隐式缓存键属于外部 Triton 行为，列表顺序不是优先级证明。

#### Device 数据流

##### 函数级调用链

launcher → autotune/JIT → `fused_rmsnorm_without_weight_kernel`，本实例 `block_l=4`；源码没有另一自有 Kernel。`tl.load/sum/math.rsqrt/store` 是框架 primitive 边界，没有 Cube/tl.dot 节点。

##### 源码等价伪码

`p=program_id(0); T=ceil(N/4); for q=p; q<T; q+=P`：令 `r=q*4+arange(4)`，`c=arange(C)`，按 `r<N` 掩码读 `x[r*C+c]`，无效行补零；按行算平方和、乘 `1/C`、加 eps、rsqrt；广播乘 x，将有效元素写到新 output。行归约没有跨 program 交换。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑元素/访问 | 存储与生命周期 |
|---|---|---|
| x/x_sq | 每任务 4C，输入字节宽 d | load 后的 Triton SSA；x_sq 前无显式转换 |
| var/rstd | 各 4 个行标量 | sum/rsqrt 的实际 dtype 由 Triton 语义决定 |
| y | 4C 逻辑元素 | 广播乘结果，store 转为输出 dtype |
| GM x/output | 最多各 4Cd B/任务 | 有效尾行各 mCd B，m=min(4,N-q*4) |
| TQue/TBuf/显式 UB/workspace | N/A | 源码未声明，不将逻辑张量当物理缓冲分配 |

##### 分层内存布局

`GM x[N,C] → masked SSA[4,C] → row sum[4] → rsqrt[4] → broadcast SSA[4,C] → GM output[N,C]`。物理 UB、寄存器、spill、线程布局由外部编译器决定，固定源码不足以给出其字节数。

##### 字节账与复用顺序

本配置完整计算一次的有效 GM 读写总量各 NCd B，合计 2NCd B。每任务逻辑 load 上界 4Cd B；平方值逻辑规模亦 4C，不能据此与 x/y 相加作为 UB 峰值。SSA 可融合或复用；无显式 workspace、无请求方 workspace 生命周期。输入只读，output 在 launch 前分配、由调用方接收并按当前框架流语义管理；未见显式 stream 参数或同步。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 已证边界 |
|---|---|
| program 间 | q=p+jP 唯一覆盖任务，无共享写、无 atomics、无跨块 barrier |
| program 内 | SSA 依赖由 Triton lowering 保序；未指定物理事件 |
| 尾块 | r<N mask 同时控制 load/store；补零行不写回；C 为正二次幂时 dim mask 恒真 |
| 精度 | x*x 前无 FP32 cast；归约隐式提升依赖框架，不能把参考实现 FP32 平方等价套入 |
| 异常数/eps | 不检查 eps 正且有限；溢出、Inf/NaN、负或零分母按真实 primitive 传播，未作数值稳定补偿 |

#### 关键实现

##### 符号证据表

| 符号 | 定位与用途 |
|---|---|
| config 4 | [候选配置](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_without_weight.py#L9-L30) |
| task 分配 | [kernel](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_without_weight.py#L42-L52)，tile=4、stride=P |
| math/store | [行归约](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_without_weight.py#L54-L60)，无额外参数结构 |


### Route R-006：block_l=2

#### 适用条件

##### 选择证据

autotune 候选 6：`triton.Config({"block_l": 2})`；有效输入为公开约定的 NPU 连续 [B,L,C]、C 为正二次幂、FP32/FP16/BF16。六配置无静态 shape 分支；运行时基准选择的胜者和编译器隐式缓存键属于外部 Triton 行为，列表顺序不是优先级证明。

#### Device 数据流

##### 函数级调用链

launcher → autotune/JIT → `fused_rmsnorm_without_weight_kernel`，本实例 `block_l=2`；源码没有另一自有 Kernel。`tl.load/sum/math.rsqrt/store` 是框架 primitive 边界，没有 Cube/tl.dot 节点。

##### 源码等价伪码

`p=program_id(0); T=ceil(N/2); for q=p; q<T; q+=P`：令 `r=q*2+arange(2)`，`c=arange(C)`，按 `r<N` 掩码读 `x[r*C+c]`，无效行补零；按行算平方和、乘 `1/C`、加 eps、rsqrt；广播乘 x，将有效元素写到新 output。行归约没有跨 program 交换。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑元素/访问 | 存储与生命周期 |
|---|---|---|
| x/x_sq | 每任务 2C，输入字节宽 d | load 后的 Triton SSA；x_sq 前无显式转换 |
| var/rstd | 各 2 个行标量 | sum/rsqrt 的实际 dtype 由 Triton 语义决定 |
| y | 2C 逻辑元素 | 广播乘结果，store 转为输出 dtype |
| GM x/output | 最多各 2Cd B/任务 | 有效尾行各 mCd B，m=min(2,N-q*2) |
| TQue/TBuf/显式 UB/workspace | N/A | 源码未声明，不将逻辑张量当物理缓冲分配 |

##### 分层内存布局

`GM x[N,C] → masked SSA[2,C] → row sum[2] → rsqrt[2] → broadcast SSA[2,C] → GM output[N,C]`。物理 UB、寄存器、spill、线程布局由外部编译器决定，固定源码不足以给出其字节数。

##### 字节账与复用顺序

本配置完整计算一次的有效 GM 读写总量各 NCd B，合计 2NCd B。每任务逻辑 load 上界 2Cd B；平方值逻辑规模亦 2C，不能据此与 x/y 相加作为 UB 峰值。SSA 可融合或复用；无显式 workspace、无请求方 workspace 生命周期。输入只读，output 在 launch 前分配、由调用方接收并按当前框架流语义管理；未见显式 stream 参数或同步。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 已证边界 |
|---|---|
| program 间 | q=p+jP 唯一覆盖任务，无共享写、无 atomics、无跨块 barrier |
| program 内 | SSA 依赖由 Triton lowering 保序；未指定物理事件 |
| 尾块 | r<N mask 同时控制 load/store；补零行不写回；C 为正二次幂时 dim mask 恒真 |
| 精度 | x*x 前无 FP32 cast；归约隐式提升依赖框架，不能把参考实现 FP32 平方等价套入 |
| 异常数/eps | 不检查 eps 正且有限；溢出、Inf/NaN、负或零分母按真实 primitive 传播，未作数值稳定补偿 |

#### 关键实现

##### 符号证据表

| 符号 | 定位与用途 |
|---|---|
| config 2 | [候选配置](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_without_weight.py#L9-L30) |
| task 分配 | [kernel](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_without_weight.py#L42-L52)，tile=2、stride=P |
| math/store | [行归约](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_without_weight.py#L54-L60)，无额外参数结构 |

## 算子特定优化

### Trick T-001：固定核数的轮转任务分配

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_without_weight.py#L42-L47)：

```python
    pid = tl.program_id(0)
    total_tasks = tl.cdiv(num_tokens, block_l)

    for task_id in range(pid, total_tasks, kernel_num):
        token_offsets = task_id * block_l + tl.arange(0, block_l)
        dim_offsets = tl.arange(0, hidden_size)
```

#### 机制与设计原因

grid 固定 P，把任意数量行块分派为每个 program 的步长 P 循环；任务唯一性由除法余数保证。无需为 N 直接创建一个 program/行块的网格。源码机制可复用，未测得调度收益。

#### 迁移边界

P 必须正且来自相容设备属性；工作量均匀并不保证每个 shape 下优于其它调度。改用不同 grid 时循环步长须同步。

#### 错误做法

保留 kernel_num=P 却另设不同 program 数，会漏任务或重复任务；用无参缓存跨异构设备推断核数亦缺依据。

### Trick T-002：行统计与归一化在一次任务中消费

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_without_weight.py#L54-L60)：

```python
        x = tl.load(x_ptr + offsets, mask=mask, other=0.0)
        x_sq = x * x
        var = tl.sum(x_sq, axis=1) * (1 / hidden_size)
        rstd = tl.math.rsqrt(var + eps)

        y = x * rstd[:, None]
        tl.store(output_ptr + offsets, y, mask=mask)
```

#### 机制与设计原因

var/rstd 在同一 JIT 任务中按行广播，源码无统计 GM 中间输出、无第二次输入 load；有效数据逻辑流量 2NCd B。不把此融合直接换算成物理 UB 或性能增益。

#### 迁移边界

保持无权重语义、连续行布局和完整 C 归约；若增加 weight/residual/分段归约须重新分析入口/中间资源。

#### 错误做法

为匹配 FP32 参考而擅自补 cast 会改变源码数值路径；以低精度平方完全等价 FP32 平方也不成立。

## 模板与实现对比

六行块配置只改变任务大小与逻辑临时元素数，算式和读写方向相同；无显式 warp/stage 配置和物理 UB 常量。公开 torch_native 路径有自己的计算精度，不把它作为本实现的 Device 证据。

## 平台差异

本卡范围950，归属arch35。公开文档 arch22/arch35 支持 Triton；README 与 architectures.json 映射 2201 的 A2/A3 及3510的950。两产品卡共享同一个 Python/JIT body，没有硬件宏分支，实际 lowering、可用资源和选型不能由共源推出相同。CI norm 组 CANN9.1.0 的 a3/950 配置不是本次执行，也不构成 A2 实测。

## 限制与失败边界

- 三维连续、C 正二次幂、受支持 dtype/device 是合同域，launcher 未完整强制；错误布局会按连续裸地址消费，不能安全泛化。
- 属性从 current_device 读取并无参缓存，AIC 与 vector 数均 assert>0；未绑定 x.device，换设备需另核对调用环境。
- eps 与低精度平方没有稳定化 guard；不保证和显式 FP32 平方参考一致。
- 无完整固定 Triton 编译器/primitive 源码；这不阻断自有算子/路线闭包，却使物理分配、精确 lowering 和隐式 dtype 规则成为明确外部边界。
- 未安装、构建、运行 autotune/Kernel/测试或校验；draft 不推荐无条件安全复用，没有性能/真机结论。

## 源码索引

### 链路索引

| 来源/阶段 | 符号 | 事实 |
|---|---|---|
| [公开语义/平台](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/fused_rmsnorm_without_weight.md) | `fused_rmsnorm_without_weight` | 三维连续、C二次幂、dtype/精度与arch22/35 |
| [Direct launcher与Device](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_without_weight.py) | `fused_rmsnorm_without_weight/fused_rmsnorm_without_weight_kernel` | 六autotune配置、固定P grid、全部JIT body |
| [设备helper](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py) | `get_device_properties` | current_device、无参cache、两核数assert |
| [公开门面](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/norm/rmsnorm_without_weight.py) | `fused_rmsnorm_without_weight/_triton_impl` | auto/triton同入口、无输入guard/fallback |
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

冻结117项及legacy补查指向已有 Triton API，已完整读后链接复用；未新建重复 API。此卡只新增 Direct backend 算子级执行知识，与带 weight RMSNorm、ACLNN norm、torch_native reference 分开。所有 source 来自同一固定 SGL commit，恰一个 primary，未伪造 verified。
