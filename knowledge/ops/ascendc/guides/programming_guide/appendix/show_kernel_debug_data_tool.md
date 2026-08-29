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

- [DumpTensor](../../../apis/simd_api/basic_api/debug_interface/onboard_print/dump_tensor.md)（`explains`）：本工具提供了对调测信息的离线解析能力；打印Tensor内容并支持自定义标签。DumpTensor 在 Kernel 侧生成带标签的 Tensor 调测数据，ShowKernelDebugData 再把导出的 bin 离线解析为可读内容；指南把具体 API 输出接到完整调试查看流程。
<!-- cannbot:related:end -->
