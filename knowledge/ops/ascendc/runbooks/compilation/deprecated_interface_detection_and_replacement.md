---
type: "Runbook"
title: "Ascend C API 废弃接口的发现、替换与重验流程"
description: "迁移 Ascend C API 时结合废弃声明告警、接口级清单与基础 API 命名变更表定位调用点；按旧重载、产品范围和目标签名选择替代。同步复合接口替换需重新核对 asc_sync 的全流水语义，并分别验证编译、依赖顺序、数值和性能。"
tags:
- "task.migration"
- "task.implementation"
- "topic.compilation"
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/deprecated_interface.md
  role: primary
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/interface_change_description.md
  role: supporting
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/defs/macro/asc_deprecation.md
  role: evidence
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/deprecated_interface/asc_mmad_deprecated.md
  role: example
created_at: '2026-10-23T02:00:00Z'
updated_at: '2026-10-23T08:55:34Z'
platforms:
- '950'
- a2
- a3
---

# Ascend C API 废弃接口的发现、替换与重验流程

## 触发条件

- 从 CANN 8.5.0 及前序版本、或 9.0.0 及前序版本升级到当前版本（命名变更对照表以这两条基线给出）；
- 代码中使用了 `*_sync` 复合接口（同步语义内置在接口里），或 `asc_loadalign`、`asc_storealign` 这类"一个名字多种模式"的重载；
- 使用了带 `unit_flag`（`uint8_t`）、`feat_offset` 等旧参数形态的接口，或旧的三参数位置控制原型；
- 工程要在 Ascend 950PR&950DT（3510）与 Atlas A3 / Atlas A2（2201）之间共用代码，需确认废弃范围在两个体系上是否一致。

## 步骤 1：判定是否存在废弃接口调用（发现）

1. **看编译告警**：部分 C API 声明可用 `ASC_DEPRECATED` 宏（公共头 `c_api/defs/macro.h`）挂上 C++ `[[deprecated]]` 属性；编译调用被标记声明的代码时，编译器会生成告警，格式为
   `Deprecated since <version>, Will be removed after <removal_date>, Use <replacement> instead.`
   告警文本自带开始废弃的版本、计划移除日期和推荐替代接口。
   **边界**：该宏只添加废弃属性和告警信息，不阻止被标记接口参与编译，也不会在计划移除日期后自动删除接口；`removal_date` 仅用于生成告警文本。编译成功或没有告警均不能证明没有废弃调用：还需确认所编译的路径和声明，并查清单中的旧原型及重载。
2. **按清单逐名对照**：不论是否出现告警，都用两份登记文档对照——`deprecated_interface.md` 给逐接口的废弃状态和替代方向；`interface_change_description.md` 是基础 API 的命名变更对照表（原接口名 → 新接口名 → 备注），不等同于 C API 废弃清单。备注列标出改名之外的参数或语义变化。
3. **区分废弃状态再排期**：清单里同时存在"后续版本会废弃"（尚未废弃，可排期替换）与"已废弃"/"旧原型已废弃"（优先替换）两种措辞，二者处理节奏不同，不要一律当成立即不可用。
4. **工程内检索**：按清单里的接口名逐个对照调用点，重点检查 `*_sync` 后缀、被重命名的基础 API 旧名（如 `ScalarGetCountOfValue`、`FusedMulAddRelu`、`GetAccVal`）、单名多模式的重载（`asc_loadalign`、`asc_storealign`）；同名时按实际参数和目标产品区分旧/新原型。

## 步骤 2：按替换类型选路径（判定树）

### A. 命名变更：先对照参数与语义

命名变更对照表中备注为"无"的条目包括：`ScalarGetCountOfValue`→`GetBitCount`、`ScalarCountLeadingZero`→`CountLeadingZero`、`ScalarGetSFFValue`→`GetSFFValue`、`FusedMulAddRelu`→`MulAddRelu`、`CastDeq`→`CastDequant`、`CompareScalar`→`Compares`、`SetAtomicNone`→`DisableDmaAtomic`、`InitConstValue`→`Fill`、`CalcTschBlockDim`→`CalcTschNumBlocks`。C API 废弃清单另给出 `asc_set_atomic_none`→`asc_disable_dma_atomic`、`asc_set_atomic_add_int`→`asc_set_atomic_add_int32`、`asc_set_atomic_max_int`→`asc_set_atomic_max_int32`、`asc_set_atomic_min_int`→`asc_set_atomic_min_int32`、`asc_get_ar_spr`→`asc_get_squeeze_status`、`asc_pack`→`asc_pack_to_low`、`asc_pack_v2`→`asc_pack_to_high` 等替代方向。"无"只表示对照表未附备注，清单的替代方向也不保证签名、状态或语义完全相同；逐项核对目标接口。

### B. 同步复合接口 → 非同步接口 + `asc_sync()`

清单列举了矩阵计算搬运、矢量数据搬运、Memory 矢量计算等多类 `*_sync` 的替代方向，例如 `asc_copy_l12ub_sync`、`asc_copy_gm2l0a_sync`、`asc_add_sync`、`asc_abs_sync`、`asc_float2half_sync`（含 `_rn`/`_rna`/`_rd`/`_ru`/`_rz`/`_ro` 等列明的变体）、`asc_duplicate_sync`、`asc_repeat_reduce_sum_sync`：按各条目选择非同步接口并核对 `asc_sync()` 的位置。`asc_sync()` 会等待同核所有流水在调用前提交的操作，并阻塞后续指令，可能比原接口同步范围更广、影响性能；清单中的“接口 + `asc_sync()`”不证明逐点等价。`asc_sync_vec()` **无入参原型**也已废弃并推荐 `asc_sync()`；带 `id` 的重载不能据此判为废弃。

### C. 重载收窄 / 模式拆分：必须显式选新模式

- `asc_loadalign(dst, src)` 原通过函数名重载承载 NORM/BRC/UP2X/DOWN2X/UNPACK/BRCV2/BRCV3/DEINTLV 等多种搬入模式，现收窄为仅 NORM，其余模式拆成独立函数（如 `asc_loadalign_brc_datablock`、`asc_loadalign_brc_elem2datablock`、`asc_loadalign_unpack4`、`asc_loadalign_deintlv`、`asc_loadalign_downsample`）。
- `asc_storealign(dst, src, mask)` 原承载 NORM/FIRST/PACK/PACKV2/INTLV 等搬出模式，现收窄为仅 NORM，其余拆为 `asc_storealign_1st`、`asc_storealign_intlv`、`asc_storealign_pack`、`asc_storealign_pack_quarter`、`asc_storealign_postupdate`。
- 带偏移量的旧原型按"无偏移 / `addr_reg` / `int32_t` / `int32_t` Post Update"分档废弃（`asc_loadalign_*_v2`、`_v3`、`_v4` 等），替换时要同时选对新函数名与目标偏移原型。
- 判定：这类不能按名字机械替换，必须先确认旧调用实际落在哪个模式分支上。

### D. 旧原型 → 显式位置参数重载

`asc_float2half`、`asc_half2float`、`asc_int322int16`、`asc_bfloat162float` 等类型转换接口中，通过后缀控制源读取位置或目的写入位置的旧三参数原型已废弃；`asc_bfloat162e2m1x2` 的旧原型也已废弃。按各自条目选择**显式位置参数**重载；`asc_muls` 改用 `asc_mul_scalar_float2half_rn` 的显式位置参数重载。
语义还发生了拆分：`asc_exp_sub` 的 `half` 输入且不带 `src_pos` 参数的原型、以及 `asc_exp_sub_v2` 原型已废弃——`float` 输入继续用 `asc_exp_sub`，`half` 输入改用带显式 `src_pos` 的 `asc_exp_sub_half2float`。

### E. 参数类型与配置方式变更：改签名，不只是改名

- `asc_mmad`：入参 `unit_flag` 为 `uint8_t` 的形态及 `asc_mmad_sync` 已废弃，改用 `unit_flag_mode` 为 `asc_unit_flag_mode` 的新接口，同步由新接口 + `asc_sync()` 实现；`asc_mmad_mx` 同理。
- **按产品分开判废弃范围**：在 Atlas A3 / Atlas A2 上，带 `feat_offset` 参数的 `asc_mmad`、`asc_mmad_s4` 以及全部 `asc_mmad_sync`、`asc_mmad_s4_sync` 也在废弃之列（该参数在 2201 原型中是无效参数）；`asc_mmad_sparse` 的废弃说明标注在 A3、A2 上。
- L2 Cache 配置改枚举：`asc_copy_gm2ub_align` / `asc_copy_ub2gm_align` 在 950 上的原高维切分搬运原型、以及 `asc_ndim_copy_gm2ub` 的原函数原型已废弃，改用 `asc_load_l2_cache_mode` / `asc_store_l2_cache_mode` 枚举值配置；`asc_set_gm2ub_pad`→`asc_set_copy_pad_val`。
- 矩阵与搬运配置类改名：`asc_set_l0c2gm_nz2nd`→`asc_set_l0c_copy_nz_para`、`asc_set_l0c2gm_channel_para`→`asc_set_l0c_copy_channel_para`、`asc_set_l0c2gm_config`→`asc_set_l0c_copy_config`、`asc_set_l12l0_padding_val`→`asc_set_l12l0b_3d_padding`、`asc_set_l13d_padding`→`asc_set_l12l0a_3d_padding`；`asc_set_fp32_mode`→`asc_disable_hf32`、`asc_enable_fp8`→`asc_disable_hif8`、`asc_enable_hf32_trans`→`asc_set_hf32_round_mode`。
- 逻辑运算收窄：`asc_and`、`asc_or` 的浮点类型重载已废弃，需按位宽选择对应的整数重载。

### F. 无替代接口与平台限定废弃（不能机械替换）

- `asc_set_l0c2gm_quant_post`：已废弃且**暂无登记的替代接口**；该需求需单独评估或重新设计，不要挑一个"看起来相近"的接口顶上。
- `asc_get_store_atomic_config`：仅在 Ascend 950PR&950DT 系列产品上废弃（替代为 `asc_atomic_add`）；`asc_set_store_atomic_config_v2` 也在 950 标注块内标注"后续版本会废弃"。
- 系统变量类要换成内置变量组合：`asc_get_block_idx`→内置变量 `block_idx` 配合 `asc_get_sub_block_num`、`asc_get_sub_block_id` 计算逻辑核索引；`asc_get_block_num`→内置变量 `block_num`。

## 步骤 3：替换后必须重验什么

1. **编译**：核对新接口的参数个数、类型、顺序。最危险的是"改名同时动了参数"的条目：`BlockReduceSum`/`BlockReduceMax`/`BlockReduceMin` 合并为 `ReduceDataBlock`（模板参数区分归约类型，且 **mask 与 repeatTime 的参数顺序被调整**）、`WholeReduceSum`/`WholeReduceMax`/`WholeReduceMin` 合并为 `ReduceRepeat`、`RepeatReduceSum`→`ReduceRepeat`（顺序调整并删除无效参数 `dstBlkStride`）。
2. **返回值与类型**：`ToFloat` 其中一个重载的返回值类型由 `float` 改为模板 `U`（`U = float`）；`SetHF32Mode`、`SetHF32TransMode` 接口名不变但参数类型由 `bool` 改为枚举——这类"能编过但语义已变"的条目要逐个核对调用点。
3. **语义拆分**：`SetMMLayoutTransform` 按 `true`/`false` 分别对应 `SetMMRowMajor`/`SetMMColumnMajor`，不能整体替换；`ScalarCast`、`ToBfloat16` 也是按目标类型拆到不同的 `Cast` 重载。
4. **同步**：B 类替换后逐个核对原同步点、目标接口的同步要求及 `asc_sync()` 的实际位置；漏补可能丢失原有顺序保证，直接照搬也不能推定同步范围和性能不变。
5. **数值**：按原 dtype 与 Round 模式后缀（`_rn`/`_rna`/`_rd`/`_ru`/`_rz`/`_ro`）逐项对照，替换后跑同一组数据对拍。来源只给出替代关系，未承诺逐位等价。
6. **性能**：同步点显式化可能改变流水结构，替换后必须重测该段 kernel；来源不含性能等价承诺。

## 失效边界

- 本卡是流程与分类，**单接口的签名、约束、产品支持**以单接口卡/文档为准（见"相邻卡分工"）。
- 平台范围：单接口 `asc_mmad` 文档列出 Ascend 950PR&950DT（`950`）、Atlas A3（`a3`）、Atlas A2（`a2`）为支持，并对 A2/A3 另列 `feat_offset` 废弃范围；这不是整个清单的统一产品矩阵。其他条目须逐项核对目标产品上的旧/新接口及同步原型；未标注产品的条目不能据此推断全平台适用。
- 本卡的"发现"手段依赖文档清单与编译告警，不构成"全工程扫描工具"的结论；清单本身会随版本更新，替换前应以目标 CANN 版本自带的文档/头文件再核对一次。

## 相邻卡分工

- [deprecated_interface](../../apis/appendix/deprecated_interface.md)：全量清单，查"哪个接口被谁替代"；本卡讲"怎么发现、怎么判替换类型、替换后验什么"。
- [interface_change_description](../../apis/appendix/interface_change_description.md)：命名变更对照表（含"改名同时改了什么"的备注）。
- [asc_mmad_deprecated](../../apis/simd_api/c_api/deprecated_interface/asc_mmad_deprecated.md)：单接口完整原型与产品支持矩阵，本卡 E 类结论出自它；[asc_mmad_mx_deprecated](../../apis/simd_api/c_api/deprecated_interface/asc_mmad_mx_deprecated.md) 同理。
- [asc_pack_deprecated_reference_contract](../../guides/regbase/asc_pack_deprecated_reference_contract.md) 与 [asc_create_iter_reg_deprecated_reference_contract](../../guides/regbase/asc_create_iter_reg_deprecated_reference_contract.md)：废弃接口的固定 reference 调用约束；本卡只给"废弃→替代"的方向，不展开单接口契约。
- [begin_tiling_data_def_deprecated](./begin_tiling_data_def_deprecated.md)：同类"废弃选型"问题但对象是 TilingData 注册宏族（高层 API 宏），不属于本卡的 C API 废弃清单。
- [ol_127_cann_api_surface_shrinks_across_versions_check_api](./ol_127_cann_api_surface_shrinks_across_versions_check_api.md)：跨版本 API 面**收缩**（旧接口在新版本上不再提供）；本卡处理的是接口存在但已废弃/改签名。
- [ascend_c_api_compatibility](../../guides/cross_gen_migration_guide/ascend_c_api_compatibility.md)：Ascend C API 兼容性策略（功能兼容/性能兼容的口径、跨架构需重新编译）；本卡是其中的"废弃与重命名"分支的操作流程。
- [cann_9_2_0](../../apis/appendix/release_notes/cann_9_2_0.md)：版本增量（公共头文件拆分、`ASC_DEPRECATED` 等）。
- [cpp_standard_support_and_syntax_restrictions](./cpp_standard_support_and_syntax_restrictions.md)：C++ 标准与语言级限制，与接口废弃是两个维度。
