---
type: Operator
title: "FusedRsqrtMul 950 Direct Invoke 算子知识"
description: "闭合FP32统计缩放的七个Triton二维候选与广播复用，记录variance及weight重复读取字节、调用方AVG与设备缓存边界。"
tags: [task.implementation, task.lookup, topic.memory, topic.precision, topic.programming_model]
status: draft
sources:
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/fused_rsqrt_mul.md
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
created_at: "2026-11-09T09:19:21Z"
updated_at: "2026-11-09T09:24:37Z"
platforms: ["950"]
cann_versions: ["9.1.0"]
---

# FusedRsqrtMul 950 Direct Invoke 算子知识

## 算子速览

唯一Direct入口 `sgl_kernel_npu.implementation.triton.norm.rmsnorm_split.fused_rsqrt_mul(x, variance, weight, eps=1e-6)`，计算 `output=x*rsqrt(variance+eps)*weight`，连续FP32三维输入、新输出、输入不写。七个二维tile候选全部源码闭合；不在内部调用fused_variance或all_reduce。已有[TP统计API](../../../../apis/sgl_kernel_npu/sgl_tp_rmsnorm_statistics.md)已全文阅读并复用。

draft明确：公开输入和统计已AVG约束未guard；current_device属性无参cache；物理编译分配/运行结果未获得，不能从逻辑tile推断实际UB安全。

## 接口与语义

### 计算语义

N=B*L；`y[t,c]=x[t,c]*rsqrt(v[t]+eps)*w[c]`。对均匀通道分片TP RMSNorm，v应是调用方完成AVG后的全局均方，未通信的局部统计不能自动变成全局结果。真实表达式先rsqrt再两次乘，FP32合同域，未作误差补偿或负统计修正。

### 输入、输出与属性

| 项 | 合同 |
|---|---|
| x | 连续NPU FP32[B,L,C]，C正且不要求二次幂 |
| variance | 同device/dtype，连续[B,L,1]或[N]，按线性行标量读，不使用stride/广播元信息 |
| weight | 同device/dtype，连续[C] |
| eps | 默认1e-6，建议有限正；不guard |
| output | empty_like(x)，新输出同shape/dtype/device；三输入只读 |

### 入口与版本

冻结短路径加包名前缀为精确入口；auto/triton公开适配只转发，torch_native独立参考不并入本图。SGL commit `dda6d36b0cdb4081e102d14c0a2fb276fc416e69`，CANN9.1.0来自README/CI固定配置，不是本次执行环境；未固定完整Triton二进制。

## Host/Launcher 执行流程

### 参数校验与前处理

helper先读current_device属性并缓存P，assertAIC/vector均>0；launcher无deviceguard且cache无设备key。然后读x.shape前三维、grid(P,)、empty_like、launch。没有ndim、连续、三张量同device/dtype、variance长度、weight长度或eps检查。真实合法域须由调用方保证，不能以mask保护超短输入storage。

### 参数、Workspace 与生命周期

无自定义POD、ACLNN、tiling、workspace；Torch输出和Triton编译临时对象由框架持有。无显式stream/wait/warp/stage配置，实际队列/同步与物理资源属于框架边界。三输入及输出须存活至异步任务完成；调用方负责AVG完成和跨流依赖。

### 启动图与失败传播

包import→helper→shape读取→empty_like→autotune/JIT单Kernel→返回output。没有内部variance/通信/CPU参考节点；属性、分配、JIT/launch异常传播，无失败fallback。包初始化torch_npu/原生库是导入依赖，不是此Kernel调用它们。autotune可能重复测量候选，输入不写且输出覆盖，无累积状态。

## Route 与参数设计

### 分核与资源计算

行块a、列块b；R=ceil(N/a)，Q=ceil(C/b)，T=RQ。program p∈[0,P)处理q=p+jP<T；row=q//Q，col=q%Q，每个二维tile唯一覆盖。尾行/列分别mask。P必须正；若零维则公开有效域外，不用除零商余推导成功。

### Route 选择

显式key=["num_tokens","hidden_size"]；七候选如下，没有静态shape到胜者表或硬件宏。Triton内部specialization/缓存键外部，不将用户key当完整缓存键。

### 模板/实现执行矩阵

| Route | 行块a | 列块b | FP32逻辑元素上界 |
|---|---:|---:|---:|
| R-001 | 256 | 256 | x/output 65536，v 256，w 256 |
| R-002 | 128 | 256 | x/output 32768，v 128，w 256 |
| R-003 | 128 | 128 | x/output 16384，v 128，w 128 |
| R-004 | 64 | 128 | x/output 8192，v 64，w 128 |
| R-005 | 64 | 64 | x/output 4096，v 64，w 64 |
| R-006 | 64 | 32 | x/output 2048，v 64，w 32 |
| R-007 | 32 | 32 | x/output 1024，v 32，w 32 |

没有tl.dot/Cube/AIC或MIX自有节点；vector核数grid并不规定实际物理lowering。

### 隐藏性能 Guard

C不要求二次幂，因为arange使用二次幂block_c且有mask；这与fused_variance全C归约不同。大tile逻辑规模大，源码无UB资源查询；不把64K元素tile或隐式Config默认值换成虚构物理内存需求。统计/权重重复GM读取次数随行列分块变化。

### POD/ABI

| 参数 | 生产/消费 |
|---|---|
| x_ptr/variance_ptr/weight_ptr | 三Tensor输入→对应maskedload，全部只读 |
| eps | runtime标量→rsqrt参数 |
| output_ptr | empty_like→maskedstore |
| num_tokens/hidden_size | runtime N/C→任务数、线性寻址、mask |
| block_l/block_c | constexpr七配置→行列arange/tile |
| kernel_num | constexpr P→任务轮转步长 |
| grid | (P,) |

无序列化POD/偏移，JIT标量/指针ABI和整数位宽是框架合同；N*C及所有地址计算须在实际lowering可表示域。

### Route 源码闭包

完整rmsnorm_split文件、public适配和helper已读；只消费本fused_rsqrt_mul路径。根setup.py→torch_wheel的stage_runtime复制完整Python包→build_wheel/setup_refactor打包；norm/backend包无Device。统计入口虽在同文件不属于本调用图。外部primitive的物理实现不伪装为自有源码。

## Kernel 实现

### 公共执行流程

轮转二维tile、三种maskedload、行rsqrt、行/列广播乘、maskedstore。无统计归约、无workspaces、无跨kernel交接；各候选如下。

### Route R-001：tile 256×256

#### 适用条件

##### 选择证据

配置[第1项](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L11-L36)：block_l=256,block_c=256，无静态shape选项规则。FP32连续NPU[B,L,C]、连续variance[N]、weight[C]满足公开合同。候选均二次幂tile，C本身可非二次幂。autotune实际胜者/内部缓存规则外部，列表顺序不是优先级。

#### Device 数据流

##### 函数级调用链

`fused_rsqrt_mul→helper→autotune/JIT→fused_rsqrt_mul_kernel→load/rsqrt/store`。本配置r=ceil(N/256),c=ceil(C/256)；只一个自有Device body，不触发同文件的variance。

##### 源码等价伪码

program p轮转q=p+jP<r*c；row=q//c，col=q%c；i=row*256+arange(256)，k=col*256+arange(256)。掩码读取x[i*C+k]、variance[i,1]、weight[k]，other0；算x*rsqrt(v+eps)*w，i<N且k<C才store。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | FP32逻辑tile/每有效任务访问 |
|---|---|
| x/output | 256×256；有效m×n时各4mn B读/写 |
| variance/rsqrt | 256×1；读4m B，不按每列元素重复 |
| weight | 256；读4n B，广播到m行 |
| 乘法中间值 | 256×256逻辑SSA；实际融合/物理分配未知 |
| workspace/TQue/TBuf | 无显式请求，N/A |

##### 分层内存布局

`GM x[N,C],v[N,1],w[C]→SSA[256,256],[256,1],[256]→rsqrt/broadcast/multiply→GM output[N,C]`。不能把这些逻辑张量之和当作实际UB/寄存器峰值。

##### 字节账与复用顺序

令r=ceil(N/256),c=ceil(C/256)。完整一次有效调用读4NC（x）+4Nc（variance）+4Cr（weight）B，写4NC B；总8NC+4Nc+4Cr B。重复次数来自任务切分，不假设缓存命中或真实DMA事务合并。无显式scratch/workspace；输出异步生命周期归Torch，输入三张量保持有效至任务完成，跨流使用归框架合同。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 任务唯一性 | q余数唯一，(row,col)商余唯一，输出tile不交叠 |
| 核间同步 | 无共享写、无原子或collective/barrier |
| 核内依赖 | load→rsqrt/mul→store的SSA顺序由Triton lowering实现 |
| 尾行/尾列 | 三种load分别mask/other0，store二维mask；无效lane结果不写 |
| FP32 | rsqrt(v+eps)→左结合x*rsqrt*weight；eps/非有限值不guard；不保证与Torch逐位一致 |
| 统计就绪 | 调用方必须先完成正确AVG及stream依赖；本入口不验证统计来源 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| fused_rsqrt_mul_kernel | [完整body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L38-L75) |
| launcher | [fused_rsqrt_mul](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L78-L96) |


### Route R-002：tile 128×256

#### 适用条件

##### 选择证据

配置[第2项](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L11-L36)：block_l=128,block_c=256，无静态shape选项规则。FP32连续NPU[B,L,C]、连续variance[N]、weight[C]满足公开合同。候选均二次幂tile，C本身可非二次幂。autotune实际胜者/内部缓存规则外部，列表顺序不是优先级。

#### Device 数据流

##### 函数级调用链

`fused_rsqrt_mul→helper→autotune/JIT→fused_rsqrt_mul_kernel→load/rsqrt/store`。本配置r=ceil(N/128),c=ceil(C/256)；只一个自有Device body，不触发同文件的variance。

##### 源码等价伪码

program p轮转q=p+jP<r*c；row=q//c，col=q%c；i=row*128+arange(128)，k=col*256+arange(256)。掩码读取x[i*C+k]、variance[i,1]、weight[k]，other0；算x*rsqrt(v+eps)*w，i<N且k<C才store。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | FP32逻辑tile/每有效任务访问 |
|---|---|
| x/output | 128×256；有效m×n时各4mn B读/写 |
| variance/rsqrt | 128×1；读4m B，不按每列元素重复 |
| weight | 256；读4n B，广播到m行 |
| 乘法中间值 | 128×256逻辑SSA；实际融合/物理分配未知 |
| workspace/TQue/TBuf | 无显式请求，N/A |

##### 分层内存布局

`GM x[N,C],v[N,1],w[C]→SSA[128,256],[128,1],[256]→rsqrt/broadcast/multiply→GM output[N,C]`。不能把这些逻辑张量之和当作实际UB/寄存器峰值。

##### 字节账与复用顺序

令r=ceil(N/128),c=ceil(C/256)。完整一次有效调用读4NC（x）+4Nc（variance）+4Cr（weight）B，写4NC B；总8NC+4Nc+4Cr B。重复次数来自任务切分，不假设缓存命中或真实DMA事务合并。无显式scratch/workspace；输出异步生命周期归Torch，输入三张量保持有效至任务完成，跨流使用归框架合同。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 任务唯一性 | q余数唯一，(row,col)商余唯一，输出tile不交叠 |
| 核间同步 | 无共享写、无原子或collective/barrier |
| 核内依赖 | load→rsqrt/mul→store的SSA顺序由Triton lowering实现 |
| 尾行/尾列 | 三种load分别mask/other0，store二维mask；无效lane结果不写 |
| FP32 | rsqrt(v+eps)→左结合x*rsqrt*weight；eps/非有限值不guard；不保证与Torch逐位一致 |
| 统计就绪 | 调用方必须先完成正确AVG及stream依赖；本入口不验证统计来源 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| fused_rsqrt_mul_kernel | [完整body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L38-L75) |
| launcher | [fused_rsqrt_mul](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L78-L96) |


### Route R-003：tile 128×128

#### 适用条件

##### 选择证据

配置[第3项](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L11-L36)：block_l=128,block_c=128，无静态shape选项规则。FP32连续NPU[B,L,C]、连续variance[N]、weight[C]满足公开合同。候选均二次幂tile，C本身可非二次幂。autotune实际胜者/内部缓存规则外部，列表顺序不是优先级。

#### Device 数据流

##### 函数级调用链

`fused_rsqrt_mul→helper→autotune/JIT→fused_rsqrt_mul_kernel→load/rsqrt/store`。本配置r=ceil(N/128),c=ceil(C/128)；只一个自有Device body，不触发同文件的variance。

##### 源码等价伪码

program p轮转q=p+jP<r*c；row=q//c，col=q%c；i=row*128+arange(128)，k=col*128+arange(128)。掩码读取x[i*C+k]、variance[i,1]、weight[k]，other0；算x*rsqrt(v+eps)*w，i<N且k<C才store。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | FP32逻辑tile/每有效任务访问 |
|---|---|
| x/output | 128×128；有效m×n时各4mn B读/写 |
| variance/rsqrt | 128×1；读4m B，不按每列元素重复 |
| weight | 128；读4n B，广播到m行 |
| 乘法中间值 | 128×128逻辑SSA；实际融合/物理分配未知 |
| workspace/TQue/TBuf | 无显式请求，N/A |

##### 分层内存布局

`GM x[N,C],v[N,1],w[C]→SSA[128,128],[128,1],[128]→rsqrt/broadcast/multiply→GM output[N,C]`。不能把这些逻辑张量之和当作实际UB/寄存器峰值。

##### 字节账与复用顺序

令r=ceil(N/128),c=ceil(C/128)。完整一次有效调用读4NC（x）+4Nc（variance）+4Cr（weight）B，写4NC B；总8NC+4Nc+4Cr B。重复次数来自任务切分，不假设缓存命中或真实DMA事务合并。无显式scratch/workspace；输出异步生命周期归Torch，输入三张量保持有效至任务完成，跨流使用归框架合同。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 任务唯一性 | q余数唯一，(row,col)商余唯一，输出tile不交叠 |
| 核间同步 | 无共享写、无原子或collective/barrier |
| 核内依赖 | load→rsqrt/mul→store的SSA顺序由Triton lowering实现 |
| 尾行/尾列 | 三种load分别mask/other0，store二维mask；无效lane结果不写 |
| FP32 | rsqrt(v+eps)→左结合x*rsqrt*weight；eps/非有限值不guard；不保证与Torch逐位一致 |
| 统计就绪 | 调用方必须先完成正确AVG及stream依赖；本入口不验证统计来源 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| fused_rsqrt_mul_kernel | [完整body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L38-L75) |
| launcher | [fused_rsqrt_mul](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L78-L96) |


### Route R-004：tile 64×128

#### 适用条件

##### 选择证据

配置[第4项](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L11-L36)：block_l=64,block_c=128，无静态shape选项规则。FP32连续NPU[B,L,C]、连续variance[N]、weight[C]满足公开合同。候选均二次幂tile，C本身可非二次幂。autotune实际胜者/内部缓存规则外部，列表顺序不是优先级。

#### Device 数据流

##### 函数级调用链

`fused_rsqrt_mul→helper→autotune/JIT→fused_rsqrt_mul_kernel→load/rsqrt/store`。本配置r=ceil(N/64),c=ceil(C/128)；只一个自有Device body，不触发同文件的variance。

##### 源码等价伪码

program p轮转q=p+jP<r*c；row=q//c，col=q%c；i=row*64+arange(64)，k=col*128+arange(128)。掩码读取x[i*C+k]、variance[i,1]、weight[k]，other0；算x*rsqrt(v+eps)*w，i<N且k<C才store。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | FP32逻辑tile/每有效任务访问 |
|---|---|
| x/output | 64×128；有效m×n时各4mn B读/写 |
| variance/rsqrt | 64×1；读4m B，不按每列元素重复 |
| weight | 128；读4n B，广播到m行 |
| 乘法中间值 | 64×128逻辑SSA；实际融合/物理分配未知 |
| workspace/TQue/TBuf | 无显式请求，N/A |

##### 分层内存布局

`GM x[N,C],v[N,1],w[C]→SSA[64,128],[64,1],[128]→rsqrt/broadcast/multiply→GM output[N,C]`。不能把这些逻辑张量之和当作实际UB/寄存器峰值。

##### 字节账与复用顺序

令r=ceil(N/64),c=ceil(C/128)。完整一次有效调用读4NC（x）+4Nc（variance）+4Cr（weight）B，写4NC B；总8NC+4Nc+4Cr B。重复次数来自任务切分，不假设缓存命中或真实DMA事务合并。无显式scratch/workspace；输出异步生命周期归Torch，输入三张量保持有效至任务完成，跨流使用归框架合同。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 任务唯一性 | q余数唯一，(row,col)商余唯一，输出tile不交叠 |
| 核间同步 | 无共享写、无原子或collective/barrier |
| 核内依赖 | load→rsqrt/mul→store的SSA顺序由Triton lowering实现 |
| 尾行/尾列 | 三种load分别mask/other0，store二维mask；无效lane结果不写 |
| FP32 | rsqrt(v+eps)→左结合x*rsqrt*weight；eps/非有限值不guard；不保证与Torch逐位一致 |
| 统计就绪 | 调用方必须先完成正确AVG及stream依赖；本入口不验证统计来源 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| fused_rsqrt_mul_kernel | [完整body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L38-L75) |
| launcher | [fused_rsqrt_mul](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L78-L96) |


### Route R-005：tile 64×64

#### 适用条件

##### 选择证据

配置[第5项](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L11-L36)：block_l=64,block_c=64，无静态shape选项规则。FP32连续NPU[B,L,C]、连续variance[N]、weight[C]满足公开合同。候选均二次幂tile，C本身可非二次幂。autotune实际胜者/内部缓存规则外部，列表顺序不是优先级。

#### Device 数据流

##### 函数级调用链

`fused_rsqrt_mul→helper→autotune/JIT→fused_rsqrt_mul_kernel→load/rsqrt/store`。本配置r=ceil(N/64),c=ceil(C/64)；只一个自有Device body，不触发同文件的variance。

##### 源码等价伪码

program p轮转q=p+jP<r*c；row=q//c，col=q%c；i=row*64+arange(64)，k=col*64+arange(64)。掩码读取x[i*C+k]、variance[i,1]、weight[k]，other0；算x*rsqrt(v+eps)*w，i<N且k<C才store。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | FP32逻辑tile/每有效任务访问 |
|---|---|
| x/output | 64×64；有效m×n时各4mn B读/写 |
| variance/rsqrt | 64×1；读4m B，不按每列元素重复 |
| weight | 64；读4n B，广播到m行 |
| 乘法中间值 | 64×64逻辑SSA；实际融合/物理分配未知 |
| workspace/TQue/TBuf | 无显式请求，N/A |

##### 分层内存布局

`GM x[N,C],v[N,1],w[C]→SSA[64,64],[64,1],[64]→rsqrt/broadcast/multiply→GM output[N,C]`。不能把这些逻辑张量之和当作实际UB/寄存器峰值。

##### 字节账与复用顺序

令r=ceil(N/64),c=ceil(C/64)。完整一次有效调用读4NC（x）+4Nc（variance）+4Cr（weight）B，写4NC B；总8NC+4Nc+4Cr B。重复次数来自任务切分，不假设缓存命中或真实DMA事务合并。无显式scratch/workspace；输出异步生命周期归Torch，输入三张量保持有效至任务完成，跨流使用归框架合同。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 任务唯一性 | q余数唯一，(row,col)商余唯一，输出tile不交叠 |
| 核间同步 | 无共享写、无原子或collective/barrier |
| 核内依赖 | load→rsqrt/mul→store的SSA顺序由Triton lowering实现 |
| 尾行/尾列 | 三种load分别mask/other0，store二维mask；无效lane结果不写 |
| FP32 | rsqrt(v+eps)→左结合x*rsqrt*weight；eps/非有限值不guard；不保证与Torch逐位一致 |
| 统计就绪 | 调用方必须先完成正确AVG及stream依赖；本入口不验证统计来源 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| fused_rsqrt_mul_kernel | [完整body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L38-L75) |
| launcher | [fused_rsqrt_mul](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L78-L96) |


### Route R-006：tile 64×32

#### 适用条件

##### 选择证据

配置[第6项](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L11-L36)：block_l=64,block_c=32，无静态shape选项规则。FP32连续NPU[B,L,C]、连续variance[N]、weight[C]满足公开合同。候选均二次幂tile，C本身可非二次幂。autotune实际胜者/内部缓存规则外部，列表顺序不是优先级。

#### Device 数据流

##### 函数级调用链

`fused_rsqrt_mul→helper→autotune/JIT→fused_rsqrt_mul_kernel→load/rsqrt/store`。本配置r=ceil(N/64),c=ceil(C/32)；只一个自有Device body，不触发同文件的variance。

##### 源码等价伪码

program p轮转q=p+jP<r*c；row=q//c，col=q%c；i=row*64+arange(64)，k=col*32+arange(32)。掩码读取x[i*C+k]、variance[i,1]、weight[k]，other0；算x*rsqrt(v+eps)*w，i<N且k<C才store。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | FP32逻辑tile/每有效任务访问 |
|---|---|
| x/output | 64×32；有效m×n时各4mn B读/写 |
| variance/rsqrt | 64×1；读4m B，不按每列元素重复 |
| weight | 32；读4n B，广播到m行 |
| 乘法中间值 | 64×32逻辑SSA；实际融合/物理分配未知 |
| workspace/TQue/TBuf | 无显式请求，N/A |

##### 分层内存布局

`GM x[N,C],v[N,1],w[C]→SSA[64,32],[64,1],[32]→rsqrt/broadcast/multiply→GM output[N,C]`。不能把这些逻辑张量之和当作实际UB/寄存器峰值。

##### 字节账与复用顺序

令r=ceil(N/64),c=ceil(C/32)。完整一次有效调用读4NC（x）+4Nc（variance）+4Cr（weight）B，写4NC B；总8NC+4Nc+4Cr B。重复次数来自任务切分，不假设缓存命中或真实DMA事务合并。无显式scratch/workspace；输出异步生命周期归Torch，输入三张量保持有效至任务完成，跨流使用归框架合同。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 任务唯一性 | q余数唯一，(row,col)商余唯一，输出tile不交叠 |
| 核间同步 | 无共享写、无原子或collective/barrier |
| 核内依赖 | load→rsqrt/mul→store的SSA顺序由Triton lowering实现 |
| 尾行/尾列 | 三种load分别mask/other0，store二维mask；无效lane结果不写 |
| FP32 | rsqrt(v+eps)→左结合x*rsqrt*weight；eps/非有限值不guard；不保证与Torch逐位一致 |
| 统计就绪 | 调用方必须先完成正确AVG及stream依赖；本入口不验证统计来源 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| fused_rsqrt_mul_kernel | [完整body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L38-L75) |
| launcher | [fused_rsqrt_mul](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L78-L96) |


### Route R-007：tile 32×32

#### 适用条件

##### 选择证据

配置[第7项](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L11-L36)：block_l=32,block_c=32，无静态shape选项规则。FP32连续NPU[B,L,C]、连续variance[N]、weight[C]满足公开合同。候选均二次幂tile，C本身可非二次幂。autotune实际胜者/内部缓存规则外部，列表顺序不是优先级。

#### Device 数据流

##### 函数级调用链

`fused_rsqrt_mul→helper→autotune/JIT→fused_rsqrt_mul_kernel→load/rsqrt/store`。本配置r=ceil(N/32),c=ceil(C/32)；只一个自有Device body，不触发同文件的variance。

##### 源码等价伪码

program p轮转q=p+jP<r*c；row=q//c，col=q%c；i=row*32+arange(32)，k=col*32+arange(32)。掩码读取x[i*C+k]、variance[i,1]、weight[k]，other0；算x*rsqrt(v+eps)*w，i<N且k<C才store。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | FP32逻辑tile/每有效任务访问 |
|---|---|
| x/output | 32×32；有效m×n时各4mn B读/写 |
| variance/rsqrt | 32×1；读4m B，不按每列元素重复 |
| weight | 32；读4n B，广播到m行 |
| 乘法中间值 | 32×32逻辑SSA；实际融合/物理分配未知 |
| workspace/TQue/TBuf | 无显式请求，N/A |

##### 分层内存布局

`GM x[N,C],v[N,1],w[C]→SSA[32,32],[32,1],[32]→rsqrt/broadcast/multiply→GM output[N,C]`。不能把这些逻辑张量之和当作实际UB/寄存器峰值。

##### 字节账与复用顺序

令r=ceil(N/32),c=ceil(C/32)。完整一次有效调用读4NC（x）+4Nc（variance）+4Cr（weight）B，写4NC B；总8NC+4Nc+4Cr B。重复次数来自任务切分，不假设缓存命中或真实DMA事务合并。无显式scratch/workspace；输出异步生命周期归Torch，输入三张量保持有效至任务完成，跨流使用归框架合同。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 任务唯一性 | q余数唯一，(row,col)商余唯一，输出tile不交叠 |
| 核间同步 | 无共享写、无原子或collective/barrier |
| 核内依赖 | load→rsqrt/mul→store的SSA顺序由Triton lowering实现 |
| 尾行/尾列 | 三种load分别mask/other0，store二维mask；无效lane结果不写 |
| FP32 | rsqrt(v+eps)→左结合x*rsqrt*weight；eps/非有限值不guard；不保证与Torch逐位一致 |
| 统计就绪 | 调用方必须先完成正确AVG及stream依赖；本入口不验证统计来源 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| fused_rsqrt_mul_kernel | [完整body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L38-L75) |
| launcher | [fused_rsqrt_mul](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L78-L96) |

## 算子特定优化

### Trick T-001：二维任务展平后固定核数轮转

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L50-L60)：

```python
    pid = tl.program_id(0)
    row_tasks = tl.cdiv(num_tokens, block_l)
    col_tasks = tl.cdiv(hidden_size, block_c)
    total_tasks = row_tasks * col_tasks

    for task_id in range(pid, total_tasks, kernel_num):
        row_pid = task_id // col_tasks
        col_pid = task_id % col_tasks

        token_offsets = row_pid * block_l + tl.arange(0, block_l)
        dim_offsets = col_pid * block_c + tl.arange(0, block_c)
```

#### 机制与设计原因

固定P个program以商余映射覆盖所有二维tile；同时支持长N和非二次幂C，不需跨核归约。没有性能量测。

#### 迁移边界

grid与kernel_num一致，Q>0，地址整数可表示；改tile后统计/权重重复读取量也改变。

#### 错误做法

把列块当独立行归约或遗漏col_tasks，造成重复/漏列；将P缓存无条件复用于另一设备。

### Trick T-002：统计和权重分别广播

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py#L67-L75)：

```python
        x = tl.load(x_ptr + offset, mask=mask, other=0.0)
        variance = tl.load(
            variance_ptr + token_offsets[:, None], mask=mask_token[:, None], other=0.0
        )
        weight = tl.load(weight_ptr + dim_offsets, mask=mask_dim, other=0.0)

        rsqrt = tl.math.rsqrt(variance + eps)
        output = x * rsqrt * weight
        tl.store(output_ptr + offset, output, mask=mask)
```

#### 机制与设计原因

每任务读m个统计、n个权重，分别广播为m×n；无需显式复制完整variance/weight矩阵到GM。逻辑流量公式如各Route，不暗示缓存或物理广播指令。

#### 迁移边界

variance必须连续一标量/行、weight连续一标量/列且已完成同步；其它广播布局须重新寻址。

#### 错误做法

认为“没有归约”就可省略前置AVG，或用短storage依靠输出mask兜底。

## 模板与实现对比

七candidate改变重复读取/逻辑tile，数学相同；fused_variance/torch_native不作为此实现Route。源码未指定warp/stage默认，不能借另一算子配置补数值。

## 平台差异

本卡950归属arch35；公开arch22/35支持，README/architectures映射A2/A3及950，源代码无平台分支。CANN9.1.0与a3/950 CI配置并非本次运行/同lowering保证，也非A2实测。

## 限制与失败边界

未guard输入合同、统计AVG或device属性cache，未固定物理UB/寄存器分配及primitive指令。eps/非有限值按实际rsqrt/mul传播。未执行上游、编译、autotune、测试或校验；draft不宣称真机复现或无条件安全复用。

## 源码索引

### 链路索引

| 阶段/源码 | 符号 | 事实 |
|---|---|---|
| [公开合同](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/fused_rsqrt_mul.md) | `fused_rsqrt_mul` | 已AVG统计/通道尾mask/arch22与35 |
| [launcher/Device](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/rmsnorm_split.py) | `fused_rsqrt_mul/fused_rsqrt_mul_kernel` | 七候选二维tile/广播缩放 |
| [公开转发](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/norm/rmsnorm_split.py) | `_rsqrt_mul_triton_impl` | Direct转发，不隐式通信 |
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

冻结117/legacy同主题TP统计API已全文读；只新增唯一fused_rsqrt_mul两平台Direct卡，不重复API或混入局部统计/通信。单repo恰一primary，未填verified。
