---
{
  "type": "Runbook",
  "title": "vLLM-Ascend 启动显存校验：他进程占卡时默认 gpu-memory-utilization=0.92 直接 ValueError",
  "description": "模型：Qwen3.6-27B BF16（多模态，TP 部署）在 vLLM-Ascend 0.30.0rc2 / torch_npu，共享 NPU 环境（卡上已有其他进程占用）。；启动参数含默认 `--gpu-memory-utilization 0.92`，物理卡 61.28 GiB。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:06Z",
  "updated_at": "2026-11-20T14:17:06Z",
  "platforms": []
}
---

# vLLM-Ascend 启动显存校验：他进程占卡时默认 gpu-memory-utilization=0.92 直接 ValueError

## 适用场景

- 模型：Qwen3.6-27B BF16（多模态，TP 部署）在 vLLM-Ascend 0.30.0rc2 / torch_npu，共享 NPU 环境（卡上已有其他进程占用）。
- 启动参数含默认 `--gpu-memory-utilization 0.92`，物理卡 61.28 GiB。

## 触发与观测

- 触发：TP8 启动时每卡仅剩约 27.73 GiB 空闲，worker 在设备初始化阶段退出。
- 原始报错（tool_observed，source 0 seq 614 逐字）：

```text
(Worker pid=15043) ERROR 11-05 09:26:58 [multiproc_executor.py:944]   File "/vllm-workspace/vllm/vllm-ascend/vllm_ascend/worker/worker.py", line 458, in _init_device
(Worker pid=15043) ERROR 11-05 09:26:58 [multiproc_executor.py:944]     raise ValueError(
(Worker pid=15043) ERROR 11-05 09:26:58 [multiproc_executor.py:944] ValueError: Free memory on device (27.73/61.28 GiB) on startup is less than desired GPU memory utilization (0.92, 56.38 GiB). Decrease GPU memory utilization or reduce GPU memory used by other processes.
```

## 探针与操作

- 判别：该 ValueError 出现在 `_init_device` 早期（早于权重加载与 HCCL），报错自带当前空闲/总量与目标值，可直接按比例下调。
- 修复：`--gpu-memory-utilization 0.40`（TP8，每 worker 权重 ~3.84 GiB）重启通过显存校验并完成权重加载；TP2 场景用 0.50（每卡权重 ~25.9 GiB，17.25*3/2 卡口径见 agent 汇总 source 0 seq 1030/1088）。

## 机制与判别

- vllm-ascend worker 启动即按 `物理总量 × utilization` 与当前空闲显存比较，不足直接抛错退出；他进程占卡（本例每卡被占约 33.5 GiB）时 0.92 默认值必然失败。
- 可区分解释：该错误与模型权重是否损坏无关（降参数后同一权重加载成功）；与 HCCL 失败（w32-s1-c3）可按报错文本区分。
- 权重体量参考（本轨迹实测，agent 汇总）：TP8 每 worker ~3.8442 GiB、TP4 每 worker ~7.5 GiB、TP2 每卡 ~25.9 GiB（27B BF16 总量 ~52 GB 与分片口径一致）。

## 验证信号

- 失败：ValueError 逐字报错（tool_observed，source 0 seq 614）。
- 修复后：TP8 util0.40 通过显存校验、8 分片加载成功、HCCL 进入初始化（agent 汇总，source 0 seq 619-664）；TP2 util0.50 完成全流程启动并服务（tool_observed，source 0 seq 1208/1216 进程参数可见 `--gpu-memory-utilization 0.50`）。

## 适用与失效边界

- 适用：共享 NPU（多进程/多服务混部）下启动 vLLM-Ascend；vLLM 同名参数语义在 NPU 平台的映射（free memory 校验）。
- 失效/停止：降 utilization 只解决“空闲显存不足”类失败，会同时压缩 KV cache 可用块（过低下采样吞吐，且另一约束 `max_num_seqs (256) exceeds available Mamba cache blocks (100)` 需 `--max-num-seqs 64` 配合，agent 转述，source 0 seq 1309/1355）；若空闲显存低于单卡权重需求则只能减 TP 卡数（增大每卡份额）或清卡。
- 数值为本机观测（61.28 GiB 物理 / 27.73 GiB 空闲），换卡型或清卡后需重算。

## 附：断言存档

- 共享 NPU 环境每卡空闲 27.73/61.28 GiB 时默认 --gpu-memory-utilization 0.92 在 worker _init_device 阶段抛 ValueError 退出；下调至 0.40(TP8)/0.50(TP2) 后同一权重完成加载与启动
