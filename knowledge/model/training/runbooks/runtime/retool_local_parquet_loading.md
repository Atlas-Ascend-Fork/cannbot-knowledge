---
type: Runbook
title: ReTool RL 本地数据集加载失败：显式选择 parquet 与默认配置
description: 在 Qwen3 Tool Agent 的历史 veRL checkout 中，处理本地 parquet 推断错误和 AIME 多配置 schema 混入，保留数据选择的边界。
tags:
- task.debugging
- topic.data_pipeline
- topic.reinforcement_learning
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/agent_rl/qwen3_tool_agent/patches/0004-Fix-local-parquet-loading-for-retool-datasets.patch
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-train/merge_requests/210
  role: evidence
created_at: '2026-10-29T04:09:07Z'
updated_at: '2026-10-29T15:39:15Z'
platforms:
- a3
---

# ReTool RL 本地数据集加载失败：显式选择 parquet 与默认配置

## 症状与快速检查

下载 DAPO-Math-17k 或 AIME 后，历史 ReTool 的 datasets.load_dataset(local_directory) 可能报 Value.__init__ 缺 dtype，或在读取多个配置时触发 CastError。先列出 data/、根目录和 part1/part2/ 下的 parquet，检查各配置 schema。

## 根因与修复

旧路径把本地目录直接交给 datasets 自动推断；修复 patch 显式使用 parquet 加载器与 data_files。目录输入先选 data/*.parquet，找不到时回退根目录 *.parquet，而非递归混入 AIME 其他配置；显式文件输入保持文件列表语义。

应用与该历史 veRL checkout 匹配的 0004 patch，确认修改落在 recipe/retool/retool.py。它承接已有前三个 patch，不替代奖励函数和预处理适配。

## 验证、回退与残留风险

打印实际加载的文件、行数、字段及 train/validation 来源，分别验证 SFT 和 RL 数据读取。若确实需要其他 AIME 配置，应单独声明并校验 schema，不能为消除错误静默丢数据。空匹配或错误目录应先修正路径，不能伪造空数据训练成功。

回退时恢复同一历史 checkout 与匹配 datasets 环境。PR210 作者报告在 A3 8 卡完成 SFT/RL 验证；本批仅核对 patch，未复测。

## Evidence

- [0004-Fix-local-parquet-loading-for-retool-datasets.patch](../../../../../cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/agent_rl/qwen3_tool_agent/patches/0004-Fix-local-parquet-loading-for-retool-datasets.patch)（primary）
- [远程来源](https://gitcode.com/cann/cann-recipes-train/merge_requests/210)（evidence）
