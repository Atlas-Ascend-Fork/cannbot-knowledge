---
type: Concept
title: DCP / HF Checkpoint（torchtitan-npu 断点恢复与权重导出）
description: torchtitan-npu Checkpoint：DCP（.metadata+*.distcp，存 model+optimizer+lr_scheduler+dataloader+train_state，可跨并行重分片，最适断点续训）vs HF safetensors（仅权重，用于开源初始化/导出）。CheckpointManager.Config + NPU 扩展项 sync_files(True)/drop_page_cache_after_save(False)/empty_cache_after_save(True)/create_seed_checkpoint/enable_first_step_checkpoint/enable_ft_dataloader_checkpoints。tyro CLI（--checkpoint.no-<field>、列表逗号串）。seed checkpoint 单卡 CPU 生成 step-0 供多卡重分片。离线转换 scripts/checkpoint_conversion/convert_to_hf.py。与 Swap Optimizer DCP 集成（pending swap 等待 + CPU cache 保存）。
tags:
- task.optimization
- topic.checkpointing
status: stable
sources:
- resource: https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/README.md
  role: primary
- resource: https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/docs/feature_guides/checkpoint.md
  role: supporting
created_at: '2026-06-23T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# DCP / HF Checkpoint（torchtitan-npu 断点恢复与权重导出）

[torchtitan](../frameworks/torchtitan.md) 训练中的 checkpoint 由
`torchtitan.components.checkpoint.CheckpointManager.Config` 提供，torchtitan-npu
通过 `CheckpointConfig`（`torchtitan_npu/config/configs.py`）补充 NPU 写盘与缓存控制。
两类权重格式 DCP 与 HF safetensors 在语义、配置项、seed checkpoint 与离线转换流程上各有分工，下文逐项展开。

## 两类格式

| 格式 | 典型文件 | 适用场景 | 训练状态 |
| --- | --- | --- | --- |
| **DCP**（PyTorch Distributed Checkpoint） | `.metadata`、`*.distcp` | 断点续训、不同并行切分间重分片加载 | 含 model + optimizer + lr_scheduler + dataloader + `train_state` |
| **Hugging Face** | `model.safetensors`、`model.safetensors.index.json` | 从开源权重初始化、导出给推理/其它生态 | 仅模型权重 |

- DCP 因可保存完整分布式训练状态，**最适合断点续训**，且可在不同 TP/DP/PP/EP 切分间重分片加载。保存目录形如 `outputs/<job_name>/checkpoint/step-1000/`：`outputs/<job_name>` 来自 `--dump_folder`、`checkpoint` 来自 `checkpoint.folder`、`step-1000` 是训练步数。
- HF safetensors 不含优化器/学习率调度器/训练步数，仅用于从预训练权重启动或训练后导出权重。

## 常用配置项（CheckpointManager.Config）

| 配置项 | 说明 |
| --- | --- |
| `enable` | 是否启用 checkpoint，**加载和保存都需打开**；`enable=False` 时即使设了 `initial_load_path` / `initial_load_in_hf=True` 也不执行加载 |
| `folder` | checkpoint 子目录名，最终路径 `{dump_folder}/{folder}` |
| `interval` | 每隔多少 step 保存一次 DCP checkpoint |
| `load_step` | 指定加载某一步；`-1` 自动加载最新 checkpoint |
| `initial_load_path` | 当前输出目录无 checkpoint 时从该路径初始化 |
| `initial_load_model_only` | 从 `initial_load_path` 加载时是否只加载模型权重，默认 `True` |
| `initial_load_in_hf` | 将 `initial_load_path` 或 `hf_assets_path` 当作 HF safetensors 加载 |
| `last_save_model_only` | 训练最后一步是否只保存模型权重，默认 `True` |
| `last_save_in_hf` | 训练最后一步是否保存为 HF safetensors |
| `export_dtype` | `last_save_model_only=True` 时最终权重导出 dtype |
| `load_only` | 只加载不保存，适合验证或调试 |
| `keep_latest_k` | 只保留最近 k 个 checkpoint，`0` 表示全部保留 |
| `exclude_from_loading` | 从 DCP 加载时排除部分状态（如 `optimizer,lr_scheduler,dataloader,train_state`）；CLI 必须用英文逗号分隔 |
| `async_mode` | DCP 异步保存方式，常用 `disabled` / `async` |
| `create_seed_checkpoint` | seed checkpoint 模式，见下文 |
| `enable_first_step_checkpoint` | 是否在 step 1 强制保存一次，常用于校验保存路径连通性 |
| `initial_load_in_hf_quantized` | 从 HF 量化权重加载，使用前需先开启 `initial_load_in_hf` |
| `enable_ft_dataloader_checkpoints` | TorchFT 场景下是否独立保存 per-replica dataloader 状态 |

### NPU 扩展（CheckpointConfig）

`torchtitan_npu/config/configs.py` 的 `CheckpointConfig(CheckpointManager.Config)`
补充三个 NPU 写盘/缓存控制项（默认值如下，verbatim）：

```python
@dataclass(kw_only=True, slots=True)
class CheckpointConfig(CheckpointManager.Config):
    """Checkpoint config with NPU-specific writer and cache controls."""
    sync_files: bool = True
    drop_page_cache_after_save: bool = False
    empty_cache_after_save: bool = True
```

- `sync_files`（默认 `True`）：写盘后是否 `FileSystemWriter` fsync 同步；设 `False` 降低保存耗时但异常退出时落盘可靠性更弱。
- `drop_page_cache_after_save`（默认 `False`）：保存后请求释放 checkpoint 文件占用的 Linux page cache，不删除文件，只降低主机内存压力。
- `empty_cache_after_save`（默认 `True`）：保存后清理 NPU caching allocator，释放临时 checkpoint 缓存后再恢复训练。

### tyro CLI 约定

- **布尔字段反转**：用 `--checkpoint.no-<field>` 把 bool 置 False（如 `--checkpoint.no-load-only`），不是 `--no-checkpoint.<field>` 也不是 `--checkpoint.<field> false`。
- **列表字段**：`exclude_from_loading` 这类列表用英文逗号串成单个参数（`--checkpoint.exclude_from_loading optimizer,lr_scheduler,dataloader`）；空格分隔会被 tyro 当成子命令报 *Unrecognized options*。
- **覆盖 registry 默认值**：`config_registry.py` 已设的字段（如 dsv32 4 层 debug 把 `load_only=True`、`initial_load_path` 写死）需 CLI 显式覆盖，只追加 `--checkpoint.enable` 不会清掉。

## 保存与读取 DCP

```python
from torchtitan.components.checkpoint import CheckpointManager
checkpoint=CheckpointManager.Config(
    enable=True, folder="checkpoint", interval=100,
    keep_latest_k=5, async_mode="disabled",
)
```

- 自动续训：用相同 `--dump_folder` + `--checkpoint.folder` 重启即从最新 `step-*` 恢复；`--checkpoint.load_step 500` 指定步数。
- 从另一 DCP 目录初始化：用新 `dump_folder`，`--checkpoint.initial_load_path .../step-500`；默认只加载模型权重，需完整恢复优化器/调度器/步数时设 `initial_load_model_only=False`。
- **优先级**：若 `{dump_folder}/{checkpoint.folder}` 已有可用 checkpoint，框架优先续训并忽略 `initial_load_path`。整体加载优先级为：现有可用 checkpoint > `initial_load_path` > `hf_assets_path`。因此从新权重启动实验时需换新 `dump_folder` 或清理旧 checkpoint 目录，否则旧目录里的可用 checkpoint 会抢先续训、覆盖从新权重启动的意图。

## 读取 / 保存 HF 权重

- 读取：启用 `--checkpoint.initial_load_in_hf`，路径含 `model.safetensors` 或 `model.safetensors.index.json`（建议含 tokenizer、`config.json`）；不显式传 `initial_load_path` 则回退顶层 `hf_assets_path`（`initial_load_path` 优先级更高）。HF 权重只能作模型权重，不恢复优化器/步数。
- 保存：同时启用 `--checkpoint.last_save_in_hf` 与 `--checkpoint.export_dtype bfloat16`（默认 `last_save_model_only=True`），最后一步导出 HF safetensors。该目录仅用于导出，不适合作完整断点恢复；保存需 state_dict 转换 + safetensors 合并，耗时通常高于 DCP。

## Seed Checkpoint

先在单卡 CPU 初始化模型，再让多卡任务通过 DCP 重分片加载。创建时关闭所有并行切分并用 `NGPU=1`：

```bash
NGPU=1 ... bash scripts/run_train.sh \
  --checkpoint.enable --checkpoint.create_seed_checkpoint \
  --parallelism.data_parallel_replicate_degree 1 \
  --parallelism.data_parallel_shard_degree 1 \
  --parallelism.tensor_parallel_degree 1 \
  --parallelism.pipeline_parallel_degree 1 \
  --parallelism.context_parallel_degree 1 \
  --parallelism.expert_parallel_degree 1
```

生成的 `step-0` 后续可作为 `checkpoint.initial_load_path` 用于多卡重分片加载。这是
[deepseek-v32-pretrain](../../guides/recipes/deepseek_v32_pretrain.md) 等大模型多卡 bring-up 的标准前置步骤。

## 离线转换 DCP → HF

`scripts/checkpoint_conversion/convert_to_hf.py` 可对**任意 step 的 DCP checkpoint**离线转换（不依赖训练最后一步自动导出）：

```bash
python scripts/checkpoint_conversion/convert_to_hf.py \
  ./outputs/dsv32_4layers/checkpoint/step-1000 \
  ./outputs/dsv32_4layers/hf_output \
  --model_name deepseek_v32 \
  --model_flavor deepseek_v32_671b_4layers_debug \
  --hf_assets_path ./assets/hf/DeepSeek-V3.2 \
  --export_dtype bfloat16
```

- 位置参数 `input_dir` / `output_dir`；可选 `--model_name`（默认 `llama3`）、`--model_flavor`（默认 `8B`）、`--hf_assets_path`、`--export_dtype`（`float16`/`bfloat16`/`float32`，默认 `float32`）。
- `input_dir` 必须是完整 DCP step 目录（含 `.metadata`）；脚本通过 `state_dict_adapter` 转换，并对含 GMM（grouped matmul）专家权重的 checkpoint 做预处理。输出形如 `model-00001-of-00001.safetensors` + `model.safetensors.index.json`。

## 模型侧 save patch（DSV3.2 / V4 高级场景）

DeepSeek-V3.2 / DeepSeek-V4 的 state_dict adapter 含模型侧保存 patch（`model.py` 的 `model.Config`），用于专家权重格式转换等高级场景。日常保存/加载优先用 `CheckpointManager.Config` 的 DCP/HF 配置；仅模型配置明确需要时才设以下字段（verbatim 默认值）：

```python
save_format: str = "dcp"            # dsv4 部分 flavor 注册为 "hf"
save_expert_format: str | None = None   # 如 "gmm"
hf_save_dir: str | None = None
save_patch_enabled: bool = False
```

## Swap Optimizer 集成

[swap-optimizer](swap_optimizer.md) 把优化器状态在 host/device 间换入换出以省显存。开启后优化器 state 仍随 DCP checkpoint 完整保存与恢复（DCP 的 `optimizer` 键覆盖之），断点续训语义不变；如只想恢复模型不恢复优化器，用 `--checkpoint.exclude_from_loading optimizer`。

## Evidence / Links

- 源文档：[torchtitan-npu](https://gitcode.com/cann/torchtitan-npu) — [`docs/feature_guides/checkpoint.md`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/docs/feature_guides/checkpoint.md)
- 代码（@8f128cd）：
  - CheckpointConfig NPU 扩展：https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/torchtitan_npu/config/configs.py
  - 离线转换：https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/scripts/checkpoint_conversion/convert_to_hf.py
  - DSV3.2 save patch：https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/torchtitan_npu/models/deepseek_v32/model.py
- 相关页：[torchtitan](../frameworks/torchtitan.md) · [swap-optimizer](swap_optimizer.md) · [deepseek-v32-pretrain](../../guides/recipes/deepseek_v32_pretrain.md)