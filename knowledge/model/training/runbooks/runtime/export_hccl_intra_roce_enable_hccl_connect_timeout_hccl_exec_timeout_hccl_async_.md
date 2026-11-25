---
{
  "type": "Runbook",
  "title": "950 八卡跨 UB 岛训练初始化失败排查链：py-spy 定位种子广播 → TLS 一致性 → HCCL_INTRA_ROCE_ENABLE → 最小算子隔离",
  "description": "硬件/环境：Ascend 950 单机 8 卡（NPU0-3、NPU4-7 分属两个 UB 岛），torchtitan-npu（DeepSeek-V4 Flash Engram validation，24.6B 参数，EP8/dp_shard=8）。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:03Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": [
    "950"
  ]
}
---

# 950 八卡跨 UB 岛训练初始化失败排查链：py-spy 定位种子广播 → TLS 一致性 → HCCL_INTRA_ROCE_ENABLE → 最小算子隔离

## 适用场景

- 平台范围依据：source 0 seq 111的实际环境/设备记录确认本次为Ascend 950；这里不扩展未记录的产品或版本。

- 硬件/环境：Ascend 950 单机 8 卡（NPU0-3、NPU4-7 分属两个 UB 岛），torchtitan-npu（DeepSeek-V4 Flash Engram validation，24.6B 参数，EP8/dp_shard=8）。
- 故障层：HCCL 集合通信初始化与首次集合通信，发生在模型构建/FSDP 应用前后，早于（或独立于）Engram/Muon 算子执行。

## 触发与观测

- 现象 A：8 卡作业未指定 seed 时，rank0 卡在 `Trainer.__init__` 随机种子广播后的 NPU→CPU 拷贝处；py-spy 定位阻塞点，用 `--debug.seed=42` 显式指定种子绕开该广播继续训练路径（source 0 seq 14）。
- 现象 B：模型构建/FSDP 应用完成后首次 HCCL `ALLGATHER` 运行 300 秒超时；日志含 watchdog timeout 告警与 `errcode:(0) errorStr: timeout or trap error. subErrType: 0x4`（source 0 seq 155、seq 160）。
- 同批日志中另见独立错误：`RuntimeError: torch_npu.npu_mhc_pre requires CANN >= 9.0.0. inner_precise=1 additionally requires aclnnMhcPreV2. Please upgrade CANN.`（source 0 seq 160）——属算子版本问题，与本卡通信故障相互独立。

## 探针与操作

1. py-spy 采样定位阻塞栈（source 0 seq 14）。
2. TLS 状态查询与统一（逐字，source 0 seq 271/273 输出）：

```bash
<internal_build_path> -s -tls -i 3 -enable 0
# 查询：hccn_tool -g -tls -i <i>；输出形如
# NPU3 device 3, tls switch[0](0:disable, 1:enable), tls preconfigured[1] ...
# NPU1 No certificate found, please set certs firstly!
```

3. 环境开关组合（逐字摘自 8 卡复跑命令，source 0 seq 367）：

```bash
export HCCL_INTRA_ROCE_ENABLE=1; export HCCL_CONNECT_TIMEOUT=120; export HCCL_EXEC_TIMEOUT=120; export HCCL_ASYNC_ERROR_HANDLING=0; export HCCL_NPU_SOCKET_PORT_RANGE=29000-29063; export HCCL_HOST_SOCKET_PORT_RANGE=29100-29163
```

4. 最小 8 卡 `all_reduce` 对照（source 0 seq 439）。

## 机制与判别

- 极小复现把失败落到环境层：HCCL 报告 TLS 配置不一致——只有 NPU3 开启 TLS、其余 7 卡关闭，8 卡 communicator 创建阶段直接失败；拓扑确认 NPU0-3 与 NPU4-7 为两个 UB 岛（source 0 seq 270）。
- 统一 TLS（NPU3 关闭）并开启 `HCCL_INTRA_ROCE_ENABLE=1` 后，标准 8 卡 HCCL 通信通过、8 个 rank 均收到 `[0..7]`（source 0 seq 366）——950 跨 NUMA/UB 岛路径需要该模式。
- 判别：最小 `all_reduce` 全 rank 返回 36，说明跨 UB 岛的普通 HCCL 路径可用；训练失败发生在更高层 DTensor/SPMD 通信或其输入准备阶段，而非底层 HCCL 建链（source 0 seq 439）。
- 判别：`ALLGATHER` 超时不是 Engram kernel 或 Muon 算法异常（source 0 seq 155）；种子广播卡死与 ALLGATHER 超时是两个独立症状（source 0 seq 14 vs seq 155）。
- NPU1 无证书，驱动拒绝任何 TLS 设置（source 0 seq 273），跨岛含 NPU1 的组合无法靠统一开关修复。

## 验证信号

- tool_observed：py-spy 栈定位 rank0 卡在种子广播 NPU→CPU 拷贝（source 0 seq 14）。
- tool_observed：hccn_tool 输出仅 NPU3 TLS 开启、NPU1 无证书（source 0 seq 273）。
- tool_observed：统一 TLS + `HCCL_INTRA_ROCE_ENABLE=1` 后 8 rank broadcast 全通过（source 0 seq 366）。
- tool_observed：最小 8 卡 all_reduce 全部返回 36（source 0 seq 439）。
- 单次环境、单次观测；Engram 专用跨岛通信是否仍受 UB 岛物理链路限制当时仍待验证（source 0 seq 366）。

## 适用与失效边界

- 适用：Ascend 950 双 UB 岛单机 8 卡、torchrun/torchtitan 类作业的 HCCL 初始化失败分层排查（进程栈 → 最小集合通信 → TLS/ROCE 开关）。
- 边界：`HCCL_INTRA_ROCE_ENABLE=1` 的必要性来自本机跨 NUMA/UB 岛路径（CANN 建议项），单岛 4 卡组合此前不需要该开关即可通过；TLS 需全组一致且证书齐全（NPU1 无证书则该卡无法参与统一 TLS 组）（source 0 seq 270、273）。
- 失效：若统一 TLS + ROCE 开关后 ALLGATHER 仍超时，应转向高层 DTensor/SPMD 输入准备排查而非继续改 HCCL 环境变量（source 0 seq 439）；种子广播卡死可用显式 seed 绕开但不消除底层广播问题（source 0 seq 14）。

## 附：断言存档

- 950 八卡跨 UB 岛 HCCL 初始化失败分层排查：py-spy 定位种子广播卡死（可用显式 seed 绕开）；极小复现发现仅 NPU3 开 TLS 致 communicator 创建失败；统一 TLS + HCCL_INTRA_ROCE_ENABLE=1 后 8 卡 broadcast 通过；最小 all_reduce 通过则指向 DTensor/SPMD 高层而非 HCCL 建链
