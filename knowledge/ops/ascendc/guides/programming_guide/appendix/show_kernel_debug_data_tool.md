---
type: Guide
title: ShowKernelDebugData工具
description: 提供Ascend C算子Kernel调测信息的离线解析能力，将导出的bin文件解析为可读格式。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/appendix/show_kernel_debug_data_tool.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# show_kernel_debug_data工具

在Ascend C算子程序代码中，用户可以使用AscendC::DumpTensor、AscendC::printf、AscendC::PrintTimeStamp、ascendc_assert接口打印相关调试信息，并通过aclInit接口或直接配置acl.json文件，启用Dump配置，导出Ascend C算子Kernel的调测信息。本工具提供了对调测信息的离线解析能力，帮助用户获取并解析调试信息，即将导出的bin文件解析成可读格式。本工具的使用示例可参考show_kernel_debug_data样例。
## 工具安装
1.  安装工具。
工具跟随CANN软件包发布（参考环境准备完成CANN安装），其路径默认为${INSTALL_DIR}/tools/show_kernel_debug_data，其中${INSTALL_DIR}请替换为CANN软件安装后文件存储路径。以root用户安装为例，安装后文件默认存储路径为：/usr/local/Ascend/cann。
2.  设置环境变量。
-   root用户安装Ascend-cann-toolkit包时
-   非root用户安装Ascend-cann-toolkit包时
3.  检查工具是否安装成功。
执行如下命令，若能正常显示--help或-h信息，则表示工具环境正常，功能可正常使用。
## 使用方法
-   命令行方式
必选：kernel侧调试信息落盘的bin文件或包含bin文件的目录路径，例如“/input/dump_workspace.bin”。
可选：解析结果的保存路径，例如“/output_dir”。默认是当前命令行执行目录下。
-   API方式
获取kernel侧调试信息并解析成可读文件。函数原型如下。
其中，输入参数说明如下。函数无输出参数和返回值。
-   bin_file_path：kernel侧调试信息落盘的bin文件或包含bin文件的目录路径，字符串类型。
-   output_path：解析结果的保存路径，字符串类型，默认是当前接口调用脚本所在目录下。
调用示例参考如下代码。
## 产物说明
工具解析结果文件目录结构如下。其中，dump_data目录是对DumpTensor、PrintTimeStamp接口解析的结果，index0对应DumpTensor接口中第二个参数desc=0时的打印，loop0表示切分后首个分块的数据打印。

<!-- cannbot:related:start -->
## 相关

- [DumpTensor](../../../apis/simd_api/basic_api/debug_interface/onboard_print/dump_tensor.md)（`explains`）：《DumpTensor》说明打印Tensor内容并支持自定义标签，可选传入Shape信息按指定维度排列展示数据。；《ShowKernelDebugData工具》说明提供Ascend C算子Kernel调测信息的离线解析能力，将导出的bin文件解析为可读格式。。二者在DumpTensor/asc_dump、checkpoint、开关和上板调试工具构成设备张量观测链；VF和精度卡给出不可用PRINTF时的替代证据路径上存在可执行的直接衔接。
- [调用算子时出现无法打开config.ini的报错](faq/config_ini_open_error.md)（`related`）：调用算子时出现无法打开config.ini的报错 与《ShowKernelDebugData工具》的实质衔接是：config.ini 打开失败要沿文件名、权限、架构配置和构建/调试工具链排查；所保留卡均提供具体检查或恢复动作。
- [NPU域上板调试（功能调试）](../debug_and_tuning/functional_debug/npu_board_debug.md)（`same_topic`）：《NPU域上板调试（功能调试）》处理“NPU域上板调试手段主要包含上板数据打印、msSanitizer内存异常检测和msDebug单步调试等功能，数据打印包括printf、DumpTensor两种方式，其中，DumpTensor是SIMD编程独有功能，用于打印指定Tensor的数据。”。《ShowKernelDebugData工具》提供“提供Ascend C算子Kernel调测信息的离线解析能力，将导出的bin文件解析为可读格式。”，其具体合同或探针直接接入NPU 上板打印、异常定位、Tiling 调试、精度对比和离线解析流程。
<!-- cannbot:related:end -->
