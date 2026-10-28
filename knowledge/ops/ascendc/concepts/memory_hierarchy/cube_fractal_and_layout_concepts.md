---
type: "Concept"
title: "Cube 分形（Fractal）与 ZN/NZ 布局概念"
description: "Cube 分形把按数据位宽确定形状的计算块连续存放（half 输入常为 16×16）；Zz 输入产品组采用 Zz × Zn = Nz，Ascend 950PR/950DT 采用 Nz × Zn = Nz。区分 512B 输入/L1 分形与固定 16×16、1024B 的 L0C 结果分形，并说明各 dtype 轴块、padding 与转换通路边界。"
tags:
- "task.design"
- "topic.memory"
- "topic.alignment"
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/technical_appendix/concepts_and_terms/neural_networks_and_operators/data_layout.md
  role: primary
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_fractal_intro/key_fractal_format_details.md
  role: primary
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_fractal_intro/background_and_core_concepts.md
  role: supporting
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/tensor_api/matrix_compute/cube_compute_load/overall_description.md
  role: supporting
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/tensor_api/matrix_compute/cube_compute_load/copy_l1_to_l0a.md
  role: supporting
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/tensor_api/matrix_compute/cube_compute_load/copy_l1_to_l0b.md
  role: supporting
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/tensor_api/matrix_compute/cube_compute_store/overall_description.md
  role: supporting
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/tensor_api/matrix_compute/mmad_compute/mmad.md
  role: supporting
created_at: '2026-10-23T02:00:00Z'
updated_at: '2026-10-26T02:54:00Z'
platforms:
- '950'
- a2
- a3
- 310p
- '910'
- kirin_x90
- kirin_9030
---

# Cube 分形（Fractal）与 ZN/NZ 布局概念

## 定义

- **数据排布格式**（Data Layout Format）是对多维 Tensor 在内存中存储方式的描述：ND/NHWC/NCHW 等普通格式为 Tensor 的轴赋予业务语义并决定哪个方向连续；NZ、Zz、Zn 等私有格式则是为满足 AI Core 中 Cube 计算单元的高性能计算需求而引入的布局。
- **分形（Fractal Matrix）**：Cube 计算单元采用分块计算逻辑（例如并行处理 16×16 的矩阵分片），分形格式通过软件层重排，使**每个对应位宽的分形块（half 输入常为 16×16）在物理内存中连续存放**，减少非连续访问；L0C 结果分形另见下表。
- **命名法"大Y小x"**：大 Y（Z/N）表示**分形之间**的排列顺序（Z = row major 行主序，N = column major 列主序）；小 x（z/n）表示**分形内部元素**的排列顺序。

三种关键格式按"大+小"展开：

| 格式 | 含义 | 分形形状 | 典型物理位置 |
|---|---|---|---|
| **Zz**（FRACTAL_ZZ） | 大 Z + 小 z，分形内外都按行主序 | 16 × (32B / sizeof(T))，512B | L0A Buffer（左矩阵，Zz 输入产品组） |
| **Zn**（FRACTAL_ZN） | 大 Z + 小 n，分形间行主序、分形内列主序 | K0 × N0，其中 K0 = 32B / sizeof(T)、N0 = 16，512B | L0B Buffer（右矩阵）；也用于 L1 Buffer / GM 保存离线处理好的右乘矩阵 |
| **Nz**（FRACTAL_NZ） | 大 N + 小 z，分形间列主序、分形内行主序 | L0C：固定 **16×16**（256 元素）<br>L1/GM：16 × (32B / sizeof(T))，512B<br>L0A（仅 950）：16 × (32B / sizeof(T)) | L0C Buffer（结果）；L1 Buffer / GM（通用中间格式）；950 的 L0A Buffer（左矩阵） |

分形形状由**数据类型位宽**决定，输入分形及 L1/GM 流转分形为 512B；L0C 结果分形不在此断言内：

- Zz 与 L1/GM 中的 Nz 为 `16 × K0`（K0 = 32B / sizeof(T)）：b32 → 16×8；b16 → 16×16；b8 → 16×32；b4 → 16×64。
- Zn 为 `K0 × N0`（K0 同上、N0 = 16）：b32 → 8×16；b16 → 16×16；b8 → 32×16；b4 → 64×16。

三种格式的转换都可写成"pad → reshape → transpose"三步，例如：

```text
Nz: (…, B, M, N) -> pad -> (…, B, M1*M0, N1*N0) -> reshape -> (…, B, M1, M0, N1, N0) -> transpose -> (…, B, N1, M1, M0, N0)
Zz: (…, B, M, K) -> pad -> (…, B, M1*M0, K1*K0) -> reshape -> (…, B, M1, M0, K1, K0) -> transpose -> (…, B, M1, K1, M0, K0)
Zn: (…, B, K, N) -> pad -> (…, B, K1*K0, N1*N0) -> reshape -> (…, B, K1, K0, N1, N0) -> transpose -> (…, B, K1, N1, N0, K0)
```

三者差别只在最后一步 transpose 的维度顺序：Nz 把 N 维提到分形之外，Zz 保持分形间行主序，Zn 让分形内部变成列主序。

## 为什么需要分形（成因）

- **连续读取**：以 half 的 16×16 输入矩形块为例，在线性布局中可能需访问不连续的多个地址逐行"收集"；分形将对应 dtype 的输入块连续化，减少多地址寻址开销。
- **读向匹配决定 Zz 与 Zn**：A 矩阵在 A×B 中被"横向扫描"，Zz 在微观上按行存储，使 A 的同一行相邻元素物理连续，Cube 左侧通道可连续（无跨步）读取；B 矩阵需要按列取用，若用普通行主序布局，同一列元素相隔整行、地址跳跃，因此 Zn 在分形内部强制按列存储，使逻辑上的一列在 L0B 中排在一起。
- **Nz 是中间标准格式**：它是对"线性数据（ND）"与"计算专用数据（Zz/Zn）"的折中，作为 L1/GM 的通用流转格式，便于在搬到 L0A/L0B 时转成对应格式；大 N 排布也便于多核并行与后续按通道维处理的算子。

## 矩阵乘法的格式组合：按产品分两族

| 产品族 | 组合 | 说明 |
|---|---|---|
| Zz 输入产品组：Atlas A2、Atlas A3、Atlas 200I/500 A2 推理产品、Atlas 推理系列、Atlas 训练系列、Kirin X90 / Kirin 9030 | **Zz × Zn = Nz** | A 在 L0A 为 Zz，B 在 L0B 为 Zn，C 在 L0C 为 Nz |
| Ascend 950PR/950DT（3510） | **Nz × Zn = Nz** | A 在 L0A 为 Nz，B 为 Zn，C 为 Nz |

可判定的结论：**B 侧恒为 Zn、C 侧恒为 Nz，跨族变化的是 A 侧（Zz ↔ Nz）**。因此把某一族的分形布局硬编码进手写 mmad 路径，换族运行时会得到错误结果——这类静默错算的实例见相邻卡。

另一个直接后果：分形物理占用按各轴块大小向上取整：half 输入常为 16×16，其他位宽按上表的 K0 计算，不能一概按 16 补齐。padding 的填充值及是否参与实际计算仍由接口有效尺寸与算法决定。

## 布局转换发生的位置与代价

**位置 1：GM → L1（搬入随路）**
以 950 的搬入通路为例，GM→L1 可随路完成 ND2ND、ND2NZ、ND2ZN、DN2NZ、DN2ZN、NZ2NZ、ZN2ZN 等组合；MX 缩放系数走独立的系数通路（ScaleND2ZZ、ScaleDN2ZZ、ZZ2ZZ、ScaleND2NN、ScaleDN2NN、NN2NN）。普通矩阵源地址 1B 对齐、目的 32B 对齐；系数接口的最小分形为 32B，不能把该单位套用于 A/B 数据搬运。

**位置 2：L1 → L0A/L0B（普通数据以 512B 分形为单位）**
以 950 的 Tensor API 通路为例，格式组合是**枚举**的，不能任意转换：

- L0A：非转置 `Nz -> Nz`；转置 `Zn -> Nz`；Img2Col `NC1HWC0 -> Nz` 或 `NDC1HWC0 -> Nz`（卷积特征图在搬运中展开为矩阵）。
- L0B：非转置 `Zn -> Zn`；转置 `Nz -> Zn`。
- 两侧的分形矩阵形态按位宽固定：L0A 侧 b4 `16*64`、b8 `16*32`、b16 `16*16`、b32 `16*8`；L0B 侧 b4 `64*16`、b8 `32*16`、b16 `16*16`、b32 `8*16`。
- 源地址 32B 对齐、目的地址（L0A/L0B）512B 对齐。

**位置 3：L0C 搬出**
950 的 L0C→GM 与 L0C→UB 支持 NZ2ND、NZ2DN、NZ2NZ 三类转换；L0C 搬出的源地址 64B 对齐，目的 GM 1B/32B、目的 UB 32B。**从 L0C 搬到 L1 时分形大小可能变化**：L0C 的 Nz 分形固定 16×16，而 L1 的 Nz 分形是 16 × (32B / sizeof(T))。

**代价与约束（可判定的部分）**

- 转换能力绑定在搬运通路上（"随路"），因此受**通路 × 格式组合**枚举限制，不是任意两种布局都能互转。
- 维度需按对应 dtype 的分形各轴大小补齐并占用物理空间；有效尺寸、padding 值与计算覆盖范围必须另行确认。
- Batch 模式下源/目的 Layout 在分形 Layout 前增加 Batch 维，**Batch 维 stride 必须等于单 Batch layout 的 `capacity()`**（按字节：stride × sizeof(T) = 单 Batch 数据的物理占用字节数），Batch 数量必须一致——否则数据错位。
- 转置类转换改变分形内排布（且可能改变分形间排布），因此与搬运指令选型和数据类型位宽绑定，不能跨位宽直接套用。

## 适用与不适用

- **适用**：任何经 Cube（mmad / 矩阵乘）的计算；A、B、C 必须按目标产品族的分形格式准备，布局是计算的**前置条件**而不是优化项。
- **不适用**：Vector 通路（GM↔UB）不涉及这些分形；普通 ND/NHWC/NCHW 格式的轴语义不属于本卡，见[数据排布格式](../../guides/technical_appendix/concepts_and_terms/neural_networks_and_operators/data_layout.md)。
- **DSL 边界**：Triton/HIVM IR 用 `DataLayout` 枚举与 `DataLayoutAttr`（transpose、fractalSizes 等）以及 `nd2nz`/`nz2nd` 操作表达同一硬件约束；那是另一套 DSL/IR 层的抽象，**只作对照，不作为本卡事实来源**。
- **API 族边界**：本卡引用的通路与格式组合按 950 的 Tensor API 文档给出（`copy` 系列为 950 支持、其他产品不支持），不能直接套到 2201 的接口族上。

## 相邻卡分工

- [l1_l0_storage_structure_and_data_paths](./l1_l0_storage_structure_and_data_paths.md)：同目录卡，讲 Cube 侧 L1/L0A/L0B/L0C 的 Bank 结构、谁能写谁、搬运粒度与随路操作位置；本卡讲"格式定义、为什么需要分形、转换发生在哪一步"。
- [data_layout](../../../triton/apis/ir/architecture/data_layout.md)：Triton/HIVM IR 的布局体系（DataLayout 枚举、DataLayoutAttr、nd2nz/nz2nd 转换操作、fixpipe dma_mode）。仅作跨 DSL 对照链接。
- [cube_manual_mmad_crossgen_001](../../runbooks/precision/cube_manual_mmad_crossgen_001.md)：把 2201 的分形布局硬编码进手写 cube 路径、在 A5 上静默错算的实例与修复路线。本卡解释"为什么跨族会错"（A 侧 Zz ↔ Nz），该卡给现象、判据与修复。
- [data_layout](../../guides/technical_appendix/concepts_and_terms/neural_networks_and_operators/data_layout.md)（镜像卡）与 [key_fractal_format_details](../../apis/simd_api/basic_api/cube_compute_isasi/cube_compute_fractal_intro/key_fractal_format_details.md)（镜像卡）：对应来源文档的原文镜像，用于查完整公式与图示；本卡做蒸馏与产品族判定。
- [nd_nz_transform_and_block_placement](../../guides/data_movement/nd_nz_transform_and_block_placement.md)：ND/NZ 随路变换的参数意图与分块写回公式；本卡给格式定义与产品族差异，不展开具体参数换算。
- [tensor_layout_and_copy_specialization](../../guides/blaze/tensor_layout_and_copy_specialization.md)：Tensor API 中 Layout 可表示的形状/步长与实际 Copy 实现消费字段的边界。

## 失效边界

- 分形组合按产品族给出：来源明确枚举了 Zz 输入产品组的产品与 950；**未列出的产品不要外推**本卡结论。
- 各产品族的 API 通路与支持格式并不相同（本卡引用的 Tensor API 搬入/搬出通路是 950 专属），跨族替换前必须核对目标族的接口与格式组合。
- 分形大小取决于数据类型位宽；本卡给出的 512B 是 Zz/Zn 以及 L1/GM 中 Nz 的形态，L0C 的 Nz 固定为 16×16（一个结果分形 1024B），两者不是同一个单位。
- 本卡不承诺布局转换的开销数值（不给出实测/理论耗时），只给出"转换发生的位置与组合限制"这类可判定事实。
