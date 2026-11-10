---
{
  "type": "Runbook",
  "title": "decode 时延瓶颈判别：单因子 bf16 实验证伪“计算受限”假瓶颈（真因为任务碎片固定开销）",
  "description": "Ascend950PR_9589 上 pangu_2_6B fp32 bs=1 decode 的 P1 剖析显示 matmul 占设备时间 88.9%，看似计算受限；但单因子全模型 bf16 实验后 TPOT 持平（29.797 vs 29.433ms，恶化 1.2% 噪声带内），证伪 C4 假设。真因是每步约 711 个算子任务 × ~40µs 固定开销（C6 碎片化），并由 QKV 融合减任务数实测 TPOT -6.6% 正向佐证。给出阈值化判别手册与单因子探针流程。",
  "tags": [
    "task.debugging",
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

# decode 时延瓶颈判别：单因子 bf16 实验证伪“计算受限”假瓶颈（真因为任务碎片固定开销）

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

结论（触发判）：在 pangu_2_6B fp32 bs=1 decode 的 P1 剖析中，matmul 类合计占设备时间 88.9%（aclnnAddmm_MatMulV3Common_MatMulV3 1152 次/47.12ms 居设备侧 Top-1），而端到端 TPOT 中位数 29.433ms 远高于设备每步有效执行时间——单看 matmul 占比会把瓶颈误判为计算受限（C4）。

## 探针与操作

判别实验 = 单因子 dtype 切换（其余一切不变，含 warmup/轮数/负载）：

第一步：跑诊断脚本确认信号（阈值表见下方 RUNBOOK 逐字引用）。

第二步：全模型 fp32→bf16 探针，先过 L0 精度门禁（事件 771 命令），再跑 P0 性能复检（事件 776 命令，逐字）：

```
. ${WORK_ROOT}/mia/scripts/setup_env.sh && cd ${WORK_ROOT} && venv/bin/python mia/scripts/bench.py task-workspace/models/pangu_2_6B npu npu-c1b-bf16 --prompt-id s03 --rounds 10 --warmup 3 --dtype bf16 --note "candidate C1b" 2>&1 | grep -vE "Warning|warn|GenerationMixin|owner|👉|auto class|related|trust_remote_code|jieba|prefix|Loading" | tail -24
```

第三步：判读——TPOT 显著下降 → C4 实锤，保留精度转换路线；TPOT 持平（噪声带内）→ C4 证伪，主因转向 C6（任务数 × 固定开销），改走减任务数路线（融合/图模式）。

第四步：用“减任务数”候选做正向验证（QKV 融合，见 [GPT-2 系模型 QKV 三投影融合单 GEMM（保留 custom_query 末层）的 decode 加速](gpt_qkv_gemm_custom_query_decode.md)）。

诊断手册阈值（diagnose.py 内置 RUNBOOK，事件 275 原文逐字）：

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

- 分支 A（C4 计算受限 / C2 带宽受限）：bf16 使权重流量减半、bf16 有效算力更高 → TPOT 应显著下降。
- 分支 B（C6 任务碎片固定开销）：每步约 711 个算子任务 × ~40µs 固定开销 ≈ 28ms 主导 → dtype 不改变任务数，TPOT 应持平。

实测落入分支 B（事件 778：TPOT 中位 29.797ms、TTFT 中位 31.13ms、峰值 4.973GB；对照事件 675：TPOT 29.433ms、峰值 9.994GB）。

结论（探针判）：单因子 bf16 探针证伪计算受限假设：全模型 bf16 后 TPOT 中位数 29.797ms vs fp32 基线 29.433ms（恶化 1.2%，噪声带内不计收益），时延不随权重流量与算力精度变化。

谱系记录（事件 781 命令原文逐字，C1b 记 rejected 并留因，同时登记 C2 融合候选及其 CostModel 上界）：

```
cd ${WORK_ROOT} && venv/bin/python mia/scripts/candidates.py task-workspace/models/pangu_2_6B set --id C1b-full-bf16 --status rejected --precision "L0 8/8 PASS cos>=0.999993 (profile/precision_l0/L0_report_bf16.json)" --perf "tpot 29.80ms vs C0 29.43ms (-1.2%, 噪声带内不计收益); peak_mem 9.99→4.97GB (-50%)" --reason "时延目标未达: fp32 decode 已贴权重流带宽地板, bf16 减半权重流不再受益; 每步 711 算子×~40us 固定开销主导 → 真因 C6 非 C4; 显存收益真实, 留作显存受限场景选项" && venv/bin/python mia/scripts/candidates.py task-workspace/models/pangu_2_6B add --id C2-qkv-fuse --parent C0-pure-device-move --domain S3 --change "QKV 三投影融合: [3x2560,2560] 单 GEMM 替代 3xaddmm (每步 192→160 个 GEMM 任务)" --status proposed --reason "诊断 run1: op_count/step=711, C6 碎片化为主因; S3 减少任务数; CostModel: 每任务固定开销~40us×32层×2次削减≈13% TPOT 上界"
```

正向佐证：QKV 融合把每步 GEMM 任务从 192 减到 160，TPOT 实测 27.477ms（-6.6%，事件 820），与“减任务数”模型方向一致（边际约 31µs/任务）。

结论（判别判）：真因判定为任务碎片固定开销（C6）：谱系将 C1b 记为 rejected 并留因（每步 711 算子×~40us 固定开销主导 → 真因 C6 非 C4）；随后 QKV 融合减少每步任务数实测 TPOT -6.6%（27.477ms），与该归因方向一致。

未验证推断（诚实标注）：~40µs/任务的固定开销是谱系推断值（由 bf16 无效与融合收益两次实验反推），未做逐任务延迟分解实测；“fp32 decode 已贴权重流带宽地板”是解释性表述，未实测带宽利用率（无 P2 级带宽数据）。

## 验证信号

- 平台 Ascend950PR_9589 / CANN 9.1.0 + 950-ops / torch_npu 2.12.0.post2；证据等级：同会话单卡、P0 协议（warmup 3 + 10 轮）中位数，单次会话观测。
- 触发信号：事件 761（设备 Top 算子表）、768（matmul_share=0.889）、675（TPOT 中位 29.433ms）。
- 探针信号：事件 772（bf16 L0 8/8 PASS，cos 0.999993–0.999996）、778（TPOT 中位 29.797ms、峰值 4.973GB）。
- 判别信号：事件 782（rejected 落盘确认）、820（QKV 融合 TPOT 27.477ms，-6.6%）。

## 适用与失效边界

- 适用：eager、bs=1/小 batch decode、任务数多（>500/步）且设备利用率低（设备时间远小于 TPOT）的 NPU 推理场景。
- 失效/不适用：prefill 或大批量（算力/带宽真正主导）时 bf16 仍可能有效——本轨迹未测；固定开销数值随 CANN/驱动/调度器版本漂移，跨版本须重跑判别实验；多卡/通信受限场景另需 C1 判别（host_dev_ratio 等）。
- 停止/回退规则：若 bf16 探针显示 TPOT 显著下降（超噪声带），则 C4 成立，应保留精度转换路线并撤销“碎片开销主导”结论。
- 单因子纪律：判别结论只在“除 dtype 外一切不变”时成立；若同时改了融合/图模式等多个因子，结论不可归因。
