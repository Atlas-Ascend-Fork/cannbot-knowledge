---
name: ops-knowledge-cv-ingest
description: 从固定版本官方源码提取至少一个 Host/launcher 可达 Device 节点含 Cube/AIC 或 MIX_CV 的源码级算子知识；闭合 Cube 节点及其与 AIV/Vector、SIMT、NDDMA、通信节点组成的单/多 Kernel 任务图、内存、workspace、同步和生命周期。若所有可达 Device 节点都不含 Cube/AIC 或 MIX_CV，无论其是 Vector、SIMT、NDDMA、通信、Hybrid 还是多 Kernel，均改用 VV Skill。
---

# Cube/CV 算子源码知识提取

本 Skill 负责把一个含可达 Cube/AIC 或 MIX_CV 节点的逻辑算子固定版本源码转换为可指导实现复用的中文 `Operator` 卡。CV 不使用简化流程：它与 VV 一样先还原平台、入口、Host 分发、Tiling/POD、模板与实际 body，再补齐 Cube/AIC 或 MIX_CV 与同图中其它节点的内存层级、交接边和同步。

只产出 Prompt 指定的最终文件。不得写 runbook、index、Registry、图谱、inventory、mapping、ledger、staging、receipt、日志或状态文件。

本 Skill 不执行编译、单元测试、真机、数值或性能测试，不生成测试代码，也不调用校验脚本。运行验证统一标记为“本次知识提取未执行”。

## 必须输入

Prompt 必须给出固定源码仓与 40 位 Commit、唯一逻辑算子、入口类型与符号、源码起始范围、目标平台、CANN 版本和独占最终文件列表。

模板中的 `<CANN_VERSION>` 使用本任务指定且有固定来源依据的 CANN 版本，不沿用示例或其他任务的版本。输入与来源冲突时先报告缺口，不生成带错误版本范围的正式卡；模板平台标签只对应本次证据范围。

| 入口类型 | 标题标签 | 最低闭包 |
|---|---|---|
| 公开 ACLNN/API | `ACLNN` | `source_closed` |
| 官方内部 Host/Tiling | `Host/Tiling` | `kernel_tiling_closed` |
| 直接调用 | `Direct Invoke` | `direct_implementation_closed` |

入口类型由 Prompt 决定，不得补造。缺少必填输入时停止写入。

写入前按 [路径 Spec](../../../governance/specs/paths.md#profile-附加层级)核对任务指定路径与入口语义：公开 ACLNN/API 的完整链路使用 `aclnn`，独立 Direct Invoke 使用 `direct`。当前 Registry 没有仅覆盖官方内部 Host/Tiling 的 call-mode；这类输入可报告源码分析与路径缺口，但必须 defer 最终卡写入，不得借用 `aclnn`、`direct` 或临时创建目录。闭包标签不替代路径准入；后续需先完成分类治理再落库。

## 开始前必须完整读取

1. [`references/execution-families.md`](references/execution-families.md)：可达 Cube/AIC 或 MIX_CV 节点及其所在单/多 Kernel 任务图闭合；
2. [`templates/operator-template.md`](templates/operator-template.md)：最终卡唯一结构。

不得只看模板和文件名后直接写卡。`references/execution-families.md` 只读实际可达执行族章节，但 Host/POD/生命周期公共章节必读。

## 源码与逻辑算子边界

- Prompt 的源码范围是扫描起点。include、继承、模板实例、共享 Tiling/POD、兄弟目录公共实现和 CMake dependency 必须在固定仓内递归追踪。
- 读取兄弟算子目录中的公共实现不允许生成兄弟逻辑算子的卡；本 Agent 仍只写目标文件。
- generated ACLNN inner bridge、普通 `Contiguous/ViewCopy` 和通用 AscendC/CATLASS primitive 内部可作为标注清楚的框架/库边界；当前实例选择的 specialization、POD、workspace、调用顺序、同步和 tail 不能外推为“公共模板”。
- 多 Kernel 公开入口中的每个核心语义节点都必须进入 launch graph。若核心节点的 Host/Tiling/Kernel 不在固定源码集合且无法闭合，不发布正式卡。

## 平台与版本判定

平台证据顺序与 VV 一致：公开 README/API 产品表 → `SUPPORT_COMPUTE_UNIT`/OpDef/config → Host selector/POD/Kernel/CI。公开文档明确“不支持”与实现接线冲突时，停止该平台正式卡并报告冲突。

只提取同平台实际支持的最新公开版本；Grad、原地、量化等不同数学语义分别建卡。`arch35`、`_apt`、`ascend950`、单个 binary config 均不是独立的平台支持证明。

## 固定提取流程

CV 沿用 VV 的完整流程，不允许退化成“Cube 段 + Vector 段”概述：

1. **冻结身份、平台与执行族**：确认入口、版本、平台、目标文件；枚举每条 Host 可达 Route 的真实执行族。
2. **扫描源码闭包**：递归枚举入口、Host/Tiling、POD、router、每个 kernel/body/helper、通信/同步实现和构建接线。
3. **还原分发和 launch graph**：识别决策树、`IsCapable`、tuple/selector；建立 key→模板→POD→kernel 节点/边→body 的完整矩阵。
4. **逐字段闭合 Host/Tiling/POD**：解释原始维度、M/N/K、tile、core、workspace 切片、selector、每个字段的 producer/consumer 和边界。
5. **逐 Route 阅读实际 body**：按调用顺序下钻 `Init/Process`、Cube/Vector/SIMT/NDDMA body、搬运、计算、同步、精度和 tail。
6. **做分层内存字节账**：逐项核对 GM/workspace/L1/L0A/L0B/L0C/UB/寄存器；对每条跨族边记录 offset、extent、dtype/layout、owner、lifetime 和同步。
7. **提炼源码级优化 trick**：提取会改变搬运、计算、内存、通信或精度的 specialization、调度、复用和同步机制，保留最小官方源码片段与迁移边界。
8. **写卡并做模板/流水线对比**：先骨架、后公共章节、再逐 Route、trick、对比、平台、限制与索引。

## 完整源码提取算法

CV 必须执行与 VV 相同粒度的入口、平台、分发、POD、逐 Route 和源码优化提取；下列内容直接构成 Skill 主流程，不能只读模板后自行概括。所有临时矩阵只保留在模型上下文，不写中间文件。

### 1. 建立完整 Golden 源码闭包

从 Prompt 指定入口和源码目录开始，递归追踪当前逻辑算子的仓内依赖，并按 `ingest/defer/skip` 分类：

- `ingest`：公开入口、API 实现、Host/Tiling、POD、router、所有可达 kernel/body/helper、通信同步和构建接线；
- `defer`：共享基类、include、CATLASS/Matmul specialization、兄弟目录公共 Tiling 或调度 helper，调用链命中后必须继续读取；
- `skip`：测试样板、未实例化通用库代码、其它逻辑算子和与目标 Route 无关的实现。

必须覆盖：

| 层级 | 必须提取的事实 |
|---|---|
| 公开入口 | API 版本、接口语义、参数、产品支持和错误边界 |
| API/Host | inner bridge、前处理、workspace/executor、launch 顺序、失败传播 |
| Tiling | selector、M/N/K 或业务维度、tile/core、workspace 切片和资源上界 |
| POD/ABI | 逐字段 producer/consumer、类型、位宽、单位、布局和 inactive 条件 |
| Router | key、模板实例、kernel 类型、编译 guard、unknown key 终点 |
| Device body | Cube/AIV/SIMT/NDDMA/通信 body、helper、内存、同步、精度和 tail |
| 构建接线 | CMake、binary config、平台 target、注册宏和 kernel 节点选择 |

多 Kernel 入口要把每个核心语义节点都闭合；若某节点实际调用其它算子，而其语义、workspace、Host/Tiling/Kernel 均不在固定源码集合，则该公开入口不能声明 `source_closed`。

### 2. 冻结语义、入口版本、平台和执行族

在阅读 Device 细节前先确认：

| 字段 | 必须确认的内容 |
|---|---|
| 逻辑算子 | 公式、输入输出有效域、Grad/原地/量化等独立语义 |
| 实际入口 | Prompt 指定的 ACLNN/API、Host/Tiling 或 Direct Invoke 符号 |
| 最新版本 | 当前平台真正支持的最新版本，以及旧版 body 复用关系 |
| 平台证据 | README/API → OpDef/config → Host/Kernel/CMake 的完整证据链 |
| 执行族 | 逐 Device 节点标记 Cube/AIC、MIX_CV、AIV_VECTOR、SIMT、NDDMA、Hybrid 或非 Vector 通信执行；多 Kernel 不是执行族 |
| 启动拓扑 | 单 Kernel 或多 Kernel；多 Kernel 时列节点和边，不用拓扑替代执行族 |
| 目标文件 | 无后缀 A2/A3 卡和 `_950` 卡的真实平台边界 |

公开文档明确“不支持”时，Kernel 文件、`arch35`、`_apt`、`ascend950` 或 CI 接线不能单独证明公开支持。文档与实现冲突时停止该平台正式卡。

执行族不能只看文件名，必须从 kernel launch 形式、entry、模板实例和实际 body 判断：

- 全部可达 Device 节点都不含 Cube/AIC 或 MIX_CV：停止 CV，改用 VV；Vector、SIMT、NDDMA、通信、Hybrid、单/多 Kernel 同样处理；
- 只要一个可达 Device 节点含 Cube/AIC 或 MIX_CV：继续 CV，并同时闭合与它同图的其它执行族节点；
- SIMT、NDDMA、通信、Hybrid 或多 Kernel 本身不能单独作为 CV 准入条件；
- dormant、device-only、无 Host producer 的实现不进入正式 Route。

### 3. 还原 Host selector 与 launch graph

#### 3.1 分发模式

识别并完整展开三类 selector：

1. 单函数 `if/else` 决策树：保持布尔关系、判断顺序和短路；
2. priority + `IsCapable`：列出全部模板、priority、逐模板资源条件和失败后下一跳；
3. tuple/注册表/lookup/编译期 specialization：展开外层平台→内层 tuple/key→router 实例。

对每条 Host 可达 Route 建立：

```text
公开入口
  -> 参数校验和前处理
    -> selector/key/模板
      -> POD 与 workspace producer
        -> kernel 节点 1
          -> 同步/交接边
            -> kernel 节点 2 ...
              -> 输出提交或失败终点
```

#### 3.2 Launch graph

每个节点必须记录：

- Host 添加或启动节点的精确函数；
- kernel entry、执行族、blockDim/grid/thread/dynamic UB；
- 输入、输出、workspace slice 和 POD；
- 前驱、后继、stream/event/flag/pipe/atomic ordering；
- launch 失败是否阻止后续节点；
- 空域、fallback 和 cleanup/lifetime。

多 Kernel 不允许只写“先 Cube 后 Vector”。必须逐边说明 producer、offset/extent、dtype/layout、consumer、同步和 owner/lifetime。

### 4. 建立 Route、模板、节点和 Guard 矩阵

| Route | key/selector | 完整命中条件 | 执行族与 kernel 节点 | 实际模板/body | 内存与同步 | tail/fallback |
|---|---|---|---|---|---|---|
| R-001 | 源码 key | 平台/dtype/shape/资源完整谓词 | 节点及顺序 | 完整 specialization | workspace/L1/L0/UB/边 | 尾块和不满足去向 |

Route 合并必须同时满足 selector、执行族、节点图、POD、内存布局、同步图、精度和 tail 完全一致。多个 key 仅在这些事实相同时才能合并，且仍要逐 key 写差异。

扫描全部隐藏 Guard：

- UB/L1/L0/workspace 容量与 baseM/baseN/baseK；
- stepM/stepN、tile、scheduler、splitK、是否全载；
- alignment、padding、bank conflict、stride 和 DMA 上限；
- rank/world size、通信 topology、thread/block/warp、dynamic UB；
- dtype/layout/platform 编译宏、量化模式、尾块和空域；
- fallback、unknown key、unsupported 和最终返回码。

每个 Guard 都要说明 Host 条件、Device/资源原因、影响 Route、不满足去向和源码符号。

### 5. 逐字段闭合 Host/Tiling/POD

#### 5.1 API 与 Host 顺序

按源码顺序提取：输入/输出/属性校验 → Contiguous/View/TransData 等前处理 → 维度归一化 → workspace size → executor/launcher → Tiling → kernel 节点添加 → stream 执行 → 失败传播和释放。

框架生成的 inner bridge 可以标注边界，但算子拥有的 selector、workspace 切片、POD、节点顺序和失败处理不能外推。

#### 5.2 Tiling 推导

必须保留变量依赖顺序：

```text
原始 shape/dtype/layout/attr
  -> M/N/K、batch、group、rank 或业务轴
  -> Route 与 specialization
  -> core/grid/thread、base/tile/step/loop
  -> workspace/L1/L0/UB 容量、offset 与对齐
  -> blockDim、节点参数和 POD 写入
```

每个公式说明元素/字节/core/thread/repeat 等单位，检查零维、向上取整、对齐、乘法溢出和字段窄化。

#### 5.3 POD/ABI

每个字段独占一行，逐项写：结构、字段、类型/位宽、`sizeof/alignof/offsetof`、单位、Host producer、Device consumer、合法范围、inactive Route 和默认值读取行为。Host 与各 kernel 节点使用不同 POD 时分别列出，不能合并成“tiling 参数”。

### 6. 逐 Route 阅读所有 Device body

每条 Route 都必须先写 entry/router，再按实际执行族下钻到方法和 API 参数。

#### 6.1 公共入口检查

- entry 参数顺序、GM 指针类型和 POD 解析；
- key、模板实参、对象构造和实际 body；
- 平台/dtype 编译 guard；
- unknown key、空指针、空域和无输出终点；
- 多 entry 之间是否共用 workspace 或同步状态。

#### 6.2 Cube 路线

闭合当前 specialization 的真实数据流：

```text
GM
  -> L1 或实际替代路径
    -> L0A/L0B
      -> Mmad/Matmul
        -> L0C
          -> Fixpipe/GM/workspace/Vector epilogue
```

必须解释：

- M/N/K、batch/group 到 core、tile、base 和 loop 的映射；
- A/B 的 layout、transpose、format 和搬运参数；
- L1/L0A/L0B/L0C 的容量、double buffer、复用和生命周期；
- Mmad/Matmul 的 type traits、scheduler、step/splitK 和累加 dtype；
- bias、scale、quant/dequant、activation、cast/round 的准确顺序；
- tail M/N/K 和 alignment/padding；
- 未使用层级必须写 `N/A + 实际替代路径`。

#### 6.3 单 Kernel MIX_CV

分别写 AIC 与 AIV 的任务图，不得合成一个“融合 Kernel”：

- AIC producer 产生哪块 L0C/GM/workspace 数据；
- AIV consumer 从哪个 offset/extent、以何 dtype/layout 读取；
- AIC↔AIV 使用的 flag/event/pipe、编号、轮次和 wait/set 顺序；
- 双方 core 映射、并发批次和 tail；
- buffer 何时可覆盖、谁拥有并在何处释放。

#### 6.4 含 Cube/AIC 或 MIX_CV 节点的多 Kernel 拓扑

逐节点写 kernel entry、body、grid/blockDim、输入输出、workspace slice 和失败传播；逐边写 producer、offset/extent、dtype/layout、consumer、ordering 和 lifetime。Host launch 顺序不自动等价于 Device 可见性，必须找到 stream/event/框架保证。

#### 6.5 SIMT

必须写：block/thread/warp 到输出域映射、threadsPerBlock、numBlocks、dynamic UB、共享/局部内存、cooperative primitive、atomic 冲突范围、barrier 和 tail。只看到四参数 launch 不足以描述算法，必须追入 SIMT body。

#### 6.6 NDDMA

必须写：源/目标 block、blockCount、blockLen、src/dst stride、alignment/padding、搬运阶段、与计算/通信的同步和不满足条件时 fallback。

#### 6.7 通信或 Hybrid

写清 rank/world size、通信 handle、token/dispatch 范围、collective 或 point-to-point 顺序、通信 buffer owner/lifetime、计算通信交叠条件、event/stream 依赖和失败传播。不能把通信库调用名当作闭包终点。

### 7. 做分层内存字节账

每条 Route 按实际层级计算：

```text
workspace_total = Σ aligned(slice_extent * sizeof(dtype))
L1_total = Σ A/B/stage buffer bytes
L0_total = L0A + L0B + L0C
UB_total = Σ depth * aligned_elements * sizeof(dtype)
dynamic_ub = SIMT launch 或 Tiling 实际值
```

逻辑 tensor 长度不能替代物理分配容量，double buffer 必须乘 depth；alias 只有在 offset 重叠和生命周期均有源码证据时才可扣除。

每条跨 kernel 或跨 AIC/AIV 边必须写：producer、offset/extent、dtype/layout、consumer、ordering/sync、owner/lifetime 和防覆盖条件。随后画与当前 Route 一致的 Mermaid 分层图；Vector 子段存在独立 UB 队列时补 `block-beta` 布局。

### 8. 下钻公共库的当前实例

通用 Matmul/CATLASS/通信库内部无需整库复制，但不能写成黑盒。必须记录当前 Route 实际选择的：

- 完整模板/type traits；
- tile/base/step/layout/transpose；
- scheduler、prologue、mainloop 和 epilogue specialization；
- workspace 或共享内存需求；
- 当前实例改变精度、量化、同步、tail 或输出布局的行为；
- 固定仓不可见的真正外部边界。

如果 selector 或构建接线无法证明某 specialization 实际命中，不得将通用模板存在当作当前实现事实。

### 9. 提炼源码级 CV 优化

只有改变搬运、计算、通信、内存、精度或调度的真实机制才写 Trick，例如：

- full-load 与分块路线按容量 specialization；
- Cube 与 Vector 融合消除中间 GM 物化；
- workspace ping-pong 或跨 kernel slice 复用；
- splitK、scheduler、base/step 针对 shape 的选择；
- quant/dequant、bias、activation 融合与累加精度控制；
- SIMT cooperative/atomic 冲突规避；
- NDDMA 合并搬运或通信计算交叠。

每条 Trick 必须包含：适用 Route、完整触发条件、固定 Commit 最小连续源码片段、关键模板/API 实参来源、机制与设计原因、平台/dtype/layout/shape/资源/通信前提、失效 Route 或 fallback、未执行运行测试状态。没有源码反例时写“固定仓未提供可验证反例”，不得编造。

### 10. 先建骨架，再按 Route 与节点填充

严格使用模板固定顺序：

1. 创建 Frontmatter、H1 和全部固定标题骨架；
2. 填接口语义、入口版本、平台和执行族；
3. 填 Host 前处理、workspace、launch graph 和失败传播；
4. 填 Route 决策树、执行矩阵、隐藏 Guard、POD 和闭包表；
5. 按 R-001、R-002 顺序，为每条 Route 填选择证据、调用链、伪码、分层内存、字节账、交接边、同步和符号；
6. 填源码 Trick 与模板/流水线对比；
7. 填平台差异、限制、失败边界、源码索引和实现复用检查；
8. 写入前逐条反查谓词、公式、模板实参、offset、同步边和结论，无法定位到固定源码的事实直接删除或改成真实缺失。

不得用“调用 Matmul”“执行 Cube 后处理”“启动多个 Kernel”等摘要代替实际 specialization、节点、内存和同步闭包。

## CV Route 闭包原则

- VV/CV 分流以目标平台范围内全部可达 Route 的节点集合为准。整体存在 Cube/AIC 或 MIX_CV 节点时，纯 Vector、SIMT、NDDMA 或通信分支也由本 Skill 在同一卡中闭合；不得逐 Route 改派 producer 或补造 Cube 路径。
- Route 只有在 selector、执行族、kernel 节点图、POD、内存布局、同步图、精度/tail 完全相同时才可合并。
- 单 Kernel MIX 必须分别写 AIC 与 AIV 的任务图，并逐交接边记录 producer、memory/offset、shape/dtype/layout、consumer、同步、轮次和 lifetime。
- 多 Kernel 必须列全节点和边；workspace 只写“存在”不算闭包。
- Cube 必须闭合当前实例的 `GM→L1→L0A/L0B→Mmad/Matmul→L0C→Fixpipe/GM`，未使用层级写 `N/A + 实际替代路径`。
- SIMT 必须写 block/thread/warp 到输出域映射、动态 UB、cooperative/atomic 和 tail；NDDMA 必须写 block/stride/alignment、阶段与 fallback。
- 通用 Matmul/CATLASS 库不整段复制，但必须列当前 route 的 tile/layout/type traits、scheduler、prologue/epilogue specialization 及其行为。

## 完成与停止条件

只有入口最低闭包、平台公开支持、Route/launch graph、逐字段 POD、每个 body/helper、分层内存、跨族同步、精度/tail、构建接线和源码级 trick 全部闭合，才允许保留最终卡。

全部 Host/launcher 可达 Device 节点都不含 Cube/AIC 或 MIX_CV 时停止 CV 写入并改用 VV Skill，无论其它节点是 Vector、SIMT、NDDMA、通信、Hybrid，也无论是单 Kernel 还是多 Kernel。闭包不足或平台冲突时不创建/覆盖对应卡，只报告精确缺口。

## 写作边界

- 正文以中文为主体，保留官方符号和硬件层级。
- 不写分数、case ID、模型轨迹、本机路径或任务控制话术。
- 不推测性能收益；只解释源码可证明的机制，并明确本次知识提取未执行编译、真机、数值或性能测试。
- 不用“调用通用 Matmul/通信模板”替代当前实例参数。
- 最终只汇报目标文件、入口/平台/版本、Route/launch graph、关键 trick、闭包结论和未生成项缺口。
