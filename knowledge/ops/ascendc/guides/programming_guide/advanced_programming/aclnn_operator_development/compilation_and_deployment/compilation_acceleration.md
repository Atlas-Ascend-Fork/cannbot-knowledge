---
type: Guide
title: 高级编程编译加速
description: 本文是扩展内容，介绍如何降低算子工程的编译耗时。算子工程编译耗时主要来自Kernel侧代码的逐芯片、逐TilingKey编译；本文从缓存复用、选择性编译、并行度和增量构建四个维度给出加速方案。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/aclnn_operator_development/compilation_and_deployment/compilation_acceleration.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 编译加速

本文是扩展内容，介绍如何降低算子工程的编译耗时。算子工程编译耗时主要来自Kernel侧代码的逐芯片、逐TilingKey编译；本文从缓存复用、选择性编译、并行度和增量构建四个维度给出加速方案。
## ccache编译缓存
ccache是编译缓存工具。第一次编译时，它把编译结果写入缓存；后续编译如果源码、编译命令、编译器等输入一致，就可以复用缓存，减少重复编译耗时。
在算子工程中，可通过CMake的CMAKE_CXX_COMPILER_LAUNCHER配置ccache。该变量会作用于Host侧C++编译；在CANN算子工程中，CMake模块也会将ccache路径传给Kernel侧编译脚本，用于Ascend C Kernel编译过程。
### 单机ccache
ccache安装及查找路径命令如下：
后续配置中的ccache路径以command -v ccache输出为准。ccache清空命令如下：
#### 启用方式
命令行临时启用
开发调试时，推荐在CMake配置阶段通过命令行启用ccache，不需要修改工程文件：
该命令会把ccache配置写入build_out/CMakeCache.txt。后续继续使用同一个build_out构建目录时，会沿用这个配置。
写入顶层CMakeLists.txt
如果希望工程长期默认启用ccache，也可以写入算子工程的顶层CMakeLists.txt，并放在创建编译目标之前，例如：
如果ccache安装在其他路径，请将/usr/bin/ccache替换为command -v ccache查到的实际路径。
#### 验证缓存是否生效
验证时需要注意：第一次构建通常是写缓存，命中率不高；第二次触发重新编译时，才应该看到缓存命中。
步骤1：清空缓存和统计，执行第一次构建。
第一次构建后，Misses通常较多，这是正常现象，表示缓存正在写入。
步骤2：保留缓存，只清空统计，再触发第二次编译。
如果源码没有变化而直接重复执行cmake --build，CMake可能判断无需重新编译，此时ccache统计不会明显变化。因此验证命中率时，可先执行clean目标清理构建产物，再重新构建：
第二次构建后，Hits或Primary storage中的Hits应明显提升。如果仍然没有命中，优先检查：
- configure阶段是否传入了-DCMAKE_CXX_COMPILER_LAUNCHER=$(command -v ccache)。
- 构建目录中的编译命令是否包含ccache，可搜索build_out下的build.make。
- 两次编译的源码、编译器和编译选项是否一致。
更多ccache配置和缓存行为说明请参考ccache官方文档。
### 分布式缓存（ccache + Redis）
适用于多机共享缓存场景：机器A编译后将结果推送至Redis，机器B在相同源码、相同编译选项和相同工具链版本下可从Redis命中缓存，减少重复编译。
分布式场景下，ccache以各机器本地缓存作为一级缓存，Redis作为共享二级缓存。
