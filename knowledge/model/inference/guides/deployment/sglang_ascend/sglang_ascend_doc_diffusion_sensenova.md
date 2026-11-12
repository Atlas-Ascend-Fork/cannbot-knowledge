---
type: Guide
title: SGLang Diffusion SenseNova昇腾配方：融合预热与批次测量
description: 说明首次SwiGLU打包预热、FIA/norm条件回退及910C历史B1/B2数据的可比边界。
tags:
- task.implementation
- topic.diffusion
- topic.multimodal
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/cookbook/diffusion/SenseNova/SenseNova-U1.5-8B-MoT.mdx
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/models/sensenova_u1/neo_unify/modeling_qwen3.py
  role: implementation
created_at: '2026-11-08T12:33:46Z'
updated_at: '2026-11-09T04:30:20Z'
platforms: []
---

# SGLang Diffusion SenseNova昇腾配方：融合预热与批次测量

## 使用条件

SenseNova-U1在满足输入要求时自动使用NPU FIA、RMSNorm和SwiGLU；FIA/SwiGLU条件不足会回退。融合MLP首次打包gate/up权重，benchmark前应完成整请求warmup，不能只调用一个空算子。多个输出和think_mode请求顺序执行，不能与普通batch吞吐直接混算。

## 来源数据与边界

来源测一台Ascend910C，4个并发2048×2048 T2I请求、50步、CFG4、BF16。未优化B1/B2的总时长234.28/234.83秒，融合B1/B2为205.94/195.02秒；B2融合峰值reserved37850MB。表中的duration、mean latency、吞吐是不同统计量，不能把其中一列当每张推理延迟。芯片名保留来源原文，未建立整卡平台注册映射，platforms保持空。

先完整预热，验证所有优化实际命中与输出质量，再在相同并发、尺寸和步数下比较B1/B2；保留布局、有效prefix长度与fallback日志。首次 torch.cat 打包存在临时分配；随后 gate/up 权重通过 set_ 绑定到 packed 切片并共享存储，并非持续保留三份独立权重。存活权重存储与分配器 reserved 内存需分别测量，不能由打包推定额外驻留量；吞吐收益不等于延迟同幅下降。本次未复测表格或运行模型。

## 配套知识

[FIA与融合MLP](../../integration/sglang_ascend/sglang_ascend_diffusion_sensenova_attention.md)；[去噪缓存实现](../../integration/sglang_ascend/sglang_ascend_diffusion_sensenova_cache.md)。
