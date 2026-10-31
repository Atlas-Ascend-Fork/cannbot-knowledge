---
type: Guide
title: Qwen3-30B-A3B：A3 上的 veRL / TorchTitan GRPO 训练
description: 区分 TorchTitan actor/ref 与 vLLM rollout，并按固定 recipe 的版本矩阵、patch 和重编译要求验证 Qwen3 GRPO 路径。
tags:
- task.implementation
- topic.reinforcement_learning
- topic.parallelism
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/llm_rl/qwen3/verl-torchtitan/README.md
  role: primary
created_at: '2026-10-29T04:09:07Z'
updated_at: '2026-10-29T15:39:15Z'
platforms:
- a3
---

# Qwen3-30B-A3B：A3 上的 veRL / TorchTitan GRPO 训练

## 适用范围与产物

固定 recipe 使用 Atlas A3 16 卡，TorchTitan 承担 actor/ref，vLLM 承担 rollout。目标产物是可复现的环境与依赖清单、数据/权重路径、启动配置、训练日志和验证结果。它是独立于 [Qwen3 MindSpeed 长序列 RL](qwen3_rl.md) 的后端路径，不能直接复用后者的性能结论。

## 版本与实施

源矩阵固定 veRL e9aa879bc61821621a36881ea305eaa0785520c1、TorchTitan ac13e536c84e7f6647b14fa9375c3c8a8a2b8578、TorchTitan-NPU（安装脚本锁定的兼容版本）；rollout 为 vLLM 0.15.0 / vLLM-Ascend 0.15.0rc1，torch 2.12.0 / torch_npu 2.12.0rc1。这是 recipe 的成套兼容组合，依赖仓 master 的新提交不能替代它。

先准备固定源码与环境，再由样例构建入口应用对应仓库的 patch。由于 TorchTitan 与 vLLM-Ascend 的依赖版本存在差异，样例在复制包代码前重编译安装 vLLM-Ascend；仅修改 Python 包路径不足以保证融合算子二进制匹配。另有 Qwen 初始化与 torchair hint_int 导入适配。

准备 GSM8K parquet 和完整 HF 格式权重，再核对模型/数据路径、可见设备、NUM_GPUS、FSDP/TP/EP 与 rollout TP/DP，执行该 recipe 的 GRPO 脚本。目录已位于 llm_rl/qwen3/verl-torchtitan，不再从旧 qwen3 根路径寻找。

## 验证、回退与停止

先验证依赖 import、patch 应用、权重加载和短程训练，再看梯度、reward 与验证曲线。源首步示例为 GBS=8、n=2、prompt=256、response=4096，653 秒是首步时间，不是稳态吞吐。本批未执行训练。

版本、二进制或 patch 不兼容时停止扩大运行，回到成套固定依赖；保留失败日志，不通过跳过初始化或修改样本口径掩盖错误。
