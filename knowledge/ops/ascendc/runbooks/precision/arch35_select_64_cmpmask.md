---
type: "Runbook"
title: "arch35 Select 超64 cmpmask 残缺判别"
description: "arch35（DAV_3510）上 Compare 一次产生的 cmpmask 有效位限 256B/sizeof(T)=64（fp32）；kernel 把 count_padded（可达 1088+）一次性传给 Compare/Select(VSEL_CMPMASK_SPR) 时，超出 64 的 cmpmask 残缺/陈旧，Select 据残缺掩码对第 65+ 元素取错分支。判别=固定 threshold≈0、放大 count_padded 做边界实验，PASS/FAIL 边界恰在 64 即定位。"
tags: ["task.debugging", "topic.precision", "topic.implementation.masking", "topic.compute.elementwise.comparison_logic"]
status: stable
sources: []
created_at: "2026-08-18T05:29:39Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# arch35 Select 超64 cmpmask 残缺判别

## 现象

`softplus_v2_grad`（arch35/DAV_3510，Ascend950PR）在修好 host 侧 scalar 缓存键后仍有批量非 scalar 用例失败，且**单跑也失败**（排除 tiling 缓存嫌疑），属真实 kernel 精度 bug。代表用例（fp32，threshold≈-1.18e-38 即≈0 负，5D 广播 shape）逐元素比对观测到 Select 取错分支：

- 某 sigmoid 分支元素（bx<threshold，应 mask=false→src1=grad_sig）：实测 actual=gradOutput，即 kernel 走了**线性分支**（mask=true→src0=gradOutput）。
- 某线性分支元素（bx>threshold，应 mask=true→src0=gradOutput）：实测 actual=gradOutput*0.5，即 kernel 走了 **sigmoid 分支**（mask=false→src1=grad_sig）。

合看即 Select 在 mask=true 时返回 src1、mask=false 时返回 src0，与语义完全反了。但 threshold=20.0 时不复现，故不是 Select 语义写反，而是 cmpmask 在大 count 下被错误填充。

## 适用场景

- **工程形态**：kernel 直调（op_kernel），AscendC SIMD 基础 API `Compare`/`Select`。
- **API 路径**：`AscendC::Compare<float, uint8_t>(dst, src0, src1, CMPMODE::GT, count)` + `AscendC::Select<float, uint8_t>(dst, mask, src0, src1, SELMODE::VSEL_CMPMASK_SPR, count)`，arch35（DAV_3510 系）。
- **验证过的平台与 CANN 版本**：Ascend950PR（注册平台 `950`），CANN 9.0.0-beta.2，arch 目录 arch35。
- **适用粒度**：`platform_wide`——arch35 上一切用 `Compare`/`Select(VSEL_CMPMASK_SPR)` 且 count 可能超 64 的 kernel 都受 cmpmask 单 repeat 容量约束。
- **路线优先级**：`diagnostic_only`——本卡只给判别方法与根因解释；分块循环修复的终版 verbatim 代码未从 trace 逐字恢复。
- **明确不适用/未验证场景**：非 arch35 架构（arch22/a2/a3 的 ONE_REPEAT_ELE_NUM 可能不同，未验证）；count 恒 ≤ 64 的 kernel 不触发；不经 `VSEL_CMPMASK_SPR`（其他 SELMODE）的 Select 不适用本根因。

## 根因

arch35 上 `Compare` 一次产生 cmpmask 的容量 = `ONE_REPEAT_ELE_NUM_FP32 = 256B / 4B = 64` 位（一个 vector repeat 的 fp32 元素数）。`Select` 以 `VSEL_CMPMASK_SPR` 模式工作时按 cmpmask 位选分支。本算子 kernel 把 `count_padded`（按 64 对齐、但可达 1088+）**一次性**传给 `Compare`/`Select`：`Compare(count_padded)` 只正确填了前 64 位 cmpmask，**超出 64 的部分 cmpmask 是陈旧/未定义**；`Select(count_padded)` 据这份残缺 cmpmask 选分支，对第 65+ 元素取错 src。threshold≈0 时 mask 高度敏感（bx 正负微小差异即翻 mask），错分支被放大成可见 mismatch；threshold=20.0 时绝大多数 bx ≪ threshold、mask 几乎恒定，即便 cmpmask 残缺也"碰巧"取对，故不复现——这也是为何本 bug 长期潜伏、只在极端 threshold 触发。参照：CANN 内置 `hard_swish_grad_v2` 在同 arch35 上显式按 `ONE_REPEAT_ELE_NUM_FP32=64` 分块循环 Compare 与 Select，即正确写法。

## 判别方法

本规则按"触发 → 探针 → 观测 → 判别"四段组织；触发与观测均为 trace 中 tool_observed 的测试/边界实验输出。

1. **触发（tool_observed 失败症状）**：逐元素比对发现 Select 在 mask=true 时返回 src1、mask=false 时返回 src0（与语义相反），但仅当 threshold≈0 且 count_padded>64 时出现；threshold=20.0 或 count_padded≤64 时不出现。即命中本规则。

2. **探针（可执行检查）**：固定 threshold≈0（构造极小负 threshold，使 mask 对 bx 正负微小差异高度敏感），逐步放大 shape 使 count_padded 跨越 64：分别取 numel=6/count_padded=64、numel=64/count_padded=64、numel=120/count_padded=128、numel=256/count_padded=256，跑同 kernel 比对 actual vs golden。再做 threshold=20.0 对照（绝大多数 bx ≪ threshold、mask 近恒定）。

3. **观测（tool_observed 边界实验，Ascend950PR/arch35）**：
   - count_padded=64（numel=6 或 64）→ **PASS**；
   - count_padded=128（numel=120）→ **FAIL**（出现 mismatch）；
   - count_padded=256（numel=256）→ **FAIL**（mismatch 更多）。
   - 边界恰在 64：count_padded ≤ 64 通过、> 64 失败。threshold=20.0 对照下不复现。

4. **判别（interpretation，根因分析）**：若 PASS/FAIL 边界恰落在 `ONE_REPEAT_ELE_NUM = 256B/sizeof(elem)`（fp32=64），根因是 cmpmask 单 repeat 容量受限——`Compare(count>容量)` 只填前若干位、`Select(VSEL_CMPMASK_SPR)` 据残缺掩码对超容元素取错分支，**而非 Select 语义写反也非 FTZ**。判别核心是 count 边界实验 + threshold 对照：边界在 64 + threshold≈0 才复现 → cmpmask 残缺；若无论 count 都反 → 语义写反；若仅极端值翻转 → 疑 FTZ。正确修复方向是按 `ONE_REPEAT_ELE_NUM` 分块循环 Compare/Select（或改用不依赖 cmpmask 的 SELMODE），而不是交换 src0/src1 强行对齐。

## 预防

- arch35 上凡用 `Compare`/`Select(VSEL_CMPMASK_SPR)` 处理变长数据，**一律**按 `ONE_REPEAT_ELE_NUM_FP32=64`（或对应 dtype 的 `256B/sizeof(elem)`）分块循环，不要把 `count_padded` 一次性传进去。
- 写 kernel 时若 Select 语义"看起来反了"，先别急着交换 src0/src1——先查 cmpmask 是否因 count 超容而残缺；用 threshold=20.0 vs threshold≈0 的对照实验可快速区分"语义写反"与"cmpmask 残缺"。
- 对照 CANN 内置 `hard_swish_grad_v2`（同 arch35）的分块写法作为参照正确实现。

## 验证信号

- 边界实验：threshold≈0 时 count_padded=64 PASS、count_padded=128 FAIL、count_padded=256 FAIL，PASS/FAIL 边界恰在 64（来源平台:950；证据等级:tool_observed）。
- 修复（Compare/Select 按 `ALIGN_ELEMENTS=64` 分块循环）后 PyTorch ST 通过数 498→565/581（来源平台:950；证据等级:tool_observed）。
- 修复后 C++ ST 57/57 通过、无回归（来源平台:950；证据等级:tool_observed）。

## 失效边界

- **平台**：本 trace 只在 Ascend950PR（`950`、arch35）实测。a2/a3（arch22/DAV_2201）的 `ONE_REPEAT_ELE_NUM` 可能不同，**未验证，推断可迁移**——迁移时须按目标 arch 重算 `256B/sizeof(elem)` 后再定块大小，不可直接照搬 64。
- **dtype**：本卡只测 fp32（64 元素/块）。fp16/bf16 的块大小应为 `256B/2B=128`，int8 为 256——未实测，按算式推导。
- **边界**：count 恒 ≤ 块大小的 kernel 不触发本 bug；不经 `VSEL_CMPMASK_SPR`（如用其他 SELMODE）的 Select 不适用本根因。

## 坏实践

- 看到 Select"取反"就直接交换 src0/src1 参数强行对齐——掩盖 cmpmask 残缺真因，且 threshold=20.0 时会从"错"变"对反再反=碰巧对"，回归隐患极大。
- 把 `count_padded` 当成"已对齐就安全"——对齐只保证是 64 的倍数，不保证 ≤ 64；count_padded=128 是 64 的倍数但仍超容。

## 误诊

早期一度怀疑 Select 语义写反或 FTZ 把 threshold flush 到 0 导致 mask 翻转。但算式核验：threshold=-1.18e-38 即便 FTZ 成 0，对 bx=-0.5953 的 mask 仍是 false、与"取反"表现一致但解释不了 count=64 通过/128 失败的边界。真因是 cmpmask 单 repeat 容量 64，非语义反也非 FTZ（来源平台:950；证据等级:agent_reported——此为排除性推理，非实测信号）。

<!-- cannbot:related:start -->
## 相关

- [AscSelect](../../apis/simd_api/c_api/reg/compare_and_select/asc_select.md)（`exemplifies`）：AscSelect：AscSelect 的 cmpmask 设置/读取和三输入别名约束直接决定结果；所选 runbook均针对该接口的 >64 掩码复用、跨调用残留、异步 RAW 或 dst/src 别名失效，而非泛化连接所有比较接口。 目标卡《arch35 Select 超64 cmpmask 残缺判别》补充：arch35（DAV_3510）上 Compare 一次产生的 cmpmask 有效位限 256B/sizeof(T)=64（fp32）；kernel 把 count_padded（可达 1088+）一次性传给 Compare/Select(VSEL_CMPMASK_SPR) 时，超出 64 的 cmpmask 残缺/陈旧，Select 据残缺掩码对第 65+ 元素取错分支。判别=固定 threshold≈0、放大 count_padd
- [GetCmpMask](../../apis/simd_api/basic_api/memory_vector_compute/compare_and_select/get_cmp_mask_isasi.md)（`exemplifies`）：《GetCmpMask》处理“获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果。”。《arch35 Select 超64 cmpmask 残缺判别》明确提供“arch35（DAV_3510）上 Compare 一次产生的 cmpmask 有效位限 256B/sizeof(T)=64（fp32）；kernel 把 count_padded（可达 1088+）一次性传给 Compare/Select(VSEL_CMPMASK_SPR) 时，超出 64 的 cmpmask 残缺/陈旧，Select 据残缺掩码对第 65+ 元素取错分支。判别=固定 threshold≈0、放大 count_padded 做边界实验，PASS/FAIL 边界恰在 64 即定位。”，其参数、调用或验证步骤直接接入GetCmpMask 对 CompareStoreToRegister 产出 mask 的读取和 Select 消费链。
- [Select](../../apis/simd_api/basic_api/reg_vector_compute/compare_and_select/select.md)（`exemplifies`）：arch35 Select 超64 cmpmask 残缺判别说明arch35（DAV_3510）上 Compare 一次产生的 cmpmask 有效位限 256B/sizeof(T)=64（fp32）；kernel 把 count_padded（可达 1088+）一次性传给 Compare/Select(VSEL_CMPMASK_SPR) 时，超出 64 的 cmpmask 残缺/陈旧，Select 据残缺掩码对第 65+ 元素取错分支。判别=固定 threshold≈0、放大 count_padded 做边界实验，PASS/FAIL 边界恰在 64 即定位。
- [Select](../../apis/simd_api/basic_api/reg_vector_compute/mask_reg_compute/select.md)（`exemplifies`）：《Select》的任务是“根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。”。《arch35 Select 超64 cmpmask 残缺判别》具体提供“arch35（DAV_3510）上 Compare 一次产生的 cmpmask 有效位限 256B/sizeof(T)=64（fp32）；kernel 把 count_padded（可达 1088+）一次性传给 Compare/Select(VSEL_CMPMASK_SPR) 时，超出 64 的 cmpmask 残缺/陈旧，Select 据残缺掩码对第 65+ 元素取错分支。判别=固定 threshold≈0、放大 count_padded 做边界实验，PASS/FAIL 边界恰在 64 即定位。”，它直接用于Reg Select 的 mask 来源、CMPMASK 生命周期、偏移、别名和跨调用污染。
- [比较与选择](../../apis/simd_api/basic_api/reg_vector_compute/compare_and_select/compare_and_select.md)（`exemplifies`）：arch35 Select 超64 cmpmask 残缺判别说明arch35（DAV_3510）上 Compare 一次产生的 cmpmask 有效位限 256B/sizeof(T)=64（fp32）；kernel 把 count_padded（可达 1088+）一次性传给 Compare/Select(VSEL_CMPMASK_SPR) 时，超出 64 的 cmpmask 残缺/陈旧，Select 据残缺掩码对第 65+ 元素取错分支。判别=固定 threshold≈0、放大 count_padded 做边界实验，PASS/FAIL 边界恰在 64 即定位。
- [arch35 Select cmpmask SPR 跨调用泄漏致非确定失败](arch35_select_cmpmask_spr.md)（`related`）：该卡覆盖 case 单跑通过、套件批跑失败的跨调用 CMPMASK 残留，与单次调用内超 64 复用形成独立诊断分支。
- [arch35 count Compare Select 异步VF 存读 RAW](arch35_count_compare_select_vf_raw.md)（`related`）：该卡证明 count-based Compare 写 UB mask 到 Select 读回之间还可能存在 VEC_STORE→VEC_LOAD RAW，可用 GetValue 探针与周期错位模式区分。
- [arch35 分块 Select 掩码偏移非 32B 对齐崩溃 507035](../compilation/arch35_select_32b_507035.md)（`related`）：该卡验证按 64 元素切 mask 的直觉修复会令第二块地址落到 byte 8、违反 32B 对齐并触发 507035，明确该补救路线不可用。
- [Duplicate 全量清零 padding 覆盖有效区 banned](duplicate_padding_banned.md)（`same_topic`）：Duplicate 全量清零 padding 覆盖有效区 banned 与《arch35 Select 超64 cmpmask 残缺判别》的实质衔接是：该故障同时受 Duplicate 无 offset 契约、Select 模式2 连续 mask 消耗和 padding 有效计数控制；所连卡都直接用于清理 padding 而不覆盖有效区或复现 cmpmask 污染。
- [Select CMPMASK_SPR 模式致混合分支误选](select_cmpmask_spr.md)（`same_topic`）：目标卡确认一次 Compare 产生的有效 mask 只覆盖 64 个 fp32 lane，本卡说明 Select 循环未推进 sel 后为何会反复消费这 64 位。
- [Select VSEL_CMPMASK_SPR count>64 掩码错位判别](select_vsel_cmpmask_spr_count_64.md)（`same_topic`）：“Select VSEL_CMPMASK_SPR count>64 掩码错位判别”定义：arch35 Select 的 VSEL_CMPMASK_SPR 对 float 仅载首 repeat 的 selMask 并对所有 repeat 复用；count>64 时后续块套用首 64 元素块掩码，错误位置 pos%64 集中在 44/55/56，双向错取 linear/sigmoid 分支。判别：逐元素比对 golden 与 actual 求 pos%64 分布，n=15360 单完整 tile 复现排除 tile 边界。；“arch35 Select 超64 cmpmask 残缺判别”定义：arch35（DAV_3510）上 Compare 一次产生的 cmpmask 有效位限 256B/sizeof(T)=64（fp32）；kernel 把 count_padded（可达 1088+）一次性传给 Compare/Select(VSEL_CMPMASK_SPR) 时，超出 64 的 cmpmask 残缺/陈旧，Select 据残缺掩码对第 65+ 元素取错分支。判别=固定 threshold≈0、放大 count_padded 做边界实验，PASS/FAIL 边界恰在 64 即定位。。实质衔接：这些卡以 64 元素周期、VselImpl sel 不偏移和首块 mask 复用闭合同一根因；分块修复受 32B 对齐阻断，Select/SetCmpMask 文档给出消费契约。
- [Select cmpmask 不偏移致分支反转诊断](select_cmpmask.md)（`same_topic`）：候选用超过 64 个元素的边界定位掩码残缺，本卡观测 n=129 起失败且约 64 元素周期。
- [arch35 Select VSEL_CMPMASK_SPR 每 64 元素复用](arch35_select_vsel_cmpmask_spr_mask_reuse_count_over_64.md)（`same_topic`）：该卡验证 64 个 b32 lane 是一次安全上限，给出将循环按 64 分段的修复边界，与 focal 的 over-64 失真完全互补。
- [arch35 Select 异步SIMT同步失效致分支错选](arch35_select_simt.md)（`same_topic`）：arch35 Select 异步SIMT同步失效致分支错选 与《arch35 Select 超64 cmpmask 残缺判别》的实质衔接是：该卡定位 arch35 VSEL_CMPMASK_SPR 在异步 VF/同步原语缺失下读取陈旧 mask；RAW、跨调用/超64复用、Compare/Select 和同步 API 是可执行区分机制。
- [arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染](arch35_vsel_cmpmask_spr_mask.md)（`same_topic`）：arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染 与《arch35 Select 超64 cmpmask 残缺判别》的实质衔接是：该卡锁定标量/小 count 的 packed mask 仅写少量字节而 Select 载入 stale padding；跨调用、超64、RAW、Compare/Select、GetValue 与同步材料提供可执行区分。
<!-- cannbot:related:end -->
