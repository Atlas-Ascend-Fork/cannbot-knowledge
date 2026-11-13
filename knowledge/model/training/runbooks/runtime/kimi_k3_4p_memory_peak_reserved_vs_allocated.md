---
{
  "type": "Runbook",
  "title": "kimi_k3 4P 训练显存峰值异常的定界（口径 + allocator 缓存/碎片结构）",
  "description": "kimi_k3_12layers_112experts 模型 4P 真机训练的显存峰值口径与 allocator 行为定界，用于真实训练的显存预算。",
  "tags": [
    "task.debugging",
    "topic.memory"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# kimi_k3 4P 训练显存峰值异常的定界（口径 + allocator 缓存/碎片结构）

kimi_k3 4P 真机训练的显存峰值远超理论预期，需要区分真实存活峰值与 allocator reserved 口径。本卡记录 memprobe/allocprobe 探针与碎片结构判别。

## 适用场景

- kimi_k3_4p.sh（kimi_k3_12layers_112experts，EP4/FSDP4，单机 4 卡，fp32 master，grad-only offload）训练中 `memory:` 打印值或 npu-smi HBM 峰值远超理论预期。
- 需要区分"真实存活显存峰值"与"allocator reserved 口径"，并定位可回收缓存/碎片来源的场景。

## 触发与观测

- 触发：执行 kimi_k3_4p.sh 时怀疑 FSDP 显存分配管理不合理；用户确认"峰值比理论预期高"。
- 实测表：

> 实测（rank 0，`kimi_k3_4p.sh`，探针见 `outputs/kimi_k3_4p_memprobe_train.py`）：fp32 分片参数（step1 起始 alloc）28.07 (=30.14 GB)；稳态 step 起始 alloc ~35.9；forward/backward 存活峰值 ~49.5；稳态 reserved（=`memory:` 打印值）~69.0；`empty_cache()` 后 reserved 35.94；设备实际 HBM 峰值（npu-smi）~77–79。

> 三条关键证据：1. torchtitan 的 `memory: 69.00GiB` 取的是 `max_reserved_gib`，不是存活显存（`metrics.py:495-527`）。2. 探针里 `torch.npu.empty_cache()` 把 reserved 从 68.90 → 35.94 GiB，说明约 33 GiB 属于该次可释放的 allocator 保留空间；不能只凭此区分缓存与碎片。3. `num_device_alloc=232, num_device_free=1`；且 step 1 仅一次 fwd/bwd 就把 reserved 从 33.27 撑到 60.56 GiB（此时优化器状态还没初始化），提示继续分析 fwd/bwd 的临时分配与复用；尚未单独量化变长分配的因果贡献。


## 探针与操作

### 复现路径约定

以下路径已脱敏。历史命令中的变量占位符需由复现者按实际环境替换；Python/JSON 字符串内的占位符不会自动展开。

- `${SCRATCH_DIR}`：由复现者创建的本次实验临时目录。


- memprobe 训练探针（outputs/kimi_k3_4p_memprobe_train.py）：阶段级采样 `torch.npu.max_memory_allocated()` / allocated / reserved。
- allocator 段级探针（allocprobe_train.py，原文核心函数）：

```python
def _dump(tag):
    import torch
    import torch_npu  # noqa: F401

    snap = torch.npu.memory._snapshot()
    segs = snap.get("segments", [])
    reserved = sum(s.get("total_size", 0) for s in segs)
    active = 0
    inactive = 0
    for s in segs:
        for b in s.get("blocks", []):
            if b.get("state") == "active_allocated":
                active += b.get("size", 0)
            else:
                inactive += b.get("size", 0)
    print(
        f"[ALLOCPROBE][rank{_rank}] {tag} reserved={reserved / _GIB:.2f}G "
        f"active={active / _GIB:.2f}G inactive={inactive / _GIB:.2f}G segments={len(segs)}",
        flush=True,
    )
```

- 运行方式：`KIMI_K3_ALLOC_PROBE=1 TRAIN_FILE=allocprobe_train PYTHONPATH=${SCRATCH_DIR}/opencode:$PYTHONPATH bash examples/kimi_k3/kimi_k3_4p.sh`；对照 `KIMI_K3_ALLOC_CONF_OVERRIDE` 覆盖 `PYTORCH_NPU_ALLOC_CONF`。

## 机制与判别

- 碎片结构：

> 碎片不是"很多小块"，而是少数超大块/段（`torch.npu.memory._snapshot()`，step 5 起始）：reserved 70.0 GiB / active 34.4 GiB / inactive 35.9 GiB，共 16 段；57.23 GiB 主段为 expandable=True，但 1.25 GiB 段和若干约 0.02 GiB 段标为 False，不能称全部 expandable；主 expandable 段：total 57.23 GiB，其中 active 只有 34.35 GiB → 单段闲置 22.9 GiB；另有整段闲置：7.01 / 3.46 / 1.25 / 0.92 GiB ≈ 12.9 GiB；top alloc 均为定长 4480 MiB（对应每层 FSDP all-gather / reduce-scatter scratch）。


## 验证信号

- allocprobe 实测输出：`step_start reserved=70.25G active=34.40G inactive=35.85G segments=16`；`seg total= 57.23G active= 34.35G blocks= 166 expandable=True`；整段闲置 `7.01G/3.46G/1.25G/0.92G`（active=0.00G）。
- 关闭 swap 的对照实验失败：`RuntimeError: Expected all tensors to be on the same device, but got grads is on cpu, different from other tensors on npu`（wrapper_NPU___fused_adamw）——说明不能简单通过关闭 swap 验证。
- `run_train.sh` 侧配置确认：`PYTORCH_NPU_ALLOC_CONF="expandable_segments:True"`、`STREAMS_PER_DEVICE=32`、`MULTI_STREAM_MEMORY_RESERVE=1`。
- validation_scope：device_functional（4P 真机训练探针与对照实验，未跑性能基线）。

## 适用与失效边界

- 适用：torch_npu allocator + NovaSwap 换存组合下的显存峰值/reserved 异常分析；判断 `memory:` 打印值口径。
- 判别规则：`empty_cache()` 后 reserved 大幅回落 ⇒ 缓存/碎片而非存活峰值。
