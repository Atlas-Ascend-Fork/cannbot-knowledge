---
{
  "type": "Runbook",
  "title": "VGGT 序列并行（Ulysses/Ring）在 A3+CANN 9.2.0 warmup 即被 aclnnFusedInferAttentionScoreV3 561103 阻断：换 die、清 alloc/task-queue 环境变量、sp4 均复现，单卡同算子正常",
  "description": "模型/框架：cann-recipes-embodied-ai `3d_vision/vggt` VGGT-1B 序列并行推理（sp2.yaml：Ulysses degree=2；sp4.yaml：Ulysses 2×Ring 2），`bash infer_test.sh spN.yaml`（torchrun）。",
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

# VGGT 序列并行（Ulysses/Ring）在 A3+CANN 9.2.0 warmup 即被 aclnnFusedInferAttentionScoreV3 561103 阻断：换 die、清 alloc/task-queue 环境变量、sp4 均复现，单卡同算子正常

## 适用场景

- 平台范围依据：source 0 seq 1、source 0 seq 264的实际环境/设备记录确认本次为Atlas A3；这里不扩展未记录的产品或版本。

- 模型/框架：cann-recipes-embodied-ai `3d_vision/vggt` VGGT-1B 序列并行推理（sp2.yaml：Ulysses degree=2；sp4.yaml：Ulysses 2×Ring 2），`bash infer_test.sh spN.yaml`（torchrun）。
- 对象：SP 路径 `vggt/sp/unified_sp_attention.py` 的 `npu_fused_infer_attention_score`（aclnnFusedInferAttentionScoreV3）调用。
- 平台/版本：Atlas A3（Ascend 910_9382），CANN 9.2.0，torch_npu 2.7.1.post2，25 图输入（[1,25,3,350,518]）。

## 触发与观测

- 触发：`bash infer_test.sh sp2.yaml`（ASCEND_RT_VISIBLE_DEVICES=0,1）模型加载成功、进入 Global Attention warmup 后双 rank 同时崩溃（sp2_RC=1，49s）（source 0 seq 258/264）。
- 原始报错（逐字，source 0 seq 269）：

```text
NPU function error: call aclnnFusedInferAttentionScoreV3 failed, error code is 561103
[ERROR] 2026-11-08-19:48:44 (PID:807428, Device:0, RankID:0) ERR00100 PTA call acl api failed.
[PID: 807428] 2026-11-08-19:48:41.917.465 Invalid_Argument(EH0012): aclrtAllocatorGetByStream failed. Parameter stream is invalid. Reason: The stream is not registered with any allocator.
TraceBack (most recent call last):
        Failed to execute operator aclnnFusedInferAttentionScoreV3_796_FusedInferAttentionScore. Reason: The dtype or format of the actual input or output parameter of the operator is inconsistent with that defined in the operator prototype Op Def.
        Cannot find binary for op FusedInferAttentionScore.
        Kernel GetWorkspace failed. opType: 35
        FusedInferAttentionScore LaunchAicore failed.
```

- rank1 异步栈落在 `_all_to_all_seq_to_head` 的 `torch.npu.synchronize()`，真实失败算子为 aclnnFusedInferAttentionScoreV3（source 0 seq 264）。

## 探针与操作

同根因三次判别尝试（全部同错）：

1. **换 die 组排除硬件**：ASCEND_RT_VISIBLE_DEVICES=0,2（避开 Alarm 态 die 1）→ 双 rank 同错 561103 "Cannot find binary"（source 0 seq 275）。
2. **清启动环境变量**：`PYTORCH_NPU_ALLOC_CONF=""`、`TASK_QUEUE_ENABLE=0`（vggt_launch/mm 默认设 expandable_segments:True / task-queue 2）→ 同错，报错入口 `npu_fused_infer_attention_score_symint`（source 0 seq 281）。
3. **sp4（Ulysses 2×Ring 2，dies 0,2,4,5）** → 双 rank 同错 561103（source 0 seq 302）。

对照（判别方向）：单卡路径同一算子调用正常（source 0 seq 296，grep 输出保留原行号）：

```text
269-        # Call NPU fused attention
270:        out = torch_npu.npu_fused_infer_attention_score(
271-            q, k, v,
272-            num_heads=num_heads,
273-            scale=float(scale),
274-            input_layout="BNSD",
275-            num_key_value_heads=num_key_value_heads,
276-            pre_tokens=65535,
277-            next_tokens=65535 if not params.causal else 0,
278-            sparse_mode=0,
279-            inner_precise=0,
280-        )[0]
```

## 机制与判别

- 机制判别链：die 无关（0,1 与 0,2 同错）→ alloc conf / task queue 无关（清空后同错）→ 与 SP 度数/组合无关（sp2/sp4 同错）；单卡同算子正常 → 失败绑定 **SP all-to-all 分片后的张量形状/格式组合**（每 rank num_heads 减半、shard_s 序列分片）在该 SoC+CANN 组合下无匹配 binary（"dtype or format ... inconsistent with op prototype / Cannot find binary"）。
- SP 路径与单卡路径的 FIA 参数面（BNSD、sparse_mode 0、pre/next 65535、inner_precise 0）一致，差异在分片后张量属性（source 0 seq 296 对照 + seq 305 归因叙述）。
- EH0012 "stream is not registered with any allocator" 与 561103 同时出现，但在清空 PYTORCH_NPU_ALLOC_CONF 后仍复现，判为伴随现象而非根因。
- 未在本环境内修复：4 次尝试后 F07 记为 blocked（环境阻断，算子二进制缺失/不支持该形状组合）。

## 验证信号

- tool_observed：sp2/sp2(dies02)/sp2(envdiag)/sp4 四次运行 RC=1 的日志逐字在案（seq 258/264/269/275/281/302），双 rank 错误码一致。
- tool_observed：单卡对照 FIA 调用源码（attention.py:270）逐字在案（seq 296）。
- agent_narrative：将根因收窄到"SP 分片后 shape/format 组合在该 SoC/CANN 无 binary"（seq 305），未做最小复现张量级验证。

## 适用与失效边界

- 适用于：VGGT（及同构 SP attention 实现）在 A3 910_9382 + CANN 9.2.0 + torch_npu 2.7.1.post2 上做多卡序列并行时的预期阻断形态与排查顺序（先换 die、再清 env、再对照单卡调用点），避免误判为硬件故障或 allocator 配置问题。
- 失效/边界：根因停留在"分片后形状组合无 binary"假说，未做独立最小张量复现；未测 ASCEND_LAUNCH_BLOCKING=1 精确栈；官方 sp2/sp4/sp8 加速数字（Ulysses=2 1.75× 等）为 A2 8 卡口径，在本环境不可达；升级 CANN/torch_npu 后需重测。

## 附：断言存档

- VGGT 序列并行（sp2/sp4，Ulysses/Ring）在 A3 910_9382 + CANN 9.2.0 + torch_npu 2.7.1.post2 上模型加载后 warmup 即双 rank 同崩：aclnnFusedInferAttentionScoreV3 error 561103，原因链「dtype or format 与算子原型不一致 / Cannot find binary for op FusedInferAttentionScore / Kernel GetWorkspace failed. opType: 35」

```text
NPU function error: call aclnnFusedInferAttentionScoreV3 failed, error code is 561103
[ERROR] 2026-11-08-19:48:44 (PID:807428, Device:0, RankID:0) ERR00100 PTA call acl api failed.
[PID: 807428] 2026-11-08-19:48:41.917.465 Invalid_Argument(EH0012): aclrtAllocatorGetByStream failed. Parameter stream is invalid. Reason: The stream is not registered with any allocator.
TraceBack (most recent call last):
        Failed to execute operator aclnnFusedInferAttentionScoreV3_796_FusedInferAttentionScore. Reason: The dtype or format of the actual input or output parameter of the operator is inconsistent with that defined in the operator prototype OpDef.
        Cannot find binary for op FusedInferAttentionScore.
        Kernel GetWorkspace failed. opType: 35
        FusedInferAttentionScore LaunchAicore failed.
```
