---
type: Guide
title: Qwen3-30B-A3B torchtitan-npu SFT（GSM8K + Ulysses CP 开箱配置）
description: Qwen3-30B-A3B torchtitan-npu SFT 开箱配置（MODULE=torchtitan_npu.models.qwen3 CONFIG=sft_qwen3_30ba3b_math，GSM8K）：seq_len4096/bs1/steps100/lr1e-5 cosine，selective AC，EP8+context_parallel_degree4(Ulysses CP)+dp_shard-1，converters npu_rms_norm/rope/permute/gmm。SFT chat 数据流水：chat-template 渲染→增量前缀重 tokenize 定位 prompt/response 边界并 label-mask（loss 仅 assistant）→短样本贪心 packing 进一个 seq_len 窗口（EOS 分隔+逐文档 position 重置）→超长样本丢弃。Qwen3 thinking 经 reasoning_content。仅单轮。区别既有 MindSpeed 版 qwen3-sft（1.7B dense/alpaca）。
tags:
- task.implementation
- topic.model_adaptation
status: stable
sources:
- resource: https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/README.md
  role: primary
- resource: https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/docs/recipe/sft.md
  role: supporting
created_at: '2026-06-23T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# Qwen3-30B-A3B torchtitan-npu SFT（GSM8K + Ulysses CP 开箱配置）

## Summary

[torchtitan](../../concepts/frameworks/torchtitan.md) 在昇腾上的开箱即用 SFT（监督微调）配置：对 **Qwen3-30B-A3B（MoE，A3B = 激活 3B / 总 30B）**在 **GSM8K 数学推理数据集**上做指令微调，内建一条「对话数据 → chat-template 渲染 → prompt label-mask → greedy packing」的自动数据流水线，并支持 **Ulysses Context Parallel** 长序列训练。一键启动：

```bash
MODULE=torchtitan_npu.models.qwen3 CONFIG=sft_qwen3_30ba3b_math bash scripts/run_train.sh
```

配置入口是注册函数 `sft_qwen3_30ba3b_math()`（`torchtitan_npu/models/qwen3/config_registry.py`），返回一个完整的 `Trainer.Config`——torchtitan 的「config 即代码」范式（对比同框架预训练页同样以注册函数承载配置）。

与 [qwen3-sft](qwen3_sft.md) 是昇腾 SFT 的两条独立技术路线：那篇走 **MindSpeed-LLM + Megatron mcore** 栈、**Qwen3-1.7B dense**、**alpaca** 指令集、**单卡 A3**、需 HF↔mcore 权重互转的四步脚本链；这条走 **torchtitan-npu（原生 FSDP/DTensor）**、**Qwen3-30B-A3B MoE**、**GSM8K**、**EP=8 + Ulysses CP=4** 的多卡 MoE 微调、直接从 HF 权重加载无需格式互转。

## 训练配置

| 维度 | 配置（源自 `sft_qwen3_30ba3b_math()`） |
| --- | --- |
| 模型 | Qwen3-30B-A3B（MoE，`model_registry("30B-A3B")`，HF 权重 `./assets/hf/Qwen3-30B-A3B`） |
| 阶段 | SFT（监督微调） |
| 框架 | torchtitan-npu（`MODULE=torchtitan_npu.models.qwen3`） |
| 数据集 | `openai/gsm8k`（`name="main"`, `split="train"`），`ChatDataLoader` |
| 序列长度 | `seq_len=4096` |
| 批 / 步 | `local_batch_size=1`，`steps=100`，`metrics.log_freq=1` |
| 优化器 | `lr=1e-5`；LR 调度 `decay_type="cosine"`、`warmup_steps=10`、`decay_ratio=0.9`、`min_lr_factor=0.1` |
| 激活重计算 | `activation_checkpoint.mode="selective"` |
| 算子转换 | `npu_rms_norm` / `npu_rope` / `npu_permute` / `npu_gmm`（见下） |

### 并行配置（MoE + Ulysses CP）

```python
parallelism=ParallelismConfig(
    data_parallel_replicate_degree=1,
    data_parallel_shard_degree=-1,      # FSDP，按可用卡数自动铺满
    tensor_parallel_degree=1,           # TP=1
    pipeline_parallel_degree=1,         # PP=1
    expert_parallel_degree=8,           # EP=8（MoE 专家并行）
    expert_tensor_parallel_degree=1,
    context_parallel_degree=4,          # Ulysses CP=4，长序列
)
```

`dp_shard=-1` 让 FSDP 自动按可用卡数铺满分片；MoE 专家走 **EP=8**、`expert_tensor_parallel=1`；长序列由 **Ulysses CP=4** 承载，TP=PP=1。Ulysses CP 的实现原理与约束见 [custom-cp-dsa](../../concepts/parallelism/custom_cp_dsa.md)（CLI 覆盖：`--parallelism.context_parallel_degree 4`）。

## NPU 算子转换

配置通过 `model_converters` 注入 4 个 NPU 融合算子转换器，把 PyTorch 原生实现替换为昇腾融合算子（见 [npu-fused-op-converters](../../concepts/frameworks/npu_fused_op_converters.md)）：

```python
model_converters=ModelConvertersContainer.Config(converters=[
    get_model_converter_config("npu_rms_norm"),
    get_model_converter_config("npu_rope"),
    get_model_converter_config("npu_permute"),
    get_model_converter_config("npu_gmm"),
])
```

其中 `npu_permute` / `npu_gmm`（grouped matmul）服务于 MoE 路由后的专家 token 重排与分组矩阵乘——这正是 30B-A3B 相比 dense 模型多出的算子需求。

## SFT 对话数据流水线

数据预处理写在 config 函数内的 `process_sample`：以 GSM8K 为例，把 `answer` 字段按 `####` 切成推理与最终答案，构造单轮对话消息列表。

```python
def process_sample(sample):
    answer = sample["answer"]
    reasoning, final_answer = answer.rsplit("####", 1)
    return [
        {"role": "user", "content": sample["question"]},
        {"role": "assistant",
         "reasoning_content": reasoning.strip(),
         "content": final_answer.strip()},
    ]
```

`reasoning_content` 字段对应 **Qwen3 thinking-mode**（思考过程与最终回答分离）。框架拿到消息列表后，`ChatDataLoader`（`torchtitan.hf_datasets.text_datasets.ChatDataLoader`）自动完成 4 步：

1. **chat-template 渲染**——调用 tokenizer 的 chat template，把消息列表渲染成完整文本。
2. **增量前缀重 tokenize 定位边界 + prompt label-mask**——通过增量前缀重新 tokenize 找到 prompt/response 边界，对 prompt 部分做 label mask，**仅对 assistant 回复计算 loss**。
3. **greedy packing**——把多个短样本贪心打包进同一个 `seq_len` 窗口，用 EOS 分隔，并做 per-document position 重置（每文档位置编码归零）。
4. **超长样本丢弃**——token 数超过 `seq_len` 的样本被**直接丢弃而非截断**，日志打印 `Dropping sample`。可增大 `seq_len` 或开启 Ulysses CP 来容纳更长样本。

> **限制**：当前仅支持**单轮对话**（一条 user + 一条 assistant），暂不支持多轮。

`process_sample` 需返回 `[{role:user,content:...}, {role:assistant,content:...}]` 形式的消息列表；可选 `reasoning_content` 启用 thinking-mode。

## 权重加载与保存

SFT 默认**直接从 HuggingFace 格式加载**预训练权重，无需 mcore 风格的格式互转：

```python
checkpoint=CheckpointConfig(
    enable=True, folder="checkpoint", load_only=False,
    initial_load_in_hf=True,
    initial_load_path="./assets/hf/Qwen3-30B-A3B",
)
```

> **注意**：`checkpoint.folder` 不能与 `checkpoint.initial_load_path` 相同，否则框架会跳过 HuggingFace 权重加载。换自己的权重时同步改 `initial_load_path` 与 `hf_assets_path`；仅调试不保存可设 `--checkpoint.load_only`。`dataloader.infinite` 默认 `true`（数据集无限循环），设 false 则遍历一轮后停止（tyro bool flag：`--dataloader.infinite` / `--dataloader.no-infinite`）。

另有 `qwen3_06b_test()` 烟雾测试配置：复用上游 `qwen3_0_6b` 预训练 config，换成 `model_registry("0.6B")`、仅注入 `npu_rms_norm`/`npu_rope` 两个转换器、数据集 `c4_test`、`warmup_steps=20`、`steps=100`、`initial_load_in_hf=True`——用于在小模型上快速验证 SFT 链路通畅。

## Evidence

- [torchtitan-npu](https://gitcode.com/cann/torchtitan-npu) — [`docs/recipe/sft.md`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/docs/recipe/sft.md)（SFT 文档：Qwen3-30B-A3B 一键启动、数据预处理 4 步自动流水线、消息格式与 thinking-mode、Ulysses CP、HF 权重加载/保存、infinite/Dropping sample 常见问题）
- [torchtitan-npu](https://gitcode.com/cann/torchtitan-npu) — [`torchtitan_npu/models/qwen3/config_registry.py`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/torchtitan_npu/models/qwen3/config_registry.py)（`sft_qwen3_30ba3b_math()` 完整 `Trainer.Config`：模型规格、4 个算子转换器、lr/调度、并行 EP=8/CP=4、`ChatDataLoader`/`process_sample`、checkpoint；`qwen3_06b_test()` 烟雾配置）

## Links

- [torchtitan](../../concepts/frameworks/torchtitan.md)（本配置所属训练框架：torchtitan-npu 的 config-as-code 范式、`Trainer.Config` 注册函数、`MODULE`/`CONFIG` 启动约定）
- [custom-cp-dsa](../../concepts/parallelism/custom_cp_dsa.md)（本页 `context_parallel_degree=4` 启用的 Ulysses Context Parallel 实现原理与约束）
- [npu-fused-op-converters](../../concepts/frameworks/npu_fused_op_converters.md)（本页 `model_converters` 注入的 `npu_rms_norm`/`npu_rope`/`npu_permute`/`npu_gmm` 算子转换机制）
- [qwen3-sft](qwen3_sft.md)（对照面：MindSpeed-LLM + Megatron mcore、Qwen3-1.7B dense、alpaca、单卡 A3 的另一条 SFT 路线——与本页 torchtitan MoE 路线区分）

<!-- cannbot:related:start -->
## 相关

- [DCP / HF Checkpoint（torchtitan-npu 断点恢复与权重导出）](../../concepts/techniques/checkpoint_dcp_hf.md)（`related`）：“HF safetensors 不含优化器/学习率调度器/训练步数，仅用于从预训练权重启动或训练后导出权重。”给出焦点端事实；“SFT 默认**直接从 HuggingFace 格式加载**预训练权重，无需 mcore 风格的格式互转”给出候选端事实。Checkpoint 卡界定 HF 权重只适合初始化或导出，Qwen3 SFT 指南给出直接加载 HF 预训练权重的实际入口，二者闭合格式选择与启动场景。
- [Qwen3-1.7B MindSpeed-LLM SFT 单卡 A3 alpaca 入门样例](qwen3_sft.md)（`related`）：焦点卡以“昇腾 SFT（监督微调）最小上手样例：用 ［mindspeed］(../../concepts/frameworks/mindspeed.md) 系的 **MindSpeed-LLM**（叠加 Megatron-LM `core_v0.12.1` 的 mcore 训练栈），对 **Qwen3-1.7B**（dense）在 **alpaca** 指令数据集上跑监督微调，**单卡即可**——硬件要求为「卡数：1张A3」。”给出单卡 dense 路线；目标卡明确“与 ［qwen3-sft］(qwen3_sft.md) 是昇腾 SFT 的两条独立技术路线”，并列出 torchtitan MoE 多卡路线，形成具体选型对照。
- [TorchTitan / torchtitan-npu（训练框架）](../../concepts/frameworks/torchtitan.md)（`related`）：“｜ `qwen3` ｜ `sft_qwen3_30ba3b_math` / `qwen3_06b_test` ｜ Qwen3 SFT/小模型 ｜”与“MODULE=torchtitan_npu.models.qwen3 CONFIG=sft_qwen3_30ba3b_math bash scripts/run_train.sh”是双方正文中的具体合同。框架卡登记 Qwen3 SFT 配置名，recipe 给出同一配置的可执行启动入口，互读可从能力清单直接进入训练任务。
<!-- cannbot:related:end -->
