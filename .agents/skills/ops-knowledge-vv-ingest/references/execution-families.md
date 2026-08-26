# 非 Cube/VV 执行族与单/多 Kernel 拓扑闭合

本参考描述 AIV/Vector、SIMT、NDDMA、非 Cube 通信/Hybrid 及它们的单/多 Kernel 启动图。只要所有 Host/launcher 可达 Device 节点都不含 AIC/Cube 或 MIX_CV，整个逻辑算子使用 VV Skill；任一可达节点含 AIC/Cube 或 MIX_CV 时整体改用 CV Skill。SIMT、NDDMA、通信和多 Kernel 本身都不是切换条件。

## Host/Launcher 参数生产

必须从入口追踪到以下参数的真实 producer 与失败传播：

- `blockDim`、核数、former/tail core 和每核覆盖域；
- tile、loop、UB/workspace 字节数及其对齐、上界和窄化顺序；
- TilingKey、selector 或模板实例的精确谓词、优先级和 fallthrough；
- POD/ABI 字段的类型、位宽、单位、初始化和 Device consumer；
- stream、workspace owner、launch 返回和异常路径。

## 非 Cube 多 Kernel 启动图

多 Kernel Route 必须先还原 Host launch graph，再逐节点使用后文对应执行族闭合。每个节点必须记录 Host 添加/启动函数、kernel entry、执行族、blockDim/grid、POD、输入输出、workspace slice、返回值和空域/fallback。每条边必须记录：

| 字段 | 必须说明 |
|---|---|
| producer / consumer | 精确 Kernel 节点和函数 |
| 交接介质 | workspace/GM 对象、offset、extent、shape、dtype、layout |
| ordering | stream、event、pipe、atomic 或框架明确保证 |
| owner/lifetime | 谁分配、何时有效、何时可覆盖/释放 |
| 失败传播 | producer 失败是否阻断 consumer，cleanup 何时执行 |

Host 代码中的书写顺序不自动等于 Device 可见性；必须定位实际 stream/event/框架顺序保证。

## Device 数据流

每个 Route 必须闭合：

```text
GM input
  -> UB/TQue/TBuf CopyIn
  -> Vector API 或 MicroAPI
  -> UB/TQue CopyOut
  -> GM output
```

多 Kernel 时，上述链路对每个节点分别闭合，并在节点之间显式插入 `GM/workspace edge + ordering + lifetime`，不得用“依次启动多个 Vector Kernel”代替。

逐阶段说明 core/tile/loop 地址公式、搬运元素数或字节数、`blockLen/srcStride/dstStride`、广播或拼接、输出有效范围和未写区域语义。

## UB、队列与寄存器

- 每个 `TQue` 的位置、depth、字节数和 owner；
- 每个 `TBuf`、LocalTensor、RegTensor 的容量、offset、别名和用途；
- `InitBuffer` 或等价分配公式、条件分配和 double buffer；
- 跨迭代复用顺序、释放点和复用前同步；
- 总占用与平台 UB 上限的必要条件，以及 Host 使用的保守条件。

未使用某类资源时明确写 `N/A + 实际替代路径`，不得虚构 Buffer。

## Vector 参数、同步与尾块

必须说明：

- Vector API 的 dst/src、dtype、repeat、repeat stride、mask 和 merge mode；
- FP16/BF16/FP32 cast、累加、scale、round 的精确顺序；
- queue/event/pipe/barrier/Atomic 的 producer→consumer 与复用清理；
- former/tail core、alignment、stride、mask、尾块和空域保护；
- reduce 的树形、跨核或 Atomic 目标、初始化和可见性。

不得只写 API 名；每个参数都要回到 Host/POD、模板常量或当前循环变量。

## SIMT

必须提取：

- `numBlocks/threadsPerBlock/dynUBufSize` 的 Host producer；
- block、warp/thread 到输出元素或行的映射；
- cooperative group、shared/dynamic UB 的布局；
- atomic 的目标地址、dtype、初始化和冲突域；
- 每个线程的循环步长、barrier 与末尾保护；
- SIMT 与前后 Vector/NDDMA/通信节点的可见性和 stream 顺序。

SIMT 只在极端 fallback 使用时仍需写入正式 Route，不得从主路线描述中消失。

## NDDMA / layout transform

必须提取：

- 输入与输出逻辑 layout、维度折叠方式；
- `blockCount/blockLen/srcStride/dstStride` 等参数的元素/字节单位；
- aligned/unaligned API、padding 与 tail；
- 大维拆分、CUT_ONCE/CUT_TWICE 等阶段图；
- 前置转换、主计算、后置恢复的 launch 顺序；
- 每阶段中间 buffer 容量、owner、同步和真实 fallback。

不得把 layout transform 当作一行 `DataCopy`；多转换 Kernel 必须保留完整网络。

## 非 Cube 通信或 Hybrid

必须写清 rank/world size、communication handle、token/dispatch 范围、collective 或 point-to-point 顺序、远端 window/URMA/SQ/CQ 等真实介质、通信 buffer owner/lifetime、计算通信交叠条件、event/stream/flag 依赖和失败传播。不能把通信库调用名当作闭包终点。

## Route 合并边界

多个 key 只有在以下条件全部相同时才合并为一个 Route：

- 实际执行族 body；
- UB/Queue/TBuf/寄存器、dynamic UB、NDDMA buffer 或通信 window 布局；
- 计算与搬运顺序；
- 同步图、精度顺序和 tail 策略；
- Kernel 节点图、节点间交接边和 lifetime。

合并后仍须在 Route 选择表逐 key 写出谓词、模板实参和差异字段。任一条件不同则拆分 Route。
