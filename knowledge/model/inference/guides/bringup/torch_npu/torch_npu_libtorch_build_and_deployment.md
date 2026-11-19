---
type: Guide
title: libtorch_npu构建与C++部署：ABI、链接和TorchScript产物
description: 区分C++ bundle与Python wheel的ABI默认值，保存初始化、链接依赖和TorchScript示例的版本边界。
tags:
- task.implementation
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/installation_guide/references/building_libtorch_npu.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/references/building_libtorch_npu.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/installation_guide/building_from_source.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/building_from_source.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/installation_guide/references/faq.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/FAQ.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/build_libtorch_npu.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/setup.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/CMakeLists.txt
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/command_output.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/libtorch_error.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/command_output.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/libtorch_error.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/release_notes.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/release_notes.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/libs/README.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/libs/README.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/examples/libtorch_hccl/README_HCCL.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/examples/libtorch_hccl/README_HCCL.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/examples/libtorch_triton_ascend/README.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/C_list.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/C_list.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/C_list.md
  role: constraint
created_at: '2026-11-09T16:32:43Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# libtorch_npu构建与C++部署：ABI、链接和TorchScript产物

## 固定来源与产品边界

固定TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的双语libtorch_npu指南，依赖同提交源码安装准备；平台限该路径的A2/A3训练系列和950DT，不把其他推理系列或950PR自动加入。此处C++ bundle不等于AOTInductor产物，也不回推发布基线。

## bundle和ABI

build_libtorch_npu.py生成libtorch_npu目录，include放头文件、lib放库、share包含Torch_npuConfig.cmake；默认Release，可用DEBUG=1选Debug。指南所列CMake>=3.18是此页门槛，不覆盖源码安装页按PyTorch/架构的推荐矩阵。

本入口只在环境显式设置_GLIBCXX_USE_CXX11_ABI时转交CMake，CMake未定义时默认0；可设1，必须与所链接PyTorch保持一致。与此不同，setup.py的Python wheel路径从USE_CXX11_ABI=True开始，只有环境值恰为"0"才关闭，启用时传CMake ABI=1。不能把一个入口的默认值套给另一个入口，或把_GLIBCXX_USE_CXX11_ABI与GCC的_ABI_VERSION参数混成一项。实际产物、PyTorch和所有C++依赖还需核对架构、编译器和ABI。

## 链接和执行层次

libtorch_resnet示例包含torch、torch_npu、torchvision及hypothesis/expecttest/packaging准备，CMake引用bundle的include/lib并链接torch_npu，PyTorch库及其TORCH_CXX_FLAGS另外保持一致。示例路径须替换为真实bundle，不能只添加头文件后认为运行库搜索路径齐全。

aarch64旧截图中torch.libs的OpenBLAS依赖libgfortran缺失，导致_gfortran_*符号未解析；可以据真实依赖配置搜索/链接路径，不能硬编码截图的Python3.8.5、哈希库名或复制不匹配库。另一个成功截图只显示配置、链接libtorch_resnet和Success，不给模型数值/吞吐，因此不能作NPU运行验收。

resnet_trace.py导出TorchScript，由ci/libtorch_resnet.sh串联导出、构建和推理；文档缩写bash libtorch_resnet.sh须注意真实脚本目录。这是存量TorchScript消费示例，不是所有模型都能trace，也不是torch.export/AOTI缓存或共享库的可互换证明。接口见[初始化与同步](../../../apis/torch_npu/libtorch_npu_lifecycle.md)。

当前没有编译、导出、加载共享库/模型或执行设备测试。部署验收需分别检查真实库依赖、设备初始化、最小模型输出和所需性能，不从历史截图推出当前环境通过。

## 发布说明的Stable ABI不替代具体构建ABI

同提交26.1版本说明新增LibTorch Stable ABI能力，但没有在该条给出全部稳定接口、二进制发行矩阵或任意历史PyTorch互换保证。它与本卡_GLIBCXX_USE_CXX11_ABI和GCC ABI选项是不同层次；不能据“Stable”省略真实产物/链接依赖的ABI匹配，也不从摘要推导全部torch_npu C++私有接口稳定。

## C++目录与两个示例的范围

主线和发布版csrc/libs/README都说明该目录用于导出NPU相关接口、构建无Python的libtorch_npu推理部分。它不表示所有相邻C++示例都不依赖Python：HCCL例子的CMake用Python找torch路径，而Triton runtime明确嵌入解释器。

[HCCL单机示例](../../../../training/guides/torch_npu_libtorch_hccl_example.md)保留单机rank→设备、FileStore和仅打印局部结果的边界；[Triton C++样例](../../optimization/torch_npu/torch_npu_libtorch_triton_runtime.md)区分lambda grid求值与整体Python依赖。两者硬件范围和验证条件尚未闭合，独立保留草稿，不由本卡平台表替它们确认所有部署组合。

## OpPlugin C++目录补充的符号与稳定接口入口

OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5的C_list按设备初始化/释放、流、事件、随机数、格式、Hooks、OpCommand和HCCL列常规接口；主线d84e9b1d6a558e5f27973cd4329f62968e46fdda明确常规符号由libtorch_npu.so导出。这是目录的链接入口说明，不是每个beta符号从此都有跨PyTorch版本稳定ABI。具体合同见[生命周期](../../../apis/torch_npu/libtorch_npu_lifecycle.md)、[设备诊断](../../../apis/torch_npu/cpp_device_and_sync_diagnostics.md)、[生成器/Hooks](../../../apis/torch_npu/cpp_generator_and_hooks.md)、[格式存储](../../../apis/torch_npu/cpp_format_and_storage_sizes.md)、[格式转换](../../../apis/torch_npu/cpp_npu_format_cast.md)、[Dropout mask](../../../apis/torch_npu/cpp_dropout_gen_mask.md)、[流](../../../apis/torch_npu/cpp_npustream.md)、[Guard](../../../apis/torch_npu/cpp_npustream_guard.md)、[Event](../../../apis/torch_npu/cpp_npuevent.md)、[OpCommand](../../../apis/torch_npu/cpp_opcommand.md)、[Host存储Tensor](../../../apis/torch_npu/cpp_swapped_memory.md)及[HCCL](../../../../training/apis/torch_npu/cpp_processgroup_hccl.md)。

两语言主线目录补LibTorch Stable ABI，指向torch_npu/csrc/inductor/aoti_torch/c/shim.h的NPU设备/接口补充、generated/v2r13/c_shim_npu.h的aoti_torch_npu_*声明，并由libtorch_npu.so导出。链接显示名省略v2r13，实际URL带该版本目录；不把省略路径当本地保证存在的文件，也不把Stable ABI描述扩到全部常规C++私有接口、所有历史包或任意CANN版本。具体头文件与跨版本发行验证尚未由此目录完成。

主线中文ATB节只有概述，英文另给op_plugin/include/atb_ops.h统一入口、op_plugin/config/atb_ops.yaml接口清单、libop_plugin_atb.so导出库和at_npu::native::atb命名空间。它与libtorch_npu.so常规接口及AOTI Stable ABI入口分别消费；这些外指文件的完整实现、ATB产品矩阵、包版本和模型正确性尚未由目录证明。本节仅记录发现及入口，不扩大本卡既有硬件范围到未列产品，也不将独立主线当发布基线。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/installation_guide/references/building_libtorch_npu.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/references/building_libtorch_npu.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/installation_guide/building_from_source.md)（primary）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/building_from_source.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/installation_guide/references/faq.md)（primary）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/installation_guide/FAQ.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/build_libtorch_npu.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/setup.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/CMakeLists.txt)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/command_output.png)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/libtorch_error.png)（constraint）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/command_output.png)（constraint）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/libtorch_error.png)（constraint）

- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/release_notes.md)（primary）

- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/release_notes.md)（constraint）

- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/libs/README.md)（primary）

- [固定来源 17](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/libs/README.md)（constraint）

- [固定来源 18](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/examples/libtorch_hccl/README_HCCL.md)（primary）

- [固定来源 19](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/examples/libtorch_hccl/README_HCCL.md)（constraint）

- [固定来源 20](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/examples/libtorch_triton_ascend/README.md)（constraint）

- [固定来源 21](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/C_list.md)（constraint）

- [固定来源 22](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/C_list.md)（primary）

- [固定来源 23](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/C_list.md)（constraint）
