---
type: Runbook
title: EPLB 专家重映射漏搬独立 scale 张量：per-expert 参数清单缺 scale 致权重/scale 失配、静默掉精度
description: 昇腾 NPU MoE 推理开启 EPLB（专家并行负载均衡）对独立-scale 量化专家（MXFP4/MXFP8/W8A8/W4A8 等「量化权重张量 + 独立 scale/bias 张量」布局）做专家重映射时的静默精度错 failure_signature。信号：结果 accuracy 掉点但不抛异常、shape/dtype 合法，开 EPLB 才复现。根因：EPLB 靠 per-expert 参数名清单（expert_weight_names）决定哪些逐专家张量随专家一起重映射/搬运，若清单只列量化权重张量（w13_weight/w2_weight）漏了对应 scale 张量（w13_weight_scale/w2_weight_scale），专家在 rank 间重排后权重换了、scale 没跟着换，反量化用到不匹配专家的 scale，还原浮点权重整体错误。修法：把 scale（及 scale_bias）张量名补进 EPLB 逐专家参数清单，使量化权重与其 scale 成组一起重映射对齐；判据用 elif quant_type in (QuantType.MXFP4, QuantType.MXFP8) 成员判断而非布尔恒真/独立 if/未定义枚举。可迁移准则：任何 MoE 专家重映射/负载均衡机制，只要专家权重是权重+独立 scale 布局，逐专家清单必须覆盖所有参与反量化的逐专家张量（scale/scale_bias），否则重排后 scale 掉队、静默掉精度。参考实现 vllm-ascend EPLB 适配器 vllm_adaptor.py，merge sha 64b05b4823ca，Ascend 950 平台。correctness 需构造真正触发专家重排的负载不均衡场景对齐 baseline。
tags:
- task.debugging
- topic.mixture_of_experts
- topic.parallelism
- topic.precision
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/9280
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-07-15T00:00:00Z'
platforms:
- '950'
---

# EPLB 专家重映射漏搬独立 scale 张量：per-expert 参数清单缺 scale 致权重/scale 失配、静默掉精度

## 信号（现象）

- 在昇腾 NPU 上对 **MoE 专家做重映射/负载均衡（EPLB 一类机制）** 且专家权重是**「量化权重张量 + 独立 scale（/bias）张量」布局**（MXFP4 / MXFP8 / W8A8 / W4A8 等）时，推理结果**数值不正确**（accuracy 掉点）。
- 关键辨识特征：**静默** —— 不抛异常、不报维度/dtype 错，前向照常跑完，只是输出错。开了 EPLB 才复现、关掉 EPLB（不重映射专家）或用非量化专家时正确，指向「专家在设备间被重排后权重与其 scale 对不上」。
- 若你观测到的是「显式报维度不匹配 / dtype 冲突 / EPLB not support <quant_type>」的**硬报错**，那是另一类问题（参数清单缺失/覆盖不全的显式版本），本页针对的是**无报错的数值错**。

## 触发条件

- MoE 推理开启 EPLB（专家并行负载均衡：运行时统计专家负载、把热专家在 rank 间重映射/重分布以均衡）。
- 专家权重采用**独立 scale 量化布局**：反量化时需要「量化权重张量」与其**独立存放的 scale 张量**成对使用，缺一不可。MXFP（Micro-scaling FP，`QuantType.MXFP4` / `QuantType.MXFP8`，对应 W4A4_MXFP / W8A8_MXFP）、以及 W8A8、W4A8（还带 scale_bias）都属于这一族。
- EPLB 靠一份 **per-expert 参数名清单**（如 `expert_weight_names`）决定「哪些逐专家张量需要随专家一起被搬运/重映射」。**该清单只列了量化权重张量、漏了对应的 scale（/bias）张量**。

## 根因

- 独立 scale 布局下，专家 `i` 的「量化权重」与其「scale 张量」是一组必须锁在一起的数据。EPLB 重映射专家时，如果只按参数清单搬运了量化权重、没搬对应 scale，专家在 rank 间重排后**权重换了、scale 没跟着换**，两者错位。
- 反量化阶段用到的是**不匹配专家的 scale**，还原出的浮点权重整体错误，于是前向结果错——但张量 shape / dtype 都合法，所以**没有任何异常，纯静默精度错**。
- 这是「独立 scale 的量化布局」与「任何做专家重排/重分布的机制」之间的**固有契约**：只要有一个逐专家张量参与反量化/计算，就必须进入重排的搬运清单。同类实现里 W8A8（`fused_w1_scale_list` / `fused_w2_scale_list`）、W4A8（含 w13/w2 的 scale 与 `scale_bias_list`）分支把各自的 scale/bias 一并列入参数清单，正是同一不变量的正例体现。

## 修法

- **把 scale（及 scale_bias）张量名补进 EPLB 的 per-expert 参数清单**，使量化权重与其 scale 作为一组被一起重映射、始终对齐。MXFP 场景下逐专家清单应同时含权重名与 scale 名：

```python
# EPLB 适配器初始化逐专家参数清单时，为 MXFP 量化补齐 scale 张量名
elif quant_type in (QuantType.MXFP4, QuantType.MXFP8):
    self.expert_weight_names = [
        "w13_weight",
        "w2_weight",
        "w13_weight_scale",   # ← 漏此项则重映射后 scale 与权重脱钩
        "w2_weight_scale",
    ]
else:
    raise ValueError(f"EPLB not support {quant_type}")
```

- **可迁移准则**：任何在昇腾上做 MoE 专家重映射/负载均衡的机制，只要专家权重是「权重张量 + 独立 scale（/bias）张量」布局，其逐专家参数清单**必须覆盖 scale（及 scale_bias）张量**；漏一个反量化输入，重排后 scale 即与权重脱钩、静默掉精度。新增一个量化类型的 EPLB 支持分支时，先核对「反量化这条路上有几个逐专家张量」，逐个进清单。
- **correctness 验证**：开 EPLB + 该量化专家跑一次带负载不均衡（触发实际重映射）的推理，对齐关 EPLB / 非量化 baseline 的输出；重点是构造真的发生专家重排的负载，否则清单缺失可能被「未触发重映射」掩盖。
- **实现细节警示（属于参考实现、非技术本身限制）**：判据必须用 `elif quant_type in (QuantType.MXFP4, QuantType.MXFP8)` 这类**成员判断**；写成 `quant_type == MXFP4 or MXFP8`（布尔恒真）、或用独立 `if` 而非 `elif`（分支被后续覆盖）、或引用未定义的枚举成员，都会让分支形同虚设或改写错专家的清单。

## Evidence

- EPLB 适配器唯一改动文件新增 MXFP4/MXFP8 分支，把 `w13_weight_scale` / `w2_weight_scale` 与量化权重名一同列入逐专家参数清单，+9 行；已合并。溯源见 [vllm-ascend-pr-9280-ascend950-feature-eplb-support-w8a8-mxfp-and-w4a4-mxfp](https://github.com/vllm-project/vllm-ascend/pull/9280)（vllm-project/vllm-ascend，merge sha `64b05b4823ca152741a7aed2d27c77158d432bd7`，`vllm_ascend/eplb/adaptor/vllm_adaptor.py`）。
- 根因（漏 scale → 权重/scale 失配 → 精度错）由上游描述明确陈述，与合并态代码「把 scale 加入参数清单」一致。
- 精度收益仅据上游自述「修复前可能结果不正确、修复后保证 accuracy correctness」，**未提供 before→after 的量化精度数字**，不外推具体指标。

## 相关页

- [expert-parallel](../../concepts/parallelism/expert_parallel.md) —— EP / 专家分布与重映射机制的 canonical 概念页
- [hybrid-mxfp8-mxfp4](../../concepts/quantization/hybrid_mxfp8_mxfp4.md) —— MXFP8 / MXFP4 微缩放量化格式与独立 scale 布局
