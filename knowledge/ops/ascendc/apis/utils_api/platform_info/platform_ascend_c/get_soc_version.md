---
type: API
title: GetSocVersion
description: 获取当前硬件平台版本型号。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/platform_info/PlatformAscendC/GetSocVersion.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetSocVersion

## 功能说明
获取当前硬件平台版本型号。
## 函数原型
## 参数说明
无
## 返回值
当前硬件平台版本型号的枚举类。该枚举类和AI处理器型号的对应关系请通过CANN软件安装后文件存储路径下include/tiling/platform/platform_ascendc.h头文件获取。
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
## 约束说明
为了满足算子二进制复用，使用Atlas A3 训练系列产品/Atlas A3 推理系列产品时，调用GetSocVersion接口返回的枚举值与Atlas A2 训练系列产品/Atlas A2 推理系列产品相同；如果需要区分，可使用接口aclrtGetSocName接口。
