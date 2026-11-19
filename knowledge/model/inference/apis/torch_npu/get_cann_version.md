---
type: API
title: get_cann_version：组件名、空字符串与容器驱动版本
description: 保存八个组件选择及CANN门槛，区分版本读取和整个软件栈配套。
tags:
- task.lookup
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-utils/torch_npu-utils-get_cann_version.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-utils/torch_npu-utils-get_cann_version.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-utils/torch_npu-utils-get_cann_version.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/__init__.py
  role: implementation
created_at: '2026-11-09T19:09:59Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# get_cann_version：组件名、空字符串与容器驱动版本

## 固定版本与产品

依据OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5的中文页及主线d84e9b1d6a558e5f27973cd4329f62968e46fdda的中英文页。A2/A3在本卡指训练系列，主线新增950DT确认不回推到发布版，不扩到950PR。旧Atlas产品只保留来源条目，不自动映射其他新型号。

发布配对PyTorch提交为f3ecfe4a7ef7395754da7ca2e35661a7132b519b；独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf单独引用，两个main不构成自动配套。以下为静态合同，没有编译、导入、加载模型、设备运行或性能测量。


## 参数和返回

`torch_npu.utils.get_cann_version(module="CANN") -> str`，module可为CANN、RUNTIME、COMPILER、HCCL、TOOLKIT、OPP、OPP_KERNEL、DRIVER，分别查询对应组件版本。无效module返回空字符串；CANN<8.1.RC1不支持此功能，也返回空字符串，因此空串不等于机器肯定没有安装该组件。

## 文件与包装位置

DRIVER版本依赖/etc/ascend_install.info及/usr/local/Ascend/driver/version.info；容器需正确映射两文件。文档示例8.3.RC1不是本环境检测结果，不把容器镜像版本当宿主驱动版本。

发布utils/__init__.py从torch_npu.npu.utils导出该函数，后者37–45行转交_C._get_cann_version；不要与collect_env.py中同名无参辅助函数混为一谈。该字符串读取不检查TorchNPU/PyTorch、OpPlugin gitlink、TorchAir、CANN与硬件的完整配套，更不等于功能/性能可用；按[固定软件栈身份](../../concepts/frameworks/ascend_software_stack_baselines.md)另行核对。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-utils/torch_npu-utils-get_cann_version.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-utils/torch_npu-utils-get_cann_version.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-utils/torch_npu-utils-get_cann_version.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/utils.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/__init__.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/__init__.py)（implementation）
