---
type: API
title: Sigmoid接口
description: 提供Sigmoid激活函数接口及GetSigmoidMaxMinTmpSize等Tiling临时空间大小查询接口。
tags: [task.lookup, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/Sigmoid_interface/Sigmoid_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Sigmoid接口

提供 Sigmoid 激活函数及 GetSigmoidMaxMinTmpSize 临时空间查询接口。Sigmoid 按元素做逻辑回归计算，输出 1/(1+e^(-x))。

接口为模板函数，支持 half、float 数据类型，`isReuseSource` 参数预留。通过 `calCount` 可指定参与计算的元素个数，也可省略表示全部参与。临时空间支持 `sharedTmpBuffer` 传入和框架申请两种方式，大小通过 GetSigmoidMaxMinTmpSize 获取。源操作数数据类型需与目的操作数一致，操作数地址需满足通用对齐约束。

<!-- cannbot:related:start -->
## 相关

- [Reciprocal 低精度致 sigmoid 比对失败](../../../../../runbooks/precision/reciprocal_sigmoid.md)（`exemplifies`）：《Reciprocal 低精度致 sigmoid 比对失败》说明AscendC::Reciprocal 为低精度查表近似指令（相对误差约 1e-3），sigmoid 的 1/(1+exp(-x)) 用其求倒数会让 verify_result.py 报 max_diff≈0.00179、16384/16384 全 mismatch；判别方法：把最后一步 Reciprocal 换成 Duplicate+Div 高精度除法后 max_diff 降为 0，即可单点归因到 Reciprocal 的低精度近似。；《Sigmoid接口》说明提供Sigmoid激活函数接口及GetSigmoidMaxMinTmpSize等Tiling临时空间大小查询接口。。二者在该失败由Reciprocal近似误差进入sigmoid末步；高精度Div替换及Exp溢出/FTZ变体用于单点归因上存在可执行的直接衔接。
- [arch35 sigmoid 大负 z 下 exp 溢出 inf 致 sig=0](../../../../../runbooks/precision/arch35_sigmoid_z_exp_inf_sig_0.md)（`exemplifies`）：《arch35 sigmoid 大负 z 下 exp 溢出 inf 致 sig=0》给出“arch35 上把 sigmoid 改写为 1/(1+exp(-z)) 后，z≈-88 时 Exp(88) 溢出为 inf 致 sig=1/inf=0，且 sig≈6e-39 子正常数被 FTZ 清零；单独跑 L1_018 即 FAIL（非跨调用污染），Actual=0 量级吻合 subnormal/FTZ 而非分支选择错。诊断指向数值形式而非控制流。”；该约束/探针可直接复现、解释或前置验证《Sigmoid接口》中的“提供Sigmoid激活函数接口及GetSigmoidMaxMinTmpSize等Tiling临时空间大小查询接口。”。
- [exp 下界 clamp -50 破坏 sigmoid 大负数下溢](../../../../../runbooks/precision/exp_clamp_50_sigmoid.md)（`exemplifies`）：《exp 下界 clamp -50 破坏 sigmoid 大负数下溢》给出“SoftplusV2Grad kernel 对 exp 输入做 max(bx,-50) 下界 clamp，把大负数 z 的 exp(z)→0 正确下溢值抬高为 exp(-50)≈1.9e-22，gradOutput 大时被放大；判别：NPU 输出≈gradOutput×exp(-50) 即命中下界 clamp bug。”；该约束/探针可直接复现、解释或前置验证《Sigmoid接口》中的“提供Sigmoid激活函数接口及GetSigmoidMaxMinTmpSize等Tiling临时空间大小查询接口。”。
- [GetSigmoidMaxMinTmpSize](get_sigmoid_max_min_tmp_size.md)（`related`）：《GetSigmoidMaxMinTmpSize》明确“用于在host侧获取Sigmoid接口所需的最大最小临时空间大小，作为Tiling参数传递到kernel侧使用。”；它与《Sigmoid接口》的“提供Sigmoid激活函数接口及GetSigmoidMaxMinTmpSize等Tiling临时空间大小查询接口。”在实际调用参数、数据流或结果校验上直接衔接。
- [Sigmoid](sigmoid.md)（`same_topic`）：《Sigmoid》明确“按元素做逻辑回归Sigmoid计算。”；它与《Sigmoid接口》的“提供Sigmoid激活函数接口及GetSigmoidMaxMinTmpSize等Tiling临时空间大小查询接口。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
