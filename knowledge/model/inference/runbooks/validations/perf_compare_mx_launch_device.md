---
{
  "type": "Runbook",
  "title": "perf_compare_mx 按数量切组把首次 launch 的时长尖峰摊进均值，制造 8.5ms 级假异常",
  "description": "doc_mx 全 case 算子性能实测中 decode_m200_mirror/fused 报 8522µs/次（同 batch 的 M=56 仅 13.9µs，README 历史值 26.1µs），复跑 64239µs。查原始 op_summary 发现首次 launch 含 642ms 的首发时长尖峰而稳态 kernel 19-24µs——脚本『按数量切组丢预热』逻辑（per_forward = len(rows)//(repeat+1)）在该 case 行分布下切组错位，把一次性开销摊进均值，是测量脚本统计瑕疵而非算子慢。按『每次 forward 以 DynamicMxQuant 开头』边界切组 + 中位数重算得 24.0µs（network 65.5µs，2.73x）；脚本已改为边界切组+中位数，但其端到端复跑未在轨迹内完成。",
  "tags": [
    "task.debugging",
    "task.testing",
    "topic.data_movement"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "agnostic"
  ]
}
---
# perf_compare_mx 按数量切组把首次 launch 的时长尖峰摊进均值，制造 8.5ms 级假异常

## 适用场景

- 模型/框架：WeLMv4 融合算子 `fused_qkv_proj_norm_rope_cache_mx` 的 msprof 性能测量脚本 `cannbot-arena/test/fused_qkv_proj_norm_rope_cache/perf_compare_mx.py`（方法：`msprof --task-time=on --ai-core=on`，解析 op_sumup 的 Task Duration，逐 op 求和）。
- 平台：Ascend 950DT，CANN 9.1.0-beta.3，msprof。
- 工作负载：doc_mx 采集的全 case 矩阵（prefill M=16500 mirror/plain + decode M∈{1,4,56,200}，fused vs network 双后端，repeat=10，warmup 1 次 forward）。
- 缺失信息：首发时长尖峰的具体构成（.so 加载/首次 dispatch）未进一步分解；"observed 85-640 ms"的波动来源未深究。

## 触发与观测

doc_mx 全 case 实测首轮（事件 1318）：9 个 case 全部 OK，但 `decode_m200_mirror/fused` 报 per_call=8521.96µs——同 batch 的 M=56 才 13.9µs、README 历史数据 M=200 为 26.1µs/66.4µs（2.54x），且同 case 的 network 后端 65.6µs 正常。单独复跑更糟（事件 1326）：per_call=64239.14µs。breakdown（事件 1322）显示异常全部落在融合 kernel 名下（`FusedQkvProjNormRopeCacheMxKernel: 8517.152µs`），`DynamicMxQuant` 仅 4.8µs。

perf_compare_mx.py 原『按数量切组』逻辑（per_forward = len(rows)//(repeat+1)，假设每次 forward 的 op 行数稳定）在 decode_m200_mirror/fused 的实际行分布下切组错位：首次 launch 额外携带首发时长尖峰（本次 642ms），按数量切组把它摊进了均值，得到 8522µs→64239µs 的假异常；op_summary 显示稳态 kernel 每次 19-24µs（比 README 历史值 26.1µs 还快）。

## 探针与操作

1. **检查复跑重复性**：单独复跑该 case（事件 1326）——复跑可重现（64ms），network 同 case 正常，问题特定于 fused M=200 的统计口径。
2. **查原始 op_summary**（事件 1329/1330，关键判别探针）：`PROF_*/mindstudio_profiler_output/op_summary_*.csv` 中融合 kernel 共 11 行（1 warmup + 10 measured），逐行打印 Task Duration：

```
total op rows: 23  fused kernel rows: 11
642146.824 _Z51kernel_FusedQkvProjNormRopeCacheMxKernel___call___038Ker
23.820 _Z51kernel_FusedQkvProjNormRopeCacheMxKernel___call___038Ker
19.393 _Z51kernel_FusedQkvProjNormRopeCacheMxKernel___call___038Ker
19.436 _Z51kernel_FusedQkvProjNormRopeCacheMxKernel___call___038Ker
20.800 _Z51kernel_FusedQkvProjNormRopeCacheMxKernel___call___038Ker
19.416 _Z51kernel_FusedQkvProjNormRopeCacheMxKernel___call___038Ker
19.272 _Z51kernel_FusedQkvProjNormRopeCacheMxKernel___call___038Ker
18.925 _Z51kernel_FusedQkvProjNormRopeCacheMxKernel___call___038Ker
19.588 _Z51kernel_FusedQkvProjNormRopeCacheMxKernel___call___038Ker
19.128 _Z51kernel_FusedQkvProjNormRopeCacheMxKernel___call___038Ker
19.252 _Z51kernel_FusedQkvProjNormRopeCacheMxKernel___call___038Ker
```

第一行 642146.824µs（约 642ms）是首发时长尖峰，其后为 18.9–23.8µs。来源把它解释为模块加载，但没有加载阶段分解或对应运行时事件，本卡仅采纳尖峰及统计污染的观测。

3. **原脚本瑕疵代码**（事件 1257/1340 oldString，按数量切组丢预热）：

```
    # rows includes warmup + repeat forwards; drop the first group's worth
    # by averaging over the last `repeat` forwards (op count per forward
    # is stable, so split by count).
    from collections import Counter

    per_forward = len(rows) // (repeat + 1)
    if per_forward == 0:
        return ("NO_OP", None, None)
    measured = rows[per_forward:]
    durs = [d for _, d, _ in measured]
    per_call = sum(durs) / repeat if len(durs) >= repeat else sum(durs) / max(1, repeat)
```

该 case 的行分布（复跑 fused backend 的 11 条 kernel 记录中首条带约 642ms 尖峰；总 op 行分布不能按固定数量可靠分组）使 `len(rows)//(repeat+1)` 的整除切组错位，warmup 没被正确丢弃且均值被尖峰污染。

4. **稳健后处理**（独立脚本对同一 op_summary 重算，事件 1333/1334）：按"每次 forward 以 `DynamicMxQuant` 开头"切组、丢弃 warmup 组、对测量组取中位数。全部 9 case 重算正常（事件 1334）：

```
case                    fused(us) network(us)  speedup
prefill_mirror              305.4       567.0    1.86x
prefill_plain               263.6       507.5    1.93x
decode_m1_mirror              9.9        31.3    3.15x
decode_m1_plain               9.2        30.9    3.35x
decode_m4_mirror             11.0        47.0    4.29x
decode_m4_plain              10.1        43.2    4.28x
decode_m56_mirror            12.5        55.7    4.47x
decode_m56_plain             12.2        50.8    4.15x
decode_m200_mirror           24.0        65.5    2.73x
```

decode_m200_mirror/fused 24.0µs，与 README 历史值 26.1µs 同量级。

5. **脚本内修复**（事件 1340，把后处理逻辑替换为边界切组 + 中位数；下列注释已收窄未验证归因，非逐字来源；逻辑仍缺修复后的端到端复跑）：

```
    if not rows:
        return ("NO_OP", None, None)
    # rows includes warmup + repeat forwards. Every forward of every backend
    # begins with DynamicMxQuant (quantize_activation), so split the
    # chronological stream into forward groups at that boundary and drop the
    # warmup group. The first launch has an observed timing spike (85-640 ms); its cause
    # was attributed to module loading in the source but not decomposed.
    # A naive count-based split can sweep it into the average; a median over the
    # measured groups reduces isolated-spike contamination under these grouping assumptions.
    groups, current = [], []
    for entry in rows:
        if "DynamicMxQuant" in entry[2] and current:
            groups.append(current)
            current = []
        current.append(entry)
    if current:
        groups.append(current)
    if len(groups) < 2:
        return ("NO_OP", None, None)
    measured_groups = groups[1:]

    import statistics

    per_forward_sums = [sum(d for _, d, _ in grp) for grp in measured_groups]
    per_call = statistics.median(per_forward_sums)
    n_used = len(per_forward_sums)
    breakdown = Counter()
    for grp in measured_groups:
        for _, d, name in grp:
            for m in _BACKENDS[backend]:
                if m in name:
                    breakdown[m] += d / n_used
                    break
    return ("OK", per_call, dict(sorted(breakdown.items(), key=lambda kv: -kv[1])))
```

## 机制与判别

- 判别分支一"算子真的慢"：被 op_summary 稳态 19-24µs 排除（比历史值还快）；
- 判别分支二"共享设备他人占用/偶发"：复跑仍见首发尖峰、network 正常，但这些观测不能排除共享设备争用或其他启动因素；
- 判别分支三"统计后处理瑕疵"：与全部观测吻合——复跑首条约 642ms 尖峰 + 按数量切组在行分布偏移时错位，把尖峰摊进 10 次均值（首轮 per_call 约 8.5ms 与后一次约 64.2ms 是不同采集轮次。后一次首发 642146.824µs 若被摊进 10 次均值，单此项约 64214.7µs，与该轮 64239.14µs 同量级；不能用它解释首轮 8521.96µs）。
- 边界确认：一次性加载大小不恒定（"observed 85-640 ms"，脚本注释记录的观测区间），因此该瑕疵在不同 case/轮次表现不同——prefill 等 case 因 kernel 行多且未超界而侥幸未错位，decode_m200 恰好是行分布触发错位的 case。

## 验证信号

（本轨迹内、Ascend 950DT 客观观测）

- 触发：事件 1318（decode_m200_mirror/fused per_call=8521.96µs，同轮 M=56 仅 13.9µs、network 65.6µs 正常）；事件 1326（复跑 64239.14µs）；事件 1322（breakdown 落在融合 kernel、README 历史值 26.1µs）。
- 诊断：事件 1330（op_summary 11 行：首行 642146.824µs 一次性加载 + 稳态 18.9-23.8µs）。
- 稳健重算：事件 1334（9 case 全部正常，decode_m200_mirror/fused 24.0µs vs network 65.5µs = 2.73x，与历史值同量级）。

稳健后处理（按『每次 forward 以 DynamicMxQuant 开头』的边界切组、丢弃 warmup 组、对测量组取中位数）重算全部 9 个 case 一切正常：decode_m200_mirror/fused 24.0µs vs network 65.5µs（2.73x），与 README 历史数据同量级；本例边界切组 + 中位数重算减小了首发尖峰的污染，但依赖分组边界正确且多数测量组正常。

已把脚本内按数量切组改为按 DynamicMxQuant 边界切组 + 中位数（含 breakdown 一并改为按测量组平均）；该编辑顺带移除了原代码块内的 from collections import Counter，复跑报 NameError，补回 import 后轨迹即结束——修复后脚本的端到端复跑未发生在本轨迹内，脚本修复以独立稳健后处理（同一算法对同一 op_summary 数据重算）的等价结果作旁证。

- 脚本修复应用与残留问题（客观事件链）：事件 1341（edit applied successfully）；事件 1344（复跑无输出）；事件 1347（NameError: name 'Counter' is not defined 的 traceback，定位 `breakdown = Counter()`）；事件 1350（补 `from collections import Counter` import 的编辑，轨迹在此结束）。

## 适用与失效边界

- 适用：任何"profiling 流水统计 warmup 后按 op 行数整除切组"的 msprof/op_summary 后处理脚本，尤其每 forward 首 op 可稳定识别（如本例 `DynamicMxQuant` = 每次融合/网络 forward 的 quantize_activation 首步）的场景。
- 修复前提：每次 forward 必须有稳定可识别的首 op 边界；若换 backend/算子后首 op 变化，切组标记需同步更新，否则会退化成更糟的错切。
- 失效/风险：中位数抗单点尖峰但抗不了系统性漂移（如全程被他人占用的轮次）；一次性加载区间 85-640ms 之外的情况未观测；本轨迹未完成修复后脚本的端到端复跑，采用前应先跑通该 case 确认。
- 停止/回退条件：若 profiling 目标本身就是"含首次加载的冷启动成本"，则不应丢弃 warmup 组——此修复只适用于稳态 kernel 计时口径。
