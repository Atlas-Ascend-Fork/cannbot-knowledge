---
type: Glossary
title: AscendC 存储层次与执行单元术语表
description: AscendC kernel 高频术语的稳定定义与检索别名——GM/L1/L0A/L0B/L0C/UB 等存储单元、AI Core 与 Cube/Vector/Scalar 执行单元、CopyIn/Compute/CopyOut 编程阶段，并给出物理存储与 TPosition 逻辑位置的边界（含 TPosition::A2 与平台 a2 的同名陷阱）。
tags:
- task.lookup
- topic.terminology
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/technical_appendix/concepts_and_terms/glossary.md
  role: primary
created_at: '2026-10-23T01:55:00Z'
updated_at: '2026-10-27T16:44:00Z'
---

# AscendC 存储层次与执行单元术语表

本表收录 AscendC kernel 材料里高频出现的**存储单元、执行单元与编程阶段**术语，给出稳定定义与
检索别名。只写定义，不含用法、配置与操作步骤；容量、对齐与数据通路细节见相邻卡。

## 存储单元

### Global Memory / GM

- **定义**：设备端的主内存，AI Core 的外部存储，用于存储大规模数据，但需要优化访问模式以提升性能。
- **别名**：GM、全局内存、设备主存

### Local Memory

- **定义**：AI Core 的内部存储，包括 L1 Buffer、L0A Buffer、L0B Buffer、L0C Buffer、UB 等存储单元。
- **别名**：片上存储、本地内存、Local Memory

### L1 Buffer

- **定义**：AI Core 内部物理存储单元，空间相对较大，通常用于缓存矩阵计算的输入数据。矩阵计算的
  输入一般需要从 GM 搬运到 L1 Buffer，然后分别搬运到 L0A Buffer 和 L0B Buffer。
- **别名**：L1、L1 缓存

### L0A Buffer

- **定义**：AI Core 内部物理存储单元，通常用于存储矩阵计算的左矩阵。
- **别名**：L0A

### L0B Buffer

- **定义**：AI Core 内部物理存储单元，通常用于存储矩阵计算的右矩阵。
- **别名**：L0B

### L0C Buffer

- **定义**：AI Core 内部物理存储单元，通常用于存储矩阵计算的结果。
- **别名**：L0C

### Unified Buffer / UB

- **定义**：AI Core 内部物理存储单元，主要用于矢量计算，也可用于存储矢量计算过程中的输入、输出
  和临时数据。
- **别名**：UB、统一缓冲、统一缓冲区

### BiasTable Buffer

- **定义**：偏置存储，AI Core 内部物理存储单元，通常用于存储矩阵计算所需的 Bias（偏置）数据。
- **别名**：偏置存储、Bias Buffer

### Fixpipe Buffer

- **定义**：AI Core 内部物理存储单元，通常用于存储 Fixpipe 搬运过程中所需的量化参数等数据。
- **别名**：Fixpipe 缓冲、量化参数缓冲

### SSBuffer

- **定义**：AI Core 内部物理存储单元。在分离模式下，Cube Core 和 Vector Core 可选择使用
  SSBuffer 在两者的 Scalar 单元之间通信；具体比例和可用性随硬件能力变化。
- **别名**：SS Buffer、Cube/Vector 通信缓冲

### Workspace

- **定义**：通常指一个预分配的、临时使用的 Global Memory 内存，用于存储中间结果或临时数据。
- **别名**：工作空间、临时 GM 区

## 执行单元与计算核

### AI Core

- **定义**：AI 处理器的计算核，负责执行矩阵、矢量计算密集的任务。
- **别名**：AI 核、AI 计算核

### Core

- **定义**：拥有独立 Scalar 计算单元的计算核；Scalar 计算单元承担核内的指令发射等功能，因此 Core
  也称之为核内的调度单元。
- **别名**：调度单元
- **边界**：与 AI Core 不是同一个词条的两种写法——源文件把两者分列为独立术语，读到"Core"时先确认
  上下文指的是"带 Scalar 的核"还是泛指的 AI Core。

### Cube

- **定义**：AI Core 上的 Cube 计算单元，负责执行矩阵运算。以 float16 数据类型为例，Cube 每次执行
  可完成两个 float16 类型的 16x16 矩阵的乘法操作。
- **别名**：Cube 单元、矩阵计算单元

### Vector

- **定义**：AI Core 上的 Vector 计算单元，负责执行矢量运算。其算力低于 Cube，但灵活度高于 Cube
  （如支持数学中的求倒数、求平方根等）。
- **别名**：Vector 单元、矢量计算单元

### Scalar

- **定义**：AI Core 上的标量计算单元，主要负责标量数据运算和对其他单元（如 MTE 数据搬运单元、
  Vector 矢量计算单元、Cube 矩阵计算单元）的指令发射。
- **别名**：Scalar 单元、标量计算单元、标量单元

### Cube Core

- **定义**：矩阵计算核，专注于矩阵计算。由 Scalar 调度单元、矩阵计算单元、搬运单元等组成，
  不包括矢量计算单元。
- **别名**：矩阵计算核、Cube 核

### Vector Core

- **定义**：矢量计算核，专注于矢量计算，由 Scalar 调度单元、矢量计算单元、搬运单元等组成，
  不包括矩阵计算单元。
- **别名**：矢量计算核、Vector 核

### AIC / AIV

- **定义**：在 AI Core 分离模式下，一组 Cube Core 和 Vector Core 组合中的 Cube Core 记作 AIC，
  其中的 Vector Core 记作 AIV。
- **别名**：AIC（Cube Core）、AIV（Vector Core）

### Fixpipe

- **定义**：AI Core 中负责将矩阵计算结果从 L0C Buffer 搬运到 Global Memory 或 L1 Buffer 的单元，
  搬运过程中随路完成量化、激活等操作。
- **别名**：FIX、固定搬出单元

### MTE1 / MTE2 / MTE3

- **定义**：Memory Transfer Engine，AI Core 的数据传递引擎。MTE1 负责把数据从 L1 Buffer 搬运到
  L0A Buffer 或 L0B Buffer 等；MTE2 负责把数据从 GM 搬运到 L1 Buffer、L0A Buffer、L0B Buffer、
  UB 等；MTE3 负责把数据从 UB 搬运到 Global Memory、L1 Buffer，以及从 L1 Buffer 搬运到
  Global Memory 等。
- **别名**：搬运单元、DMA 单元、MTE
- **边界**：源文件对三个引擎都注明"**不同硬件能力可能有差异**"，因此上述分工是术语定义，不是跨平台
  的搬运路径承诺。

## 编程阶段

### CopyIn / Compute / CopyOut

- **定义**：Ascend C 算子编程范式中典型的三个阶段。CopyIn 负责将待计算数据从 Global Memory 搬运到
  Local Memory；Compute 负责完成计算任务；CopyOut 负责将计算结果从 Local Memory 搬运到
  Global Memory。
- **别名**：搬入 / 计算 / 搬出；三段式编程范式

## 边界：物理存储与 TPosition 逻辑位置

- **TPosition**：Ascend C 管理不同层级的物理内存时，用抽象的逻辑位置（TPosition）来表达各级别
  存储，代替片上物理存储的概念，达到隐藏硬件架构的目的。其类型包括 VECIN、VECOUT、VECCALC、
  A1、A2、B1、B2、CO1、CO2 等，其中 VECIN、VECCALC、VECOUT 主要用于矢量编程，A1、A2、B1、B2、
  CO1、CO2 用于矩阵编程。
- 逻辑位置与物理存储**不是一对一**：例如 A1 与 B1 的物理存储都对应 L1 Buffer，VECIN、VECOUT、
  VECCALC 的物理存储都对应 UB。因此术语表中"在哪块存储上"的问题要区分问的是 TPosition 还是
  物理 Buffer。
- **同名陷阱**：本表中的 `A2`、`B2`、`CO2` 是 TPosition 的逻辑位置名，与产品平台取值 `a2`（Atlas A2
  系列）**无关**；`A2` 逻辑位置对应的是 L0A Buffer。检索时不要按平台含义理解。

## 与相邻卡的分工

- [NPU 内存层次与数据通路模型](../platforms/concepts/npu_memory_model.md)：给出的是**定量模型**
  （各存储层次的容量与对齐约束、MTE/FIX 流水映射、Cube 与 Vector 两条数据通路），并显式标注平台。
  本卡只回答"这个词是什么意思、还叫什么"，不带容量、对齐与流水线数值；需要判断某平台放不放得下、
  对齐要多少字节时用那张卡。
