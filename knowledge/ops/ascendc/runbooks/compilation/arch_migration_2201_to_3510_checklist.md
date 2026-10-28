---
type: Runbook
title: 2201→3510 架构迁移检查清单
description: 把 2201 上跑通的 Ascend C 算子迁到 3510（Ascend 950PR&950DT）时的逐项检查清单：API 兼容策略分层、编译入口与编译选项、被删除的基础 API 通路、L0A 分形与 UB/对齐、Subnormal 精度行为、高阶 API 算子族差异、同步与缓存约束；每项给出「怎么判断」与「不合规怎么改」。
tags:
- task.migration
- task.implementation
- topic.architecture
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/cross_gen_migration_guide/3510_arch_migration/2201_to_3510_arch_changes.md
  role: primary
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/cross_gen_migration_guide/3510_arch_migration/2201_to_3510_guide/basic_api_migration.md
  role: supporting
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/cross_gen_migration_guide/3510_arch_migration/2201_to_3510_guide/advanced_api_migration.md
  role: supporting
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/cross_gen_migration_guide/3510_arch_migration/2201_to_3510_guide/op_compilation_migration.md
  role: supporting
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/cross_gen_migration_guide/ascend_c_api_compatibility.md
  role: supporting
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/cross_gen_migration_guide/instructions_for_new_features/3510_new_features.md
  role: supporting
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/hardware_implementation/hardware_constraints/npu_arch_3510.md
  role: supporting
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/compilation_and_execution/operator_compilation/ai_core_operator_compilation.md
  role: supporting
created_at: '2026-10-23T02:00:00Z'
updated_at: '2026-10-28T02:11:00Z'
platforms:
- '950'
---

# 2201→3510 架构迁移检查清单

## 适用场景

- **任务**：把在 NPU 架构版本 2201 上跑通的 Ascend C 算子迁到 3510 上运行。来源的前提是：2201 上开发的程序要在 3510 上**重新编译**并运行，且可能需要按迁移指导调整代码——所以本卡按「重编译 + 逐项核对」组织，不承诺二进制兼容。
- **平台范围**：3510 对应的产品型号是 Ascend 950PR&950DT 系列。2201 及其它架构版本的平台不在本卡范围。
- **适用粒度**：算子族 + 构建工程级（基础 API 与高阶 API 的调用点，以及编译选项/宏开关）。
- **不适用**：把 2201 代码原样在 3510 编译通过当作"迁移完成"；SIMT 与 SIMD-SIMT 混编新编程模型自身的写法迁移也不在本卡。

## 与相邻卡的分工

- 本卡是**清单**（每项 = 怎么判断 → 不合规怎么改）。来源是 asc-devkit 的 3510 架构迁移指导、3510 硬件约束与 3510 新特性说明。
- 具体算子的端到端案例不在本卡：[Gather 双线性插值 kernel — DAV_3510 编译级配方](gather_resize_bilinear_dav3510_recipe.md)（编译级验证、精度未上板）与 [TopK 高阶 API 在 DAV_3510 编译可用（产品表未列）](topk_highlevel_api_dav3510_compile_verified.md)（文档支持矩阵未列时的编译级放行判据）。
- 构建系统层面的 arch 隔离失败见 [CMake arch 子目录隔离 dav-3510 专属 API](cmake_arch_dav_3510_api.md)；本卡只在检查项 1 引用它作为编译失败时的处置方向。
- 分层迁移档位（L1 零改动注册 / L2 同构适配）见 [L1/L2 迁移实施详细指南](../../guides/cross_gen_migration_guide/l1_l2_implementation.md)：那张卡决定**走哪一档**，本卡核对**代码里还有哪些点必须改**。
- 架构号与宏的核对链见 [Ascend arch 变体查证链路 SoC→ini→NpuArch→dispatcher](arch_variant_lookup_chain_soc_ini_npuarch_dispatcher.md) 与 [`__NPU_ARCH__` numeric macros](ol_142_npu_arch_numeric_macros_a5_3510_v220_bf16_guards_3.md)。
- 精度行为在本卡只占检查项 5；"硬件单指令路径 vs 软件实现路径"的精度差异判据见 [Reg 矢量接口硬件精度与软仿精度差异](../precision/reg_vector_hardware_vs_soft_simulation_precision.md)。

## 检查项 0：先定 API 兼容策略

**怎么判断**：按来源的兼容性策略给每个 API 分层，别整层外推：

| API 层 | 3510 兼容策略 |
|---|---|
| 高阶 API | 同领域内保证兼容；特定领域扩展特性不保证兼容 |
| 基础 API | "可兼容的基础 API"在所有架构上兼容；ISASI（体系结构相关）API 不保证跨架构兼容，来源点名 CUBE 侧 LoadData、Mmad 等 |
| 语言扩展层 C API | SIMD 的 C API 目前仅支持体系结构相关，暂未支持跨代兼容 |
| 编译器 BuiltIn API | 不保证兼容 |

**不合规怎么改**：把 ISASI、SIMD C API、BuiltIn 三层标成"必须逐调用点核对或替换"；可兼容基础 API 与同领域高阶 API 只需核对参数与数据类型（检查项 3、6）。

## 检查项 1：编译入口（架构号 / AI 处理器型号）

**怎么判断**：

- 命令行/CMake 异构编译：编译命令或 CMakeLists.txt 里是否有 `--npu-arch=dav-3510`（来源示例：`target_compile_options(demo PRIVATE $<$<COMPILE_LANGUAGE:ASC>:--npu-arch=dav-xxxx>)`）。用 Ascend C 的 CMake 封装时，架构由 `CMAKE_ASC_ARCHITECTURES` 控制（默认 `dav-2201`），需覆盖为 `-DCMAKE_ASC_ARCHITECTURES=dav-3510`，NPU 运行模式下 CMake 会自动把它注入成 `--npu-arch=<value>`。`--npu-arch` 是架构迁移的明确目标；不要只改 Host 侧字符串。若工程还使用 `--npu-soc` 或算子包配置，需同时核对实际生成的 Device 编译命令和 `AddConfig` 注册项。
- msOpGen 生成的标准自定义算子工程：编译配置项在工程目录 `CMakePresets.json` 的 `ASCEND_COMPUTE_UNIT` 字段；算子原型定义里要用 `AddConfig` 注册支持的 AI 处理器型号（`AddConfig(const char *soc)` 或 `AddConfig(const char *soc, OpAICoreConfig &aicore_config)`）。

**不合规怎么改**：把架构号改为 3510 对应值；`AddConfig` 的 soc 字符串按 `CMakePresets.json` 的 `ASCEND_COMPUTE_UNIT` 取值填写，不要自造。写 `--npu-arch` 时保持小写 `dav-` 形式（同仓 [bisheng 拒绝大写 --npu-arch=DAV2201 须用小写 dav](bisheng_npu_arch_requires_lowercase_dav_2201.md) 是 arch 名写法被编译器拒绝的案例，该案例在 a2 上观测）。

**验证**：检查编译命令（或 CMake 缓存）里 arch 确实生效；若报错是"找不到 dav-3510 专属 API 符号"，按 [CMake arch 子目录隔离](cmake_arch_dav_3510_api.md) 的思路先确认失败来自哪个目录的源文件，而不是继续改目标算子的 arch 代码。

## 检查项 2：编译选项与内置宏开关

**怎么判断**：逐项确认是否显式配置，不要依赖默认值。

| 选项/宏 | 语义与判定要点 |
|---|---|
| `--cce-ftz`（默认 `true`） | 对未显式传入 config 的部分基础 API 和高阶 API 控制非规格化数处理：`true` = FTZ，`false` = 保留 Subnormal（精度更高、性能可能下降）。SIMD 与 SIMT 都支持，**其中 SIMD 仅支持 3510**；仅 950PR&950DT 支持该选项；有 config 的接口应优先核对对应的 `FTZ_FALSE`/算法配置 |
| `ENABLE_CV_COMM_VIA_SSBUF`（默认关闭） | 控制 SSBuffer 与 UB→L1 硬通道。从其它平台移植过来的算子默认关闭以保持兼容；使用"Matmul 高阶 API + SetTensorScaleA 等"或 `DataCopy`（UB→L1）时，必须核对是否需要打开。来源只说明未启用时相关硬通道/能力不可用或走兼容路径；不要把兼容路径的精度、性能或运行结果当作硬通道证据。 |
| `--cce-disable-asc-reserved-ubuf` | 禁用 Ascend C 接口预留 UB；开启后依赖预留 UB 的接口编译报错，需替换实现。3510 预留 2KB（2201 为 8KB） |
| `--cce-disable-vf-stack-reserved-ubuf` | 仅 3510 生效；释放 6KB VF 栈预留，但编译器不能再缓存寄存器溢出数据，需保证寄存器不溢出 |
| `NO_OVERLAP_IN_MULTI_REPEAT` | 确认无地址重叠时移除多余内存同步指令，提升基础 API 高维切分性能；不确定是否重叠时不要开 |

**不合规怎么改**：按上表按需显式配置；UB 预算项（2KB vs 8KB 预留）要重算，UB 总容量与 bank 结构见检查项 4。

## 检查项 3：基础 API 可用性（删除/替换对照）

**怎么判断**：grep 调用点，再按来源的兼容性问题索引逐条对照；**不合规怎么改**见下表右列。

| 2201 上的用法 | 3510 状态 | 改法 |
|---|---|---|
| L1→GM 直搬（DataCopy/DumpTensor） | 硬件通路删除 | 纯 Cube：L1→L0A/L0B→（用单位矩阵做 Mmad）→L0C→Fixpipe→GM；CV 融合：L1→UB→GM |
| GM→L0A/L0B 的 LoadData | 硬件通路删除 | 拆两步：GM→L1，再 L1→L0A/L0B |
| `SetLoadDataBoundary` + 单次 LoadData 自动绕回 | 相关寄存器删除，接口不再支持 | 2201 上 `boundaryValue=0` 与 3510 等价，直接删调用；非 0 时把一次 LoadData 拆成多次、显式更新源/目的偏移实现绕回（配合 `SetLoadDataRepeatWithStride`/`LoadDataRepeatParamWithStride`） |
| `Fill` 直接初始化 L0A/L0B | 硬件指令删除 | 先 `Fill` 初始化 L1，再用 LoadData 搬到 L0A/L0B |
| `LoadDataWithSparse` + `MmadWithSparse`（4:2 稀疏） | 不支持 4:2 结构化稀疏 | 恢复稠密 B 矩阵布局，用 `LoadData` + `Mmad` |
| Cube 侧 int4b_t（LoadData/Mmad/LoadDataWithTranspose） | Cube 不支持 int4b_t | 在 Vector 上 Cast 成 int8_t，再经 UB→L1 搬运后做矩阵乘 |
| L0A 分形 Zz | 改为 Nz | 不复用：用 `LoadData2DParamsV2` 按 Nz 排布一次搬入；M 轴切分复用：拆两次 LoadData，把上下半部分各重排为连续 Nz 子矩阵，Mmad 逻辑不变 |
| `FixpipeParamsV220` | 兼容但仍推荐原生 | 换 `FixpipeParamsArch3510`：非 NZ2ND/NZ2DN 场景 `dstStride` 单位由 32B 变成 element；NZ2ND 场景 `ndNum`/`srcNdStride`/`dstNdStride` 收敛到 `params` 子结构 |
| `CheckLocalMemoryIA` | 相关寄存器删除 | 调测接口，直接移除调用 |

## 检查项 4：数据布局、UB 预算与对齐

**怎么判断**：

- L0A 采用 NZ 排布（2201 是 ZZ）；A 矩阵转置且非对齐时，回到对应 LoadData 搬运形态核对维度和对齐要求，不沿用 2201 的地址偏移计算。
- UB 结构变化：2201 = 16 个 bank group × 3 bank × 4KB；3510 = 8 个 bank group × 2 bank × 16KB，总容量 256KB。原有的 bank 冲突规避策略要按新 bank 尺寸重算；不能只按总容量判断可用。
- 最小访问粒度/对齐：UB 32B、L1 32B、L0A/L0B 512B、L0C 在 Mmad 时 1024B、搬出时 64B、BiasTable 64B、Fixpipe 64B（relu）或 128B（quant）。GM 搬运的内轴尽量按 128B/256B/512B 对齐；非对齐会向上取整，必须在 tiling 中计入实际搬运字节。
- 是否用到 SSBuffer：容量 3KB，独立于 L1/UB 的地址空间（限定符 `__ssbuf__`），基址由 `GetSsbufBaseAddr` 获取；仅支持 32B 对齐读写，初始内容不确定，消费者不能依赖历史内容；非 MIX 模式下 AIC/AIV0/AIV1 各占 1KB，MIX 模式共享 3KB；需开启 `ENABLE_CV_COMM_VIA_SSBUF`。

**不合规怎么改**：按 NZ 重排矩阵搬运参数；按 512B/64B 等粒度重算分形偏移；UB 预算按 256KB 与 2KB 预留重算；用 SSBuffer 前先确认编译选项与对齐/越界约束。

## 检查项 5：精度行为（Subnormal）

**怎么判断**：3510 硬件不支持 Subnormal；来源同时说明基础 API 和部分高阶 API 可通过软件实现相关语义。因此不要把“硬件不支持”改写成“所有结果必为 0”，而要按具体接口、config 和编译选项核对：

1. 是否调用 `Ln`/`Sqrt`/`Rsqrt`/`Div`/`Reciprocal`/`Exp` 及相关高阶 API？
2. 这些调用是否带 config 模板参数？
3. 输入是否可能落在 subnormal 区间，或 golden 依赖 subnormal 语义？

**不合规怎么改**：带 config 的基础 API 用 config 显式选算法，例如
`static constexpr AscendC::LnConfig CONFIG = { AscendC::LnAlgo::PRECISION_1ULP_FTZ_FALSE };` 后 `Ln<half, CONFIG>(...)`；注意 config 是 const 引用型模板参数，实参必须有静态存储期。调用时未传 config 的部分基础 API 与高阶 API 只能靠 `--cce-ftz`（默认 `true`，即 FTZ）。

**验证**：用含 subnormal 的输入构造用例；单个接口的实测判别（Exp 默认 INTRINSIC 的失配）见 [Exp 默认 INTRINSIC FTZ 致 subnormal 残留失配](../precision/exp_intrinsic_ftz_subnormal.md)——那张卡是接口级实测，本项是迁移清单里的位置。

## 检查项 6：高阶 API 与算子族差异

**怎么判断**：按算子族对照来源的兼容表，**不合规怎么改**见右列。

| 算子族 | 3510 状态 | 改法 |
|---|---|---|
| 卷积计算类高阶 API | 暂不支持 | 该族不能在 3510 走原高阶 API 路径 |
| Matmul 数据类型 | 来源表按 (A, B, Bias, C) 组合列出：`int4b_t` 行标注"3510 架构不支持"，其余组合标注"3510 架构新增" | 逐组合核对，不能沿用 2201 的 dtype 组合假设；4:2 稀疏同样不支持 |
| Hccl | `BatchWrite`、`iterate`、`Query`、`InterHcclGroupSync`、`GetWindowsInAddr/OutAddr`、`GetRankId`、`GetRankDim`、`QueueBarrier`、`GetQueueNum` 暂不支持 | 这些接口不在 3510 可用面上；新增能力为 `SetReduceType`、`AlltoAllvWrite`，Hccl 模板参数支持 `HCCL_SERVER_TYPE_CCU` |
| 数学计算 | Tanh/Asin/Sin/Acos/Cos/Log/Atan/Fmod 兼容并扩展算法配置；Power 扩展 uint8/int8/uint16/int16/uint32/bfloat16；Sign 扩展 int64 | 需要高精度/高性能算法选择时用模板参数显式指定 |
| 归一化 | Normalize/WelfordUpdate 扩展 bfloat16；LayerNorm 扩展求方差；WelfordFinalize 扩展算法配置 | bf16 与新算法配置按需启用 |
| 量化 | AscendQuant/AscendDequant/AscendAntiQuant 兼容，扩展 PRE_TOKEN/PRE_GROUP 量化与新的低精度类型 | 旧量化路径可保留，新特性按目标格式选用 |
| 归约/排序/索引/过滤/张量变换 | ReduceSum 扩展 int32/uint32/int64/uint64；ReduceMax/ReduceMin 扩展多种整型与 bf16；TopK 的 RADIX_SELECT 扩展 dtype；Sort 扩展算法配置；BroadCast 扩展动态 Shape；Transpose 新增排布转换；Fill/DropOut/Arange 扩展 dtype | 迁移时优先复用这些扩展能力，而非自研替代 |

## 检查项 7：同步、缓存与调测

**怎么判断**：以下约束在 2201 上可能不成立，迁到 3510 要重新核对：

- 核内：相同流水、相同 eventID 下连续 `SetFlag` 是未定义行为；set/wait 不匹配会残留状态影响后续算子。需要异步流水间锁式依赖时，核对 3510 新增 `Mutex`，不要用重复 SetFlag 代替。
- 核间：使用核间同步接口的核函数必须加 `mix` 函数限定符；`CrossCoreSetFlag`/`CrossCoreWaitFlag` 模式 0/1/2 的 pipe 模板参数不支持 `PIPE_ALL`、`PIPE_S`，模式 4 不支持 `PIPE_ALL`；`CrossCoreSetFlag` 计数器超过 15 次需做一次反向同步，否则会卡死。
- 缓存：标量写 GM 会经 DCache，硬件不保证 DCache 与 GM 一致；需要 `DataCacheCleanAndInvalid`，或改用 `ReadGmBypassDCache`/`WriteGmBypassDCache`；不要在未证明脏行已写回或不需保留时省略回写。

**不合规怎么改**：同步类问题按来源建议用孪生调试/mssanitizer 提前识别；新增的 `Mutex`（核内异步流水同步）与核间同步模式 4（AIV0/AIV1 可分别触发 AIC 等待）可用于替代原来的粗粒度同步。

## 验证方式

1. **编译级**：以 3510 为目标重新编译通过（编译器侧即 `--npu-arch=dav-3510`；具体构建目标名以工程为准）。
2. **结构级**：对检查项 3 的每个改动，确认数据通路与分形（L1/L0A 的 Nz）与改前假设一致。
3. **实现路径级**：记录是否启用 `ENABLE_CV_COMM_VIA_SSBUF`、是否禁用预留 UB、是否启用 `--cce-ftz` 等影响路径的开关；`CMAKE_ASC_RUN_MODE=sim/cpu` 只能验证对应仿真/CPU 路径。
4. **上板级**：subnormal 输入用例、UB bank 冲突、核内/核间同步和 DCache/GM 一致性；同步类问题按来源走孪生调试/mssanitizer。

注意：编译通过只证明符号与选项可用，**不证明精度与性能**——相邻的 Gather/TopK 卡就是"编译级验证"的先例。

## 失效边界

- 本卡每条结论都来自 asc-devkit 的 3510 迁移文档、3510 硬件约束与编译说明，**未提供 950 上板复测证据**；"验证方式"是要做的动作，不是已完成证据。
- 平台限定：3510 = Ascend 950PR&950DT 系列；`--cce-ftz`、`ENABLE_CV_COMM_VIA_SSBUF`、`NO_OVERLAP_IN_MULTI_REPEAT` 等选项仅在 950PR&950DT 支持。
- Fixpipe 在 3510 仍兼容 `FixpipeParamsV220`，"能编过"不代表已迁到原生结构体；`dstStride` 单位差异只在非 NZ2ND/NZ2DN 场景出现。
- `ENABLE_CV_COMM_VIA_SSBUF` 未打开时，不得声称使用了 SSBuffer 或 UB→L1 硬通道；若工程选择兼容路径，必须单独记录其数据通路和验证结果。
- `CMAKE_ASC_RUN_MODE=sim` 是仿真模式，`cpu` 是 CPU 调试模式；二者都不等价于 3510 上板执行，不能替代 NPU 运行验证。
- 高阶 API 与 C API 的兼容结论按层生效（检查项 0），不能用一个接口的兼容性外推整层；各表的完整 dtype/接口清单以来源表为准，本卡只列迁移时最常踩的项。
