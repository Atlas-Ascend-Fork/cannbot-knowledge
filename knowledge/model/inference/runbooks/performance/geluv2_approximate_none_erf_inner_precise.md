---
{
  "type": "Runbook",
  "title": "GeluV2(approximate=none) erf 链融合与 FA inner_precise=0 在 910_93/CANN 9.1.0 均无性能收益回退（精度反而更优）",
  "description": "ViT-L/14 的 24 条 erf 链融合为 GeluV2(none) 后精度门禁通过，1000-iter 复测为 6.324ms、关闭为 5.970ms，轨迹据此回退；首轮 500-iter 快照为 6.090ms。FA inner_precise=0 的单次 6.075ms 比默认值高 1.8%，处于约定 3% 噪声带内，只能说明未观察到可靠收益，不能推出高精度零开销或 engine 已最优。",
  "tags": [
    "task.debugging",
    "topic.model_serving",
    "topic.attention"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-04T02:06:31Z",
  "platforms": [
    "910"
  ]
}
---

# GeluV2(approximate=none) erf 链融合与 FA inner_precise=0 在 910_93/CANN 9.1.0 均无性能收益回退（精度反而更优）

## 适用场景

- 模型/框架：M400（ViT-L/14，onnx，GE Session v2 内存图 pass），MLP 激活为 erf 精确型 GELU 五算子链（onnx Div/Erf/Add/Mul/Mul；GE 图中 RealDiv/Erf/Add/Mul/Mul）。
- 平台/版本：Ascend 910B 单卡，CANN 9.1.0（aarch64），fp16 全图 + FA 融合已落地的叠加配置。
- 目标与工作负载：单卡推理 batch=1 串行（THREAD_NUM=1、circle=1000），评估 erf 链显式融合为 GeluV2(none) 与 FA inner_precise=0 的性能收益。
- 缺失信息：仅单次/两次复测（5.97～6.32ms 区间），未做多次统计；仅 fp16 口径。

## 触发与观测

触发：iter2 画像中 GE 内置融合 Gelu 24 实例 374us（fp16 比 fp32 的 330us 略慢），促使尝试显式 GeluV2；同时测试 FA 的 inner_precise 配置。开关操作简单不代表它对计算性能没有成本。

能力确认（事件 645/648）：GeluV2 在 `aic-ascend910_93-ops-info-legacy.json` 中 `attr_approximate` 支持 `none,tanh`，输入 dtype bfloat16/float16/float；erf 匹配器将 24 链全部融合（事件 682：`[GELU-PASS] fused 24 GELU chain(s) into GeluV2`）。

精度观测（事件 685）：

```
[PASS] output[0] feature (float32) max_abs=0.00048544 max_rel=522.6977%
```

性能观测（事件 685/689，A/B 同口径复测）：

```
[GE PROGRESS] iter=500/1000 | Qps=64.53 | avg session run time=6.090ms   （融合，首轮）
[GE PROGRESS] iter=1000/1000 | Qps=90.99 | avg session run time=6.324ms  （融合，复测）
=== off ===
[GE PROGRESS] iter=1000/1000 | Qps=94.71 | avg session run time=5.970ms  （关闭）
```

inner_precise=0 观测（事件 696）：

```
[GE PROGRESS] iter=1000/1000 | Qps=92.46 | avg session run time=6.075ms | TP99:6.170ms | TP999:7.317ms
```

## 探针与操作

A/B 复测命令（事件 688，原文；单次 1000-iter × 两臂）：

```
GE_GELU_FUSION_PASS=1 bash run.sh 400 --circle 1000 --debug-freq 1000 2>&1 | grep -E "GE PROGRESS|GE RESULT" | tail -3; echo "=== off ==="; GE_GELU_FUSION_PASS= bash run.sh 400 --circle 1000 --debug-freq 1000 2>&1 | grep -E "GE PROGRESS|GE RESULT" | tail -3
```

inner_precise=0 试验命令（事件 695）：`GE_FA_INNER_PRECISE=0 bash run.sh 400 --circle 1000 --debug-freq 1000`。

两项均在裁定回退后从部署配置（M400_env.sh）移除开关（默认关闭），erf 匹配器代码保留在 pass 中（开关保护）。

## 机制与判别

回退记录一（按原始日志复核）：

GeluV2 在 910_93 ops-info 中支持 approximate=none（erf 形，输入 dtype bfloat16/float16/float），匹配器融合了 24 条链，verify PASS、max_abs=0.00048544。首轮 500-iter 快照为 6.090ms，1000-iter 复测为 6.324ms，关闭臂 1000-iter 为 5.970ms，轨迹选择回退。

本例精度误差由约 1.3e-3 降至 4.85e-4；该样本不能证明所有输入均有相同比例收益。1000-iter 的时延差约 +5.9%，首轮快照差约 +2.0%，后者不能与完整复测视为相同统计窗口。GE 在 pass 运行时点链仍为五算子形态，显式融合与内置融合属于替代路线；时延差的稳定性还需重复配对测量。

回退记录二：

GE_FA_INNER_PRECISE=0 的单次 avg 为 6.075ms，默认 inner_precise=1 为 5.970ms（差约 +1.8%），轨迹回退默认 1。

判读边界：约 +1.8% 的差异落在约定的 3% 噪声带内，本例只能说未观察到可靠收益。没有重复配对统计和 engine/内部执行证据，不能据此证明关闭精度选项导致变慢、高精度中间计算没有额外开销或 engine 选择已经最优。

## 验证信号

- 事件 645：ops-info JSON 确认 GeluV2 支持 approximate=none（CANN 9.1.0 安装目录实测）。
- 事件 682：24 链融合成功（单次运行）。
- 事件 685/689：融合首轮快照 iter=500 为 6.090ms；复测 iter=1000 为 6.324ms，关闭臂 iter=1000 为 5.970ms；精度 max_abs=0.00048544。
- 事件 696：inner_precise=0 臂 6.075ms vs 默认 5.97ms（各单次 1000-iter）。
- 回退记录写入 perf_ledger（reverted: true，含重试条件）。

## 适用与失效边界

- 已观测回退：CANN 9.1.0 / ascend910_93 / fp16 全图 + FA 配置下，GeluV2(none) 的完整 1000-iter 复测较慢约 5.9%；不把首轮半程快照或该数值外推为稳定收益范围。
- 边界：结论为单/双次复测观测（5.97～6.32ms 区间，3% 噪声带约定），未做多次统计平均。
- 重试条件：CANN 版本升级后 GeluV2 优化（或 fp16 内置 Gelu 出现劣化 regression）时重评；pass 代码保留、开关默认关，重评成本为零。
- 精度优先时可评估 GE_GELU_FUSION_PASS=1；需在实际输入上重新验证误差和时延，不能保证约 3 倍精度改善或固定时延代价。
- inner_precise=0 的回退与（未在本轨迹内验证的）M200 先验结论方向一致，属旁证。
