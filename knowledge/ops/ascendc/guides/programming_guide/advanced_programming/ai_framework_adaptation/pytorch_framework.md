---
type: Guide
title: PyTorch框架
description: 通过PyTorch框架进行模型的训练、推理时，会调用很多算子进行计算。开发者开发的自定义算子如果需要集成部署到PyTorch框架，有如下几种方式：
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/ai_framework_adaptation/pytorch_framework.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# PyTorch框架

通过PyTorch框架进行模型的训练、推理时，会调用很多算子进行计算。开发者开发的自定义算子如果需要集成部署到PyTorch框架，有如下几种方式：
-   Kernel直调：通过适配torch.library或Pybind注册自定义算子，可以实现PyTorch框架调用算子Kernel程序。
-   单算子API调用：该模式下的适配插件开发流程和具体样例请参见 《TorchNPU》中的“开发指南 > 框架特性 > 自定义算子适配开发 > 基于OpPlugin算子适配开发”章节。
-   图模式调用：自定义算子在Pytorch图模式下的适配开发指导请参见 《TorchNPU》中的“TorchAir > 自定义算子入图”章节。
本节主要提供通过torch.library与Pybind注册自定义算子并实现PyTorch框架调用算子Kernel程序的指导。
-   torch.library是用于扩展PyTorch核心算子库的API集合。它允许开发者创建新的算子、并为其提供自定义实现。
-   Pybind是一个开源的C++和Python之间的桥接工具，它旨在使C++代码能够无缝地集成到Python环境中。
Pybind适用于快速将C++函数暴露给Python，实现高效接口绑定。但其生成的算子无法被PyTorch的算子系统识别，不具备schema定义与图追踪能力，因此不支持torch.compile优化。相比之下，torch.library提供了与PyTorch核心算子系统深度集成的机制，支持算子注册、schema定义和图追踪能力，是支持torch.compile的必要条件。开发者可根据需求选择对应方式。
## torch.library
下面代码以add_custom（Add自定义算子为例）算子为例，介绍通过torch.library如何调用算子Kernel程序，文档中仅介绍核心步骤，完整样例请参考torch.library样例。
1.  环境准备。
除了按照环境准备进行CANN软件包的安装，还需要安装以下依赖：
安装TorchNPU
2.  实现NPU上的自定义算子。
包括算子Kernel实现，并使用>>接口调用算子核函数完成指定的运算。样例中的c10_npu::getCurrentNPUStream接口用于获取当前npu流，返回值类型NPUStream，使用方式请参考 《TorchNPU》中的“API > 自定义API”。
需要注意的是，本样例的输入x，y的内存是在外层的Python调用脚本中分配的。
3.  自定义算子的注册。
PyTorch提供TORCH_LIBRARY宏作为自定义算子注册的核心接口，用于创建并初始化自定义算子库，注册后在Python侧可以通过torch.ops.namespace.op_name方式进行调用。TORCH_LIBRARY_IMPL用于将算子逻辑绑定到特定的DispatchKey（PyTorch设备调度标识），针对NPU设备，需要将算子实现注册到PrivateUse1这一专属的DispatchKey上。
4.  编译生成算子动态库。
5.  使用Python测试脚本进行测试。
