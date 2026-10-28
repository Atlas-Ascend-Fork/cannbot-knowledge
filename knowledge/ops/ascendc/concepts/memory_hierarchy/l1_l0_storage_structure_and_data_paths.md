---
type: "Concept"
title: "Cube 侧 L1/L0A/L0B/L0C 的存储结构与数据通路"
description: "Cube 侧 L1/L0A/L0B/L0C 的结构与通路边界：L1/L0A/L0B 结构按来源示例描述，L0C 区分 2201（128KB）与 3510（256KB）；普通输入分形为 512B，L0C 结果分形为固定 16×16、1024B，并说明 GM/L1/L0、Fixpipe 与 MX 系数通路。"
tags:
- "task.design"
- "topic.memory"
- "topic.data_movement"
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_datamove/cube_compute_load/L1_L0A_B_memory_structure_intro.md
  role: primary
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_datamove/cube_compute_store/L0C_memory_structure_intro.md
  role: primary
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_datamove/cube_compute_load/cube_compute_load_overall_description.md
  role: supporting
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_datamove/cube_compute_load/cube_compute_input_move_constraint.md
  role: supporting
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_datamove/cube_compute_store/cube_compute_store_overall_description.md
  role: supporting
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_datamove/cube_store_key_features/accompanying_quantization.md
  role: supporting
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_datamove/cube_store_key_features/accompanying_relu.md
  role: supporting
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_datamove/cube_store_key_features/NZ2ND.md
  role: supporting
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_datamove/cube_store_key_features/L0C_to_UB_dual_target_mode.md
  role: supporting
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_datamove/cube_compute_store/asc_copy_l12ub.md
  role: constraint
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_datamove/cube_compute_store/asc_copy_l12gm.md
  role: constraint
created_at: '2026-10-23T02:00:00Z'
updated_at: '2026-10-26T02:54:00Z'
platforms:
- '950'
- a2
- a3
---

# Cube 侧 L1/L0A/L0B/L0C 的存储结构与数据通路

## 定位与边界

本卡只回答 Cube 侧四个片上 Buffer 的四个问题：**结构（Bank 划分与地址编码）、读写方（谁能写谁）、搬运粒度与对齐、随路操作在哪一段发生**。Global Memory、Unified Buffer、BiasTable、Fixpipe Buffer 只作为通路端点出现。L1/L0A/L0B 的结构页未声明产品范围；L0C 容量分别以 A2/A3（2201）及 950PR/950DT（3510）为例，不能据此推断其他产品。NPU 全局存储层次、容量与对齐总表、MTE/FIX 通路与 Triton 映射见相邻卡（见文末分工）。

## 结构：Bank 组织与并发规则

| Buffer | 容量 | Bank 组织 | 地址编码 | 并发规则 |
|---|---|---|---|---|
| L1 Buffer | 512KB | 16 Bank × 32KB；每 Bank 1024 行 × 32B；16 Bank 组成 8 个 Bank Group（每 BG 2 Bank） | 19 位：`{BANK[0:0], BANK_DEPTH[9:0], BG[2:0], BANK_WIDTH[4:0]}` | 同一 Bank 最多同时允许一读或一写；同 BG 的两个 Bank 支持一个读、另一个写，不支持同时读或同时写 |
| L0A Buffer | 64KB | 仅 1 个 Bank；128 行 × 512B | 16 位：`{BANK_DEPTH[6:0], BANK_WIDTH[8:0]}` | 不允许同时读写同一地址；允许矩阵搬入写入与 `asc_mmad` 读取同一 Bank 的不同地址 |
| L0B Buffer | 64KB | 同 L0A | 同 L0A | 同 L0A |
| L0C Buffer | 2201：128KB<br>3510：256KB | 16 Bank（2201：每 Bank 8KB / 128 行 × 64B；3510：每 Bank 16KB / 256 行 × 64B）；16 个 Bank Group，每 BG 1 个 Bank | 2201 为 17 位、3510 为 18 位：`{BANK_DEPTH, BANK[3:0], BANK_WIDTH[5:0]}` | 以 `__cc__ float*` / `__cc__ int32_t*` 存放累加结果 |

读法：Bank 结构给的是**并发边界**（哪些读写可以重叠），不是容量问题——L1 的瓶颈是"同 Bank 串行 / 同 BG 一读一写"，L0A/L0B 的边界是"同址不可同时读写，异址可以"。

L0C 的三个单位不要混淆：

- 一个 16×16 结果分形占 **1024B**；
- 搬出起始地址按 **64B** 对齐；Nz2ND 的 `src_stride` 在特性页按 `C0_Size = 16 × sizeof(L0C_element)` 计数，不能把 L0A/L0B 的 512B 输入分形当作步长单位。来源的结构页虽将 `src_stride` 写为 64B，具体参数仍应以目标接口及架构文档核对；
- UnitFlag 以 **512B** 块管理读写状态，一个完整的 1024B 结果分形涉及两个标志块。Bank 结构、结果分形、UnitFlag 块是三个不同概念。

## 谁能写谁：Cube 侧通路与分工

| 通路 | 接口/机制 | 关键约束 | 架构 |
|---|---|---|---|
| GM → L1 | `asc_copy_gm2l1` 系列（连续/高维切分、2D 分形；950 另有 `_dn2nz`、`_align`、2D、高维切分等） | 源 1B 对齐，目的 32B 对齐；可随路做 ND→Nz 转换 | 按产品与接口核对 |
| GM → L0A/L0B | `asc_copy_gm2l0a` / `asc_copy_gm2l0b` | 目的 512B 对齐 | **仅 2201**；950 因硬件变更删除该通路，须拆成 GM→L1 与 L1→L0A/L0B 两步 |
| UB → L1 | `asc_copy_ub2l1`（连续重载 / 高维切分重载） | 按 32B 块配置长度和间隔 | 仅 950 |
| L1 → L0A/L0B | `asc_copy_l12l0a` / `asc_copy_l12l0b`（2D、3D）、`*_trans`（块转置；3510 的 2DV2 转置使用 `*_transpose`，不能混淆） | 源 32B、目的 512B 对齐；普通数据以 512B 分形为单位；3D 重载用于 NC1HWC0 的 image-to-column | 按产品与重载核对；3510 另有 2D/MX 扩展 |
| L1 → BiasTable | `asc_copy_l12bt` | 目的 64B 对齐；提供矩阵计算的偏置/累加初值 | 按产品与接口核对 |
| L1 → Fixpipe Buffer | `asc_copy_l12fb` | 目的 128B 对齐；搬运量化/激活参数 | 按产品与接口核对 |
| L1 → L0C | `asc_copy_l12l0c` | L0C 初值搬运 | 按接口产品支持核对 |
| L0A + L0B（+ BiasTable）→ L0C | `asc_mmad` | 矩阵乘加写入结果矩阵 | 按接口产品支持核对 |
| L0C → GM | `asc_copy_l0c2gm`（2201/3510 两套原型） | 源 64B 对齐；承载随路量化/ReLU/格式转换/通道处理 | A2/A3、950，按原型核对 |
| L0C → L1 | `asc_copy_l0c2l1` | 搬出后分形大小可能变化 | 按接口产品支持核对 |
| L0C → UB | `asc_copy_l0c2ub` | 支持双目标模式（见下） | 仅 950 |
| L1 → GM / L1 → UB | `asc_copy_l12gm`（PIPE_MTE3）/ `asc_copy_l12ub`（PIPE_MTE1） | 均以 32B 为数据块长度单位；`asc_copy_l12ub` 源/目的地址都需 32B 对齐、仅在 AIC 上执行有效（非 AIC 调用直接返回），并通过 `sub_blockid` 选择目的 Vector Core | 分别仅 2201 / 仅 950 |
| 初始化写入 | `asc_fill_l1` / `asc_fill_l0a` / `asc_fill_l0b` | 初始化 L1、L0A、L0B | 见各接口产品支持 |

通路随架构增减是本表的重点：**950 删除 GM→L0A/L0B，需拆成 GM→L1 与 L1→L0A/L0B；L0C→UB、UB→L1、L1→UB 等接口仍须按具体产品原型核对**。跨代复用代码时先按通路核对，不要假定接口在两端都存在。

## 粒度与对齐：可判定的最小单位

- 矩阵搬运（L1→L0A/L0B）的普通数据分形以 **512B** 为单位；3510 的 `asc_copy_l12l0a_mx` / `asc_copy_l12l0b_mx` 仅搬 **32B E8M0 系数分形**，A/B 数据仍需另用 2D 接口搬入，不能将 32B 外推为普通数据重载单位。
- 对齐：源地址位于 L1 时 32B、位于 GM 时 1B；目的地址位于 L0A/L0B 时 512B、位于 L1 时 32B、BiasTable 64B、Fixpipe Buffer 128B；L0C 搬出源地址 64B。
- L0C 的 Nz2ND 面向用户可配参数**单位不统一**：`m_size`/`n_size` 为元素维数，`src_stride` 以 `C0_Size` 计（`C0_Size = 16 × sizeof(L0C_element)`），`dst_stride` 以元素计。`src_matrix_stride_64b` 的命名单位与不同架构接口参数需分别核对。不能把 2201 与 3510 的参数单位直接互换。
- 稀疏搬运为 2201 专属：`asc_copy_l12l0b_sparse` 以 512B 为单位搬压缩权重矩阵到 L0B Buffer，同时以 128B 为单位把索引矩阵搬到内置专用 buffer 空间（供 `asc_mmad_sparse` 读取），两者都需按 Zn 格式排布。

## 随路操作发生在哪一段

1. **GM→L1**：随路 ND→Nz 转换（950 另有 DN→Nz）。不使能转换时**不改变**分形间与分形内排布（如 Nz→Nz、Zn→Zn）；使能时一定会改变分形排布。
2. **L1→L0A/L0B**：转置搬运一定改变分形内排布，可按需改变分形间排布；2201 的 2D 转置重载仅支持 b16，b32 的块转置还要求 L1 上满足 Nz（Row==16）或 Zn（Col==16）才能把两个连续 16×8 分形合并成 16×16 方块再转置。
3. **L0C 搬出（Fixpipe 通路）**：随路量化、随路 ReLU、随路格式转换（Nz2ND、Nz2DN）、随路通道拆分（Channel Split）/通道合并（Channel Merge）；950 的 L0C→UB 还支持双目标模式。
4. **参数来源**：Bias 经 L1→BiasTable 搬入；量化/激活参数经 L1→Fixpipe Buffer 搬入（`asc_copy_l12fb`）；Scalar 量化参数也可由 QUANT_PRE 寄存器提供。量化区与激活区**独立寻址**：Vector 量化的 `quant_pre_addr` 是参数区起始字节地址除以 128，激活参数地址索引以 64B 为单位，两者都不能直接传元素下标。

## 适用与不适用（约束清单）

- **Nz2ND 与通道拆分/合并互斥**：开启 Channel Split/Channel Merge（Nz2Nz）时 Nz2ND 不可用；目的操作数地址之间不能重叠。
- **双目标模式（仅 950、仅 L0C→UB）**：只支持普通 Nz2Nz 或 Nz2ND 场景，不支持随路功能；按 M 拆分要求 M 为 2 的倍数，按 N 拆分要求 N 为 32 的倍数；拆分后的行数不是源 `m_size`（源 `m_size` 仍传完整矩阵的 M）。
- **量化参数约束**：量化参数不能为 inf、nan 或非规格化数；缩放系数只按 QUANT_PRE 的有效位参与计算，**不保留完整 FP32 尾数精度**，输出仍为 float 的量化模式同样受影响；Vector 量化参数按原始 C 矩阵的 N 维列索引对应，分块搬出时要同步检查参数区偏移、列数、对齐与占用范围；MX 量化系数则通过 950 的独立 32B E8M0 系数搬运接口与 A/B 数据映射，不能混同为 Fixpipe 的通用参数单位；不同搬出任务需要不同系数时，应在对应搬出执行前重新配置。
- **参数先行**：随路能力要先配好参数与地址，并按依赖关系完成核内同步，再调用 L0C 搬出接口并在参数中选择对应模式。

## 与其他概念的边界

- 本卡的 512B 是 **L1→L0A/L0B 的普通输入分形单位**；L0C 侧的 64B 地址对齐和 1024B 结果分形不可与其混用，步长以具体接口参数定义为准。
- Vector 侧通路（GM↔UB）不在本卡展开；UB 只作为 L0C→UB（950）与 L1→UB（950）的端点出现。
- "谁能写谁"是通路能力，不包含同步要求：通路存在不等于可以直接连发，跨 Buffer 复用还要按生产-消费关系补同步。

## 相邻卡分工

- [npu_memory_model](../../../../common/platforms/concepts/npu_memory_model.md)：Ascend NPU 全局存储层次与数据通路模型（含容量/对齐总表、MTE/FIX 通路、`tl.load`/`tl.store`/`tl.dot` 的硬件映射）。本卡是 Cube 侧四 Buffer 的结构、读写方、粒度与随路位置细节。
- [load_data_2_d_bit_mode](../../apis/simd_api/basic_api/cube_compute_isasi/cube_compute_load/load_data_2_d_bit_mode.md)：LoadData（BitMode 2D）单接口的参数与约束（512B 分形、L1→L0A/L0B）。本卡只到"通路与粒度"层，不展开单接口参数。
- [l1_l0_a_b_memory_structure_intro](../../apis/simd_api/c_api/cube_datamove/cube_compute_load/l1_l0_a_b_memory_structure_intro.md) 与 [l0_c_memory_structure_intro](../../apis/simd_api/c_api/cube_datamove/cube_compute_store/l0_c_memory_structure_intro.md)：对应来源文档的原文镜像卡，用于查原始措辞与地址位段；本卡做的是跨文件的蒸馏与判定。
- [memory_hierarchy](../../../triton/apis/ir/architecture/memory_hierarchy.md)：Triton/HIVM IR 层的同类描述（AddressSpace 枚举、源-目标到 Pipeline 的映射）。它与本卡处于不同 DSL/IR 层，仅作对照，不作为本卡事实来源。
- [cube_fractal_and_layout_concepts](./cube_fractal_and_layout_concepts.md)：同目录的分形与 ZN/NZ 布局概念卡。本卡讲"Buffer 结构与通路"，该卡讲"格式定义、为什么需要分形、格式转换发生在哪一步"。

## 失效边界

- L1/L0A/L0B 的结构介绍未声明产品范围，只作为来源描述的结构示例，不据此推定全部产品通用；L0C 的容量与 Bank 行数按 2201/3510 两族分别给出，不要跨族套用地址位宽。
- 本卡给的是 Buffer 的物理容量；**用户可用容量可能更小**——例如 UB 需先扣除预留空间（`asc_copy_l12ub` 的约束说明给出了 UB 总容量、预留项与 SIMD+SIMT 混编时再划分 Data Cache 后的可用值），L1 侧则要求源偏移量与搬运大小之和不超过 512KB，否则触发读溢出异常。实际可用量需按具体接口与编程场景确认。
- 上表通路归属按来源中的产品支持说明归纳；具体接口的支持矩阵以其单接口文档为准。
