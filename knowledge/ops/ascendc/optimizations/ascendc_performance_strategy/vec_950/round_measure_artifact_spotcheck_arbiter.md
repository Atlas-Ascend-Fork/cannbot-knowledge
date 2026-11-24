---
type: Optimization
title: 轮次 measure 中位数伪影会高估声称加速；>1.2x 声称必须用官方路径 spot check 裁决
description: 轮次声称 >1.2x 时对最大 case 跑官方路径 spot_check：偏差 >0.2 判 not_reproducible，机制标记待重验。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/round-measure-artifact-spotcheck-arbiter.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-20T06:35:03Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "applicability": {
    "constraints": [
      "spot check 只覆盖 1 个声称收益最大的 case，其它 case 的轮次声称仍需审慎",
      "median_dispersion 的稳定样本区间可作为真实值的交叉印证",
      "同一机制可在后续轮次原样重验（R3 逐字重应用先例：case6 41.9us claimed vs 41.94us official reproducible）"
    ],
    "excluded_conditions": [
      "加速 ≤1.2x 不强制 spot check",
      "official 路径与 round 路径均 stable 且一致时无伪影，不需要本教训",
      "机制 correctness 失败时不适用（那是另一类拒绝，与测量伪影无关）"
    ],
    "required_conditions": [
      "轮次 incremental total_speedup > 1.2x（触发 item-7 spot check 门禁）",
      "被质疑 case 的官方路径 elapsed 与轮次 claimed 差异 >20%（|claimed/actual-1|>0.2）",
      "机制本身在官方路径可复现真实收益且 correctness 全过（区分伪影 vs 机制失败）"
    ]
  },
  "classification": "lesson",
  "evidence": [
    {
      "comparison_sha256": "07b70994d6a880ef55f87063b6de67493ebf3808b758c48bdd615fed73e9b656",
      "decision_sha256": "941305af516eae07a31f0fa2e5455cdc12b50a5a16b60f9275a0ca661ba1e35c",
      "operator_class": "vv-fusion",
      "performance_sha256": "743ce3cab2c3e6721959d44877fc33cdb70303957e38d19f1744dafc72d0ed2c",
      "round": 2,
      "run_id": "<run-id>",
      "status": "rejected",
      "strategy_sha256": "250e66efe24aaba4b62fa4cd7518356bf5ef958cffc6e6961d9068f1f5a4a7d2",
      "verify_sha256": "f6e5aeedd1cc7892e59ad1a67f74e6f1d2700838f3c39e5f64716899397d078d"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "measure-artifact",
      "median-dispersion"
    ],
    "dtypes": [],
    "hardware": [
      "ascend950",
      "dav_3510"
    ],
    "pattern": "round-measure-not-reproducible-official",
    "structure": []
  },
  "generality": "common",
  "id": "LESSON-ROUND-MEASURE-ARTIFACT-SPOTCHECK",
  "implementation_steps": [
    "轮次声称 >1.2x 时对最大声称 case 运行 spot_check.py 并读取 verdict",
    "not_reproducible → 检查稳定样本区间是否与官方吻合（区分伪影 vs 真实收益）",
    "机制正确时在后续轮次重应用同一 VF/描述符布局，用新的官方路径 spot check 完成验收"
  ],
  "intent": "拦截 measure.py 在 pytest 子集/并发采集下 kernel_details 中位数伪影对轮次加速的高估，防止把测量伪影当作真实收益验收，同时避免把被伪影拖累的正确机制整体否定。",
  "mechanism": "轮次 measure 采集 kernel_details 中位数 → compare_results 出 incremental total_speedup → 若 >1.2x 对收益最大 case 运行 spot_check.py（官方评测路径 kernel_details Σ Duration）→ |claimed/actual-1|>0.2 → not_reproducible → rejected，并把机制标记为 '待重验'（不直接否定机制）。",
  "name": "轮次 measure 中位数伪影会高估声称加速；>1.2x 声称必须用官方路径 spot check 裁决",
  "operator_scope": "任何在轮次路径（pytest 子集/并发采集的 kernel_details ΣDuration 中位数）声称增量加速 >1.2x 的算子优化轮次",
  "principle": "measure.py 的 kernel_details ΣDuration 中位数在并发/子集测量下可能与官方 profiler 路径偏离（median_dispersion 分布：稳定样本集中在真实值附近但中位数被离群子样本拉偏）；当声称加速 >1.2x 时，官方路径 spot check 提供独立于 round 采集的证据链，是判断 '真实机制收益 vs 测量伪影' 的仲裁者。median_dispersion 的稳定样本区间可交叉印证真实值。",
  "related_anti_patterns": [],
  "risks": [
    "把测量伪影当作真实收益验收（高估）",
    "把被拒轮次机制整体否定，丢弃真实可用机制",
    "用文字结论覆盖 spot_check 失败结果"
  ],
  "slug": "round-measure-artifact-spotcheck-arbiter",
  "summary": "mhc_sinkhorn R2 的 elementwise batch-per-lane VF 实测正确且官方路径有真实收益（case6 258->176us 1.47x、case15 1.99x、20/20 correctness），但轮次 measure 声称 case6 137us 被官方路径 spot check 证伪（claimed 137.33 vs actual 175.67us，|claimed/actual-1|=0.218>0.2）→ not_reproducible → 轮次被拒。median_dispersion 的稳定样本 172-179us 与官方 176us 吻合，证明真实增益仍存在。教训：轮次声称 >1.2x 时官方路径 spot check（acceptance-checklist item-7）是最后防线；被拒轮次不代表机制失败，应把机制原样重验于后续轮次（R3 逐字重应用同一 VF + batch-column MTE3 后被接受）。",
  "verification": {
    "correctness": [
      "R2 verify 20/20 correctness_pass",
      "case15 官方路径可复现 1.99x（ratio 1.027）"
    ],
    "performance": [
      "R2 claimed case6 137.33us vs official 175.67us（ratio 0.7818）→ not_reproducible → rejected",
      "case6 真实官方收益 258->176us（1.47x），机制仍有效；R3 重验后 case6 41.9us（官方 41.94us）"
    ],
    "rollback_signals": [
      "spot_check verdict=not_reproducible",
      "claimed/actual 偏差 >0.2"
    ]
  }
}
-->

# 性能优化策略：轮次 measure 中位数伪影会高估声称加速；>1.2x 声称必须用官方路径 spot check 裁决

单一优化点：mhc_sinkhorn R2 的 elementwise batch-per-lane VF 实测正确且官方路径有真实收益（case6 258->176us 1.47x、case15 1.99x、20/20 correctness），但轮次 measure 声称 case6 137us 被官方路径 spot check 证伪（claimed 137.33 vs actual 175.67us，|claimed/actual-1|=0.218>0.2）→ not_reproducible → 轮次被拒。median_dispersion 的稳定样本 172-179us 与官方 176us 吻合，证明真实增益仍存在。教训：轮次声称 >1.2x 时官方路径 spot check（acceptance-checklist item-7）是最后防线；被拒轮次不代表机制失败，应把机制原样重验于后续轮次（R3 逐字重应用同一 VF + batch-column MTE3 后被接受）。

## 1. 原理

measure.py 的 kernel_details ΣDuration 中位数在并发/子集测量下可能与官方 profiler 路径偏离（median_dispersion 分布：稳定样本集中在真实值附近但中位数被离群子样本拉偏）；当声称加速 >1.2x 时，官方路径 spot check 提供独立于 round 采集的证据链，是判断 '真实机制收益 vs 测量伪影' 的仲裁者。median_dispersion 的稳定样本区间可交叉印证真实值。

实现机制：轮次 measure 采集 kernel_details 中位数 → compare_results 出 incremental total_speedup → 若 >1.2x 对收益最大 case 运行 spot_check.py（官方评测路径 kernel_details Σ Duration）→ |claimed/actual-1|>0.2 → not_reproducible → rejected，并把机制标记为 '待重验'（不直接否定机制）。

## 2. 性能问题模式

- 优化目标：拦截 measure.py 在 pytest 子集/并发采集下 kernel_details 中位数伪影对轮次加速的高估，防止把测量伪影当作真实收益验收，同时避免把被伪影拖累的正确机制整体否定。
- 适用数据流：任何在轮次路径（pytest 子集/并发采集的 kernel_details ΣDuration 中位数）声称增量加速 >1.2x 的算子优化轮次
- Feature signature：`{"bottleneck": ["measure-artifact", "median-dispersion"], "dtypes": [], "hardware": ["ascend950", "dav_3510"], "pattern": "round-measure-not-reproducible-official", "structure": []}`

## 3. 正确性红线

- 把测量伪影当作真实收益验收（高估）
- 把被拒轮次机制整体否定，丢弃真实可用机制
- 用文字结论覆盖 spot_check 失败结果

资源与硬件约束：

- spot check 只覆盖 1 个声称收益最大的 case，其它 case 的轮次声称仍需审慎
- median_dispersion 的稳定样本区间可作为真实值的交叉印证
- 同一机制可在后续轮次原样重验（R3 逐字重应用先例：case6 41.9us claimed vs 41.94us official reproducible）

## 4. 泛化条件

- 策略作用域：common（跨 operator class）

适用：

- 轮次 incremental total_speedup > 1.2x（触发 item-7 spot check 门禁）
- 被质疑 case 的官方路径 elapsed 与轮次 claimed 差异 >20%（|claimed/actual-1|>0.2）
- 机制本身在官方路径可复现真实收益且 correctness 全过（区分伪影 vs 机制失败）

不适用：

- 加速 ≤1.2x 不强制 spot check
- official 路径与 round 路径均 stable 且一致时无伪影，不需要本教训
- 机制 correctness 失败时不适用（那是另一类拒绝，与测量伪影无关）

## 5. 实施步骤

1. 轮次声称 >1.2x 时对最大声称 case 运行 spot_check.py 并读取 verdict
2. not_reproducible → 检查稳定样本区间是否与官方吻合（区分伪影 vs 真实收益）
3. 机制正确时在后续轮次重应用同一 VF/描述符布局，用新的官方路径 spot check 完成验收

## 6. LLM 前置问题

- 目标实现是否满足：轮次 incremental total_speedup > 1.2x（触发 item-7 spot check 门禁）？
- 目标实现是否满足：被质疑 case 的官方路径 elapsed 与轮次 claimed 差异 >20%（|claimed/actual-1|>0.2）？
- 目标实现是否满足：机制本身在官方路径可复现真实收益且 correctness 全过（区分伪影 vs 机制失败）？
- 是否命中排除条件：加速 ≤1.2x 不强制 spot check？

## 7. 验收标准

正确性：

- R2 verify 20/20 correctness_pass
- case15 官方路径可复现 1.99x（ratio 1.027）

性能：

- R2 claimed case6 137.33us vs official 175.67us（ratio 0.7818）→ not_reproducible → rejected
- case6 真实官方收益 258->176us（1.47x），机制仍有效；R3 重验后 case6 41.9us（官方 41.94us）

回滚信号：

- spot_check verdict=not_reproducible
- claimed/actual 偏差 >0.2

## 8. 分类与证据

- Classification：`lesson`
- Generality：`common`
- Related anti-patterns：无

- mhc_sinkhorn-20260831_151225-9b5adb（round=2, status=rejected）

## 检索卡（短卡）

动作：轮次声称 >1.2x 时对最大 case 跑官方路径 spot_check：偏差 >0.2 判 not_reproducible，机制标记待重验。
适用：轮次 total_speedup > 1.2x、被质疑 case 官方 elapsed 与 claimed 差异 >20%。
限制：spot check 只覆盖 1 个 case，其余声称仍需审慎；不得整体否定被拒轮次的机制。
范围：任何在轮次 measure 路径声称增量加速 >1.2x 的优化轮次。
检索词：spot_check、median_dispersion、kernel_details、not_reproducible、item-7
机会：pytest 子集/并发采集下 kernel_details 中位数被离群子样本拉偏，高估轮次加速。
