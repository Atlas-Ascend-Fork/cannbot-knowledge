---
type: "Runbook"
title: "Maxs 下限 clamp 阻止 exp 自然下溢残留"
description: "sigmoid 类算子 grad 分支对 exp 输入做 Maxs(bx,-50) 下限 clamp 会阻止 z 极负时 exp(z) 自然下溢为 0，残留 exp(-50)≈1.9e-22 与 FLT_MAX 量级 grad 相乘得可见非零偏差，而 golden=0。判别要点是 exp 输入的下限 clamp 与大 grad 的乘积放大。"
tags: ["task.debugging", "topic.precision", "topic.compute.elementwise.math_function", "topic.compute.elementwise.activation"]
status: stable
sources: []
created_at: "2026-08-15T00:00:00Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# Maxs 下限 clamp 阻止 exp 自然下溢残留

## 现象

在 `softplus_v2_grad` 算子（arch35/DAV_3510，Ascend950PR）修复 Select 掩码错配之后，仍有部分失败用例的 sigmoid 分支元素 `actual≠golden`。L1_018 case（grad=FLT_MAX，self 在 [-100,100]，beta=17.0095，threshold=0.00401）中，z=beta*self=-506.5 的 sigmoid 分支元素 `actual=FLT_MAX`（线性分支值），`golden=0`（sigmoid 下溢，grad*0=0）。逐元素探针定位到 z 极负区间。

## 判别方法

### 触发

sigmoid 类算子的 grad 分支中，当 z 极负（z 远小于 -50）且 grad 量级极大（如 FLT_MAX）时，`actual≠golden`：actual 为大正值（FLT_MAX 或 FLT_MAX 乘小残差），golden=0（exp(z) 自然下溢为 0，grad*0=0）。触发信号：精度失败集中在 sigmoid 分支的极负 z 元素，且 grad 量级极大。

### 探针

1. 对 failing case 构造逐元素比对脚本：枚举每个元素的 self、z=beta*self、actual、golden，筛选 `actual≠golden` 的索引，打印 z 值与分支归属。
2. 检查 kernel 的 exp 输入是否做了下限 clamp：若存在 `Maxs(bx, <负下限>)` 模式，且 z 极负时该 clamp 活跃（z 小于下限），则 clamp 把 exp(z) 的自然下溢路径阻断。
3. 验证 exp 在目标平台的下溢行为：确认默认 INTRINSIC 模式下 exp(极负值)→0（FTZ），即不 clamp 时 exp(z) 自然下溢为 0。

### 观测

- L1_018 idx=67（z=-506.5）：actual=FLT_MAX，golden=0。z 极负，sigmoid 分支，golden 期望 exp 下溢→sigmoid=0→grad*0=0。
- 单独移除下限 clamp 后复查同一 case：idx=67 仍 actual=FLT_MAX、golden=0（与公式顺序变更同批应用，联合改善未单独隔离）。
- PyTorch ST 总通过数 565→568/578（联合改进，未单独隔离）。

### 判别

根因是 `Maxs(bx, -50.0)` 下限 clamp 阻止了 exp(z) 的自然下溢。机制链：z 极负（如 -506）→ `Maxs` 钳到 -50 → `exp(-50)≈1.9e-22`（非零正常数，非 subnormal）→ `sigmoid(-50)≈1.9e-22` → `grad_sig=FLT_MAX*1.9e-22≈6.5e16`（非零）→ 与 golden=0 不符。数学关系：`FLT_MAX(3.4e38) × exp(-50)(1.9e-22) ≈ 6.5e16`，远超容差。下限 clamp 只在"需要保留 subnormal/小正常数信号"时才有意义；若 exp(z) 自然下溢为 0 是期望行为（grad*0=0 与 golden 一致），则不应加下限 clamp，仅保留防正向溢出的上限 clamp（如 `Mins(bx, 50.0)` 防 exp(89)=inf）。

## 适用场景

- **工程形态**：kernel 实现（op_kernel/arch35/*.h），sigmoid 类算子的 grad 分支数值实现。
- **API 路径**：`AscendC::Maxs` / `AscendC::Mins` / `AscendC::Exp` 向量 API。
- **验证平台与版本**：Ascend950PR（arch35/DAV_3510），CANN 9.0.0-beta.2。
- **适用粒度**：`operator_family`（所有含 sigmoid/softplus 类分支、对 exp 输入做下限 clamp 的 kernel）。
- **路线优先级**：`recommended_fastpath`（移除下限 clamp，仅保留防正向溢出的上限 clamp）。
- **不适用或未验证场景**：grad 量级正常（非 FLT_MAX）时残差影响可忽略；非 sigmoid 分支（纯线性）无此问题。

## 验证信号

- L1_018 idx=67（z=-506.5）sigmoid 分支：actual=FLT_MAX，golden=0（来源平台：950；证据等级：tool_observed）
- 修复后 PyTorch ST 565→568/578（联合改进，未单独隔离）（来源平台：950；证据等级：tool_observed）

## 预防

- sigmoid/softplus 类分支对 exp 输入做下限 clamp 时，必须评估 `exp(clamp_lower)` 残差与大 grad 相乘的可见偏差。
- 判断是否需要下限 clamp：若 `exp(z)` 自然下溢为 0 是期望行为（`grad*0=0` 与 golden 一致），则不加下限 clamp；下限 clamp 只在需要保留 subnormal/小正常数信号时有意义，且需评估与大 grad 相乘的后果。

## 失效边界

- Ascend950PR/arch35 实测；grad 量级正常时 `Maxs(-50)` 残差影响可忽略，移除与否无差。
- 与公式顺序变更（aten `grad*exp(z)/(1+exp(z))`）同批应用，独立信号未隔离；若仅移除 clamp 而不改公式顺序，改善量可能不同。
- 非 arch35 平台（a2/a3）未验证，推断可迁移。

<!-- cannbot:related:start -->
## 相关

- [ClampMin](../../apis/simd_api/adv_api/math_compute/clamp_interface/clamp_min.md)（`exemplifies`）：《ClampMin》说明将srcTensor中小于scalar的数替换为scalar，大于等于scalar的数保持不变，作为dstTensor输出。；《Maxs 下限 clamp 阻止 exp 自然下溢残留》说明sigmoid 类算子 grad 分支对 exp 输入做 Maxs(bx,-50) 下限 clamp 会阻止 z 极负时 exp(z) 自然下溢为 0，残留 exp(-50)≈1.9e-22 与 FLT_MAX 量级 grad 相乘得可见非零偏差，而 golden=0。判别要点是 exp 输入的下限 clamp 与大 grad 的乘积放大。。二者在ClampMin与ClampMax共同定义上下界替换，workspace查询决定分块，exp下溢故障则直接验证错误下界的数值后果上存在可执行的直接衔接。
- [Clamp（数学计算）](../../apis/simd_api/adv_api/math_compute/clamp_interface/clamp.md)（`exemplifies`）：《Clamp（数学计算）》说明将输入中除nan值以外大于max的数替换为max，小于min的数替换为min，小于等于max和大于等于min的数保持不变，作为输出。当min大于max时，将除nan值外所有值替换为max。min和max可以为标量或LocalTensor。；《Maxs 下限 clamp 阻止 exp 自然下溢残留》说明sigmoid 类算子 grad 分支对 exp 输入做 Maxs(bx,-50) 下限 clamp 会阻止 z 极负时 exp(z) 自然下溢为 0，残留 exp(-50)≈1.9e-22 与 FLT_MAX 量级 grad 相乘得可见非零偏差，而 golden=0。判别要点是 exp 输入的下限 clamp 与大 grad 的乘积放大。。二者在Clamp、ClampMin/Max及workspace查询共享上下界替换合同，exp相关故障直接说明错误clamp边界对数值的影响上存在可执行的直接衔接。
- [Exp](../../apis/simd_api/adv_api/math_compute/exp_interface/exp.md)（`exemplifies`）：Exp 与《Maxs 下限 clamp 阻止 exp 自然下溢残留》的实质衔接是：这些卡直接给出 Exp 的高阶、基础、Reg 与 C 入口及其临时空间契约；所连排障卡均以 Exp 的溢出、下溢、FTZ 或 clamp 行为作为精度根因和修复对象。
- [Maxs](../../apis/simd_api/basic_api/memory_vector_compute/basic_arithmetic/maxs.md)（`exemplifies`）：Maxs 与《Maxs 下限 clamp 阻止 exp 自然下溢残留》的实质衔接是：Maxs 是 tensor 与标量逐元素取大值；Reg/灵活标量入口保持同一契约，Mins/Relu/LeakyRelu 以及 exp clamp 案例说明它在分段和限幅公式中的实际组合。
- [Maxs](../../apis/simd_api/basic_api/reg_vector_compute/basic_arithmetic/maxs.md)（`exemplifies`）：Maxs 与《Maxs 下限 clamp 阻止 exp 自然下溢残留》的实质衔接是：Reg Maxs 是 vector-scalar 下限 clamp，Mins/Max/其他层级 Maxs 对照操作数形态；Exp/FTZ/sigmoid 卡直接验证 clamp 阈值改变数值尾部。
- [Mins](../../apis/simd_api/basic_api/memory_vector_compute/basic_arithmetic/mins.md)（`exemplifies`）：Mins 与《Maxs 下限 clamp 阻止 exp 自然下溢残留》的实质衔接是：Mins 是 tensor 与标量逐元素取小值；Reg/灵活标量入口保持同一契约，Maxs/Min/Relu 组合及 exp clamp 案例说明它作为上界限幅的实际语义。
- [Exp 默认 INTRINSIC FTZ 致 subnormal 残留失配](exp_intrinsic_ftz_subnormal.md)（`related`）：移除下界 clamp 后，大负 z 会进入真实下溢路径；该卡进一步区分正常下溢与 (-104,-87) 次正规区间的 INTRINSIC FTZ 残留失败，防止把硬件边界误判为 clamp 未修。
- [SoftplusV2Grad VF Form B exp 溢出判别](softplusv2grad_vf_form_b_exp.md)（`related`）：SoftplusV2Grad VF Form B exp 溢出判别 与《Maxs 下限 clamp 阻止 exp 自然下溢残留》的衔接是：这些案例都直接围绕 exp/sigmoid 的溢出、下溢、FTZ、clamp 上下界或倒数精度；它们能区分 Form B 的正大输入溢出与其他极值失配根因。
- [softplus_v2_grad 极值 inf 发散源于 aten 乘除顺序](softplus_v2_grad_inf_aten.md)（`related`）：下界 clamp 修复只处理 z 极负残差；正/小正 z 的极值还受 aten 先 grad*exp 后除的溢出顺序影响，该卡提供互不重叠的另一诊断分支。
- [Ascend950 向量管 FTZ 刷新次正规 exp 为零](ascend950_ftz_exp.md)（`same_topic`）：Ascend950 向量管 FTZ 刷新次正规 exp 为零 与《Maxs 下限 clamp 阻止 exp 自然下溢残留》的实质衔接是：该卡锁定 Ascend950 Exp 次正规输出 FTZ；Exp 接口、clamp/overflow/subnormal 姊妹故障和 softplus 极值用例共同验证硬件边界与可修软件因素。
- [arch35 sigmoid 大负 z 下 exp 溢出 inf 致 sig=0](arch35_sigmoid_z_exp_inf_sig_0.md)（`same_topic`）：arch35 sigmoid 大负 z 下 exp 溢出 inf 致 sig=0 与《Maxs 下限 clamp 阻止 exp 自然下溢残留》的实质衔接是：该 sigmoid 失败由 exp(-z) 溢出和 subnormal FTZ 共同造成；Exp/Reciprocal/Clamp 接口及同类数值故障分别提供溢出阈值、稳定式和直接除法验证边界。
- [exp 下界 clamp -50 破坏 sigmoid 大负数下溢](exp_clamp_50_sigmoid.md)（`same_topic`）：两卡定位同一 SoftplusV2Grad 根因：Maxs(z,-50) 把应自然下溢为 0 的大负 z 抬到 exp(-50)，再被 FLT_MAX grad 放大；该卡还给出 6.56e16 指纹与移除 Maxs 后回归。
- [exp 输入 clamp 上界用 threshold 用户参数致溢出](exp_clamp_upper_bound_must_decouple_from_user_threshold.md)（`same_topic`）：exp 输入 clamp 上界用 threshold 用户参数致溢出 与《Maxs 下限 clamp 阻止 exp 自然下溢残留》的实质衔接是：故障由用户 threshold 充当 Exp 安全上界导致；Exp、Clamp/Mins、Sigmoid 公式及溢出/FTZ/Softplus 分支案例共同限定固定上界和极值验收。
<!-- cannbot:related:end -->
