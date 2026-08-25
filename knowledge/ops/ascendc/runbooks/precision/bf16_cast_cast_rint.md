---
type: "Runbook"
title: "bf16 扩精度 Cast 误用 CAST_RINT 产垃圾值判别"
description: "AscendC Level-2 Cast 的 RoundMode 语义按方向区分：扩精度（half/bfloat16→float，位数增加无舍入）一律 CAST_NONE；缩精度（float→half/bfloat16，位数减少须舍入）才用 CAST_RINT。把 \"bf16 不支持 CAST_NONE\" 这条缩精度约束误用到 bf16→fp32 扩精度方向、对 bf16 扩精度取 CAST_RINT，不产生精度漂移而直接产生符号翻转/量级错误的垃圾输出。判别=同实现下 fp16 全过、bf16 全错且为 garbage（非小 diff），唯一变量是 widenMode。"
tags: ["task.debugging", "topic.precision", "topic.compute.elementwise.type_conversion"]
status: stable
sources: []
created_at: "2026-08-18T16:12:00Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# bf16 扩精度 Cast 误用 CAST_RINT 产垃圾值判别

## 现象

为某 AscendC 算子的 fp16/bf16 路径实现 `ProcessFp16Bf16()`：4 buffer 布局（UB_TEMP/UB_SELF_FP32/UB_GRAD_O_FP32/UB_RESULT），链路 `CopyIn→Cast(→fp32)→VF<float>→Cast(→fp16/bf16)→CopyOut`。构建退出码 0、tiling struct 注册正常，但 ST 运行出现明显 dtype 分化：

- **fp16 用例全部 PASS**（含广播、NaN/±Inf/全零、空 Tensor 等边界）。
- **bf16 用例全部 FAIL**，且失败模式不是精度漂移，而是**大幅错误**：例如 `B_bf16_self_4_brcst_2x3x4` 首元素 `got=0.437500 exp=-0.012787 diff=4.503e-01`（符号翻转、量级错误），`D_nan_in_go_bf16` `got=0.237305 exp=-0.464039 diff=7.013e-01`，`D_pos_inf_in_self_bf16` `got=-0.486328 exp=-0.844282 diff=3.580e-01`。diff 量级 0.3~0.7，远超 bf16 容差 4e-3 三个数量级以上。

fp16 与 bf16 共用同一 `ProcessFp16Bf16` 实现、同一 4 buffer 布局、同一同步对、同一 VF 链；唯一差异是 `widenMode`（扩精度 Cast 的 RoundMode）：fp16 用 `CAST_NONE`，bf16 用 `CAST_RINT`。

## 适用场景

- **工程形态**：kernel 直调（AscendC Kernel 实现 `op_kernel/arch35/*.h`），Host Tiling 已就绪，算子内对 fp16/bf16 输入先扩精度到 fp32 再进 VF 计算链。
- **API 路径**：`AscendC::Cast(dstLocal<float>, srcLocal<half|bfloat16_t>, AscendC::RoundMode, uint32_t count)`（Level-2 Cast，TBE `kernel_operator_vec_vconv_intf_impl.h`），用于 fp16/bf16 输入扩精度到 fp32 进入 VF 计算链前的 Cast 步骤。
- **验证过的平台与 CANN 版本**：Ascend950（arch35），CANN 9.1.0（`/home/developer/Ascend/cann-9.1.0`）。
- **适用粒度**：`operator_family`——任何在 AscendC kernel 内对 bfloat16→float 做扩精度 Cast 的算子均适用。
- **路线优先级**：`diagnostic_only`——本卡只给判别方法与根因解释；修复实现的终版代码（widenMode 改为无条件 CAST_NONE）的 verbatim after/closure 未从 trace 恢复，不内联完整 after 代码。
- **不适用或未验证场景**：缩精度方向（fp32→bf16）不得用 `CAST_NONE`，必须 `CAST_RINT`（见解释）；本卡只约束 bf16→fp32（扩精度）方向。其他 bf16↔其他 dtype 组合（如 bf16→int32、fp32→half）的 RoundMode 未验证。a2/a3 未验证。

## 判别方法

### 触发（tool_observed 失败症状）

同一 `ProcessFp16Bf16` 实现下，ST 全量运行出现 dtype 分化：fp16 用例全部 PASS，bf16 用例全部 FAIL，且 bf16 失败模式为**大幅错误**（符号翻转/量级错误，diff 0.3~0.7），而非精度漂移（小 diff）。比较器输出形如 `mismatch at idx N: got=%.6f exp=%.6f diff=%.3e`，例如 `got=0.437500 exp=-0.012787 diff=4.503e-01`。

### 可执行探针

1. **同实现 dtype 对照**：保持 `ProcessFp16Bf16` 实现不变，分别跑 fp16 与 bf16 全量用例。若 fp16 全过、bf16 全错且错误模式为 garbage（符号/量级错）而非小 diff，强烈指向 RoundMode 方向误用，而非 VF 计算逻辑错误。
2. **widenMode 取值审查**：读 kernel 源码 `ProcessFp16Bf16` 内 `widenMode` 声明。若为按 dtype 条件取值（`std::is_same_v<T, half> ? CAST_NONE : CAST_RINT`，即 bf16 扩精度用了 CAST_RINT），即为根因。
3. **官方同方向实证对照**：读 CANN 官方 kernel `top_k_top_p_sample.h`（`/home/developer/Ascend/cann-9.1.0/opp/built-in/op_impl/ai_core/tbe/impl/ops_legacy/ascendc/top_k_top_p_sample/top_k_top_p_sample.h`）第 619 行附近，确认其对 `half/bfloat16 → float32` 扩精度用的是 `RoundMode::CAST_NONE`。若官方对 bf16→fp32 扩精度用 CAST_NONE，则 CAST_NONE 对该方向合法，"bf16 不支持 CAST_NONE"必另有所指（缩精度方向）。

### 原始观测（tool_observed）

- ST 运行（同一次 `./run.sh`）：fp16 用例 `[ PASS ]`（如 `B_fp16_self_1x3x1_brcst_2x3x4`），bf16 用例 `[ FAIL ]` 且为大幅错误（`B_bf16_self_4_brcst_2x3x4 -- mismatch at idx 0: got=0.437500 exp=-0.012787 diff=4.503e-01`、`D_nan_in_go_bf16 -- mismatch at idx 1: got=0.237305 exp=-0.464039 diff=7.013e-01`、`D_pos_inf_in_self_bf16 -- mismatch at idx 0: got=-0.486328 exp=-0.844282 diff=3.580e-01`）。
- kernel 源码 `ProcessFp16Bf16::widenMode` 声明为按 dtype 条件三元：`std::is_same_v<T, half> ? AscendC::RoundMode::CAST_NONE : AscendC::RoundMode::CAST_RINT`（bf16→fp32 扩精度取 CAST_RINT）；`narrowMode` 为 `CAST_RINT`。
- CANN 官方 kernel `top_k_top_p_sample.h:619`：`Cast(localValueCast, localValue, RoundMode::CAST_NONE, countLen); // half/bfloat16 -> float32`——对 half 与 bfloat16→float32 扩精度同用 CAST_NONE，注释明示。

### 解释（根因分析，属 interpretation）

`AscendC::Cast` 的 `RoundMode` 参数语义**按方向**区分，不按 dtype 全局区分：

- **扩精度方向**（half/bfloat16 → float，位数增加、无信息丢失、不需要舍入）：`CAST_NONE` 合法且正确。官方 `top_k_top_p_sample.h:619` 对 `half/bfloat16 -> float32` 用 `CAST_NONE` 实证。
- **缩精度方向**（float → half/bfloat16，位数减少、必须舍入）：`CAST_RINT`（或 `CAST_ROUND`）。"bf16 不支持 CAST_NONE" 这条约束**仅指缩精度方向**——fp32→bf16 必须舍入，不能 NONE。

开发者把任务说明里"bf16 不支持 CAST_NONE"误读为对 bf16→fp32（扩精度）也成立，于是对 bf16 扩精度用了 `CAST_RINT`。实测 bf16 路径产生符号翻转/量级错误的垃圾值（`got=0.437500 exp=-0.012787`），而非舍入误差。这表明对扩精度方向误用 `CAST_RINT` 不是"多舍了一次入"的小误差，而是触发了 Cast 指令在该方向对该 RoundMode 的非法/未定义行为，输出整体错乱。`CAST_RINT`（round to nearest integer）在类型转换语义上本就不该用于扩精度（扩精度无舍入需求），硬件实现层面把它用于 bf16→fp32 时行为未定义/错误。

机制链：`bf16 输入 → Cast(...CAST_RINT...) → 垃圾 fp32 值 → VF(sigmoid/exp/div) 在错误输入上计算 → Cast 回 bf16 → 垃圾输出`。fp16 路径因为用 `CAST_NONE` 不受影响，所以全过——这反而锁定了根因在 widenMode，而非 VF 计算链或 buffer 布局。

判别要点：当且仅当「同一实现下 fp16 全过、bf16 全错且错误模式为 garbage」且「widenMode 按 dtype 条件取值（bf16 取 CAST_RINT）」时，根因为 bf16→fp32 扩精度方向误用 CAST_RINT。仅 fp16 全过不足以定性（可能是 bf16 容差问题）；必须叠加 garbage 错误模式 + widenMode 条件取值两个信号。

## 验证信号

- ST 运行（同一次 `./run.sh` 全量用例）：fp16 用例全部 `[ PASS ]`，bf16 用例全部 `[ FAIL ]` 且为大幅错误，如 `B_bf16_self_4_brcst_2x3x4 -- mismatch at idx 0: got=0.437500 exp=-0.012787 diff=4.503e-01`、`D_nan_in_go_bf16 -- mismatch at idx 1: got=0.237305 exp=-0.464039 diff=7.013e-01`、`D_pos_inf_in_self_bf16 -- mismatch at idx 0: got=-0.486328 exp=-0.844282 diff=3.580e-01`（来源平台:950；证据等级:tool_observed）
- kernel 源码 `ProcessFp16Bf16::widenMode` 声明为按 dtype 条件三元：`std::is_same_v<T, half> ? CAST_NONE : CAST_RINT`（bf16→fp32 扩精度取 CAST_RINT），`narrowMode` 为 `CAST_RINT`（来源平台:950；证据等级:artifact_verified）
- CANN 官方 kernel `top_k_top_p_sample.h:619` 对 `half/bfloat16 -> float32` 扩精度用 `RoundMode::CAST_NONE`，注释明示 CAST_NONE 对 bf16→fp32 扩精度合法（来源平台:950；证据等级:artifact_verified）

## 失效边界

- 本卡仅验证 bf16→fp32（扩精度）方向；fp32→bf16（缩精度）必须 `CAST_RINT`，不得用 `CAST_NONE`，否则同样可能产生错误（本 trace 未对缩精度方向做 CAST_NONE 误用实测）。
- 其他 dtype 组合（bf16↔int32、fp32→half、uint8↔bf16 等）的 RoundMode 未验证，不得直接套用本卡结论；`kernel_operator_vec_vconv_intf_impl.h` / `cast_impl.h` 中对各 (src,dst) 组合有按方向的 SupportedRoundMode 校验，需逐组合查证。
- a2/a3（AscendC 其他 arch）平台未验证，推断可迁移（Cast Level-2 API 跨 arch 行为一致），但未实测——不得写入 `platforms`。

## 坏实践

- 据任务说明/设计文档里"bf16 不支持 CAST_NONE"字面推断"bf16→fp32 也得用 CAST_RINT"——把缩精度约束错误外推到扩精度方向。正确做法是查同方向 CANN 官方 kernel 用法（`top_k_top_p_sample.h`）+ 同实现 dtype 对照实测。
- 用 fp16 全过来"默认"bf16 也对——fp16 与 bf16 在本实现里共用代码、仅 widenMode 不同，fp16 全过反而说明问题就在 bf16 专属的 widenMode 分支，而非全局计算逻辑。
- 把 bf16 的 garbage 失败当成"bf16 精度天然差、放宽容差"处理——diff 量级 0.3~0.7 远超容差三个数量级，是 RoundMode 方向误用，不是精度漂移，放宽容差无法掩盖（属反投机取巧）。

<!-- cannbot:related:start -->
## 相关

- [Rintf](../../apis/simt_api/math_functions/float_math_functions/rintf.md)（`exemplifies`）：bf16 扩精度 Cast 误用 CAST_RINT 产垃圾值判别说明AscendC Level-2 Cast 的 RoundMode 语义按方向区分：扩精度（half/bfloat16→float，位数增加无舍入）一律 CAST_NONE；缩精度（float→half/bfloat16，位数减少须舍入）才用 CAST_RINT。把 "bf16 不支持 CAST_NONE" 这条缩精度约束误用到 bf16→fp32 扩精度方向、对 bf16 扩精度取 CAST_RINT，不产生精度漂移而直接产生符号翻转/量级错误的垃圾输出。判别=同实现下 fp16 全过、bf16 全错且为 garbage（非小 diff），唯一变量是 widenMode。
- [RoundMode](../../apis/simd_api/basic_api/reg_vector_compute/aux_data_types/round_mode.md)（`exemplifies`）：RoundMode 接口枚举定义 CAST_NONE、CAST_RINT 等舍入语义，本卡说明扩精度无舍入与缩精度需舍入的调用边界。
- [B16 结果大幅偏差 — UNPACK 后补 Reg Cast](b16_unpack_requires_numeric_cast_before_fp32_compute.md)（`related`）：UNPACK 卡证明布局展开不能替代 B16→FP32 数值 Cast；本卡进一步约束该显式数值 Cast 在扩精度方向必须使用 CAST_NONE。
- [Cast SatMode::SAT 饱和致 fp16 NaN/Inf 丢失](cast_satmode_sat_fp16_nan_inf.md)（`related`）：两卡把 B16 Cast 的两类独立配置错误分开：RoundMode 方向误用产生 garbage，SatMode::SAT 则以 65504/65536 指纹吞掉 NaN/Inf。
- [FP16 算子 Cast 提升-计算-回退链设计](fp16_cast_up_fp32_compute_cast_down_chain.md)（`related`）：FP16 算子 Cast 提升-计算-回退链设计 与《bf16 扩精度 Cast 误用 CAST_RINT 产垃圾值判别》的实质衔接是：FP16 提升到 FP32、VF 计算再 RINT 回退要求 Cast 模式、lane 宽、UB 容量和 MTE/Vector 同步一致；相关故障均命中这些步骤。
- [Reg CastTrait RoundMode 命名空间编译失败](../compilation/casttrait_roundmode_is_in_ascendc.md)（`related`）：Reg CastTrait RoundMode 命名空间编译失败 与《bf16 扩精度 Cast 误用 CAST_RINT 产垃圾值判别》的实质衔接是：该故障由 CastTrait 字段 RoundMode 的错误命名空间触发；trait 存储期/NTTP、merge/sat/round 枚举和 Cast 模式故障共同约束真实模板声明。
- [f32→s64 Cast 使用 CAST_NONE 触发 vcvt 静态断言](../compilation/reg_cast_f32_to_s64_uses_supported_rounding.md)（`related`）：f32→s64 Cast 使用 CAST_NONE 触发 vcvt 静态断言 与《bf16 扩精度 Cast 误用 CAST_RINT 产垃圾值判别》的实质衔接是：这些卡都约束 Reg::Cast 的 RoundMode、MaskMergeMode、trait 存储期/命名空间及宽化 lane，是同一静态断言链上的可执行检查。
- [fp32 窄化舍入模式不一致触发稀疏 MARE 越线](fp32_to_fp16_cast_matches_rne_oracle.md)（`related`）：fp32 窄化舍入模式不一致触发稀疏 MARE 越线 与《bf16 扩精度 Cast 误用 CAST_RINT 产垃圾值判别》的实质衔接是：该精度故障的核心是 fp32 窄化舍入未与 RNE oracle 对齐；Cast/Round 接口、BF16/FP16 边界值和精度验收卡直接提供对照与验证。
- [模板内 float→float Cast 使 fp32 分支全错](templated_float_input_must_bypass_same_type_cast.md)（`same_topic`）：模板内 float→float Cast 使 fp32 分支全错 与《bf16 扩精度 Cast 误用 CAST_RINT 产垃圾值判别》的实质衔接是：float 到 float 不应进入窄化 Cast，应该保持原值或 Copy；同步、BF16 分阶段、native 类型、VL、舍入与 RmsNorm 案例分别说明真正需要 Cast 时的类型、时序和验证契约。
<!-- cannbot:related:end -->
