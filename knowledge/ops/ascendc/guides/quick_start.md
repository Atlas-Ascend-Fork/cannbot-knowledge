---
type: Guide
title: 快速开始
description: 根据本地是否有NPU设备和使用目标选择对应的环境准备方式：
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/quick_start.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# 快速开始

## 🛠️ 环境准备
根据本地是否有NPU设备和使用目标选择对应的环境准备方式：
环境准备：社区体验 / 算子开发（CANN商用/社区版）：生态开发者贡献（CANN master）
无NPU设备：云开发环境：手动下载安装CANN master + 云开发环境
有NPU设备：CANN官方Docker镜像：手动下载安装CANN master + Dev Container
> [!TIP] 选择建议
>
> - 为了保障开发体验环境的质量，推荐用户基于容器化技术完成环境准备。
> - 如不希望使用容器，也可在带NPU设备的主机上完成环境准备，请参考CANN软件安装指南 - 在物理机上安装。
> - 针对仅体验"编译安装本开源仓 + 仿真环境运行算子"的用户，不要求主机带NPU设备，可跳过安装NPU驱动和固件，直接安装CANN包，请参考下载安装CANN包。
### 1️⃣ 云开发环境
对于无NPU设备的用户，可直接使用CANNLab云开发环境，即"一站式开发平台"，该平台提供了在线可直接运行的昇腾ARM架构环境，环境中已安装必备的驱动固件、软件包和依赖，无需手动安装。该平台目前仅适用于Atlas A2系列产品，提供两种接入方式：
- WebIDE，提供网页版的便携开发体验。
- VSCode IDE，支持远程连接云开发环境，提供VSCode强大插件市场的支持。
1. 进入开源仓Gitcode页面，单击"CANNLab > 云开发"按钮，使用已认证过的华为云账号登录。若未注册或认证，请根据页面提示进行注册和认证。
2. 根据页面提示创建NPU环境并配置规格，启动云开发环境后，单击"连接 > WebIDE 或 Visual Studio Code"进入一站式开发平台。开源项目的资源默认在/mnt/workspace目录下。
### 2️⃣ CANN官方Docker镜像
对于有NPU设备的用户，可使用CANN官方Docker镜像进行开发体验。
1. 确认主机环境
- 是否已安装NPU驱动和固件，使用npu-smi info能够输出NPU相关信息，如没有安装，请参考《CANN软件安装指南》中“准备软件包”和“安装NPU驱动和固件”章节。驱动与固件是运行态依赖，若仅编译本项目源码，可以不安装。
- 是否已安装Docker，使用docker --version能够输出Docker版本信息，如没有安装，请参考Docker官方安装指南。
2. 下载CANN镜像
从昇腾镜像仓库拉取已预集成CANN镜像：
3. 运行Docker
拉取镜像后，需要以特定参数启动，以便容器内能访问宿主机的NPU设备。

<!-- cannbot:related:start -->
## 相关

- [Ascend C多层级编程接口选择参考](asc_how_to_choose_api.md)（`related`）：Ascend C多层级编程接口选择参考 与《快速开始》的实质衔接是：概述/快速开始解释学习入口，TPipe/TQue 原理与范式对应 choice guide 的易编程层，兼容性策略说明跨代选择接口层时的稳定性成本。
- [Hello World](getting_started/quick_start/simd_programming/hello_world.md)（`related`）：快速开始总页给出 HelloWorld 所处的学习顺序和前置环境。
<!-- cannbot:related:end -->
