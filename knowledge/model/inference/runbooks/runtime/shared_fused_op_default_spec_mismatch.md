---
type: Runbook
title: 复用共享融合算子/量化方法到不同结构模型时的静默规格失配（MoE 默认 SiLU 遇 GEGLU、钳位 SwiGLU 需专用算子、mxfp8 Linear 丢 dense 的 bias）
description: 复用共享融合算子/量化方法到不同结构模型时的静默规格失配（MoE 默认 SiLU 遇 GEGLU、钳位 SwiGLU 需专用算子、mxfp8 Linear 丢 dense 的 bias）。把一套为模型 A 写的共享融合算子 / 量化 Linear method 复用到结构不同的模型 B 时，其默认假设（激活函数、是否带 bias、是否钳位）可能与 B 的规格不符，且静默算错或丢参数——表现为精度异常/输出乱码，而非报错。给新结构模型 bringup 遇到「输出乱码但不报错」时，先怀疑复用的共享组件默认假设不匹配。
tags:
- task.debugging
- topic.mixture_of_experts
- topic.precision
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/304
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/392
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/408
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/issues/8463
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 复用共享融合算子/量化方法到不同结构模型时的静默规格失配（MoE 默认 SiLU 遇 GEGLU、钳位 SwiGLU 需专用算子、mxfp8 Linear 丢 dense 的 bias）

## 适用场景

把一套为模型 A 写的**共享融合算子 / 量化 Linear method** 复用到结构不同的模型 B 时，其**默认假设（激活函数、是否带 bias、是否钳位）**可能与 B 的规格不符，且**静默算错或丢参数**——表现为精度异常/输出乱码，而非报错。给新结构模型 bringup 遇到「输出乱码但不报错」时，先怀疑复用的共享组件默认假设不匹配。

## 症状 → 根因 → 修法（四类）

### A. MoE 融合算子默认 SiLU，模型用 GEGLU → 专家算错激活

- 信号：把 GELU 激活（`gelu_pytorch_tanh` / GEGLU）的 MoE 模型接入，表现为**首 token 输出 EOS + 高频词重复**。
- 根因：框架默认的 FusedMoEGMM 量化方法**硬编码 `npu_swiglu`（SiLU）**，直接复用会让专家算错激活。
- 修法：自定义 GEGLU 版 MoE 计算方法。

### B. 钳位 SwiGLU 激活被普通融合算子静默丢上界

- 信号：带钳位 SwiGLU（clamped/bounded gated activation，gpt-oss 式）的量化 MoE 共享专家，用普通融合算子 `npu_dequant_swiglu_quant` / `npu_swiglu` 时静默丢掉模型规格要求的激活上界。
- 修法：改用 clamp 变体融合算子，且**钳位参数在不同量化路径下接口不同**——int8 路径走 `npu_dequant_swiglu_clamp_quant`（传 `swiglu_mode=1`/`clamp_limit`/`glu_alpha`/`glu_bias`），fp8/mxfp8 路径走 `npu_swiglu_group_quant`（传 `clamp_value`）。

### C. 为无 bias MoE 写的 mxfp8 Linear method 丢掉 dense 的 attention bias

- 信号：bringup 带 attention bias 的 dense 模型（盘古 7B），bias 丢失。
- 根因：共享的 `module/quantization/mxfp8.py` 的 `MxFp8LinearMethod` 原本只注册 weight+weight_scale、**丢弃 bias**（为无 bias 的 MoE 模型写的）。
- 修法：补上把 bias 转 fp32+contiguous 重新注册。

### D. 激活派发门控用「字符串 == 枚举」恒 False → OAI/钳位 SwiGLU 静默回落通用算子

与 A/B 不同：这里**专用激活路径（`swiglu_oai`）本身存在且正确**，坏掉的是**选它的那道门控条件**——共享 fused-MoE MLP 用**字符串字面量比对**来判断激活类型，而框架升级把该字段从字符串换成了枚举，比对恒 False，本该走的专用分支被静默跳过、回落到 `else` 的通用 SwiGLU。

- 信号：MoE MLP 声明 `activation="swigluoai"`（OAI/clamped 门控 SwiGLU）的模型，`temperature=0.0` 下输出乱码/数值错误，**无报错、无崩溃**；换用旧版框架时同一模型正常。
- 根因：非量化 fused-MoE MLP 派发处写 `if activation == "swigluoai":` 用字符串字面量比。上游框架在某个版本把 `activation` 字段从普通字符串改为激活枚举对象传入，枚举对象与字符串直接 `==` 恒为 `False`，于是 `swiglu_oai` 专用分支不进，回落到 `else` 的通用 `npu_swiglu`。两条激活数学不同（OAI/clamped 变体带上界，通用 SiLU-SwiGLU 无），走错激活即产出错误结果。这是一个**静默错激活核选择**，管线不报错、只有末端输出异常，定位困难。
- 修法：派发前把激活标识**规范化再比对**——`act_name = getattr(activation, "value", activation)`（枚举取 `.value` 拿到字符串，纯字符串因无 `value` 属性返回自身），随后 `if act_name == "swigluoai":`。此写法同时兼容「传字符串」与「传枚举」两种调用约定。

## 通用先验

- 复用共享融合算子/量化 method 到新模型前，**核对三点默认假设**：激活函数（SiLU vs GEGLU vs 钳位）、是否处理 bias、量化路径（int8 vs fp8/mxfp8 接口不同）。
- 症状是「静默算错/丢参数」（输出乱码但不报错）时，优先查复用组件的默认规格，而非模型逻辑。
- 失配不止出在「算子入参/默认值」，也可能出在**选算子的那道门控条件**：当派发用**字符串字面量比对**激活/dtype/mode 标识时，上游把该字段改成枚举（或反之）会让比对恒 False、专用分支被静默跳过、回落到通用路径。**框架跨版本升级后同一模型突然输出错误、旧版正常**，是这类门控失配的强信号。防御写法是派发前规范化标识——`getattr(x, "value", x)` 同时吃字符串与枚举。

> ⚠️ 派发门控是「静默错激活/错核选择」的隐蔽来源：专用路径存在且正确，坏的只是选它的 `if`。查根因时不仅核默认值，也要核门控比对的两侧类型是否被上游换过。

## 风险 / 边界

- clamp 融合算子的入参名随量化路径不同（int8 vs mxfp8），别混用。
- 这些是共享组件在其原始服务对象上的默认值，不是算子本身的限制。
- D 类的门控规范化（`getattr(x, "value", x)`）只修了它落地的那一处派发点；同一仓其它按字符串比对激活/mode 的派发点若也被上游换成枚举，会各自独立踩坑，需逐处核对——不是一个全局修复。这类问题是框架新旧版 activation 类型 string↔enum 的集成级行为差异，最可靠的验证是真机端到端推理而非单测。

## 相关经验

- 注意力映射到 FIA 的 sparse_mode/激活承接见 [attention-to-fia-sparse-mode-sink-window](../../optimizations/experience/rules/attention_to_fia_sparse_mode_sink_window.md)。
- 量化权重加载布局/命名门控见 [quant-weight-load-layout-and-naming](../../optimizations/experience/rules/quant_weight_load_layout_and_naming.md)。

## Evidence

- `diff 事实`（@dc0404e）：`MxFp8LinearMethod` 原丢 bias，补注册 bias(fp32,contiguous)。
- `diff 事实`（@2111318）：钳位 SwiGLU int8 走 `npu_dequant_swiglu_clamp_quant`、fp8/mxfp8 走 `npu_swiglu_group_quant`。
- `diff 事实`（@8721be4）：FusedMoEGMM 硬编码 `npu_swiglu`(SiLU)，GEGLU 模型须自定义、否则首 token EOS+重复。
- `diff 事实`（D 类，@756029b50）：非量化 fused-MoE MLP `unquant_apply_mlp` 新增 `act_name = getattr(activation, "value", activation)`，激活比对由 `activation == "swigluoai"` 改为 `act_name == "swigluoai"`；框架某版本起该字段由字符串改传激活枚举，字符串比恒 False 致 `swiglu_oai` 专用分支静默回落通用 `npu_swiglu`。维护者定位在派发点并说明枚举来由；before→after 为仓自报手工端到端回归（gpt-oss-120b，TP=8，enforce-eager），无独立复测、未加单测。
- 溯源下探（D 类）：[vllm-ascend-issue-8463-bug-the-inference-result-of-the-gptoss-120b-model-is-incorrect-on-vllm-a](https://github.com/vllm-project/vllm-ascend/issues/8463)
- 溯源下探：[cann-recipes-infer-pr-304-feat-pangu-7b-model-inference-support-on-cann](https://gitcode.com/cann/cann-recipes-infer/merge_requests/304)、[cann-recipes-infer-pr-392-feat-shared-expert-adapt-clamp](https://gitcode.com/cann/cann-recipes-infer/merge_requests/392)、[cann-recipes-infer-pr-408-feat-add-gemma-4-model-optimized-by-agent-skills](https://gitcode.com/cann/cann-recipes-infer/merge_requests/408)

<!-- cannbot:related:start -->
## 相关

- [DequantSwigluQuant 950 ACLNN 算子知识](../../../../ops/ascendc/operators/aclnn/nn/quant/dequant_swiglu_quant_950.md)（`related`）：带钳位 SwiGLU（clamped/bounded gated activation，gpt-oss 式）的量化 MoE 共享专家，用普通融合算子 `npu_dequant_swiglu_quant` / `npu_swiglu` 时静默丢掉模型规格要求的激活上界。950 V2 只使用普通 SwiGLU：`swish(A)*B=A/(1+exp(-A))*B`，`activateLeft` 决定 A/B。故障规格与 950 V2 的普通公式构成明确的能力边界：该平台路由不能承接 bounded 激活，选型时应避免把它当作钳位变体。
- [DequantSwigluQuant A2/A3 ACLNN 算子知识](../../../../ops/ascendc/operators/aclnn/nn/quant/dequant_swiglu_quant.md)（`related`）：带钳位 SwiGLU（clamped/bounded gated activation，gpt-oss 式）的量化 MoE 共享专家，用普通融合算子 `npu_dequant_swiglu_quant` / `npu_swiglu` 时静默丢掉模型规格要求的激活上界。`swigluMode=1` 时按偶/奇通道 gather，计算 `min(x_glu,L)/(1+exp(-alpha*min(x_glu,L))) * (clamp(x_linear,-L,L)+beta)`。故障信号要求保留的上界、alpha 与 beta 语义由 A2/A3 V2 的模式 1 公式直接承接，可据此替换普通融合路径并验证钳位结果。
- [Gemma-4-26B-A4B](../../concepts/models/gemma4_26b_a4b.md)（`related`）：“**MoE**：128 experts，top-8，moe_intermediate=704，专家激活 **GEGLU**（`Gemma4GegluMoEGMM`）。”；“- 根因：框架默认的 FusedMoEGMM 量化方法**硬编码 `npu_swiglu`（SiLU）**，直接复用会让专家算错激活。”。运行手册直接解释焦点模型不能复用默认 SiLU MoE 融合路径的静默精度风险。
- [MXFP8 A8W8 (DiT Linear)](../../concepts/quantization/mxfp8_a8w8.md)（`related`）：焦点卡写明“仅量化 Transformer block 中的 2D Linear；adaLN / modulation 与 1D 权重跳过”，候选卡写明“共享的 `module/quantization/mxfp8.py` 的 `MxFp8LinearMethod` 原本只注册 weight+weight_scale、**丢弃 bias**”。概念卡给出正常量化范围，排障卡指出复用无 bias 实现到 dense attention Linear 会静默丢参。
<!-- cannbot:related:end -->
