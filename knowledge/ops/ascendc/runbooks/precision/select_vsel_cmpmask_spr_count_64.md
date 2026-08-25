---
type: "Runbook"
title: "Select VSEL_CMPMASK_SPR count>64 掩码错位判别"
description: "arch35 Select 的 VSEL_CMPMASK_SPR 对 float 仅载首 repeat 的 selMask 并对所有 repeat 复用；count>64 时后续块套用首 64 元素块掩码，错误位置 pos%64 集中在 44/55/56，双向错取 linear/sigmoid 分支。判别：逐元素比对 golden 与 actual 求 pos%64 分布，n=15360 单完整 tile 复现排除 tile 边界。"
tags: ["task.debugging", "topic.compute.elementwise.comparison_logic", "topic.implementation.api_layer.basic_api", "topic.implementation.masking", "topic.precision"]
status: stable
sources: []
created_at: "2026-08-15T16:49:00Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# Select VSEL_CMPMASK_SPR count>64 掩码错位判别

## 现象

`softplus_v2_grad`（arch35/Ascend950，CANN 9.0.0-beta.2）在修完 L2 缓存键漏 scalar 之后仍有部分用例失败。逐元素比对 golden 与 NPU actual，观测到**双向错误**：

- `pos=108`（z=-2.1 ≤ threshold）：golden 为 sigmoid 分支值，actual 取 linear 分支——kernel 错取 linear。
- `pos=120`（z=2.56 > threshold）：golden 为 linear，actual 取 sigmoid——kernel 错取 sigmoid。

双向错误说明不是分支条件写反，而是 `Select` 的掩码被污染。把所有错误位置 `pos % 64` 求分布，集中在 `44, 55, 56, 12, 31` 等固定偏移；进一步取 n=15360（单个完整 tile，64 对齐）仍复现，排除 tiling 尾块/广播对齐问题——锁定在 `Select` 调用本身。

## 适用场景

- **工程形态**：AscendC Kernel 直调（op_kernel），arch35（Ascend950）vector `Select` API。
- **API 路径**：`Select(dst, selMask, src0, src1, selMode, count)` 公共重载（经 `VselImpl`），`selMode` 取 `VSEL_CMPMASK_SPR`(mode 0) 或 `VSEL_TENSOR_TENSOR_MODE`(mode 2)；配套 `Compare<float, uint8_t>(bMask, bBx, bThr, GT, count)` 产掩码。
- **验证过的平台与 CANN 版本**：Ascend950（arch35），CANN 9.0.0-beta.2（头文件 `cann-9.0.0-beta.2/x86_64-linux/asc/impl/basic_api/dav_c310/kernel_operator_vec_sel_impl.h`）。
- **适用粒度**：`platform_wide`——所有 arch35 上对 count>repeatElm（float 为 64）的 `Select` 调用都受此 API 语义约束。
- **路线优先级**：对 count 大于 GetVecLen/sizeof(T) 的场景，`VSEL_TENSOR_TENSOR_MODE` 是唯一逐 repeat 重载掩码的正确模式。
- **不适用或未验证场景**：count ≤ repeatElm 时 `VSEL_CMPMASK_SPR` 与 mode 2 行为一致，本卡不约束小 count；非 arch35（如 a2/a3）未在本 trace 验证。

## 判别方法

- **触发（tool_observed 失败）**：bf16/大 shape 多 tile 用例部分元素错，逐元素比对观测到双向错误——z≤threshold 处 golden 为 sigmoid 分支而 actual 错取 linear，z>threshold 处 golden 为 linear 而 actual 错取 sigmoid。
- **探针（可执行检查）**：固定随机种子复现失败 case，写探针逐元素比对 golden 与 NPU actual，统计错误位置 pos % 64 分布；再用 n=15360（单个完整 tile，64 对齐，无尾块）单独复现，排除 tiling 尾块/广播对齐归因。
- **观测（tool_observed）**：错误位置 pos % 64 集中于 44, 55, 56, 12, 31 等固定偏移；n=15360 单完整 tile 仍有约 808 处大差异，确认 bug 在 `Select` 调用本身而非多 tile 边界。
- **判读（interpretation，根因分析）**：arch35 `SelectMode0Level2`（对应 `VSEL_CMPMASK_SPR`）对 sizeof(T)==4（float）取 repeatElm = GetVecLen/sizeof(T) = 64、repeatTime = CeilDivision(calCount, 64)；其实现 Reg::LoadAlign + MaskUnPack **仅从 sel buffer 载首 repeat 的掩码一次**，随后对所有 repeatTime 次循环复用同一 selMask。count>64 时元素 64..N 全部套用首 64 元素块的掩码，错误位置自然呈 pos % 64 固定偏移模式。对照 `VSEL_TENSOR_TENSOR_MODE`（mode 2）每个 repeat 重新从 sel buffer 对应偏移重载掩码；`Compare` 本身把完整掩码 per repeat 正确写入 bMask，故错在 `SelectMode0Level2` 只读首段。判据：错误位置 pos%64 呈固定偏移 + 单完整 tile 仍复现 → 命中 `VSEL_CMPMASK_SPR` 掩码复用语义缺陷。

## 验证信号

- 错误位置 pos % 64 集中于 44, 55, 56, 12, 31 等固定偏移，符合“首 64 块掩码套用到全部元素”模式（来源平台：Ascend950；证据等级：tool_observed）。
- n=15360（单完整 tile，64 对齐）仍出错，排除 tile 边界归因（来源平台：Ascend950；证据等级：tool_observed）。
- API 头文件取证：`kernel_operator_vec_sel_impl.h` 的 `SelectMode0Level2` 载一次掩码复用 vs `VSEL_TENSOR_TENSOR_MODE` 逐 repeat 重载（来源平台：Ascend950；证据等级：artifact_verified）。
- 将 `Select` 的 selMode 由 `VSEL_CMPMASK_SPR` 切换为 `VSEL_TENSOR_TENSOR_MODE` 后，同一测试集失败用例数显著下降，验证根因判读正确（来源平台：Ascend950；证据等级：tool_observed）。

## 预防

- arch35 上 `Select` 的 count 大于 GetVecLen/sizeof(T) 时禁用 `VSEL_CMPMASK_SPR`，统一用 `VSEL_TENSOR_TENSOR_MODE`；或在 `Select` 封装处对 count>repeatElm 自动切 mode 2。
- 写 `Select` + `Compare` 组合时，先验证 bMask 长度 = Ceil(count, repeatElm) * repeatElm / 8 字节且 `Compare` per repeat 写满，再选 selMode。

## 失效边界

- 推断 a2/a3 同名 API 行为可能不同（不同 arch 的 `kernel_operator_vec_sel_impl.h` 实现），未在本 trace 验证，可迁移需查对应 arch 头文件。
- count ≤ repeatElm（float 即 ≤64）时两模式行为一致，本卡结论不适用。

<!-- cannbot:related:start -->
## 相关

- [AscSelect](../../apis/simd_api/c_api/reg/compare_and_select/asc_select.md)（`exemplifies`）：AscSelect：AscSelect 的 cmpmask 设置/读取和三输入别名约束直接决定结果；所选 runbook均针对该接口的 >64 掩码复用、跨调用残留、异步 RAW 或 dst/src 别名失效，而非泛化连接所有比较接口。 目标卡《Select VSEL_CMPMASK_SPR count>64 掩码错位判别》补充：arch35 Select 的 VSEL_CMPMASK_SPR 对 float 仅载首 repeat 的 selMask 并对所有 repeat 复用；count>64 时后续块套用首 64 元素块掩码，错误位置 pos%64 集中在 44/55/56，双向错取 linear/sigmoid 分支。判别：逐元素比对 golden 与 actual 求 pos%64 分布，n=15360 单完整 tile 复现排除 tile 边界。
- [GetCmpMask](../../apis/simd_api/basic_api/memory_vector_compute/compare_and_select/get_cmp_mask_isasi.md)（`exemplifies`）：《GetCmpMask》处理“获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果。”。《Select VSEL_CMPMASK_SPR count>64 掩码错位判别》明确提供“arch35 Select 的 VSEL_CMPMASK_SPR 对 float 仅载首 repeat 的 selMask 并对所有 repeat 复用；count>64 时后续块套用首 64 元素块掩码，错误位置 pos%64 集中在 44/55/56，双向错取 linear/sigmoid 分支。判别：逐元素比对 golden 与 actual 求 pos%64 分布，n=15360 单完整 tile 复现排除 tile 边界。”，其参数、调用或验证步骤直接接入GetCmpMask 对 CompareStoreToRegister 产出 mask 的读取和 Select 消费链。
- [Select](../../apis/simd_api/basic_api/memory_vector_compute/compare_and_select/select.md)（`exemplifies`）：“Select VSEL_CMPMASK_SPR count>64 掩码错位判别”定义：arch35 Select 的 VSEL_CMPMASK_SPR 对 float 仅载首 repeat 的 selMask 并对所有 repeat 复用；count>64 时后续块套用首 64 元素块掩码，错误位置 pos%64 集中在 44/55/56，双向错取 linear/sigmoid 分支。判别：逐元素比对 golden 与 actual 求 pos%64 分布，n=15360 单完整 tile 复现排除 tile 边界。；“Select”定义：根据selMask比特位值从两个源操作数中选取元素，比特位为1选src0，为0选src1，支持三种选择模式。。实质衔接：这些卡以 64 元素周期、VselImpl sel 不偏移和首块 mask 复用闭合同一根因；分块修复受 32B 对齐阻断，Select/SetCmpMask 文档给出消费契约。
- [Select](../../apis/simd_api/basic_api/reg_vector_compute/compare_and_select/select.md)（`exemplifies`）：Select VSEL_CMPMASK_SPR count>64 掩码错位判别说明arch35 Select 的 VSEL_CMPMASK_SPR 对 float 仅载首 repeat 的 selMask 并对所有 repeat 复用；count>64 时后续块套用首 64 元素块掩码，错误位置 pos%64 集中在 44/55/56，双向错取 linear/sigmoid 分支。判别：逐元素比对 golden 与 actual 求 pos%64 分布，n=15360 单完整 tile 复现排除 tile 边界。
- [Select](../../apis/simd_api/basic_api/reg_vector_compute/mask_reg_compute/select.md)（`exemplifies`）：《Select》的任务是“根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。”。《Select VSEL_CMPMASK_SPR count>64 掩码错位判别》具体提供“arch35 Select 的 VSEL_CMPMASK_SPR 对 float 仅载首 repeat 的 selMask 并对所有 repeat 复用；count>64 时后续块套用首 64 元素块掩码，错误位置 pos%64 集中在 44/55/56，双向错取 linear/sigmoid 分支。判别：逐元素比对 golden 与 actual 求 pos%64 分布，n=15360 单完整 tile 复现排除 tile 边界。”，它直接用于Reg Select 的 mask 来源、CMPMASK 生命周期、偏移、别名和跨调用污染。
- [SetCmpMask](../../apis/simd_api/basic_api/memory_vector_compute/compare_and_select/set_cmp_mask_isasi.md)（`exemplifies`）：“Select VSEL_CMPMASK_SPR count>64 掩码错位判别”定义：arch35 Select 的 VSEL_CMPMASK_SPR 对 float 仅载首 repeat 的 selMask 并对所有 repeat 复用；count>64 时后续块套用首 64 元素块掩码，错误位置 pos%64 集中在 44/55/56，双向错取 linear/sigmoid 分支。判别：逐元素比对 golden 与 actual 求 pos%64 分布，n=15360 单完整 tile 复现排除 tile 边界。；“SetCmpMask”定义：设置CmpMask比较寄存器的值，配合不传入mask参数的Select接口使用。。实质衔接：这些卡以 64 元素周期、VselImpl sel 不偏移和首块 mask 复用闭合同一根因；分块修复受 32B 对齐阻断，Select/SetCmpMask 文档给出消费契约。
- [比较与选择](../../apis/simd_api/basic_api/reg_vector_compute/compare_and_select/compare_and_select.md)（`exemplifies`）：Select VSEL_CMPMASK_SPR count>64 掩码错位判别说明arch35 Select 的 VSEL_CMPMASK_SPR 对 float 仅载首 repeat 的 selMask 并对所有 repeat 复用；count>64 时后续块套用首 64 元素块掩码，错误位置 pos%64 集中在 44/55/56，双向错取 linear/sigmoid 分支。判别：逐元素比对 golden 与 actual 求 pos%64 分布，n=15360 单完整 tile 复现排除 tile 边界。
- [arch35 分块 Select 掩码偏移非 32B 对齐崩溃 507035](../compilation/arch35_select_32b_507035.md)（`related`）：“Select VSEL_CMPMASK_SPR count>64 掩码错位判别”定义：arch35 Select 的 VSEL_CMPMASK_SPR 对 float 仅载首 repeat 的 selMask 并对所有 repeat 复用；count>64 时后续块套用首 64 元素块掩码，错误位置 pos%64 集中在 44/55/56，双向错取 linear/sigmoid 分支。判别：逐元素比对 golden 与 actual 求 pos%64 分布，n=15360 单完整 tile 复现排除 tile 边界。；“arch35 分块 Select 掩码偏移非 32B 对齐崩溃 507035”定义：为绕过 VselImpl 不偏移 sel 指针的问题，尝试分块 Select(SEL_CHUNK=64) 用 bMask[off>>3] 按 bitmask 偏移 mask 张量；第二块起 mask 源地址落 byte 8 非 32B 对齐，set_cmpmask 加载致 AIC runtime error 507035 崩溃。n=64 单块通过、n>=128 多块崩溃。banned 路线——对齐与 cmpmask 宽度约束互斥，无分块粒度可同时满足。。实质衔接：这些卡以 64 元素周期、VselImpl sel 不偏移和首块 mask 复用闭合同一根因；分块修复受 32B 对齐阻断，Select/SetCmpMask 文档给出消费契约。
- [Duplicate 全量清零 padding 覆盖有效区 banned](duplicate_padding_banned.md)（`same_topic`）：Duplicate 全量清零 padding 覆盖有效区 banned 与《Select VSEL_CMPMASK_SPR count>64 掩码错位判别》的实质衔接是：该故障同时受 Duplicate 无 offset 契约、Select 模式2 连续 mask 消耗和 padding 有效计数控制；所连卡都直接用于清理 padding 而不覆盖有效区或复现 cmpmask 污染。
- [Select CMPMASK_SPR 模式致混合分支误选](select_cmpmask_spr.md)（`same_topic`）：“Select VSEL_CMPMASK_SPR count>64 掩码错位判别”定义：arch35 Select 的 VSEL_CMPMASK_SPR 对 float 仅载首 repeat 的 selMask 并对所有 repeat 复用；count>64 时后续块套用首 64 元素块掩码，错误位置 pos%64 集中在 44/55/56，双向错取 linear/sigmoid 分支。判别：逐元素比对 golden 与 actual 求 pos%64 分布，n=15360 单完整 tile 复现排除 tile 边界。；“Select CMPMASK_SPR 模式致混合分支误选”定义：arch35(dav_c310) 高层 Select 用 VSEL_CMPMASK_SPR 时 set_cmpmask 不随 repeat 偏移 mask 指针，count 超过一个 repeat 的 64 个 fp32 元素时每 repeat 复用首 64bit mask 致混合分支误选；改 VSEL_TENSOR_TENSOR_MODE 后失败数由 116 降至 3 判明根因。。实质衔接：这些卡以 64 元素周期、VselImpl sel 不偏移和首块 mask 复用闭合同一根因；分块修复受 32B 对齐阻断，Select/SetCmpMask 文档给出消费契约。
- [Select cmpmask 不偏移致分支反转诊断](select_cmpmask.md)（`same_topic`）：“Select VSEL_CMPMASK_SPR count>64 掩码错位判别”定义：arch35 Select 的 VSEL_CMPMASK_SPR 对 float 仅载首 repeat 的 selMask 并对所有 repeat 复用；count>64 时后续块套用首 64 元素块掩码，错误位置 pos%64 集中在 44/55/56，双向错取 linear/sigmoid 分支。判别：逐元素比对 golden 与 actual 求 pos%64 分布，n=15360 单完整 tile 复现排除 tile 边界。；“Select cmpmask 不偏移致分支反转诊断”定义：arch35/dav_c100 上 Select(VSEL_CMPMASK_SPR) 在 count>128 时 L1 出现约 1.2% element mismatch 与 mask 分支反转；通过 n 规模扫描与 VselImpl 源码读取定位为 repeatRounding 循环中 sel 指针不偏移、后续 repeat 复用首块 cmpmask。。实质衔接：这些卡以 64 元素周期、VselImpl sel 不偏移和首块 mask 复用闭合同一根因；分块修复受 32B 对齐阻断，Select/SetCmpMask 文档给出消费契约。
- [arch35 Select VSEL_CMPMASK_SPR 每 64 元素复用](arch35_select_vsel_cmpmask_spr_mask_reuse_count_over_64.md)（`same_topic`）：“Select VSEL_CMPMASK_SPR count>64 掩码错位判别”定义：arch35 Select 的 VSEL_CMPMASK_SPR 对 float 仅载首 repeat 的 selMask 并对所有 repeat 复用；count>64 时后续块套用首 64 元素块掩码，错误位置 pos%64 集中在 44/55/56，双向错取 linear/sigmoid 分支。判别：逐元素比对 golden 与 actual 求 pos%64 分布，n=15360 单完整 tile 复现排除 tile 边界。；“arch35 Select VSEL_CMPMASK_SPR 每 64 元素复用”定义：arch35 Select 模式0 VSEL_CMPMASK_SPR 的 selMask 有效位限 256/sizeof(T)=64，多轮迭代复用同一 64bit 掩码，count>64 时元素 p 实际取 bit(p%64)，导致跨 64 元素块掩码错配，sigmoid 区元素被误判为线性分支返回 gradOutput。。实质衔接：这些卡以 64 元素周期、VselImpl sel 不偏移和首块 mask 复用闭合同一根因；分块修复受 32B 对齐阻断，Select/SetCmpMask 文档给出消费契约。
- [arch35 Select cmpmask SPR 跨调用泄漏致非确定失败](arch35_select_cmpmask_spr.md)（`same_topic`）：arch35 Select cmpmask SPR 跨调用泄漏致非确定失败 与《Select VSEL_CMPMASK_SPR count>64 掩码错位判别》的实质衔接是：这些卡都围绕 arch35 VSEL_CMPMASK_SPR 的生成、复用、偏移或跨调用污染；Set/GetCmpMask 是直接控制和观察该 SPR 状态的接口。
- [arch35 Select 异步SIMT同步失效致分支错选](arch35_select_simt.md)（`same_topic`）：arch35 Select 异步SIMT同步失效致分支错选 与《Select VSEL_CMPMASK_SPR count>64 掩码错位判别》的实质衔接是：该卡定位 arch35 VSEL_CMPMASK_SPR 在异步 VF/同步原语缺失下读取陈旧 mask；RAW、跨调用/超64复用、Compare/Select 和同步 API 是可执行区分机制。
- [arch35 Select 超64 cmpmask 残缺判别](arch35_select_64_cmpmask.md)（`same_topic`）：“Select VSEL_CMPMASK_SPR count>64 掩码错位判别”定义：arch35 Select 的 VSEL_CMPMASK_SPR 对 float 仅载首 repeat 的 selMask 并对所有 repeat 复用；count>64 时后续块套用首 64 元素块掩码，错误位置 pos%64 集中在 44/55/56，双向错取 linear/sigmoid 分支。判别：逐元素比对 golden 与 actual 求 pos%64 分布，n=15360 单完整 tile 复现排除 tile 边界。；“arch35 Select 超64 cmpmask 残缺判别”定义：arch35（DAV_3510）上 Compare 一次产生的 cmpmask 有效位限 256B/sizeof(T)=64（fp32）；kernel 把 count_padded（可达 1088+）一次性传给 Compare/Select(VSEL_CMPMASK_SPR) 时，超出 64 的 cmpmask 残缺/陈旧，Select 据残缺掩码对第 65+ 元素取错分支。判别=固定 threshold≈0、放大 count_padded 做边界实验，PASS/FAIL 边界恰在 64 即定位。。实质衔接：这些卡以 64 元素周期、VselImpl sel 不偏移和首块 mask 复用闭合同一根因；分块修复受 32B 对齐阻断，Select/SetCmpMask 文档给出消费契约。
- [arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染](arch35_vsel_cmpmask_spr_mask.md)（`same_topic`）：arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染 与《Select VSEL_CMPMASK_SPR count>64 掩码错位判别》的实质衔接是：该卡锁定标量/小 count 的 packed mask 仅写少量字节而 Select 载入 stale padding；跨调用、超64、RAW、Compare/Select、GetValue 与同步材料提供可执行区分。
<!-- cannbot:related:end -->
