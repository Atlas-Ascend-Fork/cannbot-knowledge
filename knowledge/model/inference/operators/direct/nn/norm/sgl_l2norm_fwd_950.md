---
type: Operator
title: "L2normFwd 950 Direct Invoke 算子知识"
description: "闭合L2Norm两宽度分支的FP32平方和、行块与dtype输出，保留小宽度program尾行重叠及未显式padding边界，区分逻辑流量和编译器分配。"
tags: [task.implementation, task.lookup, topic.memory, topic.precision, topic.programming_model]
status: draft
sources:
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/l2norm_fwd.md
    role: primary
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/l2norm_fwd.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/norm/l2norm_fwd.py
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
created_at: "2026-11-09T09:15:06Z"
updated_at: "2026-11-09T09:24:37Z"
platforms: ["950"]
cann_versions: ["9.1.0"]
---

# L2normFwd 950 Direct Invoke 算子知识

## 算子速览

按最后一维平方和归一化，`y=x/sqrt(sum(x²)+eps)`，不除 D；Direct 入口 `sgl_kernel_npu.implementation.triton.norm.l2norm_fwd.l2norm_fwd(x, eps=1e-6, output_dtype=None)`。D≤512 的多行块分支与 D>512 的一行分支全部闭合，均使用 FP32 中间值。输入只读，新输出恢复原 shape。

保留 draft：小宽度分支存在可由公式复验的 program 行区间重叠，且 block-pointer load 没有显式 padding_option；非二次幂列的补充值不能由自有源码证明。没有运行复现或物理 UB 分配结论。已有[接口合同](../../../../apis/sgl_kernel_npu/sgl_l1_l2_norm.md)完整阅读并复用，L1 不属于本算子。

## 接口与语义

### 计算语义

展平 T 行、D 列。理想实数语义 `y[t,j]=float(x[t,j])/sqrt(Σ_k float(x[t,k])²+eps)`，最后转输出 dtype。实际宽分支用 `1/tl.sqrt`，小分支用 `tl.rsqrt`，不承诺两者逐位一致。小分支在 D<BD 时需要归约 padding 为零才能直接得到此数学语义，源码未显式指定其值。

### 输入、输出与属性

| 项 | 合同及边界 |
|---|---|
| x | 连续NPU FP16/BF16/FP32，至少一维，D>0且可view(-1,D)；无自动连续化 |
| eps | 默认1e-6；建议有限非负，零行使用正数；无检查 |
| output_dtype | None取输入dtype，否则FP16/BF16/FP32；只决定输出，不放宽宽度guard |
| y | empty_like二维view后再view回原shape；输入不写 |

### 入口与版本

冻结短路径加 `sgl_kernel_npu.` 包名前缀即精确Direct入口；公开auto/triton转发此函数，torch_native的独立PyTorch参考不并入Device图。SGL固定commit `dda6d36b0cdb4081e102d14c0a2fb276fc416e69`。CANN9.1.0来自README/CI norm组和容器参数，不是本次环境核验；Triton二进制/lowering版本未完整固定。

## Host/Launcher 执行流程

### 参数校验与前处理

保存x.shape→`x.view(-1,x.shape[-1])`→empty_like（可改dtype）→assert输出末维stride1。令F=65536//输入element_size，BD=min(F,next_power_of_2(D))；D>BD则抛RuntimeError。此错误文字用“>=64KB”，真实条件允许D=F，应按条件理解。无输入设备/全部dtype/连续性/eps显式guard，view失败直接传播。

### 参数、Workspace 与生命周期

无自定义POD、ACLNN executor或workspace。Torch输出、view及Triton编译资源由框架管理；返回异步输出，源码没有host等待/显式stream。num_warps=8、num_stages=3是launch元参数，不可据此生成Ascend物理UB或线程数。小分支helper无参cache取current_device核数P，并同时assertAIC/vector>0；未绑定x.device，须核对切设备与缓存属性相容。

### 启动图与失败传播

`package import → Direct function → view/empty_like/assert/widthguard → D分支 → 一个JIT kernel → y.view(original_shape)`。小分支再调用核数helper；宽分支不需要helper。无fallback。import时torch_npu/原生库加载是包前提，不是本数学Kernel调用原生算子。

## Route 与参数设计

### 分核与资源计算

R-001：D≤512；P=vectorcores>0，M=ceil(T/P)，BT=min(109,floor(109*128/BD))，Q=ceil(M/BT)。grid P；p处理行 `pM+jBT+[0,BT)`，j∈[0,Q)。BT*BD≤13952，但这是逻辑tile约束不是实际UB字节证明。NB=ceil(T/2048)传入却未消费。R-002：D>512，grid T，每program一行，BD列按D mask。

### Route 选择

| Route | 条件 | 函数/实例 |
|---|---|---|
| R-001 | 0<D≤512且D≤BD | l2norm_fwd_kernel_opt，BT/BD constexpr；输入三dtype×输出三dtype |
| R-002 | 512<D≤BD | l2norm_fwd_kernel，BD constexpr；输入三dtype×输出三dtype |

### 模板/实现执行矩阵

R-001的BD为D向上二次幂，BT公式随BD缩小行块；R-002的BD同规则受F限制。FP16/BF16输入F32768，FP32输入F16384。两者无tl.dot/Cube/AIC/MIX节点；线程/物理backend仍归Triton编译器。九个dtype组合不改变自有控制图，store转换不同。

### 隐藏性能 Guard

源码注释称控制BT以免FP32中间值及多缓冲溢出UB，实际只限制逻辑tile≤109×128；未查询物理容量，不能证明所有target均可放入。R-001未把每块尾行裁到(p+1)M；需要Q*BT=M或有效末端无重叠等附加条件才能证明program写集合不相交。

### POD/ABI

| 参数/元参数 | 生产与消费 |
|---|---|
| x,y | Torch二维view/empty_like→裸行主序指针，输入只读/输出写 |
| eps | runtime→分母；JIT标量ABI外部 |
| D | runtime→行步长/边界 |
| BD | constexpr→两分支列tile |
| NB | runtime，只R-001传入，未读 |
| T | runtime，只R-001全局行边界 |
| MBS | runtime，M→R-001基址/子块次数 |
| BT | constexpr→R-001行tile |
| grid | P或T |
| num_warps/num_stages | 均8/3，物理解释外部 |

`do_not_specialize=["NB","T","MBS"]`仅R-001；无自定义序列化、字段偏移或确定整数位宽，尺寸与地址算术须在实际JIT类型可表示域内。

### Route 源码闭包

120行实现包含全部自有launcher及两个Device；helper与公开转发已读。根setup→torch_wheel复制完整Python包、build_wheel/setup_refactor打包；backend/norm包无新增节点。包导入库初始化与Torch/Tritonprimitive均明示外部边界，没有遗漏自有分支。

## Kernel 实现

### 公共执行流程

load→FP32→平方和→加eps→逆根→乘输入→按输出dtype store；无统计GM暂存、无跨program归约、无原子。两分支边界策略不同，不能只凭共同算式合并安全结论。

### Route R-001：小宽度多行块

#### 适用条件

##### 选择证据

实现第85–108行D≤512；Phelper、M/BT公式如上。该分支没有autotune。

#### Device 数据流

##### 函数级调用链

`l2norm_fwd → get_device_properties → l2norm_fwd_kernel_opt → make_block_ptr/load/sum/rsqrt/store`。NB未消费；无另一个自有Kernel。

##### 源码等价伪码

p=program_id；for j<ceil(M/BT)：r=pM+jBT，建立shape(T,D)、stride(D,1)、offset(r,0)、block(BT,BD)、order(1,0)的输入块指针；boundary_check(0,1) load后转FP32→axis1平方和→rsqrt→广播乘；输出同形块指针，显式转element_ty后带边界检查store。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模 | 字节与生命周期 |
|---|---|---|
| load tile | BT×BD | 原dtype d，转FP32后4BTBD；不等于物理双份分配 |
| 平方/归约/逆根 | BTBD/BT/BT | FP32逻辑SSA，编译器可融合/复用 |
| GM有效行 | 每program集合[pM,min(T,pM+QBT)) | 每行读Dd、写De；d/e输入/输出字节宽 |
| workspace/UB/TQue/TBuf | N/A | 源码未显式分配 |

##### 分层内存布局

`GM x[T,D] → blockptr[BT,BD] → FP32 SSA → row[BT] → FP32 SSA → GM y[T,D]`。UB/寄存器/spill未从编译结果获得。

##### 字节账与复用顺序

若T>0，令 `A=Σ_{p=0}^{P-1} max(0,min(T,pM+QBT)-pM)` 为实际合法行访问次数，则逻辑GM读A*D*d、写A*D*e；一般A可能>T，不应无条件声称只读写TD次。每次load/write只按全局shape裁边，逻辑padding不计GM。无workspace交接；output存活至框架确认异步任务完成，调用方负责跨流使用规则。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 精确边界 |
|---|---|
| 内部依赖 | SSA→Triton lowering，未显式barrier事件 |
| 行尾重叠 | QBT>M时相邻区间可能重叠，无原子/去重；即使理想值相同也不是已证明无race |
| 静态例子 | 若运行时P=2、T=3、D=128，则M2、BT109、Q1，p0写0..2、p1写2；是条件化公式例子，不声称真实硬件P2 |
| 列尾 | D<BD，boundary_check load未指定padding_option；不能由源码证明填零，若越界lane未定义则参与axis1归约 |
| store尾 | block-pointer boundary_check(0,1)保护全局行列；不保护每program的M行配额 |
| 数值 | FP32平方/归约/rsqrt，eps不检查；FP32仍可溢出，输出舍入由storecast控制 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| l2norm_fwd_kernel_opt | [完整分支](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/l2norm_fwd.py#L38-L62) |
| BT/launch | [launcher](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/l2norm_fwd.py#L85-L108) |
| get_device_properties | 无参cache/current_device属性，见源码索引 |

### Route R-002：宽维一行归约

#### 适用条件

##### 选择证据

D>512且D≤BD；第109–118行grid=(T,)，不走helper。

#### Device 数据流

##### 函数级调用链

`l2norm_fwd→l2norm_fwd_kernel→tl.load/to(float32)/sum/sqrt/store`；没有附加自有节点。

##### 源码等价伪码

p=program_id；指针+=pD；cols=arange(BD)；maskedload(cols<D,other0)并转FP32；v=sum(x*x)，r=1/sqrt(v+eps)，y=x*r；maskedstore cols<D。输出转换隐含在store，不是显式b_y.to语句。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/流量 |
|---|---|
| load与FP32值 | BD lanes，FP32逻辑4BD B |
| square/y | 各BD逻辑FP32，不汇总成实际UB峰值 |
| scalar sum/rstd | 各1 FP32 |
| GM有效数据 | 每行Dd读取、De写入，总TD(d+e) B |
| workspace/物理UB | 无显式请求/分配，N/A |

##### 分层内存布局

GM一行→maskedSSA[BD]→FP32标量→SSA[BD]→GM输出一行。由compiler管理物理分层，不虚构UB地址、队列深度。

##### 字节账与复用顺序

每program消费一行，与其它program地址不交叠；padding lane显式0不读GM。输入及输出由Torch持有，统计值仅任务内SSA；无workspace与显式跨kernel交接。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 行映射 | program p只写p行，合法T范围内无跨program共享写 |
| D尾 | load other0，store同mask，归约零padding明确 |
| 精度 | FP32平方和与1/sqrt，非RMS；store到目标dtype |
| primitive | sqrt/reduction指令与物理同步由Triton；无真机结论 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| l2norm_fwd_kernel | [源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/l2norm_fwd.py#L15-L35) |
| 宽度dispatch | [源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/l2norm_fwd.py#L109-L118) |

## 算子特定优化

### Trick T-001：小宽度按列宽压缩行tile

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/l2norm_fwd.py#L85-L94)：

```python
    if D <= 512:
        NB = triton.cdiv(T, 2048)

        # Keep the tile no larger than the existing 109 x 128 configuration.
        # Wider padded feature dimensions otherwise overflow UB with the FP32
        # intermediates and multi-buffering used by the optimized kernel.
        bt = min(109, (109 * 128) // BD)
        num_core = get_device_properties()[1]
        main_bs = triton.cdiv(T, num_core)
        grid = (num_core,)
```

#### 机制与设计原因

保持BT*BD≤13952个逻辑元素，随着列tile增大减少行tile；固定核数网格分配连续M行基址。注释的UB动机不等于可复验物理字节账。

#### 迁移边界

需补证每program尾行配额和blockload padding合同；当前小分支不能直接作为通用安全模板。

#### 错误做法

把shape全局boundary_check误认为会限制本program的M行，或把num_stages3机械乘到SSA字节数当UB需求。

### Trick T-002：宽分支显式零padding完成单行归约

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/l2norm_fwd.py#L27-L35)：

```python
    cols = tl.arange(0, BD)
    mask = cols < D
    b_x = tl.load(x + cols, mask=mask, other=0.0).to(tl.float32)
    b_var = tl.sum(b_x * b_x, axis=0)
    b_rstd = 1 / tl.sqrt(b_var + eps)
    # tl.store(Rstd + i_t, rstd)
    # Normalize and apply linear transformation
    b_y = b_x * b_rstd
    tl.store(y + cols, b_y, mask=mask)
```

#### 机制与设计原因

把非二次幂D补成BD进行固定大小归约，padding显式0、统计不落GM；一次读入在归一化复用。无性能实测。

#### 迁移边界

受输入dtype宽度guard约束；无法仅改变输出dtype绕开F。FP32平方和仍有数值范围限制。

#### 错误做法

在另一block-pointer分支未指定padding时直接套用本分支other0保证，或把sum除D变成RMSNorm。

## 模板与实现对比

两个Kernel属于同一逻辑L2Norm，形状、平方和语义、outputdtype一致；小分支多行rsqrt与宽分支单行1/sqrt在padding/写集合/数学primitive上存在实际差异，未当作完全相同后端。torch_native是外部参考入口，未用它填补小分支实现约束。

## 平台差异

本卡950，arch35；公开doc arch22/arch35支持；README/architectures映射到A2/A3和950。自有源码两平台同体，无硬件宏分支；物理lowering/资源/primitive行为依赖对应Triton工具链。CANN9.1.0来自CI固定norm配置，a3/950是配置证据，不是本次运行或A2实测。

## 限制与失败边界

小分支重叠公式与未显式padding须在复用前处理；源代码未作安全修正。所有地址/尺寸计算需在实际JIT整数类型可表示域；API仅约定连续NPU输入，launcher无完整guard。宽度上限按输入dtype、D==F可通过，错误字符串不能替代条件。无运行、构建、测试/校验、性能和物理分配证据；draft不承诺安全迁移。

## 源码索引

### 链路索引

| 阶段/源码 | 符号 | 事实 |
|---|---|---|
| [公开API](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/l2norm_fwd.md) | `l2norm_fwd` | 语义、dtype、两宽度分支、arch22/35 |
| [launcher/Device](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/l2norm_fwd.py) | `l2norm_fwd/l2norm_fwd_kernel[_opt]` | 完整120行，两个可达Kernel |
| [公开适配](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/norm/l2norm_fwd.py) | `_triton_impl` | auto/triton延迟直达；reference分离 |
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

冻结117/legacy结果仅同主题API，已完整读；链接复用L1/L2合并API，新增本唯一L2Norm Direct两平台实现卡。无新API/没有改现有合同。全部固定SGL来源单primary，未填verified。
