---
{
  "type": "Runbook",
  "title": "vLLM-Ascend msprof 三段式 profiling 的产物落点与在线解析卡滞处置",
  "description": "vLLM-Ascend msprof 三段式 profiling 的产物落点（<输出根>/trace/stage{0,1,2}_rank0/<hash>_ascend_pt/ASCEND_PROFILER_OUTPUT/）与在线解析卡滞处置（kill 后对 stage 目录走 torch_npu.profiler.profiler.analyse() 离线重解析）。",
  "tags": [
    "task.testing",
    "topic.performance.analysis"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# vLLM-Ascend msprof 三段式 profiling 的产物落点与在线解析卡滞处置


## 适用场景
适用场景：对 vllm serve 起的多阶段/多 rank 服务（如 omni 模型 MiniCPM-o）做 CANN 级 profiling（msprof，官方 profiling_msprof 文档方法 b）。

## 触发与观测
触发与观测：stage2 的在线 analyse 预计超 30 分钟并伴随 "Failed to get acl to npu flow events" ERROR。

## 探针与操作

### 复现路径约定

以下路径已脱敏。历史命令中的变量占位符需由复现者按实际环境替换；Python/JSON 字符串内的占位符不会自动展开。

- `${PROFILE_ROOT}`：本次 profiling 输出根目录。
- `${SCRATCH_DIR}`：由复现者创建的本次实验临时目录。

探针与操作：轮询 bench/serve 日志（"Profiler stopped successfully" 计数、最后几行）；列出 trace 目录确认哪些 stage 已完整解析、哪些只有原始 dump。

## 机制与判别
机制与判别：stage0/1 已完整解析（trace_view.json 660MB + 五个 CSV），stage2 原始数据已落盘但在线解析慢且报 acl-to-npu flow events 错误——kill 在线解析后可用 torch_npu.profiler.profiler.analyse() 离线重解析。


机制片段：


```
Profile 产物在 `${PROFILE_ROOT}/`，按 stage 分目录：

```
${PROFILE_ROOT}/
├── stage0_rank0/<hash>_ascend_pt/ASCEND_PROFILER_OUTPUT/
│   ├── trace_view.json   (660 MB, Perfetto 可打开)
│   ├── op_statistic.csv
│   ├── operator_details.csv
│   ├── kernel_details.csv
│   ├── api_statistic.csv
│   └── step_trace_time.csv
├── stage1_rank0/<hash>_ascend_pt/ASCEND_PROFILER_OUTPUT/  (同上结构)
└── stage2_rank0/<hash>_ascend_pt/   (原始数据已落盘，在线解析还在跑/可中断)
```

- **stage0、stage1**：已完整解析，`trace_view.json` + CSV 齐全，可直接用 Perfetto 或 MindStudio 打开。
- **stage2**：`.db`/原始 dump 已落盘，但在线 `analyse` 进程还在跑（日志预计 >30min，有 "Failed to get acl to npu flow events" 报错但仍会产出）。如果不想等，可以直接 kill stage2 worker 或整个服务，然后对 stage2 目录走文档 §3.4 的离线 `analyse()`：
  ```bash
  python -c "from torch_npu.profiler.profiler import analyse; analyse('${PROFILE_ROOT}/stage2_rank0')"
  ```
- bench 的性能指标（TTFT/TPOT/ITL/AUDIO_RTF 等）在 `${SCRATCH_DIR}/vllm_bench.log` 里，已经打印完整（P99 AUDIO_RTF 1.02）。
```

## 验证信号
验证信号：验证层级为设备级产物观测（device_functional 的工件核验）：产物目录结构、文件清单（trace_view.json 660MB、op_statistic.csv 等）与在线解析日志均为实测 tool_result。

## 适用与失效边界
适用与失效边界：适用于 torch_npu/CANN msprof 系 profiling（目录结构 ASCEND_PROFILER_OUTPUT 与 CSV 清单是 msprof 通用产物形态）；离线 analyse() 的路径参数是环境特定的。局限："在线解析超 30 分钟"的预估与实测 4:50 的关系说明该提示偏保守。

## 结论与证据边界

- ：多阶段 vllm serve 的 msprof profiling 产物落点：<输出根>/trace/stage{0,1,2}_rank0/<hash>_ascend_pt/ASCEND_PROFILER_OUTPUT/，其中 stage0/stage1 已完整解析（trace_view.json 660MB 可用 Perfetto/MindStudio 打开，另有 op_statistic.csv、operator_details.csv、kernel_details.csv、api_statistic.csv、step_trace_time.csv），stage2 的 .db/原始 dump 已落盘但在线 analyse 还在跑。

- ：在线解析的卡滞判别与处置：stage2 解析日志给出 "The parsing time is expected to exceed 30 minutes"（实测 CANN profiling data parsed in 0:04:50）且伴随 "Failed to get acl to npu flow events" ERROR（会继续产出）——不想等可直接 kill stage2 worker 或整个服务，再对该目录走离线重解析：python -c "from torch_npu.profiler.profiler import analyse; analyse('<stage_dir>')"。
