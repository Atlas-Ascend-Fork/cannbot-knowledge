---
{
  "type": "Runbook",
  "title": "verl GRPO 0% 处 AssertionError: Conflicting values for meta_info key 'timing'——DataProto.concat 严格判等与 16 路并行 rollout 汇聚冲突",
  "description": "verl GRPO 训练 Qwen3-32B（单 A3 节点 16 NPU，Megatron TP8+PP2+CP1，vLLM rollout）在 0/55 首个 rollout 汇聚处抛 AssertionError: Conflicting values for meta_info key 'timing'（verl/protocol.py:959 的 assert merged_meta_info[k] == v），经 RayTaskError 上抛 driver 终止训练。根因为 DataProto.concat 对 meta_info 逐键严格判等，而 16 路 worker 的 per-rank 生成计时 timing 必然跨 rank 不一致；属框架层逻辑缺陷，日志全文无设备错误码/HCCL 超时/OOM/core 信号。",
  "tags": [
    "task.debugging",
    "topic.reinforcement_learning"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "a3"
  ]
}
---
# verl GRPO 0% 处 AssertionError: Conflicting values for meta_info key 'timing'——DataProto.concat 严格判等与 16 路并行 rollout 汇聚冲突


## 适用场景

verl GRPO 训练 Qwen3-32B（单 A3 节点 16 NPU，Megatron TP8+PP2+CP1，vLLM rollout）在 0/55 首个 rollout 汇聚处抛 AssertionError: Conflicting values for meta_info key 'timing'（verl/protocol.py:959 的 assert merged_meta_info[k] == v），经 RayTaskError 上抛 driver 终止训练。根因为 DataProto.concat 对 meta_info 逐键严格判等，而 16 路 worker 的 per-rank 生成计时 timing 必然跨 rank 不一致；属框架层逻辑缺陷，日志全文无设备错误码/HCCL 超时/OOM/core 信号（修复方向与修复建议块未进入账本证据，本卡不作断言）。

## 触发与观测

> 触发：verl GRPO 训练 Qwen3-32B（单 A3 节点 16 NPU，8TP+2PP+1CP，vLLM rollout，use_kl_loss=True）在训练进度 0%（0/55，已耗时 42:42）的首个 generate_sequences 汇聚点抛 AssertionError: Conflicting values for meta_info key 'timing'（${TRAINING_RECIPE_ROOT}/llm_rl/qwen3/verl/protocol.py:959 的 DataProto.concat），经 ray.exceptions.RayTaskError 上抛 driver，训练任务终止。

**机制片段：M1**：

```
65:   File "${TRAINING_RECIPE_ROOT}/llm_rl/qwen3/verl/protocol.py", line 959, in concat
66:     assert merged_meta_info[k] == v, f"Conflicting values for meta_info key '{k}'"
67:            ^^^^^^^^^^^^^^^^^^^^^^^^
68: AssertionError: Conflicting values for meta_info key 'timing'
```

## 探针与操作

### 复现路径约定

以下路径已脱敏。历史命令中的变量占位符需由复现者按实际环境替换；Python/JSON 字符串内的占位符不会自动展开。

- `${TRAINING_RECIPE_ROOT}`：该次实验的训练 Recipes 检出根目录。


（探针见“触发与观测”中的日志读取与下面的验证命令；本候选无独立探针环节。）

## 机制与判别

> 根因（confirmed，file:line 级）：verl 框架层缺陷——DataProto.concat（protocol.py:959）对 meta_info 逐键使用严格相等断言（assert merged_meta_info[k] == v），generate_sequences 由 16 路 worker 并行执行，per-rank 生成计时 meta_info['timing'] 跨 rank 必然存在差异，首个 rollout 步（0/55）汇聚时断言失败抛出 AssertionError，经 Ray 上抛 driver，训练任务终止；属应用框架逻辑错误引发的进程中断，与 NPU/CANN 设备层无直接关联。'timing' 差异的具体成因保留为 hypothesis（最可能是 vLLM 异步生成与变长提示的负载不均，但缺各 rank timing 数值与 device 日志，无法排除单 rank 设备侧卡慢）。

> 判别：应用日志全文无任何设备错误码、HCCL 超时/重试、OOM 或 core 信号，缩界到框架层而非设备层；Ray 重复调度/输出错配假设 excluded（traceback 为单次 generate_sequences 的 collect 汇聚链路、帧连续无重复任务帧，报错 key 明确为 'timing' 属 meta_info 合并语义而非张量/数据错配）；其他 meta_info 键冲突假设 excluded（异常消息原文明确指认 key 'timing'）；设备侧单 rank 卡慢假设 unresolved（缺 plog/device_log/npu_smi，但即使成立直接失败点仍是框架层断言）。

**机制片段：M2**：

```
"description": "verl 框架层缺陷：DataProto.concat（${TRAINING_RECIPE_ROOT}/llm_rl/qwen3/verl/protocol.py:959）对 meta_info 逐键使用严格相等断言（assert merged_meta_info[k] == v）。generate_sequences 由 16 路 worker 并行执行，per-rank 生成计时 meta_info['timing'] 跨 rank 必然存在差异，首个 rollout 步（0/55）汇聚时断言失败抛出 AssertionError，经 Ray 上抛 driver，训练任务终止。属应用框架逻辑错误引发的进程中断，与 NPU/CANN 设备层无直接关联；'timing' 差异的具体成因保留为 hypothesis。",
```

## 验证信号

本卡验证信号并入『触发与观测』『机制与判别』：来源结论 与登记机制片段：M1/M2（traceback 断言原文与根因分析报告）。

## 适用与失效边界

适用：verl 多 worker rollout 汇聚阶段的 AssertionError 定界（meta_info 键冲突语义）。失效边界：'timing' 跨 rank 差异的具体成因（负载不均 vs 单 rank 设备卡慢）因缺 plog/device_log/npu_smi 与各 rank timing 数值保留 hypothesis；无 verl/vLLM/CANN 版本号，无法核对上游修复 commit；未复跑验证修复（reproducible=false、fix_verified=false）；本候选不覆盖设备侧健康性证明。
