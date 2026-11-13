---
{
  "type": "Runbook",
  "title": "修复配方 · dsv41_fused_attn 两段式路径与合并 kernel 的跨核 event-8 同步点修复：set 恢复每 token 一次",
  "description": "dsv41_fused_attn 的两段式路径（STAGE_QKS/STAGE_PVEPI）与试验性合并单 kernel（STAGE_FUSED）共用代码形态下，跨核同步点的位置是回归敏感点。修复：把 set_cross_core(pipe=V, event_id=8) 恢复到 token 循环内（每 token 一次）并写入注释说明死锁机理；STAGE_FUSED 保留自己独立的同步副本，不与两段式路径共享 wait。",
  "tags": [
    "task.debugging",
    "topic.attention"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "950"
  ]
}
---
# 修复配方 · dsv41_fused_attn 两段式路径与合并 kernel 的跨核 event-8 同步点修复：set 恢复每 token 一次

## 适用场景

pypto_pro（Ascend A5 pl.jit）多核 kernel 开发：同一仓库中存在「两段式生产路径 + 试验性合并单 kernel 路径」共用代码的形态，典型如 dsv41_fused_attn 的 STAGE_QKS/STAGE_PVEPI 与 STAGE_FUSED。


## 触发与观测
触发：为 STAGE_FUSED 合并而做的重构落地后，即使 `USE_FUSED_PREFILL=False`，`test_device_vllm_prefill_block_split_is_bitwise_equal[2/4]`、`test_device_pvepi_block_split_is_bitwise_equal[2]` 等两组用例 aicore timeout 挂死（T≥2），另有 18 个用例失败；单跑 prefill_matches_reference / pvepi_matches_host_pack / kv_decode_block_split 能过。

## 探针与操作

### 复现路径约定

以下路径已脱敏。历史命令中的变量占位符需由复现者按实际环境替换；Python/JSON 字符串内的占位符不会自动展开。

- `${SCRATCH_DIR}`：由复现者创建的本次实验临时目录。

1) 反证「合并路径独立」假设：USE_FUSED_PREFILL 已改回 False 仍挂 → 合并重构改动了 STAGE_QKS/STAGE_PVEPI 共享代码。2) 对比 ${SCRATCH_DIR}/before_dir（最后一次全绿副本）与当前文件的 `event_id=8` 出现位置（grep 行号位移）；3) 逐行 cat -A 核对 token 循环内的 wait/set 缩进层级，确认 Vector 段的 set 被 hoist 到循环外。

## 机制与判别
修复单元注释说明死锁机理与恢复位置。判别要点：新增跨核同步（event 2/3/4/9）只在 STAGE_FUSED 内使用不构成两段式风险。修复原则：独立路径恢复原位（每 token 一次），合并 kernel 保留自己的同步副本，两条路径不共享 wait。

### 补充机制片段
```
                # Reverse release for the score ring, **per token**: the Cube
                # section waits event 8 once after each token's chunks, so the
                # Vector section must raise it once per token too.  A single
                # release after the whole loop leaves the AIC blocked on token
                # 2 while token 1's Vector work waits for Cube -- an aicore
                # timeout.  STAGE_FUSED has its own kernel and its own copy of
                # this handover, so this standalone QKS path is unaffected by
                # the merged entry.
                pl.system.set_cross_core(pipe=pl.PipeType.V, event_id=8)
```

## 验证信号
修复 edit 本体（，tool_result，含死锁机理注释）。

### 结论与证据边界

  修复：把 set_cross_core(pipe=V, event_id=8) 恢复到 token 循环内（每 token 一次）并写入注释说明死锁机理；STAGE_FUSED 保留自己独立的同步副本（独立 kernel 内的 event 2/3/4/9），不与两段式路径共享 wait。

## 适用与失效边界
适用：pl.jit 多核（AIC+AIV）环形槽位同步的任何重构审查。失效/边界：(a) 本轨迹为紧急止血会话，任务要求的全量 44 测试套件复跑在轨迹内未完成（trace 截断于事件 103），全量复跑结果未在轨迹内捕获；(b) 修复仅隔离/恢复同步点，不尝试修好合并路径本身（绿优先于保留新功能）；(c) 事件计数协议要求「双方无条件推进计数」（即使某 AIV 无真实 head），审查时需同时检查这一条。
