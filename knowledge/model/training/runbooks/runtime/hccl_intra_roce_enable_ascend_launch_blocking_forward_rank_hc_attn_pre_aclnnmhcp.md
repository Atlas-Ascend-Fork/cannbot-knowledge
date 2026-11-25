---
{
  "type": "Runbook",
  "title": "950 八卡组合验证两重阻塞：成功启动环境差集（HCCL_INTRA_ROCE_ENABLE+端口段）与 torch_npu inner_precise=1 的 aclnnMhcPreV2 缺失",
  "description": "环境/任务：Ascend 950 八卡，torchtitan-npu DeepSeek-V4 Engram + MHC + sparse_attn 三 override 组合验收（CANN 9.2.0 稳定环境）。；两重阻塞分别位于：HCCL 初始化（环境层）与首次 forward 的 mHC 算子调用（算子 ABI 层）。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:04Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": [
    "950"
  ]
}
---

# 950 八卡组合验证两重阻塞：成功启动环境差集（HCCL_INTRA_ROCE_ENABLE+端口段）与 torch_npu inner_precise=1 的 aclnnMhcPreV2 缺失

## 适用场景

- 平台范围依据：source 0 seq 365的实际环境/设备记录确认本次为Ascend 950；这里不扩展未记录的产品或版本。

- 环境/任务：Ascend 950 八卡，torchtitan-npu DeepSeek-V4 Engram + MHC + sparse_attn 三 override 组合验收（CANN 9.2.0 稳定环境）。
- 两重阻塞分别位于：HCCL 初始化（环境层）与首次 forward 的 mHC 算子调用（算子 ABI 层）。

## 触发与观测

- 第二轮 8 卡在 `set_determinism()` 前的 HCCL/AICPU 初始化报 `507018`，未进入 override 应用或模型 forward——该轮不能判断 MHC 与 Engram 是否冲突（source 0 seq 406）。
- 沿用已验证环境后，完整组合所有 rank 在首次 forward 的 `hc_attn_pre` 处报同一个 `aclnnMhcPreV2` 缺失，进程退出、无残留（source 0 seq 574）。

## 探针与操作

1. 历史对照（source 0 seq 457）：此前会话加入 `ASCEND_LAUNCH_BLOCKING=1`、显式 `ASCEND_RT_VISIBLE_DEVICES`、`HCCL_INTRA_ROCE_ENABLE=1` 与 socket 端口范围后，8 卡确实能进入 forward，随后才暴露 MHC 的 `aclnnMhcPreV2` 缺失。
2. 成功启动环境差集复现（source 0 seq 508）：8 卡前一条无 MHC 的成功训练使用 `HCCL_INTRA_ROCE_ENABLE=1`、端口 `27000-27063/27100-27163`，且未设置 `ASCEND_LAUNCH_BLOCKING` 与额外 120 秒 HCCL 超时；严格复用该环境后组合测试进入 forward。
3. 符号级定位（source 0 seq 666）：当前 `torch_npu` 在 `inner_precise=1` 时会调用 `aclnnMhcPreV2`，而本机 CANN 9.2 只提供旧的 `aclnnMhcPre`——版本接口不匹配。

## 机制与判别

- 判别一（初始化 vs 算子）：507018 发生在 override 应用前 → 属通信环境层；严格复用成功环境后越过初始化，失败点移动到 `hc_attn_pre` 的算子符号缺失——两重阻塞相互独立（source 0 seq 406、508、574）。
- 判别二（ABI 缺失根因）：代码+二进制符号核对显示 `inner_precise=1` 路径需要 `aclnnMhcPreV2`，本机 CANN 9.2 二进制无该符号 → 需要升级 CANN/换 torch_npu 构建或避开 inner_precise，而非代码修复（source 0 seq 666）。
- 绕行：保留 sparse attention 与 Engram、只启用可用的 `mhc.asc_hc_post`，让 HcPre 走 Torch 回退，验证实际可用组合（source 0 seq 574）。

## 验证信号

- tool_observed：507018 初始化失败（未进入 override/forward）（source 0 seq 406）。
- tool_observed：复用成功环境差集后组合进入 forward（source 0 seq 508）。
- tool_observed：所有 rank 首次 forward `hc_attn_pre` 报 `aclnnMhcPreV2` 缺失、无残留进程（source 0 seq 574）。
- tool_observed：符号核对 `inner_precise=1`→`aclnnMhcPreV2`，本机 CANN 9.2 仅旧 `aclnnMhcPre`（source 0 seq 666）。

## 适用与失效边界

- 适用：950 八卡 torchtitan-npu 组合验收的两层排查模板——先对齐历史成功启动环境（`HCCL_INTRA_ROCE_ENABLE=1` + 独立端口段、避免多余阻塞/超时变量），再在 forward 层做算子符号核对。
- 失效/限制：环境差集是「复现成功」的必要组合而非因果证明；`aclnnMhcPreV2` 缺失绑定当前 torch_npu 构建 × CANN 9.2.0 符号集，任一方升级后需重查；HcPre 走 Torch 回退是功能绕行，性能含义未评估。

## 附：断言存档

- 950 八卡组合验收两重阻塞：初始化层 507018 需复用成功环境差集(HCCL_INTRA_ROCE_ENABLE=1+端口段 27000-27063/27100-27163，勿加多余 ASCEND_LAUNCH_BLOCKING/超时)；forward 层所有 rank hc_attn_pre 报 aclnnMhcPreV2 缺失——torch_npu inner_precise=1 调用 aclnnMhcPreV2 而本机 CANN 9.2 只有旧 aclnnMhcPre；绕行为仅启用 mhc.asc_hc_post、HcPre 走 Torch 回退

```text
8 卡前一条无 MHC 的成功训练使用的是 `HCCL_INTRA_ROCE_ENABLE=1`、端口 `27000-27063/27100-27163`，并且未设置 `ASCEND_LAUNCH_BLOCKING` 与额外的 120 秒 HCCL 超时。
```
