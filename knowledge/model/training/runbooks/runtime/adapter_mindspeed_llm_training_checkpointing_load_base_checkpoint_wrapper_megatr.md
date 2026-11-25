---
{
  "type": "Runbook",
  "title": "MindSpeed-LLM LoRA 完整状态断点续训：--lora-load 不跟随训练状态，需以训练 checkpoint 目录统一恢复",
  "description": "框架/模型链路：MindSpeed-LLM（DSV4-0731 BF16 LoRA SFT，legacy torch checkpoint、distributed/swap optimizer），Megatron-LM checkpointing。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:05Z",
  "updated_at": "2026-11-20T14:17:05Z",
  "platforms": []
}
---

# MindSpeed-LLM LoRA 完整状态断点续训：--lora-load 不跟随训练状态，需以训练 checkpoint 目录统一恢复

## 适用场景

- 框架/模型链路：MindSpeed-LLM（DSV4-0731 BF16 LoRA SFT，legacy torch checkpoint、distributed/swap optimizer），Megatron-LM checkpointing。
- 版本：MindSpeed-LLM master `b899791cd44fa72cf640c0e720ff9f81d7e3f3bb`，MindSpeed `65634689bed75ee9b6df666d526f7f16051a3db5`，Megatron `a845aa7e12b3a117e24c2352b9e3e60bad2e3a17`（source 0 seq 491）。
- 目标：长周期 LoRA 训练中断后恢复，要求框架状态与连续训练逐项等价（optimizer/RNG/进度），冻结底座不重存。

## 触发与观测

- 触发：训练难以一次跑完，需要断点续训；现有脚本固定携带 `--no-save-optim --no-save-rng --no-load-optim --no-load-rng --finetune`（source 0 seq 491）。
- 缺陷复现：隔离探针中，原代码以 `--load BASE --lora-load ADAPTER` 恢复时，仍去底座目录寻找 `distrib_optim.pt`（source 0 seq 451，tool_observed）。

## 探针与操作

before 缺陷链（source 0 seq 24、seq 491，source_read）：

- `mindspeed_llm/training/checkpointing.py:65 _load_base_checkpoint_wrapper` 在 `lora_load` 时把 adapter 权重并入底座（:96/:100），但 Megatron `load_checkpoint` 的局部 `load_dir` 仍为 BASE；
- 3rdparty/Megatron-LM distributed optimizer 分支重新从 BASE 读取 tracker，选择 BASE 下 `distrib_optim.pt`，并覆盖 `iteration`、`release`，进而影响 RNG 恢复条件；
- 另有两处独立缺口：`_load_from_state_dict_wrapper` 过滤 missing LoRA keys 不区分首次初始化与完整恢复（CPU 执行显示删除 `lora_A.weight` 后 `load_state_dict(strict=True)` 仍成功）；训练脚本固定 no-save/no-load。

after（source 0 seq 491、seq 617/689）：

- 完整恢复时以 ADAPTER（`RESUME_DIR`）作为整个训练状态加载目录，模型合并继续从 BASE 取冻结权重；iteration、release、optimizer、scheduler、RNG、consumed samples 必须来自同一训练 checkpoint，训练元数据不从底座兜底；
- 完整续训禁止静默忽略缺失 LoRA 权重/优化器/RNG/分片，缺失即明确报错；
- 脚本拆分首次训练（finetune/no-load 可用）与续训（移除 `--finetune`/`--no-load-*`，保存 optimizer/RNG，`--use-checkpoint-opt_param-scheduler` 恢复 LR 进度）两条分支；保留 `--lora-ckpt-filter`（只过滤模型权重，不删 optimizer/scheduler/RNG 顶层状态）。

验收探针（source 0 seq 245/278/402）：隔离脚本以真实 PEFT adapter、DDP、distributed swap Adam 构建"连续更新"与"step3 保存→新进程恢复→step6"两进程对照，逐项比较 LoRA 权重、FP32 主权重、Adam 状态、学习率、随机状态、样本序列。

## 机制与判别

- 等价性判别：不能只看 loss 是否接得上；必须逐项比较可训练参数三份状态（FP32 主权重 + Adam 一阶/二阶矩）、调度器、RNG 与后续样本顺序（source 0 seq 228、seq 451）。
- 新增存储估算：仅可训练 LoRA 参数新增约 12 字节/参数（FP32 主权重 4 + exp_avg 4 + exp_avg_sq 4）；r64 配置完整续训 checkpoint 约 141 GiB（理论估算，非实测，source 0 seq 564）。
- 未验证边界：合成梯度/小模型探针不等于完整 DSV4 训练流程、32 rank 或 64K 验收（source 0 seq 451、seq 491）；算子非确定性按用户要求排除在等价性之外。

## 验证信号

- 两卡 NPU 对照：step3 保存、新进程恢复至 step6，LoRA 权重、FP32 主权重、Adam 状态、学习率、随机状态、样本序列逐项完全相等；并复现原代码去 BASE 找 `distrib_optim.pt` 的错误（source 0 seq 451，device_functional）。
- 四卡 NPU PP2/CP2/EP2 对照：恢复状态及后续三步更新完全一致（source 0 seq 490，device_functional）。
- 生产修复落地后：四卡对照再次通过（step3→step6 各状态逐项相同），17 项回归测试通过；独立保存目录（两个 PP stage 各自分片+进度文件）模拟亦通过（source 0 seq 744、seq 816，device_functional）。
- CPU 级：missing-key wrapper 行为（strict=True 仍接受缺失 LoRA 权重）单独复现（source 0 seq 491，cpu_reference）。

## 适用与失效边界

- 适用：MindSpeed-LLM 该版本 lineage 的 `--load BASE --lora-load ADAPTER` 恢复路径；其它实现需重新核对 load_dir 路由。
- 完整续训不支持同时更改 LR 计划/并行拓扑/LoRA target 等条件；底座冻结权重始终复用原底座，不随续训重存。
- 探针使用小模型与构造梯度（后期补真实前后向），等价性结论限于框架状态恢复层；端到端大模型验收未在本轨迹内完成。

## 附：断言存档

- MindSpeed-LLM(b899791c) 以 --load BASE --lora-load ADAPTER 恢复时，load_checkpoint 局部 load_dir 仍为 BASE，distributed optimizer 分支从 BASE 读 tracker 并选择 BASE 的 distrib_optim.pt，且覆盖 iteration/release 影响 RNG 恢复；隔离探针在两卡 NPU 复现该路径错误

```text
1. `--load BASE --lora-load ADAPTER` 时，`mindspeed_llm/training/checkpointing.py::_load_base_checkpoint_wrapper` 把 adapter 权重与训练元数据并入底座，但 Megatron `load_checkpoint` 的局部 `load_dir` 仍为 BASE。
   - `3rdparty/Megatron-LM/megatron/training/checkpointing.py` 的 distributed optimizer 分支重新从 BASE 读取 tracker，选择 BASE 下的 `distrib_optim.pt`。
   - 该分支还覆盖 `iteration`、`release`；如果 BASE 为 release，后续 RNG 恢复条件也会受到影响。
```

```text
mindspeed_llm/training/checkpointing.py:65:def _load_base_checkpoint_wrapper(fn):
mindspeed_llm/training/checkpointing.py:96:            if not args_.lora_load or getattr(args_, 'is_load_refer', False):
mindspeed_llm/training/checkpointing.py:100:            state_dict_lora, checkpoint_name_lora, release_lora, ckpt_type_lora = fn(args_.lora_load, args_, rank0)
```
