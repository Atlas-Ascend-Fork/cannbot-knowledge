---
type: Guide
title: Wan2.1 的 Ring-SP 上游单案例性能观测
description: 保留 torch_npu 2.10 下单NPU与双NPU Ring-SP 的工作负载、阶段耗时和重复信息缺口。
tags:
- task.implementation
- task.optimization
- topic.model_serving
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/optimization/ring_sp_performance.mdx
  role: primary
created_at: '2026-11-08T12:09:58Z'
updated_at: '2026-11-08T12:09:58Z'
platforms: []
---

# Wan2.1 的 Ring-SP 上游单案例性能观测

## 上游观察与适用范围

来源比较Wan2.1-T2V-1.3B-Diffusers，torch_npu2.10.0，提示词为a cat is playing piano。基线ulysses1/ring1、num-gpus1；实验ulysses1/ring2、num-gpus2，均sglang generate并保存输出。页面只称Ascend NPU，没有具体产品，因此draft空平台；本次未跑生成。

| 阶段 | 单NPU基线秒 | 双NPU Ring秒 | 来源比值 |
|---|---:|---:|---:|
| Input validation | 0.0002 | 0.0003 | 0.67× |
| Text encoding | 3.5820 | 3.5936 | 1.00× |
| Latent preparation | 0.0055 | 0.0007 | 7.86× |
| Timestep preparation | 0.0007 | 0.0008 | 0.88× |
| Denoising | 239.2580 | 121.2788 | 1.97× |
| Decoding | 16.4969 | 13.8685 | 1.19× |
| Total，pixel生成结束 | 266.50 | 141.86 | 1.88× |

主要差异来自denoising，但资源同时由1变2；1.88×是延迟比，不是每卡吞吐提高1.88×。来源未报告独立重复、warmup、分辨率/帧数、采样步数、CANN/芯片和图像质量对照。单prompt结果只能作为复现线索，不能推广到其他模型、Ring degree或多节点。复现需补全这些条件并验证输出质量及通信开销。

## Evidence

- [sglang：docs/docs/hardware-platforms/ascend-npus/optimization/ring_sp_performance.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/optimization/ring_sp_performance.mdx)（primary）
