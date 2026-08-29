---
type: API
title: PlatformAscendCManager
description: Kernel直调场景下获取硬件平台信息的单例管理类，通过GetInstance获取PlatformAscendC指针以访问核数等平台信息。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/platform_info/PlatformAscendCManager.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# PlatformAscendCManager

## 功能说明
基于Kernel Launch算子工程，通过Kernel直调（Kernel Launch）方式调用算子的场景下，可能需要获取硬件平台相关信息，比如获取硬件平台的核数。PlatformAscendCManager类提供获取平台信息的功能：通过该类的GetInstance方法可以获取一个PlatformAscendC类的指针，再通过该指针获取硬件平台相关信息，支持获取的信息可参考PlatformAscendC。
> [!CAUTION]注意
>-   使用该功能需要包含"tiling/platform/platform_ascendc.h"头文件，并在编译脚本中链接tiling_api、platform动态库。
>    -   包含头文件的样例如下：
>
>    -   链接动态库的样例如下:
>
## 函数原型
## 参数说明
customSocVersion：AI处理器型号。
AI处理器的型号请通过如下方式获取：
-   针对如下产品：在安装AI处理器的服务器执行npu-smi info命令进行查询，获取Name信息。实际配置值为AscendName，例如Name取值为xxxyy，实际配置值为Ascendxxxyy。
Atlas A2 训练系列产品/Atlas A2 推理系列产品
Atlas 200I/500 A2 推理产品
Atlas 推理系列产品
Atlas 训练系列产品
-   针对Atlas A3 训练系列产品/Atlas A3 推理系列产品，在安装AI处理器的服务器执行npu-smi info -t board -i  -c 命令进行查询，获取Chip Name和NPU Name信息，实际配置值为Chip Name_NPU Name。例如Chip Name取值为Ascendxxx，NPU Name取值为1234，实际配置值为Ascendxxx_1234。其中：
-   id：设备id，通过npu-smi info -l命令查出的NPU ID即为设备id，命令中表示为`。
-   chip_id：芯片id，通过npu-smi info -m命令查出的Chip ID即为芯片id，命令中表示为。
-   针对Ascend 950PR/Ascend 950DT，在安装AI处理器的服务器执行npu-smi info -t board -i 命令进行查询，获取Chip Name和NPU Name信息，实际配置值为Chip Name_NPU Name。例如Chip Name取值为Ascendxxx，NPU Name取值为1234，实际配置值为Ascendxxx_1234。
其中，id为设备id，通过npu-smi info -l命令查出的NPU ID即为设备id，命令中表示为`。
## 返回值说明
无
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [直调共享库加载未定义平台符号—补齐CANN链接依赖](../../../runbooks/compilation/platform_manager_shared_library_link_dependencies.md)（`exemplifies`）：“该 host 入口调用了 `platform_ascendc::PlatformAscendCManager::GetInstance()` 来取得 AIV 核数”；“使用该功能需要包含"tiling/platform/platform_ascendc.h"头文件，并在编译脚本中链接tiling_api、platform动态库”。API 卡的链接合同正是 Runbook 中 undefined symbol 的根因与修复依据。
- [ArgMax 950 Direct Invoke 算子知识](../../../operators/direct/math/math/arg_max_950.md)（`related`）：“Direct `PlatformAscendCManager` 读取 AIV core/UB；显式 launcher”给出 ArgMax 950 Host 的平台查询动作；“通过该类的GetInstance方法可以获取一个PlatformAscendC类的指针，再通过该指针获取硬件平台相关信息”给出 manager 到平台对象的访问合同。
- [Sigmoid 950 Direct Invoke 算子知识](../../../operators/direct/nn/activation/sigmoid_950.md)（`related`）：“`calc_sigmoid_tiling_params(totalLength, elementBytes)` 查询 AIV 核数和 UB 字节数；AIV 核数非正时回退为 1。”给出 Direct Host 的平台信息需求；“基于Kernel Launch算子工程，通过Kernel直调（Kernel Launch）方式调用算子的场景下，可能需要获取硬件平台相关信息，比如获取硬件平台的核数。PlatformAscendCManager类提供获取平台信息的功能：通过该类的GetInstance方法可以获取一个PlatformAscendC类的指针，再通过该指针获取硬件平台相关信息，支持获取的信息可参考PlatformAscendC。”给出直调场景的获取入口。
<!-- cannbot:related:end -->
