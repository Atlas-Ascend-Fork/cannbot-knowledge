---
type: Runbook
title: 模型导入失败：models 命名空间遮蔽与 PYTHONPATH 缺失
description: ModuleNotFoundError models.gpt_oss 等同级模块导入失败时，区分模型子目录 __init__.py 遮蔽和启动脚本缺少仓库根路径。
tags:
- task.debugging
- topic.model_adaptation
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-migrator/references/common_issues.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/scripts/set_env.sh
  role: supporting
created_at: '2026-11-09T09:23:45Z'
updated_at: '2026-11-09T09:23:45Z'
platforms:
- agnostic
---

# 模型导入失败：models 命名空间遮蔽与 PYTHONPATH 缺失

## 症状与快速检查

从 models/<name> 启动后，executor/core/support_models.py 导入兄弟模型时出现 ModuleNotFoundError: No module named 'models.gpt_oss'。先记录 cwd、sys.path 和 models 的实际解析位置；同时检查 models/<name>/models/__init__.py 是否存在。

## 诊断与修复

模型内部 models/__init__.py 会把该子目录变成 regular package，从当前启动目录遮蔽仓库顶层 models namespace。只有确认顶层采用 namespace package、且文件确实是误建包入口时，才删除这个多余 __init__.py；不要为所有 Python 包套用这一修法。

另一条独立原因是自建 infer.sh 未把仓库根加入 PYTHONPATH。启动前根据脚本位置解析仓库根并加入搜索路径，或复用 executor/scripts/set_env.sh；后者已经处理仓库路径时不必重复添加。路径缺失与包遮蔽可能同时存在，设置 PYTHONPATH 不保证消除 regular package 的遮蔽。

## 验证、回退与边界

在原 cwd、原 Python 环境重新检查 import 的解析位置，再从原入口拉起，确认注册表能导入所有所需模型。修复仅影响导入；不能据此认定权重、算子或 NPU 环境已验收。保留启动脚本与目录改动的差异，包结构不符合上述前提时回退并按实际 import traceback 定位。

## Evidence

- [.agents/skills/model-infer-migrator/references/common_issues.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-migrator/references/common_issues.md)
- [executor/scripts/set_env.sh](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/scripts/set_env.sh)
