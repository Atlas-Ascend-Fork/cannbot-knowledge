# 非 Cube/VV 单/多 Kernel 知识卡模板

本模板是最终 `Operator` 卡的唯一结构。生成时替换全部 `<...>`，不得改名、增删或重排固定标题。入口类型由调用 Prompt 指定，Skill 不选择来源层。

入口标签区分公开 ACLNN/API 的 `ACLNN`、官方内部入口的 `Host/Tiling` 和直接调用的 `Direct Invoke`。标签不定义存储路径；当前正式卡支持 `ACLNN` 和 `Direct Invoke`，Host/Tiling 独立入口没有已注册 call-mode，按主 Skill defer 写入。平台标签与 Frontmatter 必须一一对应：

| 平台标签 | `platforms` |
|---|---|
| `A2` | `[a2]` |
| `A3` | `[a3]` |
| `A2/A3` | `[a2, a3]` |
| `950` | `["950"]` |

```markdown
---
type: Operator
title: "<逻辑算子名> <平台标签> <入口标签> 算子知识"
description: "说明 <实际入口符号> 在 <平台标签> 上的接口语义、Host/Launcher 参数生成、Route 选择、单/多 Kernel 启动图与逐节点实现。"
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
| 执行类型 | <逐节点写 AIV_VECTOR/SIMT/NDDMA/非 Cube 通信/Hybrid；多 Kernel 列节点组合，不把拓扑当执行族> |
| Kernel 路线 | <R-001...，按后文顺序> |
| 核心资源 | <按实际节点写 GM/UB/TQue/TBuf/寄存器/dynamic UB/NDDMA buffer/通信 window/workspace> |
| 来源闭包 | <source_closed/kernel_tiling_closed/direct_implementation_closed>：<入口到 Kernel 的闭包摘要> |
| 验证状态 | 已完成源码闭包检查；本次知识提取未执行编译、真机、数值或性能测试。 |

## 接口与语义

### 计算语义

<公式、维度定义、运算顺序和输出有效域。>

### 输入、输出与属性

| 参数 | shape/layout | dtype | 约束、默认值与语义 |
|---|---|---|---|
| <...> | <...> | <...> | <...> |

### 入口与版本

<说明实际入口、版本族选择、入口复用及公开性；不得把一种入口补造成另一种。>

## Host/Launcher 执行流程

### 参数校验与前处理

<按调用顺序说明校验、shape 处理、Contiguous/View 或 direct 参数准备和失败返回。>

### 参数、Workspace 与生命周期

<说明参数 producer、workspace 公式/owner、executor 或 launcher 生命周期和 stream。>

### 启动图与失败传播

<说明 Host/Tiling 或 launcher 入口、单/多 Kernel 节点和启动顺序。逐节点列 Host 启动函数、entry、blockDim/grid、POD、输入输出和 workspace slice；逐边列 producer/consumer、offset/extent、dtype/layout、ordering、owner/lifetime 和失败传播。>

## Route 与参数设计

### 分核与资源计算

<说明 block/core、former/tail core、tile/loop、UB/workspace 公式、对齐和上界。>

### Route 选择

| 顺序 | Route | Key/模板 | 精确选择条件与优先级 | 不适用去向 |
|---:|---|---|---|---|
| 1 | R-001 <实现族名称> | <逐 key/selector/实例> | <完整 Host/launcher 谓词> | <下一 Route 或失败> |

```text
<与表格同序的 Host/launcher 决策树>
```

### 模板/实现执行矩阵

| Route | key/selector | dtype/shape/platform 完整命中条件 | 执行拓扑与 Kernel 节点 | 实际模板/body | 内存与同步特征 | tail/fallback |
|---|---|---|---|---|---|---|
| R-001 <实现族名称> | <逐 key> | <保持源码谓词与优先级> | <单/多 Kernel 节点及顺序> | <逐节点完整模板实例与方法> | <UB/workspace/边/同步> | <尾块与失败去向> |

### 隐藏性能 Guard

| Guard | Host/Tiling 条件 | Device/资源原因 | 影响 Route | 不满足时去向 | 源码符号 |
|---|---|---|---|---|---|
| <UB/alignment/repeat/stride/dtype/platform/空域 guard> | <源码布尔式> | <为什么该资源或 API 需要它> | <R-...> | <下一 Route/fallback/失败> | <文件 + 符号> |

### POD/ABI

| 结构 | 字段 | 类型/位宽 | ABI 布局 | 单位 | Host/launcher producer | Device consumer | 边界 |
|---|---|---|---|---|---|---|---|
| <一个结构> | <单个字段，不得合并多个字段> | <...> | <sizeof/alignof/offsetof；固定仓不可见则明确写出> | <...> | <精确函数/赋值表达式> | <精确函数/读取用途> | <...> |

### Route 源码闭包

| Route | Key/selector | Host/Tiling producer | POD/参数 | Kernel entry/router 节点 | Kernel body/直接依赖 | 构建接线 |
|---|---|---|---|---|---|---|
| R-001 <实现族名称> | <逐 key/selector> | <文件 + 函数> | <结构和关键字段> | <文件 + entry/实例> | <文件 + body/helper> | <文件 + target/config> |

## Kernel 实现

### 公共执行流程

<只写全部 Route 共享的 launch graph、entry/router、逐节点 Vector/SIMT/NDDMA/通信实际管线和公共 workspace/资源关系。>

### Route R-001：<实现族名称>

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| <API/Host/Tiling/Router> | <仓内相对路径> | <精确函数/模板实例> | <保持源码布尔关系和判断顺序> | <key、Route、fallback 或失败> |

#### Device 数据流

##### 函数级调用链

```text
<Host launch node-1 entry(args, tiling-1)>
  -> <RouteClass1::Process>
    -> <Init/CopyIn/Compute/CopyOut 实际方法>
  -> <workspace/GM edge + ordering>
<Host launch node-2 entry(args, tiling-2)>  # 单 Kernel 时删除此节点
  -> <RouteClass2::Process>
```

##### 源码等价伪码

```text
<按源码顺序保留 core/tile/loop、地址/offset、条件、CopyIn、Vector 计算、同步和有效输出提交；标明这是伪码>
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| <GM/UB/TQue/TBuf/寄存器/dynamic UB/NDDMA buffer/通信 window/workspace> | <...> | <...> | <...> | <...> | <...> | <...> | <depth、alignment、alias、复用> |

##### 分层内存布局

```mermaid
block-beta
  columns 4
  inQ["inputQueue · depth=<n> · <字节公式>"]:2
  calc["calcBuf · <字节公式>"]:1
  outQ["outputQueue · depth=<n> · <字节公式>"]:1
```

<AIV 节点的每个 buffer、depth、子区和字节公式都必须来自 InitBuffer/等价分配；SIMT/NDDMA/通信节点改画 dynamic UB、中间 buffer 或 window 真实布局。未使用 AIV UB 时删除示例图并写 `N/A + 实际替代路径`，不臆造。>

##### 字节账与复用顺序

```text
UB_total = <逐个 Queue/TBuf/LocalTensor 字节公式求和>
UB_total <= <Host 使用的平台可用 UB>
dynamic_ub = <SIMT launch/Tiling 实际值或 N/A>
workspace_total = <逐 slice 对齐字节公式>
=> <tile/IsCapable 上界>
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| <真实 buffer/offset> | <方法> | <方法> | <方法/迭代> | <DeQue/FreeTensor/event/pipe> | <不得提前覆盖的条件> |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| <...> | <Queue/event/pipe/barrier/Atomic 或 N/A> | <...> | <...> | <内存片或数据阶段> | <cast/accumulate/scale/round/repeat/stride/mask/tail/空域> |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | <仓内相对路径> | <函数> | <选择、参数或资源事实> |
| Kernel entry/router | <仓内相对路径> | <entry/实例> | <key 到 body 的映射> |
| Device body/helper | <仓内相对路径> | <实际方法/模板实例> | <循环、地址、搬运、Vector 参数、同步或 tail 事实> |

<后续 Route 严格重复以上五个四级标题。>

## 算子特定优化

### Trick T-001：<源码中真实存在的高杠杆机制>

#### 触发与源码依据

- 适用 Route：<R-...>
- 触发条件：<完整 Host/模板/循环条件>
- Golden 来源：<写成指向 40 位 Commit 文件 blob URL 与连续行范围的 Markdown 链接>

**官方源码（固定 Commit 连续逐字摘录）**：

```cpp
<只保留决定分发、内存复用、Vector 参数、同步或 tail 的最小连续源码片段>
```

#### 机制与设计原因

<说明该机制如何改变搬运、计算、内存或精度；解释关键 API 每个实参的来源和选择原因。不得写未实测的性能百分比。>

#### 迁移边界

- 适用：<可迁移场景>
- 前提：<平台/API/shape/dtype/对齐/资源条件>
- 失效：<不成立时必须改用的 Route 或实现>
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

<源码存在真实 fallback/反例时写错误做法与后果；没有证据时写“固定仓未提供可验证反例”，不得编造代码。>

<后续 Trick 按源码真实高杠杆机制递增编号；普通 C++ 封装不算优化。>

## 模板与实现对比

| 对比维度 | R-001 <名称> | R-002 <名称> | 设计选择依据 |
|---|---|---|---|
| 命中条件/优先级 | <...> | <...> | <何时选哪条> |
| 模板与 dtype | <...> | <...> | <...> |
| 循环与分核 | <...> | <...> | <...> |
| Queue/TBuf/寄存器/dynamic UB/通信 window | <...> | <...> | <...> |
| 内存总占用与复用 | <...> | <...> | <...> |
| 搬运/Vector/SIMT/NDDMA/通信 API | <...> | <...> | <...> |
| 同步、精度与 tail | <...> | <...> | <...> |
| fallback/失败边界 | <...> | <...> | <...> |

## 平台差异

| 项目 | A2 | A3 | Ascend 950 |
|---|---|---|---|
| 支持状态 | <支持/不支持/固定仓不可见> | <...> | <...> |
| Host/Launcher | <差异或共用> | <...> | <...> |
| Kernel/资源 | <差异或共用> | <...> | <...> |

## 限制与失败边界

- <接口、shape、dtype、layout、UB 上限、窄化/溢出、fallback 或源码冲突。>
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
