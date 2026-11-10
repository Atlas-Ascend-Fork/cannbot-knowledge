---
{
  "type": "Runbook",
  "title": "共享宿主上跨时段性能比较假象的判别与同会话交替 A/B 计时法",
  "description": "基线（11:50）与改造后（14:22）分属不同宿主负载时段的两次单跑绝对耗时直接相减，会产生虚假收益（本例 paged prefill 168.52 ms、−17%，不可复现）。判别法：负载下同时段复测 eager 与 paged 单跑均显著变慢（226.64 / 231.75 ms）；再用同一进程只构建一次模型、交替（并轮换先后顺序）测量 eager/paged，以比值为准——两轮同会话（12+20 reps、合并 32 样本）prefill 比值 1.000、decode 0.992，性能中性结论可复现。",
  "tags": [
    "task.debugging",
    "topic.model_serving",
    "topic.attention"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-03T12:00:00Z",
  "platforms": [
    "950"
  ]
}
---

# 共享宿主上跨时段性能比较假象的判别与同会话交替 A/B 计时法

## 适用场景

- 场景：共享宿主（本例 96 核 CPU、多人多组重载作业并存）上做 NPU 推理性能对比（改造前后、两版实现 A/B）。
- 模型/平台：HYV4 L=4（6.039B）随机权重独立部署，Ascend950PR_9589 单卡，CANN 9.1.0，torch_npu 2.12.0；对比对象为阶段 0 eager（concat 动态 KV）与阶段 2 Paged MLA + FA v2 absorb。
- 工作负载：prompt 13 token、batch=1、8 步 decode（prefill 单次 + decode 单步计时）。
- 缺失信息说明：仅单卡、单请求、超小上下文；绝对耗时本身随宿主负载漂移，本卡结论只针对「如何获得可复现的相对结论」。

## 触发与观测

- 触发：`stage2_paged_metadata.json` 记录 paged prefill **168.52 ms**（相对 11:50 采集的基线 202.40 ms 呈 −17%），来自不同进程、不同时段的两次单跑（基线 11:50、paged 14:22）。
- 观测（事件 75/83，14:4x–14:5x 宿主重载时段复测）：
  - paged 单跑：prefill **231.75 ms**、decode 65.27–69.18 ms（token 与实施记录逐位一致，代码未变）；
  - eager 单跑（`HYV4_USE_PAGED_FA=0`）：prefill **226.64 ms**、decode 首步 63.87 ms 后回落 50.78–51.35 ms（token 逐位复现阶段 0 基线）。
  - 共享宿主上跨时段采集的绝对耗时不可比较：stage2 记录的 paged prefill 168.52 ms（相对 11:50 基线呈 −17%）在 14:4x 负载时段复测为 231.75 ms，同时段 eager 单跑 prefill 226.64 ms 也远高于其 11:50 记录的 202.40 ms——两者同步变慢证明漂移来自宿主负载而非代码。

## 探针与操作

同会话交替 A/B 计时法（`tools/review_ab_timing.py`）要点：

1. **同一进程内只构建一次模型**（seed=1234，固定权重），eager 与 paged 共用同一模型实例，各自持有独立 cache；
2. 每次计时前后 `torch.npu.synchronize()`；
3. **交替执行并轮换先后顺序**，消除次序/首测偏差（事件 106 原文）：

```python
    # interleave with alternating order to cancel any order/first-mover bias
    e_pre, p_pre = [], []
    for _ in range(2):
        eager_prefill(); paged_prefill()
    torch.npu.synchronize()

    def time_one(fn):
        torch.npu.synchronize(); t0 = time.time(); fn(); torch.npu.synchronize()
        return (time.time() - t0) * 1000.0

    for i in range(args.reps):
        if i % 2 == 0:
            e_pre.append(time_one(eager_prefill)); p_pre.append(time_one(paged_prefill))
        else:
            p_pre.append(time_one(paged_prefill)); e_pre.append(time_one(eager_prefill))
```

4. decode 用 teacher-forced 喂 CPU golden 轨迹（两条路径同 token），每步 q_len=1 计时；
5. 多轮（12/20 reps）+ 跨会话重复 + `tools/summarize_same_session_ab.py` 合并样本，报告中位数、min/max 与 **paged/eager 比值**；运行前后记录 `/proc/loadavg` 作为负载旁证。

失败路线（不可采用）：用两次不同时段的 `infer.sh` 单跑耗时直接相减得出「收益」——168.52 ms / −17% 即此产物。

## 机制与判别

- 机制：宿主 CPU/内存带宽争抢会同步抬升两个被测实现的绝对耗时（模型构建 165–171 s、小算子 launch 均受影响）；同进程交替测量让负载漂移在时间轴上对两组样本近似均摊，比值（paged/eager）对宿主负载不敏感，绝对中位数仍然漂移。
- 判别分支：
  - 「记录收益是真实的」 vs 「测量假象」：若收益真实，负载时段 eager 复测应≈其历史记录（202.40 ms）而 paged 显著更慢/快；实测 eager 复测 226.64 ms（比自身记录高 ~12%）且 paged 复测 231.75 ms（比记录高 ~38%）——两者同步抬高，判为宿主负载假象。
  - 「偶发噪声」 vs 「稳定结论」：交替 A/B 两轮独立会话的比值方向一致（prefill 0.9976/1.0066、decode 0.9909/0.9929），且合并 32 样本后 prefill 比值 1.0、decode 0.9923——判为性能中性，非单次波动。
- 判别探针：同一进程内只构建一次模型（seed=1234），交替测量 eager/paged 的 prefill 与 decode，并交替先后顺序消除次序偏差，以 paged/eager 比值为准；两轮同会话（12+20 reps、合并 32 样本）得到 prefill 比值 1.000（215.087 / 215.091 ms）、decode 比值 0.992（52.142 / 52.549 ms），当前规模（prompt 13 token、KV ≤ 23）paged 与 eager 性能中性。

## 验证信号

- 事件 75/83：负载时段 paged/eager 单跑复测（token 逐位复现证明代码未变，耗时却整体抬高——假象证据）。
- 事件 99/103：同进程交替 A/B 第 1 轮（10 reps）：prefill 比值 1.0058、decode 比值 0.9259（宿主高噪声）。
- 事件 114/117：第 2 轮（12 reps，轮换顺序）：prefill 比值 1.0126、decode 比值 1.0359。
- 事件 73/81（宿主空闲窗口 loadavg ~5.9–12.4）：同会话两轮——12 reps prefill 比值 0.9976 / decode 0.9909；20 reps prefill 比值 1.0066 / decode 0.9929。
- 事件 88：合并 32 样本：prefill eager 中位数 215.091 ms / paged 215.087 ms / 比值 1.0；decode eager 52.549 ms / paged 52.142 ms / 比值 0.9923。
- 事件 94/102：`stage2_paged_metadata.json` 重写为同会话口径（`prefill_ms_paged 215.087 / ratio 1.0`、`decode_avg_ms_paged 52.142 / ratio 0.9923`），`_notes` 声明 168.52 ms 已删除及原因。该判别可复现：两轮独立同会话 A/B 的 prefill 比值分别为 0.9976 与 1.0066、decode 比值分别为 0.9909 与 0.9929，方向一致（中性）；据此 stage2_paged_metadata.json 的 168.52 ms / −17% 结论被撤销并改记同会话比值口径。
- 证据等级：单机单卡；单跑绝对值为高方差观测；比值为两轮独立会话 + 一轮 reviewer 轮换顺序会话共 3 次一致；NPU 端计时含 Python 侧 `time.time` + `torch.npu.synchronize`。

## 适用与失效边界

- 适用：任何共享宿主上的 A/B 性能判别，尤其是「改造前后」跨小时/跨进程的场景；比值口径可直接写进 baseline metadata。
- 失效/风险：
  - 绝对中位数仍随宿主漂移（215 ms 在重载时段会变为 226–242 ms），跨环境迁移绝对值无意义；
  - 若两个实现互斥资源（同一 NPU 上串行预热）或计时窗口内负载突变，交替仍可能偏置，需多轮 + 轮换顺序 + 独立会话重复；
  - 该方法判别的是「相对比值」，不能替代大 batch/长序列下的真实负载收益评估；
  - 本例当前规模性能中性不代表 Paged MLA 无长期价值——收益预期在长序列（消 O(T) concat/展开）与图模式静态 shape（分析结论，未在长序列上实测）；
  - 计时含 host 侧 launch 开销，对超小 kernel 主导的负载，比值解释需谨慎（decode ±4–8% 波动即属此情形）。
