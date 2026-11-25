---
{
  "type": "Runbook",
  "title": "sr_denoise 阶段 ~550ms NPU 空闲：CPUOffloadWrapper 每步整模 CPU→NPU 权重搬运与常驻修复",
  "description": "daVinci-MagiHuman sr_540p / sr_1080p（双 DiT 各 28.54GB，5 步 SR 去噪）在 Atlas A3（Ascend 910_9382 V1，原记录65GB HBM）单卡（torch 2.10.0+cpu / torch_npu 2.10.0）上，sr_denoise 阶段 profiler 显示 NPU 长空闲。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:05Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": [
    "a3"
  ]
}
---

# sr_denoise 阶段 ~550ms NPU 空闲：CPUOffloadWrapper 每步整模 CPU→NPU 权重搬运与常驻修复

## 适用场景

- 平台范围依据：source 0 seq 217的实际环境/设备记录确认本次为Atlas A3；这里不扩展未记录的产品或版本。

- 以source 0 seq217的实机asys型号为准；早期进度里的Atlas A2括注不再采用。

daVinci-MagiHuman sr_540p / sr_1080p（双 DiT 各 28.54GB，5 步 SR 去噪）在 Atlas A3（Ascend 910_9382 V1，原记录65GB HBM）单卡（torch 2.10.0+cpu / torch_npu 2.10.0）上，sr_denoise 阶段 profiler 显示 NPU 长空闲。分析方法适用于一切「按 kernel timeline 定位固定空闲 gap」的场景。

## 触发与观测

- 量化（step_trace_time.csv，单 profiled step）：sr_540p Computing 3.015s / Free 0.564s / 空闲占比 15.8%；sr_1080p Computing 29.538s / Free 0.566s / 占比 1.9%——两分辨率空闲绝对值几乎相同（~0.565s），是固定开销而非分辨率相关（source 0 seq 38/45/50）。
- gap 归因（task_time.csv 逐 kernel 差分 + trace_view.json 区间事件）：单一大 gap 544.8ms（540p）/549.6ms（1080p），出现在首个 `Sort`（AI_CPU）之前，占全部空闲 96%；区间内 331 次 `aten::to` → `aten::_to_copy` → `aten::copy_` → `AscendCL@aclrtMemcpy`（合计 517ms），即 SR 模型 331 个权重张量逐个 CPU→NPU 搬运（source 0 seq 60/128/142/154）。
- 根因代码：`CPUOffloadWrapper._run_with_optional_offload`（cpu_offload_wrapper.py:182）每次 forward 前 `self.model.to(self.npu_device)` 整模上卡、forward 后回 CPU——5 个 SR step 每步搬一次（source 0 seq 151）。容量核算：SR 阶段前 NPU 仅占用 2.14GB（540p）/2.21GB（1080p），65GB HBM 远大于 SR 模型 28.54GB，可整体常驻（source 0 seq 186/181）。

## 探针与操作

- 空闲量化：`ASCEND_PROFILER_OUTPUT/step_trace_time.csv` 的 Computing/Free/Stage 列；`task_time*.csv` 按 task_start/task_stop 差分列 top gap；`trace_view.json` 解析 gap 区间内事件聚合（按 name 汇总 count/total dur）。
- 修复（video_generate.py SR denoise 循环前后）：循环前 `gc.collect(); torch.npu.empty_cache()` 后调用 `sr_model.disable_offload()` 使 SR 模型常驻 NPU（base 已回 CPU）；循环后 `enable_offload()` 恢复（source 0 seq 202-208）。
- 副作用修复：`infer_sr_1080p.sh:15` 默认 `export SR2_1080=true`，该分支会 `self.sr_model = self.sr_model.to("cpu")` 把 `CPUOffloadWrapper` unwrap 成裸 `DiTModel`，导致随后的 `enable_offload()` 报 `AttributeError: 'DiTModel' object has no attribute 'enable_offload'`；调整顺序为 `enable_offload()` 先于 SR2_1080 unwrap（source 0 seq 338/384/389）。

## 机制与判别

- 判别特征：「空闲绝对值不随分辨率/计算量变化」指向固定开销（权重搬运/同步/初始化），「gap 集中在首个 AI_CPU Sort 前」+「区间内 aclrtMemcpy × 恰好等于权重张量数」锁定 per-forward 整模 offload。
- 修复成立的前提是内存核算：SR 阶段独占设备时余量充足才可常驻；否则需分块或换卡。
- 干扰排除：profiler 解析本身可在 SR 段引入 ~60s 墙钟噪声，且 `aten::_linalg_solve_ex` CPU 回退贡献 ~37s——墙钟对比必须看 profiled step 的 Computing/Free 或无 profiler 的 tqdm 每步（原始 5.64s/step → 优化 3.03s/step）（source 0 seq 266/298/315）。

## 验证信号

- profiler apples-to-apples（同一 profiled step）：sr_540p Free 564ms→12ms（-97.8%），Stage 3.580s→3.015s；sr_1080p Free 566ms→10ms（-98.2%），Stage 30.103s→29.718s（source 0 seq 273/413）。
- 输出正常：sr_540p 1.99MB、sr_1080p 8.3MB mp4 落盘（source 0 seq 321/419，tool_observed）。
- 无 profiler 的 tqdm 每步：5.64s/step → 3.03s/step（source 0 seq 312）。

## 适用与失效边界

修复依赖「SR 模型可整模驻留」的显存前提（本例 65GB 卡 + 阶段性独占）；HBM 更小或需与其他大模型并发时不适用。331 张量/517ms 的数字限本模型与 PCIe/HCCS 带宽。SR2_1080 顺序 bug 是该仓库脚本默认值交互所致；linalg_solve CPU 回转为独立已知问题。

## 附：断言存档

- sr_denoise 阶段 ~0.565s 固定 NPU 空闲（540p 占 15.8%、1080p 占 1.9%，绝对值与分辨率无关）的根因是 CPUOffloadWrapper._run_with_optional_offload 每次 forward 前把 SR 模型整体 CPU→NPU：trace 区间内 331 次 aten::to→aclrtMemcpy 合计 517ms，单一大 gap 占全部空闲 96%；内存核算（SR 阶段前仅占 2.14GB，65GB HBM 可容纳 28.54GB SR 模型）支持常驻。

```text
name                                                  count total_dur_us  total_s
Free                                                      4       544965    0.545
aten::to                                                331       527439    0.527
aten::_to_copy                                          331       526535    0.527
aten::copy_                                             331       519909    0.520
AscendCL@aclrtMemcpy                                    331       517070    0.517
```
