---
{
  "type": "Runbook",
  "title": "减 batch_size（64→32）不能缓解 DeepSeek-V3.2-Exp 16cp CI 样例的 warmup prefill OOM",
  "description": "对 16cp CI 样例的 warmup prefill MoE dispatch OOM（EL0004），按 OOM 缓解顺序先试减 batch_size（64→32，max_prefill_tokens 保持 65536）：16 rank 仍全部 Aborted（core dumped），bs32 运行日志含 1 条 OutOfMemoryError，OOM 位置不变。失效机制为 prefill wave 大小由 prefill_batch_size = max(1, max_prefill_tokens // seq_len) 计算而不依赖 batch_size（代码阅读推断）；同日改 max_prefill_tokens 65536→16384（batch_size 保持 64）一次通过，构成同环境 A/B 对照。",
  "tags": [
    "task.debugging",
    "topic.graph_execution",
    "topic.memory",
    "topic.speculative_decoding"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-06T09:40:40Z",
  "platforms": [
    "a3"
  ]
}
---

# 减 batch_size（64→32）不能缓解 DeepSeek-V3.2-Exp 16cp CI 样例的 warmup prefill OOM

## 适用场景

- 模型/框架：DeepSeek-V3.2-Exp（W4A8C8 量化权重），cann-recipes-infer 仓，`bash executor/scripts/infer.sh --model deepseek_v3_2_exp --yaml ci/<yaml>`。
- 平台/版本：Atlas A3（Ascend 910_9362），单机 16 die（8 物理卡，单 die 64GB HBM）；Docker 镜像 `cann9.0_pt2.8.0_dsv3.2_aarch_image:v0.1`（容器内 CANN 9.0.0、PyTorch 2.8.0+cpu、torch_npu）。
- 负载：CI 样例 `config/ci/deepseek_v3.2_exp_rank_16_16ep_16cp_w4a8c8_mtp3_minibatch4.yaml`（CP16+EP16+MTP3、input_truncated_len=16384、max_prefill_tokens=65536），InfiniteBench longbook_qa_eng。
- 数据来源：2026-10-17 单日单次 A/B（来源记录），背景 OOM 与修复对照见[DeepSeek-V3.2-Exp W4A8C8 16cp CI 样例 warmup prefill MoE dispatch OOM：max_prefill_tokens 65536→16384 修复](deepseek_v32_exp_w4a8c8_warmup.md)。

路径约定：`${RECIPES_ROOT}` 为cann-recipes-infer 源码根。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

该 CI 样例原样执行（batch_size=64、max_prefill_tokens=65536）在 warmup prefill 的 MoE dispatch（aclnnCat 算子）处稳定 OOM：设备侧 `Memory_Allocation_Failure(EL0004)`、`NPU out of memory. NPUWorkspaceAllocator tried to allocate 512.00 MiB(NPU 0; 61.27 GiB total capacity; 577.31 MiB free)`，16 rank 全部 core dumped。按 AGENTS.md 的 OOM 缓解顺序，第一优先尝试是"减 batch_size"——本卡记录该路线的客观失败。

## 探针与操作

1. 尝试（attempt，2026-10-17 事件 159 参数原文）：`sed 's/batch_size: 64/batch_size: 32/' models/deepseek_v3_2_exp/config/ci/deepseek_v3.2_exp_rank_16_16ep_16cp_w4a8c8_mtp3_minibatch4.yaml > models/deepseek_v3_2_exp/config/ci/tmp_oom_bs32.yaml`；副本参数确认（事件 160）：

```
  batch_size: 32
  max_prefill_tokens: 65536
```

2. 执行副本（事件 162：`docker exec ... bash executor/scripts/infer.sh --model deepseek_v3_2_exp --yaml ci/tmp_oom_bs32.yaml`）→ 16 rank 全部 Aborted（事件 163）：

```
${RECIPES_ROOT}/executor/scripts/function.sh: line 328: 109427 Aborted                 (core dumped) "${cmd[@]}" &> ${WORK_DIR}/${RES_PATH}/log_${LOCAL_RANK}.log
${RECIPES_ROOT}/executor/scripts/function.sh: line 328: 109431 Aborted                 (core dumped) "${cmd[@]}" &> ${WORK_DIR}/${RES_PATH}/log_${LOCAL_RANK}.log
```

3. 事后统计（事件 371/372，对当天各 res 目录 log_0.log 的 grep 计数）：

```
===bs32 timing===
2026-10-17 07:52:45
OOM: 1
```

即 bs32 运行日志中 `OutOfMemoryError` 计数为 1（与原样例 65536 运行相同），OOM 仍在同一 65536-token prefill wave 位置。
4. 同日对照（事件 166~170）：将 max_prefill_tokens 65536→16384（batch_size 保持 64）则一次通过（MTP3 等效 18.96 ms/token，全 rank 无 ERROR）——构成同环境 A/B，证明有效变量是 max_prefill_tokens 而非 batch_size。

## 机制与判别

- 结论 1：将 batch_size 由 64 减为 32（max_prefill_tokens 保持 65536 不变）后，warmup prefill 仍在同一 65536-token wave 处 OOM，16 rank 全部 Aborted（core dumped），bs32 运行日志中 OutOfMemoryError 计数为 1——减 batch_size 对该 OOM 无效，不可采用该缓解路线。
- 结论 2：失效机制（代码阅读推断，未见直接显存测量）：warmup prefill 的并发序列数按 prefill_batch_size = max(1, max_prefill_tokens // seq_len) 计算且不依赖 batch_size，减 batch_size 不改变 warmup prefill wave 的激活峰值；同日将 max_prefill_tokens 65536→16384（batch_size 保持 64）则一次通过。
- 判别依据（executor/core/engine/execution_engine.py，2026-10-14 事件 180/181 逐字）：

```
        if self.infer_config.parallel_config.cp_size > 1 and self.infer_config.scheduler_config.cp_mini_batch >= 1:
            prefill_batch_size = self.infer_config.scheduler_config.cp_mini_batch
        else:
            prefill_batch_size = self.infer_config.scheduler_config.batch_size_per_dp_rank
        decode_batch_size = self.infer_config.scheduler_config.batch_size_per_dp_rank
        seq_len = self.input_truncated_len

        max_prefill_tokens = self.infer_config.scheduler_config.max_prefill_tokens
        if max_prefill_tokens > 0:
            seq_len = min(seq_len, max_prefill_tokens)
            prefill_batch_size = max(1, max_prefill_tokens // seq_len)
            if (
                self.infer_config.parallel_config.cp_size > 1
                and self.infer_config.scheduler_config.cp_mini_batch >= 1
            ):
                prefill_batch_size = min(
                    prefill_batch_size,
                    self.infer_config.scheduler_config.cp_mini_batch,
                )

        return prefill_batch_size, decode_batch_size, seq_len
```

  该公式不含 batch_size；warmup prefill 的 wave 大小（激活显存峰值来源）由 max_prefill_tokens 决定。此为代码层推断，未做显存级测量。

## 验证信号

- 失败信号（客观）：事件 163（16 个 `Aborted (core dumped)`）、事件 372（bs32 日志 OutOfMemoryError 计数 1）；运行时段 07:52:45–07:58:44（约 6 分钟后崩溃）。
- 对照信号（客观）：同日同环境 max_prefill_tokens 16384 运行（事件 169/170）EXIT 通过、MTP3 等效 18.96 ms/token、1028 有效 token、accept rate 1.0000。
- 证据等级：单日单次 A/B（2026-10-17），bs32 路线仅执行 1 次；无成功信号，本卡如实记录失败，不伪称缓解有效。

## 适用与失效边界

- 边界：本结论限定于 OOM 位于 warmup/正式 prefill wave（由 max_prefill_tokens 决定并发序列数）的场景；若 OOM 发生在 decode 阶段（batch_size 主导激活），减 batch_size 可能有效——该情形未在本组来源观测验证。
- 单次实验，未见跨日重复；机制解释为代码阅读推断而非显存测量；若框架版本更新了 prefill 批大小计算逻辑（如引入 batch_size 上限或 cp_mini_batch 钳制），需重新评估。
- 停止条件：遇到 warmup prefill MoE dispatch OOM 时，可跳过"减 batch_size"直接下调 max_prefill_tokens；若下调后仍 OOM，再按 enable_prefill_multi_cycle → moe_chunk_max_len → kvp_size → 更高压缩量化的顺序继续。
