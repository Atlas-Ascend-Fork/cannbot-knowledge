---
type: API
title: 构造和析构函数
description: 创建与释放OpTilingRegistry对象。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/OpTilingRegistry/constructor_and_destructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# OpTilingRegistry构造和析构函数

创建与释放OpTilingRegistry对象。函数原型：OpTilingRegistry()（构造函数）和~OpTilingRegistry()（析构函数）。无参数、无返回值、无约束。OpTilingRegistry用于Tiling调优场景下注册和管理算子的Tiling策略，通过构造函数创建实例后可进行Tiling策略的注册和查询，析构时自动释放资源。调用示例：context_ascendc::OpTilingRegistry tmpIns;

<!-- cannbot:related:start -->
## 相关

- [LoadTilingLibrary](load_tiling_library.md)（`related`）：构造和析构函数说明创建与释放OpTilingRegistry对象；对LoadTilingLibrary而言，LoadTilingLibrary 完成共享库装载后由 GetTilingFunc 取函数；链接缺符号和产物不含目标符号是两个可操作的验证分支。
- [GetTilingFunc](get_tiling_func.md)（`same_topic`）：焦点处理OpTilingRegistry 加载动态库并取得 TilingFunc 的调测流程；构造和析构函数正文界定“创建与释放OpTilingRegistry对象”。候选承担 Registry 加载、对象构造、opName 设置、ContextBuilder 与 GetTilingFunc 调测，runbook复现函数依赖错误。
- [OpTilingRegistry](op_tiling_registry.md)（`same_topic`）：OpTilingRegistry 总览把构造析构、LoadTilingLibrary 和 GetTilingFunc 组织为完整注册流程。
- [Utils API简介](intro.md)（`same_topic`）：OpTilingRegistry 简介说明对象负责加载 Tiling 动态库并查找函数，给构造/析构函数提供生命周期上下文。
<!-- cannbot:related:end -->
