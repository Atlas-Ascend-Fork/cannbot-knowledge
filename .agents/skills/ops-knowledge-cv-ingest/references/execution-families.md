# Cube/CV 执行族提取闭包

本参考只用于至少一个 Host/launcher 可达 Device 节点含 Cube/AIC 或 MIX_CV 的逻辑算子。只读取目标 route 命中的章节；一个 route 若跨族，必须把 Cube 节点与其它节点的交接边也写出来。分流以目标范围内全部可达 Route 为单位；只有整个算子都没有 Cube/AIC/MIX_CV 时才改用 VV Skill，CV 算子中的纯非 Cube Route 仍在本卡闭合。

## 目录

- [1. AIV Vector / RegBase](#1-aiv-vector--regbase)
- [2. SIMT](#2-simt)
- [3. AIC Cube](#3-aic-cube)
- [4. 单 Kernel MIX_CV](#4-单-kernel-mix_cv)
- [5. 含 Cube 节点的多 Kernel 拓扑](#5-含-cube-节点的多-kernel-拓扑)
- [6. NDDMA / layout transform](#6-nddma--layout-transform)
- [7. Host、POD、编译与生命周期](#7-hostpod编译与生命周期)
- [8. 从交付件提取时的裁剪边界](#8-从交付件提取时的裁剪边界)

## 1. AIV Vector / RegBase

必须提取：

- 每核 tile 与总输出域的映射，former/tail 核差异；
- GM→UB→寄存器→UB→GM 的地址、元素数与字节单位；
- `TQue/TBuf/LocalTensor/RegTensor` 的 owner、深度、容量和复用序；
- VF/MicroAPI 的类型实参、mask 元素计数、repeat/stride、load/store tail；
- BF16/FP16/FP32 cast 顺序、round mode 和中间精度；
- reduce 的树形、cache/标量闭环与 barrier；
- double buffer 是否真实存在，以及循环是否能覆盖搬运/计算。

常见失真：

- 把多个 pathId 汇入一个标量公共路线；
- 只写 API 名，不写参数来源和 mask/tail；
- 把寄存器 route 改成 classic Vector 而不保留数据流；
- 写了 TBuf 但没有对应 `InitBuffer`，或条件分配与 `Get<T>()` guard 不一致。

## 2. SIMT

必须提取：

- `numBlocks/threadsPerBlock/dynUBufSize` 的 Host producer；
- block、warp/thread 到输出元素或行的映射；
- cooperative group、shared/dynamic UB 的布局；
- atomic 的目标地址、dtype、初始化和冲突域；
- 每个线程的循环步长与末尾保护；
- SIMT 与后续 Vector/Cube kernel 的可见性和 stream 顺序。

若 SIMT 只在极端 fallback 使用，仍需明确谓词和成本边界，不得从主路线描述中消失。

## 3. AIC Cube

### 3.1 Host tiling producer

逐字段说明：

- 原始 `M/N/K` 与 batch/group/expert 维；
- layout（ND/NZ/ZN/fractal）和 transpose 语义；
- `baseM/baseN/baseK`；
- `stepM/stepN/stepKa/stepKb`；
- `depthA1/depthB1/dbL0C`；
- split-K/stream-K/iter-batch/scheduler 模式；
- AIC 核数、tail block、空 group；
- workspace 和 system workspace。

不能只列最终数值；要写推导顺序、上界、对齐以及被哪个 Device consumer 读取。

### 3.2 Device 数据流

按真实顺序闭合：

```text
GM A/B
  → L1(A1/B1)：copy 粒度、layout、ping-pong
  → L0A/L0B：LoadData 参数、K 循环和 tail
  → Mmad：acc dtype、HF32/quant mode、累加边界
  → L0C：容量、复用、dbL0C
  → Fixpipe / CopyOut：dst layout、scale/bias/quant、尾块
  → GM 或 CV 交接边
```

每层记录容量公式。未使用某层时写 `N/A + 实际替代路径`。

### 3.3 Scheduler 和模板实例

保留足以唯一实例化模板的信息：

- dispatch policy；
- tile shape/layout/type traits；
- scheduler 的 block→tile 映射和 group 边界；
- prologue/epilogue 类型；
- Fixpipe 参数、量化 scale/bias 来源；
- AIC-only/MIX 的 compile-time guard。

大型通用 Matmul 库无需复制，但不能只写“调用通用模板”。知识必须列出本 route 选择的 specialization 和它改变的行为。

## 4. 单 Kernel MIX_CV

先画 AIC/AIV 同一 launch 内的任务图，再分别应用 Cube 与 Vector 闭包。额外说明：

- AIC:AIV 比例及 `blockDim` 编码；
- `ASCEND_IS_AIC/AIV` 分支；
- 两侧是否共享同一 tiling POD；
- Cube producer 的完成信号、Vector consumer 的等待点；
- flag/semaphore 的 ID、轮次、复用周期和防覆盖协议；
- PIPE_FIX、MTE、Vector pipeline 的可见性；
- 某一侧核数为 0 或输出为空时的终点。

不要假设同步一定是 `CrossCoreSetFlag/WaitFlag`；按实际 primitive 记录。

## 5. 含 Cube 节点的多 Kernel 拓扑

多 Kernel 不是执行族。含 Cube/AIC 或 MIX_CV 的 Route 按本节记录节点与交接；同一 CV 算子的纯非 Cube 多 Kernel Route 也须记录以下节点、边和生命周期，按实际执行族使用对应章节，不因单条 Route 无 Cube 而改派 VV。

为 launch graph 中每个节点记录：kernel、执行族、输入、输出、workspace slice、blockDim。为每条边记录：

| 字段 | 必须说明 |
|---|---|
| memory | 正式输出 / 临时 workspace / 原输入别名 |
| shape | 逻辑 shape 与物理对齐 shape |
| dtype/layout | producer 写入与 consumer 读取必须一致 |
| offset/capacity | 字节公式及对齐 |
| ordering | 同 stream 顺序、event、flag 或显式同步 |
| lifetime | owner、释放点、异常路径 |

重点检查：

- Host 是否一次性分配并切片；
- 多 kernel 是否都使用当前 stream；
- producer 只写部分 workspace 时 consumer 是否误读；
- launch 失败后是否仍提交后继；
- output 是否在最后一个 kernel 完成前被提前释放或返回无 owner 的裸指针。

## 6. NDDMA / layout transform

必须提取：

- 输入与输出逻辑 layout、维度折叠方式；
- `blockCount/blockLen/srcStride/dstStride` 等参数的元素/字节单位；
- aligned/unaligned API、padding 与尾块；
- 大维拆分、CUT_ONCE/CUT_TWICE 等阶段图；
- 前置转置、主计算、后置恢复的 launch 顺序；
- 每阶段的中间 buffer 容量和 owner；
- NDDMA 不适用时的真实 fallback。

不要把 layout transform 当作一行 `DataCopy`。若一个 route 由多个转换 kernel 组成，必须保留完整网络。

## 7. Host、POD、编译与生命周期

### 7.1 POD/ABI

- 使用固定宽度整数，记录 `sizeof/alignof/offsetof`；
- 区分元素数、字节数、block 数、core 数和指针；
- union/variant 必须由 route 唯一选择，初始化 inactive storage；
- by-value POD 在 launch 返回前完成复制；pointer POD 的 backing 保持到 stream 完成；
- Host producer 与 Device consumer 对每个字段一一核对。

### 7.2 Host/device 编译边界

direct-launch 的同一 Device TU 可能经历 Host pass 与 Device pass：

- Device-only 类型、intrinsic 和目标架构专用头用真实 Host-pass 宏守护；
- Host pass 保留可链接的 entry 壳和 launch wrapper；
- Host plugin 不直接 include Device-only 大头；
- 共享头只放 POD、声明和 Host-safe 类型；
- 不通过改编译模式、伪造架构宏或 Host simulation 绕过真实 Device 编译。

### 7.3 自包含边界

知识应说明需要哪些类型/API/模板能力，不写机器安装路径。交付中若 vendored 依赖很大：

- 提取当前 route 实际用到的 specialization 和调用闭包；
- 区分编译依赖与运行语义；
- 不要求读者寻找某台机器上的算子实现；
- 不把整套通用模板库复制进知识。

## 8. 从交付件提取时的裁剪边界

### 必须保留

- 改变 route 可达性的 Host 谓词；
- POD/ABI、workspace 和 launch graph；
- 高收益 route 的 tile、scheduler、memory hierarchy、同步和尾块；
- 为补官方覆盖缺口新增的 device route；
- 精度相关的 cast/scale/round/累加顺序；
- 真实失败终点与安全 fallback。

### 可以压缩

- 未被当前 route 实例化的通用模板；
- 重复的类型 traits 和机械 overload；
- 构建系统样板；
- Python 包装样板；
- 与技术路线无关的报告、日志和评测参数。

### 不得混入正文

- 分数、case 编号、模型名或排行榜名称；
- 机器绝对路径和安装版本定位；
- “照抄交付件”“复现某实现”等任务控制话术；
- 未验证的性能推断。
