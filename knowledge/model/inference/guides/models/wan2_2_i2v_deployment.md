---
type: Guide
title: Wan2.2-I2V A2/A3 并行与缓存生成验收流程
description: Wan2.2-I2V A2/A3 并行与缓存生成验收流程，串联固定版本配置、来源冲突、精度与性能验证以及回退入口。
tags:
- task.implementation
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/wan2.2-i2v/wan2.2-i2v_optimization.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/wan2.2-i2v/README.md
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/06656b0519fde3256eed1b2a77e5327898e0b00f/models/wan2.2-i2v/infer.sh
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/06656b0519fde3256eed1b2a77e5327898e0b00f/models/wan2.2-i2v/config/14b_cfg2_ulysses4.yaml
created_at: '2026-10-21T09:56:21Z'
updated_at: '2026-10-22T01:37:00Z'
platforms:
- a2
- a3
---
# Wan2.2-I2V A2/A3 并行与缓存生成验收流程

## 目标、输入与产物

面向固定来源中的 Wan2.2-I2V 实现，输入包括平台、权重、实际配置和任务指标；产物为可追溯配置、正确性/性能记录及回退入口。模型结构由[模型 Concept](../../concepts/models/wan2_2_i2v.md)维护。以下描述固定版本实践，不能当作当前所有软件版本的部署保证。

## 1. 固定启动版本与输入

旧优化文档的generate.py/run.sh与后续infer.sh/YAML入口分开使用。2c45117 README明确A2/A3单/多卡；普通输入为参考图、prompt、seed、尺寸、帧数和步数。统一14b_single与14b_cfg2_ulysses4分别配置单卡缓存或CFG2×Ulysses4/VAE/FSDP，不能混读旧JSON与新YAML参数名。启动机制见 [多模态启动](../../concepts/frameworks/mm_inference_launch.md)。

## 2. 核对融合与数值

Attention的实际长度、BNSD与输出transpose/contiguous、interleave RoPE、RMSNorm各自对齐原模型。三个LN与modulate的融合只在对应gamma/beta条件下讨论；旧文档FusedLayerNormModulate的scale未定义，属于不可直接复制的片段，必须先核对实际实现，不能作为开箱修复配方。

## 3. 分别验收并行和cache

VAE空间边界由 [VAE流程](../../optimizations/rules/vae_multicard_spatial_parallel.md)维护；CFG条件/无条件预测的通信由 [CFG流程](../../optimizations/rules/cfg_parallel_sample_level_diffusion.md)维护；Ring异步本地/远程FA与LSE合并由 [Ring流程](../../optimizations/rules/ring_attention_comm_compute_overlap_lse_merge.md)维护。逐一确认通信组和输出，不把示意当作所有组合已运行。

Step cache的旧入口JSON为NoCache/FBCache/TeaCache，cond/uncond状态须分开。旧文档给出的module/dit_cache_step/cache_step.py在固定2f82d10下获取失败，不将该路径视为已恢复实现；新YAML的dit_cache.method按其版本入口处理。阈值、warmup与多项式系数是旧样例参数，不保证其他帧数/输入质量。缓存规则见 [cache与SP规则](../../optimizations/rules/dit_cache_with_sequence_parallel.md)。

## 4. 验证任务而非片段

保存生成视频并验收参考图一致性、时间连贯性、内存和端到端时延；旧优化文档未给完整benchmark，后续README的数字须另绑定该版本配置，不在迁移中补造测量或阈值。

## 验证、停止与回退

保存实际权重、软件版本、平台、并行组、输入与输出；以未启用待验优化的路径作对应基线，逐项比较 logits/任务质量、时延和峰值内存，并分别记录冷启动、warmup 与稳态重复测量。遇到源中未覆盖的形状、后端或平台时停止套用。失败后恢复对应版本的配置、权重与编译缓存，再按关联 Runbook 排查；没有实际跑通的回退不写为已验证。

本卡未记录独立的模型执行或硬件复测。来源自报和输出“看起来正常”不能替代本部署的精度验收；执行后应另存实际环境、配置和测量记录。


## Evidence

- [固定来源 1](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/wan2.2-i2v/wan2.2-i2v_optimization.md)
- [固定来源 2](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/wan2.2-i2v/README.md)
- [固定来源 3](https://gitcode.com/cann/cann-recipes-infer/blob/06656b0519fde3256eed1b2a77e5327898e0b00f/models/wan2.2-i2v/infer.sh)
- [固定来源 4](https://gitcode.com/cann/cann-recipes-infer/blob/06656b0519fde3256eed1b2a77e5327898e0b00f/models/wan2.2-i2v/config/14b_cfg2_ulysses4.yaml)

## 历史 JSON 配置对照

下例来自旧 2f82d10 优化文档，不是后续统一 YAML 的字段契约；旧 cache_step 路径仍未恢复，不作为已运行配置。

```json
{
 "cache_forward": "NoCache",
 "enable_separate_cfg": true,
 "FBCache": {"cache_name": "FBCache", "rel_l1_thresh": 0.05, "latent": "latent", "judge_input": "cache_latent"},
 "TeaCache": {"cache_name": "TeaCache", "rel_l1_thresh": 0.1,
 "coefficients": [733.226126, -401.131952, 67.5869174, -3.149879, 0.0961237896],
 "latent": "latent", "warmup": 2, "judge_input": "modulated_inp"}
}
```
