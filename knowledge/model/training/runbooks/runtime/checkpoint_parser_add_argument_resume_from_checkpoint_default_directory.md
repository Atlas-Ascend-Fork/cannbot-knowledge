---
{
  "type": "Runbook",
  "title": "换数据继续预训练时 resume 恢复旧 iteration 撞上新算 LR 调度：走 weights-only init 而非 resume_from_checkpoint",
  "description": "自研 mini_deepseekv4_titan 1B 预训练仓（DDP/DeepSpeed ZeRO-2、safetensors checkpoint、无状态 get_lr 余弦调度）。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:04Z",
  "updated_at": "2026-11-20T14:17:04Z",
  "platforms": []
}
---

# 换数据继续预训练时 resume 恢复旧 iteration 撞上新算 LR 调度：走 weights-only init 而非 resume_from_checkpoint

## 适用场景

自研 mini_deepseekv4_titan 1B 预训练仓（DDP/DeepSpeed ZeRO-2、safetensors checkpoint、无状态 get_lr 余弦调度）。已用一份 10B 数据完成预训练，现换成全新、更大的 100B 数据包（通识/code/math 更多样）继续预训练（continued pretraining），需要决定用 `--resume_from_checkpoint` 还是 weights-only init 加载旧权重。凡「LR 调度按当前数据集长度现算 + checkpoint 恢复 iteration 计数」的自训框架都适用。

## 触发与观测

用户提问（source 0 seq 53）：10B 数据已训完、100B 新数据就绪，走 init 还是 resume。本轨迹无运行期故障——这是切换前的策略判别；若强行 resume，预测的故障模式见下。

## 探针与操作

只读源码三处（无设备执行）：

1. `pretrain.py`（source 0 seq 59，节选 resume 相关分支）：

```python
        if args.resume_from_checkpoint and os.path.exists(args.resume_from_checkpoint):
            if use_deepspeed:
                ds_ckpt_files = [f for f in os.listdir(args.resume_from_checkpoint) if f.endswith('.pt') and ('zero_pp_rank' in f or 'mp_rank' in f)]
                if ds_ckpt_files:
                    load_path, client_state = model.load_checkpoint(args.resume_from_checkpoint, load_optimizer_states=True, load_lr_scheduler_states=False)
                    if client_state:
                        start_epoch = client_state.get("epoch", 0)
                        start_step = client_state.get("step", 0)
                        start_iteration = client_state.get("iteration", 0)
```

（DDP 路径走 `load_checkpoint(...)`，见 artifact 之外 seq 59/73；DeepSpeed 目录只有 safetensors 时在 DS init 前 `load_state_dict` 当初始化、`start_iteration` 保持 0——框架已有 init 语义，但 DDP 路径没有。）

2. `get_lr`（source 0 seq 71 逐字）：

```python
def get_lr(it, max_lr, min_lr, warmup_iters, lr_decay_iters):
    """
    根据迭代次数返回学习率, it为总迭代次数
    """
    # 1. warmup 阶段
    if it < warmup_iters:
        return max_lr * it / warmup_iters  # 线性增加到最大学习率
    # 2. 衰减结束，使用最小学习率
    if it > lr_decay_iters:
        return min_lr  # 衰减结束，使用最小学习率
    # 3. 余弦衰减阶段
    decay_ratio = (it - warmup_iters) / (
        lr_decay_iters - warmup_iters
    )  # 衰减阶段中，当前迭代相对于剩余迭代的比例
    assert 0 <= decay_ratio <= 1
    coeff = 0.5 * (
        1.0 + math.cos(math.pi * decay_ratio)
    )  # coeff 是一个从 0 到 1 之间变化的系数，控制学习率的衰减

    return min_lr + coeff * (max_lr - min_lr)
```

3. `load_checkpoint`（source 0 seq 73 逐字节选）：

```python
    # 加载优化器状态
    optimizer_state_path = os.path.join(checkpoint_path, "optimizer.pt")
    if os.path.exists(optimizer_state_path):
        optimizer.load_state_dict(torch.load(optimizer_state_path, map_location=device))

    # 加载训练状态
    training_state_path = os.path.join(checkpoint_path, "training_state.json")
    if os.path.exists(training_state_path):
        with open(training_state_path, "r", encoding="utf-8") as f:
            training_state = json.load(f)
```

## 机制与判别

三处错配（source 0 seq 74，基于 seq 59/71/73 源码读取的归纳）：

1. **LR 调度错配（最致命）**：`total_iters` 按新数据集长度重算（pretrain.py:135-136），warmup/decay 区间随之变化；resume 恢复的 `start_iteration` 是 10B 轮的旧 step 数（pretrain.py:333）。训练循环 `it = epoch * iter_per_epoch + step + 1`（pretrain.py:418）把旧 iteration 喂给按新区间定义的 `get_lr`——`get_lr` 无状态、只看 `it` 与新区间，落点完全错配：轻则直接跳过 warmup 以大 LR 起步，重则旧 `it > 新 lr_decay_iters` 之外再触发 `assert 0 <= decay_ratio <= 1`（utils.py:44）崩溃。
2. **skip step 白跑**：pretrain.py:414 对 `start_step` 之前的 step `continue`，本意接续旧数据读取；数据集已换，跳过只是丢弃新数据前段。
3. **输出目录污染**：pretrain.py:355-360 从 checkpoint 父目录推断输出路径，100B 新轮会写进旧 `pretrained_.../` 目录。

判别：DeepSpeed 分支目录内仅有 safetensors 时天然走「权重当初始化、iteration 归零」（seq 59 源码），说明 weights-only init 是框架已验证语义；问题只在 DDP 路径缺入口。

处置两案（seq 74）：
- **方案 A（已采纳，改代码）**：新增 `--init_from_weights`：只 `load_state_dict(strict=False)`，不碰 optimizer/iteration/输出目录，与 resume 互斥、resume 优先，init 场景沿用旧权重目录 config。argparse 与互斥/config 编辑已落盘（source 0 seq 80/90，artifact 2）。
- **方案 B（不改代码绕过）**：把 10B `model.safetensors` 复制为假 checkpoint 目录并**删掉 `optimizer.pt` 与 `training_state.json`**——`load_checkpoint` 只剩权重可载，`training_state` 为 None → `start_iteration` 保持 0、LR 从头调度；代价是输出目录推断仍挂在假目录父级。

```python
    # Checkpoint 设置
    parser.add_argument("--resume_from_checkpoint", type=str, default=None, help="Path to checkpoint directory to resume training from (恢复 optimizer/iteration/LR 调度/输出目录, 用于中断续训)")
    parser.add_argument("--init_from_weights", type=str, default=None, help="Path to a weights dir (含 *.safetensors) 用作初始化: 只加载模型权重 (strict=False), 不恢复 optimizer/iteration/LR 调度, 输出目录当作全新训练. 用于换数据继续预训练 (continued pretraining). 与 --resume_from_checkpoint 互斥, resume 优先")
```

## 验证信号

- user_reported（触发）：source 0 seq 53（10B→100B 换数据、init/resume 二选一）。
- tool_observed（源码级）：seq 71 get_lr 无状态调度与 assert；seq 73 load_checkpoint 恢复 optimizer/training_state；seq 59 resume 分支与 DS init 语义。
- agent_narrative：seq 74 三处错配归因与方案结论；「continued pretraining 宜用略低峰值 LR + 重新 warmup，避免旧权重被大 LR 冲垮」为建议，未经实验。
- 实现状态：方案 A 的权重加载插入（模型创建后、DDP/DS wrap 前）被用户中断（seq 95 拒绝），**未闭合、未运行**；本卡为诊断形态，不含成功修复声明。

## 适用与失效边界

- 已证边界（源码级）：该仓 resume 语义 = 恢复 optimizer + iteration + 旧目录推断；DS 路径 safetensors-only 目录等价于 init。
- 适用前提：LR 调度由「当前数据集长度现算」且 checkpoint 携带旧 iteration 的自训框架；若调度已持久化进 checkpoint（load_lr_scheduler_states=True）则错配前提不成立。
- 未验证：assert 崩溃分支为源码推断，未实际触发；方案 B 假目录绕过未实测；训练效果（100B 新轮 loss 曲线）无观测。
- 伴随事实（同轨迹，非本卡主题）：ShardedPreTrainDataset 的 `bisect.bisect_right` 缺 `import bisect` 会在每次 `__getitem__` 抛 NameError，已补导入（seq 28-29）；validate() 做成分块线性扫描的显式方法（min/max/越界 token 统计），仅语法检查通过（seq 48-49）。

## 附：断言存档

- mini_deepseekv4_titan 1B 预训练仓中 resume_from_checkpoint 会同时恢复 optimizer 状态与旧 iteration 并沿用 checkpoint 父目录推断输出路径；换新数据集（10B→100B）继续预训练时 total_iters/warmup/decay 按新数据重算而 start_iteration 是旧值，无状态 get_lr(it) 查新调度发生错配，轻则跳过 warmup 重则 assert 0<=decay_ratio<=1 直接崩溃；应改用 weights-only init（--init_from_weights 或删掉 optimizer.pt/training_state.json 的假 checkpoint 目录）
