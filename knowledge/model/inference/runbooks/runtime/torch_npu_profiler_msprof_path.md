---
{
  "type": "Runbook",
  "title": "torch_npu profiler 设备侧事件缺失：msprof 不在 PATH 的定位与修复",
  "description": "torch_npu 2.12.0.post2 + CANN 9.1.0 用 tensorboard_trace_handler 剖析时，若 msprof 不在 PATH，CANN 数据导出子进程失败但主流程不中断，剖析结果静默只剩 host 侧事件（trace 仅 cpu_op/dequeue/enqueue，kernel_details.csv 不生成），仅有一条导出失败日志。修复 = 把 /usr/local/Ascend/cann-9.1.0/tools/profiler/bin 加入 PATH 重跑；解析还需绑定本次run，不能回退到历史成功目录。修复后 kernel_details.csv/operator_details.csv/step_trace_time.csv 完整生成，设备侧 Top 算子可解析。",
  "tags": [
    "task.debugging",
    "topic.graph_execution",
    "topic.model_serving"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "950"
  ]
}
---
# torch_npu profiler 设备侧事件缺失：msprof 不在 PATH 的定位与修复

## 适用场景

- torch_npu 2.12.0.post2 + CANN 9.1.0（Ascend950PR_9589，aclnn-only）用 `torch_npu.profiler` + `tensorboard_trace_handler` 做算子级剖析，发现“剖析成功但设备侧全空”或 CANN 导出报错时。
- 症状组合：REPORT 只有 host 侧 aten:: 算子、trace 只有 cpu_op/enqueue/dequeue、kernel_details.csv 不生成。

路径补充：`${WORK_ROOT}` 为本地推理迁移/性能实验工作根，包含文中 mia、venv 与 task-workspace 相对目录。按本地环境设置变量，保留文中的相对路径关系。

## 触发与观测

（失败，事件 744 工具结果原文逐字）：

```
|[2026-10-14 18:40:12] [ERROR] [1441345] profiler.py: Failed to export CANN Profiling data. Error msg: Export CANN Profiling data failed! 'msprof' command not found!Please re-source the CANN package to fix this error.
```

（修复前的三种失败形态，均为客观工具结果）：

- 形态一（事件 717）：P1 报告显示 `设备侧总耗时: 0.0 ms | host 侧总耗时: 456.8 ms | host/dev 比: 456790.514`、`设备算子种类: 0, 总下发次数: 0`，只有 host 侧 `aten::linear` 1158 次/45.02ms 等条目。
- 形态二（事件 721）：trace_view.json（截断修复后可解析）含 32988 个 X 事件，cat 仅有 cpu_op(25980)/dequeue(3504)/enqueue(3504)，无任何设备 kernel cat。
- 形态三（事件 706/690）：trace_view.json 与 export_chrome_trace 均出现尾部截断 `json.decoder.JSONDecodeError: Expecting ',' delimiter`（与 CommunicationParser 失败伴生）。

## 探针与操作

1. 定位 msprof 实际路径（事件 747/748）：`find /usr/local/Ascend/cann-9.1.0 -name "msprof"` → `/usr/local/Ascend/cann-9.1.0/tools/profiler/bin/msprof`（另有 x86_64-linux/bin 下同名）。
2. 修复 = PATH 注入后重跑（事件 750 命令原文逐字）：

```
. ${WORK_ROOT}/mia/scripts/setup_env.sh && export PATH=/usr/local/Ascend/cann-9.1.0/tools/profiler/bin:/usr/local/Ascend/cann-9.1.0/x86_64-linux/bin:$PATH && cd ${WORK_ROOT} && venv/bin/python mia/scripts/profile_p1.py task-workspace/models/pangu_2_6B run1-c0-fp32 --prompt-id s03 --steps 6 2>&1 | grep -E "top:|P1 signals|msprof|kernel_details" | head -10
```

3. 解析绑定：事件758的历史补丁选择“最新且有CSV”的目录，但最新run失败时会退回旧成功run，而且空列表在assert之前就被索引。不要把该补丁作为本次成功的判据。应由本次profiler回调或明确的run清单记录输出目录，再检查其工件；下面是供本地采用的解析守卫建议，不是轨迹内已验证的设备补丁：

```python
from pathlib import Path


def require_current_kernel_csv(current_run_output_dir):
    out_dir = Path(current_run_output_dir)
    if not out_dir.is_dir():
        raise FileNotFoundError(f"current profiler output dir not found: {out_dir}")
    kernel_csv = out_dir / "kernel_details.csv"
    if not kernel_csv.is_file():
        raise FileNotFoundError(f"current run has no kernel_details.csv: {out_dir}")
    return kernel_csv
```

`current_run_output_dir` 必须指向本次run的 `ASCEND_PROFILER_OUTPUT`，由调用方显式传入；不能通过“存在CSV”反推哪个是本次run。当前run缺失工件时应报告失败，历史目录只能做标明来源的历史分析。

4. 若需要分析截断trace，可保留原始文件并仅解析到最后一个完整事件；必须标明这是部分数据，不能将补闭合后的JSON当成完整剖析结果。优先检查本次run的kernel_details.csv。

## 机制与判别

- 根因：torch_npu 的 CANN 剖析数据导出是子进程调用 `msprof` 命令；msprof 不在 PATH 时导出失败，但 profiler 主流程不抛异常、不中断，只留下 host 侧事件——设备侧数据**静默缺失**而非报错停止，唯一线索是那条 export failed 日志。
- 判别要点：本修复解决“设备事件缺失”；trace_view.json 尾部截断是伴生的另一问题（确定性修复解析兜底）；两者都修好前，诊断（如 matmul 占比）只能用 host 分发数据降级（R1 分级降级），可能误判瓶颈。
- 验证前提：修复后必须先确认 kernel_details.csv 真的生成且目录绑定本次run，而非历史成功run（事件755给出本次目录清单），再解析下结论。

结论（失败判）：torch_npu 2.12.0.post2 的 CANN 剖析数据导出依赖 PATH 中的 msprof：msprof 缺失时仅报错 Failed to export CANN Profiling data ... 'msprof' command not found，剖析结果静默只剩 host 侧事件（trace 中仅 cpu_op/dequeue/enqueue 三类 X 事件，设备 kernel cat 为 0）。

结论（修复判）：修复为把 msprof 所在目录加入 PATH 后重跑（export PATH=/usr/local/Ascend/cann-9.1.0/tools/profiler/bin:/usr/local/Ascend/cann-9.1.0/x86_64-linux/bin:$PATH）：最新 run 目录生成 kernel_details.csv 等完整 CSV，设备侧 Top 算子可解析（aclnnAddmm_MatMulV3Common_MatMulV3 1152 次/47.12ms）。

结论（解析边界）：历史run会残留，不能通过“最新且含CSV”选择验收工件。应记录并显式传入本次run输出目录，缺失设备CSV则不能报告本次设备分析成功。trace_view.json若截断，修复出的部分数据也须标明不完整。

## 验证信号

- 事件 755：最新 run 目录（本次run的 `*_ascend_pt/ASCEND_PROFILER_OUTPUT/`）出现 kernel_details.csv、operator_details.csv、step_trace_time.csv、task_time.csv、analysis.db、ascend_pytorch_profiler.db（对比：失败 run 目录只有 analyse.done + trace_view.json）。
- 事件 761：设备侧 Top 算子成功解析（aclnnAddmm_MatMulV3Common_MatMulV3 1152 次/47.12ms、aclnnMatmul_TransposeAiCore_Transpose 576 次/1.82ms 等 5 项）。
- 修复在本轨迹内闭合：失败（744）→ PATH修复（750）→ 本次目录与解析结果（755/761）；历史解析补丁758仍有上述选择缺陷，同一剖析任务 run1-c0-fp32。
- 平台 Ascend950PR_9589 / CANN 9.1.0 / torch_npu 2.12.0.post2；单次修复验证。

## 适用与失效边界

- msprof 路径随 CANN 版本/安装布局变化（本例 /usr/local/Ascend/cann-9.1.0/tools/profiler/bin/msprof）；source 官方 set_env.sh 通常也会注入该 PATH——本机因未 source 且自组 LD_LIBRARY_PATH/OPP 环境而触发。
- 若补 PATH 后仍无设备事件，须另查 SoC 剖析支持、驱动版本与 PROF 目录权限（本轨迹未遇到，属未验证分支）。
- 输出目录名含主机名+PID+时间戳，多次重跑会残留失败目录，必须显式绑定本次输出目录并校验kernel_details.csv存在；mtime或“有CSV”只能辅助核对，不能替代run身份。
- npu-smi CLI 静默失败（exit 1 无输出）是本机另一独立异常，与剖析无关，用 acl 运行时直查替代。
