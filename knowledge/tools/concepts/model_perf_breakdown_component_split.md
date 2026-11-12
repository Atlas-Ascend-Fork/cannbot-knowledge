---
type: Concept
title: 模型推理性能数据的按层拆解方法（kernel_details 到 component 实例）
description: 把 profiler 产物 kernel_details.csv 按用户描述的模型结构切成 component 实例（每层 attn/ffn/moe…），再按 cluster 规则对 component 内部算子分桶，生成 wall_ms/bubble_ms 中位数与异常 layer 定位；判档复用（小改/中改/大改）避免重复对话定规则。
tags: [task.debugging, topic.performance.analysis, topic.model_architecture]
status: stable
sources:
  - resource: https://gitcode.com/cann/cannbot-skills/blob/6b7d8fdf1f213c20f231688665879b5bffa7f9d6/model/model-infer-perf-breakdown/SKILL.md
    role: primary
created_at: "2026-11-05T02:10:00Z"
updated_at: "2026-11-05T02:10:00Z"
platforms: [a2, a3, "950"]
aliases: [perf breakdown, component 实例, wall_ms, bubble_ms, 异常 layer]
---

# 模型推理性能数据的按层拆解方法（kernel_details 到 component 实例）

输入一份 profiler 产物（`kernel_details.csv` + `trace_view.json`），结合用户对模型结构的口头描述，把 op 序列切成 component 实例（每层 attention / ffn / moe…），再按 cluster 规则统计每类计算的 wall_ms + bubble_ms 中位数、抖动与异常 layer。适用于「分析大模型推理性能、找抖动 layer」的任务。

## 拆解流程

```
Step 0: 收齐 prof 路径 + 模型脚本路径（硬约束）
Step 1: kernel_details.csv → 单 step op 序列提取
Step 2: 用户描述模型结构 → structure spec；敲定每个 component 的 stream sample 范围（须用户确认）
Step 3: 用户与 agent 对话定 cluster 规则（把 component 内部算子分桶）
Step 4: 按 component 切 csv / trace（单层下钻）
Step 5: 洞察归纳（语义判断 + 脚本统计）
```

产出 wall_ms / bubble_ms 中位数、抖动与异常 layer 的单层下钻视图。内部指标字段用 `*_ms`，展示按量级自动使用 µs 或 ms。

## 判档复用（避免重复定规则）

复跑同一 run 目录时先做产物 diff 判档：

| 档 | 触发信号 | 复用范围 |
| --- | --- | --- |
| 小改 | kernel 集合完全相同、anchor 计数偏差为 0、stream anchors 相近位置命中 | 结构 spec 与 cluster 规则全复用，跳过所有对话 |
| 中改 | 出现新 normalized_name、anchor 计数偏差 ≤10%、sample 偏移 >5 行、shape 分布漂移 | 结构 spec 复用 + 回显问；重出 stream sample；cluster 规则增量补 |
| 大改 | anchor 计数偏差 >10%、总 op 数偏差 >30%、关键 anchor 消失 | 重走结构描述与 sample；旧规则只作参考逐条审 |

判档后向用户复述结论确认；用户不同意按用户给的档位走。首次跑（目录空）跳过 diff 走全量流程。

## 纪律与边界

- 禁止修改用户提供的任何原始文件（prof / modeling 源码 / config）；产物只写到本次 run 目录；
- wall/bubble 中位数反映 component 实例耗时结构；「异常 layer」是统计离群判定，根因仍需下钻该层 op 与 trace；
- 本卡为方法论蒸馏（来源技能的脚本与 CLI 细节留技能仓）；采集侧前置契约见[torch_npu.profiler 采集卡](torch_npu_profiler_collection_contract.md)——kernel_details.csv 列数不足（9 列）时先补 ExperimentalConfig 重采。
