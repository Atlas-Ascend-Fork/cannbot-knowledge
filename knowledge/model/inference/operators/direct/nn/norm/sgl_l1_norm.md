---
type: Operator
title: SGL带符号行归一化 A2/A3 Direct Invoke 算子知识
description: 还原l1_norm的Vector核分行、整行归约和FP32输出，区分带符号分母、无掩码宽度及Triton编译器资源边界。
tags: [task.implementation, task.lookup, topic.data_movement, topic.memory, topic.precision, topic.programming_model]
status: stable
sources:
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/en/operators/norm/l1_norm.md
    role: primary
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/l1_norm.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/norm/l1_norm.py
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/norm/l1_norm.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/setup.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernels.yml
    role: supporting
created_at: "2026-11-09T06:56:41Z"
updated_at: "2026-11-10T07:06:47Z"
platforms: [a2, a3]
cann_versions: ["9.1.0"]
---

# SGL带符号行归一化 A2/A3 Direct Invoke 算子知识

## 算子速览

| 项目 | 内容 |
|---|---|
| 实际入口 | `implementation.triton.norm.l1_norm.l1_norm(input)`；独立Direct Invoke |
| 计算语义 | `Y[r,c]=X[r,c]/sum_j X[r,j]`，不取绝对值、不加epsilon |
| 输入输出 | 连续NPU `[B,H]`，输入FP16/BF16/FP32，新输出FP32；H为正二次幂 |
| 执行类型 | 单个Triton Vector归约节点，无`tl.dot`、Cube或MIX_CV |
| Kernel 路线 | R-001：按Vector核数分配连续行区间 |
| 核心资源 | GM输入/输出、每program的一行逻辑向量与标量归约；物理UB由外部Triton编译器安排 |
| 来源闭包 | `direct_implementation_closed`：Python launcher、设备属性helper和全部JIT body已定位；编译器降级与运行时stream提交为外部框架边界 |
| 验证状态 | 已完成源码闭包检查；本次知识提取未执行编译、真机、数值或性能测试。 |

## 接口与语义

### 计算语义

对每一行计算带符号和，再逐元素相除。零行和可产生Inf或NaN，正负数抵消也会触发；这不是按绝对值计算的L1范数。源码在除法完成后显式`.to(tl.float32)`并写输出，没有显式FP32输入cast，也没有指定`tl.sum`的dtype或归约树；不要据此承诺不同编译器下的逐位结果。

### 输入、输出与属性

| 参数 | shape/layout | dtype | 约束、默认值与语义 |
|---|---|---|---|
| input | `[B,H]`，连续 | FP16/BF16/FP32 | launcher只读取前两维，kernel直接用`r*H+c`，不读取stride；正确调用应满足文档二维约束 |
| output | `[B,H]`，新连续分配 | FP32 | 不覆盖input；H必须为正二次幂以满足`tl.arange(0,H)` |

### 入口与版本

本卡固定Triton实现入口。公共`operators.norm.l1_norm`的`auto`与`triton`最终调用该入口；`torch_native`是CPU NumPy精度参考，其核心实现不属于本Direct Invoke闭包。旧`norm/l1_norm.py`保留相同JIT算法，但导入旧设备helper路径。API选择与L2的差别见[行归一化接口](/model/inference/apis/sgl_kernel_npu/sgl_l1_l2_norm.md)。

CANN 9.1.0来自固定快照norm CI版本配置；它限定本次分析背景，不表示本次已在该版本运行，也不承诺其它版本兼容性。

## Host/Launcher 执行流程

### 参数校验与前处理

`l1_norm`读取`input.shape[0:2]`，先以`torch.empty(B,H,device=input.device,dtype=float32)`分配输出，再调用`get_device_properties`。helper查询当前NPU的`num_aicore`和`num_vectorcore`并断言两者均大于0，以`functools.cache`缓存无参结果。没有dtype、连续性、维数、非零行和检查或contiguous拷贝。形状索引、分配或属性断言异常会在launch前传播。

### 参数、Workspace 与生命周期

令`C=num_vectorcore`，grid为`(C,)`。输入和新输出Tensor分别拥有GM存储，launcher返回输出Tensor，不分配额外workspace或executor。JIT/stream提交、Tensor在异步执行中的存活管理由Torch/Triton运行时承担，源码没有显式event、同步等待、record_stream或自定义回收器，不能从Python返回推断Device已完成。

### 启动图与失败传播

```text
l1_norm: shape -> empty(FP32) -> get_device_properties -> l1_norm_kernel[(C,)]
  kernel(pid): 行区间 -> load -> sum -> divide -> cast(FP32) -> store
```

唯一Device节点的参数为input/output指针、运行时B、constexpr H/C。无跨Kernel边、无中间GM对象、无后继launch；launch异常直接传播。没有主动失败回退或cleanup节点，Tensor按框架所有权释放。实际stream由外部运行时选择，本文件未显式传入stream参数。

## Route 与参数设计

### 分核与资源计算

`L=(B-1)//C+1=ceil(B/C)`（B为非负整数且C>0时）。program `p`处理`[pL,min((p+1)L,B))`。每次迭代装载一整行H元素，不按H再切tile。B=0时L=0，各program不执行行循环；未执行此边界用例。H的正二次幂条件来自文档和`tl.arange`，launcher未主动验证。

### Route 选择

| 顺序 | Route | Key/模板 | 精确选择条件与优先级 | 不适用去向 |
|---:|---|---|---|---|
| 1 | R-001 整行归约 | `l1_norm_kernel<H,C>` | 直接调用唯一实现，H/C作为constexpr | 发生的Python/JIT/运行时异常直接传播，无回退；Direct未检查stride，布局违约也可能在有效存储内静默误算，不保证拒绝非法输入 |

```text
Direct l1_norm(input)
  -> 获取B/H和C -> 唯一JIT实例<H,C> -> R-001
```

### 模板/实现执行矩阵

| Route | key/selector | dtype/shape/platform 完整命中条件 | 执行拓扑与 Kernel 节点 | 实际模板/body | 内存与同步特征 | tail/fallback |
|---|---|---|---|---|---|---|
| R-001 | constexpr H/C；B为运行时参数 | A2/A3连续二维FP16/BF16/FP32，H正二次幂，C>0 | 单Vector JIT kernel | `l1_norm_kernel`完整行循环 | 不同pid写不同整行，无跨核归约 | 行区间上限用min；列无mask；无fallback |

### 隐藏性能 Guard

| Guard | Host/Tiling 条件 | Device/资源原因 | 影响 Route | 不满足时去向 | 源码符号 |
|---|---|---|---|---|---|
| 当前设备核数 | `num_aicore>0 and num_vectorcore>0` | grid及行划分的除数必须有效，虽然算法只使用Vector核数 | R-001 | helper断言 | `get_device_properties` |
| H正二次幂 | 无Host检查 | `tl.arange(0,H)`没有padding或列mask | R-001 | 不满足文档/JIT契约 | `l1_norm_kernel` |
| 连续二维 | 无Host检查 | 地址固定为`r*H+c` | R-001 | 不会自动改走stride版本 | `l1_norm`/`l1_norm_kernel` |
| 单行资源 | 无显式UB容量selector | 整行逻辑向量由Triton编译器分配资源 | R-001 | 不能从源码给出最大H或保底路线 | `l1_norm_kernel` |
| 设备属性缓存 | 无参cache，无设备key | 首次查询结果被后续调用复用；current_device与input.device未核对 | R-001 | 多设备/异构使用需调用方另外核对 | `get_device_properties` |

### POD/ABI

没有自定义C++ POD或Tiling结构。JIT调用参数如下；Python/Triton封送ABI、物理offset与对齐由外部编译器负责，固定仓不包含生成stub，不能填造C++ `sizeof/offsetof`。

| 结构 | 字段 | 类型/位宽 | ABI 布局 | 单位 | Host/launcher producer | Device consumer | 边界 |
|---|---|---|---|---|---|---|---|
| JIT调用 | input_ptr | Tensor数据指针 | 外部封送ABI | 输入元素地址 | input | `tl.load(input_ptr+r*H+cols)` | 连续二维 |
| JIT调用 | output_ptr | FP32 Tensor数据指针 | 外部封送ABI | FP32元素地址 | `torch.empty` | `tl.store` | B×H元素 |
| JIT调用 | batch_size | Python整数，非constexpr | 运行时标量位宽由JIT封送确定 | 行 | `input.shape[0]` | block_size、row_end | 无显式窄化检查 |
| JIT特化 | hidden_size | `tl.constexpr` | 编译期常量，无自定义POD字段 | 元素/行 | `input.shape[1]` | arange、线性地址 | 正二次幂 |
| JIT特化 | NUM_CORES | `tl.constexpr` | 编译期常量 | program数 | `num_vectorcore` | block_size | 大于0 |

### Route 源码闭包

| Route | Key/selector | Host/Tiling producer | POD/参数 | Kernel entry/router 节点 | Kernel body/直接依赖 | 构建接线 |
|---|---|---|---|---|---|---|
| R-001 | 唯一H/C特化 | implementation下`l1_norm`与设备helper | 上表5个参数，无POD | `l1_norm_kernel[(C,)]` | 同文件全部JIT body | `python/sgl_kernel_npu/setup.py::find_namespace_packages`包含implementation包；运行时JIT |

## Kernel 实现

### 公共执行流程

只有R-001。无Cube节点、显式TQue、AscendC `InitBuffer`、NDDMA或通信节点；不能把Triton逻辑向量改写为虚构的AscendC队列。

### Route R-001：按核分配连续行

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Direct launcher | `implementation/triton/norm/l1_norm.py` | `l1_norm` | `kernel[(num_vectorcore,)](...,H,C)` | 唯一实例 |
| 属性helper | `implementation/triton/utils/triton_utils.py` | `get_device_properties` | 两种核数均>0 | C用于分行 |
| Kernel | `implementation/triton/norm/l1_norm.py` | `l1_norm_kernel` | `for row_idx in range(row_begin,row_end)` | 仅处理本核行域 |

#### Device 数据流

##### 函数级调用链

```text
l1_norm -> get_device_properties -> l1_norm_kernel[(C,)]
  -> program_id -> ceil(B/C) -> 行循环
    -> tl.arange(0,H) -> tl.load -> tl.sum -> divide
    -> .to(tl.float32) -> tl.store
```

##### 源码等价伪码

```text
p = program_id(0)
L = (B-1)//C + 1
for r = p*L .. min((p+1)*L,B)-1:
    cols = [0,H)
    x = load(input + r*H + cols)   # 无列mask
    y = x / sum(x)                # 有符号和，无eps
    store(output + r*H + cols, cast_fp32(y))
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM input | `(r*H+c)*sizeof(input.dtype)` | B×H×s字节，s为输入字节数 | 连续行 | 调用方 | tl.load | 输入Tensor，执行完成前有效 | 不按stride读取 |
| 逻辑向量 | H个输入lane及除法结果 | 逻辑读取H×s、FP32写出H×4；不是物理UB分配公式 | JIT中间值 | load/divide/cast | sum/store | 当前行迭代 | 编译器负责寄存器/UB复用 |
| GM output | `(r*H+c)*4` | B×H×4字节 | FP32连续 | tl.store | 调用方后续使用 | 新Tensor | 不同program行域互斥 |
| workspace | N/A | 0个自有临时GM字节 | N/A | N/A | N/A | 无 | 无 |

##### 分层内存布局

```mermaid
flowchart LR
  X["GM input: B×H×s"] --> V["每program逐行H个逻辑lane"]
  V --> S["带符号sum标量"]
  S --> D["向量除法后cast FP32"]
  V --> D
  D --> Y["GM output: B×H×4"]
```

AIV物理UB布局：N/A，实际替代路径为Triton编译器分配；固定仓没有显式buffer/depth或生成代码，不绘制虚构的`block-beta`。

##### 字节账与复用顺序

```text
input GM有效域 = B*H*s bytes
output GM分配 = B*H*4 bytes
workspace_total = 0 bytes（算子自有临时GM）
每行逻辑搬运 = H*s读 + H*4写
UB_total/dynamic_ub = 外部JIT生成资源，源码不提供物理字节数或launch dynamic UB参数
```

因此不能用H×s代替实际UB容量、也不能从这份源码推出最大H。没有显式double buffer、物理别名或缓冲区深度可计。

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| `buffered_values`逻辑值 | load后除法赋值 | sum、cast/store | 下一行迭代的新SSA值 | Triton数据依赖；物理分配由编译器负责 | 不声称存在特定UB原地别名 |
| 输出行 | 当前program | 调用方 | 本kernel不重写该行 | p的行区间互斥 | C>0、合法B/H |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| 行内归约 | tl.sum及SSA依赖 | 整行load | divide | 同一program逻辑值 | 无显式归约dtype或tree参数 |
| 跨program | 无需跨核归约，输出行互斥 | 各program | 各自store | 各自行域 | row_end=min(...,B)，多余program空循环 |
| 列域 | 整行arange，无mask | load | store | H个有效lane | H需正二次幂，不补齐到next_power_of_2 |
| 输出 | 显式to(float32) | 除法结果 | FP32 GM store | 输出Tensor | 零分母不保护；没有epsilon |
| Host/Device | 外部Torch/Triton运行时 | launch | 后续stream消费 | 输入输出存储 | 本文件无显式完成同步 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | `implementation/triton/norm/l1_norm.py` | `l1_norm` | FP32输出分配及C维grid |
| Kernel entry/router | 同上 | `l1_norm_kernel` | H/C constexpr，唯一body |
| Device body/helper | 同上及`implementation/triton/utils/triton_utils.py` | 行循环、`get_device_properties` | 分行、无mask归约和属性缓存 |

## 算子特定优化

### Trick T-001：核内连续行复用整行归约管线

#### 触发与源码依据

- 适用 Route：R-001。
- 触发条件：合法连续二维输入、H正二次幂且C>0；B由C个program连续分块。
- Golden 来源：[固定JIT body第18至23行](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/l1_norm.py#L18-L23)。

**官方源码（固定 Commit 连续逐字摘录）**：

```python
    block_size = (batch_size - 1) // NUM_CORES + 1
    row_begin = pid * block_size
    row_end = tl.minimum((pid + 1) * block_size, batch_size)
    for row_idx in range(row_begin, row_end):
        cols = tl.arange(0, hidden_size)
        buffered_values = tl.load(input_ptr + row_idx * hidden_size + cols)
```

#### 机制与设计原因

grid保持C个program，每个program内部迭代相邻行，整行归约的中间结果无需物化为GM分母数组或提交第二个归一化kernel。`NUM_CORES`来自硬件属性，`hidden_size`来自shape并作为constexpr，行尾由min收口；同一行只在一个program中归约，不需要跨核atomic。源码没有提供对照性能数据，不能据此声称比每行一个program更快。

#### 迁移边界

- 适用：连续小行宽的带符号权重重新归一化。
- 前提：H符合整行arange契约、编译器资源可容纳；设备属性查询与输入设备一致。
- 失效：stride不连续、需要绝对值范数或epsilon、行宽超出编译资源时必须另做实现，当前入口没有替代路线。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

固定仓未提供可验证反例。根据明确地址式，不应把有间隔的二维view当作连续行输入；也不能把CPU NumPy参考的传输时间当本kernel的执行时间。

## 模板与实现对比

| 对比维度 | R-001 整行归约 | 设计选择依据 |
|---|---|---|
| 命中条件/优先级 | Direct唯一实现 | 无自动fallback |
| 模板与 dtype | H/C constexpr，输入dtype由Tensor决定，输出FP32 | 无dtype分支key |
| 循环与分核 | C个program，每核ceil(B/C)行 | 行尾min，无跨核归约 |
| Queue/TBuf/寄存器/dynamic UB/通信 window | 逻辑lane，物理资源由JIT负责 | 源码没有显式AscendC资源分配 |
| 内存总占用与复用 | 新输出4BH字节，无自有workspace | 不把逻辑lane数当物理UB |
| 搬运/Vector/SIMT/NDDMA/通信 API | load→sum→divide→cast→store | 一次kernel完成每行 |
| 同步、精度与 tail | SSA、互斥行域、min行尾 | 列无mask、零分母无保护 |
| fallback/失败边界 | Python/JIT异常向上传播 | 参考实现需显式选择 |

## 平台差异

| 项目 | A2 | A3 | Ascend 950 |
|---|---|---|---|
| 支持状态 | 文档arch22支持 | 文档arch22支持 | 文档arch35支持，见独立950卡 |
| Host/Launcher | 相同Python body | 相同Python body | 相同Python body |
| Kernel/资源 | 动态查询Vector核数 | 动态查询Vector核数 | 编译器与硬件资源另行生成 |

## 限制与失败边界

- 公开输入契约与Host检查不同：launcher不主动验证维数、dtype、stride、H二次幂或非零分母。
- `get_device_properties`缓存首次当前设备属性，未以input.device或device index为key；多设备使用不能假设会重新探测。
- 物理UB/寄存器数、硬件stream提交、JIT ABI位宽与具体归约指令序列属于未包含的编译器/运行时边界；本卡不提供虚构的最大行宽或性能上界。
- 旧API与新API的别名不意味着CPU参考也属于这个Device闭包。950实现见[950源码卡](sgl_l1_norm_950.md)。

## 源码索引

### 链路索引

以下Python相对路径均以`python/sgl_kernel_npu/sgl_kernel_npu/`为前缀。

| 链路阶段 | 文件 | 关键符号 | 支撑内容 |
|---|---|---|---|
| 入口声明/约束 | `docs/api/en/operators/norm/l1_norm.md` | Hardware support、参数表 | 平台、连续性、H与dtype契约 |
| 入口实现 | `operators/norm/l1_norm.py` | `_triton_impl`、`l1_norm` | auto/triton指向相同实现 |
| Host/Tiling/Launcher | `implementation/triton/norm/l1_norm.py` | `l1_norm` | 分配与grid |
| Host/Tiling/Launcher | `implementation/triton/utils/triton_utils.py` | `get_device_properties` | 当前设备核数与cache |
| Kernel entry/body | `implementation/triton/norm/l1_norm.py` | `l1_norm_kernel` | 整行Vector归约完整body |
| 旧入口对照 | `norm/l1_norm.py` | `l1_norm` | 同算法旧导入路径 |
| 构建接线 | `python/sgl_kernel_npu/setup.py` | `find_namespace_packages` | 打包Python实现；JIT无需离线Device target |
| 平台映射 | `python/sgl_kernel_npu/README.md` | 架构选择 | arch22/arch35与产品映射 |
| 平台映射 | `csrc/cmake/architectures.json` | 2201、3510 | compute unit列表 |
| 版本依据 | `.github/workflows/pr-test-kernels.yml` | test-norm-ops | CANN9.1.0版本配置，非本次测试结果 |

### 实现复用检查

| 检查项 | 可复用事实 | 不得改变的约束 | 源码符号 |
|---|---|---|---|
| ABI/POD | 五个JIT参数，无自定义POD | 指针顺序、B运行时、H/C constexpr | l1_norm_kernel |
| 调用顺序 | 分配后查属性，再提交唯一kernel | 不能把Python返回当完成同步 | l1_norm |
| workspace/内存 | 输出4BH字节，无自有临时GM | 输入连续、输出生命周期交给框架 | torch.empty、tl.load/store |
| 同步 | program行域互斥，归约在program内部 | 改成跨program拆行时需重新设计归约 | row_begin/row_end |
| 精度与尾块 | 有符号sum、除法后FP32cast | 无绝对值、无epsilon、无列mask | tl.sum、tl.arange |
| 失败边界 | 属性断言，异常传播，无自动fallback | CPU参考需显式选择且不适用图捕获 | get_device_properties、公共分发 |
