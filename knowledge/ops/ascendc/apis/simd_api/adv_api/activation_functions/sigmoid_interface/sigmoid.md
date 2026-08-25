---
type: API
title: Sigmoid
description: 按元素做逻辑回归Sigmoid计算。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/Sigmoid_interface/Sigmoid.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# Sigmoid

按元素做逻辑回归Sigmoid，计算公式如下：

函数原型：
template <typename T, bool isReuseSource = false>
__aicore__ inline void Sigmoid(const LocalTensor<T>& dstTensor, const LocalTensor<T>& srcTensor, const LocalTensor<uint8_t>& sharedTmpBuffer, const uint32_t calCount)

参数：
- T：操作数的数据类型。支持的数据类型为：half、float。
- isReuseSource：是否允许修改源操作数。该参数预留，传入默认值false即可。
- dstTensor（输出）：目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。
- srcTensor（输入）：源操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 源操作数的数据类型需要与目的操作数保持一致。
- sharedTmpBuffer（输入）：临时缓存。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 用于Sigmoid内部复杂计算时存储中间变量，由开发者提供。 临时空间大小BufferSize的获取方式请参考GetSigmoidMaxMinTmpSize。

约束：
- 操作数地址对齐要求请参见通用地址对齐约束。
- 不支持源操作数与目的操作数地址重叠。
- 不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品Vector Core。

<!-- cannbot:related:start -->
## 相关

- [Reciprocal 低精度致 sigmoid 比对失败](../../../../../runbooks/precision/reciprocal_sigmoid.md)（`exemplifies`）：《Reciprocal 低精度致 sigmoid 比对失败》说明AscendC::Reciprocal 为低精度查表近似指令（相对误差约 1e-3），sigmoid 的 1/(1+exp(-x)) 用其求倒数会让 verify_result.py 报 max_diff≈0.00179、16384/16384 全 mismatch；判别方法：把最后一步 Reciprocal 换成 Duplicate+Div 高精度除法后 max_diff 降为 0，即可单点归因到 Reciprocal 的低精度近似。；《Sigmoid》说明按元素做逻辑回归Sigmoid计算。。二者在该失败由Reciprocal近似误差进入sigmoid末步；高精度Div替换及Exp溢出/FTZ变体用于单点归因上存在可执行的直接衔接。
- [arch35 sigmoid 大负 z 下 exp 溢出 inf 致 sig=0](../../../../../runbooks/precision/arch35_sigmoid_z_exp_inf_sig_0.md)（`exemplifies`）：该故障卡把 Sigmoid 在大负输入下的 Exp 溢出与中间 subnormal 被 FTZ 清零落实为可观测的 Actual=0，并给出区别于控制流错误的判据。
- [exp 下界 clamp -50 破坏 sigmoid 大负数下溢](../../../../../runbooks/precision/exp_clamp_50_sigmoid.md)（`exemplifies`）：该卡说明 Sigmoid/softplus 的 exp 负向输入不应做 -50 下界截断，并用输出等于 gradOutput×exp(-50) 的信号定位错误 clamp。
- [exp 输入 clamp 上界用 threshold 用户参数致溢出](../../../../../runbooks/precision/exp_clamp_upper_bound_must_decouple_from_user_threshold.md)（`exemplifies`）：exp 输入 clamp 上界用 threshold 用户参数致溢出 与《Sigmoid》的实质衔接是：故障由用户 threshold 充当 Exp 安全上界导致；Exp、Clamp/Mins、Sigmoid 公式及溢出/FTZ/Softplus 分支案例共同限定固定上界和极值验收。
- [GetSigmoidMaxMinTmpSize](get_sigmoid_max_min_tmp_size.md)（`related`）：GetSigmoidMaxMinTmpSize 在 host 侧返回 Sigmoid sharedTmpBuffer 的合法范围；Sigmoid 的 isReuseSource、shape 和实际预留空间必须与该结果一致。
- [Swish](../swish_interface/swish.md)（`related`）：Swish 与《Sigmoid》的实质衔接是：Swish kernel 与临时空间查询直接配套；SiLU 是 beta=1 的同公式变体，Sigmoid 是门控项。
- [Sigmoid接口](sigmoid_interface.md)（`same_topic`）：《Sigmoid》明确“按元素做逻辑回归Sigmoid计算。”；它与《Sigmoid接口》的“提供Sigmoid激活函数接口及GetSigmoidMaxMinTmpSize等Tiling临时空间大小查询接口。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
