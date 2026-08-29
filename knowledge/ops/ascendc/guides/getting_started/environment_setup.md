---
type: Guide
title: 环境准备
description: 介绍Ascend C算子开发的环境准备，包括驱动固件、CANN软件包与CMake安装。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/getting_started/environment_setup.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 环境准备

-   进行Ascend C算子开发之前，需要安装驱动固件和CANN软件包，请参考《CANN快速安装》完成环境准备。
-   安装CMake。通过CMake编译Ascend C算子时，要求安装3.16及以上版本的CMake，如果版本不符合要求，可以参考如下示例安装满足要求的版本。
示例：安装3.16.0版本的CMake（x86_64架构）。
