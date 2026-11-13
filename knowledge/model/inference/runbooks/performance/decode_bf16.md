---
{
  "type": "Runbook",
  "title": "小 batch decode 的 bf16 负结果与任务下发开销排查",
  "description": "Ascend950PR_9589 上 pangu_2_6B fp32 bs=1 decode 的 matmul 占设备时间 88.9%，全模型 bf16 后 TPOT 为 29.797ms，fp32 基线为 29.433ms，未观察到时延收益；显存峰值约减半。后续 QKV 融合观测到 TPOT 下降 6.6%，支持继续排查任务下发与执行粒度，但两项实验不能证明固定开销是唯一瓶颈。",
  "tags": [
    "task.debugging",
    "topic.model_serving"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "950"
  ]
}
---
# 小 batch decode 的 bf16 负结果与任务下发开销排查

## 适用场景

- 模型/框架：GPT-2 系 eager 实现（GPTPanguForCausalLM，2.73B，fp32，GPT-2 式 tril uint8 mask + torch.where + -1e4 masked_bias），PyTorch 2.12.0 + torch_npu 2.12.0.post2，transformers 4.46.3（直接构造加载）。
- 平台：Ascend950PR_9589 单卡（aclnn-only，HBM 实测 123.2GB），CANN 9.1.0 + 用户级 Ascend-cann-950-ops 9.1.0，驱动 7.0.t9.0.B887。
- 工作负载：bs=1、prompt 17 token、greedy 生成 16 token 的 decode；eager 模式、无并行。
- 目标：当剖析显示“matmul 占设备时间绝大头”时，判别真瓶颈是算力/带宽（C4/C2）还是小任务碎片固定开销（C6），避免在错误方向上做精度转换优化。

路径补充：`${WORK_ROOT}` 为本地推理迁移/性能实验工作根，包含文中 mia、venv 与 task-workspace 相对目录。按本地环境设置变量，保留文中的相对路径关系。

## 触发与观测

- P1 剖析（torch_npu profiler + kernel_details.csv 解析）设备侧 Top-1 算子：`aclnnAddmm_MatMulV3Common_MatMulV3` 1152 次 / 47.12ms（事件 761，工具结果原文）。Top-5 设备算子 6 个 decode 步合计约 53ms（约 8.8ms/步，由事件 761 数据求和可得）。
- 诊断脚本输出：top_matmul_share = 0.889、top_elementwise_share = 0.949、op_count = 4266（6 步，约 711/步）、host_dev_ratio = 0.0（事件 765/768）。
- 端到端 TPOT 中位数 29.433ms（事件 675）远高于设备每步有效执行时间——设备时间与端到端时延之间的缺口指向下发/固定开销。
- host 侧 trace 仅 cpu_op(25980)/dequeue(3504)/enqueue(3504) 三类 X 事件，无设备 kernel cat（事件 721）；enqueue 3504/6 步 = 584 任务/步，top 算子下发计数约 711/步，越过 C6 阈值（>500）。

结论（触发判）：在 pangu_2_6B fp32 bs=1 decode 的 P1 剖析中，matmul 类合计占设备时间 88.9%（aclnnAddmm_MatMulV3Common_MatMulV3 1152 次/47.12ms 居设备侧 Top-1），而端到端 TPOT 中位数 29.433ms 远高于设备每步有效执行时间——单看 matmul 占比不足以确认计算受限。

## 探针与操作

判别实验 = 单因子 dtype 切换（其余一切不变，含 warmup/轮数/负载）：

第一步：跑诊断脚本确认信号（阈值表见下方 RUNBOOK 逐字引用）。

第二步：全模型 fp32→bf16 探针，先过 L0 精度门禁（事件 771 命令），再跑 P0 性能复检（事件 776 命令，逐字）：

```
. ${WORK_ROOT}/mia/scripts/setup_env.sh && cd ${WORK_ROOT} && venv/bin/python mia/scripts/bench.py task-workspace/models/pangu_2_6B npu npu-c1b-bf16 --prompt-id s03 --rounds 10 --warmup 3 --dtype bf16 --note "candidate C1b" 2>&1 | grep -vE "Warning|warn|GenerationMixin|owner|👉|auto class|related|trust_remote_code|jieba|prefix|Loading" | tail -24
```

第三步：判读——TPOT 下降可支持在当前负载继续评估 bf16；没有收益则记录该路线的负结果，并检查 host 下发、同步、设备占用和 dtype 路径差异。dtype 切换同时影响算力、流量和算子实现，任何一个结果都不足以单独确认或排除某类瓶颈。

第四步：用“减任务数”候选做正向验证（QKV 融合，见 [GPT-2 系模型 QKV 三投影融合单 GEMM（保留 custom_query 末层）的 decode 加速](gpt_qkv_gemm_custom_query_decode.md)）。

来源诊断脚本的启发式阈值（不是实测定律或根因验收门限；下列代码保留来源形式，仅用于列出待检查方向）：

```
# 诊断手册（阈值=知识库 runbook 卡的机器可读投影；本种子库为最小内置集）
RUNBOOK = [
    {"cause": "C5 下发/同步开销", "signal": "host_dev_ratio",
     "cond": lambda s: s > 1.5, "threshold": ">1.5",
     "suggest_domains": ["S5 图模式", "S6 多流", "S3 融合(减少算子数)"]},
    {"cause": "C4 计算受限(fp32 算力利用率)", "signal": "top_matmul_share",
     "cond": lambda s: s > 0.5, "threshold": ">0.5 且 fp32 dtype",
     "suggest_domains": ["S4 量化/精度转换(bf16)", "S3 融合"]},
    {"cause": "C2 访存带宽受限", "signal": "top_elementwise_share",
     "cond": lambda s: s > 0.3, "threshold": ">0.3",
     "suggest_domains": ["S3 融合(减访存)", "S4 量化"]},
    {"cause": "C6 图执行低效(小算子碎片)", "signal": "op_count_per_step",
     "cond": lambda s: s > 500, "threshold": ">500",
     "suggest_domains": ["S5 图模式", "S2 缓存布局", "S3 融合"]},
]
```

## 机制与判别

可区分解释分支：

- 假设 A：降低精度减少当前关键路径的计算或访存时间，可能使 TPOT 下降；具体收益取决算子实现、利用率和其他开销。
- 假设 B：任务下发、同步或执行粒度限制了 dtype 转换收益。任务数较多与端到端/设备时间差提供排查线索，但没有逐任务延迟分解，不能把 TPOT 除以任务数当作已测固定开销。

实测 bf16 没有观察到时延收益（事件 778：TPOT 中位 29.797ms、TTFT 中位 31.13ms、峰值 4.973GB；对照事件 675：TPOT 29.433ms、峰值 9.994GB）。

结论（探针判）：本负载全模型 bf16 后 TPOT 中位数为 29.797ms，fp32 基线为 29.433ms（约 +1.2%，来源约定不计为可靠差异），没有取得时延收益；峰值显存由 9.994GB 降至 4.973GB。

后续 QKV 融合在相同负载下观测到 TPOT 27.477ms（较 fp32 基线下降约 6.6%）。31 层投影由每层 3 次变为 1 次，理论减少 62 次线性投影调用；实际设备 kernel 数和逐任务开销未重新统计。融合还会改变 GEMM 形状与存储行为，因此该结果支持评估执行粒度，不能单独证明收益全部来自固定 launch 开销。

来源曾提出约 40µs/任务的成本模型及权重带宽地板解释，两者均缺乏直接测量，本卡不将其采纳为已验证根因或性能上界。

## 验证信号

- 平台 Ascend950PR_9589 / CANN 9.1.0 + 950-ops / torch_npu 2.12.0.post2；证据等级：同会话单卡、P0 协议（warmup 3 + 10 轮）中位数，单次会话观测。
- 触发信号：事件 761（设备 Top 算子表）、768（matmul_share=0.889）、675（TPOT 中位 29.433ms）。
- 探针信号：事件 772（bf16 L0 8/8 PASS，cos 0.999993–0.999996）、778（TPOT 中位 29.797ms、峰值 4.973GB）。
- 判别信号：事件 782（rejected 落盘确认）、820（QKV 融合 TPOT 27.477ms，-6.6%）。

## 适用与失效边界

- 适用：eager、bs=1/小 batch decode、任务数多（>500/步）且设备利用率低（设备时间远小于 TPOT）的 NPU 推理场景。
- 失效/不适用：prefill 或大批量（算力/带宽真正主导）时 bf16 仍可能有效——本轨迹未测；固定开销数值随 CANN/驱动/调度器版本漂移，跨版本须重跑判别实验；多卡/通信受限场景另需 C1 判别（host_dev_ratio 等）。
- 停止/回退规则：若 bf16 探针显示可靠收益，在精度门禁通过后继续该路线；若没有收益，保留负结果并对其他候选做独立测量。不要由单项 dtype 实验直接决定根因。
- 单因子纪律：判别结论只在“除 dtype 外一切不变”时成立；若同时改了融合/图模式等多个因子，结论不可归因。
