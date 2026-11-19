---
type: Guide
title: libtorch HCCL 单机示例：rank 映射与结果验收边界
description: 对照主线和发布版示例识别设备编号、FileStore、构建路径与仅打印局部结果的边界。
tags:
- task.implementation
- topic.parallelism
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/examples/libtorch_hccl/README_HCCL.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/examples/libtorch_hccl/README_HCCL.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/examples/libtorch_hccl/allreduce_hccl.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/examples/libtorch_hccl/libtorch_hccl.sh
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/examples/libtorch_hccl/CMakeLists.txt
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/examples/libtorch_hccl/allreduce_hccl.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/examples/libtorch_hccl/libtorch_hccl.sh
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/examples/libtorch_hccl/CMakeLists.txt
  role: implementation
created_at: '2026-11-09T16:51:39Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# libtorch HCCL 单机示例：rank 映射与结果验收边界

## 版本与草稿原因

固定TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf及发布提交f3ecfe4a7ef7395754da7ca2e35661a7132b519b的libtorch_hccl说明、C++、启动脚本和CMake。示例未给完整产品矩阵，构建及验收也有未闭合条件，本卡draft、platforms为空；不将其存在当所有设备、跨节点或发布组合已经运行验证。

## 实际通信流程

RANK默认0、SIZE默认1；设备字符串实际为npu:{rank}，README概述中的npu:0不是所有rank共用的固定设备。脚本默认起2个本机进程，NUM_PROCESSES可改，未检查可见设备数量，也没有global rank到local device的跨节点映射。

C++用固定/tmp/c10d_hccl_example的FileStore协调，创建ProcessGroupHCCL，建立10个FP32全1Tensor，shape为(1000,16*(i+1))。依序提交allreduce、保存Work再逐个wait，之后将前3个Tensor拷CPU、打印各首元素，最后finalize_npu。Work等待与整个设备所有流的屏障仍按实际实现区分。

脚本清理该固定FileStore文件并同时启动各rank，这不是可直接并发启动多作业或跨节点的通用launcher；本文未删除临时文件、创建进程/通信端口或运行设备。

## 构建路径不完全自动

CMake优先TORCH_INSTALL_DIR，否则执行PYTHON_EXECUTABLE导入torch找路径，但该文件自己没有find_package Python或设置解释器，不能仅因已安装torch就承诺自动探测成功。TORCH_NPU_INSTALL_DIR只从环境取，缺失仅告警，后面仍链接torch_npu；告警不意味着可以不提供库。

示例配置C++17/C11，链接torch、torch_cpu、c10、torch_npu，aarch64还提示torch.libs。它没有自动导入全部Torch CMake编译选项/ABI，必须与实际PyTorch和libtorch_npu匹配，不能用“Release”标签代替ABI检查。[C++ bundle与ABI](../../inference/guides/bringup/torch_npu/torch_npu_libtorch_build_and_deployment.md)和[生命周期声明](../../inference/apis/torch_npu/libtorch_npu_lifecycle.md)各按自身版本范围消费。

## 输出不是完整数值断言

默认两rank的全1求和应为2.0，改SIZE后期望值相应变化，不能固定用2判断所有配置。源码仅打印前三个Tensor首元素，没有对全部10个Tensor/元素做assert，“运行成功”字符串也无完整数值判断门控。要验收完整通信，需确认所有rank、所有结果、shape/dtype及异常分支，不能把历史预期输出当作验证依据。

两版启动脚本原字节相同；C++/CMake差异主要排版，已分别完整读取。没有执行构建、导入torch、加载库或启动NPU通信。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/examples/libtorch_hccl/README_HCCL.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/examples/libtorch_hccl/README_HCCL.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/examples/libtorch_hccl/allreduce_hccl.cpp)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/examples/libtorch_hccl/libtorch_hccl.sh)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/examples/libtorch_hccl/CMakeLists.txt)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/examples/libtorch_hccl/allreduce_hccl.cpp)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/examples/libtorch_hccl/libtorch_hccl.sh)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/examples/libtorch_hccl/CMakeLists.txt)（implementation）
