---
{
  "type": "Runbook",
  "title": "全模型 bf16 转换不改善 bs=1 decode 时延（显存减半成立）",
  "description": "pangu_2_6B fp32 迁移 Ascend950PR_9589 后的常规第一候选（全模型 .to(bf16) 含 KV cache）被实验证伪时延收益：L0 精度门禁 8/8 PASS（cos≥0.999993），但 TPOT 中位 29.797ms vs fp32 基线 29.433ms（恶化 1.2%，噪声带内不计收益）；显存峰值 9.99→4.97GB（-50%）真实。失败条件明确：任务碎片固定开销主导的 bs=1 eager decode。",
  "tags": [
    "task.debugging",
    "topic.precision",
    "topic.model_serving"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-06T09:40:40Z",
  "platforms": [
    "950"
  ]
}
---

# 全模型 bf16 转换不改善 bs=1 decode 时延（显存减半成立）

## 适用场景

- 迁移 NPU 后的常规“第一候选”：fp32 模型全量 .to(bf16)（含 KV cache dtype 联动），期待时延收益——本轨迹给出该预期在此场景下的否定性结果。
- 本例：imone/pangu_2_6B（2.73B，fp32，eager GPT-2 式 attention），Ascend950PR_9589 单卡（aclnn-only），CANN 9.1.0 + 950-ops，torch_npu 2.12.0.post2。
- 负载：bs=1、prompt 17 token、greedy 生成 16 token 的 decode；TP=1、eager、无并发。
- 定位：时延维度的否定性结果（已按门禁记 rejected-for-latency）+ 显存维度的正面结果；不伪称成功。

路径补充：`${WORK_ROOT}` 为本地推理迁移/性能实验工作根，包含文中 mia、venv 与 task-workspace 相对目录。按本地环境设置变量，保留文中的相对路径关系。

## 触发与观测

（尝试）按 PDP 流程把 C1b 全模型 bf16 作为 S4 域候选执行：先过 L0 精度门禁（事件 771），再跑 P0 性能复检（事件 776）。

（精度观测）L0 门禁 8/8 PASS：logit 余弦 0.999993–0.999996（≥0.999 容差），mae 约 0.1（fp32 时约 3e-5），吐字全部可读（事件 772）。

（时延失败）TPOT 中位 29.797ms vs fp32 基线 29.433ms（恶化 1.2%，噪声带内不计收益）；TTFT 中位 31.13ms vs 28.255ms；吞吐 33.56 vs 33.98 tok/s（事件 778）。

（显存结果）峰值 9.994GB → 4.973GB（-50%，事件 778）。

## 探针与操作

性能复检命令（单因子入口 --dtype bf16，事件 776 原文逐字）：

```
. ${WORK_ROOT}/mia/scripts/setup_env.sh && cd ${WORK_ROOT} && venv/bin/python mia/scripts/bench.py task-workspace/models/pangu_2_6B npu npu-c1b-bf16 --prompt-id s03 --rounds 10 --warmup 3 --dtype bf16 --note "candidate C1b" 2>&1 | grep -vE "Warning|warn|GenerationMixin|owner|👉|auto class|related|trust_remote_code|jieba|prefix|Loading" | tail -24
```

谱系记录（事件 781 命令原文逐字，rejected 留因 + 后续候选登记）：

```
cd ${WORK_ROOT} && venv/bin/python mia/scripts/candidates.py task-workspace/models/pangu_2_6B set --id C1b-full-bf16 --status rejected --precision "L0 8/8 PASS cos>=0.999993 (profile/precision_l0/L0_report_bf16.json)" --perf "tpot 29.80ms vs C0 29.43ms (-1.2%, 噪声带内不计收益); peak_mem 9.99→4.97GB (-50%)" --reason "时延目标未达: fp32 decode 已贴权重流带宽地板, bf16 减半权重流不再受益; 每步 711 算子×~40us 固定开销主导 → 真因 C6 非 C4; 显存收益真实, 留作显存受限场景选项" && venv/bin/python mia/scripts/candidates.py task-workspace/models/pangu_2_6B add --id C2-qkv-fuse --parent C0-pure-device-move --domain S3 --change "QKV 三投影融合: [3x2560,2560] 单 GEMM 替代 3xaddmm (每步 192→160 个 GEMM 任务)" --status proposed --reason "诊断 run1: op_count/step=711, C6 碎片化为主因; S3 减少任务数; CostModel: 每任务固定开销~40us×32层×2次削减≈13% TPOT 上界"
```

## 机制与判别

- 为什么无时延收益（轨迹内推断，方向被后续融合实验佐证）：bs=1 decode 的时延地板 = 每步约 711 个算子任务 × ~40µs 固定开销 ≈ 28ms；bf16 只减半权重流量、不减任务数，故 TPOT 不动（判别实验详见 [decode 时延瓶颈判别：单因子 bf16 实验证伪“计算受限”假瓶颈（真因为任务碎片固定开销）](../performance/decode_bf16.md)）。
- 精度代价真实但可控：cos 从 1.000000 降到 0.999993–0.999996，mae 从 ~3e-5 升到 ~0.1；eager attention 的 -1e4 masked_bias dtype 转换路径是 bf16 化的首要排查点（本例未触发 FAIL）。
- 与 C1a（autocast 仅包 matmul）的关系：C1b 已证伪时延收益，C1a 依赖同判别逻辑，降优先级未执行（谱系留 proposed 未竟）。

结论（否定判）：全模型 fp32→bf16 权重转换（含 KV cache）在 pangu_2_6B bs=1 decode 不改善时延：TPOT 中位 29.797ms vs fp32 基线 29.433ms（恶化 1.2%，噪声带内不计收益），按门禁记为 rejected。

结论（显存判）：bf16 的显存收益真实：峰值显存 9.994GB→4.973GB（-50%），且精度门禁 8/8 PASS（logit 余弦 0.999993–0.999996 ≥ 0.999）。

结论（边界判）：该否定性结论的边界：仅覆盖 bs=1 decode 的固定开销主导区，prefill/大批量算力或带宽主导场景未测；谱系将 bf16 留作显存受限场景选项。

## 验证信号

- 事件 772：bf16 L0 门禁 8/8 PASS（cos 0.999993–0.999996，readable=1.00，exit=0）。
- 事件 778：P0 复检（TPOT 中位 29.797ms、TTFT 中位 31.13ms、吞吐 33.56 tok/s、峰值 4.973GB；10 轮 + warmup 3）。
- 事件 782：rejected 落盘确认（"ok, 3 candidates"）。
- 对照基线：事件 675（fp32 npu-c0-fp32：TPOT 中位 29.433ms、峰值 9.994GB；同会话同口径）。
- 平台 Ascend950PR_9589 / CANN 9.1.0 + 950-ops；单会话单卡、10 轮中位数（单次会话观测）。

## 适用与失效边界

- 明确失败条件：bs=1、eager、任务碎片固定开销主导（每步任务数 >500 且设备利用率低）的 decode 场景，bf16 转换不给时延收益。
- 仍值得采用的条件：显存受限（峰值 -50%）、或算力/带宽主导的负载（prefill、大 batch——本轨迹未测，不外推）、或配合图模式后固定开销不再是地板时（未验证，属假设）。
- 版本敏感：固定开销与 aclnn 调度随 CANN/驱动漂移，跨版本须重跑“C4/C6 判别实验”再决定。
- 回退路径：保留 fp32（本轨迹 promoted 链 = fp32 + qkv-fuse）；若为显存采用 bf16，须过 L0 门禁并关注 masked_bias 路径的 mae 变化。
