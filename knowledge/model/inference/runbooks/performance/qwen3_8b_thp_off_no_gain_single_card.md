---
{
  "type": "Runbook",
  "title": "Qwen3-8B 单卡 THP 开关的单次热运行对照与统计边界",
  "description": "Qwen3-8B 单卡 BF16 热运行中，THP ON 的 Prefill/Decode 为 36.89/15.48ms，OFF 为 35.25/15.4936ms。OFF 相对 ON 的 Prefill 低约 4.45%、Decode 高约 0.09%；无多轮重复，不能认定显著收益或等效。",
  "tags": [
    "task.debugging",
    "topic.memory"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# Qwen3-8B 单卡 THP 开关的单次热运行对照与统计边界

## 适用场景
- 单卡 NPU 推理服务（cann-recipes qwen3_8b 1tp 类部署）在 OS 层做性能优化选型时，评估透明大页（THP）开关收益。
- 建立环境测试基线后逐项验证 OS 优化项（THP/标准大页/malloc 大页/glibc 大页）的场景。
- 判断"OS 内存页优化是否是推理瓶颈"的决策依据。

## 触发与观测
- 触发：OS 优化项总览中 THP 原标记"OS 默认开启、无法关闭做对照、基线已含"，用户要求"把 THP 关掉对比下，看开启后有什么效果"，并以热启动数据为准。
- 观测：关闭 THP（/sys/kernel/mm/transparent_hugepage/enabled 置 never）后跑冷启动（建缓存）+ 热启动（取数），与 THP ON 热启动基线对比。

## 探针与操作

### 复现路径约定

以下路径已脱敏。历史命令中的变量占位符需由复现者按实际环境替换；Python/JSON 字符串内的占位符不会自动展开。

- `${BENCH_ROOT}`：本卡基准脚本所在工程根目录。

- 基线 bench 脚本：
````bash
bash ${BENCH_ROOT}/run_bench.sh 2>&1
````
- 负载：Qwen3-8B BF16 单卡（Ascend910，CANN 9.0.0，ge_graph 图模式，qwen3_8b_1tp.yaml，torch 2.8.0+cpu / torch_npu 2.8.0.post4 / transformers 5.0.0）。
- 统计口径：从运行日志解析 Inference time (prefill) 与全部 decode 步，计算均值/中位数/标准差/吞吐，并与 THP ON 热启动基线（Prefill 36.89 ms / Decode 15.48 ms / 64.58 tok/s）对比。

## 机制与判别
- 对照结果：
````text
=== THP OFF 热启动 ===
Prefill: 35.25 ms
Decode avg: 15.4936 ms
Decode median: 15.49 ms
Decode stdev: 0.0581 ms
Decode throughput: 64.54 tok/s

=== 对比 (THP ON 基线 vs THP OFF) ===
Prefill: 36.89 vs 35.25 -> THP 提升 +4.65%
Decode:  15.48 vs 15.4936 -> THP 提升 -0.09%
吞吐:    64.58 vs 64.54 -> THP 提升 +0.06%

=== 恢复 THP ===
[always] madvise never
````
- 判别：以 OFF 为分母，ON 的 Prefill 高 4.65%（反向比较 OFF 相对 ON 低 4.45%）、Decode 与吞吐数值接近，未建立统计等效（本次观测，见结论：）。
- 结论：THP OFF 热启动实测 Prefill 35.25 ms、Decode avg 15.4936 ms（median 15.49 ms、stdev 0.0581 ms）、吞吐 64.54 tok/s；THP ON 热启动基线 Prefill 36.89 ms、Decode 15.48 ms、吞吐 64.58 tok/s——以 OFF 为分母，ON 的 Prefill 高 4.65%（反向比较 OFF 相对 ON 低 4.45%）、ON 相对 OFF 的 Decode 约 -0.09%、吞吐约 +0.06%，未建立统计等效（本次观测）。

## 验证信号
- 客观信号：事件 1637（bench 完整输出：环境检查全 OK、推理退出码 0、结果表 Prefill 35.25 ms vs 基线 41.90 ms 为冷启动基线行）；事件 1640（热启动统计与对比计算，见上文工件）。
- 报告落盘：事件 1642/1645/1648 将结论写入 os_optimization_summary.md（THP 已测试，旧报告中的 Prefill -4.65%/Decode -0.09% 使用了混合分母或方向；本卡按 ON 基线重算为 OFF Prefill -4.45%、Decode +0.09%）。
- 注意：bench 表头显示的"基线 41.90 ms"是脚本内置冷启动基线；热启动对比使用 36.89 ms，口径以热启动为准。

## 适用与失效边界
- 适用：单卡 NPU 推理负载上评估透明大页（THP）开关的对照收益。
- 失效边界：单次热运行、无多轮重复测量，4.65% 的 Prefill 差异可能落在噪声区间；不能推广到 CPU 密集（如重度 host 侧预处理）负载。
- 未覆盖：多卡/多进程共享主机内存场景下 THP 的影响。
