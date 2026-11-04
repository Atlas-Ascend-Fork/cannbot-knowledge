---
type: Runbook
title: msprof 资源占比定位逐行 V 调用主导而非搬运瓶颈
description: op_summary 的 vec/scalar/mac/mte 占比是可重叠的流水 cycle 份额，只能当排查线索（优先查向量/标量调用组织与等待，再看搬运），判瓶颈须回到源码与成对对照；本例据此选“批量化+因子折进操作数”而非调搬运。
tags: [task.optimization, topic.performance.analysis, topic.programming_model.execution_unit.vector]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/guide/operator_practice/performance_analysis/analyze_performance_data.md
    role: supporting
created_at: "2026-10-28T09:46:50Z"
updated_at: "2026-11-02T07:57:34Z"
platforms: ["310p"]
---

# msprof 资源占比定位逐行 V 调用主导而非搬运瓶颈

## 现象

一个基于 Cube+Mmad 的分块递推算子（门控 delta rule 类）在 310P 上首版 kernel 已能跑通、精度也过，但主口径（msprof kernel 级耗时）明显慢于参考实现，且“加大双缓冲/提高 mte2 重叠”一类常规搬运优化几乎没有收益。

对单例做 `msprof --ai-core=on --task-time=on` 采集后，从 `op_summary*.csv` 里挑 `Op Name` 含目标 kernel 的中位时长行，逐列读出资源占比（只看比例，不看绝对时长）：

```
vec_ratio        0.432
mac_ratio        0.021
scalar_ratio     0.318
mte1_ratio       0.022
mte2_ratio       0.347
mte3_ratio       0.07
memory_bound     0.803
```

判别特征：**vec_ratio + scalar_ratio 合计约占 aicore 时间的三分之二以上，而 mac_ratio 只有 2% 量级**；mte2_ratio 虽然不低，但两个搬运比都明显小于 vec+scalar 之和。也就是说占比形态与“指令条数主导（向量调用多 + 标量循环多）、立方（mac）闲置”的假设一致。占比只是各流水的 cycle 份额、可重叠，不能当互斥的墙钟时间相加——它给出的是排查优先级，最终判定靠源码形态与成对对照（见“判别方法”与“验证信号”）。

配套读法是看 `scalar_ratio` 本身：标量占比占到三成是一个**线索**——可能存在按行/按元素的标量循环（如逐行 `GetValue`、逐行 `Duplicate`、逐行 `Muls`），也可能是标量侧等待/调度占比高；占比本身区分不了这两者，本例是回到源码看到显式循环后才确认的。

## 适用场景

- 工程形态：AscendC kernel 直调（自写 `__global__ __aicore__` kernel + torch.ops 绑定），非 aclnn/spec 生成。
- API 路径：`msprof`（`--ai-core=on --task-time=on`）→ `mindstudio_profiler_output/op_summary_*.csv` 的 `vec_ratio`/`scalar_ratio`/`mac_ratio`/`mte2_ratio`/`memory_bound` 列；kernel 侧手段涉及 `Mmad`（Cube）、`Brcb`/`Transpose`/`Select`/`Muls`/`Cast`（Vector）、`DataCopy`（MTE）。
- 验证过的平台与 CANN 版本：310P（dav-m200 / DAV_2002）+ CANN 9.1.0。
- 适用粒度：platform_wide（任何在 310P 上做 Cube+Vector 混合算子的 profiling 选型）。
- 路线优先级：recommended_fastpath。
- 明确不适用 / 未验证场景：A 核（cube）密集的 GEMM 型算子（mac_ratio 高时不适用）；纯 MTE 受限的 streaming 算子；未在 910B/其他 SoC 上验证（未验证，推断可迁移，但 910 系 profiling 列名与占比基线不同）。

## 判别方法

1. 采集：对单例跑 `msprof --ai-core=on --task-time=on`，在 `op_summary*.csv` 中按 `Task Duration(us)` 取中位行（避免首跑冷启动/尾块噪声）。
2. 读占比（**线索优先级，不是判定**——各流水占比可重叠，不能相加当互斥墙钟，也不能仅凭占比排除访存/同步限制）：
   - `vec_ratio + scalar_ratio` 明显高于 `mte2_ratio` 且 `mac_ratio` < 5% → 优先按“向量/标量指令条数与组织”排查：读源码数 V 调用次数、找逐行循环，再看等待/冲突类指标；确认后再动“减少 V 调用、消除标量循环、立方批量化”。
   - `mte2_ratio` 最高且 `memory_bound` 接近 1、vec/mac 都低 → 优先按搬运排查（双缓冲/融合搬运），同样须用源码与对照确认。
   - `mac_ratio` 高但利用率低 → 优先按 tiling/尾块排查。
3. 交叉验证：把 `scalar_ratio` 单独看——占比高提示“可能有逐行/逐元素标量循环（`GetValue`、按 `i` 的 `Muls`/`Duplicate` 循环）”，但占比区分不了“标量计算”与“标量等待/调度”，也没有可跨算子复用的阈值（本例 ≈0.32，未做阈值标定）；确认只能回源码 + 修复前后对照。
4. 定手段（方向都落在“把每行一次 V 调用变成一次立方/一次整张量 V 调用”；**其中第 1 项在本会话已被证伪并回退**，列出仅为说明杠杆方向）：
   - 前缀和 + 广播因子矩阵改用 Cube（`Ltri @ g_bcast`）——**已证伪候选**：强门控用例上非确定性漂移、整体回退，终版用的是向量前缀和，不得直接采用，见 [前缀和立方化到 Ltri@bcast：思路可行，强门控下漂移已回退](prefix_sum_two_mmad_ltri_split_banned.md)；
   - 逐行衰减因子折进 f16 的 A 操作数，整带一次 Mmad；
   - 逐行掩码/权重改用整张量 `Select`/`Brcb` 列广播（注意 m200 上全张量 Select 的可用性，见同目录精度类卡）。

## 设计决策

- 选择“先 profiling 再动手”而不是直接上双缓冲：同一算子内两条路线的成对实测表明，搬运优化收益远小于删 V 调用与标量循环；若按直觉加双缓冲，会把 UB 预算吃光（本算子的 scratch 预算是硬约束，见同目录精度类卡）而收益很小。
- 放弃“把 chunk 变小以减少单 chunk 标量次数”：标量次数与 chunk 数成正比，缩小 chunk 反而增加总次数。
- 当前方案属 recommended_fastpath。

## 系统信息

- toolchain：CANN 9.1.0，bisheng/ccec 编译器，`cmake` + `ascendc.cmake`，SOC_VERSION=Ascend310P3。
- 目标平台：310P（dav-m200 / DAV_2002）。
- 采集产物：`msprof` 输出目录下 `mindstudio_profiler_output/op_summary_*.csv`；脚本侧用 `csv.DictReader` 读列（探针命令见下）。
- 相关文件：`kernel/<generic>.cpp`（被测 kernel）、评测侧 `msprof_perf_summary.py` 生成 wrapper（只读）。

## 完整代码

诊断脚本（可直接复用；把 `<kernel>` 换成目标 kernel 名）：

```python
cd <diag-dir>/prof_baseline/PROF_*/mindstudio_profiler_output && python3 -c "
import csv, os
f=[x for x in os.listdir('.') if x.startswith('op_summary')][0]
rows=[r for r in csv.DictReader(open(f)) if '<kernel>' in r['Op Name']]
ds=sorted(float(r['Task Duration(us)']) for r in rows)
r=[r for r in rows if abs(float(r['Task Duration(us)'])-ds[len(ds)//2])<1e-9][0]
for c in ['vec_ratio','scalar_ratio','mac_ratio','mte1_ratio','mte2_ratio','mte3_ratio','memory_bound']:
    print(f'  {c:24s} {r.get(c)}')
"
```

## 性能影响

同一算子内部两条路线成对对比（同一 msprof kernel Task_Duration 主口径、同一 10 例代表集、310P）：按本卡选型重写后的 v2 路线相对旧“逐行 V 调用/标量循环”路线约 **1.4x**（310P；这是整轮重写的合并收益，未做逐手段消融，不能拆归因给任何单一手段）；其中“逐行暖读改 32B”单项在 12 chunks 的用例上相对旧暖读省约 7% kernel 时间。均为同一 kernel 内的成对相对值，不作通用预期收益。

## 预防

- 每轮优化前先看 `vec_ratio`/`scalar_ratio`/`mac_ratio`，不要凭直觉猜瓶颈。
- 看到按 `for (i < 64)` 的 `Muls`/`Duplicate`/`GetValue` 循环，默认它们是主要成本，先想能否用一次 Mmad 或一次整张量 V 调用替换。
- `cube_utilization` 低不一定是 tiling 问题，也可能只是立方没被用上（数据都在向量路径上算）。

## 验证信号

来源说明：本卡来自一次 310P 上的算子性能优化开发会话，profiling 由 `msprof` 采集并在同一会话内用上述脚本读取 CSV 复现。

- 单例 op_summary 占比：`vec_ratio≈0.43`、`scalar_ratio≈0.32`、`mac_ratio≈0.02`、`mte2_ratio≈0.35`、`memory_bound≈0.80`（来源平台：310P；证据等级：tool_observed）。
- 按该选型重写后，主口径 10 例代表集全部有效（valid 10/10）、`COMPARE-EXIT=0`（来源平台：310P；证据等级：tool_observed）。
- 同一算子两条路线的成对相对对比：v2 路线相对旧逐行路线约 1.4x（来源平台：310P；证据等级：tool_observed）。

## 失效边界

- 只在 310P + CANN 9.1.0 上验证；910B/910C 的 op_summary 列与占比基线不同，未验证（推断可迁移，但判别阈值需重标）。
- 占比是各流水 cycle 份额、可重叠：本卡不主张“vec+scalar > mte2 即可判定指令数瓶颈”，也不设“scalar_ratio 超过某阈值即存在标量循环”的判据；占比只用于确定排查顺序。
- 若 `mac_ratio` 已经很高（立方吃满），本卡的“批量化到立方”建议无效，应按 tiling/尾块方向排查。
- 未决项：
  - **复现并追根因到机制层**：本会话未做逐手段消融，“删 V 调用”与“K64-native 减少 padding”各自贡献多少未分离；下个 agent 若要复用结论，应先做单手段 A/B。
  - 主口径 10 例代表集是按容器代表性挑选的固定子集，未验证其对全量 50 例分布的覆盖偏差。

## 坏实践

- 只看总时长不看资源占比就上双缓冲：本算子 UB scratch 预算紧，双缓冲会挤掉因子/掩码槽，收益却被 V 调用数掩盖。
- 把 `memory_bound≈0.8` 直接当成“搬运瓶颈”结论：mte2 只有约三成半，vec+scalar 合计更高——应优先怀疑指令条数，并按第 2 步回到源码与对照确认，而不是直接改搬运。
- 用 wall-clock（含 host 侧同步）判断 kernel 优化收益：本会话中 wall 与 kernel 口径差异可达数倍，必须以 kernel Task_Duration 为准。

## 误诊

- 推断（非实测）：会话早期曾把“用例测错”（据称 kernel 慢一个量级）归因为并发/设备争用；实际是拿错了对比用例的编号，重新对齐代表集后 kernel 单 chunk 成本与预期一致（该因果为会话自述，未作为验证信号）。

## 相关（平台对照）

- 950 平台的同类占比判别：[mte2_issue_overhead_vs_bandwidth_bound](mte2_issue_overhead_vs_bandwidth_bound.md)（“MTE2 占比高 ≠ 带宽 bound”，用每描述符耗时/有效带宽区分发射开销）。
- 平台边界：本卡的占比基线（本例 `mte2_ratio` 约 0.35 仍非首瓶颈、`vec+scalar` 合计过半）是在 310P（dav-m200）上读出的；950 卡的判别阈值与结论不可与本卡互相套用——两张卡都只主张“先看占比再选杠杆”，具体比例与阈值必须按平台重新标定。
