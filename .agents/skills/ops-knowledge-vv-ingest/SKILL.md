---
name: ops-knowledge-vv-ingest
description: 从固定版本官方源码提取不含可达 Cube/AIC 或 MIX_CV 节点的逻辑算子源码级知识；支持 AIV/Vector、SIMT、NDDMA、非 Cube 通信/Hybrid 及它们的单/多 Kernel 启动图，闭合逐 Route/Kernel 实现、内存字节账、workspace/同步/生命周期与优化 trick。任一可达节点出现 Cube/AIC 或 MIX_CV 时改用 CV Skill。
---

# 非 Cube/VV 算子源码知识提取

本 Skill 负责把一个不含 Cube/AIC 与 MIX_CV 可达节点的逻辑算子固定版本源码转换为一张可直接指导实现复用的中文 `Operator` 卡。它不是格式填充器：必须先还原 Host 分发、Tiling 参数生产、单/多 Kernel 启动图、逐节点执行族、Device 循环/线程/搬运网络、内存、workspace 交接、同步、精度与尾块，再写最终卡。

只产出调用任务指定的最终文件。算子卡以外的 runbook、index、Registry、图谱、inventory、mapping、ledger、staging、receipt、日志和状态文件均不属于本 Skill。

本 Skill 不执行编译、单元测试、真机、数值或性能测试，不生成测试代码，也不调用校验脚本。运行验证统一标记为“本次知识提取未执行”。

## 必须输入

调用 Prompt 必须给出固定源码仓与 40 位 Commit、唯一逻辑算子、入口类型与符号、源码起始范围、目标平台、CANN 版本和独占最终文件列表。

入口类型由 Prompt 决定，本 Skill 不把一种入口补成另一种：

| 入口类型 | 标题标签 | 最低闭包 |
|---|---|---|
| 公开 ACLNN/API | `ACLNN` | `source_closed` |
| 官方内部 Host/Tiling | `Host/Tiling` | `kernel_tiling_closed` |
| 直接调用 | `Direct Invoke` | `direct_implementation_closed` |

缺少必填输入时停止写入并报告缺口。

写入前按 [路径 Spec](../../../governance/specs/paths.md#profile-附加层级)核对任务指定路径与入口语义：公开 ACLNN/API 的完整链路使用 `aclnn`，独立 Direct Invoke 使用 `direct`。当前 Registry 没有仅覆盖官方内部 Host/Tiling 的 call-mode；这类输入可报告源码分析与路径缺口，但必须 defer 最终卡写入，不得借用 `aclnn`、`direct` 或临时创建目录。闭包标签不替代路径准入；后续需先完成分类治理再落库。

模板中的 `<CANN_VERSION>` 使用本任务指定且有固定来源依据的 CANN 版本，不沿用示例或其他任务的版本。输入与来源冲突时先报告缺口，不生成带错误版本范围的正式卡；模板平台标签只对应本次证据范围。

## 开始前必须完整读取

1. [`references/execution-families.md`](references/execution-families.md)：非 Cube 执行族、单/多 Kernel 拓扑闭包和参数检查表；
2. [`templates/operator-template.md`](templates/operator-template.md)：最终卡唯一结构。

不得仅阅读模板后直接写卡。

## 源码边界

- Prompt 给出的源码范围是**扫描起点**，不是禁止追踪 include、继承和构建依赖的目录围栏。为闭合当前逻辑算子，必须递归读取固定仓内所有直接和传递依赖，包括兄弟目录中的公共 Tiling 基类、模板、POD 和构建 target。
- 扩展源码范围不等于扩展逻辑算子；仍然只允许写 Prompt 指定的目标文件。
- 自动生成的 ACLNN inner bridge、框架 `Contiguous/ViewCopy`、executor 壳和 AscendC primitive 内部可作为明确标注的框架边界；算子拥有的 Host selector、POD producer、Kernel router/body、同步 helper 和构建接线不得外推。
- 若公开入口以 `Sort`、`Cast`、`InplaceIndexAdd` 等外部算子组成核心算法，这些节点不是普通框架前后处理。其语义、顺序、workspace 和实现无法从固定源码集合闭合时，不发布正式卡。
- 多 Kernel 不是执行族。只要公开入口的所有可达 Device 节点都不含 Cube/AIC 或 MIX_CV，仍属于 VV；每个核心语义节点及其 Host/Tiling/POD/Kernel、节点间 workspace 边、顺序、同步和 owner/lifetime 都必须闭合。

## 平台与版本判定

按以下顺序取证，不得只看目录名：

1. 公开 README/API 文档的产品支持表和接口约束；
2. `SUPPORT_COMPUTE_UNIT`、OpDef、平台注册与 binary config；
3. Host selector、POD producer、Kernel body 和活动构建/CI 接线。

公开文档明确写“不支持”而实现接线写“支持”时，记录为发布冲突，不创建或覆盖该平台正式卡。`arch35`、`_apt`、`ascend950` 路径只表示实现信号，不单独证明 Ascend 950 公开支持。

同一平台存在多个 API 版本时，只提取实际支持的最新公开版本；新版本复用旧 body 时追到真实实现。Grad、原地、量化及其它不同数学语义必须是独立逻辑算子。

## 固定提取流程

严格依次执行，任一 gate 未通过不得跳到写作：

1. **冻结身份、平台与两轴分类**：确认入口、版本族、公开性、平台证据、输出文件；分别标记“每个节点的执行族”与“单/多 Kernel 拓扑”，确认所有可达 Device 节点都不含 Cube/AIC 或 MIX_CV。
2. **扫描源码闭包**：递归枚举入口、Host/Tiling、POD、router、每个 kernel/body/helper、节点间同步和构建接线；在模型上下文中标注 `ingest/defer/skip`。
3. **还原分发与 launch graph**：识别决策树型、优先级 `IsCapable` 型或自定义 selector；建立完整的 key/selector→模板→POD→kernel 节点/边→body 映射。
4. **逐字段闭合 Host/Tiling/POD**：保留每个字段的 producer、类型、单位、对齐/窄化、所属节点、consumer 与 inactive 条件；推导 block/core、tile/loop、workspace 切片和 UB 上限。
5. **逐 Route 阅读全部 Kernel 节点**：按真实启动和调用顺序，对 AIV 下钻 Vector/MicroAPI 与 UB，对 SIMT 下钻 block/thread/warp 与 dynamic UB，对 NDDMA 下钻 block/stride/alignment 与阶段图，对通信/Hybrid 下钻 rank、buffer、ordering 和生命周期。
6. **做节点内与跨节点内存账**：逐 Kernel 从 `InitBuffer` 或等价分配计算 UB；逐边记录 workspace/GM 的 offset、extent、dtype/layout、producer、consumer、owner/lifetime 和同步，核对 depth/double buffer/别名/复用安全性。
7. **提炼算子特定优化 trick**：只从源码中提取改变搬运、计算、内存或精度行为的机制；保留最小官方源码片段、触发条件、为什么有效、迁移边界和有证据的错误做法。
8. **写卡并跨 Route 收口**：先建完整骨架，再依次填公共章节、逐 Route、模板对比、平台差异、限制和源码索引。

## 完整源码提取算法

以下步骤必须在 `SKILL.md` 本体内完成，不得只凭模板标题自由发挥。所有表格先在模型上下文建立，确认闭包后再写入最终卡；不得落盘为中间文件。

### 1. 建立 Golden 源码清单

从 Prompt 指定的入口和源码目录开始，递归追踪当前逻辑算子的仓内依赖。逐文件归入以下三类：

- `ingest`：直接决定接口、平台、分发、参数、Kernel 或构建的文件，必须完整阅读；
- `defer`：公共基类、include、模板或 helper，只有调用链命中后才读取，但一旦命中就必须追到实际实现；
- `skip`：测试样板、版权文件、未实例化的无关通用模板和其它逻辑算子。

必须覆盖的源码层级如下：

| 层级 | 必须提取的事实 |
|---|---|
| 公开入口 | ACLNN/API 声明、参数、版本、公开支持平台和错误语义 |
| API 实现 | inner bridge、Contiguous/View、workspace/executor、实际 Host 入口 |
| Host/Tiling | shape/dtype/layout 校验、Route selector、tile/core/workspace 计算和失败终点 |
| POD/ABI | 结构定义、逐字段 producer、类型/位宽、单位、对齐、inactive 条件和 Device consumer |
| Kernel router | key/模板实例、平台或 dtype 编译 guard、未知 key 和空指针终点 |
| Kernel body | AIV 的 `Init/Process/CopyIn/Compute/CopyOut`，SIMT 线程 body，NDDMA 阶段网络，非 Cube 通信/Hybrid body，以及各自 helper、内存、同步、精度和 tail |
| Launch graph | Host 启动节点及顺序、每节点的 entry/POD/blockDim、节点间 workspace/GM 边、同步、失败传播和 owner/lifetime |
| 构建接线 | CMake、binary config、注册宏、目标文件和平台编译选择 |

每个待写入事实都要同时记录：仓库、40 位 Commit、仓内相对路径、精确符号和它支撑的结论。只有目录 URL、文件名或搜索命中不算证据。

### 2. 冻结逻辑算子、入口版本与平台

先写一份模型上下文中的身份表，至少回答：

| 字段 | 必须确认的内容 |
|---|---|
| 逻辑语义 | 公式、输入输出有效域、Grad/原地/量化等语义边界 |
| 实际入口 | Prompt 指定的 ACLNN/API、Host/Tiling 或 Direct Invoke 符号 |
| 版本族 | 同一平台实际支持的最新版本，以及旧版本 body 的复用关系 |
| 公开性 | README/API 文档是否公开，是否存在“文档不支持、实现接线支持”的冲突 |
| 平台 | A2、A3、Ascend 950 分别由哪些公开文档、OpDef/config、Host/Kernel/构建事实支撑 |
| 执行族 | 逐个 Host/launcher 可达 Device 节点标记 `AIV_VECTOR`/SIMT/NDDMA/非 Cube 通信/Hybrid，并确认不含 Cube/AIC 或 MIX_CV |
| 启动拓扑 | 单 Kernel 或多 Kernel；多 Kernel 时列出节点、边、workspace、ordering 和 lifetime |
| 目标文件 | 无后缀卡和 `_950` 卡分别覆盖哪个平台，不得扩大 Prompt 文件集 |

平台取证顺序固定为：

1. README/API 文档产品支持表和约束；
2. `SUPPORT_COMPUTE_UNIT`、OpDef、平台注册与 binary config；
3. Host selector、Kernel guard、活动 CMake/CI 接线。

公开文档明确“不支持”时，不得只凭 `arch35`、`_apt`、`ascend950`、Kernel 文件存在或 CI 条目发布正式卡。证据冲突必须停止对应平台写入并报告。

### 3. 还原 Host 分发与 launch graph，而不是罗列 TilingKey

先判断 Host 使用哪种分发模式，再按真实判断顺序展开。

#### 模式 A：单函数决策树

典型特征是一个 `Compute/DoTiling/SelectKey` 函数内连续 `if/else`，最后调用 `SetTilingKey`。必须提取：

- 每个条件的完整布尔关系、判断顺序和短路语义；
- dtype、shape、空域、平台、UB、alignment 等变量从哪里产生；
- 命中后的 key、POD 写入、blockDim 和失败或 fallback；
- 不能把嵌套条件压缩成可能改变优先级的并列表达式。

#### 模式 B：优先级加 `IsCapable`

典型特征是多模板类各自实现 `IsCapable/GetTilingKey`，框架按 priority 尝试。必须提取：

- 所有候选模板及 priority，明确数值方向；
- 每个 `IsCapable` 的 shape/dtype/platform/资源谓词；
- 失败后尝试的下一模板和最终失败终点；
- `GetTilingKey`、实际模板参数、POD 类型与 Kernel router 的对应关系。

#### 模式 C：表驱动或多层 selector

遇到 tuple、注册宏、lookup table、编译期 specialization 或外层/内层 selector 时，必须展开：

```text
公开入口/平台
  -> 外层 selector
    -> tuple/key/模板实例
      -> POD producer
        -> Kernel entry/router
          -> 实际 body/helper
```

注册表中存在的条目不等于 Host 可达 Route。只有从实际入口和当前平台可达的路线才进入正式卡。

对每条 Route 还要独立建立 launch graph。每个节点记录 Host 添加/启动函数、kernel entry、真实执行族、blockDim/grid/thread/dynamic UB、POD、输入输出和 workspace slice；每条边记录 producer/consumer、offset/extent、dtype/layout、stream/event/pipe/atomic ordering、owner/lifetime 与失败是否阻断后续节点。单 Kernel 是只有一个 Device 节点的特例；节点数不改变 VV/CV 分流。

### 4. 生成 Route、模板与 Guard 矩阵

对每个 Host 可达实现族建立一行：

| Route | key/selector | 完整命中条件 | 执行拓扑与 Kernel 节点 | 模板/body | 内存与同步 | tail/fallback |
|---|---|---|---|---|---|---|
| R-001 | 源码 key | 保持优先级的完整谓词 | 单/多 Kernel 节点及顺序 | 完整模板实参与实际方法 | UB/workspace/event | 尾块和不满足去向 |

Route 合并必须同时满足：选择谓词等价、POD 布局相同、Device body 相同、内存与同步相同、精度和 tail 相同。仅 dtype key 不同但模板和行为完全相同时可以合并，仍需逐 key 写差异。

随后扫描所有会改变 Route 或资源上界的隐藏 Guard：

- UB 可用量、`InitBuffer` 总量和 double buffer 深度；
- DMA alignment、blockLen、stride、repeat/mask 上限；
- bank conflict padding、former/tail core 和空域；
- dtype/platform 编译宏与 specialization；
- fallback、unknown key、unsupported 和返回码。

每个 Guard 必须写出 Host 条件、Device 原因、影响 Route、不满足去向和源码符号，不能只写“为了性能”。

### 5. 逐字段闭合 Host/Tiling/POD

#### Host/API 前处理

按真实调用顺序记录：

1. 输入、输出、属性校验和错误返回；
2. shape、dtype、layout、axis、标量的归一化；
3. `Contiguous/View/ViewCopy` 等框架边界及其输入输出；
4. workspace size、executor/launcher、stream 和 owner/lifetime；
5. Host/Tiling 入口、逐节点 blockDim/Kernel launch、节点间 ordering 和失败传播。

框架生成代码不可见时可标为框架边界，但算子拥有的参数转换、selector、POD 写入和 launch 顺序必须继续追踪。

#### Tiling 推导

按变量依赖顺序解释，而不是只抄最终数值：

```text
原始 shape/dtype/layout
  -> 元素数、轴长、行数或 batch
  -> block/core 分配与 former/tail core
  -> tile 长度、loop 次数和尾 tile
  -> UB/workspace 字节数与对齐
  -> Route/key、blockDim 和 POD 写入
```

每个公式必须说明单位是元素、字节、block、repeat 还是 core，并检查乘法溢出、窄化、向上取整、对齐和零维边界。

#### POD/ABI

每个字段独占一行，不得将多个字段合并。逐字段确认：

- 结构名、字段名、源码类型和位宽；
- `sizeof/alignof/offsetof`；固定仓确实无法获知时才写明不可见；
- Host producer 的精确赋值表达式；
- Device consumer 的精确读取位置和用途；
- 单位、合法范围、inactive Route 和默认/零值是否会被读取；
- Host 与 Device 使用的结构、命名空间和序列化宏是否一致。

### 6. 逐 Route 阅读 Kernel 实体

每条 Route 的每个 Kernel 节点都必须下钻到真实 body，不能在 entry 或模板名处停止。多 Kernel 时先按 Host 启动顺序列节点和边；AIV 节点执行 6.1–6.6，SIMT/NDDMA/通信/Hybrid 节点分别执行 6.7–6.9。

#### 6.1 Entry 与 router

- Kernel entry 参数顺序和 GM 指针类型；
- POD 解析、key 分支、模板实参和类构造；
- 平台/dtype 编译 guard；
- unknown key、空指针、空域和无输出终点。

#### 6.2 类结构与初始化

- 继承关系和基类实际复用的方法；
- 模板参数、构造参数、`TPipe` 所有权；
- `TQue/TBuf/LocalTensor/RegTensor` 成员及 Queue position；
- `InitBuffer` 的 buffer 名、depth、逐块容量和条件分配；
- GM/UB tensor 绑定的 base offset 和有效 extent。

#### 6.3 `Process` 与分核循环

- `GetBlockIdx` 到数据域的映射；
- former/tail core 分支；
- 外层 core、tile、repeat 或行循环的嵌套关系；
- 循环次数来自哪个 POD 字段；
- 空域、尾循环和最后一次有效长度。

#### 6.4 `CopyIn`

- 每路 GM 输入的 base、offset、extent 和 owner；
- `DataCopy/DataCopyPad` 的 blockCount、blockLen、srcStride、dstStride；
- 多路拼接、广播常量、padding 和对齐；
- `AllocTensor/EnQue/DeQue` 或等价生命周期。

#### 6.5 `Compute` 与 helper

按源码调用顺序写完整计算管线。对每个关键 Vector API 必须解释：

- dst/src 类型、shape 和实际内存；
- mask、repeatTimes、block stride、repeat stride 的来源；
- broadcast、zeroing/merging、cast/round 模式为什么这样取值；
- 中间 buffer 是否原地覆盖或跨步骤复用；
- FP16/BF16/FP32 的升精度、累加、降精度顺序；
- tail、padding 和无效 lane 如何避免参与结果。

#### 6.6 `CopyOut`

- 输出 base offset、有效长度和布局；
- UB→GM 搬运参数和 tail；
- 多路输出拆分、原地更新或 partial 输出；
- `EnQue/DeQue/FreeTensor`、pipe/event 和最终可覆盖点。

#### 6.7 SIMT 节点

对每个 SIMT 节点必须写清 `numBlocks/threadsPerBlock/dynUBufSize` 的 Host producer，block/warp/thread 到输出域的映射，cooperative group 与 shared/dynamic UB 布局，atomic 的目标、dtype、初始化和冲突域，每线程循环步长、barrier 与尾部保护，以及与前后节点的可见性。极端 fallback 中的 SIMT 仍是正式 Route。

#### 6.8 NDDMA 节点

必须闭合输入/输出逻辑 layout、维度折叠、`blockCount/blockLen/srcStride/dstStride` 的单位、aligned/unaligned API、padding/tail、大维拆分和 CUT_ONCE/CUT_TWICE 等阶段图，以及每阶段中间 buffer、owner、顺序和 fallback。不得把 layout transform 压缩成一行 `DataCopy`。

#### 6.9 非 Cube 通信或 Hybrid 节点

写清 rank/world size、communication handle、token/dispatch 范围、collective 或 point-to-point 顺序、远端 window/URMA/SQ/CQ 等真实介质、buffer owner/lifetime、计算通信交叠条件、event/stream/flag 依赖和失败传播。不能把通信库调用名当作闭包终点。

每条 Route 正文至少需要 launch graph、逐节点函数级调用链、保留循环/线程/地址/条件的源码等价伪码、资源搬运表、节点间 workspace/同步/生命周期表和 Host/entry/body 三层符号证据。

### 7. 做分层内存字节账和复用证明

从当前 Route 的真实分配逐项计算：

```text
queue_bytes = depth * aligned_elements * sizeof(dtype)
tbuf_bytes = aligned_elements * sizeof(dtype)
register_bytes = 固定仓可证明的寄存器占用；不可见时只说明生命周期
UB_total = Σ(queue_bytes) + Σ(tbuf_bytes) + Σ(other_local_bytes)
UB_total <= Host selector 使用的平台可用 UB
dynamic_ub = SIMT launch/Tiling 的实际值
workspace_total = Σ aligned(slice_extent * sizeof(dtype))
```

不得用 tensor 的逻辑有效长度代替 buffer 分配容量。`depth=2` 必须乘入总量；alias/复用只有在同一物理子区并有生命周期证据时才能扣除。

AIV 节点要画真实 `mermaid block-beta` UB 布局，节点名称、depth、字节公式和子区必须对应初始化源码。SIMT/NDDMA/通信节点按其真实层级写 dynamic UB、中间 buffer 或通信 window；未使用 AIV UB 时写 `N/A + 实际替代路径`，不伪造 `block-beta`。随后逐复用子区说明写入者、消费点、下一次覆盖、同步依据和防止提前覆盖的条件。

重点检查四类高价值复用，但只有源码命中时才写：

1. Vector API 原地写回；
2. 同一 TBuf 跨步骤或跨迭代覆盖；
3. 编译期条件分配消除不需要的 buffer；
4. 计算结果直接写 output Queue，避免中间物化。

### 8. 提炼源码级算子优化

普通 C++ 封装、命名、继承和模板语法本身不算优化。只有改变以下至少一个维度的真实机制才进入 `Trick`：

- 搬运：减少 GM/UB 数据量、合并 DMA、广播复用、避免重复装载；
- 计算：减少 Vector 指令、扩大有效 repeat、改变归约或并行策略；
- 内存：降低 UB、原地复用、条件分配、避免中间物化；
- 精度：稳定计算顺序、升精度累加、受控 cast/round；
- 调度：用 Host specialization、模板或 tail 路线避免运行时低效分支。

每条 Trick 必须形成闭包：

1. 适用 Route 和完整触发条件；
2. 含 40 位 Commit、文件与连续行范围的最小官方源码片段；
3. 关键 API/模板实参来自哪个 POD、常量或循环变量；
4. 为什么会改变搬运、计算、内存、精度或调度；
5. 可迁移场景、平台/API/dtype/shape/资源前提；
6. 失效时的 Route、fallback 或错误终点；
7. 没有固定源码反例时明确写“固定仓未提供可验证反例”，不得编造。

不写性能百分比和未经真机验证的收益结论，只解释源码可证明的机制。

### 9. 先建完整骨架，再逐 Route 填充

写目标卡时严格使用模板标题顺序：

1. 先填 Frontmatter、H1、全部 H2/H3/H4/H5 空骨架；
2. 填接口语义、入口版本和平台证据；
3. 填 Host/Launcher 顺序、workspace、launch graph、跨节点生命周期和失败传播；
4. 填 Route 决策树、模板/节点矩阵、隐藏 Guard、POD 和闭包表；
5. 按 R-001、R-002 顺序逐条、逐 Kernel 节点填完整实现；
6. 填 Trick 和跨 Route 模板对比；
7. 填平台差异、限制、失败边界和逐文件源码索引；
8. 写入前逐条反查正文中的谓词、公式、API 实参、同步边和结论，无法定位到固定源码的内容直接删除或改成真实缺失。

不得先写摘要后跳过 Route 细节，不得用文件清单、阶段箭头或“调用公共模板”代替源码级正文。

## Route 与知识密度原则

- Route 是“选择谓词 + 参数布局 + Kernel 节点图 + Device body + 内存/同步/tail”相同的实现族，不等于一个 TilingKey。只有这些事实全部相同的 key 才能合并；合并后仍须逐 key 写选择条件与参数差异。
- Device-only、dormant、dead 路线不写入正文；Host 可达 fallback 即使低频也必须写。
- 每条 Route 必须下钻到实际方法，不得以“调用公共模板”“调用 Vector/SIMT/NDDMA/通信 API”结束。
- 必须解释 API 参数为什么取该值以及来自哪个 POD、模板常量或循环变量，而非只列 API 名。
- 官方源码片段只用于锁定难以从伪码可靠重建的分发、内存复用、执行族参数、同步和 tail 机制；片段须来自固定 Commit、标注文件和行范围，不复制大段通用库。
- `固定仓不可见` 只能描述真实外部边界，不能掩盖尚未读取的仓内依赖。

## 完成与停止条件

只有以下条件全部满足才允许保留最终卡：

- 入口类型与最低闭包匹配，平台公开支持无冲突；
- 所有 Host/launcher 可达 Device 节点都不含 Cube/AIC 或 MIX_CV；AIV/Vector、SIMT、NDDMA、非 Cube 通信/Hybrid 无论单 Kernel 还是多 Kernel 都属于 VV；
- key/selector、POD、全部 entry/body、直接 helper、Kernel 节点/边和构建接线闭合；
- 每条 Route 都有模板身份、launch graph、逐节点函数调用链、源码等价伪码、UB/workspace 字节账、节点内与节点间同步/精度/tail/lifetime 和源码符号证据；
- 至少提炼一条由源码支持的算子特定优化 trick；若源码确无优化分支，须用源码证据说明单一朴素实现边界，而不是编造 trick；

若任一 Host/launcher 可达 Device 节点发现 Cube/AIC 或 MIX_CV，停止 VV 写入并报告应切换 CV Skill。SIMT、NDDMA、非 Cube 通信/Hybrid 和多 Kernel 本身不得触发切换。闭包不足或平台冲突时不创建/覆盖对应卡，只报告精确缺口。

## 写作边界

- 正文以中文为主体；官方符号、API、dtype、layout 和硬件层级保留原名。
- 不写分数、case ID、模型轨迹、本机路径或任务控制话术。
- 不推测性能收益；只能写源码可证明的减少搬运、减少物化、提高并行度等机制，并明确本次知识提取未执行编译、真机、数值或性能测试。
- 不把源码文件列表当作知识正文。
- 最终只汇报目标文件、入口/平台/版本、Route/launch graph、关键 trick、闭包结论与未生成项缺口。
