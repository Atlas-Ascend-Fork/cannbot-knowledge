---
type: Guide
title: Qwen3-30B-A3B TorchTitan SFT（原入口已移除）
description: 当前锁定源码已移除原 Qwen3 GSM8K SFT registry、文档与 converter 入口；撤下不可执行的旧命令，说明重建所需契约与当前可用导航。
tags:
- task.implementation
- topic.model_adaptation
status: deprecated
sources:
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/architecture.md
  role: primary
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/examples/qwen3_5/readme.md
  role: supporting
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/user-guides/quickstart.md
  role: supporting
created_at: '2026-06-23T00:00:00Z'
updated_at: '2026-10-29T15:32:47Z'
platforms:
- agnostic
---

# Qwen3-30B-A3B TorchTitan SFT（原样例入口已移除）

## 当前状态

本 Guide 对应的 `torchtitan_npu.models.qwen3`、`sft_qwen3_30ba3b_math` 与 `docs/recipe/sft.md` 已不在当前锁定源码中，旧 npu_* converter 配置也已退出当前组件替换机制。因此撤下该样例的一键命令、固定 GSM8K/EP8/CP4 参数及旧 ChatDataLoader 契约，避免它们被作为最新可执行方案召回；原始内容和来源保留在 Git 历史及迁移审计。

当前仓库的 Qwen3.5 多模态 debug/CPT 样例位于 `examples/qwen3_5/`，依赖上游 recipe，不能替代或证明 Qwen3-30B-A3B 的 GSM8K SFT。尤其该 VL 路径尚不支持 CP，不能沿用此页旧 CP4 配置。

## 继续构建时的核对项

若要在当前 TorchTitan 上重建 Qwen3 SFT，需要独立提供并核验模型 registry、对话数据处理、assistant label-mask、packed position、有效 token 损失与 HF adapter，再确定设备与并行范围。只复用通用 run_train.sh 或替换模型名不足以恢复原样例；本次没有创建未经验证的兼容入口。

已有可用导航：[MindSpeed Qwen3-1.7B SFT](qwen3_sft.md) 描述另一模型规格与训练栈，迁移时需要重新做权重/数据/并行配置；TorchTitan 的当前配置与 override 见 [框架说明](../../concepts/frameworks/torchtitan.md)。

## Evidence

- [architecture.md](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/architecture.md)（primary）
- [readme.md](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/examples/qwen3_5/readme.md)（supporting）
- [quickstart.md](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/user-guides/quickstart.md)（supporting）
