---
{
  "type": "Runbook",
  "title": "DeepEP offload 反向重计算中 dispatch 反量化前大空泡的定位",
  "description": "kimi k3 训练（k3-shared-w13 代码路径）开启 DeepEP offload + FP8 后反向重计算时间线空泡的离线 profiling 定位，服务 MoE 训练性能优化。",
  "tags": [
    "task.debugging",
    "topic.memory"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T12:00:00Z",
  "updated_at": "2026-11-13T02:13:38Z",
  "platforms": []
}
---
# DeepEP offload 反向重计算中 dispatch 反量化前大空泡的定位

kimi k3 训练开启 DeepEP offload + FP8 后，反向重计算 dispatch 侧反量化算子前出现毫秒级空泡而 combine 侧没有。本卡记录 H2D 恢复等待归因链与缓解方向。

## 适用场景

- kimi k3 训练开启 DeepEP offload + FP8（MX 量化）后，profiling 时间线显示反向重计算 dispatch 侧反量化算子（AntiMxQuant）前出现毫秒级空泡，而 combine 侧没有。
- 需要判断"反量化算子慢"还是"等待 offload 恢复慢"的场景。
- 环境：Ascend profiler（ASCEND_PROFILER_OUTPUT，sqlite db + trace_view.json），k3-shared-w13 代码路径。

## 触发与观测

- 触发：分析 profiling_deepep_offload_w13，"为什么 deepep offload 的 dispatch 的反向重计算的反量化算子前面有一个大空泡。但是 combine 的反向重计算的反量化算子前面并没有空泡？"
- 核心观测：

> dispatch 反量化前的大空泡不是 `AntiMxQuant` 本身慢，而是主计算 stream 在等 saved DeepEP dispatch output 的 CPU→NPU H2D 恢复完成。`unpack()` 的顺序是：按需 `_fetch()` → `current_stream.wait_event(fetch_event)` → `AntiMxQuant`；当前配置又显式关闭了一层 ahead prefetch：`prefetch_boundary_to_device=False`。

> dispatch `hidden_states_RD`（`131096×3584` + `131096×56×2`，92 次）：Anti 前空泡 avg 8.329ms，median 10.661ms，P90 12.591ms，Anti 平均耗时 534.6us；combine `combined_TD`（`8192×3584` + `8192×56×2`，92 次）：Anti 前空泡 avg 0.130us，max 0.250us，Anti 45.1us。


## 探针与操作

- sqlite TASK 表查询（连接级 startNs/endNs/streamId）确认 DeepEP dispatch/combine 的 host 侧提交。
- trace_view.json窗口分析：先设置环境变量`TRACE_JSON`为本次采集的trace_view.json完整路径；按采集记录调整lo/hi、pid/tid。以下为路径变量化后的历史探针，不保留私有实验根：

```
@'
import json
import os
p=os.environ["TRACE_JSON"]
with open(p,encoding='utf-8') as f: data=json.load(f)
lo=1793292009330700; hi=1793292009331500
for e in data:
 try: ts=float(e.get('ts'))
 except: continue
 if lo<=ts<=hi and e.get('pid')==556 and e.get('tid')==556 and e.get('cat')=='cpu_op':
  a=e.get('args') or {}
  print(f"{ts:.3f} dur={e.get('dur',0)} name={e.get('name')} seq={a.get('Sequence number')} dims={a.get('Input Dims','')!r} types={a.get('Input type','')!r}")
'@ | python -
```

- 该窗口可见：`acl_memcpy_host_to_device`（8192,3584 fp8 + 8192,56,2 scale）→ `record_event` → `wait_event` → `aclnnAntiMxQuant` → 后续 matmul。

## 机制与判别

- 判别链：AntiMxQuant 自身仅 534.6us，排除"算子慢"；空泡 = wait_event 等待 H2D 恢复。
- 代码锚点：activation_checkpoint.py:779（unpack 顺序）、config_registry.py:176（prefetch_boundary_to_device=False）、token_dispatcher.py:484/522（dispatch 返回 hidden_states_RD、combine 返回 combined_TD）。

## 验证信号

- 分层统计（92 层）与单层抽样数字见"触发与观测"；来源窗口包含H2D、EVENT::record/wait、aclnnAntiMxQuant及后续反向事件与Input Dims；复现时使用上方探针核对本次采集，原始profiling资产未随本文发布。
- validation_scope：source_read + static_check（profiling 数据离线分析；无设备回归）。

## 适用与失效边界

- 适用：DeepEP offload + FP8 的反向重计算空泡归因；判定"dispatch 侧大 / combine 侧无"的不对称来自 saved tensor 体量与按需 H2D 时机。

- 失效边界：若 saved tensor 已被其他机制提前恢复（如 prefetch 已开启），空泡成因需另行排查；本结论基于该会话的 profiling 快照与代码静态对照，未做修复后复测。
