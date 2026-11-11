---
type: Optimization
title: 'F8: HSetFlag+MemoryT::L0B:mixed_entry_sequence:507014'
description: 用硬件 L0 一致性 flag（`HSetFlag/HWaitFlag<HardEvent::M_MTE1|MTE1_M, MemoryT::L0B, false>`）替换
tags:
- task.debugging
- topic.data_movement
- topic.programming_model
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/4917980395de8b8703aa7ec62213fafbe7bec01e/plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/runbooks/failure-patterns/f8-hflag-l0b-coherent-mixed-entry-hang.md
  role: evidence
created_at: '2026-10-30T13:45:00Z'
updated_at: '2026-10-30T13:45:00Z'
platforms:
- a2
- a3
---

# F8: HSetFlag+MemoryT::L0B:mixed_entry_sequence:507014

> 进化失败模式元数据（迁移自旧 OKF，机器可读副本见 ascendc-evolution-knowledge/references/okf_compat.json）：
> key: "HSetFlag+MemoryT::L0B:mixed_entry_sequence:507014"
> phenomenon: runtime_failure
> severity: blocking
> failed_combination: ["X62", "HSetFlag", "MemoryT::L0B"]
> operator_type: ["attention", "cv_fusion", "matmul"]
> occurrences: 2

## Symptom
用硬件 L0 一致性 flag（`HSetFlag/HWaitFlag<HardEvent::M_MTE1|MTE1_M, MemoryT::L0B, false>`）替换
L0 ping-pong 的虚拟 `SetFlag/WaitFlag` 后：孤立 60-iter probe 全 clean（case32 30/30、case26 60/60，
数值与基线逐位一致），但 canonical 混合入口序列（同一进程先跑参考模型，再按 case 0(pair)→16(quad)→
33(quad)→49(pair) 顺序）稳定挂死：约 5–15 min 后 `507014 AclrtSynchronizeDeviceWithTimeout`
（aicore task timeout，非 507015）。

## 触发条件
- 910B2C + CANN 9.1.0，cube 内核自管 L0 ping-pong（本项目 gemm_v0）
- 仅在「批量/混合入口序列 + 先跑参考模型」时出现；单 case 孤立重复不现
- rung 分配无关：全量 H 与仅 quad rung H 都挂

## Root cause class
跨 launch / 设备域的硬件 flag 缺陷（不是 L0 数据 hazard）：flag 在孤立重复下正确退休，但在
混合 entry 序列/长期连续 launch 下不退休或错误配对，导致 aicore 卡死。

## Resolution
- 不要用 H flag 作为竞态修复；回退 X62 `PipeBarrier<PIPE_ALL>()`（唯一实测安全兜底）
- 用 X63（跨调用槽位续接 + 隔步 drain）与 PV/K 步合并回收屏障代价（48_GqaSparseFwd：697.64→641.41us）
- 验证协议：任何竞态修复必须跑 canonical 混合入口序列（不是只跑 probe），并至少 2 次独立复现

## Evidence
48_GqaSparseFwd 新版技能栈进化（2026-10-30）：r1_p1（device 1）首次发现，canonical 精度阶段 507014；
r2_p0（device 0）全量 H 与仅 quad H 均挂；r3_p0（device 0）第二次独立复现并确认数值正确。
