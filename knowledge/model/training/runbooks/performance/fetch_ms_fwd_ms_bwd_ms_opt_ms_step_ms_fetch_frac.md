---
{
  "type": "Runbook",
  "title": "Speculators 训练取数瓶颈分诊：`fetch_ms/fetch_frac`（_StepTimer）定位数据链路占比，`Time taken for batch_get_into` 是 Mooncake C++ easylog INFO 且用 `MC_YLT_LOG_LEVEL` 控制",
  "description": "Speculators/hs_connectors 训练（NPU + Mooncake 取数）性能排查：判断 step 慢在取数还是计算、取数内部又慢在哪一段，以及治理 Mooncake 原生计时日志。",
  "tags": [
    "task.optimization",
    "topic.performance.analysis"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:04Z",
  "updated_at": "2026-11-20T14:17:04Z",
  "platforms": []
}
---

# Speculators 训练取数瓶颈分诊：`fetch_ms/fetch_frac`（_StepTimer）定位数据链路占比，`Time taken for batch_get_into` 是 Mooncake C++ easylog INFO 且用 `MC_YLT_LOG_LEVEL` 控制

> 候选 w09-s2-c4 · area=performance · route=training · form=diagnostic_rule
> 来源：source 0 = 内部账号

## 适用场景

Speculators/hs_connectors 训练（NPU + Mooncake 取数）性能排查：判断 step 慢在取数还是计算、取数内部又慢在哪一段，以及治理 Mooncake 原生计时日志。

## 触发与观测

- 触发（source 0 seq 2102，user_reported 训练日志）：单 step 日志显示 `fetch_ms=4.03e+04 ms`、`fwd_ms=6.18e+03`、`bwd_ms=9.12e+02`、`opt_ms=5.84e+02`、`step_ms=4.80e+04`、`fetch_frac=0.840`（source 0 seq 2123/2152 复述，tool_observed 数值来自日志）。
- 日志来源判别（source 0 seq 63 digest 摘要级 + seq 1917，agent_narrative+tool_observed strings 结果）：`Time taken for batch_get_into:` 不在训练仓库打印，来自已安装 Mooncake 原生库（`strings libmooncake_store.so` 能找到原样字符串，含 `Time taken for batch_get_into_offload_object_internal:` 等内部阶段）；训练仓库侧计时是 `trainer.py` 的 `_StepTimer`（每次 mark 强制 accelerator.synchronize 取真实设备时间）并经 `speculators.metrics` 记录 `fetch_ms/fwd_ms/bwd_ms` 等。
- 该日志只覆盖原生 `batch_get_into()` 调用耗时，不等于完整取数耗时：之后还有 NPU slot 复制、同步与校验（source 0 seq 75 digest 摘要级，agent_narrative）。

## 探针与操作

- 占比分诊（source 0 seq 2123/2152，agent_narrative）：`fetch_frac=0.84` 即每 step 约 48 s 中 40 s 在取数、训练计算合计约 7.7 s → 优先优化数据供应链（vLLM 生成、meta 等待、batch_get_into、token_ids get_tensor、collate），而非 forward/backward。
- 段内拆分（source 0 seq 2152，agent_narrative）：分别记录 A `generate_hidden_states()` 起止、B `_wait_for(meta)`、C `batch_get_into`、D `token_ids get_tensor`、E Collate、F forward；A-B 大→vLLM/HTTP 排队；B-C 大→Producer 写入/meta 发布延迟；C-D 大→ADXL/HCCL 读取瓶颈。
- 疑点排序（source 0 seq 2152）：同 rank 内同步 HTTP 串行请求 + 等最慢 rank；Producer 单 writer（`self._num_writer_threads = 1`）排队；meta 等待/`OBJECT_NOT_FOUND`、`REPLICA_IS_NOT_READY`、`TRANSFER_FAIL` 重试；direct-read 仍有 `ADXL pool slot -> hidden_states_out -> CollateFn batch buffer` 两次潜在拷贝。
- 关日志（source 0 seq 1917，agent_narrative）：`export MC_YLT_LOG_LEVEL=error`（或单次 `MC_YLT_LOG_LEVEL=error torchrun ...`）隐藏 INFO/WARN 保留 ERROR/CRITICAL；源码默认 `warn`，若仍打印说明运行时被设成 `info`。不要依赖 `GLOG_minloglevel`——Mooncake 该部分走 easylog 级别控制，不受 glog 环境变量影响；只屏蔽单条日志需改源码重编 `libmooncake_store.so`。

## 机制与判别

`profile/fetch_ms` 是「上一个 step 结束到 forward 开始」的总等待，包含 DataLoader 取样、vLLM HTTP、meta 等待、传输、collate、搬运；不能把 fetch_ms 直接当推理耗时。判别次序：先看 fetch_frac 确认数据链路占比 → 再用 A-F 时间点拆段 → `Time taken for batch_get_into` 数值与 fetch_ms 的占比决定查传输（ADXL/HCCL）还是查复制/同步/校验/collate。注意本案例中 fetch_ms=40s 期间同时存在 `get_buffer ...:meta` 分配失败重试（w09-s2-c2），配置错误会直接污染 fetch 口径——先修配置再测性能（source 0 seq 2123）。

## 验证信号

- fetch_frac=0.840、各段毫秒值为训练日志原始输出（source 0 seq 2102/2123，tool_observed/user_reported）。
- 单机 1→3 测试日志中出现 `Time taken for batch_get_into: ...` 印证该串来自 Mooncake 侧（source 0 seq 742，tool_observed）。
- A-F 拆分与 1→4/1→8/1→16 阈值实验在本轨迹未执行，属建议项。

## 适用与失效边界

- 数值（40.3 s/48 s/84%）是本次观测（2 机 16 卡、该版本 vLLM/Mooncake/CANN、含已修复的 local buffer 配置后日志），不构成通用加速比；无 baseline/candidate 同 workload 对比，不作性能结论。
- `MC_YLT_LOG_LEVEL` 语义与 easylog 实现绑定，Mooncake 版本变更需复核；`_StepTimer` 每次 mark 强制同步本身有开销（日志频率 `log_freq` 可调，source 0 seq 2038 digest 摘要级）。

## 附：断言存档

- fetch_frac=0.840（fetch 40.3s / step 48.0s，fwd 6.18s、bwd 0.91s、opt 0.58s）表明瓶颈在取数链路而非训练计算；应用 A-F 时间点拆分（generate_hidden_states→meta 等待→batch_get_into→get_tensor→collate→forward）定位段内热点

```text
fetch_ms   = 4.03e+04 ms
fwd_ms     = 6.18e+03 ms
bwd_ms     = 9.12e+02 ms
opt_ms     = 5.84e+02 ms
step_ms    = 4.80e+04 ms
fetch_frac = 0.840
```
