---
type: "Runbook"
title: "Reciprocal 低精度致 sigmoid 比对失败"
description: "AscendC::Reciprocal 为低精度查表近似指令（相对误差约 1e-3），sigmoid 的 1/(1+exp(-x)) 用其求倒数会让 verify_result.py 报 max_diff≈0.00179、16384/16384 全 mismatch；判别方法：把最后一步 Reciprocal 换成 Duplicate+Div 高精度除法后 max_diff 降为 0，即可单点归因到 Reciprocal 的低精度近似。"
tags: ["task.debugging", "topic.compute.elementwise.activation", "topic.compute.elementwise.math_function", "topic.precision"]
status: stable
sources: []
created_at: "2026-08-18T05:30:07Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["a2"]
---

# Reciprocal 低精度致 sigmoid 比对失败

## 现象

在基于 `ascendc-direct-invoke-template` 的 `add_custom` 模板改造 `sigmoid_custom` 直调算子时，kernel 用 `AscendC::Reciprocal` 实现 `sigmoid(x)=1/(1+exp(-x))` 的求倒数步骤。工程目录 `/mnt/workspace/gitCode/CANNBot/operators/sigmoid_custom/`，目标平台 dav-2201（Atlas A2 / 910B3），CANN 9.1.0。编译通过、kernel 正常运行无报错，但精度比对输出 `Verification FAILED!`：`Max diff: 0.0017892718315124512`、`Mismatch count: 16384 / 16384`，即 16384 个元素全部不匹配（输入全 5.5f 故每元素偏差恒定）。golden 参考值为 `sigmoid(5.5)=1/(1+exp(-5.5))=0.9959298968315125`。

## 适用场景

- **工程形态**：kernel 直调（ops-direct-invoke，可执行文件通路 + PyTorch `torch.ops.load_library` 通路）。
- **API 路径**：`AscendC::Reciprocal(dst, src, count)`（低精度倒数）vs `AscendC::Div(dst, src0, src1, count)` + `AscendC::Duplicate(dst, scalar, count)`；元素级 vector API。
- **验证过的平台与 CANN 版本**：dav-2201（Atlas A2 / 910B3），CANN 9.1.0。`platforms: [a2]`。
- **适用粒度**：`operator_family`——凡需要 `1/(1+exp(-x))` 形式倒数（sigmoid、logistic 相关、softsign 等）的元素级 kernel 均适用。
- **不适用/未验证场景**：性能极致敏感且可接受近似倒数的场景（`Reciprocal` 可能更快，本 trace 未做性能对比，未验证其相对加速）。950/a3 平台未验证，推断可迁移（见 `## 失效边界`）。

## 判别方法

**触发条件**：元素级 kernel 把 `1/(1+exp(-x))` 的最后一步求倒数实现为 `AscendC::Reciprocal(yLocal, tmp, count)`（其中 `tmp = 1 + exp(-x)` 已由高精度 `Muls→Exp→Adds` 算出）。kernel 编译通过、运行无报错，但 `verify_result.py`（`rtol=1e-5, atol=1e-6`）报 `Verification FAILED!`，且 `Mismatch count` 等于元素总数、`Max diff` 落在 1e-3 量级（约 0.00179）。

**可执行探针**：在 `build/` 目录下跑直调验证，并对照“把最后一步 `Reciprocal` 换成 `Duplicate(ones,1.0f,count)` + `Div(yLocal, ones, tmp, count)` 后重编重跑”的对照实验：

```bash
source $ASCEND_HOME_PATH/set_env.sh && python3 ../scripts/gen_data.py \
  && ./sigmoid_custom \
  && python3 ../scripts/verify_result.py output/output.bin output/golden.bin
```

判定：对照实验前后 `verify_result.py` 的 `Max diff` 从 ~1e-3 量级降到 0，即单点归因到 `Reciprocal` 的低精度近似（同一 kernel 的 `Muls/Exp/Adds` 未改）。

**原始观测**：修复前 `verify_result.py` 输出 `Max diff: 0.0017892718315124512, Mean diff: 0.0017892718315124512, Mismatch count: 16384 / 16384`（tool_observed，trace seq64 bash stdout）。换 `Div` 后 `Max diff: 0.0`、`Verification PASSED!`（tool_observed，trace seq73 bash stdout）。

**解释**（agent 根因分析）：`AscendC::Reciprocal` 在 dav-2201 上是低精度近似指令（查表法实现），相对误差约 1e-3 量级。`tmp = 1 + exp(-5.5) = 1.00408677`，`Reciprocal(y, tmp)` 的硬件近似结果与 numpy 精确除法的偏差约 `0.00179/0.99593 ≈ 0.0018`（约 0.18% 相对误差），与 `Reciprocal` 的 1e-3 量级相对误差界一致，故 16384/16384 全部超出 `rtol=1e-5, atol=1e-6` 容差而 mismatch。归因为单点：同一 kernel 的 `Muls/Exp/Adds` 未改，仅把最后一步 `Reciprocal` 换成 `Div` 后 `max_diff` 即由 0.00179 降为 0.0，故唯一误差源是 `Reciprocal` 的低精度近似，而非 `Exp`/`Muls` 等前置步骤。注意：`Reciprocal` 查表/牛顿迭代的精确实现机制与官方文档承诺的相对误差界，本 trace 未查证上游 CANN 文档，归因来自 agent 推理 + 前后 `max_diff` 对比（0.00179→0.0）的间接证据。

## 验证信号

来源：sigmoid_custom 直调算子在 dav-2201（910B3, CANN 9.1.0）上的开发会话，修复前直调验证失败，将 `Reciprocal` 换为 `Duplicate+Div` 并重新编译后重跑同一验证。

- 修复前直调：`Max diff=0.0017892718315124512, Mean diff=0.0017892718315124512, Mismatch count=16384/16384`（来源平台：a2；证据等级：tool_observed）
- 修复后直调：`Verification PASSED! Shape: (16384,), Max diff: 0.0`（来源平台：a2；证据等级：tool_observed）
- 修复后 PyTorch 通路：P1 random `Max diff=1.1920928955078125e-07` PASSED、P2 zeros `Max diff=0.0` PASSED、P3 pos_5.5 `Max diff=0.0` PASSED、P4 neg_5.5 `Max diff=0.0` PASSED、Total 4/4 PASSED（来源平台：a2；证据等级：tool_observed）
- 端到端 `run.sh --skip-build`：直调 + PyTorch 通路全通过（来源平台：a2；证据等级：tool_observed）

## 失效边界

- **未验证，推断可迁移**：950（Ascend950）、a3 平台未在本 trace 验证；`Div`/`Duplicate`/`Reciprocal` 均为跨架构 vector API，推断 `Reciprocal` 低精度特性与 `Div` 高精度特性在 950/a3 上一致，但需上板实测确认。
- 本 trace 仅验证 `x=5.5f` 固定值与随机/零/负值四个 PyTorch 用例，未覆盖极值（如 `x` 接近溢出边界）下 `Exp` 自身的精度行为；极值场景下 `Exp` 可能成为新的瓶颈，本判别方法的单点归因假设（前置步骤高精度）可能不成立。
- 性能代价未采集：本 trace 未做 profiling，未验证 `Div` 相对 `Reciprocal` 的性能代价；若性能敏感且可接受 ~1e-3 量级相对误差，需另行测量。

<!-- cannbot:related:start -->
## 相关

- [AscDiv](../../apis/simd_api/c_api/reg/arithmetic_compute/asc_div.md)（`exemplifies`）：《Reciprocal 低精度致 sigmoid 比对失败》说明AscendC::Reciprocal 为低精度查表近似指令（相对误差约 1e-3），sigmoid 的 1/(1+exp(-x)) 用其求倒数会让 verify_result.py 报 max_diff≈0.00179、16384/16384 全 mismatch；判别方法：把最后一步 Reciprocal 换成 Duplicate+Div 高精度除法后 max_diff 降为 0，即可单点归因到 Reciprocal 的低精度近似。；《AscDiv》说明根据mask对源操作数src0、src1按元素求商，将结果写入目的操作数dst。。二者在该失败由Reciprocal近似误差进入sigmoid末步；高精度Div替换及Exp溢出/FTZ变体用于单点归因上存在可执行的直接衔接。
- [AscDiv](../../apis/simd_api/c_api/vector_compute/asc_div.md)（`exemplifies`）：《Reciprocal 低精度致 sigmoid 比对失败》说明AscendC::Reciprocal 为低精度查表近似指令（相对误差约 1e-3），sigmoid 的 1/(1+exp(-x)) 用其求倒数会让 verify_result.py 报 max_diff≈0.00179、16384/16384 全 mismatch；判别方法：把最后一步 Reciprocal 换成 Duplicate+Div 高精度除法后 max_diff 降为 0，即可单点归因到 Reciprocal 的低精度近似。；《AscDiv》说明asc_div（矢量计算）。二者在该失败由Reciprocal近似误差进入sigmoid末步；高精度Div替换及Exp溢出/FTZ变体用于单点归因上存在可执行的直接衔接。
- [Exp](../../apis/simd_api/adv_api/math_compute/exp_interface/exp.md)（`exemplifies`）：《Reciprocal 低精度致 sigmoid 比对失败》说明AscendC::Reciprocal 为低精度查表近似指令（相对误差约 1e-3），sigmoid 的 1/(1+exp(-x)) 用其求倒数会让 verify_result.py 报 max_diff≈0.00179、16384/16384 全 mismatch；判别方法：把最后一步 Reciprocal 换成 Duplicate+Div 高精度除法后 max_diff 降为 0，即可单点归因到 Reciprocal 的低精度近似。；《Exp》说明按元素取自然指数，可选择是否使用泰勒展开公式进行计算。二者在该失败由Reciprocal近似误差进入sigmoid末步；高精度Div替换及Exp溢出/FTZ变体用于单点归因上存在可执行的直接衔接。
- [GetSigmoidMaxMinTmpSize](../../apis/simd_api/adv_api/activation_functions/sigmoid_interface/get_sigmoid_max_min_tmp_size.md)（`exemplifies`）：《Reciprocal 低精度致 sigmoid 比对失败》说明AscendC::Reciprocal 为低精度查表近似指令（相对误差约 1e-3），sigmoid 的 1/(1+exp(-x)) 用其求倒数会让 verify_result.py 报 max_diff≈0.00179、16384/16384 全 mismatch；判别方法：把最后一步 Reciprocal 换成 Duplicate+Div 高精度除法后 max_diff 降为 0，即可单点归因到 Reciprocal 的低精度近似。；《GetSigmoidMaxMinTmpSize》说明用于在host侧获取Sigmoid接口所需的最大最小临时空间大小，作为Tiling参数传递到kernel侧使用。。二者在该失败由Reciprocal近似误差进入sigmoid末步；高精度Div替换及Exp溢出/FTZ变体用于单点归因上存在可执行的直接衔接。
- [Reciprocal](../../apis/simd_api/basic_api/memory_vector_compute/basic_arithmetic/reciprocal.md)（`exemplifies`）：《Reciprocal 低精度致 sigmoid 比对失败》说明AscendC::Reciprocal 为低精度查表近似指令（相对误差约 1e-3），sigmoid 的 1/(1+exp(-x)) 用其求倒数会让 verify_result.py 报 max_diff≈0.00179、16384/16384 全 mismatch；判别方法：把最后一步 Reciprocal 换成 Duplicate+Div 高精度除法后 max_diff 降为 0，即可单点归因到 Reciprocal 的低精度近似。；《Reciprocal》说明单目矢量计算接口，对输入tensor按元素取倒数。。二者在该失败由Reciprocal近似误差进入sigmoid末步；高精度Div替换及Exp溢出/FTZ变体用于单点归因上存在可执行的直接衔接。
- [Sigmoid](../../apis/simd_api/adv_api/activation_functions/sigmoid_interface/sigmoid.md)（`exemplifies`）：《Reciprocal 低精度致 sigmoid 比对失败》说明AscendC::Reciprocal 为低精度查表近似指令（相对误差约 1e-3），sigmoid 的 1/(1+exp(-x)) 用其求倒数会让 verify_result.py 报 max_diff≈0.00179、16384/16384 全 mismatch；判别方法：把最后一步 Reciprocal 换成 Duplicate+Div 高精度除法后 max_diff 降为 0，即可单点归因到 Reciprocal 的低精度近似。；《Sigmoid》说明按元素做逻辑回归Sigmoid计算。。二者在该失败由Reciprocal近似误差进入sigmoid末步；高精度Div替换及Exp溢出/FTZ变体用于单点归因上存在可执行的直接衔接。
- [Sigmoid接口](../../apis/simd_api/adv_api/activation_functions/sigmoid_interface/sigmoid_interface.md)（`exemplifies`）：《Reciprocal 低精度致 sigmoid 比对失败》说明AscendC::Reciprocal 为低精度查表近似指令（相对误差约 1e-3），sigmoid 的 1/(1+exp(-x)) 用其求倒数会让 verify_result.py 报 max_diff≈0.00179、16384/16384 全 mismatch；判别方法：把最后一步 Reciprocal 换成 Duplicate+Div 高精度除法后 max_diff 降为 0，即可单点归因到 Reciprocal 的低精度近似。；《Sigmoid接口》说明提供Sigmoid激活函数接口及GetSigmoidMaxMinTmpSize等Tiling临时空间大小查询接口。。二者在该失败由Reciprocal近似误差进入sigmoid末步；高精度Div替换及Exp溢出/FTZ变体用于单点归因上存在可执行的直接衔接。
- [Exp 默认 INTRINSIC FTZ 致 subnormal 残留失配](exp_intrinsic_ftz_subnormal.md)（`related`）：《Reciprocal 低精度致 sigmoid 比对失败》说明AscendC::Reciprocal 为低精度查表近似指令（相对误差约 1e-3），sigmoid 的 1/(1+exp(-x)) 用其求倒数会让 verify_result.py 报 max_diff≈0.00179、16384/16384 全 mismatch；判别方法：把最后一步 Reciprocal 换成 Duplicate+Div 高精度除法后 max_diff 降为 0，即可单点归因到 Reciprocal 的低精度近似。；《Exp 默认 INTRINSIC FTZ 致 subnormal 残留失配》说明arch35 Exp 默认 ExpAlgo::INTRINSIC 将 subnormal 输入 FTZ 为 0；softplus_v2_grad 的 sigmoid 分支在 z∈(-104,-87)（exp(z) 为 fp32 subnormal）+ gradOutput≈FLT_MAX 时，aten 顺序 grad*exp(z) 的中间 subnormal 被 FTZ→0 致 actual=0，而 aten golden（CPU 保留 subnormal）得有限值。aten 顺序（默认 INTRINSIC）575/578（3 失败，subnormal 区间）与 spec 除法形式 567/578（11 失败，z>0 溢出区间）失败集不重叠，无单一顺序在所有极值下匹配 golden，需按 golden 来源选顺序。。二者在该失败由Reciprocal近似误差进入sigmoid末步；高精度Div替换及Exp溢出/FTZ变体用于单点归因上存在可执行的直接衔接。
- [SoftplusV2Grad VF Form B exp 溢出判别](softplusv2grad_vf_form_b_exp.md)（`related`）：《Reciprocal 低精度致 sigmoid 比对失败》说明AscendC::Reciprocal 为低精度查表近似指令（相对误差约 1e-3），sigmoid 的 1/(1+exp(-x)) 用其求倒数会让 verify_result.py 报 max_diff≈0.00179、16384/16384 全 mismatch；判别方法：把最后一步 Reciprocal 换成 Duplicate+Div 高精度除法后 max_diff 降为 0，即可单点归因到 Reciprocal 的低精度近似。；《SoftplusV2Grad VF Form B exp 溢出判别》说明arch35 SoftplusV2Grad VF 链在 bf16/fp16 用 Form B(exp(cbx)/(1+exp(cbx))) 实例化时，大 threshold 或 grad=inf 使正向 Exp(cbx) 溢出为 inf/NaN 发散于 golden Form A 的判别：触发=mare 超阈、探针=sigmoid 分支形态、观测=22 FAIL→3 FAIL、解释=正向 exp 输入溢出。。二者在该失败由Reciprocal近似误差进入sigmoid末步；高精度Div替换及Exp溢出/FTZ变体用于单点归因上存在可执行的直接衔接。
- [dav-2201 Rsqrt 精度不足 — 改用 Sqrt 加标量倒数](rsqrt_fast_approximation_use_sqrt_reciprocal.md)（`related`）：《Reciprocal 低精度致 sigmoid 比对失败》说明AscendC::Reciprocal 为低精度查表近似指令（相对误差约 1e-3），sigmoid 的 1/(1+exp(-x)) 用其求倒数会让 verify_result.py 报 max_diff≈0.00179、16384/16384 全 mismatch；判别方法：把最后一步 Reciprocal 换成 Duplicate+Div 高精度除法后 max_diff 降为 0，即可单点归因到 Reciprocal 的低精度近似。；《dav-2201 Rsqrt 精度不足 — 改用 Sqrt 加标量倒数》说明RmsNorm 的 fp32 rstd 使用不带 config 的 Rsqrt 后呈现约 2^-9 量化偏差；改为 Sqrt、标量读回与 1.0f/s 后恢复 fp32 精度。。二者在该失败由Reciprocal近似误差进入sigmoid末步；高精度Div替换及Exp溢出/FTZ变体用于单点归因上存在可执行的直接衔接。
- [exp 下界 clamp -50 破坏 sigmoid 大负数下溢](exp_clamp_50_sigmoid.md)（`related`）：《Reciprocal 低精度致 sigmoid 比对失败》说明AscendC::Reciprocal 为低精度查表近似指令（相对误差约 1e-3），sigmoid 的 1/(1+exp(-x)) 用其求倒数会让 verify_result.py 报 max_diff≈0.00179、16384/16384 全 mismatch；判别方法：把最后一步 Reciprocal 换成 Duplicate+Div 高精度除法后 max_diff 降为 0，即可单点归因到 Reciprocal 的低精度近似。；《exp 下界 clamp -50 破坏 sigmoid 大负数下溢》说明SoftplusV2Grad kernel 对 exp 输入做 max(bx,-50) 下界 clamp，把大负数 z 的 exp(z)→0 正确下溢值抬高为 exp(-50)≈1.9e-22，gradOutput 大时被放大；判别：NPU 输出≈gradOutput×exp(-50) 即命中下界 clamp bug。。二者在该失败由Reciprocal近似误差进入sigmoid末步；高精度Div替换及Exp溢出/FTZ变体用于单点归因上存在可执行的直接衔接。
- [softplus_v2_grad 极端 FLT_MAX 与 aten 不可对齐](softplus_v2_grad_flt_max_aten.md)（`related`）：《Reciprocal 低精度致 sigmoid 比对失败》说明AscendC::Reciprocal 为低精度查表近似指令（相对误差约 1e-3），sigmoid 的 1/(1+exp(-x)) 用其求倒数会让 verify_result.py 报 max_diff≈0.00179、16384/16384 全 mismatch；判别方法：把最后一步 Reciprocal 换成 Duplicate+Div 高精度除法后 max_diff 降为 0，即可单点归因到 Reciprocal 的低精度近似。；《softplus_v2_grad 极端 FLT_MAX 与 aten 不可对齐》说明softplus_v2_grad 在 gradOutput=±FLT_MAX 或 threshold=858 超出 spec extreme_inputs 的极端应力输入下，NPU 稳定式 gradOutput×sigmoid(z) 与 aten 不稳定式 aop×exp(z)/(exp(z)+1) 因计算顺序与硬件 FTZ 在 fp32 表示极限处不可对齐；软件无法修复，banned。。二者在该失败由Reciprocal近似误差进入sigmoid末步；高精度Div替换及Exp溢出/FTZ变体用于单点归因上存在可执行的直接衔接。
- [arch35 sigmoid 大负 z 下 exp 溢出 inf 致 sig=0](arch35_sigmoid_z_exp_inf_sig_0.md)（`same_topic`）：《Reciprocal 低精度致 sigmoid 比对失败》说明AscendC::Reciprocal 为低精度查表近似指令（相对误差约 1e-3），sigmoid 的 1/(1+exp(-x)) 用其求倒数会让 verify_result.py 报 max_diff≈0.00179、16384/16384 全 mismatch；判别方法：把最后一步 Reciprocal 换成 Duplicate+Div 高精度除法后 max_diff 降为 0，即可单点归因到 Reciprocal 的低精度近似。；《arch35 sigmoid 大负 z 下 exp 溢出 inf 致 sig=0》说明arch35 上把 sigmoid 改写为 1/(1+exp(-z)) 后，z≈-88 时 Exp(88) 溢出为 inf 致 sig=1/inf=0，且 sig≈6e-39 子正常数被 FTZ 清零；单独跑 L1_018 即 FAIL（非跨调用污染），Actual=0 量级吻合 subnormal/FTZ 而非分支选择错。诊断指向数值形式而非控制流。。二者在该失败由Reciprocal近似误差进入sigmoid末步；高精度Div替换及Exp溢出/FTZ变体用于单点归因上存在可执行的直接衔接。
<!-- cannbot:related:end -->
