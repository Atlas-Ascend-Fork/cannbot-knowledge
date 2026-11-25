---
{
  "type": "Runbook",
  "title": "daVinci-MagiHuman CPU offload 单次耗时插桩与 NPU→CPU/CPU→NPU 不对称观测",
  "description": "模型/框架：SandAI daVinci-MagiHuman 视频生成模型（base DiT + SR denoise DiT 双模型流水线），CANN/torch_npu 环境，NPU 单卡（torch.npu.synchronize 可用）。",
  "tags": [
    "task.implementation",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:04Z",
  "updated_at": "2026-11-20T14:17:04Z",
  "platforms": []
}
---

# daVinci-MagiHuman CPU offload 单次耗时插桩与 NPU→CPU/CPU→NPU 不对称观测
## 适用场景

- 模型/框架：SandAI daVinci-MagiHuman 视频生成模型（base DiT + SR denoise DiT 双模型流水线），CANN/torch_npu 环境，NPU 单卡（torch.npu.synchronize 可用）。
- 目标：量化 CPUOffloadWrapper 在推理管线中的 offload 真实耗时，定位 offload 环节主导开销；sr_540p 与 sr_1080p 共用 `inference/pipeline/video_generate.py` 的 `evaluate()` 路径，一处插桩同时覆盖。
- offload 配置：`offload_config.model_cpu_offload=true, gpu_resident_weight_ratio=0.35, offload_policy=HEURISTIC`（source 0 seq 51/55）。


## 触发与观测

用户要求分别统计 base model offload 与 SR denoise model CPU→NPU 耗时（source 0 seq 1）。真实运行日志（log_infer_sr_540p.log / log_infer_sr_1080p.log，2026-07-06）逐字输出（source 0 seq 108）：

```text
log_infer_sr_540p.log:360:[2026-07-06 19:51:57,860 - INFO] [Rank 0] [OFFLOAD] Base model offload (NPU->CPU) time: 0.003 s
log_infer_sr_540p.log:366:[2026-07-06 19:52:07,655 - INFO] [Rank 0] [OFFLOAD] SR denoise model CPU->NPU time: 1.683 s
log_infer_sr_1080p.log:360:[2026-07-06 19:58:21,746 - INFO] [Rank 0] [OFFLOAD] Base model offload (NPU->CPU) time: 0.002 s
log_infer_sr_1080p.log:366:[2026-07-06 19:58:31,667 - INFO] [Rank 0] [OFFLOAD] SR denoise model CPU->NPU time: 1.855 s
```

同日志解析复核（source 0 seq 137）：`Base=11.219, SR=30.837, Decode=8.953, BaseOffload=0.003, SRLoad=1.683`（540p）；`Base=11.135, SR=163.957, Decode=24.301, BaseOffload=0.002, SRLoad=1.855`（1080p）。

## 探针与操作

对 `inference/pipeline/video_generate.py` 的 `evaluate()` 做两处插桩（before 为裸调用 `self.model.enable_offload()` / `self.sr_model.disable_offload()`；after 逐字如下）。base 模型 NPU→CPU（source 0 seq 64）：

```python
        # Free HBM for the SR model: move base back to CPU and re-enable offload.
        if base_is_wrapped:
            torch.npu.synchronize()
            _base_offload_start = time.time()
            self.model.enable_offload()
            torch.npu.synchronize()
            _base_offload_elapsed = time.time() - _base_offload_start
            print_rank_0(f"[OFFLOAD] Base model offload (NPU->CPU) time: {_base_offload_elapsed:.3f} s")
```

SR denoise 模型 CPU→NPU（source 0 seq 68）：

```python
            sr_is_wrapped = isinstance(self.sr_model, CPUOffloadWrapper)
            if sr_is_wrapped:
                torch.npu.synchronize()
                _sr_load_start = time.time()
                self.sr_model.disable_offload()
                torch.npu.synchronize()
                _sr_load_elapsed = time.time() - _sr_load_start
                print_rank_0(f"[OFFLOAD] SR denoise model CPU->NPU time: {_sr_load_elapsed:.3f} s")
```

前置 `import time`（source 0 seq 60）。要点：offload 前后各一次 `torch.npu.synchronize()`，保证测的是该次搬运的 wall time 而非异步队列时间。

## 机制与判别

- 结论 1：synchronize+time 包裹法可以直接测得 CPUOffloadWrapper 单次 enable/disable_offload 的 wall time，并落到现有 `print_rank_0` 日志体系（source 0 seq 64、68；语法校验 source 0 seq 78，解析回读 source 0 seq 137）。
- 结论 2：本次观测中 SR 模型 CPU→NPU 加载（1.683s/1.855s）比 base 模型 NPU→CPU 卸载（0.003s/0.002s）高约三个数量级；在该 0.35 常驻比例配置下，offload 环节的主导开销是 SR 模型重载。
- 未验证推断：NPU→CPU 侧近零的机制未剖析——可能因异步搬运未真正同步完成、或 gpu_resident_weight_ratio=0.35 使大部分权重常驻无需回搬，本轨迹无证据区分，不作为已证机制。

## 验证信号

- 工具观测（tool_observed）：`python3 -c "import ast; ast.parse(...)"` → `syntax OK`（source 0 seq 78）；grep 真实日志得到 4 行 OFFLOAD 计时（source 0 seq 108）；log_stat 解析回读与日志一致（source 0 seq 137）。
- 信号等级：设备运行日志（Rank 0），单次运行、每分辨率各 1 个样本；无重复采样与统计口径。
- 覆盖 base/distill（无 SR、无 OFFLOAD 行）路径：正则不匹配返回 0.0，输出侧由 `if has_sr` 守护（source 0 seq 157 模拟日志验证）。

## 适用与失效边界

- 单卡、rank0 输出；多卡场景仅 rank0 可见。数值仅代表该次运行的 wall time，不能外推为该模型 offload 的普遍耗时。
- 0.003s 的 NPU→CPU 侧测量值不应解读为"回搬免费"——机制未知（见上）。
- 失效条件：offload 实现改为纯异步且不在此处同步时，包裹法测到的将只是提交耗时； gpu_resident_weight_ratio/offload_policy 改变后不对称幅度可能变化，需重测。

## 附：断言存档

- 在 CPUOffloadWrapper 包装的模型上，用 torch.npu.synchronize()+time.time() 包裹 enable_offload()/disable_offload() 并经 print_rank_0 输出，可测得单次 offload 操作的 wall time；sr_540p 与 sr_1080p 共用 video_generate.py 的 evaluate() 路径，一处插桩同时覆盖两种分辨率。
- 本次观测（offload_config: model_cpu_offload=true, gpu_resident_weight_ratio=0.35, offload_policy=HEURISTIC，sr_540p/sr_1080p 各 1 次真实运行）：base 模型 enable_offload（NPU→CPU）耗时 0.003s/0.002s，SR denoise 模型 disable_offload（CPU→NPU）耗时 1.683s/1.855s；SR 模型重载是 offload 环节的主导开销。NPU→CPU 侧近零的机制未剖析（是否异步或与常驻权重比例有关，未知）。
