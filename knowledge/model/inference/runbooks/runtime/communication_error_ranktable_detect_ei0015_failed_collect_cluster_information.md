---
{
  "type": "Runbook",
  "title": "vLLM-Ascend TP 启动长等待掩盖 HCCL/单卡故障：用 worker 日志判别三类根因",
  "description": "模型：Qwen3.6-27B BF16（多模态）在 vLLM-Ascend 0.30.0rc2 / vLLM 0.30.0 / torch_npu，Atlas NPU 16 卡环境按需选卡 TP 部署。；现象：TP 启动后 EngineCore 长时间无输出、端口不监听、进程不退出，日志周期性打印共享内存广播等待，易被误判为“Ascend 编译慢”。",
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

# vLLM-Ascend TP 启动长等待掩盖 HCCL/单卡故障：用 worker 日志判别三类根因

## 适用场景

- 模型：Qwen3.6-27B BF16（多模态）在 vLLM-Ascend 0.30.0rc2 / vLLM 0.30.0 / torch_npu，Atlas NPU 16 卡环境按需选卡 TP 部署。
- 现象：TP 启动后 EngineCore 长时间无输出、端口不监听、进程不退出，日志周期性打印共享内存广播等待，易被误判为“Ascend 编译慢”。

## 触发与观测

- 表层观测：EngineCore 每分钟打印 `No available shared memory broadcast block found in 60 seconds.`，API server 存活但端口 18000 未监听（agent 汇总轮询，source 0 seq 742/756/894）。
- 真实根因 A（TP8，设备 8-15）：HCCL 通信初始化失败（tool_observed，source 0 seq 782 逐字）：

```text
(Worker_TP0 pid=18439) ERROR ... RuntimeError: create_config:../torch_npu/csrc/distributed/HCCLUtils.cpp:142 HCCL function error: hcclCommInitRootInfoConfig(numRanks, &rootInfo, rank, config, &(comm->hcclComm_)), error code is 1 (parameter error)
(Worker_TP0 pid=18439) ERROR ... [PID: 18439] 2026-11-05-11:14:20.052.900 Communication_Error_Ranktable_Detect(EI0015): Failed to collect cluster information of the communicator based on rootInfo detection. Reason: No rank in the communicator can connect to the root node within the timeout period. List of unconnected ranks: "[3,]".
(Worker_TP0 pid=18439) ERROR ... Solution: 1. Check whether all ranks in the communicator have delivered the communicator creation interface. ... 3. Check whether the HCCL_SOCKET_IFNAME environment variable of all nodes is correctly configured. 4. Increase the timeout by configuring the HCCL_CONNECT_TIMEOUT environment variable.
```

- 真实根因 B（TP4，设备 8,9,10,11）：物理设备 9 设备子进程/HDC 启动超时（agent 转述日志，source 0 seq 1018）：`RuntimeError: ExchangeDevice ... error code is 507033` / `Inner_Error_Device_Subprocess_Startup_Timeout` / `TsdOpen failed. devId=9` / `HDC link is faulty`；同一日志另见 Worker `init_device` 失败链（tool_observed，source 0 seq 1013：`vllm_ascend/worker/worker.py _init_device` → `Exception: WorkerProc initialization failed due to an exception in a background process`）。

## 探针与操作

- 判别探针（对启动日志直接检索，不等超时）：

```bash
rg -n 'HCCL|Communication_Error|unconnected|TsdOpen|ExchangeDevice|RuntimeError|ERROR' <vllm-server-log> | tail -60
```

- 相关超时提示（tool_observed，source 0 seq 1013/1075 逐字）：`The timeout interval of the HCCL operator is 1836s. Timeout in seconds for execute_model RPC calls in multiprocessing must be greater than 1836s, Set VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS=3000`
- 处置：根因 A 换设备集合重试（本例放弃 TP8）；根因 B 剔除故障卡（设备 9），改 TP3/TP2（8,10）。两者都不能靠延长等待解决。

## 机制与判别

- “共享内存广播等待”是 EngineCore 等待 worker 就绪的表层症状，可同时掩盖 HCCL rank 失联与单卡 HDC 故障；真正根因只出现在 Worker/EngineCore 错误日志里，必须检索而不是等待。
- 三类可区分解释：①HCCL rank 失联（EI0015 + unconnected ranks 列表，通信/网络配置维度，日志给出 4 条官方 Solution）；②单卡设备子进程启动超时（ExchangeDevice 507033 + `TsdOpen failed. devId=<N>`，直接点名物理设备）；③正常长编译（无 ERROR、日志推进到 warmup/graph capture，等待后能到 `Application startup complete`——本轨迹 TP4 首次初始化约 13 分钟后确实完成过启动）。
- 判别要点：`devId=N`/`unconnected ranks` 给出具体卡号，用于组合可用设备集合；本例最终 8,10 + TP2 成功。

## 验证信号

- 根因 A：EI0015 + `List of unconnected ranks: "[3,]"`（tool_observed，source 0 seq 782）。
- 根因 B：507033/`TsdOpen failed. devId=9`（agent 转述，source 0 seq 1018）；Worker init_device 失败堆栈（tool_observed，source 0 seq 1013）。
- 处置后成功：TP2(8,10) 完成启动并服务（tool_observed，source 0 seq 1208/1209）。
- 对照③：同配置首次初始化 ~13-14 分钟（权重加载 ~14s，其后 Ascend 编译/KV cache/多模态 encoder 初始化为主），服务在 `timeout 900` 到期瞬间才完成启动被误杀（agent 汇总，source 0 seq 954/1151）。

## 适用与失效边界

- 适用：vllm-ascend 多卡 TP 启动排障；单机多卡选卡场景。
- 失效/停止：EI0015 官方 Solution 涉及多节点网络配置（HCCL_SOCKET_IFNAME 等），本轨迹为单机场景仅用换卡规避，未验证网络侧修复；设备 9 为本机个案，结论只保留“按日志点名剔除故障卡”的方法而非固定卡号。
- 超时经验：首次启动 timeout 需覆盖编译时间（≥1800s 量级），但延长超时前必须先排除根因 A/B。

## 附：断言存档

- vLLM-Ascend TP 启动期共享内存广播长等待可掩盖真实根因：TP8 为 HCCL EI0015 unconnected rank 3；TP4 为设备 9 ExchangeDevice 507033/TsdOpen 子进程启动超时；必须检索 worker 日志而非等待

```text
Exception: WorkerProc initialization failed due to an exception in a background process. See stack trace for root cause.
```
