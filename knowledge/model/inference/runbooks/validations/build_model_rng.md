---
{
  "type": "Runbook",
  "title": "独立部署随机权重推理复现性修复：建模收敛到单一 build_model 统一 RNG 消耗顺序",
  "description": "无 checkpoint 的固定种子随机权重部署中，Runner 在构造模型前未调用 torch.manual_seed，导致每次 infer.sh 权重不同、输出与基线记录不一致。把建模收敛为 models/modeling_hy_v4.py::build_model（manual_seed → 构造 → init_weights → cast_model_dtype，device 迁移最后做且不消耗 RNG），runner/golden/compare 三处统一调用后，连续两次 infer.sh 输出逐位一致，CPU↔NPU 一致性指标复现不变。",
  "tags": [
    "task.debugging",
    "task.testing",
    "topic.model_serving",
    "topic.attention"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-03T12:00:00Z",
  "platforms": [
    "950"
  ]
}
---

# 独立部署随机权重推理复现性修复：建模收敛到单一 build_model 统一 RNG 消耗顺序

## 适用场景

- 模型/框架：无本地 checkpoint 的固定种子随机初始化权重部署（本例 HYV4/tencent Hy4-preview，vendored `models/modeling_hy_v4.py`，torch 2.12.0+cpu + torch_npu 2.12.0）。
- 平台：Ascend950PR_9589 单卡，CANN 9.1.0；CPU 侧同一 venv 解释器。
- 目标：`bash infer.sh` 的 `output_text` / `generated_token_ids` 必须可复现，且与 `baseline_metadata.json` 记录一致（随机权重部署的基线可信前提）。
- 缺失信息说明：本结论基于 L=4（6.039B）随机权重、batch=1、8 token 生成；未在真实权重/多卡下验证（真实权重路径不走随机初始化，不受本 bug 影响）。

## 触发与观测

- 触发：主 agent 验证发现 `runner_hy_v4.py` 在构造模型并调用 `init_weights` 之前没有设置 `torch.manual_seed(self.seed)`，而 `tools/golden_cpu.py` 与 `tools/compare_golden_npu.py` 的 `build_model` 均先 seed。
- 客观测（事件 108）：修复前的 `bash infer.sh` 实跑输出 `...池事件updatedAtupdatedAtAllocateAllocateAllocateAllocate`，与 `baseline_metadata.json` 记录的 `output_text` 不一致——runner 建模路径缺少 torch.manual_seed 时，每次 bash infer.sh 生成不同随机权重，output_text 与 generated_token_ids 不可复现，且与已记录基线不一致。
- 根因：建模路径三处（runner / golden 工具 / compare 工具）各自维护建模代码，RNG 消耗顺序不统一，runner 侧漏 seed。

## 探针与操作

修复前 runner 建模段（无 seed，事件 64 oldString 原文）：

```python
        # Deterministic CPU init then move to NPU: identical weights to golden_cpu.py.
        self.model = HYV4ForCausalLM(self.config)
        init_weights(self.model, self.config)
        cast_model_dtype(self.model, torch.bfloat16)
        self.model = self.model.to(self.device)
        self.model.eval()
```

修复分两步：

1. 在 `models/modeling_hy_v4.py` 中新增单一来源 `build_model`（事件 55 原文）：

```python
def build_model(config, seed, dtype=torch.bfloat16, device=None):
    """Deterministic random-weight model from a fixed ``seed``.

    Single source of truth for the no-checkpoint path: the RNG is seeded, then
    the model is constructed on CPU, initialized and cast **in exactly this
    order**. Both the CPU golden reference and the NPU runner must call this
    helper so their weights stay bit-identical (any extra/different RNG
    consumption before construction would silently diverge). ``device`` is
    applied only after init/cast, which consumes no RNG.
    """
    torch.manual_seed(seed)
    model = HYV4ForCausalLM(config)
    init_weights(model, config)
    cast_model_dtype(model, dtype)
    if device is not None:
        model = model.to(device)
    model.eval()
    return model
```

2. runner 改为调用共享实现（事件 64 newString 原文），golden/compare 工具删除各自的 `build_model` 副本改为 import：

```python
        # Deterministic CPU init then move to NPU: identical weights to golden_cpu.py.
        # Reuse the shared build_model (seed -> construct -> init_weights -> cast)
        # so the RNG consumption order can never drift from the CPU golden path.
        self.model = build_model(self.config, self.seed, torch.bfloat16, device=self.device)
        self.model.eval()
```

验证命令：

```bash
bash infer.sh > logs/repro_runA.log 2>&1; echo "RUN_A_EXIT=$?"
bash infer.sh > logs/repro_runB.log 2>&1; echo "RUN_B_EXIT=$?"
grep -E "generated_token_ids|Request 0: outputs|prefill is" logs/repro_runA.log logs/repro_runB.log
```

## 机制与判别

- 机制：随机初始化权重的逐位一致性由 **RNG 消耗顺序** 决定——`torch.manual_seed(seed)` → 构造（每个 `nn.Parameter` 按注册顺序消耗随机数）→ `init_weights`（重采样）→ `cast_model_dtype`。任何一处顺序漂移或多一次 RNG 消耗都会静默产生不同权重。`.to(device)` 不消耗 RNG，因此放在最后是安全的。
- 判别：两次运行 `generated_token_ids` 逐位一致（事件 122/125）只能证明「同一二进制内确定性」；与 `npu_vs_cpu.json` 中 NPU greedy tokens 完全一致、且与重跑的 CPU↔NPU 一致性指标不变（事件 149），共同证明权重与 golden 逐位对齐。若只有逐位一致而无 golden 对齐，需怀疑两边都在用「另一个（相同的错误）种子」。
- 未验证推断：`warmup + 正式两次 model_generate` 不引入非确定性（warmup 不改权重、不落 RNG 到 cache）——本轨迹以两次 infer.sh 输出一致间接支持，未单独做 RNG 状态断言。

## 验证信号

- 事件 122：`RUN_A_EXIT=0 RUN_B_EXIT=0`（两次独立进程连续运行成功）。
- 事件 125：RUN A 与 RUN B 的 `generated_token_ids` 均为 `[101453, 58721, 70389, 70389, 76480, 76480, 76480, 76480]`、`output_text` 相同——将建模收敛为单一 build_model（torch.manual_seed(seed) → 构造 HYV4ForCausalLM → init_weights → cast_model_dtype，device 迁移放在 init/cast 之后且不消耗 RNG），runner、golden 工具与 compare 工具统一调用后，连续两次 bash infer.sh 的 generated_token_ids 与 output_text 逐位一致。
- 事件 149：重跑 `tools/compare_golden_npu.py`，修复后 CPU↔NPU 一致性复现不变：prefill logits cosine 0.999971、top-10 重叠 10/10，教师强制 decode 逐步 cosine ≥ 0.996914、argmax 6/7。
- 基线同步重生成：`agentic/baseline/baseline_metadata.json` 更新为新固定种子输出（prefill 202.40 ms / decode 51.96 ms，事件 141/145）。
- 证据等级：单机单卡（Ascend950PR_9589）、L=4 随机权重、seed=1234，两次独立 infer.sh 进程 + 一次 golden 对比重跑。

## 适用与失效边界

- 适用：所有「无 checkpoint、固定种子随机初始化」的部署/验证链路（CPU golden、NPU runner、compare 工具共享同一建模实现）。
- 失效/风险：
  - 一旦引入真实权重加载（`from_pretrained`），本机制不适用（不再消耗 RNG 建模）。
  - 任何在 `build_model` 之外新增的 RNG 消耗（如随机 mask、dropout 未关）都会破坏逐位一致性，需保持「建模单点」纪律。
  - 多进程/多卡各自建 RNG 流时需显式 per-rank seed，本轨迹未覆盖。
  - torch/模型结构变更会改变 RNG 消耗序列，golden 产物（`cpu_golden.pt`）需随之重建。
- 回退：保留修复前的三段式建模即可回到旧行为（不推荐，输出不可复现）。
