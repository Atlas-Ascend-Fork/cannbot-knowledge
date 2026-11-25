---
{
  "type": "Runbook",
  "title": "Mooncake Ascend Direct 跨机 1 producer→16 consumer 在 HCCL 通信域建立阶段失败（503900/HcclCommPrepare ret 0x9），单机 1→3 同版本可行",
  "description": "Speculators 训练链路（2 机 16 卡 Ascend NPU）用 Mooncake Ascend Direct（ADXL）从 vLLM 推理 producer 向训练侧 consumer 传输 hidden states：producer 1 个 TransferEngine。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:04Z",
  "updated_at": "2026-11-20T14:17:04Z",
  "platforms": []
}
---

# Mooncake Ascend Direct 跨机 1 producer→16 consumer 在 HCCL 通信域建立阶段失败（503900/HcclCommPrepare ret 0x9），单机 1→3 同版本可行

> 候选 w09-s2-c1 · area=runtime · route=training · form=diagnostic_rule
> 来源：source 0 = 内部账号

## 适用场景

Speculators 训练链路（2 机 16 卡 Ascend NPU）用 Mooncake Ascend Direct（ADXL）从 vLLM 推理 producer 向训练侧 consumer 传输 hidden states：producer 1 个 TransferEngine，训练侧每 rank 各初始化 1 个 consumer engine（direct-read/方案 B）。出现 producer 端 `batch_put_from` 失败而 consumer 端 engine 均已监听时适用。

## 触发与观测

- 触发：跨机场景 producer 写第一个样本即失败。用户提供的 producer 时间线（source 0 seq 521，user_reported）：`HcclAdapter::HcclCommPrepare fail, ret: 0x9`，`error code[503900], local engine:[内网地址已脱敏], remote engine:[内网地址已脱敏], timeout:10000 ms`；producer 轮询 13 个不同 consumer 端口全部 503900/Transfer failed，24 次 Transfer failed，12 个样本写入失败；consumer 端 0 个 503900、80 个 `Timed out waiting for Mooncake key`。
- 错误链（source 0 seq 521，user_reported）：`HcclAdapter::HcclCommPrepare fail, ret: 0x9 (channel.cc:79) → channel->Initialize fail → CreateChannel fail → ConnectInfoProcess fail → 503900: Failed to check peer process ret status (channel_msg_handler.cc:568) → DoConnect fail → ConnectWhenTransfer fail (adxl_inner_engine.cc:528) → TransferSync fail → batch_put_from status=-800 → RuntimeError: Mooncake batch_put_from failed`。
- 判别一（source 0 seq 526，agent_narrative）：失败点在「已找到远端 engine 之后的 HCCL 通信域建立阶段」，不是 TCP 端口未监听（consumer 16 个引擎全部初始化并监听成功）；consumer 侧 meta 超时是 producer 写失败的连锁反应，非独立故障。
- 根因收窄（source 0 seq 514，agent_narrative）：工作区 diff 中 `_set_direct_read_enabled(True)` 覆盖了显式 `MOONCAKE_ADXL_PROXY=1`，导致 16 个 rank 全部初始化 consumer engine；503900 的直接原因是 proxy 模式被状态覆盖后错误创建多 consumer。

## 探针与操作

- 单机隔离实验设计（source 0 seq 620，agent_narrative+tool_observed）：本机无 NPU 设备节点时先确认前置（`/dev/davinci*`、`/dev/hisi_hdc`、可启动的 Ascend Mooncake master）；现有 `scripts/test_mooncake_npu_transfer.py` 固定 `protocol="tcp"` 且 producer 先拷 CPU，不能用于验证 HCCL 1→多。
- 单机 1→3 实测（source 0 seq 741/742，tool_observed）：NPU 12 producer + NPU 13/14/15 三个 consumer，Master :50051，Ascend Direct 协议，一次性 /tmp 脚本：三个 consumer 均完成 `batch_get_into()` + NPU tensor 内容/token_ids/hidden_states 校验，日志 `Connected to segment: ...`×3、`RECEIVED adxl-1tomany-shared`，全程无 503900、无 HcclCommPrepare fail。
- 环境注意（source 0 seq 1537，agent_narrative）：昇腾要求 `HCCL_CONNECT_TIMEOUT` 至少 120 秒，设 10 不合法会以无关错误先行失败。

## 机制与判别

503900 表示 HCCL channel 建立时「对端进程返回状态检查失败」，发生在首次实际传输触发 `HcclCommPrepare/CreateChannel` 时（engine 初始化成功不等于 channel 可建）。单机 1→3 成功证明当前 CANN/Mooncake 版本的 Ascend Direct 本身支持 1→多 consumer；跨机 1→16 失败不能归因于「不支持一对多」，判别方向应依次排查：consumer 规模/HCCL channel 数量上限、consumer 设备映射（`ASCEND_RT_VISIBLE_DEVICES` 每 consumer 独立且真实绑定不同 NPU）、多进程同时初始化的资源竞争、跨机网络/设备配置、producer/consumer CANN 与 libhccl 版本一致性（source 0 seq 742/526，agent_narrative）。

## 验证信号

- 单机 1→3：三个 consumer RECEIVED 且校验通过（source 0 seq 742，tool_observed）。
- 跨机 1→16：13 个端口、24 次 Transfer failed 全部同链路失败（source 0 seq 521，user_reported）。
- 1→4/1→8/1→16 阈值实验在本会话未执行，失败规模阈值未确定（source 0 seq 742 明确列为下一步）。

## 适用与失效边界

- 结论限定 Mooncake Ascend Direct + HCCL 传输路径；TCP/RDMA Mooncake 不经过 HCCL channel，不适用本判别。
- 单机结论不外推跨机：单机 HCCS 拓扑与跨机 RoCE/网络配置不同；跨机失败的最终根因（规模上限 vs 环境不一致）在本轨迹内未闭合，修复验证见后续会话（用户回退多 consumer 改动恢复跨机可用，source 0 seq 761/774 digest 摘要级）。
- 排查时先核对 `MOONCAKE_ADXL_PROXY` 等显式开关是否被进程内 direct-read 状态覆盖（优先级应为显式 proxy 配置 > 默认 direct-read，source 0 seq 514）。

## 附：断言存档

- 跨机 1 producer→16 consumer 时 Mooncake Ascend Direct 在 HCCL 通信域建立阶段失败（HcclCommPrepare ret 0x9 / 503900），13 个 consumer 端口全部失败；consumer 引擎均已监听，meta 超时为连锁反应

```text
HcclAdapter::HcclCommPrepare fail, ret: 0x9  (channel.cc:79)
  → channel->Initialize fail  (channel_manager.cc:415)
  → CreateChannel fail  (channel_msg_handler.cc:337)
  → ConnectInfoProcess fail  (channel_msg_handler.cc:411)
  → 503900: Failed to check peer process ret status  (channel_msg_handler.cc:568)
  → DoConnect fail  (channel_msg_handler.cc:525)
  → ConnectWhenTransfer fail  (adxl_inner_engine.cc:528)
  → TransferSync fail  (adxl_engine_impl.cc:116)
  → batch_put_from status=-800  (Python层)
  → RuntimeError: Mooncake batch_put_from failed
```

```text
Connected to segment: [REDACTED:private_ip]:21230
Connected to segment: [REDACTED:private_ip]:21354
Connected to segment: [REDACTED:private_ip]:21479
Time taken for batch_get_into: ...
RECEIVED adxl-1tomany-shared
```
