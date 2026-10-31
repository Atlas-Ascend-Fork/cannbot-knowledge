---
type: Optimization
title: 图后端与布局组合的待核验观测：精度、时延和 buffer 配置
description: 图后端、FIA布局、可变buffer与编译选项的待验证问题；撤下无法绑定原始记录的旧精度和性能断言。
tags:
- task.debugging
- topic.graph_execution
status: draft
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/utils/graph_utils.py
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/model_worker.py
  role: supporting
created_at: '2026-10-21T01:51:39Z'
updated_at: '2026-10-29T13:55:50Z'
platforms: []
---

# 图后端与布局组合：待验证问题

## 当前证据状态

此卡维持draft，平台与Scope未知。旧稿的兼容性PASS/FAIL表、16/16输出、时延和编译耗时未能绑定原始模型/环境/日志，已从当前正文撤下，追溯保留在本仓Git历史。背景指南展示选项不等于证明旧故障根因或修复有效。

## 待验证的问题

- 同一模型/软件下，所需FIA布局、Tensor或list长度接口和图后端能否组合，需分别验证；不能由BSH/BNSD名称直接推导可用性。
- KV/SSM buffer的就地更新和别名关系是否保留，需最小复现与重复replay；不能未经验证把精度漂移归因为某后端。
- 懒构建权重或buffer是否进入编译区，需查看实际捕获图和初始化顺序；图外物化是待评估方案，不能声称必定解决stale pointer。
- clone_output、inplace_pass、capture_limit等选项会影响图与内存；没有当前模型的证据时不提供一套通用推荐值。

## 当前接口背景与验收

当前共享Executor的GE使用dynamic=False；npugraph_ex由enable_dynamic_graph控制，默认True。缓存的非预热执行会跳guard，这不能代替正确性和输入边界验证。

补齐模型/软件提交、平台、命令、最小输入、输出误差和原始trace后再评审；同时测冷启动、稳态和内存，不将多个优化阶段拼为一组后端对照。本次未执行这些实验。

- [图模式决策](../rules/graph_mode_enable_decision_profiling.md)
- [当前编译入口](../../guides/optimization/graph_mode_decode_only_compile_backends.md)

## Evidence

- [graph_utils.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/utils/graph_utils.py)（supporting）
- [model_worker.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/model_worker.py)（supporting）
