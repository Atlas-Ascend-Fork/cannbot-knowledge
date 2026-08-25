---
type: "Runbook"
title: "exp 下界 clamp -50 破坏 sigmoid 大负数下溢"
description: "SoftplusV2Grad kernel 对 exp 输入做 max(bx,-50) 下界 clamp，把大负数 z 的 exp(z)→0 正确下溢值抬高为 exp(-50)≈1.9e-22，gradOutput 大时被放大；判别：NPU 输出≈gradOutput×exp(-50) 即命中下界 clamp bug。"
tags: ["task.debugging", "topic.precision", "topic.compute.elementwise.activation", "topic.compute.elementwise.math_function"]
status: stable
sources: []
created_at: "2026-08-15T00:00:00Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# exp 下界 clamp -50 破坏 sigmoid 大负数下溢

## 现象

在 Ascend950PR 上为 `softplus_v2_grad` 做精度回归（golden=`torch.ops.aten.softplus_backward`，fp32 atol=1.22e-4/rtol=1.22e-3）。部分 L1 case 失败，特征为 `self`（即 `z=beta*self`）为大负数且 `gradOutput` 幅值很大时，NPU 输出远大于 golden=0。

最小复现：`z = beta*self = -1105`，`gradOutput = 3.4e38`（接近 FLT_MAX）。golden = `gradOutput * sigmoid(z) = 3.4e38 * 0 = 0`（sigmoid 在大负数处下溢为 0）。NPU 输出 `6.56e16`，正好等于 `gradOutput × exp(-50) ≈ 3.4e38 × 1.9e-22 ≈ 6.5e16`——即 exp 输入被 clamp 到 -50 后，`exp(-50)≈1.9e-22` 本应下溢为 0，却被人为抬高，再乘大 gradOutput 放大成可见误差。

## 适用场景

- **工程形态**：kernel 直调（RegBase，op_kernel/arch35 路径）。
- **API 路径**：`AscendC::Maxs`/`AscendC::Mins`（逐元素标量 clamp）/`AscendC::Exp`/`AscendC::Div`/`AscendC::Mul` 构成的 sigmoid 分支。
- **验证平台与版本**：Ascend950PR，CANN cann-9.0.0-beta.2。
- **适用粒度**：`operator_family`——任何含 `sigmoid/exp` 分支且对 exp 输入做下界 clamp 的算子（softplus 家族、sigmoid 相关 grad）。
- **路线优先级**：`recommended_fastpath`——移除无数学必要性的 exp 下界 clamp。
- **不适用/未验证场景**：上界 clamp（防 exp 正向溢出）必须保留，仅下界 clamp 是 bug；非 exp 类激活未验证；a2/a3 推断同 V pipe exp 语义但未实测，采用前需在目标平台复现探针确认。

## 判别方法

### trigger

精度回归中失败 case 集中在 `z=beta*self` 为大负数（如 `z<-50`）且 `gradOutput` 幅值大时；NPU 输出 ≈ `gradOutput × exp(-50)` 而非 0。最小复现 `z=-1105, gradOutput=3.4e38`：golden=0，NPU=6.56e16。

### probe

取单元素 `z=-1105, gradOutput=3.4e38` 跑 kernel，比对 NPU 输出与 `gradOutput × exp(-50) ≈ 6.5e16`：

- `NPU ≈ 6.5e16 = gradOutput × exp(-50)` → 命中下界 clamp bug；
- `NPU = 0`（或 fp32 非规范数）→ 非本 bug。

### observation

`z=-1105, gradOutput=3.4e38` 实测：golden=0，NPU=6.56e16≈`gradOutput × exp(-50)`。该值正是 exp 输入被 clamp 到 -50 后 `exp(-50)≈1.9e-22` 再乘大 gradOutput 的产物，与下界 clamp 抬高正确下溢值的机制吻合。

### interpretation

`ComputeFp32Core` 中对 exp 输入做双向 clamp（before 机制 artifact，read 自 `op_kernel/arch35/softplus_v2_grad_kernel.h` 的 `ComputeFp32Core` exp 输入 clamp 段）：

`bx_clamped = min(max(bx, -50.0), threshold)`

机制链：
- sigmoid 分支处理 `z <= threshold` 的元素。对 `z` 为大负数（如 -1105），数学上 `exp(z) → 0`（fp32 下正确下溢），`sigmoid(z) = exp(z)/(1+exp(z)) → 0`，`gradOutput × sigmoid(z) → 0`。
- `max(bx, -50)` 把 `bx` 从 -1105 抬到 -50，于是 `exp(bx_clamped) = exp(-50) ≈ 1.9e-22`（而非 0）。
- `gradOutput × 1.9e-22`：当 gradOutput ≈ 3.4e38 时，`3.4e38 × 1.9e-22 ≈ 6.5e16`，远超容差。
- 下界 clamp 无数学必要性：exp 对负输入只会单调趋于 0，不会溢出；上界 clamp（`Mins(bx, threshold)`）才是防 exp 正向溢出（`exp(88)` 已接近 fp32 上限）。

根因是对 exp 函数溢出方向的误解：exp 仅对正输入溢出，对负输入只会下溢到 0（正确值）；为"防溢出"加双向 clamp 时，下界 clamp 反而破坏了 sigmoid 大负数下溢的正确结果。

## 验证信号

本卡信号来自本次会话在 Ascend950PR 上的实测（CANN cann-9.0.0-beta.2）。

- 最小复现 `z=-1105/gradOutput=3.4e38`：golden=0，NPU=6.56e16≈`gradOutput×exp(-50)`（来源平台：950；证据等级: tool_observed）。
- before 机制 artifact：read 命中 `ComputeFp32Core` 内 `Maxs(bx,-50)+Mins(bx,threshold)` 双向 clamp（来源平台：950；证据等级: artifact_verified）。
- 应用修复（移除 `Maxs` 下界 clamp 行，仅保留 `Mins` 上界）后 PyTorch ST 失败由 114 降至 7（来源平台：950；证据等级: tool_observed）。
## 失效边界

- z∈[-95,-38] 区间 `exp(z)` 为 fp32 非规范数，NPU V pipe FTZ 会刷为 0；当 `gradOutput=±FLT_MAX` 时，golden（CPU 保留非规范数）得小非零值、NPU=0，仍不可对齐——这是硬件 FTZ，非本卡 bug，见极端值独立卡。
- a2/a3 推断可迁移（同 V pipe exp 语义），未验证，采用前需在目标平台复现探针确认。

## 预防

- 对 exp/log/sigmoid 类算子做输入 clamp 前，先分析函数在负/正方向的真实溢出方向：exp 仅正方向溢出，负方向下溢到 0（正确值）；不要为"防溢出"加双向 clamp。
- clamp 边界值（如 -50）的选取必须有数值依据，不能凭直觉。

## 坏实践

- "exp 输入双 clamp 防 exp 溢出"——下界 clamp 破坏 sigmoid 大负数下溢，是数值稳定性误区。

<!-- cannbot:related:start -->
## 相关

- [ClampMin](../../apis/simd_api/adv_api/math_compute/clamp_interface/clamp_min.md)（`exemplifies`）：《ClampMin》说明将srcTensor中小于scalar的数替换为scalar，大于等于scalar的数保持不变，作为dstTensor输出。；《exp 下界 clamp -50 破坏 sigmoid 大负数下溢》说明SoftplusV2Grad kernel 对 exp 输入做 max(bx,-50) 下界 clamp，把大负数 z 的 exp(z)→0 正确下溢值抬高为 exp(-50)≈1.9e-22，gradOutput 大时被放大；判别：NPU 输出≈gradOutput×exp(-50) 即命中下界 clamp bug。。二者在ClampMin与ClampMax共同定义上下界替换，workspace查询决定分块，exp下溢故障则直接验证错误下界的数值后果上存在可执行的直接衔接。
- [Clamp（数学计算）](../../apis/simd_api/adv_api/math_compute/clamp_interface/clamp.md)（`exemplifies`）：《Clamp（数学计算）》说明将输入中除nan值以外大于max的数替换为max，小于min的数替换为min，小于等于max和大于等于min的数保持不变，作为输出。当min大于max时，将除nan值外所有值替换为max。min和max可以为标量或LocalTensor。；《exp 下界 clamp -50 破坏 sigmoid 大负数下溢》说明SoftplusV2Grad kernel 对 exp 输入做 max(bx,-50) 下界 clamp，把大负数 z 的 exp(z)→0 正确下溢值抬高为 exp(-50)≈1.9e-22，gradOutput 大时被放大；判别：NPU 输出≈gradOutput×exp(-50) 即命中下界 clamp bug。。二者在Clamp、ClampMin/Max及workspace查询共享上下界替换合同，exp相关故障直接说明错误clamp边界对数值的影响上存在可执行的直接衔接。
- [Exp](../../apis/simd_api/adv_api/math_compute/exp_interface/exp.md)（`exemplifies`）：Exp 与《exp 下界 clamp -50 破坏 sigmoid 大负数下溢》的实质衔接是：这些卡直接给出 Exp 的高阶、基础、Reg 与 C 入口及其临时空间契约；所连排障卡均以 Exp 的溢出、下溢、FTZ 或 clamp 行为作为精度根因和修复对象。
- [Maxs](../../apis/simd_api/basic_api/reg_vector_compute/basic_arithmetic/maxs.md)（`exemplifies`）：Maxs 与《exp 下界 clamp -50 破坏 sigmoid 大负数下溢》的实质衔接是：Reg Maxs 是 vector-scalar 下限 clamp，Mins/Max/其他层级 Maxs 对照操作数形态；Exp/FTZ/sigmoid 卡直接验证 clamp 阈值改变数值尾部。
- [Mins](../../apis/simd_api/basic_api/memory_vector_compute/basic_arithmetic/mins.md)（`exemplifies`）：Mins 与《exp 下界 clamp -50 破坏 sigmoid 大负数下溢》的实质衔接是：Mins 是 tensor 与标量逐元素取小值；Reg/灵活标量入口保持同一契约，Maxs/Min/Relu 组合及 exp clamp 案例说明它作为上界限幅的实际语义。
- [Sigmoid](../../apis/simd_api/adv_api/activation_functions/sigmoid_interface/sigmoid.md)（`exemplifies`）：该卡说明 Sigmoid/softplus 的 exp 负向输入不应做 -50 下界截断，并用输出等于 gradOutput×exp(-50) 的信号定位错误 clamp。
- [Sigmoid接口](../../apis/simd_api/adv_api/activation_functions/sigmoid_interface/sigmoid_interface.md)（`exemplifies`）：《exp 下界 clamp -50 破坏 sigmoid 大负数下溢》给出“SoftplusV2Grad kernel 对 exp 输入做 max(bx,-50) 下界 clamp，把大负数 z 的 exp(z)→0 正确下溢值抬高为 exp(-50)≈1.9e-22，gradOutput 大时被放大；判别：NPU 输出≈gradOutput×exp(-50) 即命中下界 clamp bug。”；该约束/探针可直接复现、解释或前置验证《Sigmoid接口》中的“提供Sigmoid激活函数接口及GetSigmoidMaxMinTmpSize等Tiling临时空间大小查询接口。”。
- [Ascend950 向量管 FTZ 刷新次正规 exp 为零](ascend950_ftz_exp.md)（`related`）：去掉软件下界 clamp 后剩余窄带 0 才可归因于硬件 FTZ。
- [Exp 默认 INTRINSIC FTZ 致 subnormal 残留失配](exp_intrinsic_ftz_subnormal.md)（`related`）：下界 clamp 卡给出 actual≈grad×exp(-50) 的独立签名，可先排除人为抬高负尾；focal 则处理移除 clamp 后仍为 actual=0 的真实 subnormal FTZ 残留。
- [Reciprocal 低精度致 sigmoid 比对失败](reciprocal_sigmoid.md)（`related`）：《Reciprocal 低精度致 sigmoid 比对失败》说明AscendC::Reciprocal 为低精度查表近似指令（相对误差约 1e-3），sigmoid 的 1/(1+exp(-x)) 用其求倒数会让 verify_result.py 报 max_diff≈0.00179、16384/16384 全 mismatch；判别方法：把最后一步 Reciprocal 换成 Duplicate+Div 高精度除法后 max_diff 降为 0，即可单点归因到 Reciprocal 的低精度近似。；《exp 下界 clamp -50 破坏 sigmoid 大负数下溢》说明SoftplusV2Grad kernel 对 exp 输入做 max(bx,-50) 下界 clamp，把大负数 z 的 exp(z)→0 正确下溢值抬高为 exp(-50)≈1.9e-22，gradOutput 大时被放大；判别：NPU 输出≈gradOutput×exp(-50) 即命中下界 clamp bug。。二者在该失败由Reciprocal近似误差进入sigmoid末步；高精度Div替换及Exp溢出/FTZ变体用于单点归因上存在可执行的直接衔接。
- [SoftplusV2Grad VF Form B exp 溢出判别](softplusv2grad_vf_form_b_exp.md)（`related`）：SoftplusV2Grad VF Form B exp 溢出判别 与《exp 下界 clamp -50 破坏 sigmoid 大负数下溢》的衔接是：这些案例都直接围绕 exp/sigmoid 的溢出、下溢、FTZ、clamp 上下界或倒数精度；它们能区分 Form B 的正大输入溢出与其他极值失配根因。
- [SoftplusV2Grad 非默认θ线性区分支缺失致超差](softplusv2grad.md)（`related`）：目标卡说明下界 clamp -50 会把本应下溢为 0 的大负 z 抬成可见残差；在本卡补齐 threshold 分支后，sigmoid 区仍需保留自然下溢语义。
- [arch35 sigmoid 大负 z 下 exp 溢出 inf 致 sig=0](arch35_sigmoid_z_exp_inf_sig_0.md)（`related`）：改用 exp(-z) 的另一公式会在相反方向溢出；两卡用于选择稳定 sigmoid 分支。
- [Maxs 下限 clamp 阻止 exp 自然下溢残留](maxs_clamp_exp.md)（`same_topic`）：两卡定位同一 SoftplusV2Grad 根因：Maxs(z,-50) 把应自然下溢为 0 的大负 z 抬到 exp(-50)，再被 FLT_MAX grad 放大；该卡还给出 6.56e16 指纹与移除 Maxs 后回归。
- [exp 输入 clamp 上界用 threshold 用户参数致溢出](exp_clamp_upper_bound_must_decouple_from_user_threshold.md)（`same_topic`）：exp 输入 clamp 上界用 threshold 用户参数致溢出 与《exp 下界 clamp -50 破坏 sigmoid 大负数下溢》的实质衔接是：故障由用户 threshold 充当 Exp 安全上界导致；Exp、Clamp/Mins、Sigmoid 公式及溢出/FTZ/Softplus 分支案例共同限定固定上界和极值验收。
<!-- cannbot:related:end -->
