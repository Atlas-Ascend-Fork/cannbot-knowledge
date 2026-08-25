---
type: Guide
title: 算子包部署时出现权限不足报错
description: 部署自定义算子包时，出现如下报错信息：
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/appendix/faq/operator_deploy_permission_error.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 算子包部署时出现权限不足报错

## 现象描述
部署自定义算子包时，出现如下报错信息：
## 问题根因
当前操作用户缺少对部署路径下vendors目录的写权限。
自定义算子包默认安装路径${INSTALL_DIR}/opp/vendors的目录权限与CANN软件包安装用户和安装配置有关：root用户安装CANN，${INSTALL_DIR}/opp/vendors权限为755；非root用户携带--install for all参数安装CANN，该目录权限为755，非root用户不带--install for all参数安装CANN时，该目录权限为750。
例如，root用户安装CANN软件包后，HwHiAiUser属组用户在对应目录部署自定义算子包，因为其他用户没有写权限，会出现上述报错信息，提示权限不足导致自定义算子包部署失败。
## 处理步骤
-   方法一：使用--install-path参数指定安装目录（参考指定目录安装）。运行用户需要对指定的安装路径有可读写权限。安装后执行生成的set_env.bash脚本，由该脚本配置算子运行时查找路径。
-   方法二：联系CANN软件包安装用户修改默认安装路径下的vendors目录权限，比如修改为777：
