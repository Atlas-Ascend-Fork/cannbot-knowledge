---
type: Optimization
title: HunyuanVideo 稀疏与 Ring 的来源数据及平台缺口
description: 最新稀疏与Ring来源表、已接入的当前实现和仍缺失的硬件/build/质量信息。
tags:
- task.testing
- topic.performance.analysis
status: draft
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/hunyuan-video/hunyuan_video_optimization.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/sample_video.py
  role: constraint
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/blockwise_sparse/sparse_method.py
  role: implementation
created_at: '2026-10-21T09:56:25Z'
updated_at: '2026-10-29T14:13:05Z'
platforms: []
---

# HunyuanVideo 稀疏与 Ring 的来源数据及平台缺口

## Workload

TopK/SVG 表与四卡 Ring 表分别保留；前者未在表内明确绑定卡数。TopK blockQ128/K512、CAC0.66、step10–49；SVG sparsity0.8、step14–49来自源文档。

## Hardware

这些稀疏表未独立绑定明确硬件/软件记录，不能从邻近A3/950表推断。保持draft、platforms=[]。

## Software

来源固定到下列提交；没有与每行数据绑定的完整软件build和原始运行记录，安装章节示例不自动等于测量环境。

## Baseline 与 Variant

仅在同一来源明确对照的行内比较。不同平台、阶段、batch、框架、量化、并行与版本不拼接为一次受控试验，也不把累计优化归因给单个开关。

## Metric Definition

字段和单位沿用源表。时延起止、首token/warmup处理、吞吐分母和精度指标未完整披露时保持未知，不由字段名称自行补计算公式。

## Repetition and Variance

没有足够的逐轮原始样本、重复次数、方差或置信区间。本仓未独立复测，不新增 verified。

## Result

### TopK/SVG（卡数待核验）

| Method | Sparsity | DiT Time (s) | E2E Time (s) | DiT Speedup | E2E Speedup |
| ------ | -------- | -----------: | -----------: | ----------: | ----------: |
| Baseline | – | 3459.52 | 3577.19 | 1.00× | 1.00× |
| TopK | 76% | **1839.48** | **1963.52** | **1.88×** | **1.82×** |
| SVG | 80% | 2036.18 | 2167.55 | 1.70× | 1.65× |

### 四卡Ring

| 方案 | `720*1280*209`, CAC `0.9` | `720*1280*209`, CAC `0.66` | `720*1280*129`, CAC `0.9` | `720*1280*129`, CAC `0.66` |
| ---- | ------------------------: | -------------------------: | ------------------------: | -------------------------: |
| Ring Attention | 2250 | 2250 | 949 | 949 |
| Ring + TopK | 1877 | 1385 | 812 | 554 |
| Ring + TopK + overlap | 1742 | 1327 | 822 | 584 |

另一Ulysses联合优化段给DiT耗时：单卡3587→2160s；四卡904→576（负载均衡564）s；八卡464→335（负载均衡321）s。三组不补作与上面单卡/四卡表相同的实验。

Ring overlap在209帧/CAC0.66下1385→1327s，而129帧下554→584s反而更慢；不声称overlap必然有收益。


## Limitations 与验证

当前源码已实现Ring TopK、LSE overlap与SVG，旧拒绝组合的结论已撤销；仍须匹配稀疏算子接口后验证，源码存在不补齐各表硬件与测量缺口。画质、逐轮样本和硬件仍待补。

复现与回退入口：[模型部署与验收流程](../../guides/models/hunyuan_video_deployment.md)。性能与输出质量分别验收；来源自报不构成本仓复现。


## Evidence

- [hunyuan_video_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/hunyuan-video/hunyuan_video_optimization.md)（primary）
- [sample_video.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/sample_video.py)（constraint）
- [sparse_method.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/blockwise_sparse/sparse_method.py)（implementation）

## 本轮来源核对与剩余缺口

重新读取同一固定指南的稀疏章节：编译示例使用 `--soc=ascend910_93`，并同时列出 A2/910b 与 A3/910_93 的映射。这确认构建选项，不是每张性能表的硬件日志；文首 A2、前面表格 A3、量化表 950PR 的不同范围也不能混用。

TopK/SVG 表内没有明确卡数，不再把默认单卡配置当作该表的测量卡数。四卡 Ring 的单位由相应段落确认为秒。源码与新版文档包含 Ring/LSE 路径，但稀疏算子依赖仍指向滚动上游，缺少与各组测量匹配的算子提交、输入输出与硬件记录，继续 draft。
