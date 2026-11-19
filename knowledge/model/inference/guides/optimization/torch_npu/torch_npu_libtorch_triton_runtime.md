---
type: Guide
title: C++调用Triton样例：嵌入Python依赖和grid求值边界
description: 区分C++ lambda grid不经Python与整体runtime仍嵌入解释器，保留版本、链接和误差输出的样例身份。
tags:
- task.implementation
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/examples/libtorch_triton_ascend/README.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/examples/libtorch_triton_ascend/triton_runtime/CMakeLists.txt
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/examples/libtorch_triton_ascend/triton_runtime/include/python_env.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/examples/libtorch_triton_ascend/triton_runtime/src/python_env.cpp
  role: implementation
created_at: '2026-11-09T16:51:39Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# C++调用Triton样例：嵌入Python依赖和grid求值边界

## 固定版本与草稿原因

固定TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的examples/libtorch_triton_ascend。README推荐TorchNPU产品26.1.0/CANN9.1、Triton-Ascend>=3.2.2并指向外部release/PR246；未提供完整硬件及PyTorch包矩阵，外部链接未摄取，故draft、platforms为空，不自动套用主线2.14或26.0/PyTorch2.8。

## C++ grid不等于整个流程脱离Python

样例分别展示显式grid的Add、C++ lambda计算grid的Add及LayerNorm。lambda grid的求值在C++，但triton_runtime整体通过pybind11::embed和Python3::Python链接解释器，PythonEnv会检查Py_IsInitialized、按需Py_Initialize，并import模块/在__main__全局环境eval代码。因此“无需Python参与”仅对应grid求值，不能推广成无Python运行时或纯C++离线Kernel部署。

PythonEnv用单例和initialized_标记，本局部没有完整并发/GIL/退出生命周期合同，不据ensure_initialized调用推导任意多线程调用安全。这里只读取代码，没有嵌入解释器或执行eval/import。

## 构建产物及环境

文档先在triton_runtime构建libtriton_runtime.so，再调用examples/run_demo.sh；主CMake要求C++17、Python3>=3.10的Interpreter+Development、Torch和pybind11。目标链接还含torch_npu、CANN runtime/ascendcl/profapi、dl、ssl/crypto等；头/库路径分别取真实PyTorch、TorchNPU、CANN和Python环境，不能只安装pybind11就认为依赖齐备。

FAQ的unsupported relocation或缺libpython*.so案例要求CPython共享库，静态libpython*.a不等价；文档建议Python开发包或Conda环境是该场景路线，不保证任意发行版包都适配当前解释器/架构/ABI。PythonEnv注释让调用者提供PYTHONHOME以找到site-packages，但未设置该值，也不把它当所有嵌入环境的通用值。

LOG_TORCH_TRITON_RUNTIME=1用于详细日志。LayerNorm历史输出BLOCK_SIZE512、max diff约7.15e-7和match YES只属于示例比较，不是本卡实测、全dtype/shape精度承诺或端到端性能报告。本卡覆盖调用/部署层，未将my_kernels.py的Kernel编写扩为生产工程。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/examples/libtorch_triton_ascend/README.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/examples/libtorch_triton_ascend/triton_runtime/CMakeLists.txt)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/examples/libtorch_triton_ascend/triton_runtime/include/python_env.h)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/examples/libtorch_triton_ascend/triton_runtime/src/python_env.cpp)（implementation）
