---
type: Concept
title: DCP / HF Checkpoint（torchtitan-npu 断点恢复与权重导出）
description: 当前 TorchTitan checkpointer 配置、DCP/HF 格式与加载优先级、量化 HF 模型限制、NPU 同步 writer、NovaSwap 异步边界及 SHA-256 完整性校验。
tags:
- task.optimization
- topic.checkpointing
status: stable
sources:
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/developer_guides/checkpoint.md
  role: primary
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/extensions/torchtitan/components/checkpoint.py
  role: implementation
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/extensions/components/validation.py
  role: implementation
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/tools/checkpoint_conversion/convert_to_hf.py
  role: implementation
created_at: '2026-06-23T00:00:00Z'
updated_at: '2026-10-29T15:24:41Z'
platforms:
- agnostic
---

# DCP / HF Checkpoint（训练恢复与权重导出）

## Summary

DCP 保存模型、optimizer、lr_scheduler、dataloader 与训练状态；HF safetensors 只表示模型权重，适合初始化和导出，不能作为完整训练断点。当前配置基于 `torchtitan.components.checkpointer.CheckpointManager`；旧 `components.checkpoint` 为兼容再导出，NPU 扩展通过 `Config.extensions` 接入，不再使用旧 `config/configs.py` 的 CheckpointConfig。

## 必要开关和加载优先级

`checkpoint.enable=False` 时既不保存也不加载，即使提供 initial_load_path。V4 registry 默认 interval100，V3.2 debugmodel 默认 interval10、last_save_model_only=False，两者 checkpoint 默认均关闭。

目录一般为 `{dump_folder}/{checkpoint.folder}/step-N/`，含 `.metadata` 与 `*.distcp`。load_step=-1 选最新 step；已有输出目录的可用 checkpoint 优先于 initial_load_path，后者又优先于 hf_assets_path。新实验使用新的 dump-folder，避免意外续训旧状态。

initial_load_path 要求绝对路径或远程 URI。默认 initial_load_model_only=True；完整恢复需 `--checkpoint.no-initial-load-model-only`，可用 exclude_from_loading 排除 optimizer、lr_scheduler、dataloader 等。DCP 能重分片，但是否支持目标并行拓扑还取决于模型 adapter/optimizer，不能由格式能力承诺所有跨 world size 组合。

## 当前配置与 CLI

| 配置 | 语义 |
|---|---|
| enable / folder / interval | 保存与加载总开关、子目录、保存步数间隔 |
| load_step / load_only | 指定恢复 step / 只加载不保存 |
| initial_load_path / initial_load_model_only | 初始来源 / 是否只加载模型 |
| initial_load_in_hf / initial_load_in_hf_quantized | HF 权重 / 量化 HF 权重读取 |
| last_save_model_only / last_save_in_hf | 最后一步仅模型 / HF 导出；HF 要求 model-only |
| export_dtype | float16、bfloat16 或 float32 |
| keep_latest_k | 0 保留全部，不能设置1 |
| async_mode | disabled、async、async_with_pinned_mem；受 optimizer 兼容条件约束 |
| enable_first_step_checkpoint | 首步保存，用于验证路径 |
| create_seed_checkpoint | 创建未应用并行切分的初始状态 |

Python 用下划线，当前 tyro CLI 用连字符，如 `--dump-folder`、`--checkpoint.load-step 500`。布尔关闭使用 `--checkpoint.no-enable`，不是字段后跟 false；列表使用逗号串单一参数。不要再给新入口传旧 sync_files/drop_page_cache_after_save/empty_cache_after_save 字段。

```python
from torchtitan.components.checkpointer import CheckpointManager
checkpoint = CheckpointManager.Config(
    enable=True, folder="checkpoint", interval=100,
    keep_latest_k=5, async_mode="disabled",
)
```

## NPU writer、swap 和完整性清单

extension CheckpointManager 的同步 native DCP 使用 `FileSystemWriter(per_thread_copy_ahead=0)`，处理 Virtual Optimizer storage 与 copy-ahead 的兼容；async 或 HF 委托上游。

NovaSwap 支持同步与 CPU snapshot 的 async，但其 live CPU views 不兼容 async_with_pinned_mem，启用时构造器直接拒绝。fresh-load、未使用参数的状态初始化与搬运依赖见 [Swap](swap_optimizer.md) 和 [Virtual](virtual_optimizer.md)，不能沿用旧 CPU cache/zero-storage 容器接口。

`--checkpoint.extensions.verify-hash-manifest` 默认关闭，开启后在保存前写 pending marker，保存完成后生成 SHA-256 清单，加载权重前校验。当前实现对清单缺失会抛 FileNotFoundError，pending 或 hash mismatch 也拒绝加载；与 Config 注释中的“无清单静默通过”不同。rank0 判定尚无跨 rank 广播，详细边界见 [检查点哈希清单](checkpoint_hash_manifest.md)。

## HF 权重与量化格式

HF 初始化需同时开启 checkpoint 和 initial_load_in_hf，保持 initial_load_model_only=True；目录准备 safetensors 或索引以及 config/tokenizer。最后一步 HF 导出需 model adapter 与 last_save_in_hf、last_save_model_only=True，不保存优化器或训练进度。

initial_load_in_hf_quantized 当前只由 DeepSeek V4 adapter 选择两类 MX reader：固定格式 `.weight + E8M0 .scale`，以及 export_quantized_hf.py 的 safetensors metadata 协议，后者优先探测。V4.1 等其他模型未选择这些 reader，应先反量化为 BF16，不能把开关存在当作任意模型通用支持。

## Seed 与离线导出

seed checkpoint 在 NGPU=1、DP replicate/shard、TP/PP/CP/EP 全为1时创建未切分状态，生成 step-0 后让多卡任务重分片加载；不是用同一个 seed 重随机初始化来替代权重一致性。

当前 NPU 离线工具入口已移动为 `torchtitan_npu/tools/checkpoint_conversion/convert_to_hf.py`，接收 input_dir/output_dir、model_name、model_flavor、hf_assets_path、export_dtype 等。model_name 可为完整 NPU 模块名，短名则按 torchtitan.models 前缀导入；默认 llama3/8B 不适用于所有模型。它还包含 CPU Engram/EMA 状态导出与分文件并行读取能力。输入需完整 DCP step 目录，按实际 registry flavor 和 adapter 选择；不要继续使用旧 deepseek_v32 flavor 示例或旧模型侧 save_patch 字段。

## 验证

分别核对加载日志、模型权重与 optimizer moments/step、调度器和数据进度，再验证续训第一步。模型-only/HF 验证不能代替完整恢复验收。本次为固定源码核对，未执行 NPU 保存、训练或跨拓扑恢复。

## Evidence

- [checkpoint.md](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/developer_guides/checkpoint.md)（primary）
- [checkpoint.py](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/extensions/torchtitan/components/checkpoint.py)（implementation）
- [validation.py](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/extensions/components/validation.py)（implementation）
- [convert_to_hf.py](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/tools/checkpoint_conversion/convert_to_hf.py)（implementation）

## Links

- [TorchTitan NPU](../frameworks/torchtitan.md)
- [Swap Optimizer](swap_optimizer.md)
- [Virtual Optimizer](virtual_optimizer.md)
- [V3.2 训练](../../guides/recipes/deepseek_v32_pretrain.md)
