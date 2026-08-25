---
type: "Runbook"
title: "Select CMPMASK_SPR 模式致混合分支误选"
description: "arch35(dav_c310) 高层 Select 用 VSEL_CMPMASK_SPR 时 set_cmpmask 不随 repeat 偏移 mask 指针，count 超过一个 repeat 的 64 个 fp32 元素时每 repeat 复用首 64bit mask 致混合分支误选；改 VSEL_TENSOR_TENSOR_MODE 后失败数由 116 降至 3 判明根因。"
tags: ["task.debugging", "topic.compute.elementwise.comparison_logic", "topic.implementation.api_layer.basic_api", "topic.precision"]
status: stable
sources: []
created_at: "2026-08-18T08:28:51Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# Select CMPMASK_SPR 模式致混合分支误选

## 现象

在 Ascend950PR（`__NPU_ARCH__==3510` → dispatcher 选中 `dav_c310` 变体，CANN cann-9.0.0-beta.2）上调试 `softplus_v2_grad` 反向算子 PyTorch ST。基线 `bash build.sh --soc=ascend950 -j8` 编译安装后跑 `python3 test.py --lib ./build/libtorch_adapter.so`，出现批量失败，形态集中在 L1 大 shape 用例：对应当取线性分支（`z > threshold`，应返回 grad_output）的元素，NPU 返回 `0.5*grad_output`（即 `sigmoid(0)*grad_output`），反之亦然。失败沿 tile 内 dim3 维度呈结构化分布（如 d3=8 仅 element0 错、d3=9 全错、d3=10 element1-8 错），形如 mask 数据在 repeat 间未偏移的"移位/复用"特征。

## 适用场景

- 工程形态：ops-registry-invoke（算子仓开发），kernel 直调 + aclnn L2。
- API 路径：`AscendC::Select<float, uint8_t>(dst, maskUb, src0, src1, SELMODE, count)` 高层向量选择 API；`AscendC::Compare` 生成 mask。
- 验证过的平台与 CANN 版本：Ascend950PR（`__NPU_ARCH__==3510` → `dav_c310`），CANN cann-9.0.0-beta.2。
- 适用粒度：`operator_family`（所有在 dav_c310/arch35 上用 `Select(...,count)` 高层 API 处理 count 超过一个 repeat 的混合分支的算子）。
- 不适用/未验证场景：dav_c100 / dav_c220 / dav_m200 等其他 `__NPU_ARCH__` 变体未验证。

## 判别方法

**trigger（触发）**：PyTorch ST 批量失败，失败形态为混合分支误选——大 shape 用例中本应取线性分支的元素返回了 sigmoid 分支值（`0.5*grad_output`），或反之；失败沿 dim3 呈结构化"移位/复用"分布。基线 `VSEL_CMPMASK_SPR` 模式下 116/578 失败（精确计数见 `## 验证信号`）。

**probe（可执行探针）**：将 kernel `ComputeFp32Core` 中 `Select` 调用的 SELMODE 常量从 `VSEL_CMPMASK_SPR` 改为 `VSEL_TENSOR_TENSOR_MODE`（仅 1 行常量替换），撤销此前任何手动分段，重跑 PyTorch ST：

```
python3 test.py --lib ./build/libtorch_adapter.so
```

若失败数从约 116 骤降至个位数（与本根因无关的极值 FTZ 残留），则判明根因为 CMPMASK_SPR 路径的 mask 偏移缺陷。

**observation（工具观测）**：改 MODE 后 PyTorch ST 失败数 116 降至 3（575/578 通过），C++ ST 57/57 通过，L0 功能用例 51/51 通过——模式替换直接消除了结构化混合分支误选，证实根因在 SELMODE 而非计算公式或数据布局。

**interpretation（根因解释）**：dav_c310 高层 `Select(...,count)` 在 `VSEL_CMPMASK_SPR` 路径中，`VselIntrinsicsImpl` 调用 `set_cmpmask(sel)` 把整段 mask 装入 CMPMASK SPR，但分块循环对 `sel`（mask 指针）不做偏移；因此当 count 超过一个 repeat 的 fp32 元素数（`ONE_REPEAT_ELE_NUM_FP32=64`）时，每个 repeat 复用首 64-bit mask，混合分支（部分 `z>thr`、部分 `z<=thr`）误选。改用 `VSEL_TENSOR_TENSOR_MODE` 后，mask 作为 tensor 参数传入，`VselImpl` 每 repeat 用 `sel + i*selOffset` 正确偏移，对任意 count 正确。注意变体查证：Ascend950PR 即 `__NPU_ARCH__==3510` 经 dispatcher 映射到 `dav_c310/`（支持 mode 2），而非 `dav_c100/`；误读变体会得到"arch35 仅支持 CMPMASK_SPR"的错误前提。

## 验证信号

- 基线（VSEL_CMPMASK_SPR）：PyTorch ST 578 用例 116 失败，混合分支误选（来源平台:950；证据等级:tool_observed）
- 改 MODE 为 VSEL_TENSOR_TENSOR_MODE（仅改 1 行常量）：PyTorch ST 575/578 通过（来源平台:950；证据等级:tool_observed）
- C++ ST（`bash run.sh --real`）：57/57 通过（来源平台:950；证据等级:tool_observed）
- L0 功能用例（`python3 test.py --level L0`）：51/51 通过（来源平台:950；证据等级:tool_observed）

## 失效边界

- dav_c100 / dav_c220 / dav_m200 等其他变体未验证；改 MODE 前须先确认目标变体经 dispatcher 映射且支持 `VSEL_TENSOR_TENSOR_MODE`（mode 2），不支持时改 MODE 会 assert false。
- 剩余 3 个失败（极值 `grad=+-FLT_MAX`、`z` 落次正规 exp 区间）与本根因无关，属硬件 FTZ，另行声明。

## 预防

- 开发期对照 `DESIGN.md` 检查"实现↔设计"的 SELMODE 偏差：DESIGN 指定 `VSEL_TENSOR_TENSOR_MODE` 而实现用 `VSEL_CMPMASK_SPR` 即高优先级假设。
- 在 dav_c310/arch35 上优先用 `VSEL_TENSOR_TENSOR_MODE`（mask 作为 tensor 参数，每 repeat 自动偏移）；仅当变体不支持 mode 2 时才退回 CMPMASK_SPR 并手动按 `ONE_REPEAT_ELE_NUM_FP32`(=64) 分段 Compare+Select。

<!-- cannbot:related:start -->
## 相关

- [AscSelect](../../apis/simd_api/c_api/reg/compare_and_select/asc_select.md)（`exemplifies`）：AscSelect：AscSelect 的 cmpmask 设置/读取和三输入别名约束直接决定结果；所选 runbook均针对该接口的 >64 掩码复用、跨调用残留、异步 RAW 或 dst/src 别名失效，而非泛化连接所有比较接口。 目标卡《Select CMPMASK_SPR 模式致混合分支误选》补充：arch35(dav_c310) 高层 Select 用 VSEL_CMPMASK_SPR 时 set_cmpmask 不随 repeat 偏移 mask 指针，count 超过一个 repeat 的 64 个 fp32 元素时每 repeat 复用首 64bit mask 致混合分支误选；改 VSEL_TENSOR_TENSOR_MODE 后失败数由 116 降至 3 判明根因。
- [GetCmpMask](../../apis/simd_api/basic_api/memory_vector_compute/compare_and_select/get_cmp_mask_isasi.md)（`exemplifies`）：《GetCmpMask》处理“获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果。”。《Select CMPMASK_SPR 模式致混合分支误选》明确提供“arch35(dav_c310) 高层 Select 用 VSEL_CMPMASK_SPR 时 set_cmpmask 不随 repeat 偏移 mask 指针，count 超过一个 repeat 的 64 个 fp32 元素时每 repeat 复用首 64bit mask 致混合分支误选；改 VSEL_TENSOR_TENSOR_MODE 后失败数由 116 降至 3 判明根因。”，其参数、调用或验证步骤直接接入GetCmpMask 对 CompareStoreToRegister 产出 mask 的读取和 Select 消费链。
- [Select](../../apis/simd_api/basic_api/memory_vector_compute/compare_and_select/select.md)（`exemplifies`）：Select 接口给出三种选择模式和 mask 分支语义，本卡用 mode 0 与 tensor mode 的单变量 A/B 验证多 repeat 行为差异。
- [Select](../../apis/simd_api/basic_api/reg_vector_compute/mask_reg_compute/select.md)（`exemplifies`）：《Select》的任务是“根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。”。《Select CMPMASK_SPR 模式致混合分支误选》具体提供“arch35(dav_c310) 高层 Select 用 VSEL_CMPMASK_SPR 时 set_cmpmask 不随 repeat 偏移 mask 指针，count 超过一个 repeat 的 64 个 fp32 元素时每 repeat 复用首 64bit mask 致混合分支误选；改 VSEL_TENSOR_TENSOR_MODE 后失败数由 116 降至 3 判明根因。”，它直接用于Reg Select 的 mask 来源、CMPMASK 生命周期、偏移、别名和跨调用污染。
- [SetCmpMask](../../apis/simd_api/basic_api/memory_vector_compute/compare_and_select/set_cmp_mask_isasi.md)（`exemplifies`）：SetCmpMask 接口说明 mask 被装入比较寄存器供不显式传 mask 的 Select 使用，正是本卡 CMPMASK_SPR repeat 复用的寄存器边界。
- [Duplicate 全量清零 padding 覆盖有效区 banned](duplicate_padding_banned.md)（`related`）：为清理 CMPMASK padding 而全量 Duplicate 会覆盖有效 gradOutput；目标卡否定这一绕过路线，补充本卡 MODE A/B 之外的修复边界。
- [arch35 Select cmpmask SPR 跨调用泄漏致非确定失败](arch35_select_cmpmask_spr.md)（`related`）：目标卡处理单 case 通过、套件失败的 CMPMASK SPR 跨调用残留；本卡处理单次大 count 的 repeat 内复用，两种相似误选需按触发维度区分。
- [arch35 Select 异步SIMT同步失效致分支错选](arch35_select_simt.md)（`related`）：目标卡提出 CMPMASK 设置与 vsel 的异步同步问题；本卡通过 selOffset 源码和 mod-64 失败结构锁定另一机制，二者是需用规模扫描和 barrier A/B 区分的候选根因。
- [arch35 count Compare Select 异步VF 存读 RAW](arch35_count_compare_select_vf_raw.md)（`related`）：目标卡定位 Compare 写 mask UB 到 Select 读 mask UB 的 VF RAW；本卡定位 SPR mode 内 repeat 指针不推进，barrier 是否改变失败可区分两条机制。
- [arch35 分块 Select 掩码偏移非 32B 对齐崩溃 507035](../compilation/arch35_select_32b_507035.md)（`related`）：手工按 64 分块规避本卡 mask 复用时，第二块 mask 地址可能落在 8B 而非 32B 对齐边界；目标卡记录该 workaround 的 507035 失败。
- [Select VSEL_CMPMASK_SPR count>64 掩码错位判别](select_vsel_cmpmask_spr_count_64.md)（`same_topic`）：“Select VSEL_CMPMASK_SPR count>64 掩码错位判别”定义：arch35 Select 的 VSEL_CMPMASK_SPR 对 float 仅载首 repeat 的 selMask 并对所有 repeat 复用；count>64 时后续块套用首 64 元素块掩码，错误位置 pos%64 集中在 44/55/56，双向错取 linear/sigmoid 分支。判别：逐元素比对 golden 与 actual 求 pos%64 分布，n=15360 单完整 tile 复现排除 tile 边界。；“Select CMPMASK_SPR 模式致混合分支误选”定义：arch35(dav_c310) 高层 Select 用 VSEL_CMPMASK_SPR 时 set_cmpmask 不随 repeat 偏移 mask 指针，count 超过一个 repeat 的 64 个 fp32 元素时每 repeat 复用首 64bit mask 致混合分支误选；改 VSEL_TENSOR_TENSOR_MODE 后失败数由 116 降至 3 判明根因。。实质衔接：这些卡以 64 元素周期、VselImpl sel 不偏移和首块 mask 复用闭合同一根因；分块修复受 32B 对齐阻断，Select/SetCmpMask 文档给出消费契约。
- [Select cmpmask 不偏移致分支反转诊断](select_cmpmask.md)（`same_topic`）：两卡均从 VselImpl 的 repeat 循环确认 sel 指针不偏移，导致 count 超过 64 个 fp32 元素后复用首块 CMPMASK 并反转混合分支。
- [arch35 Select VSEL_CMPMASK_SPR 每 64 元素复用](arch35_select_vsel_cmpmask_spr_mask_reuse_count_over_64.md)（`same_topic`）：目标卡用 `bit(p%64)` 精确表达每 64 元素复用，本卡用 116→3 的 MODE A/B 闭环验证同一 CMPMASK_SPR repeat 偏移缺陷。
- [arch35 Select 超64 cmpmask 残缺判别](arch35_select_64_cmpmask.md)（`same_topic`）：目标卡确认一次 Compare 产生的有效 mask 只覆盖 64 个 fp32 lane，本卡说明 Select 循环未推进 sel 后为何会反复消费这 64 位。
- [arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染](arch35_vsel_cmpmask_spr_mask.md)（`same_topic`）：arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染 与《Select CMPMASK_SPR 模式致混合分支误选》的实质衔接是：该卡锁定标量/小 count 的 packed mask 仅写少量字节而 Select 载入 stale padding；跨调用、超64、RAW、Compare/Select、GetValue 与同步材料提供可执行区分。
<!-- cannbot:related:end -->
