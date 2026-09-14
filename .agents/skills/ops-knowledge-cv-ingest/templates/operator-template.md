# Cube/CV 知识卡模板

本模板是最终 `Operator` 卡的唯一结构。生成时替换全部 `<...>`，不得改名、增删或重排固定标题。入口类型由调用 Prompt 指定，Skill 不选择来源层。

入口标签区分公开 ACLNN/API 的 `ACLNN`、官方内部入口的 `Host/Tiling` 和直接调用的 `Direct Invoke`。标签不定义存储路径；当前正式卡支持 `ACLNN` 和 `Direct Invoke`，Host/Tiling 独立入口没有已注册 call-mode，按主 Skill defer 写入。平台标签与 Frontmatter 必须一一对应：

| 平台标签 | `platforms` |
|---|---|
| `A2` | `[a2]` |
| `A3` | `[a3]` |
| `A2/A3` | `[a2, a3]` |
| `950` | `["950"]` |

CV 分流针对目标算子的全部可达 Route；整体至少有一个 Cube/AIC 或 MIX_CV 节点即可。某条 Route 没有 Cube 节点时仍保留在本卡，不补造 Cube 节点或拆交 VV；按该 Route 的真实执行族填写资源与同步。

```markdown
---
type: Operator
title: "<逻辑算子名> <平台标签> <入口标签> 算子知识"
description: "说明 <实际入口符号> 在 <平台标签> 上的接口语义、Host/Launcher 参数生成、Route 选择与 Kernel 实现。"
tags: [task.implementation, task.lookup, topic.data_movement, topic.memory, topic.precision, topic.programming_model]
status: stable
sources:
  - resource: <含 40 位 Commit 的入口声明或约束文件 blob URL>
    role: header
  - resource: <含 40 位 Commit 的入口实现文件 blob URL>
    role: implementation
  - resource: <含 40 位 Commit 的 Host/Tiling/POD 文件 blob URL>
    role: implementation
  - resource: <含 40 位 Commit 的 Kernel entry/body 文件 blob URL>
    role: implementation
  - resource: <含 40 位 Commit 的构建接线文件 blob URL>
    role: implementation
created_at: "<UTC RFC3339 秒精度>"
updated_at: "<UTC RFC3339 秒精度>"
platforms: [<按平台标签填写>]
cann_versions: ["<CANN_VERSION>"]
---

# <逻辑算子名> <平台标签> <入口标签> 算子知识

## 算子速览

| 项目 | 内容 |
|---|---|
| 实际入口 | <入口符号、版本和入口类型> |
| 计算语义 | <核心公式或数据变换> |
| 输入输出 | <关键 shape、dtype、layout> |
| 执行类型 | <必须至少列一个 AIC_CUBE 或 MIX_CV 可达节点；再按实际列同图的 AIV_VECTOR/SIMT/NDDMA/通信/Hybrid 节点，多 Kernel 不当执行族> |
| Kernel 路线 | <R-001...，按后文顺序> |
| 核心资源 | <GM/workspace/L1/L0/UB/寄存器> |
| 来源闭包 | <source_closed/kernel_tiling_closed/direct_implementation_closed>：<入口到 Kernel 的闭包摘要> |
| 验证状态 | 已完成源码闭包检查；本次知识提取未执行编译、真机、数值或性能测试。 |

## 接口与语义

### 计算语义

<公式、维度定义、运算顺序；量化、bias、activation、cast 和 round 的先后关系。>

### 输入、输出与属性

| 参数 | shape/layout | dtype | 约束、默认值与语义 |
|---|---|---|---|
| <...> | <...> | <...> | <...> |

### 入口与版本

<说明实际入口、版本族选择、入口复用及公开性；不得把一种入口补造成另一种。>

## Host/Launcher 执行流程

### 参数校验与前处理

<按调用顺序说明校验、Contiguous/View/TransData 或 direct 参数准备和失败返回。>

### 参数、Workspace 与生命周期

<说明参数 producer、workspace 公式/切片/owner、executor 或 launcher 生命周期和 stream。>

### 启动图与失败传播

<说明 Host/Tiling 或 launcher 入口、blockDim、launch graph、Kernel entry 和失败传播。>

## Route 与参数设计

### 分核与资源计算

<说明原始维度、分核、tile、UB/L1/L0/workspace 计算顺序、对齐和上界。>

### Route 选择

| 顺序 | Route | Key/模板 | 精确选择条件与优先级 | 不适用去向 |
|---:|---|---|---|---|
| 1 | R-001 <实现族名称> | <逐 key/selector/实例> | <完整 Host/launcher 谓词> | <下一 Route 或失败> |

```text
<与表格同序的 Host/launcher 决策树>
```

### 模板/实现执行矩阵

| Route | key/selector | dtype/shape/platform 完整命中条件 | 执行族与 kernel 节点 | 实际模板/body | 内存与同步特征 | tail/fallback |
|---|---|---|---|---|---|---|
| R-001 <实现族名称> | <逐 key> | <源码谓词与优先级> | <当前 Route 的实际执行族及单/多 Kernel 节点图；允许纯非 Cube 分支> | <完整实例与方法> | <workspace/L1/L0/UB/同步> | <尾块与失败去向> |

### 隐藏性能 Guard

| Guard | Host/Tiling 条件 | Device/资源原因 | 影响 Route | 不满足时去向 | 源码符号 |
|---|---|---|---|---|---|
| <UB/L1/L0/base/step/alignment/rank/thread/dtype/platform guard> | <源码布尔式> | <为什么当前 specialization 需要它> | <R-...> | <下一 Route/fallback/失败> | <文件 + 符号> |

### POD/ABI

| 结构 | 字段 | 类型/位宽 | ABI 布局 | 单位 | Host/launcher producer | Device consumer | 边界 |
|---|---|---|---|---|---|---|---|
| <一个结构> | <单个字段，不得合并多个字段> | <...> | <sizeof/alignof/offsetof；固定仓不可见则明确写出> | <...> | <精确函数/赋值表达式> | <精确函数/读取用途> | <...> |

### Route 源码闭包

| Route | Key/selector | Host/Tiling producer | POD/参数 | Kernel entry/router | Kernel body/直接依赖 | 构建接线 |
|---|---|---|---|---|---|---|
| R-001 <实现族名称> | <逐 key/selector> | <文件 + 函数> | <结构和关键字段> | <文件 + entry/实例> | <文件 + body/helper> | <文件 + target/config> |

## Kernel 实现

### 公共执行流程

<只写全部 Route 共享的 entry/router、任务图、公共 workspace 切片和同步关系。>

### Route R-001：<实现族名称>

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| <API/Host/Tiling/Router> | <仓内相对路径> | <精确函数/模板实例> | <保持源码布尔关系和判断顺序> | <key、Route、fallback 或失败> |

#### Device 数据流

##### 函数级调用链

```text
<entry(args, tiling)>
  -> <RouteClass::Process>
    -> <Init/调度方法>
    -> <实际 body/helper 方法>
    -> <输出提交方法>
```

##### 源码等价伪码

```text
<按源码顺序保留循环、地址/offset、条件、搬运、计算、同步和有效输出提交；标明这是伪码>
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| <GM/workspace/L1/L0A/L0B/L0C/UB/寄存器；未使用层级写 N/A> | <...> | <...> | <...> | <...> | <...> | <...> | <...> |

##### 分层内存布局

```mermaid
flowchart LR
  GM["GM 输入"] --> L1["L1 或 N/A"]
  L1 --> L0["L0A/L0B→Mmad→L0C 或实际替代路径"]
  L0 --> WS["GM/workspace 交接"]
  WS --> UB["AIV UB/TQue/TBuf"]
  UB --> OUT["GM 输出"]
```

<按当前 Route 的真实执行族改画；Vector 子段另给 block-beta UB 布局。每个层级、节点和边必须来自源码。>

##### 字节账、交接边与复用顺序

```text
workspace_total = <逐 slice 字节公式>
L1/L0/UB = <当前 specialization 的逐层容量公式>
UB_total <= <Host 使用的平台可用 UB>
```

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 安全条件 |
|---|---|---|---|---|---|---|---|
| <真实跨 kernel/跨 AIC-AIV 边或 buffer> | <方法> | <字节公式> | <...> | <方法> | <flag/event/stream/pipe> | <owner 与释放点> | <防覆盖/尾块条件> |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| <...> | <event/flag/pipe/barrier/Atomic/stream 顺序或 N/A> | <...> | <...> | <内存片或数据阶段> | <cast/accumulate/scale/round/alignment/stride/mask/tail/空域> |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | <仓内相对路径> | <函数> | <选择、参数或资源事实> |
| Kernel entry/router | <仓内相对路径> | <entry/实例> | <key 到 body 的映射> |
| Device body/helper | <仓内相对路径> | <实际方法/模板实例> | <循环、地址、搬运、计算、同步或 tail 事实> |

<后续 Route 严格重复以上五个四级标题。>

## 算子特定优化

### Trick T-001：<源码中真实存在的调度、融合、复用或精度机制>

#### 触发与源码依据

- 适用 Route：<R-...>
- 触发条件：<完整 selector/模板/shape/平台条件>
- Golden 来源：<写成指向 40 位 Commit 文件 blob URL 与连续行范围的 Markdown 链接>

**官方源码（固定 Commit 连续逐字摘录）**：

```cpp
<只保留决定 specialization、内存层级、跨族同步、量化/精度或 tail 的最小连续源码片段>
```

#### 机制与设计原因

<解释该机制如何改变搬运、计算、通信、内存或精度，并说明关键 API/模板实参为什么取该值。>

#### 迁移边界

- 适用：<可迁移场景>
- 前提：<平台/API/shape/dtype/layout/资源/通信条件>
- 失效：<必须改用的 Route 或实现>
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

<有固定源码反例/fallback时写错误与后果；否则写“固定仓未提供可验证反例”，不得编造。>

<后续 Trick 按真实高杠杆机制递增编号。>

## 模板与实现对比

| 对比维度 | R-001 <名称> | R-002 <名称> | 设计选择依据 |
|---|---|---|---|
| 命中条件/优先级 | <...> | <...> | <...> |
| 执行族/节点图 | <...> | <...> | <...> |
| M/N/K、tile 与 scheduler | <...> | <...> | <...> |
| workspace/L1/L0/UB | <...> | <...> | <...> |
| AIC/AIV 或 kernel 交接 | <...> | <...> | <...> |
| 同步、精度与 tail | <...> | <...> | <...> |
| fallback/失败边界 | <...> | <...> | <...> |

## 平台差异

| 项目 | A2 | A3 | Ascend 950 |
|---|---|---|---|
| 支持状态 | <支持/不支持/固定仓不可见> | <...> | <...> |
| Host/Launcher | <差异或共用> | <...> | <...> |
| Kernel/资源 | <差异或共用> | <...> | <...> |

## 限制与失败边界

- <接口、shape、dtype、layout、资源、溢出、fallback 或源码冲突。>
- <固定仓不可见和未验证内容；不得推测补齐。>

## 源码索引

### 链路索引

| 链路阶段 | 文件 | 关键符号 | 支撑内容 |
|---|---|---|---|
| 入口声明/约束 | <相对路径> | <...> | <...> |
| 入口实现 | <相对路径> | <...> | <...> |
| Host/Tiling/Launcher | <相对路径> | <...> | <...> |
| Kernel entry/body | <相对路径> | <...> | <...> |
| 构建接线 | <相对路径> | <...> | <...> |

每行只写一个文件，并确保该文件存在于 Frontmatter `sources`。

### 实现复用检查

| 检查项 | 可复用事实 | 不得改变的约束 | 源码符号 |
|---|---|---|---|
| ABI/POD | <...> | <字段顺序、位宽、单位、inactive 字段等> | <...> |
| 调用顺序 | <...> | <producer→consumer/launch 顺序> | <...> |
| workspace/内存 | <...> | <offset、extent、alignment、owner/lifetime> | <...> |
| 同步 | <...> | <event/flag/pipe/Atomic/stream 协议> | <...> |
| 精度与尾块 | <...> | <cast/round/accumulate/mask/tail> | <...> |
| 失败边界 | <...> | <fallback、空域、错误终点> | <...> |
```
