---
type: "Runbook"
title: "Cast SatMode::SAT 饱和致 fp16 NaN/Inf 丢失"
description: "dav-3510 上高层 AscendC::Cast 与底层 Reg::Cast 对 b16↔fp32 一律硬编码 SatMode::SAT，fp16 NaN/Inf 在第一次 b16→fp32 Cast 即被饱和为 65504，castTrait 调参（NO_SAT/默认/参考 castTraitB16ToB32）与 PostElewise Compare+Select 均无法恢复 NaN/Inf，禁止作为 NaN/Inf 传播配方。"
tags: ["task.debugging", "topic.precision", "topic.compute.elementwise.type_conversion"]
status: stable
sources: []
created_at: "2026-08-15T00:00:00Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# Cast SatMode::SAT 饱和致 fp16 NaN/Inf 丢失

## 现象

`euclidean_norm` Branch-0 kernel 在 dav-3510（Ascend 950）跑 ACLNN ST（`operators/euclidean_norm_package/tests/aclnn`，`bash run.sh`），修复 tilingKey 编码后转绿到 8/11 PASSED，剩 3 条 fp16 精度失败：

- `case08_nan_propagation_fp16`：输入含 NaN，`expected NaN, got 65504.000000`（65504 = fp16 max finite）。
- `case09_inf_propagation_fp16`：输入含 +Inf，`expected inf, got 65504.000000`。
- `case10_fp16_overflow_ap007`：输入全 60000.0（平方和上溢），`expected inf, got 65536.000000`。

预期语义（DESIGN §4.3.2）是 fp16 NaN/Inf 在 reduction 输出中硬对齐传播。三条失败的 `actual` 全部落在 65504/65536 量级，是 Cast 饱和的典型指纹。

## 适用场景

- **工程形态**：ACLNN 算子仓 kernel 直调，Vector 计算链含 b16↔fp32 Cast（pre-elewise Cast→fp32、post-elewise Sqrt+Cast 回 b16）。
- **API 路径**：`AscendC::Reg::Cast` / 高层 `AscendC::Cast` / `CastIntrinsicsImplVF`（`asc/impl/basic_api/dav_3510/kernel_operator_vec_vconv_impl.h`）。
- **验证过的平台与 CANN 版本**：Ascend 950（dav-3510），CANN 9.1.0。
- **适用粒度**：`platform_wide`（dav-3510 上所有用 Reg::Cast 做 b16↔fp32 的 kernel）。
- **路线优先级**：`banned`（禁止用 castTrait 调参传播 NaN/Inf）。
- **明确不适用或未验证场景**：int32 dtype 不经 b16 Cast，不在此列；非 dav-3510 平台的 Cast SatMode 行为未验证。

## 根因

`asc/impl/basic_api/dav_3510/kernel_operator_vec_vconv_impl.h` 中 `CastIntrinsicsImplVF` 的 castTrait 硬编码（CANN 头文件 file_read 实测）：

```cpp
static constexpr Reg::CastTrait castTrait = {
    Reg::RegLayout::ZERO, Reg::SatMode::SAT, Reg::MaskMergeMode::ZEROING, roundMode};
```

即高层 `AscendC::Cast` 对所有 b16↔fp32 转换强制 `SatMode::SAT`（饱和），底层 `Reg::Cast` 指令同样饱和。NaN/Inf 在 b16→fp32 Cast 阶段（`CastSquareVf`）就被饱和为 65504，后续 `Square(65504)=4.29e9 → ReduceSum → Sqrt ≈ 65536 → Cast 回 fp32→fp16` 再次饱和到 65504。NaN/Inf 信息在第一次 Cast 已丢失，PostElewise 阶段 fp32 中已无 NaN 标记位，无法用 Compare+Select 恢复。

## 失败路线

围绕"用 castTrait 调参让 b16↔fp32 Cast 保留 NaN/Inf"这一目标，以下路线均 banned（尝试后失败/回退）：

1. **`kCastTraitFromFp32Fp16 = {ZERO, NO_SAT, ZEROING, CAST_RINT}`**（post-elewise fp32→fp16）：`NO_SAT` 在硬件 `Reg::Cast` 上不被尊重，ST 输出仍饱和到 65504。banned。
2. **默认 `castTrait`（`MaskMergeMode::UNKNOWN`）**：编译报 `MaskMergeMode::UNKNOWN` 不支持，必须 `ZEROING` 或 `MERGING`，无法成图。banned。
3. **CANN 参考 `castTraitB16ToB32 = {ZERO, UNKNOWN, ZEROING, UNKNOWN}` / `castTraitB32ToB16 = {ZERO, NO_SAT, ZEROING, CAST_RINT}`**（`asc/impl/adv_api/detail/common/common.h`）：b16→fp32 仍不保留 NaN，硬件指令层无视 `SatMode::NO_SAT/UNKNOWN`。banned。
4. **PostElewise Compare+Select 检测路线**（检测 fp32 是否为 65504 后 Select 写 NaN bit 模式）：65504 是合法 finite 值，无法与饱和结果区分；且 NaN 在 b16→fp32 Cast 阶段已丢失，PostElewise 阶段已无原始 NaN 信号。banned。

结论：在 dav-3510 上经 Cast 传播 NaN/Inf 的路线 banned，须 bypass Cast（在 b16 原始位上检测指数位 `0x1F` 后直接写 fp16 NaN/Inf bit 模式到输出）。

## 验证信号

- case08/09/10 在上述全部 castTrait 调参尝试后仍 FAIL，`actual=65504.000000 / 65536.000000`（来源平台:950；证据等级:tool_observed）。
- `CastIntrinsicsImplVF` castTrait 硬编码 `Reg::SatMode::SAT`，来自 CANN 头文件 `asc/impl/basic_api/dav_3510/kernel_operator_vec_vconv_impl.h`（及 `reg_compute/dav_3510/kernel_reg_compute_vec_vconv_impl.h`）file_read（来源平台:950；证据等级:artifact_verified）。
- ST 最终 8/11 PASSED，3 条 fp16 NaN/Inf/overflow 标记为硬件限制，未放宽测试容差（来源平台:950；证据等级:tool_observed）。

## 失效边界

- 推断可迁移：a2 / a3 平台的 `Reg::Cast` 同源 `asc/impl/basic_api/dav_*` 实现路径，SatMode 行为预计同构——未验证，推断可迁移。
- 未验证场景：若未来 CANN 在 `CastIntrinsicsImplVF` 引入 `SatMode::NO_SAT` 真正生效的硬件路径，本 banned 结论需重测。

## 坏实践

- 把 `compareOutput` 改成"fp16 NaN/Inf 等价于 65504"放行通过——掩盖真实 NaN/Inf 传播缺陷，属测试侧放松捷径，禁止作为正卡。
- 在 PostElewise 用 Compare(fp32==65504) Select NaN：65504 是合法 finite，误判率高，已验证无效。

## 误诊

- 初判 `kCastTraitFromFp32Fp16` 的 `NO_SAT` 会生效（agent_reported，非实测）；实测 ST 后仍饱和，纠正为硬件限制。

<!-- cannbot:related:start -->
## 相关

- [Cast](../../apis/simd_api/basic_api/reg_vector_compute/type_conversion/cast.md)（`exemplifies`）：《Cast》说明Reg矢量计算的精度转换接口，支持浮点转整数、浮点转浮点、整数转浮点和整数转整数四种类型转换。；《Cast SatMode::SAT 饱和致 fp16 NaN/Inf 丢失》说明dav-3510 上高层 AscendC::Cast 与底层 Reg::Cast 对 b16↔fp32 一律硬编码 SatMode::SAT，fp16 NaN/Inf 在第一次 b16→fp32 Cast 即被饱和为 65504，castTrait 调参（NO_SAT/默认/参考 castTraitB16ToB32）与 PostElewise Compare+Select 均无法恢复 NaN/Inf，禁止作为 NaN/Inf 传播配方。。二者在Reg Cast的源目类型布局、舍入、饱和及mask trait必须共同匹配，相关编译和NaN故障是这些配置错误的直接验证上存在可执行的直接衔接。
- [IsNan接口](../../apis/simd_api/adv_api/math_compute/is_nan_interface/is_nan_interface.md)（`exemplifies`）：《IsNan接口》处理“按元素判断浮点数是否为NaN，并提供临时空间大小获取接口。”。《Cast SatMode::SAT 饱和致 fp16 NaN/Inf 丢失》提供“dav-3510 上高层 AscendC::Cast 与底层 Reg::Cast 对 b16↔fp32 一律硬编码 SatMode::SAT，fp16 NaN/Inf 在第一次 b16→fp32 Cast 即被饱和为 65504，castTrait 调参（NO_SAT/默认/参考 castTraitB16ToB32）与 PostElewise Compare+Select 均无法恢复 NaN/Inf，禁止作为 NaN/Inf 传播配方。”，其具体合同或探针直接接入IsNan 的 Kernel/Tiling 合同、跨 dtype 谓词与 Cast 保留 NaN 的前置条件。
- [RoundMode](../../apis/simd_api/basic_api/reg_vector_compute/aux_data_types/round_mode.md)（`exemplifies`）：RoundMode 与《Cast SatMode::SAT 饱和致 fp16 NaN/Inf 丢失》的实质衔接是：RoundMode 与 SatMode 共同配置 Reg Cast；所选故障卡直接覆盖命名空间、非法 CAST_NONE、BF16 CAST_RINT 和 NaN/Inf 饱和后果。
- [SatMode](../../apis/simd_api/basic_api/reg_vector_compute/aux_data_types/sat_mode.md)（`exemplifies`）：SatMode 枚举定义 SAT/NO_SAT 语义，本卡进一步给出 dav-3510 Cast 实现硬编码 SAT 后 NaN/Inf 变为 65504 的实测边界。
- [A3 RMSNorm 不要用分母正值保护吞掉 NaN 传播](rmsnorm_nan_propagation_not_positive_guard.md)（`related`）：NaN 传播失败还可能更早发生在 b16 Cast 饱和阶段；目标卡的 65504 指纹与本卡有限零值指纹可区分 Cast 丢 NaN和倒数 guard 丢 NaN。
- [FP16 算子 Cast 提升-计算-回退链设计](fp16_cast_up_fp32_compute_cast_down_chain.md)（`related`）：FP16 算子 Cast 提升-计算-回退链设计 与《Cast SatMode::SAT 饱和致 fp16 NaN/Inf 丢失》的实质衔接是：FP16 提升到 FP32、VF 计算再 RINT 回退要求 Cast 模式、lane 宽、UB 容量和 MTE/Vector 同步一致；相关故障均命中这些步骤。
- [HiFloat8 SatMode::SAT Cast NaN 映射 0x00](hifloat8_satmode_sat_cast_nan_0x00.md)（`related`）：两卡都验证 SatMode::SAT 会破坏 NaN，但目标 HiFloat8 路径映射到 0x00，本卡 FP16 路径映射到 65504；输出指纹可区分具体转换链。
- [MX-FP4 NaN 块 device 写 e8m0=0xFF、fp4=0x0](mx_fp4_nan_device_e8m0_0xff_fp4_0x0.md)（`related`）：FP16 卡说明 SatMode::SAT 会把 NaN/Inf 饱和成有限值，MX-FP4 卡则记录 CAST_RINT 把 NaN 映射 0；共同要求 golden 按目标 Cast/SatMode 的真实特殊值语义实现。
- [b16 running 经 fp32 回转会改写 NaN payload](bit_exact_b16_nan_payload_needs_original_dtype_running_value.md)（`related`）：目标卡说明即使 NaN 仍存在，B16→FP32→B16 也会改写 payload；本卡是更强边界——SAT 在第一次 Cast 已完全丢失 NaN/Inf。
- [bf16 扩精度 Cast 误用 CAST_RINT 产垃圾值判别](bf16_cast_cast_rint.md)（`related`）：两卡把 B16 Cast 的两类独立配置错误分开：RoundMode 方向误用产生 garbage，SatMode::SAT 则以 65504/65536 指纹吞掉 NaN/Inf。
<!-- cannbot:related:end -->
