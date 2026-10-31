---
type: Guide
title: Cosmos3-Nano：A3 推理与 CP/CFGP/FSDP 组合
description: 按固定适配文档准备 Cosmos3-Nano 与 Wan2.2 VAE，并区分 FSDP 参数分片域和 CP/CFGP 计算域的规模约束。
tags:
- task.implementation
- topic.model_serving
- topic.diffusion
- topic.parallelism
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-embodied-ai/21a5ed789ceb2a4b72277573f5ec5ec531b92ee1/world_model/cosmos3/README.md
  role: primary
created_at: '2026-10-29T04:09:07Z'
updated_at: '2026-10-29T12:00:02Z'
platforms:
- a3
---

# Cosmos3-Nano：A3 推理与 CP/CFGP/FSDP 组合

## 适用范围与预期产物

固定样例面向 A3，提供 T2V、I2V、V2V 的基础推理与多卡适配。产物应记录实际上游 revision、适配文件、软件环境、权重、输入 JSON、输出及并行配置。

## 准备与执行

文档环境为 CANN 9.0.0、torch_npu 2.10.0、Python 3.13。原 Cosmos 框架需与本样例的适配文件相配套；文档只给短 revision a61b292，完整复现还须解析并记录 40 位上游提交，不能把短引用当成新的固定 source。

Cosmos3-Nano 权重之外，还需在同一本地权重目录放 Wan2.2_VAE.pth；不要求为此下载完整 Wan2.2 模型。安装适配后先验证单卡 T2V，再检查 I2V/V2V 的 vision_path、权重和输出路径。

## 多卡约束

CP 按 token 序列分摊 Attention，文档范围为 1～32；CFGP 切分有条件与无条件分支，只支持 1 或 2；FSDP 的 dp-shard-size 用于参数分片。FSDP 的 DP 域独立于 CP/CFGP 域，要求：

- dp-shard-size × dp-replicate-size = WORLD_SIZE。
- WORLD_SIZE 能被 cp-size × cfgp-size 整除。

不能将三者简单相乘后当作全局卡数。

## 验证、回退与停止

逐项记录进程数、通信组、单卡峰值内存、输出有效性及固定 seed 的数值差异。文件缺失、并行度不整除、上游/适配版本不一致或输出异常时停止增加规模，回到已验证单卡配置。源文档未给受控性能对照，本批未运行推理，故不承诺吞吐收益。
